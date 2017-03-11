#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import asyncio

import tornado.web
import tornado.gen

from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from handlers.base import BaseHandler
from logic.uploadfile import UploadFile

class UploadHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=2)

    #@run_on_executor
    def background_task(self, obj):
        return obj.upload_to_s3()

    @tornado.gen.coroutine
    def post(self):
        obj = UploadFile(
            body=self.request.body,
            content_type=self.request.headers.get("Content-Type")
        )

        ret = obj.write_entry()

        self.background_task(obj)

        self.write_json(data={"token": ret})
