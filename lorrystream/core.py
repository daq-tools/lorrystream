# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import asyncio
import json
import logging
import operator
import typing as t

from streamz import Sink, Source, Stream
from streamz.batch import Batch

from lorrystream.exceptions import InvalidContentTypeError, InvalidSinkError, InvalidSourceError
from lorrystream.model import Channel, Packet, SinkInputType, StreamAddress
from lorrystream.streamz.model import BusMessage
from lorrystream.util.data import get_sqlalchemy_dialects

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
        return Packet(payload=json.loads(msg.payload), busmsg=msg)

    @staticmethod
    def decode_mqtt(msg):
        """
        Decode `MQTTMessage` object into `Packet` object.
        """
        return Packet(payload=json.loads(msg.payload), busmsg=msg)

    @staticmethod
    def decode_busmessage(busmsg: BusMessage):
        """
        Decode `BusMessage` object into `Packet` object.
        """
        return Packet(payload=busmsg.data.payload, busmsg=busmsg)

    @staticmethod
    def decode_json(packet: Packet):
        """
        Decode `MQTTMessage` object into `Packet` object.
        """
        packet.payload = json.loads(packet.payload)
        return packet

    @staticmethod
    def decode_busmessage_json(busmsg: BusMessage):
        """
        Decode `BusMessage` object into `Packet` object.
        """
        if busmsg.data.payload is None:
            return None
        return Packet(payload=json.loads(busmsg.data.payload), busmsg=busmsg)


class ChannelFactory:
    def __init__(self, source: str, sink: SinkInputType):
        self.source_element: Source = None
        self.sink_element: t.Union[Sink, t.Callable] = None
        self.transformers: t.List[t.Callable] = []
        self.pipeline: t.Union[Batch, Stream] = None

        # FIXME: Obtain parameters from user.
        self.batch_size = 2
        self.timeout = 0.25

        # When no sink is specified, use STDOUT.
        # TODO: How to use `sys.stdout.buffer.write` instead?
        if sink is None:
            sink = print

        self.source_address = StreamAddress.from_url(source)
        self.sink_address = StreamAddress.resolve_sink(sink)

        # Select source element for pipeline.
        self.select_source(source)

        # Create first half of pipeline.
        self.mkpipeline()

        # Select sink element for pipeline.
        self.select_sink(sink)

    def select_source(self, location: str):
        """
        Select source element of pipeline.
        """
        uri = self.source_address.uri
        if uri.scheme.startswith("amqp"):
            logger.info("Subscribing to AMQP")
            self.source_element = Stream.from_amqp(str(uri))
            self.transformers.append(Decoders.decode_busmessage)

        elif uri.scheme.startswith("mqtt"):
            self.source_element = Stream.from_mqtt_plus(uri)
            self.transformers.append(Decoders.decode_busmessage)

        else:
            raise InvalidSourceError(f"Source scheme unknown: {uri.scheme}")

        if "content-type" in self.source_address.options:
            source_content_type = self.source_address.options["content-type"]
            if source_content_type == "json":
                self.transformers.append(Decoders.decode_json)
            else:
                raise InvalidContentTypeError(f"Invalid content type for source '{uri}': {source_content_type}")

    def mkpipeline(self):
        """
        n: int
            Maximum partition size
        timeout: int or float, optional
            Number of seconds after which a partition will be emitted,
            even if its size is less than ``n``. If ``None`` (default),
            a partition will be emitted only when its size reaches ``n``.
        """
        self.pipeline = self.source_element.partition(n=self.batch_size, timeout=self.timeout).to_batch()
        for transformer in self.transformers:
            self.pipeline = self.pipeline.map(transformer)

    def select_sink(self, location: SinkInputType):
        """
        Select sink element of pipeline.
        """
        db_dialects = get_sqlalchemy_dialects()
        uri = self.sink_address.uri

        if uri.scheme.startswith("callable"):
            self.sink_element = self.pipeline.stream.sink(location)

        elif uri.scheme in db_dialects:
            # TODO: Weave in more sophisticated transformations here,
            #       like topic/topology/storage convergence from Kotori.
            self.pipeline = self.pipeline.map(operator.attrgetter("payload")).to_dataframe()

            self.sink_element = self.pipeline.stream.dataframe_to_sql(dburi=str(self.sink_address.uri))
        else:
            raise InvalidSinkError(f"Invalid sink location: {location}")

    def transform(self, thing: t.Callable) -> "ChannelFactory":
        self.transformers.append(thing)
        return self

    def channel(self) -> Channel:
        """
        Produce `Channel` object from elements.
        """
        return Channel(source=self.source_element, pipeline=self.pipeline, sink=self.sink_element)


class Engine:
    def __init__(self):
        self.channels: t.Dict[str, Channel] = {}
        self._terminate_event = asyncio.Event()

    def register(self, channel: Channel):
        logger.info(f"Registering channel: {channel}")
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
