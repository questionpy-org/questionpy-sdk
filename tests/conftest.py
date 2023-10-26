#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from shutil import move

import pytest
from click.testing import CliRunner
from pydantic import ValidationError
from questionpy_common.manifest import Manifest
from yaml import safe_dump

from questionpy_sdk.commands._helper import create_normalized_filename
from questionpy_sdk.commands.package import package


def assert_same_structure(directory: Path, expected: list[Path]) -> None:
    """
    Checks if the directory has the same folder structure as `expected`.

    Args:
        directory: directory to check
        expected: expected structure
    """
    assert sorted(file for file in directory.rglob("*") if file.is_file()) == sorted(expected)


def create_package(path: Path, short_name: str, namespace: str = "local", version: str = "0.1.0") -> \
        tuple[Path, Manifest]:
    """
    Create a '.qpy'-package.

    The test will skip if the packaging fails and xfail if the manifest is invalid.

    Args:
        path: path to the folder where the package should be created or the path to the package itself
        short_name: short name of the package
        namespace: namespace of the package
        version: version of the package

    Returns:
        path to the package and the manifest
    """
    try:
        manifest = Manifest(short_name=short_name, namespace=namespace, version=version, api_version="0.1",
                            author="pytest")
    except ValidationError as e:
        pytest.xfail(f"Invalid manifest while creating the package: {e}")

    runner = CliRunner()
    with runner.isolated_filesystem() as fs:
        directory = Path(fs, manifest.short_name)
        directory.mkdir()

        with (directory / "qpy_manifest.yml").open("w") as manifest_file:
            safe_dump(manifest.model_dump(exclude={"type"}), manifest_file)

        package_path = Path("package.qpy")

        result = runner.invoke(package, [str(directory), "-o", str(package_path)])
        if result.exit_code != 0:
            pytest.skip(f"Could not create the package: {result.stdout}")

        if path.is_dir():
            new_package_path = path / create_normalized_filename(manifest)
        else:
            new_package_path = path
        move(package_path, new_package_path)
        return new_package_path, manifest
