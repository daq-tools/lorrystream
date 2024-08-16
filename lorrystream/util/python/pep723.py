import re
import typing as t

import tomli

PEP_723_REGEX = r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$"


def read_inline_script_metadata(script: str) -> t.Dict[str, t.Any]:
    """
    Reference implementation to read inline script metadata (PEP 723).

    https://packaging.python.org/en/latest/specifications/inline-script-metadata/
    https://peps.python.org/pep-0723/
    """
    name = "script"
    matches = list(filter(lambda m: m.group("type") == name, re.finditer(PEP_723_REGEX, script)))
    if len(matches) > 1:
        raise ValueError(f"Multiple {name} blocks found")
    if len(matches) == 1:
        content = "".join(
            line[2:] if line.startswith("# ") else line[1:]
            for line in matches[0].group("content").splitlines(keepends=True)
        )
        return tomli.loads(content)
    else:
        return {}
