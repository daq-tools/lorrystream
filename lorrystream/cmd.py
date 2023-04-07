# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import asyncio
import logging
import re
import typing as t

from lorrystream.core import run_single

logger = logging.getLogger(__name__)


def get_location(element: t.Union[str, None]) -> str:
    if element is None:
        raise ValueError("Unable to decode location from empty element")
    matches = re.match(".*location=(.*)", element)
    if not matches:
        raise ValueError(f"Unable to decode location from element: {element}")
    location = matches.group(1)
    return location


def parse_launch(command: str):
    logger.info(f"Running command: {command}")
    elements = map(str.strip, command.split("!"))
    source = None
    sink = None
    for element in elements:
        name, rest = element.split(" ")
        if name.endswith("src"):
            source = element
        elif name.endswith("sink"):
            sink = element
    source_uri = get_location(source)
    sink_uri = get_location(sink)
    logger.info(f"Source: {source_uri}, Sink: {sink_uri}")
    asyncio.run(run_single(source_uri, sink_uri))
