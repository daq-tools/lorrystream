# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import random
import typing as t
from pathlib import Path

BACKENDS = ["streamz", "tributary"]


def random_table_name(label: t.Union[Path, str]):
    name = label
    if isinstance(label, Path):
        name = label.name
    return f"lorrystream-test-{name}-{random.randint(1, 9999)}"  # noqa: S311
