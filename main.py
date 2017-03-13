#!/usr/bin/python3.5
# Author <Jaideep Khandelwal jdk2588@gmail.com>

import os
import sys
SRC_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(SRC_PATH))

import time
import settings

import signal
import logging
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from urls import urls
from functools import partial

from tornado.log import app_log as logging

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 5

class App(tornado.web.Application):
    def listen(self, port, address='', **kwargs):
        self.port = port
        server = tornado.httpserver.HTTPServer(self, **kwargs)
        server.listen(port, address)

def sig_handler(server, sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()

    def stop_loop(deadline):
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop, deadline)
        else:
            io_loop.stop()
            logging.info('Shutdown finally')

    def shutdown():
        logging.info('Stopping http server')
        server.stop()
        stop_loop(time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)

    logging.warning('Caught signal: %s', sig)
    io_loop.add_callback_from_signal(shutdown)

def main():
    tornado.options.parse_command_line()
    logging.info('Running on %s:%s' % \
        (settings.APP_HOST, settings.APP_PORT))

    application = App(urls, transforms=None)
    http_server = tornado.httpserver.HTTPServer(
        application,
        max_buffer_size=settings.MAX_BUFFER_SIZE,
        max_body_size=settings.MAX_BODY_SIZE,
        no_keep_alive=True, xheaders=True)

    http_server.bind(settings.APP_PORT, settings.APP_HOST)

    #Using 0 will run on max CPU on machine
    http_server.start(settings.NUMBER_OF_FORKS)

    signal.signal(signal.SIGTERM, partial(sig_handler, http_server))
    signal.signal(signal.SIGINT, partial(sig_handler, http_server))

    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
