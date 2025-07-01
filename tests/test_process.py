import json
import os
import sys

import pytest
from commons_codec.model import ColumnType, ColumnTypeMapStore, TableAddress


@pytest.fixture
def reset_handler():
    try:
        del sys.modules["lorrystream.process.kinesis_cratedb_lambda"]
    except KeyError:
        pass


def test_kinesis_dynamodb_cratedb_lambda_basic(mocker, cratedb, reset_handler):
    """
    Test AWS Lambda processing Kinesis DynamoDB CDC event, converging to CrateDB.
    """

    # Read event payload.
    with open("tests/testdata/kinesis_dynamodb.json") as fp:
        event = json.load(fp)

    # Configure.
    handler_environment = {
        "MESSAGE_FORMAT": "dynamodb",
        "SINK_SQLALCHEMY_URL": cratedb.get_connection_url(),
        "SINK_TABLE": "testdrive-dynamodb-cdc",
    }
    mocker.patch.dict(os.environ, handler_environment)

    # Provision CrateDB.
    cratedb.database.run_sql(
        """
        CREATE TABLE "testdrive-dynamodb-cdc" (
            pk OBJECT(STRICT) AS ("device" STRING PRIMARY KEY, "timestamp" STRING PRIMARY KEY),
            data OBJECT(DYNAMIC),
            aux OBJECT(IGNORED)
        );
    """
    )

    # Invoke Lambda handler.
    from lorrystream.process.kinesis_cratedb_lambda import handler

    handler(event, None)

    # Verify record exists in CrateDB.
    cratedb.database.run_sql('REFRESH TABLE "testdrive-dynamodb-cdc";')
    assert cratedb.database.count_records("testdrive-dynamodb-cdc") == 1

    records = cratedb.database.run_sql('SELECT * FROM "testdrive-dynamodb-cdc";', records=True)
    assert records[0] == {
        "pk": {"device": "foo", "timestamp": "2024-07-12T01:17:42"},
        "data": {"temperature": 42.42, "humidity": 84.84},
        "aux": {},
    }


def test_kinesis_dynamodb_cratedb_lambda_batch(mocker, cratedb, reset_handler):
    """
    Test AWS Lambda processing Kinesis DynamoDB CDC event, converging to CrateDB.
    This time, using batch processing on Kinesis.
    """

    # Read event payload.
    with open("tests/testdata/kinesis_dynamodb.json") as fp:
        event = json.load(fp)

    # Configure.
    handler_environment = {
        "MESSAGE_FORMAT": "dynamodb",
        "SINK_SQLALCHEMY_URL": cratedb.get_connection_url(),
        "SINK_TABLE": "testdrive-dynamodb-cdc",
        "USE_BATCH_PROCESSING": "true",
    }
    mocker.patch.dict(os.environ, handler_environment)

    # Provision CrateDB.
    cratedb.database.run_sql(
        """
        CREATE TABLE "testdrive-dynamodb-cdc" (
            pk OBJECT(STRICT) AS ("device" STRING PRIMARY KEY, "timestamp" STRING PRIMARY KEY),
            data OBJECT(DYNAMIC),
            aux OBJECT(IGNORED)
        );
    """
    )

    # Invoke Lambda handler.
    from lorrystream.process.kinesis_cratedb_lambda import handler

    outcome = handler(event, None)
    assert outcome == {"batchItemFailures": []}

    # Verify record exists in CrateDB.
    cratedb.database.run_sql('REFRESH TABLE "testdrive-dynamodb-cdc";')
    assert cratedb.database.count_records("testdrive-dynamodb-cdc") == 1

    records = cratedb.database.run_sql('SELECT * FROM "testdrive-dynamodb-cdc";', records=True)
    assert records[0] == {
        "pk": {"device": "foo", "timestamp": "2024-07-12T01:17:42"},
        "data": {"temperature": 42.42, "humidity": 84.84},
        "aux": {},
    }


def test_kinesis_dms_cratedb_lambda_basic(mocker, cratedb, reset_handler):
    """
    Test AWS Lambda processing AWS DMS events, converging to CrateDB.
    """

    # Read event payload.
    with open("tests/testdata/kinesis_dms.json") as fp:
        event = json.load(fp)

    # Define column type mapping for CrateDB processor.
    column_types = ColumnTypeMapStore().add(
        table=TableAddress(schema="public", table="foo"),
        column="attributes",
        type_=ColumnType.OBJECT,
    )

    # Configure environment variables.
    handler_environment = {
        "MESSAGE_FORMAT": "dms",
        "COLUMN_TYPES": column_types.to_json(),
        "SINK_SQLALCHEMY_URL": cratedb.get_connection_url(),
    }
    mocker.patch.dict(os.environ, handler_environment)

    # Invoke Lambda handler.
    from lorrystream.process.kinesis_cratedb_lambda import handler

    handler(event, None)

    # Verify record exists in CrateDB.
    cratedb.database.run_sql('REFRESH TABLE "public"."foo";')
    assert cratedb.database.count_records("public.foo") == 1

    records = cratedb.database.run_sql('SELECT * FROM "public"."foo";', records=True)
    assert records[0] == {
        "pk": {"id": 46},
        "data": {"name": "Jane", "age": 31, "attributes": {"baz": "qux"}},
        "aux": {},
    }
