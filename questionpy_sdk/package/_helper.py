#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.manifest import SourceManifest


def create_normalized_filename(manifest: SourceManifest) -> str:
    """Creates a normalized file name for the given manifest.

    Args:
        manifest: manifest of the package

    Returns:
        normalized file name
    """
    return f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.qpy"
