import asyncio
import os
from pprint import pprint

from kinesis import Consumer

os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY"]


async def main():
    """
    iterator_type:

    LATEST - Read only new records.
    TRIM_HORIZON - Process all available records.
    AT_TIMESTAMP - Specify a time from which to start reading records.
    """
    async with Consumer(
        stream_name="testdrive-dms-postgresql-dev-stream",
        region_name="eu-central-1",
        iterator_type="TRIM_HORIZON",
        sleep_time_no_records=0.2,
    ) as consumer:
        while True:
            async for item in consumer:
                pprint(item)  # noqa: T203


if __name__ == "__main__":
    asyncio.run(main())
