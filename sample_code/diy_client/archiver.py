# -*- coding: utf-8 -*-
"""
archiver.py

archive one file
"""
import hashlib
import hmac
import httplib
import logging
import os
import os.path
from cStringIO import StringIO
import time

from sample_code.diy_client.http_util import compute_authentication_string, \
        compute_uri, \
        current_timestamp

def archive_blob(config, message, body, send_queue):
    """
    archive a blob of data passed as an argument
    """
    assert type(body) == list, body
    assert len(body) == 1, body

    _archive(config, message, body[0], send_queue)

def archive_file(config, message, _body, send_queue):
    """
    archive a file of data passed as an argument
    """
    file_object = open(message["path"], "r")
    _archive(config, message, file_object, send_queue)
    file_object.close()

def _archive(config, message, body, send_queue):
    """
    If the body argument is present, it should be a string of data to send 
    after the headers are finished. Alternatively, it may be an open file 
    object, in which case the contents of the file is sent; 
    this file object should support fileno() and read() methods. 
    """
    log = logging.getLogger("_archive")

    connection = httplib.HTTPConnection(config["BaseAddress"])

    status_message = {
        "message-type"  : message["client-topic"],
        "status"        : "sending request",
        "error-message" : None,
        "completed"     : False,        
    }
    send_queue.put((status_message, None, ))

    method = "POST"
    timestamp = current_timestamp()
    uri = compute_uri(message["key"]) 
    authentication_string = compute_authentication_string(
        config["Username"], 
        config["AuthKey"],
        config["AuthKeyId"],
        method, 
        timestamp
    )
        
    authentification_string = compute_authentication_string(
        config, 
        method, 
        timestamp
    )

    headers = {
        "Authorization"         : authentification_string,
        "X-DIYAPI-Timestamp"    : str(timestamp),
        "agent"                 : 'diy-tool/1.0'
    }

    log.info("uri = '%s'" % (uri, ))
    connection.request(method, uri, body=body, headers=headers)

    response = connection.getresponse()
    response.read()
    connection.close()

    status_message = {
        "message-type"  : message["client-topic"],
        "status"        : None,
        "error-message" : None,
        "completed"     : True,        
    }

    if response.status == httplib.OK:
        status_message["status"] = "OK"
        log.info("archvie successful")
    else:
        message = "request failed %s %s" % (response.status, response.reason, ) 
        log.warn(message)
        status_message["status"] = "error"
        status_message["error-message"] = message

    send_queue.put((status_message, None, ))
        
