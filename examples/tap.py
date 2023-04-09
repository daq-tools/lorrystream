# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import typing as t

from lorrystream.core import ChannelFactory
from lorrystream.model import Packet


def trace(packets: t.List[Packet]):
    print("packets:", packets)


def main():
    # Create channels.
    channel = ChannelFactory(source="A", sink="B").channel()
    channel.tap(trace)
