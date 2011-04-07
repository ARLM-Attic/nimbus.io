# -*- coding: utf-8 -*-
"""
util.py

utility functions for unit tests
"""
import logging
import time
import os
import os.path
import subprocess
import sys

from diyapi_database_server import database_content

def random_string(size):
    with open('/dev/urandom', 'rb') as f:
        return f.read(size)

def generate_key():
    """generate a unique key for data storage"""
    n = 0
    while True:
        n += 1
        yield "test-key-%06d" % (n, )

def generate_database_content(
    timestamp=time.time(), version_number=0, segment_number=1
):
    return database_content.factory(
        timestamp=timestamp, 
        is_tombstone=False,  
        version_number=version_number,
        segment_number=segment_number,  
        segment_size=42,  
        segment_count=1,
        total_size=4200,  
        file_adler32=345, 
        file_md5='\x936\xeb\xf2P\x87\xd9\x1c\x81\x8e\xe6\xe9\xec)\xf8\xc1',
        segment_adler32=123, 
        segment_md5="1111111111111111",
        file_name="aaa"
    )

def identify_program_dir(target_dir):
    python_path = os.environ["PYTHONPATH"]
    for work_path in python_path.split(os.pathsep):
        test_path = os.path.join(work_path, target_dir)
        if os.path.isdir(test_path):
            return test_path

    raise ValueError(
        "Can't find %s in PYTHONPATH '%s'" % (target_dir, python_path, )
    )

def poll_process(process):
    process.poll()
    if process.returncode is None:
        return None

    return (process.returncode, process.stderr.read(), )

def terminate_process(process):
    process.terminate()
    process.wait()
    if process.returncode != 0:
        print >> sys.stderr, " "
        print >> sys.stderr, "-" * 15
        print >> sys.stderr, process.returncode
        print >> sys.stderr, process.stderr.read()
        print >> sys.stderr, "-" * 15
        print >> sys.stderr, process.returncode
    assert process.returncode == 0, \
        process.returncode

def start_database_server(node_name, address, repository_path):
    log = logging.getLogger("start_database_server_%s" % (node_name, ))
    server_dir = identify_program_dir(u"diyapi_database_server")
    server_path = os.path.join(server_dir, "diyapi_database_server_main.py")
    
    args = [
        sys.executable,
        server_path,
    ]

    environment = {
        "PYTHONPATH"                        : os.environ["PYTHONPATH"],
        "SPIDEROAK_MULTI_NODE_NAME"         : node_name,
        "DIYAPI_DATABASE_SERVER_ADDRESS"    : address,
        "DIYAPI_REPOSITORY_PATH"            : repository_path,
    }        

    log.info("starting %s %s" % (args, environment, ))
    return subprocess.Popen(args, stderr=subprocess.PIPE, env=environment)

def start_data_writer(
    node_name, address, database_server_address, repository_path
):
    log = logging.getLogger("start_data_writer_%s" % (node_name, ))
    server_dir = identify_program_dir(u"diyapi_data_writer")
    server_path = os.path.join(server_dir, "diyapi_data_writer_main.py")
    
    args = [
        sys.executable,
        server_path,
    ]

    environment = {
        "PYTHONPATH"                        : os.environ["PYTHONPATH"],
        "SPIDEROAK_MULTI_NODE_NAME"         : node_name,
        "DIYAPI_DATA_WRITER_ADDRESS"        : address,
        "DIYAPI_DATABASE_SERVER_ADDRESS"    : database_server_address,
        "DIYAPI_REPOSITORY_PATH"            : repository_path,
    }        

    log.info("starting %s %s" % (args, environment, ))
    return subprocess.Popen(args, stderr=subprocess.PIPE, env=environment)

def start_data_reader(
    node_name, address, database_server_address, repository_path
):
    log = logging.getLogger("start_data_reader_%s" % (node_name, ))
    server_dir = identify_program_dir(u"diyapi_data_reader")
    server_path = os.path.join(server_dir, "diyapi_data_reader_main.py")
    
    args = [
        sys.executable,
        server_path,
    ]

    environment = {
        "PYTHONPATH"                        : os.environ["PYTHONPATH"],
        "SPIDEROAK_MULTI_NODE_NAME"         : node_name,
        "DIYAPI_DATA_READER_ADDRESS"        : address,
        "DIYAPI_DATABASE_SERVER_ADDRESS"    : database_server_address,
        "DIYAPI_REPOSITORY_PATH"            : repository_path,
    }        

    log.info("starting %s %s" % (args, environment, ))
    return subprocess.Popen(args, stderr=subprocess.PIPE, env=environment)

def start_anti_entropy_server(node_name, address, database_server_addresses):
    log = logging.getLogger("_start_anti_entropy_server%s" % (node_name, ))
    server_dir = identify_program_dir(u"diyapi_anti_entropy_server")
    server_path = os.path.join(
        server_dir, "diyapi_anti_entropy_server_main.py"
    )
    
    args = [
        sys.executable,
        server_path,
    ]

    environment = {
        "PYTHONPATH"                        : os.environ["PYTHONPATH"],
        "SPIDEROAK_MULTI_NODE_NAME"         : node_name,
        "DIYAPI_ANTI_ENTROPY_SERVER_ADDRESS": address,
        "DIYAPI_DATABASE_SERVER_ADDRESSES"  : \
            " ".join(database_server_addresses),
        "PANDORA_DB_PW_pandora_storage_server" : \
            os.environ["PANDORA_DB_PW_pandora_storage_server"],
    }        

    log.info("starting %s %s" % (args, environment, ))
    return subprocess.Popen(args, stderr=subprocess.PIPE, env=environment)

def start_space_accounting_server(node_name, address, pipeline_address):
    log = logging.getLogger("_start_space_accounting_server%s" % (node_name, ))
    server_dir = identify_program_dir(u"diyapi_space_accounting_server")
    server_path = os.path.join(
        server_dir, "diyapi_space_accounting_server_main.py"
    )
    
    args = [
        sys.executable,
        server_path,
    ]

    environment = {
        "PYTHONPATH"                        : os.environ["PYTHONPATH"],
        "SPIDEROAK_MULTI_NODE_NAME"         : node_name,
        "PANDORA_DB_PW_pandora_storage_server" : \
            os.environ["PANDORA_DB_PW_pandora_storage_server"],
        "DIYAPI_SPACE_ACCOUNTING_SERVER_ADDRESS" : address,
        "DIYAPI_SPACE_ACCOUNTING_PIPELINE_ADDRESS" : pipeline_address,
    }        

    log.info("starting %s %s" % (args, environment, ))
    return subprocess.Popen(args, stderr=subprocess.PIPE, env=environment)

