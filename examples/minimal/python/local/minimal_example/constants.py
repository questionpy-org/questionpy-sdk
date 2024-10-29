from pathlib import Path as _Path
from typing import Final as _Final

SHORT_NAME_FOLDER: _Final[_Path] = _Path(__file__).parent
NAMESPACE_FOLDER: _Final[_Path] = SHORT_NAME_FOLDER.parent

NAMESPACE: _Final[str] = NAMESPACE_FOLDER.name
"""Namespace of the package."""
SHORT_NAME: _Final[str] = SHORT_NAME_FOLDER.name
"""Short name of the package."""
