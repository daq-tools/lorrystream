# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the GPLv3 license, see LICENSE.

import asyncio
import json
import logging

import pytest
import sqlalchemy as sa

from lorrystream.core import ChannelFactory, Engine

capmqtt_decode_utf8 = True


logger = logging.getLogger(__name__)


class engine_single_shot:
    def __init__(self, *channels):
        self.engine = Engine()
        for channel in channels:
            self.engine.register(channel)

    async def __aenter__(self, *channels):
        logger.info("Starting engine")
        self.engine.start()
        await asyncio.sleep(0.25)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await asyncio.sleep(1.00)
        logger.info("Stopping engine")
        self.engine.stop()
        await asyncio.sleep(0.25)
        return False


@pytest.mark.asyncio_cooperative
async def test_dataframe_to_sql(mosquitto, cratedb, capmqtt):
    cratedb.reset()

    database_url = cratedb.get_connection_url()
    channel = ChannelFactory("mqtt://localhost/testdrive/%23", f"{database_url}/?table=testdrive").channel()

    # Run machinery and publish reading.
    async with engine_single_shot(channel):
        reading = {"device": "foo", "temperature": 42.42, "humidity": 84.84}
        capmqtt.publish("testdrive/readings", json.dumps(reading))
        capmqtt.publish("testdrive/readings", json.dumps(reading))

    # Validate data in storage system.
    sa_engine = sa.create_engine(database_url)
    with sa_engine.connect() as conn:
        conn.exec_driver_sql("REFRESH TABLE testdrive;")
        with conn.execute(sa.text("SELECT COUNT(*) FROM testdrive;")) as result:
            assert result.scalar_one() == 2
