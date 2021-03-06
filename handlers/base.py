#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import json
import settings
import tornado.web

class CustomException(tornado.web.HTTPError):
    pass

class BaseHandler(tornado.web.RequestHandler):

    def prepare(self, *args, **kwargs):
        '''Check for X-Auth header in the request header,
        so service not open to public access '''

       # _auth = self.request.headers.get("X-Auth")
       # if not _auth or _auth != settings.AUTH_HEADER_VAL:
       #     raise Exception("Client not authorized to make request")

        super(BaseHandler, self).prepare(*args, **kwargs)

    def _execute(self, *args, **kwargs):

        if "application/json" in (
         self.request.headers.get('Content-Type') or {}
        ):
             try:
                 params = json.loads(self.request.body)
             except ValueError:
                 raise Exception("Cannot JSON decode data")

        super(BaseHandler, self)._execute(*args, **kwargs)

    def write_json(self, data=None, code=200, message=None):
        ret = {
            "data": data or {},
            "message": message or "OK",
            "code": code
        }
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(ret)

    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps({
                'code': status_code,
                'error': {
                    'reason': self._reason
                }
            }))

    def write(self, *args, **kwargs):
        super(BaseHandler, self).write(*args, **kwargs)
        self.finish()
