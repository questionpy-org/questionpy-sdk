from pathlib import Path
from shutil import move

import pytest
from click.testing import CliRunner
from pydantic.error_wrappers import ValidationError

from questionpy_sdk.commands.package import package

from yaml import safe_dump
from questionpy_common.manifest import Manifest


def assert_same_structure(directory: Path, expected: list[Path]) -> None:
    """
    Checks if the directory has the same folder structure as `expected`.
    """
    assert sorted(file for file in directory.rglob("*") if file.is_file()) == sorted(expected)


def normalized_file_name(manifest: Manifest) -> str:
    """
    Returns a normalized file name for the given `manifest`.
    """
    return f"{manifest.namespace}-{manifest.short_name}-{manifest.version}.qpy"


def create_package(path: Path, short_name: str, namespace: str = "local", version: str = "0.1.0") -> \
        tuple[Path, Manifest]:
    """
    Create a '.qpy'-package inside the existing folder of the given `path`.

    The test will skip if the packaging fails.
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

        with (directory / "qpy_manifest.yml").open("w") as f:
            safe_dump(manifest.dict(exclude={"type"}), f)

        package_path = Path("package.qpy")

        result = runner.invoke(package, [str(directory), "-o", str(package_path)])
        if result.exit_code != 0:
            pytest.skip(f"Could not create the package: {result.stdout}")

        if path.is_dir():
            new_package_path = path / normalized_file_name(manifest)
        else:
            new_package_path = path
        move(package_path, new_package_path)
        return new_package_path, manifest
