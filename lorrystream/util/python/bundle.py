import typing as t
from pathlib import Path

from lorrystream.util.python.pep723 import read_inline_script_metadata


def collect_requirements(*artifacts: t.Union[str, Path]):
    """
    Collect dependencies from script metadata, as per PEP 723.
    """
    dependencies: t.List[str] = []
    for artifact in artifacts:
        if isinstance(artifact, Path):
            payload = artifact.read_text()
        else:
            payload = artifact
        metadata = read_inline_script_metadata(payload)
        if isinstance(metadata, dict):
            dependencies += metadata.get("dependencies", [])
    return dependencies
