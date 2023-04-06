###########
LorryStream
###########


*****
About
*****

*LorryStream* is a light-weight, polyglot event- or stream-processing system,
which can be used as a data backplane-, message relay-, and pipeline-subsystem.
It is based on `Streamz`_ and other modern Python libraries.

You can use LorryStream to stream data received from the network into storage
systems, or to relay it to other bus systems. It can be used both as a
standalone program, and as a library.

It is conceived in the spirit to generalize the corresponding subsystems of
programs and frameworks like `Kotori`_, `Wetterdienst`_, `Luftdatenpumpe`_,
`amqp-forward`_, `ttnlogger`_, `Kahn`_, `mqttwarn`_, `FIWARE QuantumLeap`_,
or `CrateOM`_.


Motivation
==========

Implement a reusable solution, simple to install and operate, that doesn't
depend on vendor-provided infrastructure, and can easily be embedded into
existing frameworks and software stacks, or integrated otherwise by running
it as a sidecar-service.

Details
=======

- Data sources are message bus systems like AMQP, Kafka, MQTT, ZeroMQ,
  and network listener endpoints for TCP, HTTP, and WebSocket.
- Data sinks are RDBMS databases supported by SQLAlchemy, or other message
  brokers.

Caveat
======

Please note that LorryStream is alpha-quality software, and a work in progress.
Contributions of all kinds are very welcome, in order to make it more solid.

Breaking changes should be expected until a 1.0 release, so version pinning
is recommended, especially when you use it as a library.

Only a few features sketched out in the README have actually been
implemented right now.


********
Synopsis
********

The canonical command is ``lorry relay <source> <sink>``.
Please note ``%23`` is ``#``.

.. code-block:: sh

    lorry relay \
        "mqtt://localhost/testdrive/%23" \
        "crate://localhost/?table=testdrive"

If you prefer a GStreamer-like pipeline definition syntax.

.. code-block:: sh

    lorry launch "mqttsrc location=mqtt://localhost/testdrive/%23 ! sqlsink location=crate://localhost/?table=testdrive"


**********
Quickstart
**********

If you are in a hurry, and want to run LorryStream without any installation,
just use the OCI image on Podman or Docker.

.. code-block:: sh

    docker run --rm --network=host ghcr.io/daq-tools/lorrystream \
        lorry relay \
        "mqtt://localhost/testdrive/%23" \
        "crate://localhost/?table=testdrive"


*****
Setup
*****

Install ``lorrystream`` from PyPI.

.. code-block:: sh

    pip install lorrystream


*****
Usage
*****

This section outlines some example invocations of LorryStream, both on the
command line, and per library use. Other than the resources available from
the web, testing data can be acquired from the repository's `testdata`_ folder.

Prerequisites
=============

For properly running some of the example invocations outlined below, you will
need a few servers. The easiest way to spin up those instances is to use Podman
or Docker.

.. code-block:: sh

    docker run --name=mosquitto --rm -it --publish=1883:1883 \
        eclipse-mosquitto:2.0.15 mosquitto -c /mosquitto-no-auth.conf

-- https://github.com/docker-library/docs/blob/master/eclipse-mosquitto/README.md

.. code-block:: sh

    docker run --name=cratedb --rm -it --publish=4200:4200 --publish=5432:5432 \
        crate:5.2 -Cdiscovery.type=single-node

-- https://github.com/docker-library/docs/blob/master/crate/README.md


Command line use
================

Help
----

.. code-block:: sh

    lorry --help
    lorry info
    lorry relay --help

Bus to storage
--------------

.. code-block:: sh

    # Relay messages from MQTT to CrateDB.
    lorry relay \
        "mqtt://localhost/testdrive/%23" \
        "crate://localhost/?table=testdrive"

Bus to bus
----------

.. code-block:: sh

    # Relay messages from AMQP to MQTT.
    lorry relay \
        "amqp://localhost/testdrive/demo" \
        "mqtt://localhost/testdrive/demo"


Library use
===========

.. code-block:: python

    >>> from lorrystream import parse_launch
    >>> parse_launch("mqttsrc location=mqtt://localhost/testdrive/%23 ! sqlsink location=crate://localhost/?table=testdrive")


OCI
---

OCI images are available on the GitHub Container Registry (GHCR). We are
publishing image variants for general availability- and nightly-releases,
and pull requests.

In order to always run the latest ``nightly`` development version, and to use a
shortcut for that, this section outlines how to use an alias for ``lorry``,
and a variable for storing the data source and sink URIs. It may be useful to
save a few keystrokes on subsequent invocations.

.. code-block:: sh

    docker pull ghcr.io/daq-tools/lorrystream:nightly
    alias lorry="docker run --rm --interactive ghcr.io/daq-tools/lorrystream:nightly lorry"
    SOURCE=mqtt://localhost/testdrive/%23
    SINK=crate://crate@localhost:4200/?table=testdrive

    lorry relay "${SOURCE}" "${SINK}"


*******************
Project information
*******************

Development
===========
For installing the project from source, please follow the `development`_
documentation.

Prior art
=========
There are a many other projects which are aiming at similar goals, and where
LorryStream borrows ideas from.

- `Airflow`_
- `GStreamer`_
- `ioBroker`_
- `Kotori`_
- `Node-RED`_
- `Telegraf`_
- `Tremor`_
- `Tributary`_


.. _Airflow: https://github.com/apache/airflow
.. _amqp-forward: https://github.com/daq-tools/amqp-forward
.. _CrateOM: https://crateom.io/
.. _development: doc/development.rst
.. _fsspec: https://pypi.org/project/fsspec/
.. _GStreamer: https://en.wikipedia.org/wiki/GStreamer
.. _ioBroker: https://github.com/ioBroker
.. _Kahn: https://github.com/maritime-labs/kahn
.. _Kotori: https://github.com/daq-tools/kotori
.. _Luftdatenpumpe: https://github.com/earthobservations/luftdatenpumpe
.. _mqttwarn: https://github.com/jpmens/mqttwarn
.. _Node-RED: https://github.com/node-red
.. _pandas: https://pandas.pydata.org/
.. _FIWARE QuantumLeap: https://github.com/orchestracities/ngsi-timeseries-api
.. _SQLAlchemy: https://pypi.org/project/SQLAlchemy/
.. _Streamz: https://github.com/python-streamz/streamz
.. _Telegraf: https://github.com/influxdata/telegraf
.. _testdata: https://github.com/daq-tools/lorrystream/tree/main/tests/testdata
.. _Tributary: https://github.com/streamlet-dev/tributary
.. _Tremor: https://www.tremor.rs/
.. _ttnlogger: https://github.com/daq-tools/ttnlogger
.. _Wetterdienst: https://github.com/earthobservations/wetterdienst/
