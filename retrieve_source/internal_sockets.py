# -*- coding: utf-8 -*-
"""
internal_sockets.py

addresses of sockets used internally by retrieve_source
external addresses come from environment variables
"""
import os

from tools.zeromq_util import ipc_socket_uri

_local_node_name = os.environ["NIMBUSIO_NODE_NAME"]
_socket_dir = os.environ["NIMBUSIO_SOCKET_DIR"]

db_controller_pull_socket_uri = ipc_socket_uri(_socket_dir,
                                               _local_node_name,
                                               "db_controller_pull")

db_controller_router_socket_uri = ipc_socket_uri(_socket_dir,
                                               _local_node_name,
                                               "db_controller_router")

io_controller_pull_socket_uri = ipc_socket_uri(_socket_dir,
                                               _local_node_name,
                                               "io_controller_pull")

io_controller_router_socket_uri = ipc_socket_uri(_socket_dir,
                                               _local_node_name,
                                               "io_controller_router")

internal_socket_uri_list = [db_controller_pull_socket_uri, 
                            db_controller_router_socket_uri,
                            io_controller_router_socket_uri,
                            io_controller_router_socket_uri, ]


