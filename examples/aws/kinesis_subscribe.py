"""
Synopsis, using LocalStack:

# Define service endpoint.
export AWS_ENDPOINT_URL="http://localhost:4566"

# Subscribe using StreamName or StreamARN.
python examples/aws/kinesis_subscribe.py testdrive
python examples/aws/kinesis_subscribe.py arn:aws:kinesis:eu-central-1:842404475894:stream/testdrive

# Use alternative backend. Default: async-kinesis.
export LORRY_BACKEND=ingestr

Use jq [1] or qv [2] to display data from dump file in JSONL/NDJSON format.
cat dms-over-kinesis.json | jq
qv dms-over-kinesis.json -l 999 -q "select metadata['operation'] as op, metadata['partition-key-type'] as 'partition-key-type', metadata['partition-key-value'] as 'partition-key-value', metadata['record-type'] as 'record-type', metadata['schema-name'] || '.' || metadata['table-name'] as table from tbl"

[1] https://github.com/jqlang/jq
[2] https://github.com/timvw/qv
"""  # noqa: E501

import asyncio
import os
import sys
from pprint import pprint  # noqa: F401

import orjson
from kinesis import Consumer, StringProcessor

from lorrystream.util.data import to_json

if "AWS_ACCESS_KEY" in os.environ:
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY"]
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")
try:
    STREAM_NAME = sys.argv[1]
except IndexError:
    print("ERROR: Please supply stream name as positional argument", file=sys.stderr)  # noqa: T201
    sys.exit(2)
BACKEND = os.environ.get("LORRY_BACKEND", "async-kinesis")


async def main():
    """
    iterator_type:

    LATEST - Read only new records.
    TRIM_HORIZON - Process all available records.
    AT_TIMESTAMP - Specify a time from which to start reading records.
    """
    if BACKEND == "async-kinesis":
        async with Consumer(
            endpoint_url=ENDPOINT_URL,
            stream_name=STREAM_NAME,
            # region_name="eu-central-1",
            # TODO: Make configurable.
            iterator_type="TRIM_HORIZON",
            sleep_time_no_records=0.2,
            processor=StringProcessor(),
        ) as consumer:
            while True:
                async for item in consumer:
                    record = orjson.loads(item)
                    print(to_json(record))  # noqa: ERA001, T203
                    # pprint(record)  # noqa: ERA001, T203

    elif BACKEND == "ingestr":
        from dlt.common.configuration.specs import AwsCredentials
        from ingestr.src.kinesis import kinesis_stream

        for record in kinesis_stream(
            stream_name=STREAM_NAME,
            initial_at_timestamp=-1,
            credentials=AwsCredentials(),
            parse_json=False,
        ):
            record.update(orjson.loads(record.pop("data")))
            print(to_json(record))  # noqa: ERA001, T203
            # pprint(record)  # noqa: ERA001, T203

    else:
        raise NotImplementedError(f"Backend not supported: {BACKEND}")


if __name__ == "__main__":
    asyncio.run(main())
