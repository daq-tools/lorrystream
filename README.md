# LorryStream

## About

**LorryStream** is a lightweight and polyglot stream-processing library,
to be used as a data backplane-, message relay-, or pipeline-subsystem,
in the spirit of [socat] and [GStreamer]. It is based on [Streamz],
[Dask], and other Python libraries.

You can use **LorryStream** to store data received from the network into
databases, or to relay it back to the network, for example into
different bus systems. It can be used both as a standalone program, and
as a library.

It is conceived to generalize and improve the corresponding subsystems
of programs and frameworks like [Kotori], [Wetterdienst], [Luftdatenpumpe],
[amqp-forward], [ttnlogger], [Kahn], or [mqttwarn].


## Synopsis

The canonical command is `lorry relay <source> <sink>`. Please note
`%23` is `#`.

``` sh
lorry relay \
    "mqtt://localhost/testdrive/%23" \
    "crate://localhost/?table=testdrive"
```

If you prefer a GStreamer-like pipeline definition syntax.

``` sh
lorry launch "mqttsrc location=mqtt://localhost/testdrive/%23 ! sqlsink location=crate://localhost/?table=testdrive"
```

## Quickstart

If you are in a hurry, and want to run LorryStream without any
installation, just use the OCI image on Podman or Docker.

``` sh
docker run --rm --network=host ghcr.io/daq-tools/lorrystream \
    lorry relay \
    "mqtt://localhost/testdrive/%23" \
    "crate://localhost/?table=testdrive"
```

## Setup

Install `lorrystream` from PyPI.

``` sh
pip install lorrystream
```

## Usage

This section outlines some example invocations of LorryStream, both on
the command line, and per library use. Other than the resources
available from the web, testing data can be acquired from the
repository's [testdata] folder.

### Prerequisites

For properly running some of the example invocations outlined below, you
will need a few servers. The easiest way to spin up those instances is
to use Podman or Docker.

``` sh
docker run --name=mosquitto --rm -it --publish=1883:1883 \
    eclipse-mosquitto:2.0.15 mosquitto -c /mosquitto-no-auth.conf
```

-- <https://github.com/docker-library/docs/blob/master/eclipse-mosquitto/README.md>

``` sh
docker run --name=cratedb --rm -it --publish=4200:4200 --publish=5432:5432 \
    crate:5.2 -Cdiscovery.type=single-node
```

-- <https://github.com/docker-library/docs/blob/master/crate/README.md>

### Command line use

#### Help

``` sh
lorry --help
lorry info
lorry relay --help
```

#### Bus to storage

``` sh
# Relay messages from MQTT to CrateDB.
lorry relay \
    "mqtt://localhost/testdrive/%23" \
    "crate://localhost/?table=testdrive"
```

#### Bus to bus

``` sh
# Relay messages from AMQP to MQTT.
lorry relay \
    "amqp://localhost/testdrive/demo" \
    "mqtt://localhost/testdrive/demo"
```

### Library use

``` python
>>> from lorrystream import parse_launch
>>> parse_launch("mqttsrc location=mqtt://localhost/testdrive/%23 ! sqlsink location=crate://localhost/?table=testdrive")
```

#### OCI

OCI images are available on the GitHub Container Registry (GHCR). We are
publishing image variants for general availability- and
nightly-releases, and pull requests.

In order to always run the latest `nightly` development version, and to
use a shortcut for that, this section outlines how to use an alias for
`lorry`, and a variable for storing the data source and sink URIs. It
may be useful to save a few keystrokes on subsequent invocations.

``` sh
docker pull ghcr.io/daq-tools/lorrystream:nightly
alias lorry="docker run --rm --interactive ghcr.io/daq-tools/lorrystream:nightly lorry"
SOURCE=mqtt://localhost/testdrive/%23
SINK=crate://crate@localhost:4200/?table=testdrive

lorry relay "${SOURCE}" "${SINK}"
```


## Story

### Details

- Data sources are message bus systems like AMQP, Kafka, MQTT, ZeroMQ,
  and network listener endpoints for TCP, UDP, HTTP, and WebSocket.
