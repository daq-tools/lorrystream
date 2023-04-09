# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

from lorrystream.core import ChannelFactory


def sink(data):
    print("data:", data)


async def run_engine(source_uri: str, sink_uri: str):
    # Create channels.
    channel = ChannelFactory(source=source_uri, sink=sink).channel()
    print(channel)
