# ruff: noqa: S608
import json
import logging
import typing as t
from collections import OrderedDict

from lorrystream.util.data import asbool

logger = logging.getLogger(__name__)


class OpsLogDecoder:
    """
    Utilities for decoding DynamoDB CDC operations events.
    """

    @classmethod
    def decode_opslog_item(cls, record: t.Dict[str, t.Any]):
        """
        DROP TABLE transactions;
        CREATE TABLE transactions (id INT) WITH (column_policy = 'dynamic');
        CREATE TABLE transactions (data OBJECT(DYNAMIC));

        -- https://www.singlestore.com/blog/cdc-data-from-dynamodb-to-singlestore-using-dynamodb-streams/
        """
        event_source = record.get("eventSource")
        event_name = record.get("eventName")
        if event_source != "aws:dynamodb":
            raise ValueError(f"Unknown eventSource: {event_source}")

        if event_name == "INSERT":
            json_str = json.dumps(cls.materialize_new_image(record["dynamodb"]["NewImage"]))
            sql = f"INSERT INTO transactions (data) VALUES ('{json_str}');".strip()

        elif event_name == "MODIFY":
            key1 = record["dynamodb"]["Keys"]["device"]["S"]
            key2 = record["dynamodb"]["Keys"]["timestamp"]["S"]
            json_str = json.dumps(cls.materialize_new_image(record["dynamodb"]["NewImage"]))
            sql = f"""
                UPDATE transactions
                SET data = '{json_str}'
                WHERE data['device'] = '{key1}' AND data['timestamp'] = '{key2}';""".strip()

        elif event_name == "REMOVE":
            key1 = record["dynamodb"]["Keys"]["device"]["S"]
            key2 = record["dynamodb"]["Keys"]["timestamp"]["S"]
            sql = f"""
                DELETE FROM transactions
                WHERE data['device'] = '{key1}' AND data['timestamp'] = '{key2}';""".strip()

        else:
            raise ValueError(f"Unknown CDC event name: {event_name}")

        return sql

    @classmethod
    def materialize_new_image(cls, item: t.Dict[str, t.Dict[str, str]]) -> t.Dict[str, str]:
        """
        {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "qux"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        }

        A complete list of DynamoDB data type descriptors:

        S – String
        N – Number
        B – Binary
        BOOL – Boolean
        NULL – Null
        M – Map
        L – List
        SS – String Set
        NS – Number Set
        BS – Binary Set

        """
        out = OrderedDict()
        for key, value_composite in item.items():
            type_: str = list(value_composite.keys())[0]
            value: t.Any = list(value_composite.values())[0]
            if type_ == "S":
                # TODO: Add heuristics for detecting types of timestamps or others?
                pass
            elif type_ == "N":
                value = float(value)
            elif type_ == "B":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            elif type_ == "BOOL":
                value = asbool(value)
            elif type_ == "NULL":
                value = None
            elif type_ == "M":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            elif type_ == "L":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            elif type_ == "SS":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            elif type_ == "NS":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            elif type_ == "BS":
                raise NotImplementedError(f"Type not implemented yet: {type_}")
            out[key] = value
        return out
