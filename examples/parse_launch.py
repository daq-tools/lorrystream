# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

from lorrystream import parse_launch
from lorrystream.util.common import setup_logging


def main():
    parse_launch(
        "mqttsrc location=mqtt://localhost/testdrive/%23 ! sqlsink location=crate://localhost/?table=testdrive"
    )


if __name__ == "__main__":
    setup_logging()
    main()
