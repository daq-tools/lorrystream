import dataclasses
import typing as t
from collections import OrderedDict

import boltons.urlutils
import paho.mqtt.client
from paho.mqtt.client import MQTTMessage
from pika import BasicProperties
from pika.spec import Basic, Channel
from streamz import Stream

Universal = t.Optional[t.Any]


@dataclasses.dataclass
class BusMessageConnection:
    stream: Universal = None

    # MQTT
    client: Universal = None

    # AMQP
    channel: Universal = None


@dataclasses.dataclass
class BusMessageData:
    # AMQP: basic_deliver, MQTT: `msg` modulo `payload`
    meta: Universal = None

    # AMQP: properties, MQTT: userdata
    headers: Universal = None

    # AMQP: body, MQTT: msg
    payload: Universal = None


@dataclasses.dataclass
class BusMessage:
    """
    AMQP:

    - channel
    - basic_deliver
    - properties: https://www.rabbitmq.com/publishers.html#message-properties
    - body

    MQTT

    - client
    - userdata
    - msg

    """

    connection: BusMessageConnection
    data: BusMessageData

    @classmethod
    def from_amqp_pika(
        cls,
        stream: Stream,
        channel: Channel,
        basic_deliver: Basic.Deliver,
        properties: BasicProperties,
        body: t.Union[str, bytes],
    ):
        """
        Construct a `BusMessage` instance from Pika's `on_message` callback information.

        :param stream: Streamz's `Stream` instance.
        :param channel: Pika's channel instance.
        :param basic_deliver: Pika's `Deliver` instance.
        :param properties: Pika's `BasicProperties` instance.
        :param body: Message payload.
        :return:
        """
        return BusMessage(
            connection=BusMessageConnection(
                stream=stream,
                channel=channel,
            ),
            data=BusMessageData(
                meta=cls._pika_delivery_to_dict(basic_deliver),
                headers=cls._pika_properties_to_dict(properties),
                payload=body,
            ),
        )

    @classmethod
    def from_mqtt_paho(
        cls, stream: Stream, client: paho.mqtt.client.Client, userdata: t.Dict, msg: paho.mqtt.client.MQTTMessage
    ):
        """
        Construct a `BusMessage` instance from Paho's `on_message` callback information.

        :param stream: Streamz's `Stream` instance.
        :param client: Paho's `Client` instance.
        :param userdata: Userdata alongside message.
        :param msg: Paho's `MQTTMessage` instance.
        :return:
        """
        return BusMessage(
            connection=BusMessageConnection(
                stream=stream,
                client=client,
            ),
            data=BusMessageData(
                meta=cls._paho_decode_metadata(msg),
                headers=userdata,
                payload=msg.payload,
            ),
        )

    @staticmethod
    def _pika_delivery_to_dict(basic_deliver) -> t.Dict:
        deliver_slots = ["consumer_tag", "delivery_tag", "redelivered", "exchange", "routing_key"]
        items = OrderedDict()
        for attr in deliver_slots:
            items[attr] = getattr(basic_deliver, attr)
        return items

    @staticmethod
    def _pika_properties_to_dict(properties) -> t.Dict:
        items = OrderedDict()
        for key, value in properties.__dict__.items():
            if getattr(properties.__class__, key, None) != value:
                items[key] = value
        return items

    @staticmethod
    def _paho_decode_metadata(msg: MQTTMessage) -> t.Dict:
        header_slots = ["timestamp", "state", "dup", "mid", "topic", "qos", "retain", "info"]
        items = OrderedDict()
        for slot in header_slots:
            items[slot] = getattr(msg, slot)
        return items


class URL(boltons.urlutils.URL):
    @property
    def path_unquoted(self):
        """The URL's path, in text form, not quoted."""
        return "/".join(self.path_parts)


boltons.urlutils.register_scheme("mqtt", uses_netloc=True, default_port=1883)
boltons.urlutils.register_scheme("mqtts", uses_netloc=True, default_port=8883)
