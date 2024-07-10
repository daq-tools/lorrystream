# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import logging
import textwrap
import typing as t

import click

from lorrystream.util.common import setup_logging

logger = logging.getLogger(__name__)


def boot_click(ctx: click.Context, verbose: bool = False, debug: bool = False):
    """
    Bootstrap the CLI application.
    """

    # Adjust log level according to `verbose` / `debug` flags.
    log_level = logging.WARNING
    if verbose:
        log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG

    # Setup logging, according to `verbose` / `debug` flags.
    setup_logging(level=log_level)


def to_list(x: t.Any, default: t.List[t.Any] = None) -> t.List[t.Any]:
    if not isinstance(default, t.List):
        raise ValueError("Default value is not a list")
    if x is None:
        return default
    if not isinstance(x, t.Iterable) or isinstance(x, str):
        return [x]
    elif isinstance(x, list):
        return x
    else:
        return list(x)


def docstring_format_verbatim(text: t.Optional[str]) -> str:
    """
    Format docstring to be displayed verbatim as a help text by Click.

    - https://click.palletsprojects.com/en/8.1.x/documentation/#preventing-rewrapping
    - https://github.com/pallets/click/issues/56
    """
    text = text or ""
    text = textwrap.dedent(text)
    lines = [line if line.strip() else "\b" for line in text.splitlines()]
    return "\n".join(lines)
