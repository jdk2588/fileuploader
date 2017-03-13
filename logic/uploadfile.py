import os
import math
import time
import logging
import multiprocessing

from boto.s3.key import Key
from filechunkio import FileChunkIO

import settings
from documents.files import UploadedFiles
from utils import tokengen, S3Connection, guess_mime_type

MIN_CHUNK_SIZE = 5242880

def progress(done, size, *args, **kwargs):
    logging.info('%d KB transferred / %d KB total' % (done/1024, size/1024))


class UploadFile():
    def __init__(self, *args, **kwargs):
        self.filebody = kwargs.get("body")
        self.filename = tokengen()
        self.content_type = kwargs.get("content_type")
        self.content_length = kwargs.get("content_length") or 0
        self.s3_conn = S3Connection()
        self.filepath = None
        self.headers = {}

    @property
    def get_file_path(self):

        if self.filepath:
            return self.filepath

        localstor = settings.LOCAL_STORAGE_DIR
        if not os.path.exists(localstor):
            os.makedirs(localstor)

        if not settings.LOCAL_STORAGE_DIR.endswith("/"):
            localstor = localstor + "/"


        self.filepath = localstor + self.filename
        return self.filepath

    @property
    def get_headers(self):
        if self.headers:
            return self.headers

        self.headers = {
            "Content-Type": self.content_type,
        }

        return self.headers


    def save_to_file(self):

        output_file = open(self.get_file_path, 'wb+')
        output_file.write(self.filebody)

        if not self.content_type:
            self.content_type = guess_mime_type(self.get_file_path)

    def write_entry(self):

        """Having seperate entry for filename, in case
        filename, passed in future"""

        _data = {
            "token":self.filename,
            "filename": self.filename,
            "cloudfilename": self.filename,
            "contenttype": self.content_type
        }

        obj = UploadedFiles(**_data)
        obj.save()

        self.file_mongo_obj = obj

        return self.filename

    def delete_entry(self):
        self.file_mongo_obj.upload_failed = True
        self.file_mongo_obj.save()

    def update_entry(self):
        self.file_mongo_obj.is_uploaded = True
        self.file_mongo_obj.save()

    def single_file(self):
        try:

            k = Key(self.s3_conn.bucket)

            k.metadata = self.get_headers
            k.key = self.filename

            k.set_contents_from_filename(
                self.get_file_path,
                headers=self.get_headers,
                cb=progress
            )

        except Exception as e:
            self.delete_entry()
            raise Exception("There was some problem in uploading")


    def upload_part(self, mpart_id, part_num, offset, _bytes, retries=2):

        try:
            for everypart in self.s3_conn.bucket.get_all_multipart_uploads():
                if everypart.id == mpart_id:
                    with FileChunkIO(self.get_file_path, 'r', offset=offset,
                                 bytes=_bytes) as _fpart:

                         logging.info("Uploading part %s", part_num)
                         everypart.upload_part_from_file(
                             _fpart, part_num=part_num,
                             cb=progress
                         )

                    break

        except Exception as e:
            if retries:
                retries -= 1
                self.upload_part(
                    mpart_id, part_num, offset, _bytes, retries=retries)

                logging.warning("%s part failed for %s" % part_num,
                                self.get_file_path)
            else:
                raise e


    def initiate_multipart_upload(self):
        self.multi_part = self.s3_conn.bucket.initiate_multipart_upload(
            self.filename,
            headers=self.get_headers,
            metadata=self.get_headers
        )

        self.temp_part = 1

    def complete_upload(self):
        self.multi_part.complete_upload()
        self.update_entry()

    def cancel_upload(self):
        self.multi_part.cancel_upload()
        self.delete_entry()

    def process_chunk_write(self, data):
        _temp = self.filename + str(time.time())
        _file = open(_temp, "wb+")
        _file.write(data)
        _file.seek(0)

        self.multi_part.upload_part_from_file(
             _file, part_num=self.temp_part,
             cb=progress, num_cb=3
        )

        _file.close()
        os.remove(_temp)
        self.temp_part += 1


    def multipart_file_big(self):
        self.initiate_multipart_upload()

        chunk_size = MIN_CHUNK_SIZE
        bytes_per_chunk = max(int(math.sqrt(MIN_CHUNK_SIZE) *
                                  math.sqrt(self.file_size)), MIN_CHUNK_SIZE)

        chunk_count = int(math.ceil(self.file_size / float(bytes_per_chunk)))

        pool = multiprocessing.Pool(processes=4)

        for _chu in range(chunk_count):
            offset = bytes_per_chunk * _chu
            _bytes = min(chunk_size, self.file_size - offset)

            pool.apply_async(self.upload_part, [self.multi_part.id, _chu+1,
                                           offset, _bytes])

        pool.close()
        pool.join()

        if len(self.multi_part.get_all_parts()) == chunk_count:
            self.complete_upload()
        else:
            self.cancel_upload()
            raise Exception("There was some problem in uploading")


    def keep_adding_size(self, queue):

            size = MIN_CHUNK_SIZE
            start = 0
            data = b""

            while queue.qsize() and start < min(MIN_CHUNK_SIZE,
                                                self.content_length):
                d = queue.get()
                data += d.result()
                start = len(data)

            if self.content_length > 0:
                self.content_length -= MIN_CHUNK_SIZE

            self.process_chunk_write(data)


    def pick_via_queue(self, queue):

        try:
            self.initiate_multipart_upload()
            while queue.qsize():
                self.keep_adding_size(queue)
            self.complete_upload()

        except Exception as e:

            self.cancel_upload()
            raise e

    def upload_to_s3(self, queue=None):
        #Save to the file first
        #TODO:Try to put stream directly

        '''Using queue preferred, to put streams of data else use multiprocess for,
        big file in different parts or upload in once, though problem with multipr-
        ocess is too many processes spawn, though Threading will have GIL issue,
        better way could be to have a task queue manager like Celery'''

        logging.info("Processing file %s", self.filename)
        if queue:
            t1 = time.time()
            self.pick_via_queue(queue)
            t2 = time.time()
            logging.info("Time taken for file %s is %s", self.filename, t2-t1)

        else:

            t1 = time.time()
            self.save_to_file()

            #Based on file size decide, to use multipart or upload in once
            self.file_size = os.stat(self.get_file_path).st_size

            _uload_func = self.single_file
            if self.file_size > MIN_CHUNK_SIZE:
                _uload_func = self.multipart_file_big

            _uload_func()
            t2 = time.time()
            logging.info("Time taken for file %s is %s", self.filename, t2-t1)
            return self.filename
