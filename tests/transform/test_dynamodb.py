import decimal

from lorrystream.transform.dynamodb import DynamoCDCTranslatorCrateDB

READING_BASIC = {"device": "foo", "temperature": 42.42, "humidity": 84.84}

MSG_INSERT_BASIC = {
    "awsRegion": "us-east-1",
    "eventID": "b015b5f0-c095-4b50-8ad0-4279aa3d88c6",
    "eventName": "INSERT",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720740233012995,
        "Keys": {"device": {"S": "foo"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "NewImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "foo"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        },
        "SizeBytes": 99,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_INSERT_NESTED = {
    "awsRegion": "us-east-1",
    "eventID": "b581c2dc-9d97-44ed-94f7-cb77e4fdb740",
    "eventName": "INSERT",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "table-testdrive-nested",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720800199717446,
        "Keys": {"id": {"S": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266"}},
        "NewImage": {
            "id": {"S": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266"},
            "data": {"M": {"temperature": {"N": "42.42"}, "humidity": {"N": "84.84"}}},
            "meta": {"M": {"timestamp": {"S": "2024-07-12T01:17:42"}, "device": {"S": "foo"}}},
        },
        "SizeBytes": 156,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_MODIFY = {
    "awsRegion": "us-east-1",
    "eventID": "24757579-ebfd-480a-956d-a1287d2ef707",
    "eventName": "MODIFY",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720742302233719,
        "Keys": {"device": {"S": "foo"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "NewImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "55.66"},
            "device": {"S": "bar"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        },
        "OldImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "foo"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        },
        "SizeBytes": 161,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_REMOVE = {
    "awsRegion": "us-east-1",
    "eventID": "ff4e68ab-0820-4a0c-80b2-38753e8e00e5",
    "eventName": "REMOVE",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720742321848352,
        "Keys": {"device": {"S": "bar"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "OldImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "55.66"},
            "device": {"S": "bar"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        },
        "SizeBytes": 99,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}


def test_decode_ddb_deserialize_type():
    assert DynamoCDCTranslatorCrateDB(table_name="foo").deserialize_item({"foo": {"N": "84.84"}}) == {
        "foo": decimal.Decimal("84.84")
    }


def test_decode_cdc_insert_basic():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_INSERT_BASIC) == 'INSERT INTO "foo" (data) '
        'VALUES (\'{"humidity": 84.84, "temperature": 42.42, "device": "foo", "timestamp": "2024-07-12T01:17:42"}\');'
    )


def test_decode_cdc_insert_nested():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_INSERT_NESTED)
        == 'INSERT INTO "foo" (data) VALUES (\'{"id": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266", '
        '"data": {"temperature": 42.42, "humidity": 84.84}, '
        '"meta": {"timestamp": "2024-07-12T01:17:42", "device": "foo"}}\');'
    )


def test_decode_cdc_modify():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_MODIFY) == 'UPDATE "foo" '
        'SET data = \'{"humidity": 84.84, "temperature": 55.66, '
        '"device": "bar", "timestamp": "2024-07-12T01:17:42"}\' '
        "WHERE data['device'] = 'foo' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )


def test_decode_cdc_remove():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_REMOVE) == 'DELETE FROM "foo" '
        "WHERE data['device'] = 'bar' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )
