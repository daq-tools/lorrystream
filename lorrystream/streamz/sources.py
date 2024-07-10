# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of a BSD-3-Clause license, see LICENSE.
import asyncio
import logging
import queue
import typing as t
from collections import OrderedDict

from streamz import Stream, from_mqtt, from_q

from lorrystream.streamz.amqp import ReconnectingExampleConsumer
from lorrystream.streamz.amqp_blocking import AMQPAdapter
from lorrystream.streamz.model import URL, BusMessage, BusMessageConnection, BusMessageData
from lorrystream.util.aio import AsyncThreadTask

logger = logging.getLogger(__name__)


@Stream.register_api()
class FromAmqp(from_q):
    """Read from AMQP source

    See https://en.wikipedia.org/wiki/AMQP for a description of the protocol
    and its uses.

    TODO: See also ``sinks.to_amqp``.

    Requires ``pika``

    The outputs are ``paho.mqtt.client.MQTTMessage`` instances, which each have
    attributes timestamp, payload, topic, ...

    NB: paho.mqtt.python runs on its own thread in this implementation. We may
    wish to instead call client.loop() directly

    - https://www.rabbitmq.com/uri-spec.html
    - https://www.rabbitmq.com/uri-query-parameters.html

    :param host: str
    :param port: int
    :param topic: str
        (May in the future support a list of topics)
    :param keepalive: int
        See mqtt docs - to keep the channel alive
    :param client_kwargs:
        Passed to the client's ``connect()`` method
    """

    def __init__(self, uri: str, reconnect: bool = True, **kwargs):
        self.uri = uri
        self.stopped = True
        consumer_class: t.Callable = ExampleConsumer
        if reconnect:
            consumer_class = ReconnectingExampleConsumer
        self.consumer = consumer_class(self.uri, on_message=self._on_message)
        super().__init__(q=queue.Queue(), **kwargs)

    def _delivery_to_dict(self, basic_deliver):
        deliver_attrs = ["consumer_tag", "delivery_tag", "redelivered", "exchange", "routing_key"]
        items = OrderedDict()
        for attr in deliver_attrs:
            items[attr] = getattr(basic_deliver, attr)
        return items

    def _properties_to_dict(self, properties):
        items = OrderedDict()
        for key, value in properties.__dict__.items():
            if getattr(properties.__class__, key, None) != value:
                items[key] = value
        return items

    def _on_message(self, channel, basic_deliver, properties, body):
        busmsg = BusMessage.from_amqp_pika(self, channel, basic_deliver, properties, body)
        self.q.put(busmsg)

    async def run(self):
        AsyncThreadTask(self.consumer.run).run()
        await super().run()

    def stop(self):
        # TODO: Does not work with CTRL+C yet. Validate if it works on other occasions at least.
        if not self.stopped:
            self.consumer.stop()
            self.consumer = None
            self.stopped = True
        super().stop()


@Stream.register_api()
class FromMqttPlus(from_mqtt):
    def __init__(self, uri: URL, client_kwargs=None, **kwargs):
        host = uri.host or "localhost"
        port = uri.port or uri.default_port
        topic = uri.path_unquoted.lstrip("/")
        logger.info(f"Subscribing to MQTT topic '{topic}' at broker on '{host}")
        super().__init__(host, port, topic, keepalive=60, client_kwargs=client_kwargs, **kwargs)

    def _on_message(self, client, userdata, msg):
        busmsg = BusMessage.from_mqtt_paho(self, client, userdata, msg)
        self.q.put(busmsg)


from_amqp = FromAmqp
from_mqtt_plus = FromMqttPlus
