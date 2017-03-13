#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import tornado.web
import tornado.gen
from handlers.base import BaseHandler
from logic.getfile import GetFile

class RetrieveHandler(BaseHandler):

    @tornado.gen.engine
    def get(self, token):
        retobj = GetFile(token)
        _data = retobj.generate_signed_url()

        #If redirect url present then redirect
        if _data.get("redirect_url"):
            self.set_header("Content-Type", "%s" % _data['content_type'])
            self.redirect(_data.get("redirect_url"))
        else:
            self.write_json(**{"data": _data, "message": _data["message"]})
