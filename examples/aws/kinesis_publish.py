"""
Synopsis, using LocalStack:

    export AWS_ENDPOINT_URL="http://localhost:4566"
    python lorrystream/spike/kinesis/publish.py testdrive
"""

import asyncio
import os
import sys

from kinesis import Producer

if "AWS_ACCESS_KEY" in os.environ:
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY"]
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")
try:
    STREAM_NAME = sys.argv[1]
except IndexError:
    print("ERROR: Please supply stream name as positional argument", file=sys.stderr)  # noqa: T201
    sys.exit(2)

reading = {"device": "foo", "temperature": 42.42, "humidity": 84.84}


async def main():

    # Put item onto queue to be flushed via `put_records()`.
    async with Producer(
        endpoint_url=ENDPOINT_URL,
        stream_name=STREAM_NAME,
        # region_name="eu-central-1",
        buffer_time=0.01,
    ) as producer:
        await producer.put(reading)


if __name__ == "__main__":
    asyncio.run(main())
