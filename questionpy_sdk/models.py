#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Self, cast

from pydantic import BaseModel, Field, ModelWrapValidatorHandler, field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo

from questionpy_common.manifest import AbstractDynamicQPyDependency, DependencyLockStrategy, PackageType, SourceManifest
from questionpy_common.version_specifiers import QPyDependencyVersionSpecifier

BuildHookName = Literal["pre", "post"]

_SHORT_DYN_DEPENDENCY_PATTERN = re.compile(r"^@(?P<ns>[a-z\d_]+)/(?P<sn>[a-z\d_]+)\s*")


class SourceStaticQPyDependency(BaseModel):
    path: Path

    @model_validator(mode="wrap")
    @classmethod
    def _validate(cls, data: object, handler: ModelWrapValidatorHandler[Self]) -> Self:
        if isinstance(data, str):
            if data.startswith("@"):
                msg = f"The dependency '{data}' looks like a dynamic dependency such as @myns/mypackage:1.2.3."
                raise ValueError(msg)
            return cls(path=Path(data))

        return handler(data)


class SourceDynamicQPyDependency(AbstractDynamicQPyDependency):
    lock: DependencyLockStrategy | Literal[False] | None = None
    """Whether and how to lock this dependency when packaging.

    The default is based on the package type:
    - `QUESTION` and `QUESTIONTYPE` default to `preferred-no-downgrade`.
    - `LIBRARY` default to `False`, i.e. no locking.
    """

    @model_validator(mode="wrap")
    @classmethod
    def _validate_from_str(cls, data: object, handler: ModelWrapValidatorHandler[Self]) -> Self:
        if isinstance(data, str):
            data = data.strip()

            match = _SHORT_DYN_DEPENDENCY_PATTERN.match(data)
            if not match:
                msg = (
                    f"The dependency '{data}' doesn't look like a dynamic dependency, which should take the form of "
                    f"'@myns/mypackage ^= 1.2.3' or '@myns/mypackage == 1.2.3-rc.2'."
                )
                raise ValueError(msg)

            if match.group(0) == data:
                # There is nothing more (i.e., no version specifier) in the dependency string.
                # This means to use the newest version of the dependency.
                version_specifier = None
            else:
                # There's more content, which we expect to be a version specifier.
                version_specifier = QPyDependencyVersionSpecifier.from_string(data[match.span(0)[1] :])

            return cls(
                namespace=match.group("ns"),
                short_name=match.group("sn"),
                version=version_specifier,
                include_prereleases=False,
                lock=None,
            )

        return handler(data)

    @model_validator(mode="after")
    def _validate_prereleases(self) -> Self:
        if self.version:
            for clause in self.version.clauses:
                if "-" in clause.operator:
                    msg = f"include_prereleases is not set, yet '{clause}' compares to a prerelease."
                    raise ValueError(msg)

        return self


type SourceQPyDependency = SourceStaticQPyDependency | SourceDynamicQPyDependency


class SourceDependencies(BaseModel):
    qpy: list[SourceQPyDependency] = []


class PackageConfig(SourceManifest):
    """A QuestionPy source package configuration.

    This class extends [`SourceManifest`][questionpy_common.manifest.SourceManifest] by incorporating additional
    configuration parameters.
    """

    build_hooks: Mapping[BuildHookName, str | list[str]] = {}
    ignore: list[str] = []
    lock_dependencies: DependencyLockStrategy | Literal[False] = Field(default=cast("Any", None), validate_default=True)
    dependencies: SourceDependencies = SourceDependencies()

    def to_manifest(self) -> SourceManifest:
        """Creates [`SourceManifest`][questionpy_common.manifest.SourceManifest] from config model."""
        return SourceManifest.model_validate(dict(self))

    @field_validator("lock_dependencies", mode="before")
    @classmethod
    def _default_lock_strategy(cls, value: object, info: ValidationInfo) -> object:
        if value is None:
            match info.data["type"]:
                case PackageType.QUESTION | PackageType.QUESTIONTYPE:
                    return "preferred-no-downgrade"
                case PackageType.LIBRARY:
                    return False

        return value
