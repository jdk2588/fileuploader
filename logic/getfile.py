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
        if not _file:
            return (False, "No such file exist")

        #Ensure the file has been uploaded or present in S3 
        cloudfileobj = self.s3_conn.bucket.get_key(self.token)
        if not cloudfileobj:
            return (False, "The file is still being uploaded")
        else:
            ret = cloudfileobj.generate_url(
                settings.SIGNED_URL_EXPIRATION,
                response_headers={"Content-Type": cloudfileobj.content_type}
            )

            return (True, ret)
