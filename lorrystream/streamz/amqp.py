# Copyright (c) 2009-2021, Tony Garnock-Jones, Gavin M. Roy, Pivotal Software, Inc and others.
# All rights reserved. Distributed under the terms of a BSD-3-Clause license, see LICENSE.
#
# Derived from:
# https://github.com/pika/pika/blob/1.3.1/examples/asyncio_consumer_example.py

# pylint: disable=C0111,C0103,R0205

import functools
import logging
import time
import typing as t

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.exchange_type import ExchangeType

from lorrystream.model import StreamAddress

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class AMQPAdapter:
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, this class will stop and indicate
    that reconnection is necessary. You should look at the output, as
    there are limited reasons why the connection may be closed, which
    usually are tied to permission related issues or socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """

    def __init__(self, address: StreamAddress, on_message: t.Callable = None):
        """
        Create and maintain a connection to an AMQP broker.
        """
        LOGGER.info('Creating consumer')

        self.address = address

        if "queue" not in self.address.options:
            raise ValueError("Consuming from AMQP requires a queue name")

        self.queue_name = self.address.options["queue"]
        self.exchange_name = self.address.options.get("exchange", "")
        self.exchange_type = self.address.options.get("exchange-type", "direct")
        self.routing_key = self.address.options.get("routing-key")

        self.should_reconnect = False
        self.was_consuming = False

        self._connection: AsyncioConnection
        self._channel: Channel
        self._closing = False
        self._consumer_tag: str
        self._consuming = False
        # In production, experiment with higher prefetch values
        # for higher consumer throughput
        self._prefetch_count = 1_000

        self.deliver_message = on_message

    def needs_setup(self, key: str):
        """
        Whether the URL query parameter ``setup={exchange,queue,bind}`` was specified.
        """
        if "setup" in self.address.options:
            setup = self.address.options["setup"]
            return key in setup
        return False

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.adapters.asyncio_connection.AsyncioConnection

        """
        LOGGER.info('Connecting to %s', self.address.uri)
        return AsyncioConnection(
            parameters=pika.URLParameters(str(self.address.uri)),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed)

    def close_connection(self):
        self._consuming = False
        if self._connection.is_closing or self._connection.is_closed:
            LOGGER.info('Connection is closing or already closed')
        else:
            LOGGER.info('Closing connection')
            self._connection.close()

    def on_connection_open(self, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :param pika.adapters.asyncio_connection.AsyncioConnection _unused_connection:
           The connection

        """
        LOGGER.info('Connection opened')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        """This method is called by pika if the connection to RabbitMQ
        can't be established.

        :param pika.adapters.asyncio_connection.AsyncioConnection _unused_connection:
           The connection
        :param Exception err: The error

        """
        LOGGER.error('Connection open failed: %s', err)
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.

        """
        del self._channel
        if self._closing:
            LOGGER.info('Connection closed, stopping i/o loop')
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reconnect necessary: %s', reason)
            self.reconnect()

    def reconnect(self):
        """Will be invoked if the connection can't be opened or is
        closed. Indicates that a reconnect is necessary then stops the
        ioloop.

        """
        LOGGER.info('Signalling reconnect')
        self.should_reconnect = True
        self.stop()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll may declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        LOGGER.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange()

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param Exception reason: why the channel was closed

        """
        LOGGER.warning('Channel %i was closed: %s', channel, reason)
        self.close_connection()

    def setup_exchange(self):
        """Set up the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.
        """
        # Note: using functools.partial is not required, it is demonstrating
        # how arbitrary data can be passed to the callback when it is called
        if self.needs_setup("exchange"):
            LOGGER.info('Declaring exchange: %s', self.exchange_name)
            cb = functools.partial(
                self.on_exchange_declareok, userdata=self.exchange_name)
            self._channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type=ExchangeType(self.exchange_type),
                callback=cb)
        else:
            self.setup_queue()

    def on_exchange_declareok(self, _unused_frame, userdata):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame
        :param str|unicode userdata: Extra user data (exchange name)

        """
        LOGGER.info('Exchange declared: %s', userdata)
        self.setup_queue()

    def setup_queue(self):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        """
        if self.needs_setup("queue"):
            LOGGER.info('Declaring queue %s', self.queue_name)
            cb = functools.partial(self.on_queue_declareok, userdata=self.queue_name)
            self._channel.queue_declare(queue=self.queue_name, callback=cb)
        else:
            self.setup_bind()

    def on_queue_declareok(self, _unused_frame, userdata):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. We may advance to binding that queue.

        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        LOGGER.info('Queue declared: %s', self.queue_name)
        self.setup_bind()

    def setup_bind(self):
        """
        Bind the queue and exchange together with the routing key, by issuing
        the Queue.Bind RPC command. When this command is complete, the
        on_bindok method will be invoked by pika.
        :return:
        """
        if self.needs_setup("bind"):
            LOGGER.info(
                "Binding queue '%s' to exchange '%s' with routing key '%s'",
                self.queue_name, self.exchange_name, self.routing_key
            )
            if self.routing_key is None:
                raise ValueError("When binding a queue, the routing key is required")
            cb = functools.partial(self.on_bindok, userdata=self.queue_name)
            self._channel.queue_bind(
                self.queue_name,
                self.exchange_name,
                routing_key=self.routing_key,
                callback=cb)
        else:
            self.subscribe()

    def on_bindok(self, _unused_frame, userdata):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point, we will advance to actually consume messages.

        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
        :param str|unicode userdata: Extra user data (queue name)

        """
        LOGGER.info('Queue bound: %s', userdata)
        self.subscribe()

    def subscribe(self):
        """
        Actually start consuming messages, after setting the prefetch size for this channel.
        """
        LOGGER.info('Subscribing')
        self.set_qos()

    def set_qos(self):
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.

        """
        LOGGER.info('Setting QOS to: %d', self._prefetch_count)
        self._channel.basic_qos(
            prefetch_count=self._prefetch_count, callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point, we will start consuming messages.

        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame

        """
        LOGGER.info('QOS set to: %d', self._prefetch_count)
        self.start_consuming()

    def start_consuming(self):
        """Start consuming messages.

        This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        LOGGER.info('Start consuming')
        self._consumer_tag = self._channel.basic_consume(
            self.queue_name, self.on_message)
        self._consuming = True

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, _unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel _unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param bytes body: The message body

        """
        self.was_consuming = True
        LOGGER.info('Received message # %s from %s: %s',
                    basic_deliver.delivery_tag, properties.app_id, body)
        if self.deliver_message:
            self.deliver_message(_unused_channel, basic_deliver, properties, body)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            cb = functools.partial(
                self.on_cancelok, userdata=self._consumer_tag)
            self._channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)

        """
        self._consuming = False
        LOGGER.info(
            'RabbitMQ acknowledged the cancellation of the consumer: %s',
            userdata)
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        LOGGER.info('Closing the channel')
        self._channel.close()

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the AsyncioConnection to operate.

        """
        LOGGER.info('Starting consumer')
        self._connection = self.connect()
        self._connection.ioloop.run_forever()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        if not self._closing:
            self._closing = True
            LOGGER.info('Stopping consumer')
            if self._consuming:
                self.stop_consuming()
                # TODO: Is this wrong on the original?
                # self._connection.ioloop.run_forever()  # noqa: ERA001
                self._connection.ioloop.stop()
            else:
                self._connection.ioloop.stop()
            LOGGER.info('Stopped consumer')


class ReconnectingAMQPAdapter:
    """This is an example consumer that will reconnect if the nested
    AMQPAdapter indicates that a reconnect is necessary.

    """

    def __init__(self, address: StreamAddress, on_message: t.Callable = None):
        self.address = address
        self._reconnect_delay = 0
        self._on_message = on_message
        self._consumer = self.consumer_factory()

    def consumer_factory(self):
        return AMQPAdapter(address=self.address, on_message=self._on_message)

    def run(self):
        while True:
            try:
                self._consumer.run()
            except KeyboardInterrupt:
                self._consumer.stop()
                break
            self._maybe_reconnect()

    def stop(self):
        self._consumer.stop()

    def _maybe_reconnect(self):
        if self._consumer.should_reconnect:
            self._consumer.stop()
            reconnect_delay = self._get_reconnect_delay()
            LOGGER.info('Reconnecting after %d seconds', reconnect_delay)
            time.sleep(reconnect_delay)
            self._consumer = self.consumer_factory()

    def _get_reconnect_delay(self):
        if self._consumer.was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay


def main():
    """
    Demo how to use ``StreamAddress`` and ``ReconnectingAMQPAdapter`` to create a pipeline source element.

    DATA='{"id": "device-42", "temperature": 42.42, "humidity": "84.84"}'
    echo "${DATA}" | amqp-publish --url='amqp://guest:guest@localhost:5672/%2F' --routing-key=queue-43
    """
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    amqp_url = "amqp://guest:guest@localhost:5672/%2F?queue=queue-43&setup=queue"
    address = StreamAddress.from_url(amqp_url)
    consumer = ReconnectingAMQPAdapter(address=address)
    consumer.run()


if __name__ == '__main__':
    main()
