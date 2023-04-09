# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import dataclasses
import operator
import typing as t
from urllib.parse import parse_qs, urlparse

import funcy
from streamz import Sink, Source

from lorrystream.exceptions import InvalidSinkError
from lorrystream.streamz.model import URL, BusMessage

SinkInputType = t.Union[str, t.Callable, None]


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
    busmsg: t.Optional[BusMessage] = None

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


@dataclasses.dataclass
class StreamAddress:
    uri: URL
    options: t.Dict[str, str] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_url(cls, url: str):
        uri = URL(url)

        # Separate URI query parameters used by LorryStream.
        control_option_names = ["content-type"]
        options = funcy.project(uri.query_params, control_option_names)
        query_params = funcy.omit(uri.query_params, control_option_names)
        uri.query_params = query_params

        return cls(uri=uri, options=options)

    @classmethod
    def resolve_sink(cls, sink: SinkInputType):
        """
        Select sink element of pipeline.
        """

        if callable(sink):
            url = f"callable://{sink.__name__}"
        elif isinstance(sink, str):
            url = sink
        else:
            raise InvalidSinkError(f"Invalid sink: {sink}")

        uri = URL(url)
        return cls(uri=uri)
