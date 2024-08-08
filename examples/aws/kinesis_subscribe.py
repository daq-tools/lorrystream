"""
Synopsis, using LocalStack:

    export AWS_ENDPOINT_URL="http://localhost:4566"
    python lorrystream/spike/kinesis/subscribe.py testdrive
"""

import asyncio
import os
import sys
from pprint import pprint

from kinesis import Consumer, StringProcessor

if "AWS_ACCESS_KEY" in os.environ:
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY"]
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL")
try:
    STREAM_NAME = sys.argv[1]
except IndexError:
    print("ERROR: Please supply stream name as positional argument", file=sys.stderr)  # noqa: T201
    sys.exit(2)


async def main():
    """
    iterator_type:

    LATEST - Read only new records.
    TRIM_HORIZON - Process all available records.
    AT_TIMESTAMP - Specify a time from which to start reading records.
    """
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
                pprint(item)  # noqa: T203


if __name__ == "__main__":
    asyncio.run(main())
