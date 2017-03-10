#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

from handlers.base import BaseHandler
from handlers.upload import UploadHandler
from handlers.retrieve import RetrieveHandler

urls = (
    (r'/upload', UploadHandler),
    (r'/token/([a-f0-9]{40})', RetrieveHandler),
    (r'.*', BaseHandler),
)
