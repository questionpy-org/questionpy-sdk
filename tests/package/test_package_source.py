#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import pytest

from questionpy_sdk.constants import PACKAGE_CONFIG_FILENAME
from questionpy_sdk.models import PackageConfig
from questionpy_sdk.package.errors import PackageSourceValidationError
from questionpy_sdk.package.source import PackageSource


def test_validate(source_path: Path) -> None:
    try:
        PackageSource(source_path)
    except PackageSourceValidationError as exc:
        pytest.fail(f"Validation failed: {exc}")


def test_attributes(source_path: Path) -> None:
    source = PackageSource(source_path)
    assert isinstance(source.config, PackageConfig)
    assert source.config_path == source_path / PACKAGE_CONFIG_FILENAME
    assert source.normalized_filename == "local-minimal_example-0.1.0.qpy"
    assert source.path == source_path


def test_missing_config_raises_error(source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME
    config_path.unlink()

    with pytest.raises(PackageSourceValidationError) as exc:
        PackageSource(source_path)

    assert exc.match(f"The config '{config_path}' does not exist")


def test_invalid_config_raises_error(source_path: Path) -> None:
    config_path = source_path / PACKAGE_CONFIG_FILENAME

    with config_path.open("w") as f:
        f.write("foo bar")
    with pytest.raises(PackageSourceValidationError) as exc:
        PackageSource(source_path)

    assert exc.match(f"Failed to validate package config '{config_path}'")


def test_missing_file_raises_error(source_path: Path) -> None:
    init_path = source_path / "python" / "local" / "minimal_example" / "__init__.py"
    init_path.unlink()

    with pytest.raises(PackageSourceValidationError) as exc:
        PackageSource(source_path)

    assert exc.match(f"Expected '{init_path}' to exist")
