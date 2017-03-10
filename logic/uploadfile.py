import os
import math
import settings

import logging
from filechunkio import FileChunkIO
from utils import tokengen, S3Connection, guess_mime_type

from documents.files import UploadedFiles

from boto.s3.key import Key

MIN_CHUNK_SIZE = 5242880

def progress(done, size):
    logging.info("Uploading done: [%s KB] of ~ [%s KB]" % (don/1024, size/1024))


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

        return self.filename

    def delete_entry(self):
        _file = UploadedFiles.objects.get(token=self.token)
        _file.delete()

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


    def multipart_file_big(self):
        try:
            multi_part = self.s3_conn.bucket.initiate_multipart_upload(
                os.path.basename(self.get_file_path),
                headers=self.get_headers,
                metadata=self.get_headers
            )

            chunk_size = MIN_CHUNK_SIZE
            chunk_count = int(math.ceil(self.file_size / float(chunk_size)))

            for i in range(chunk_count):
                offset = chunk_size * i
                _bytes = min(chunk_size, self.file_size - offset)
                with FileChunkIO(self.get_file_path, 'r', offset=offset,
                             bytes=_bytes) as _fpart:
                     multi_part.upload_part_from_file(
                         _fpart, part_num=i + 1,
                         cb=progress
                     )

            multi_part.complete_upload()

        except:
            multi_part.cancel_upload()
            self.delete_entry()

            raise Exception("There was some problem in uploading")

    def upload_to_s3(self):
        #Save to the file first
        #TODO:Try to stream directly

        self.save_to_file()

        #Based on file size decide, to use multipart or upload in once
        self.file_size = os.stat(self.get_file_path).st_size

        _uload_func = self.single_file
        if self.file_size > MIN_CHUNK_SIZE:
            _uload_func = self.multipart_file_big

        _uload_func()
        return self.filename
