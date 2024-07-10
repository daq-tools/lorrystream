# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import asyncio
import json
import logging
import typing as t

import pika
import pytest
from testcontainer_python_rabbitmq import RabbitMQContainer

from lorrystream.core import ChannelFactory, Engine

capmqtt_decode_utf8 = True


logger = logging.getLogger(__name__)


class engine_single_shot:
    def __init__(self, *channels):
        self.engine = Engine()
        for channel in channels:
            self.engine.register(channel)

    async def __aenter__(self, *channels):
        logger.info("Starting engine")
        self.engine.start()
        logger.info("Engine started")
        await asyncio.sleep(0.25)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await asyncio.sleep(1.00)
        logger.info("Stopping engine")
        self.engine.stop()
        logger.info("Engine stopped")
        await asyncio.sleep(0.25)
        return False


@pytest.mark.asyncio_cooperative
async def test_amqp_to_sql(rabbitmq: t.Tuple[pika.BlockingConnection, RabbitMQContainer], cratedb):

    rabbitmq_container: RabbitMQContainer
    rabbitmq_connection: pika.BlockingConnection
    rabbitmq_container, rabbitmq_connection = rabbitmq

    amqp_host = rabbitmq_container.get_container_host_ip()
    amqp_port = rabbitmq_container.get_exposed_port(5672)
    amqp_url = f"amqp://guest:guest@{amqp_host}:{amqp_port}"
    database_url = cratedb.get_connection_url()

    channel = ChannelFactory(
        source=f"{amqp_url}/%2F?content-type=json&reconnect=false",
        sink=f"{database_url}/?table=testdrive-amqp",
    ).channel()

    reading = {"device": "foo", "temperature": 42.42, "humidity": 84.84}
    payload = bytes(json.dumps(reading), "utf-8")

    # Run machinery and publish reading.
    amqp_channel = rabbitmq_connection.channel()
    async with engine_single_shot(channel):
        amqp_channel.basic_publish(exchange="message", routing_key="example.text", body=payload)
        amqp_channel.basic_publish(exchange="message", routing_key="example.text", body=payload)
        rabbitmq_connection.process_data_events(0.01)

    # Validate data in storage system.
    cratedb.database.refresh_table("testdrive-amqp")
    assert cratedb.database.count_records("testdrive-amqp") == 2


@pytest.mark.asyncio_cooperative
async def test_mqtt_to_sql(mosquitto, cratedb, capmqtt):

    database_url = cratedb.get_connection_url()
    channel = ChannelFactory(
        source="mqtt://localhost/testdrive/%23?content-type=json",
        sink=f"{database_url}/?table=testdrive-mqtt",
    ).channel()

    reading = {"device": "foo", "temperature": 42.42, "humidity": 84.84}
    payload = json.dumps(reading)

    # Run machinery and publish reading.
    async with engine_single_shot(channel):
        capmqtt.publish("testdrive/readings", payload)
        capmqtt.publish("testdrive/readings", payload)

    # Validate data in storage system.
    cratedb.database.refresh_table("testdrive-mqtt")
    assert cratedb.database.count_records("testdrive-mqtt") == 2
