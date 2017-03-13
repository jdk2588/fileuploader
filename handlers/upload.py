#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import logging
import tornado.web
import tornado.gen

from tornado.queues import Queue
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import settings

from handlers.base import BaseHandler
from logic.uploadfile import UploadFile


@tornado.web.stream_request_body
class UploadHandler(BaseHandler):

    executor = ThreadPoolExecutor(max_workers=settings.THREAD_WORKERS)

    def prepare(self, *args, **kwargs):

        #Queue to take chunks of data received'''
        self.queue = Queue()

        #Change the size of body
        if self.request.method.lower() == "post":
            self.request.connection.set_max_body_size(settings.MAX_STREAMED_SIZE)

        try:
            self.content_length = int(
                self.request.headers.get("Content-Length", "0")
            )
        except KeyError:
            self.content_length = 0

        super(UploadHandler, self)._execute(*args, **kwargs)

    @tornado.gen.coroutine
    def data_received(self, chunk):
        #Put chunks in a queue as received'''
        yield self.queue.put(chunk)


    #Upload to S3, with Threaded Pool
    @run_on_executor(executor='executor')
    def background_task(self, obj):
        return obj.upload_to_s3(self.queue)

    @tornado.gen.coroutine
    def post(self):
        obj = UploadFile(
            body=self.request.body,
            content_type=self.request.headers.get("Content-Type"),
            content_length=self.content_length
        )

        ret = obj.write_entry()
        self.write_json(data={"token": ret})
        yield self.background_task(obj)
