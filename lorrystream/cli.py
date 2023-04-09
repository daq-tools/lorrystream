# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import logging
import typing as t

import click

from lorrystream import parse_launch
from lorrystream.core import run_single
from lorrystream.util.about import AboutReport
from lorrystream.util.aio import make_sync
from lorrystream.util.cli import boot_click, docstring_format_verbatim

logger = logging.getLogger(__name__)


def help_relay():
    """
    Import and export data into/from InfluxDB

    SOURCE can be a file or a URL.
    TARGET can be a file or a URL.

    Synopsis
    ========

    # Relay messages from MQTT to CrateDB.
    lorry relay \\
        "mqtt://localhost/testdrive/#" \\
        "crate://localhost/testdrive/data"

    # Relay messages from AMQP to MQTT.
    lorry relay \\
        "amqp://localhost/testdrive/demo" \\
        "mqtt://localhost/testdrive/demo"

    """  # noqa: E501


def help_launch():
    """
    Launch a LorryStream pipeline.

    """  # noqa: E501


@click.group()
@click.version_option(package_name="lorrystream")
@click.option("--verbose", is_flag=True, required=False, help="Turn on logging")
@click.option("--debug", is_flag=True, required=False, help="Turn on logging with debug level")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool):
    verbose = True
    return boot_click(ctx, verbose, debug)


@cli.command("info", help="Report about platform information")
def info():
    AboutReport.platform()


@cli.command(
    "launch",
    help=docstring_format_verbatim(help_launch.__doc__),
    context_settings={"max_content_width": 120},
)
@click.argument("command", nargs=-1)
@click.pass_context
def launch(ctx: click.Context, command: t.Tuple[str]):
    logger.info("Starting")
    command_str = " ".join(command)
    parse_launch(command_str)


@cli.command(
    "relay",
    help=docstring_format_verbatim(help_relay.__doc__),
    context_settings={"max_content_width": 120},
)
@click.argument("source", type=str, required=True)
@click.argument("sink", type=str, required=False)
@click.pass_context
@make_sync
async def relay(ctx: click.Context, source: str, sink: str):
    logger.info("Starting")
    await run_single(source, sink)
