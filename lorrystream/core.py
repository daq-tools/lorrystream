# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import asyncio
import json
import logging
import operator
import typing as t

from streamz import Source, from_mqtt
from yarl import URL

from lorrystream.exceptions import InvalidSourceError
from lorrystream.model import Channel, Packet

logger = logging.getLogger(__name__)


async def run_single(source_uri: str, sink_uri: str):
    """
    Create a single channel and run it on the engine, blocking forever.

    :param source_uri: Source element URI
    :param sink_uri: Sink element URI
    :return:
    """

    # Create channel.
    channel = ChannelFactory(source=source_uri, sink=sink_uri).channel()

    # Run channel with engine.
    engine = Engine()
    engine.register(channel)
    await engine.run_forever()


async def run_channels(*channels: Channel):
    """
    Obtain multiple channel objects and run them on the engine, blocking forever.

    :param channels: List of channel objects
    :return:
    """
    engine = Engine()
    for channel in channels:
        engine.register(channel)
    await engine.run_forever()


class Decoders:
    @staticmethod
    def decode_mqtt_json(msg):
        """
        Decode `MQTTMessage` object into `Packet` object.
        """
        return Packet(payload=json.loads(msg.payload), original=msg)


class ChannelFactory:
    def __init__(self, source: str, sink: t.Union[str, t.Callable]):
        self.source: Source
        self.sink: t.Union[None, t.Callable]

        self.source_uri = URL(source)
        if callable(sink):
            self.sink_uri = URL(f"callable://{sink.__name__}")
        else:
            self.sink_uri = URL(sink)

        self.transformers: t.List[t.Callable] = []

        # FIXME
        if self.source_uri.scheme.startswith("mqtt"):
            host = self.source_uri.host or "localhost"
            port = self.source_uri.port or 1883
            topic = self.source_uri.path.lstrip("/")
            logger.info(f"Subscribing to MQTT topic: {topic}")
            self.source = from_mqtt(host, port, topic)
            self.transformers.append(Decoders.decode_mqtt_json)
        else:
            raise InvalidSourceError(f"Source scheme unknown: {self.source_uri.scheme}")

        if callable(sink):
            self.sink = sink
        else:
            self.sink = None

        self.batch_size = 2
        self.timeout = 0.25

    def transform(self, thing: t.Callable):
        self.transformers.append(thing)
        return self

    def channel(self) -> Channel:
        """
        n: int
            Maximum partition size
        timeout: int or float, optional
            Number of seconds after which a partition will be emitted,
            even if its size is less than ``n``. If ``None`` (default),
            a partition will be emitted only when its size reaches ``n``.
        """
        pipeline = self.source.partition(n=self.batch_size, timeout=self.timeout).to_batch()
        for transformer in self.transformers:
            pipeline = pipeline.map(transformer)

        # Connect with sink.
        if self.sink is None:
            # TODO: Not only handle SQL, but also other sinks.
            # TODO: Determine if `self.sink_uri.scheme` is one of SQLAlchemy's supported ones.
            pipeline = pipeline.map(operator.attrgetter("payload"))
            pipeline = pipeline.to_dataframe()
            pipeline.stream.dataframe_to_sql(dburi=str(self.sink_uri))
        else:
            if callable(self.sink):
                pipeline.stream.sink(self.sink)

        channel = Channel(source=self.source, pipeline=pipeline, sink=self.sink)
        return channel


class Engine:
    def __init__(self):
        self.channels: t.Dict[str, Channel] = {}
        self._terminate_event = asyncio.Event()

    def register(self, channel: Channel):
        logger.info(f"Registering channel {channel}")
        # FIXME: The registry is currently a bit naive.
        name = str(channel.source)
        self.channels[name] = channel

    def start(self):
        for name, channel in self.channels.items():
            logger.info(f"Starting channel {name}")
            channel.source.start()

    def stop(self):
        for channel in self.channels.values():
            logger.info(f"Stopping channel {channel}")
            channel.source.stop()

    def terminate(self):
        self._terminate_event.set()

    async def run_forever(self):
        # Start engine.
        self.start()
        # Wait forever.
        await self._terminate_event.wait()
