#!/usr/bin/python
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import settings

from utils import S3Connection
from documents.files import UploadedFiles

class GetFile():
    def __init__(self, token):
        self.s3_conn = S3Connection()
        self.token = token

    def generate_signed_url(self):

        #Check if the token corresponds to a valid file
        _file = UploadedFiles.objects.get(token=self.token)

        is_uploaded = False
        if not _file:
            ret_obj = "No such file exist"
        elif _file.upload_failed:
            ret_obj = "Sorry! This file could not be uploaded"
        elif not _file.is_uploaded:
            ret_obj = "The file is still being uploaded"
        else:
            is_uploaded = True

            #Ensure the file has been uploaded or present in S3
            cloudfileobj = self.s3_conn.bucket.get_key(self.token)
            ret_obj = cloudfileobj.generate_url(
                settings.SIGNED_URL_EXPIRATION,
                response_headers={"Content-Type": cloudfileobj.content_type}
            )

        return (is_uploaded, ret_obj)
