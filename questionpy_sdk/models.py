#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Literal, Mapping, Union
from questionpy_common.manifest import Manifest


BuildHookName = Literal["pre", "post"]


class PackageConfig(Manifest):
    """
    This class expands upon :class:`questionpy_common.manifest.Manifest` by
    incorporating additional configuration parameters.
    """

    build_hooks: Mapping[BuildHookName, Union[str, list[str]]] = {}

    @property
    def manifest(self) -> Manifest:
        """Create :class:`questionpy_common.manifest.Manifest` from config model."""
        return Manifest.model_validate(dict(self))
