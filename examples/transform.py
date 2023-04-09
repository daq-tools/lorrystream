# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

from lorrystream.core import ChannelFactory, Engine


def foo(value):
    """
    An example data transformation callback.
    :param value:
    :return:
    """
    # print("value:", value)  # noqa: ERA001
    value["number"] *= 5
    return value


async def run_engine(dburi):
    # Create channels.
    channel = ChannelFactory(source="A", sink="B").transform(foo).channel()

    # Run channels with engine.
    engine = Engine()
    engine.register(channel)
    await engine.run_forever()
