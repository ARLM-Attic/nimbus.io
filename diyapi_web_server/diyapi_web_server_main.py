# -*- coding: utf-8 -*-
"""
diyapi_web_server_main.py

Receives HTTP requests and distributes data to backend processes over amqp.
"""
import gevent
from gevent import monkey
monkey.patch_all()

import sys

from gevent import wsgi
from gevent.event import Event

from diyapi_web_server.application import Application
from diyapi_web_server.amqp_handler import AMQPHandler


class WSGIServer(wsgi.WSGIServer):
    def __init__(self):
        super(WSGIServer, self).__init__(('', 8088), Application())


class WebServer(object):
    def __init__(self):
        self.wsgi_server = WSGIServer()
        self.amqp_handler = AMQPHandler()
        self._stopped_event = Event()

    def start(self):
        self._stopped_event.clear()
        self.wsgi_server.start()
        self.amqp_handler.start()

    def stop(self):
        self.amqp_handler.stop()
        self.wsgi_server.stop()
        self._stopped_event.set()

    def serve_forever(self):
        self.start()
        self._stopped_event.wait()


def main():
    WebServer().serve_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv))