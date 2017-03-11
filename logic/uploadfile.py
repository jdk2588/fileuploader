import os
import math
import settings

import logging
import multiprocessing

from filechunkio import FileChunkIO
from utils import tokengen, S3Connection, guess_mime_type

from documents.files import UploadedFiles

from boto.s3.key import Key
import time

MIN_CHUNK_SIZE = 5242880

def progress(done, size):
    logging.info('%d KB transferred / %d KB total' % (done/1024, size/1024))


class UploadFile():
    def __init__(self, *args, **kwargs):
        self.filebody = kwargs.get("body")
        self.filename = tokengen()
        self.content_type = kwargs.get("content_type")
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
        self.file_mongo_obj.delete()

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

        except:
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
                self.upload_part(mpart_id, part_num, offset, _bytes, retries=retries)
                logging.warning("%s part failed for %s" % part_num,
                                self.get_file_path)
            else:
                raise e


    def multipart_file_big(self):
        multi_part = self.s3_conn.bucket.initiate_multipart_upload(
            os.path.basename(self.get_file_path),
            headers=self.get_headers,
            metadata=self.get_headers
        )

        chunk_size = MIN_CHUNK_SIZE
        bytes_per_chunk = max(int(math.sqrt(MIN_CHUNK_SIZE) *
                                  math.sqrt(self.file_size)), MIN_CHUNK_SIZE)

        chunk_count = int(math.ceil(self.file_size / float(bytes_per_chunk)))

        pool = multiprocessing.Pool(processes=4)

        for _chu in range(chunk_count):
            offset = bytes_per_chunk * _chu
            _bytes = min(chunk_size, self.file_size - offset)

            pool.apply_async(self.upload_part, [multi_part.id, _chu+1,
                                           offset, _bytes])

        pool.close()
        pool.join()

        if len(multi_part.get_all_parts()) == chunk_count:
            multi_part.complete_upload()
            self.update_entry()
        else:
            multi_part.cancel_upload()
            self.delete_entry()
            raise Exception("There was some problem in uploading")


    def upload_to_s3(self):
        #Save to the file first
        #TODO:Try to stream directly

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
