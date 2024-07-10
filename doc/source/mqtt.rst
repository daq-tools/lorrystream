###########
MQTT source
###########


************
Introduction
************

The `MQTT`_ protocol is a lightweight, publish-subscribe, machine to machine
network protocol for message queue/message queuing service.


**************
Basic examples
**************

Prerequisites
=============

In order to run all the examples successfully, you will need Mosquitto and
CrateDB. The easiest way is to use a Docker Compose file we provide for that
purpose.

.. code-block:: console

    wget https://github.com/daq-tools/lorrystream/raw/main/docker-compose.yml
    docker compose up --detach cratedb mosquitto

Connectivity
============

The most basic example is to subscribe to a data source, and to relay it to
STDOUT. This means the data will be either printed to your terminal, or
redirected to a file or pipe. It is useful to verify if connecting to the data
source works well, and to inspect data or metadata information.

.. code-block:: console

    # Subscribe to MQTT topic and relay data stream to terminal.
    lorry relay "mqtt://localhost/testdrive/%23"

This command effectively connects to an MQTT broker on ``localhost``, subscribes
to the MQTT topic ``testdrive/#``, and relays the data stream to your terminal,
without applying any kind of decoding. Please note to use ``%23`` for the topic
wildcard character ``#``.

You can verify everything works by publishing an example message to the MQTT
topic, for example using ``mosquitto_pub``.

.. code-block:: console

    # Submit message.
    echo "hello world" | mosquitto_pub -t 'testdrive/foo' -l

Storage
=======

For the next examples, let's define a message payload in JSON format.

.. code-block:: console

    DATA='{"id": "device-42", "temperature": 42.42, "humidity": 84.84}'

An only slightly more advanced example would be to converge data from MQTT into
an SQLite database.

.. code-block:: console

    # Start relay.
    lorry relay \
        "mqtt://localhost/testdrive/%23?content-type=json" \
        "sqlite:///data.sqlite?table=testdrive"

    # Submit data.
    echo "${DATA}" | mosquitto_pub -t 'testdrive/foo' -l

    # Verify data has been stored.
    sqlite3 data.sqlite "SELECT * FROM testdrive;"

If you are aiming to store high volumes of data, consider using a database
designed for that purpose.

.. code-block:: console

    lorry relay \
        "mqtt://localhost/testdrive/%23?content-type=json" \
        "crate://localhost/?table=testdrive"

**LorryStream** uses SQLAlchemy for connecting to the target database, which
supports a wide range of databases. In order learn more details, please visit
the documentation section about the :ref:`database-sink`.


.. _MQTT: https://en.wikipedia.org/wiki/MQTT
