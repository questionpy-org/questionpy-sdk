from abc import ABC, abstractmethod
from contextlib import AbstractContextManager

from pathspec import PathSpec

from questionpy_sdk.package.source import PackageSource


class BuildEnvironment(AbstractContextManager, ABC):
    def __init__(self, source: PackageSource, ignore_spec: PathSpec) -> None:
        self._source = source
        self._ignore_spec = ignore_spec
