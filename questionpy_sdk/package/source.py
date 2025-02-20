#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path

import yaml
from pydantic import ValidationError
from yaml import YAMLError

from questionpy import i18n
from questionpy.i18n import GettextDomain
from questionpy_common.manifest import Bcp47LanguageTag
from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.models import PackageConfig
from questionpy_sdk.package.errors import PackageSourceValidationError

from ._helper import create_normalized_filename


class PackageSource:
    """Represents a package source directory on the filesystem."""

    def __init__(self, path: Path):
        """Initializes a package source from a directory path.

        Args:
            path: Package source path.

        Raises:
            PackageSourceValidationError: If the package source could not be validated.
        """
        self._path = path
        self._validate()

    def _validate(self) -> None:
        self._check_required_paths()

    def _check_required_paths(self) -> None:
        # check for `python/NAMESPACE/SHORTNAME/__init__.py`
        package_init_path = self._path / "python" / self.config.namespace / self.config.short_name / "__init__.py"
        if not package_init_path.is_file():
            msg = f"Expected '{package_init_path}' to exist"
            raise PackageSourceValidationError(msg)

    @cached_property
    def config(self) -> PackageConfig:
        try:
            with self.config_path.open() as config_file:
                return PackageConfig.model_validate(yaml.safe_load(config_file))
        except FileNotFoundError as exc:
            msg = f"The config '{self.config_path}' does not exist."
            raise PackageSourceValidationError(msg) from exc
        except YAMLError as exc:
            msg = f"Failed to parse config '{self.config_path}': {exc}"
            raise PackageSourceValidationError(msg) from exc
        except ValidationError as exc:
            # TODO: pretty error feedback (https://docs.pydantic.dev/latest/errors/errors/#customize-error-messages)
            msg = f"Failed to validate package config '{self.config_path}': {exc}"
            raise PackageSourceValidationError(msg) from exc

    @property
    def config_path(self) -> Path:
        return self._path / PACKAGE_CONFIG_FILENAME

    @property
    def normalized_filename(self) -> str:
        return create_normalized_filename(self.config)

    @property
    def path(self) -> Path:
        return self._path

    def discover_po_files(self) -> Iterator[tuple[GettextDomain, Bcp47LanguageTag, Path]]:
        locale_dir = self.path / "locale"
        po_file: Path
        for po_file in locale_dir.glob("*.po"):
            yield i18n.domain_of(self.config), Bcp47LanguageTag(po_file.stem), po_file

        for po_file in locale_dir.glob("*/*.po"):
            yield GettextDomain(po_file.stem), Bcp47LanguageTag(po_file.parent.name), po_file

    def discover_pot_files(self) -> Iterator[tuple[GettextDomain, Path]]:
        for pot_file in (self.path / "locale").glob("*.pot"):
            yield GettextDomain(pot_file.stem), pot_file
