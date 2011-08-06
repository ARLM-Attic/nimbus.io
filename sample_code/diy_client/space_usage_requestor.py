# -*- coding: utf-8 -*-
"""
space_usage_requestor.py

request space usage
"""
import os.path
import logging

from sample_code.diy_client.http_connection import HTTPConnection, \
        HTTPRequestError

def request_space_usage(config, message, _body, send_queue):
    """
    request space usage
    """
    log = logging.getLogger("request_space_usage")

    status_message = {
        "message-type"  : message["client-topic"],
        "status"        : None,
        "error-message" : None,
        "space-usage"   : None,
        "completed"     : True,        
    }

    connection = HTTPConnection(
        config["BaseAddress"],
        config["Username"], 
        config["AuthKey"],
        config["AuthKeyId"]
    )

    method = "GET"
    uri = os.path.join(os.sep, "usage") 

    try:
        response = connection.request(method, uri)
    except HTTPRequestError, instance:
        status_message["status"] = "error"
        status_message["error-message"] = str(instance)
        connection.close()
        send_queue.put((status_message, None, ))
        return
    else:
        data = response.read()
    finally:
        connection.close()

    status_message["status"] = "OK"
    status_message["space-usage"] = data
    log.info("space usage successful %s" % (data, ))
    send_queue.put((status_message, None, ))
        