import os
import socket
import time

import boto3
import botocore
import pytest
from localstack_utils.localstack import startup_localstack, stop_localstack

from lorrystream.util.data import asbool

TEST_STREAMS = [
    "test",
    "testdrive",
]


def isUp(host, port):
    """
    Test if a host is up.

    https://github.com/lovelysystems/lovely.testlayers/blob/0.7.0/src/lovely/testlayers/util.py#L6-L13
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ex = s.connect_ex((host, port))
    if ex == 0:
        s.close()
        return True
    return False


@pytest.fixture(scope="session")
def localstack_service():
    if not isUp("localhost", 4566):
        startup_localstack(tag="3.6")
    yield
    if not asbool(os.environ.get("TC_KEEPALIVE")):
        stop_localstack()


@pytest.fixture(scope="function")
def localstack(localstack_service):
    kinesis = boto3.client(
        service_name="kinesis",
        endpoint_url="http://localhost:4566",
    )
    for stream_name in TEST_STREAMS:
        try:
            kinesis.delete_stream(StreamName=stream_name)
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
    time.sleep(0.5)
