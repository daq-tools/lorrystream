# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import pytest

from lorrystream.util.common import setup_logging

from .fixtures.amqp import rabbitmq, rabbitmq_service  # noqa: F401


@pytest.fixture
def cratedb(cratedb_service):
    cratedb_service.reset(
        [
            "testdrive-amqp",
            "testdrive-mqtt",
        ]
    )
    yield cratedb_service


setup_logging()
