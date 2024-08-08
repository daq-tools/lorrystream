# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import pytest

from lorrystream.util.common import setup_logging

from .fixtures.amqp import rabbitmq, rabbitmq_service  # noqa: F401
from .fixtures.localstack import boto3_configure_localstack, boto3_session, localstack, localstack_service  # noqa: F401


@pytest.fixture
def cratedb(cratedb_service):
    cratedb_service.reset(
        [
            "public.foo",
            "testdrive-amqp",
            "testdrive-dynamodb-cdc",
            "testdrive-mqtt",
        ]
    )
    yield cratedb_service


setup_logging()