- Data sinks are RDBMS databases supported by SQLAlchemy, or other
  message brokers.

### Motivation

- Implement a reusable solution, simple to install and operate, that
  doesn't depend on vendor-provided infrastructure, and can easily be
  embedded into existing frameworks and software stacks, or integrated
  otherwise by running it as a separate service.
- Help the community and industry to modernize their aging DAQ backend
  systems designed within the previous decades.
- Use as pipeline elements, protocol translator, bridge elements.

### Background

> Flow-Based Programming ([FBP]) is a programming paradigm that uses a
> "data processing factory" metaphor for designing and building applications.
> It is a special case of [dataflow] programming characterized by asynchronous,
> concurrent processes "under the covers".
>
> FBP has been found to support improved development time and
> maintainability, reusability, rapid prototyping, simulation, improved
> performance, and good communication among developers, maintenance
> staff, users, systems people, and management - not to mention that FBP
> naturally takes advantage of multiple cores, without the programmer
> having to struggle with the intricacies of multitasking.
>
> -- [Flow-based Programming]

### Caveat

Please note that LorryStream is alpha-quality software, and a work in
progress. Contributions of all kinds are very welcome, in order to make
it more solid.

Breaking changes should be expected until a 1.0 release, so version
pinning is recommended, especially when you use it as a library.


## Project information


### Contributions

The LorryStream library is an open source project, and is [managed on
GitHub]. Every kind of contribution, feedback, or patch, is much welcome.
[Create an issue] or submit a patch if you think we should include a new
feature, or to report or fix a bug.

### Development

In order to setup a development environment on your workstation, please
head over to the [development sandbox]
documentation. When you see the software tests succeed, you should be
ready to start hacking.

### License

The project is licensed under the terms of the LGPL license, see
[LICENSE].

### Prior art

We are maintaining a [list of other projects] with
the same or similar goals like LorryStream.

### Kudos

- [J. Paul Rodker Morrison] for discovering/inventing the Flow-Based
  Programming ([FBP]) paradigm in the late '60s.

- [Matthew Rocklin], [Christopher J. 'CJ' Wright], and [Chinmay Chandak]
  for conceiving [Streamz].


[amqp-forward]: https://github.com/daq-tools/amqp-forward
[Chinmay Chandak]: https://github.com/chinmaychandak
[Christopher J. 'CJ' Wright]: https://github.com/CJ-Wright
[Create an issue]: https://github.com/daq-tools/lorrystream/issues
[Dask]: https://github.com/dask/dask
[Dataflow]: https://en.wikipedia.org/wiki/Dataflow
[development sandbox]: https://github.com/daq-tools/lorrystream/blob/main/doc/development.rst
[FBP]: https://en.wikipedia.org/wiki/Flow-based_programming
[Flow-based Programming]: https://jpaulm.github.io/fbp/
[fsspec]: https://pypi.org/project/fsspec/
[GStreamer]: https://en.wikipedia.org/wiki/GStreamer
[J. Paul Rodker Morrison]: https://jpaulm.github.io/
[Kahn]: https://github.com/maritime-labs/kahn
[Kotori]: https://github.com/daq-tools/kotori
[LICENSE]: https://github.com/daq-tools/lorrystream/blob/main/LICENSE
[list of other projects]: https://github.com/daq-tools/lorrystream/blob/main/doc/prior-art.rst
[Luftdatenpumpe]: https://github.com/earthobservations/luftdatenpumpe
[managed on GitHub]: https://github.com/daq-tools/lorrystream
[Matthew Rocklin]: https://github.com/mrocklin
[mqttwarn]: https://github.com/jpmens/mqttwarn
[pandas]: https://pandas.pydata.org/
[socat]: http://www.dest-unreach.org/socat/
[SQLAlchemy]: https://pypi.org/project/SQLAlchemy/
[Streamz]: https://github.com/python-streamz/streamz
[testdata]: https://github.com/daq-tools/lorrystream/tree/main/tests/testdata
[ttnlogger]: https://github.com/daq-tools/ttnlogger
[Wetterdienst]: https://github.com/earthobservations/wetterdienst/
