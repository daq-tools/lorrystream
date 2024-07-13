# ruff: noqa: S608 FIXME: Possible SQL injection vector through string-based query construction
import logging
import typing as t

import simplejson as json
import toolz
from boto3.dynamodb.types import TypeDeserializer

logger = logging.getLogger(__name__)


class DynamoCDCTranslatorBase:
    """
    Translate DynamoDB CDC events into different representations.
    """

    def __init__(self):
        self.deserializer = TypeDeserializer()

    def deserialize_item(self, item: t.Dict[str, t.Dict[str, str]]) -> t.Dict[str, str]:
        """
        Deserialize DynamoDB type-enriched nested JSON snippet into vanilla Python.

        Example:
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

        -- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html#HowItWorks.DataTypeDescriptors
        """
        return toolz.valmap(self.deserializer.deserialize, item)


class DynamoCDCTranslatorCrateDB(DynamoCDCTranslatorBase):
    """
    Translate DynamoDB CDC events into CrateDB SQL statements that materialize them again.

    The SQL DDL schema for CrateDB:
    CREATE TABLE <tablename> (data OBJECT(DYNAMIC));

    Blueprint:
    https://www.singlestore.com/blog/cdc-data-from-dynamodb-to-singlestore-using-dynamodb-streams/
    """

    # Define name of the column where CDC's record data will get materialized into.
    DATA_COLUMN = "data"

    def __init__(self, table_name: str):
        super().__init__()
        self.table_name = self.quote_table_name(table_name)

    @property
    def sql_ddl(self):
        """
        Define SQL DDL statement for creating table in CrateDB that stores re-materialized CDC events.
        """
        return f"CREATE TABLE {self.table_name} ({self.DATA_COLUMN} OBJECT(DYNAMIC));"

    def to_sql(self, record: t.Dict[str, t.Any]) -> str:
        """
        Produce INSERT|UPDATE|DELETE SQL statement from INSERT|MODIFY|REMOVE CDC event record.
        """
        event_source = record.get("eventSource")
        event_name = record.get("eventName")

        if event_source != "aws:dynamodb":
            raise ValueError(f"Unknown eventSource: {event_source}")

        if event_name == "INSERT":
            values_clause = self.image_to_values(record["dynamodb"]["NewImage"])
            sql = f"INSERT INTO {self.table_name} " f"({self.DATA_COLUMN}) " f"VALUES ('{values_clause}');"

        elif event_name == "MODIFY":
            values_clause = self.image_to_values(record["dynamodb"]["NewImage"])
            where_clause = self.keys_to_where(record["dynamodb"]["Keys"])
            sql = f"UPDATE {self.table_name} " f"SET {self.DATA_COLUMN} = '{values_clause}' " f"WHERE {where_clause};"

        elif event_name == "REMOVE":
            where_clause = self.keys_to_where(record["dynamodb"]["Keys"])
            sql = f"DELETE FROM {self.table_name} " f"WHERE {where_clause};"

        else:
            raise ValueError(f"Unknown CDC event name: {event_name}")

        return sql

    def image_to_values(self, image: t.Dict[str, t.Any]) -> str:
        """
        Serialize CDC event's "(New|Old)Image" representation to a `VALUES` clause in CrateDB SQL syntax.

        IN (top-level stripped):
        "NewImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "foo"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        }

        OUT:
        {"humidity": 84.84, "temperature": 42.42, "device": "foo", "timestamp": "2024-07-12T01:17:42"}
        """
        return json.dumps(self.deserialize_item(image))

    def keys_to_where(self, keys: t.Dict[str, t.Dict[str, str]]) -> str:
        """
        Serialize CDC event's "Keys" representation to an SQL `WHERE` clause in CrateDB SQL syntax.

        IN (top-level stripped):
        "Keys": {
            "device": {"S": "foo"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        }

        OUT:
        WHERE data['device'] = 'foo' AND data['timestamp'] = '2024-07-12T01:17:42'
        """
        constraints: t.List[str] = []
        for key_name, key_value_raw in keys.items():
            key_value = self.deserializer.deserialize(key_value_raw)
            # FIXME: Does the quoting of the value on the right hand side need to take the data type into account?
            constraint = f"{self.DATA_COLUMN}['{key_name}'] = '{key_value}'"
            constraints.append(constraint)
        return " AND ".join(constraints)

    @staticmethod
    def quote_table_name(name: str):
        """
        Poor man's table quoting.

        TODO: Better use or vendorize canonical table quoting function from CrateDB Toolkit, when applicable.
        """
        if '"' not in name:
            name = f'"{name}"'
        return name
