import os
import typing as t

import pika
import pytest
from _pytest.fixtures import FixtureRequest
from cratedb_toolkit.testing.testcontainers.util import KeepaliveContainer
from testcontainers.rabbitmq import RabbitMqContainer

from lorrystream.util.data import asbool


class RabbitMQContainerPlus(KeepaliveContainer, RabbitMqContainer):
    KEEPALIVE = asbool(os.environ.get("CRATEDB_KEEPALIVE", os.environ.get("TC_KEEPALIVE", False)))

    def _configure(self) -> None:
        self.with_name("testcontainers-rabbitmq")


@pytest.fixture
def rabbitmq_service(request: FixtureRequest) -> t.Tuple[RabbitMqContainer, pika.BlockingConnection]:
    container = RabbitMQContainerPlus(image="docker.io/rabbitmq:4")
    container.start()
    container.readiness_probe()
    connection = pika.BlockingConnection(container.get_connection_params())
    return container, connection


@pytest.fixture
def rabbitmq(rabbitmq_service) -> t.Tuple[RabbitMqContainer, pika.BlockingConnection]:
    _, connection = rabbitmq_service
    channel = connection.channel()
    channel.queue_delete("t-queue")
    channel.exchange_delete("t-exchange")
    connection.process_data_events(0.01)
    channel.close()
    return rabbitmq_service
