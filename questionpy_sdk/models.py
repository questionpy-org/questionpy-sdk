#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Mapping
from typing import Literal

from questionpy_common.manifest import SourceManifest

BuildHookName = Literal["pre", "post"]


class PackageConfig(SourceManifest):
    """A QuestionPy source package configuration.

    This class extends [`SourceManifest`][questionpy_common.manifest.SourceManifest] by incorporating additional
    configuration parameters.
    """

    build_hooks: Mapping[BuildHookName, str | list[str]] = {}

    @property
    def manifest(self) -> SourceManifest:
        """Creates [`SourceManifest`][questionpy_common.manifest.SourceManifest] from config model."""
        return SourceManifest.model_validate(dict(self))
