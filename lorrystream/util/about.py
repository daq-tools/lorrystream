# Copyright (c) 2013-2023 The Kotori developers and contributors.
# This module is part of LorryStream and is released under the MIT License.
# See LICENSE file for more information.

import platform
import sys
import textwrap
import typing as t

from colorama import Fore, Style

string_or_list = t.Union[str, t.List[str], t.Iterable[str]]


def section(text: str):
    return armor(text, title)


def subsection(text: str):
    return armor(text, subtitle)


def armor(text: str, formatter: t.Callable):
    guard = "=" * len(text)
    print(guard)
    print(formatter(text))
    print(guard)


def title(text: str):
    return Fore.CYAN + Style.BRIGHT + text + Style.RESET_ALL


def subtitle(text: str):
    return Fore.YELLOW + Style.BRIGHT + text + Style.RESET_ALL


def text_list(data: string_or_list):
    if isinstance(data, str):
        return data
    elif isinstance(data, t.List):
        return ", ".join(data)
    else:
        raise ValueError("Unable to flatten list")


def bullet_list(data: t.List[str]):
    data.sort()
    lines = [f"- {text_list(line)}" for line in data]
    return "\n".join(lines)


def wrap_list(data: t.List[str], **kwargs):
    data = [item for item in data if item is not None]
    data.sort()
    text = ", ".join(data)
    return "\n".join(textwrap.wrap(text, width=80, **kwargs))


def bullet_item(data: string_or_list, label: str = None):
    if data is None:
        return None
    if label is None:
        label = ""
    else:
        label = f"{label}: "
    if isinstance(data, (t.List, t.KeysView, t.ValuesView)):
        text = wrap_list(list(data), subsequent_indent="  ")
    else:
        text = data
    return f"- {label}{text}"


class AboutReport:
    @staticmethod
    def platform():
        section("Platform")
        print()

        subsection("Python")
        print(bullet_item(platform.platform()))
        print()

        # SQLAlchemy
        from importlib.metadata import entry_points

        import sqlalchemy.dialects

        subsection("SQLAlchemy")
        print(bullet_item(sqlalchemy.dialects.registry.impls.keys(), label="Dialects built-in"))
        dialects: t.List[str]
        if sys.version_info >= (3, 10):
            eps = entry_points(group="sqlalchemy.dialects")
            dialects = [dialect.name for dialect in eps]
        else:
            dialects = []
        print(bullet_item(dialects, label="Dialects 3rd-party"))
        print(bullet_item(sqlalchemy.dialects.plugins.impls.keys(), label="Plugins"))
        print()

        # fsspec
        try:
            import fsspec

            subsection("fsspec protocols")
            print(bullet_item(fsspec.available_protocols()))
            print()

            subsection("fsspec compressions")
            print(bullet_item(fsspec.available_compressions()))
            print()
        except ImportError:
            pass

        # pandas
        subsection("pandas module versions")
        import pandas

        pandas.show_versions(as_json=False)
        print()
