# -*- coding: utf-8 -*-
"""
retrieve_key_start_reply.py

RetrieveKeyStartReply message
"""
from collections import namedtuple
import struct

from tools.marshalling import marshall_string, unmarshall_string
from diyapi_database_server import database_content

# 32s - request-id 32 char hex uuid
# B   - result: 0 = success 
# d   - timestamp
# ?   - is_tombstone
# B   - segment_number
# I   - segment size
# I   - segment count
# Q   - total_size
# L   - adler32
#16s  - md5 
_header_format = "!32sBd?BIIQL16s"
_header_size = struct.calcsize(_header_format)

_header_tuple =  namedtuple(
    "header", [
        "request_id",
        "result",
        "timestamp", 
        "is_tombstone", 
        "segment_number", 
        "segment_count",
        "segment_size", 
        "total_size", 
        "adler32",
        "md5"
    ]
)

class RetrieveKeyStartReply(object):
    """AMQP message to request retrieval of a key"""

    routing_tag = "retrieve_key_start_reply"
   
    successful = 0
    error_key_not_found = 1
    error_exception = 2
    error_database = 3
    error_invalid_duplicate = 4
    error_timeout_waiting_key_insert = 5

    def __init__(
        self, 
        request_id, 
        result, 
        timestamp = 0.0,
        is_tombstone = False,
        segment_number = 0,
        segment_count = 0,
        segment_size = 0,
        total_size = 0,
        adler32 = 0,
        md5 = "",
        data_content="",
        error_message=""
    ):
        self.request_id = request_id
        self.result = result
        self.timestamp = timestamp
        self.is_tombstone = is_tombstone
        self.segment_number = segment_number
        self.segment_count = segment_count
        self.segment_size = segment_size
        self.total_size = total_size
        self.adler32 = adler32
        self.md5 = md5
        self.data_content = data_content
        self.error_message = error_message

    @property
    def error(self):
        return self.result != RetrieveKeyStartReply.successful

    @classmethod
    def unmarshall(cls, data):
        """return a RetrieveKeyStartReply message"""
        pos = 0
        header = _header_tuple._make(struct.unpack(
            _header_format, data[pos:pos+_header_size]
        ))
        pos += _header_size

        if header.result == 0:
            return RetrieveKeyStartReply(                
                header.request_id, 
                header.result, 
                header.timestamp,
                header.is_tombstone,
                header.segment_number,
                header.segment_count,
                header.segment_size,
                header.total_size,
                header.adler32,
                header.md5,
                data_content=data[pos:]
            )

        (error_message, pos) = unmarshall_string(data, pos)

        return RetrieveKeyStartReply(
            request_id, result, error_message
        )

    def marshall(self):
        """return a data string suitable for transmission"""
        header = struct.pack(
            _header_format, 
            self.request_id, 
            self.result, 
            self.timestamp,
            self.is_tombstone,
            self.segment_number,
            self.segment_count,
            self.segment_size,
            self.total_size,
            self.adler32,
            self.md5
        )

        if self.result == 0:
            return "".join([header, self.data_content]) 

        packed_error_message = marshall_string(self.error_message)
         
        return "".join([header, packed_error_message, ])
