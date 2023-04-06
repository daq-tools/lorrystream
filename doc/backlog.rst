###################
LorryStream backlog
###################


***********
Iteration 1
***********
- [x] Data model: ``Channel`` and ``Packet``
- [x] Make it work with MQTT and CrateDB
- [x] GStreamer-like pipeline definition language

  - https://gstreamer.freedesktop.org/documentation/tools/gst-launch.html
- [x] Docs: Command line vs. library use
- [x] Rename to LorryStream
- [x] Add software tests


***********
Iteration 2
***********
- [x] Docs: Improve README
- [o] Provide Docker Compose file for running auxiliary services
- [o] Sink: SQLite
- [o] Docs: Provide full example using ``curl``: MQTT to SQLite
- [o] Make essential parameters configurable
- [o] Examples: Make more example programs work
- [o] Examples: Add example to manipulate data
- [o] Add more transformers
- [o] Provide replacement for ``amqp-to-mqtt``

  - https://testcontainers-python.readthedocs.io/en/latest/rabbitmq/README.html
- [o] Provide replacement for ``PutsReq``

  - https://community.hiveeyes.org/t/datenweiterleitung-via-ttn-lora-zu-hiveeyes-bob-und-beep-einrichten/3197
  - https://community.hiveeyes.org/t/tts-ttn-daten-an-kotori-weiterleiten/1422/27
  - https://github.com/flow-heater/flow-heater/pull/34
- [o] Examples: Add ``appsink`` example
- [o] Improve inline docs
- [o] Release 0.1.0


***********
Iteration 3
***********
- [o] Development: Code reloading
- [o] Fallback-based content decoder, Kotori-style; see ``funcy``
- [o] "First sample" hook to hand over to graphing subsystem
- [o] TLS to brokers
- [o] Formats: JSON, NDJSON, CSV, Muon
- [o] How to inspect the queue and flush all remaining items?

  a) on shutdown
  b) periodically
- [o] Custom decoder in Python and JavaScript
- [o] Source: Kafka. -- https://streamz.readthedocs.io/en/latest/api.html#streamz.from_kafka_batched
- [o] How to provide custom DDL statements, in order to account for sharding and partitioning?
- [o] How to invoke on/with Dask Distributed?

  - https://distributed.dask.org
  - https://github.com/dask/distributed
  - https://streamz.readthedocs.io/en/latest/dask.html#parallel-execution
- [o] Tap: Decode the topic and use corresponding details within the database addressing scheme,
  see "Kotori DAQ topology strategies": https://github.com/daq-tools/kotori/tree/main/kotori/daq/strategy
- [o] More __future__ examples for README
- [o] Re-use data loaders from other frameworks

  - Tributary
  - Hamilton: https://github.com/DAGWorks-Inc/hamilton/pull/128
    See also https://multithreaded.stitchfix.com/blog/2021/10/14/functions-dags-hamilton/
- [o] Source: Google Cloud PubSub (see testcontainers)
- [o] Source: Network / ZMQ / ZeroMQ

  - https://pypi.org/project/network-pipeline/
- [o] Launch multiple channels per config file
- [o] Grafana subsystem example
- [o] Source/Sink: MySQL and S3

  - https://github.com/danielnuriyev/streamz-example
- [o] Sink: Enable running data into multiple sinks at the same time
- [o] Logo

  - https://www.alamy.com/stock-photo/kerala-india-decorated-lorry.html?sortBy=relevant
  - https://www.turbosquid.com/de/3d-models/kerala-lorry-3d-model-1496574
- [o] Jupyter notebook examples

  - https://github.com/NicolaZomer/Koln_Traffic_Regulator_with_Parallel_Computing#notebook-4-dashboard-and-streaming
- [o] Audit log
- [o] Adapters to Airflow and Flink?


***********
Iteration 4
***********
- [o] Async decoder?
- [o] Emit with metadata
- [o] Source: Filesystem, using ``Stream.from_textfile()``
- [o] Source: Periodic
- [o] Sink: to_mqtt, to_websocket, to_kafka, to_textfile
- [o] ``--describe`` pipeline
- [o] Decoder and transformer subsystem
- [o] Run with dask-distributed
- [o] Sink: Prometheus?
  -- https://github.com/prometheus/client_python#exporting-to-a-pushgateway
- [o] Source: How to capture streams from different CDC interfaces?

  - https://datacater.io/blog/2021-09-02/postgresql-cdc-complete-guide.html
  - https://www.arcion.io/learn/postgresql-cdc
  - https://dbastreet.com/?p=1459
  - https://github.com/dgea005/pypgoutput
- [o] Stream data from Linux subsystems

  - Unix sockets: https://github.com/Kixunil/ws-unix-framed-bridge
  - Linux IIO
- [o] Source: Redis, Apache IoTDB
