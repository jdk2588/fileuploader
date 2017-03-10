#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import tornado.web
import tornado.gen
from handlers.base import BaseHandler
from logic.getfile import GetFile

class RetrieveHandler(BaseHandler):

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, token):
        retobj = GetFile(token)
        redirect, url = retobj.generate_signed_url()

        if redirect:
            self.redirect(url)
        else:
            self.write_json({"data": url})
