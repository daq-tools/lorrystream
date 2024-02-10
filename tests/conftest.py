# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import pytest

from lorrystream.util.common import setup_logging


@pytest.fixture
def cratedb(cratedb_service):
    cratedb_service.reset(["testdrive"])
    yield cratedb_service


setup_logging()
