#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ModelWrapValidatorHandler, model_validator

from questionpy_common.manifest import SourceManifest

BuildHookName = Literal["pre", "post"]


class SourceStaticQPyDependency(BaseModel):
    path: Path

    @model_validator(mode="wrap")
    @classmethod
    def _validate(cls, data: object, handler: ModelWrapValidatorHandler[Self]) -> Self:
        if isinstance(data, str):
            if data.startswith("@"):
                msg = f"The dependency '{data}' looks like a dynamic dependency such as @myns/mypackage:myver."
                raise ValueError(msg)
            return cls(path=Path(data))

        return handler(data)


type SourceQPyDependency = SourceStaticQPyDependency


class SourceDependencies(BaseModel):
    qpy: list[SourceQPyDependency] = []


class PackageConfig(SourceManifest):
    """A QuestionPy source package configuration.

    This class extends [`SourceManifest`][questionpy_common.manifest.SourceManifest] by incorporating additional
    configuration parameters.
    """

    build_hooks: Mapping[BuildHookName, str | list[str]] = {}
    ignore: list[str] = []
    dependencies: SourceDependencies = SourceDependencies()

    def to_manifest(self) -> SourceManifest:
        """Creates [`SourceManifest`][questionpy_common.manifest.SourceManifest] from config model."""
        return SourceManifest.model_validate(dict(self))
