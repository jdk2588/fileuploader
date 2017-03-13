#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import os
import sys
SRC_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(SRC_PATH))

import settings

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from urls import urls

from tornado.log import app_log as logging


class App(tornado.web.Application):
    def listen(self, port, address='', **kwargs):
        self.port = port
        server = tornado.httpserver.HTTPServer(self, **kwargs)
        server.listen(port, address)

def main():
    tornado.options.parse_command_line()
    logging.info('Starting Tornado web server on http://localhost:%s' % \
        settings.APP_PORT)

    application = App(urls, transforms=None)
    http_server = tornado.httpserver.HTTPServer(
        application,
        max_buffer_size=settings.MAX_BUFFER_SIZE,
        max_body_size=settings.MAX_BODY_SIZE,
        no_keep_alive=True, xheaders=True)

    http_server.bind(settings.APP_PORT, settings.APP_HOST)
    http_server.start(1)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
