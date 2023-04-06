# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import logging
import shlex
import subprocess
import sys
from textwrap import dedent

import colorlog
from colorlog.escape_codes import escape_codes

logger = logging.getLogger(__name__)


SQLALCHEMY_LOGGING = True


def setup_logging_basic(level=logging.INFO):
    log_format = "%(asctime)-15s [%(name)-24s] %(levelname)-8s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)


def setup_logging(level=logging.INFO):
    reset = escape_codes["reset"]
    log_format = f"%(asctime)-15s [%(name)-26s] %(log_color)s%(levelname)-8s:{reset} %(message)s"

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format))

    logging.basicConfig(format=log_format, level=level, handlers=[handler])

    # Enable SQLAlchemy logging.
    if SQLALCHEMY_LOGGING:
        logging.getLogger("sqlalchemy").setLevel(level)


def get_version(appname):
    from importlib.metadata import PackageNotFoundError, version  # noqa

    try:
        return version(appname)
    except PackageNotFoundError:  # pragma: no cover
        return "unknown"


def run_command(command: str):
    """
    https://stackoverflow.com/a/48813330
    """
    command = dedent(command).strip()
    cmd = shlex.split(command)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        logger.error(f"Command failed (exit code {exc.returncode}). The command was:\n{command}")
        logger.error(exc.output)
        raise
    else:
        if output:
            logger.info(f"Command output:\n{output}")
