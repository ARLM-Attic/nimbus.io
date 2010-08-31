# -*- coding: utf-8 -*-
"""
anti_entropy_audit_reply.py

AntiEntropyAuditReply message
"""
import struct

from diyapi_tools.marshalling import marshall_string, unmarshall_string

# 32s - request-id 32 char hex uuid
#   B - result successful = 0
_header_format = "32sB"
_header_size = struct.calcsize(_header_format)

class AntiEntropyAuditReply(object):
    """AMQP message returning a list of known avatars from the database"""

    routing_tag = "anti_entropy_audit_reply"

    successful = 0
    audit_error = 1
    other_error = 2
   
    def __init__(self, request_id, result, error_message=""):
        self.request_id = request_id
        self.result = result
        self.error_message = error_message

    @property
    def error(self):
        return self.result != AntiEntropyAuditReply.successful

    @classmethod
    def unmarshall(cls, data):
        """return a AntiEntropyAuditReply message"""
        pos = 0
        (request_id, result, ) = struct.unpack(
            _header_format, data[pos:pos+_header_size]
        )
        pos += _header_size
        if result == 0:
            error_message = ""
        else:
            (error_message, pos) = unmarshall_string(data, pos)

        message = AntiEntropyAuditReply(
            request_id, result, error_message
        )
        return message

    def marshall(self):
        """return a data string suitable for transmission"""
        header = struct.pack(
            _header_format, 
            self.request_id,
            self.result
        )
        if self.result == 0:
            packed_error_message = ""
        else:
            packed_error_message = marshall_string(self.error_message)

        return "".join([header, packed_error_message, ])
