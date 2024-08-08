"""
Verify connectivity with Amazon Kinesis.

- https://en.wikipedia.org/wiki/Amazon_Kinesis
- https://docs.localstack.cloud/user-guide/aws/kinesis/
- https://docs.localstack.cloud/user-guide/tools/testing-utils/
"""

import logging
import time

logger = logging.getLogger(__name__)


def test_kinesis_stream_operations(localstack, boto3_session):
    kinesis = boto3_session.client("kinesis")

    kinesis.create_stream(StreamName="test", ShardCount=1)
    time.sleep(0.1)

    response = kinesis.list_streams()
    assert response["StreamNames"] == ["test"]
    time.sleep(0.1)
