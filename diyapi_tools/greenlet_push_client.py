# -*- coding: utf-8 -*-
"""
greenlet_push_client.py

a class that manages a zeromq PUSH socket as a client,
The purpose is to have multiple clients pushing to a single PULL server
"""
from collections import namedtuple
import logging

from gevent_zeromq import zmq

_message_format = namedtuple("Message", "control body")

class GreenletPUSHClient(object):
    """
    a class that manages a zeromq PUSH socket as a client,
    The purpose is to have multiple clients pushing to a single PULL server
    """
    def __init__(self, context, node_name, address):
        self._log = logging.getLogger("PUSHClient-%s" % (node_name, ))

        self._push_socket = context.socket(zmq.PUSH)
        self._log.debug("connecting to%s" % (address, ))
        self._push_socket.connect(address)

    def close(self):
        self._push_socket.close()

    def send(self, message, data=None):
        self._log.info("sending message: %s" % (
            message.control,  
        ))
        if data is not None:
            self._push_socket.send_json(message, zmq.SNDMORE)
            self._push_socket.send(data, copy=False)
        else:
            self._push_socket.send_json(message)
