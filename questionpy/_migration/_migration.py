#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from abc import ABC, abstractmethod
from bisect import insort

from ._base import BaseMigration
from .errors import MigrationNotPossibleError

type MigrationsRegistry = list[type[Migration]]


MIGRATIONS_REGISTRY: MigrationsRegistry = []


def _migration_strategy(migration_cls: type["Migration"]) -> str:
    """Migrations are sorted by their module and class name."""
    return migration_cls.__module__ + "." + migration_cls.__qualname__


class Migration(BaseMigration, ABC):
    """The base class for migrations from and to the current package."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        insort(MIGRATIONS_REGISTRY, cls, key=_migration_strategy)

    @abstractmethod
    def upgrade(self) -> None:
        """Upgrade the previous state to this version.

        It is generally assumed, that upgrading is always possible, but if that is not the case the
        `MigrationNotPossibleError` should be raised.
        """

    def downgrade(self) -> None:
        """Downgrade this state to the previous version.

        The `MigrationNotPossibleError` should be raised if downgrading is not possible. This is also the default
        behaviour.
        """
        raise MigrationNotPossibleError
