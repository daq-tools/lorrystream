###########
LorryStream
###########


*****
About
*****

**LorryStream** is a lightweight and polyglot stream-processing library, to
be used as a data backplane-, message relay-, or pipeline-subsystem, in the
spirit of `socat`_ and `GStreamer`_. It is based on `Streamz`_, `Dask`_, and
other Python libraries.

You can use LorryStream to stream data received from the network into storage
systems, or to relay it to other bus systems. It can be used both as a
standalone program, and as a library.

It is conceived to generalize and improve the corresponding subsystems of
programs and frameworks like `Kotori`_, `Wetterdienst`_, `Luftdatenpumpe`_,
`amqp-forward`_, `ttnlogger`_, `Kahn`_, `mqttwarn`_, `FIWARE QuantumLeap`_,
or `CrateOM`_.

Details
=======

- Data sources are message bus systems like AMQP, Kafka, MQTT, ZeroMQ,
  and network listener endpoints for TCP, UDP, HTTP, and WebSocket.
- Data sinks are RDBMS databases supported by SQLAlchemy, or other message
  brokers.

Motivation
==========

- Implement a reusable solution, simple to install and operate, that doesn't
  depend on vendor-provided infrastructure, and can easily be embedded into
  existing frameworks and software stacks, or integrated otherwise by running
  it as a separate service.

- Help the community and industry to modernize their aging DAQ backend systems
  designed within the previous decades.

Background
==========

  Flow-Based Programming (`FBP`_) is a programming paradigm that uses a "data
  processing factory" metaphor for designing and building applications.
  It is a special case of `dataflow`_ programming characterized by
  asynchronous, concurrent processes "under the covers".

  FBP has been found to support improved development time and maintainability,
  reusability, rapid prototyping, simulation, improved performance, and good
  communication among developers, maintenance staff, users, systems people, and
  management - not to mention that FBP naturally takes advantage of multiple
  cores, without the programmer having to struggle with the intricacies of
  multitasking.

  -- `Flow-based Programming`_

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

Resources
=========
- `Source code <https://github.com/daq-tools/lorrystream>`_
- `Documentation <https://github.com/daq-tools/lorrystream>`_
- `Python Package Index (PyPI) <https://pypi.org/project/lorrystream/>`_

Contributions
=============
The LorryStream library is an open source project, and is `managed on
GitHub`_.
Every kind of contribution, feedback, or patch, is much welcome. `Create an
issue`_ or submit a patch if you think we should include a new feature, or to
report or fix a bug.

Development
===========
In order to setup a development environment on your workstation, please head
over to the `development sandbox`_ documentation. When you see the software
tests succeed, you should be ready to start hacking.

License
=======
The project is licensed under the terms of the MIT license, see `LICENSE`_.

Prior art
=========
There are a many other projects which are aiming at similar goals, and where
LorryStream inherits ideas and inspirations from.

- `Apache Airflow`_
- `Apache Flink`_
- `Armeria`_
- `Crossbar.io`_
- `FlowForge`_
- `Frankenstein Automation Gateway`_
- `GStreamer`_
- `ioBroker`_
- `JavaFBP`_
- `Kotori`_
- `Node-RED`_
- `NoFlo`_
- `PutsReq`_
- `rill`_
- `socat`_
- `Telegraf`_
- `Tremor`_
- `Tributary`_

Credits
=======
- `J. Paul Rodker Morrison`_ for discovering/inventing the Flow-Based
  Programming (FBP) paradigm in the late '60s.


.. _Apache Airflow: https://github.com/apache/airflow
.. _Apache Flink: https://github.com/apache/flink
.. _Armeria: https://github.com/line/armeria
.. _amqp-forward: https://github.com/daq-tools/amqp-forward
.. _CrateOM: https://crateom.io/
.. _Create an issue: https://github.com/daq-tools/lorrystream/issues
.. _Crossbar.io: https://crossbar.io/
.. _Dask: https://github.com/dask/dask
.. _Dataflow: https://en.wikipedia.org/wiki/Dataflow
.. _development sandbox: doc/development.rst
.. _FBP: https://en.wikipedia.org/wiki/Flow-based_programming
.. _FIWARE QuantumLeap: https://github.com/orchestracities/ngsi-timeseries-api
.. _Flow-based Programming: https://jpaulm.github.io/fbp/
.. _FlowForge: https://flowforge.com/
.. _Frankenstein Automation Gateway: https://github.com/vogler75/automation-gateway
.. _fsspec: https://pypi.org/project/fsspec/
.. _GStreamer: https://en.wikipedia.org/wiki/GStreamer
.. _ioBroker: https://github.com/ioBroker
.. _J. Paul Rodker Morrison: https://jpaulm.github.io/
.. _JavaFBP: https://github.com/jpaulm/javafbp
.. _Kahn: https://github.com/maritime-labs/kahn
.. _Kotori: https://github.com/daq-tools/kotori
.. _LICENSE: LICENSE
.. _Luftdatenpumpe: https://github.com/earthobservations/luftdatenpumpe
.. _managed on GitHub: https://github.com/daq-tools/lorrystream
.. _mqttwarn: https://github.com/jpmens/mqttwarn
.. _Node-RED: https://github.com/node-red
.. _NoFlo: https://github.com/noflo/noflo
.. _pandas: https://pandas.pydata.org/
.. _PutsReq: https://github.com/daq-tools/putsreq
.. _rill: https://github.com/PermaData/rill
.. _socat: http://www.dest-unreach.org/socat/
.. _SQLAlchemy: https://pypi.org/project/SQLAlchemy/
.. _Streamz: https://github.com/python-streamz/streamz
.. _Telegraf: https://github.com/influxdata/telegraf
.. _testdata: https://github.com/daq-tools/lorrystream/tree/main/tests/testdata
.. _Tributary: https://github.com/streamlet-dev/tributary
.. _Tremor: https://www.tremor.rs/
.. _ttnlogger: https://github.com/daq-tools/ttnlogger
.. _Wetterdienst: https://github.com/earthobservations/wetterdienst/
