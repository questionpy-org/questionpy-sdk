#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import importlib
import pkgutil
from collections import defaultdict
from typing import NamedTuple

from ._base import MigrationQuestionStateWithVersion
from ._migration import Migration, MigrationsRegistry, migrations_registry
from ._side_migration import SideMigration, SideMigrationsRegistry, side_migrations_registry
from .errors import MigrationDiscoveryError, MigrationNotPossibleError

__all__ = [
    "Migration",
    "MigrationNotPossibleError",
    "MigrationQuestionStateWithVersion",
    "Migrations",
    "SideMigration",
    "get_migrations",
]


class Migrations(NamedTuple):
    package: MigrationsRegistry
    """Migrations from and to this package."""
    side: SideMigrationsRegistry
    """Migrations from other packages to this package."""


def get_migrations(namespace: str, short_name: str) -> Migrations:
    """The package and its dependencies must be importable."""
    module_name = f"{namespace}.{short_name}.migrations"

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return Migrations([], defaultdict(defaultdict))

    try:
        for module_info in pkgutil.walk_packages(module.__path__, prefix=f"{module_name}."):
            importlib.import_module(module_info.name)
    except Exception as e:
        raise MigrationDiscoveryError from e

    return Migrations(migrations_registry, side_migrations_registry)
