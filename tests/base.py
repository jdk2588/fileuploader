import os
import sys
SRC_PATH = os.path.abspath(os.path.dirname(__file__) + "../..")
sys.path.append(os.path.join(SRC_PATH))

import time
import unittest
import tornado.httpserver
import tornado.httpclient

from urls import urls
import settings

class BaseTestCase(unittest.TestCase):
    http_server = None
    response = None
    host = None
    port = None
    base_url = None
    http_client = None

    headers = None
    token = None
    signed_url = None

    def setUp(self):
        self.sleep = False
        self.host = settings.APP_HOST
        self.port = settings.APP_PORT
        self.base_url = 'http://%s:%s/' % (self.host, self.port)
        self.http_client = tornado.httpclient.AsyncHTTPClient()
        self.sleep_time = 10

        self.headers = tornado.httputil.HTTPHeaders()
        application = tornado.web.Application(urls)
        self.http_server = tornado.httpserver.HTTPServer(application)
        self.http_server.listen(self.port)


    def get(self, url, **kwargs):
        self._request(url, 'GET', **kwargs)

    def post(self, url, data=None, **kwargs):
        self._request(url, 'POST', data, **kwargs)

    def external_request(self, url, **kwargs):
        request = tornado.httpclient.HTTPRequest(
            url, "GET", self.headers,
            **kwargs
        )
        self.http_client.fetch(request, self._handle_response)
        tornado.ioloop.IOLoop.instance().start()

    def _request(self, url, method, data=None, **kwargs):
        url = self.base_url + url
        request = tornado.httpclient.HTTPRequest(
            url, method, self.headers,
            **kwargs
        )
        if data:
            request.body = data
        self.http_client.fetch(request, self._handle_response)
        tornado.ioloop.IOLoop.instance().start()

    def tearDown(self):
        if self.sleep:
            time.sleep(self.sleep_time)
        self.http_server.stop()

    def _handle_response(self, response):
        self.response = response
        tornado.ioloop.IOLoop.instance().stop()
