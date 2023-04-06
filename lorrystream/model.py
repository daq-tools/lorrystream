# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import dataclasses
import operator
import typing as t
from urllib.parse import parse_qs, urlparse

from streamz import Sink, Source


@dataclasses.dataclass
class Channel:
    source: Source
    pipeline: t.Any
    sink: t.Union[t.Callable, Sink]

    def tap(self, callback: t.Callable):
        self.pipeline.stream.sink(callback)


@dataclasses.dataclass
class Packet:
    payload: t.Any
    original: t.Any

    @staticmethod
    def payloads(data):
        return list(map(operator.attrgetter("payload"), data))


class ConnectionString:
    """
    Helper class to support ``IoAccessor.export()``.
    """

    def __init__(self, url):
        self.url_raw = url
        self.url = urlparse(url)

    def get_database(self):

        # Try to get database name from query parameter.
        database = self.get_query_param("database")

        # Try to get database name from URL path.
        if database is None:
            if self.url.path.startswith("/"):
                database = self.url.path[1:]

        return database or "dwd"

    def get_table(self):
        return self.get_query_param("table") or "weather"

    def get_path(self):
        return self.url.path or self.url.netloc

    def get_query_param(self, name):
        query = parse_qs(self.url.query)
        try:
            return query[name][0]
        except (KeyError, IndexError):
            return None
