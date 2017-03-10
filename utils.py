import os
import sys
SRC_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(SRC_PATH, "../"))

import settings
import hashlib

from boto import connect_s3
from datetime import datetime


def tokengen():
    rand = os.urandom(1024)
    s = hashlib.sha1()
    s.update(rand)
    s.update(str(datetime.utcnow()).encode('utf-8'))
    return s.hexdigest()

def guess_mime_type(source):
    try:
        import magic
    except ImportError:
        print("Could not get python-magic module, will help in identifying MIME Type \
              in case Content-Type is not passed in request headers")
        return None

    if isinstance(source, file):
        return magic.from_buffer(source.read(), mime=True)

    return magic.from_file(source, mime=True)


class S3Connection(object):
    def __init__(self,access_key=None,secret_key=None,host=None):

        self.conn = connect_s3(
            aws_access_key_id=access_key or settings.AWS_ACCESS_KEY,
            aws_secret_access_key=secret_key or settings.AWS_SECRET_ACCESS,
            host=host or settings.AWS_BUCKET_REGION
        )

        self.bucket = self.conn.get_bucket(settings.AWS_BUCKET_NAME)
