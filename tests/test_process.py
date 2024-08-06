import json
import os
import sys

import pytest


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
    cratedb.database.run_sql('CREATE TABLE "testdrive-dynamodb-cdc" (data OBJECT(DYNAMIC));')

    # Invoke Lambda handler.
    from lorrystream.process.kinesis_cratedb_lambda import handler

    handler(event, None)

    # Verify record exists in CrateDB.
    cratedb.database.run_sql('REFRESH TABLE "testdrive-dynamodb-cdc";')
    assert cratedb.database.count_records("testdrive-dynamodb-cdc") == 1

    records = cratedb.database.run_sql('SELECT * FROM "testdrive-dynamodb-cdc";', records=True)
    assert records[0] == {
        "data": {"temperature": 42.42, "humidity": 84.84, "device": "foo", "timestamp": "2024-07-12T01:17:42"}
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
    cratedb.database.run_sql('CREATE TABLE "testdrive-dynamodb-cdc" (data OBJECT(DYNAMIC));')

    # Invoke Lambda handler.
    from lorrystream.process.kinesis_cratedb_lambda import handler

    outcome = handler(event, None)
    assert outcome == {"batchItemFailures": []}

    # Verify record exists in CrateDB.
    cratedb.database.run_sql('REFRESH TABLE "testdrive-dynamodb-cdc";')
    assert cratedb.database.count_records("testdrive-dynamodb-cdc") == 1

    records = cratedb.database.run_sql('SELECT * FROM "testdrive-dynamodb-cdc";', records=True)
    assert records[0] == {
        "data": {"temperature": 42.42, "humidity": 84.84, "device": "foo", "timestamp": "2024-07-12T01:17:42"}
    }
