#######
Backlog
#######


***********
Iteration 1
***********
- [x] Data model: ``Channel`` and ``Packet``
- [x] Make basic example with MQTT and CrateDB work
- [x] Docs: Command line vs. library use
- [x] Rename to LorryStream
- [x] Add software tests


***********
Iteration 2
***********
- [x] Docs: Improve README
- [o] https://github.com/rrpelgrim/stream-this-dataset
- [o] Use stdout as sink when <sink> argument is omitted
- [o] Flink: https://github.com/apache/flink/blob/release-1.17.0/flink-python/pyflink/examples/datastream/connectors/kafka_avro_format.py
- [o] Provide Docker Compose file for running auxiliary services
- [o] Sink: SQLite
- [o] Docs: Provide full example using ``curl``: MQTT to SQLite
- [o] Make essential parameters configurable
- [o] Examples: Make more example programs work
- [o] Examples: Add example to manipulate data
- [o] Add more transformers
- [o] Provide replacement for ``amqp-to-mqtt``

  - https://testcontainers-python.readthedocs.io/en/latest/rabbitmq/README.html
  - ``amqp-consume --queue=secpi-on_off cat``
  - ``echo '{"action": "shutdown"}' | amqp-publish --routing-key=secpi-op-m``
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
- [o] Polars also offers streaming and sinking.

  - https://pola-rs.github.io/polars-book/user-guide/lazy-api/streaming.html
- [o] Docs

  - https://www.redhat.com/sysadmin/getting-started-socat
  - http://www.dest-unreach.org/socat/doc/socat.html#EXAMPLES
  - https://fiware-tutorials.readthedocs.io/en/stable/iot-over-mqtt/
- [o] Docs: ``curl``

  - https://curl.se/docs/mqtt.html
  - https://everything.curl.dev/usingcurl/mqtt
  - https://cogentdatahub.com/connect/mqtt/
  - https://gist.github.com/jforge/c783e47c430a897a7bddb95b64f8fcc0
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
- [o] Source: How to capture streams from different CDC interfaces?

  - https://datacater.io/blog/2021-09-02/postgresql-cdc-complete-guide.html
  - https://www.arcion.io/learn/postgresql-cdc
  - https://dbastreet.com/?p=1459
  - https://github.com/dgea005/pypgoutput
- [o] Stream data from Linux subsystems

  - Unix sockets: https://github.com/Kixunil/ws-unix-framed-bridge
  - Linux IIO
- [o] Source: Redis, Apache IoTDB
- [o] Docs: https://github.com/jackersson/gst-python-tutorials
- [o] Source: https://gstreamer.freedesktop.org/documentation/soup/souphttpsrc.html
- [o] Source: ``universal_pathlib``
- [o] Bus: AMQP 1.0 / STOMP (over WebSocket)

  - https://activemq.apache.org/
  - https://activemq.apache.org/amqp
  - https://activemq.apache.org/components/artemis/documentation/latest/amqp.html
  - https://activemq.apache.org/components/classic/
  - https://stomp.github.io/
  - https://activemq.apache.org/stomp
  - https://stackoverflow.com/questions/33954952/amqp-1-0-library-for-python
  - https://qpid.apache.org/
  - https://qpid.apache.org/proton/
  - https://github.com/apache/qpid-proton/tree/main/python/examples
  - https://pypi.org/project/uamqp/
  - https://github.com/Azure/azure-uamqp-python
  - https://access.redhat.com/documentation/en-us/red_hat_amq/6.3/html/client_connectivity_guide/amqppython
- [o] Bus: NATS

  - https://pypi.org/project/propan/
  - https://github.com/nats-io/nats.js

- https://cloudevents.io/

  - https://github.com/cloudevents/sdk-python
  - https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md

- https://pypi.org/project/aiomsg/
- https://pypi.org/project/arq/
- [o] Integrate with Tinybird
  - https://github.com/localstack/verdin
- https://www.kubeflow.org/docs/components/pipelines/v2/components/
- XML via JsonML?
  - https://en.wikipedia.org/wiki/JsonML
  - https://github.com/stleary/JSON-java/blob/master/src/main/java/org/json/JSONML.java
  - http://www.jsonml.org/
  - https://github.com/sasano8/jsonml
  - https://github.com/sasano8/jsonast

