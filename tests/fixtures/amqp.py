import os
import typing as t

import pika
import pytest
from _pytest.fixtures import FixtureRequest
from cratedb_toolkit.testing.testcontainers.util import KeepaliveContainer
from testcontainer_python_rabbitmq import RabbitMQContainer

from lorrystream.util.data import asbool


class RabbitMQContainerPlus(KeepaliveContainer, RabbitMQContainer):
    KEEPALIVE = asbool(os.environ.get("CRATEDB_KEEPALIVE", os.environ.get("TC_KEEPALIVE", False)))

    def _configure(self) -> None:
        self.with_name("testcontainers-rabbitmq")


@pytest.fixture
def rabbitmq_service(request: FixtureRequest) -> t.Generator[RabbitMQContainer, None, None]:
    config = RabbitMQContainerPlus()
    credentials = pika.PlainCredentials(username="guest", password="guest")  # noqa: S106
    with config as container:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=container.get_container_host_ip(),
                port=container.get_amqp_port(),
                credentials=credentials,
            )
        )
        yield container, connection


@pytest.fixture
def rabbitmq(rabbitmq_service) -> t.Generator[RabbitMQContainer, None, None]:
    _, connection = rabbitmq_service
    channel = connection.channel()
    channel.queue_delete("t-queue")
    channel.exchange_delete("t-exchange")
    connection.process_data_events(0.01)
    channel.close()
    yield rabbitmq_service
