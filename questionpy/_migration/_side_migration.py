#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from abc import ABC, abstractmethod
from collections import defaultdict

from ._base import BaseMigration

type SideMigrationsRegistry = defaultdict[str, defaultdict[str, dict[int, type[SideMigration]]]]


SIDE_MIGRATIONS_REGISTRY: SideMigrationsRegistry = defaultdict(lambda: defaultdict(dict))


class SideMigration(BaseMigration, ABC):
    """The base class for migrations from other packages to the current package."""

    def __init_subclass__(
        cls, /, for_namespace: str, for_short_name: str, for_state_version: int, **kwargs: object
    ) -> None:
        super().__init_subclass__(**kwargs)
        SIDE_MIGRATIONS_REGISTRY[for_namespace][for_short_name][for_state_version] = cls

    @abstractmethod
    def sidegrade(self) -> None:
        """Sidegrade the given state to this version.

        If the migration is not possible, raise the `MigrationNotPossibleError`.
        """
