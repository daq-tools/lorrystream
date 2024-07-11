import asyncio
import os

from kinesis import Producer

os.environ["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY"]

reading = {"device": "foo", "temperature": 42.42, "humidity": 84.84}


async def main():

    # Put item onto queue to be flushed via `put_records()`.
    async with Producer(stream_name="testdrive-stream", region_name="us-east-1", buffer_time=0.01) as producer:
        await producer.put(reading)


if __name__ == "__main__":
    asyncio.run(main())
