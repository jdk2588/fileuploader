#!/usr/bin/python
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import settings

from utils import S3Connection
from documents.files import UploadedFiles, DoesNotExist
from handlers.base import CustomException

class GetFile():
    def __init__(self, token):
        self.s3_conn = S3Connection()
        self.token = token

    def generate_signed_url(self):

        #Check if the token corresponds to a valid file
        try:
            _file = UploadedFiles.objects.get(token=self.token)
        except DoesNotExist:
            raise CustomException(reason="InvalidFile", status_code=404)

        ret = {}

        is_uploaded = False

        if _file.upload_failed:
            raise CustomException(
                reason="UploadFailed",
                status_code=412)
        elif not _file.is_uploaded:
            ret["message"] = "The file is still being uploaded"
        else:
            is_uploaded = True

            #Ensure the file has been uploaded or present in S3
            cloudfileobj = self.s3_conn.bucket.get_key(self.token)

            ret["content_type"] = cloudfileobj.content_type
            ret["redirect_url"] = cloudfileobj.generate_url(
                settings.SIGNED_URL_EXPIRATION,
                response_headers={"Content-Type": cloudfileobj.content_type}
            )

        ret["is_uploaded"] = is_uploaded

        return ret
