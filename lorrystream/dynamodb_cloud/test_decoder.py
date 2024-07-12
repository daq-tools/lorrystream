from lorrystream.dynamodb_cloud.decoder import OpsLogDecoder

MSG_INSERT = {
    "awsRegion": "us-east-1",
    "eventID": "b015b5f0-c095-4b50-8ad0-4279aa3d88c6",
    "eventName": "INSERT",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "table-testdrive",
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
MSG_MODIFY = {
    "awsRegion": "us-east-1",
    "eventID": "24757579-ebfd-480a-956d-a1287d2ef707",
    "eventName": "MODIFY",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "table-testdrive",
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
    "tableName": "table-testdrive",
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


def test_decode_insert():
    assert (
        OpsLogDecoder.decode_opslog_item(MSG_INSERT) == "INSERT INTO transactions (data) "
        'VALUES (\'{"humidity": 84.84, "temperature": 42.42, "device": "foo", "timestamp": "2024-07-12T01:17:42"}\');'
    )


def test_decode_modify():
    assert (
        OpsLogDecoder.decode_opslog_item(MSG_MODIFY) == "UPDATE transactions\n                "
        'SET data = \'{"humidity": 84.84, "temperature": 55.66, '
        '"device": "bar", "timestamp": "2024-07-12T01:17:42"}\'\n                '
        "WHERE data['device'] = 'foo' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )


def test_decode_remove():
    assert (
        OpsLogDecoder.decode_opslog_item(MSG_REMOVE) == "DELETE FROM transactions\n                "
        "WHERE data['device'] = 'bar' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )
