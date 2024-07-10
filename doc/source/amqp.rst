###########
AMQP source
###########


************
Introduction
************

The `AMQP`_ protocol is an open standard application layer protocol for
message-oriented middleware. The defining features of AMQP are message
orientation, queuing, routing (including point-to-point and
publish-and-subscribe), reliability, and security.

In order operate an AMQP relay application successfully, we recommend to
get familiar with relevant AMQP jargon, like "queues", "exchanges", and
"routing keys". For example, see `RabbitMQ Exchanges, routing keys and bindings`_.

AMQP knows different exchange types: "Direct", "Topic", "Fanout", and
"Headers". The examples in this tutorial use the default direct exchange
with no name, unless otherwise noted.


Default Exchange
================

    The default exchange is a pre-declared direct exchange with no name, usually
    referred to by an empty string. When you use the default exchange, your message
    is delivered to the queue with a name equal to the routing key of the message.
    Every queue is automatically bound to the default exchange with a routing
    key which is the same as the queue name.


********
Synopsis
********

Prerequisites
=============

In order to run all the examples successfully, you will need an AMQP broker
like RabbitMQ or GarageMQ, and CrateDB. The easiest way is to use a Docker Compose
file we provide for that purpose.

.. code-block:: console

    wget https://github.com/daq-tools/lorrystream/raw/main/docker-compose.yml
    docker compose up --detach cratedb rabbitmq

Verify Connectivity
===================

The most basic example is to start consuming from an AMQP queue, and to relay
its messages to STDOUT. This means incoming data will be either printed to your
terminal, or redirected to a file or pipe. It is useful to verify connecting to
the data source works well, and to inspect data or metadata information.

.. code-block:: console

    # Declare a queue.
    amqp-declare-queue --url="amqp://guest:guest@localhost:5672/%2F" --queue=queue-42

    # Subscribe to a queue and relay data stream to terminal.
    lorry relay "amqp://guest:guest@localhost:5672/%2F?queue=queue-42&content-type=json"

You can verify everything works by publishing an example message to the AMQP
default exchange, for example by using ``amqp-publish`` program.

.. code-block:: console

    # Define message, and publish.
    DATA='{"id": "device-42", "temperature": 42.42, "humidity": "84.84"}'
    echo "${DATA}" | amqp-publish \
        --url="amqp://guest:guest@localhost:5672/%2F" \
        --routing-key=queue-42

The ``lorry relay`` command effectively connects to an AMQP broker on
``localhost``, starts consuming messages from the queue ``queue-42``,
decoding the content payload from JSON, and relays the data stream to your
terminal.

Please note to use ``%2F`` for the `AMQP vhost`_ when not configured differently,
which is effectively ``/``.

Relay to Databases
==================

Relay data from AMQP into databases. LorryStream uses SQLAlchemy for connecting
to all types of databases supported. In order learn more details, please visit
the documentation section about the :ref:`database-sink`.

Relay data into a database table in SQLite.

.. code-block:: console

    # Start relay.
    lorry relay \
        "amqp://guest:guest@localhost:5672/%2F?queue=queue-42&content-type=json" \
        "sqlite:///data.sqlite?table=testdrive"

    # Submit data.
    echo "${DATA}" | amqp-publish \
        --url="amqp://guest:guest@localhost:5672/%2F" \
        --routing-key=queue-42

    # Verify data has been stored.
    sqlite3 data.sqlite "SELECT * FROM testdrive;"

If you are aiming to store high volumes of data, consider using a database
designed for that purpose. In this case, relay data into a database table
stored in CrateDB.

.. code-block:: console

    # Start relay.
    lorry relay \
        "amqp://guest:guest@localhost:5672/%2F?queue=queue-42&content-type=json" \
        "crate://localhost/?table=testdrive-queue-42"

    # Submit data.
    echo "${DATA}" | amqp-publish \
        --url="amqp://guest:guest@localhost:5672/%2F" \
        --routing-key=queue-42

    # Verify data has been stored.
    crash -c 'REFRESH TABLE "testdrive-queue-42";'
    crash -c 'SELECT * FROM "testdrive-queue-42";'


**************
Advanced Usage
**************

If you need to set up the AMQP exchange or queue before consuming it, and don't
want to or can't use the ``amqp-declare-queue`` or other programs for declaring
fundamental entities on your AMQP broker, LorryStream supports you by accepting
corresponding URL query parameters.

:queue:
    The name of the AMQP queue.
    It is the single obligatory parameter, the others are optional.
:setup:
    Whether to invoke a corresponding _declare_ operation before consuming messages.
    Accepts a list of ``exchange``, ``queue``, and ``bind`` values, separated by commas.
    The default is to not declare anything at all, and just to start consuming.
:exchange:
    The name of the AMQP exchange.
:exchange-type:
    The type of the AMQP exchange when declaring it per ``setup=exchange``.
    Accepts one of ``direct``, ``topic``, ``fanout``, or ``headers`` values.
    The default exchange type is ``direct``.
:routing-key:
    The AMQP routing key or pattern where the relay is consuming from.

Examples
========

Use the parameter ``setup=queue`` to set up the AMQP queue before starting to
consume messages.

.. code-block:: console

    lorry relay "amqp://guest:guest@localhost:5672/%2F?queue=queue-42&setup=queue&content-type=json"

If you need to set up the queue, and its binding to an exchange, please use the
URL query parameter ``setup=queue,bind``. This requires you to also specify
``exchange``, and ``routing-key``.

.. code-block:: console

    # Start relay.
    lorry relay "amqp://guest:guest@localhost:5672/%2F?exchange=amq.direct&queue=queue-42&routing-key=foobar&setup=queue,bind&content-type=json"

    # Submit data.
    echo "${DATA}" | amqp-publish \
        --url='amqp://guest:guest@localhost:5672/%2F' \
        --exchange=amq.direct --routing-key=foobar

If you need to set up all of the exchange, the queue, and its binding to an
exchange, please use the URL query parameter ``setup=exchange,queue,bind``.

.. code-block:: console

    # Start relay.
    lorry relay "amqp://guest:guest@localhost:5672/%2F?exchange=custom-exchange&queue=queue-42&routing-key=foobar&setup=exchange,queue,bind&content-type=json"

    # Submit data.
    echo "${DATA}" | amqp-publish \
        --url='amqp://guest:guest@localhost:5672/%2F' \
        --exchange=custom-exchange --routing-key=foobar

If you also need to define the exchange type, please use the
``exchange-type={direct,topic,fanout,headers}`` URL query parameter.

.. code-block:: console

    # Start relay.
    lorry relay "amqp://guest:guest@localhost:5672/%2F?exchange=custom-exchange&exchange-type=topic&queue=queue-42&routing-key=foobar&setup=exchange,queue,bind&content-type=json"


*******
Backlog
*******

.. code-block:: console

    echo "${DATA}" | \
        lorry publish "amqp://guest:guest@localhost:5672/%2F?routing-key=queue-42"



.. _AMQP: https://en.wikipedia.org/wiki/AMQP
.. _AMQP vhost: https://www.rabbitmq.com/docs/uri-spec#virtual-host
.. _RabbitMQ Exchanges, routing keys and bindings: https://www.cloudamqp.com/blog/part4-rabbitmq-for-beginners-exchanges-routing-keys-bindings.html
