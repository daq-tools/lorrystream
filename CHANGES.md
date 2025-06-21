# Changelog

## in progress

## 2025-06-21 v0.0.7
- DMS: Updated from engine version 3.5.2 to 3.6.1
- DMS: Improved stack configuration and replication settings
- DMS: Fix unordered event processing (DDL after DML), see also [CODEC-101].
  Let's tune down the Kinesis stream by switching from capacity mode
  `ON_DEMAND` to `PROVISIONED`, with a fixed number of provisioned shards, `1`.
- Kinesis: Improved example subscriber program

[CODEC-101]: https://github.com/crate/commons-codec/issues/101

## 2024-09-02 v0.0.6
- Dependencies: Unpin sqlalchemy-cratedb, to always use the latest version

## 2024-08-21 v0.0.5
- Dependencies: Unpin commons-codec, to always use the latest version

## 2024-08-16 v0.0.4
- Dependencies: Update to `commons-codec` version 0.0.6

## 2024-08-16 v0.0.3
- Carabas: A subsystem to divert workloads to other people’s computers

## 2024-07-10 v0.0.2
- Initial working version, supporting MQTT, AMQP, and SQLAlchemy/CrateDB
- Add CLI interface
- Add logging
- Add software tests

## 2023-04-06 v0.0.1
- Framework and code layout explorations
