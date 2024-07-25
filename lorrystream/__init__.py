from importlib.metadata import version

from .cmd import parse_launch

__appname__ = "lorrystream"
__version__ = version(__appname__)

__all__ = [
    "parse_launch",
]
