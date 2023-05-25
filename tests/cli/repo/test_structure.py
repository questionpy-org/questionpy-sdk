from pathlib import Path

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands._helper import create_normalized_filename
from questionpy_sdk.commands.repo.structure import structure
from tests.conftest import create_package, assert_same_structure


def test_structure_no_arguments_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(structure)
        assert result.exit_code != 0
        assert "Error: Missing argument 'ROOT'." in result.stdout


def test_structure_with_not_existing_root_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(structure, ["root"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'ROOT': Directory 'root' does not exist." in result.stdout


def test_structure_with_file_as_root_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "root").touch()
        result = runner.invoke(structure, ["root"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'ROOT': Directory 'root' is a file." in result.stdout


def test_structure_with_missing_out_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "root").mkdir()
        result = runner.invoke(structure, ["root"])
        assert result.exit_code != 0
        assert "Error: Missing argument 'OUT_PATH'" in result.stdout


def test_structure_with_existing_out_path_raises_error() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "root").mkdir()
        Path(directory, "out").mkdir()
        result = runner.invoke(structure, ["root", "out"])
        assert result.exit_code != 0
        assert "Error: Invalid value for 'OUT_PATH': Path 'out' is a directory." in result.stdout


def test_structure_with_empty_folder() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        Path(directory, "root").mkdir()
        result = runner.invoke(structure, ["root", "out"])
        assert result.exit_code == 0

        out_path = Path(directory, "out")
        assert out_path.exists()

        assert_same_structure(out_path, [
            out_path / "META.json",
            out_path / "PACKAGES.json.gz",
        ])


@pytest.mark.parametrize("count", [1, 3])
def test_structure_creates_only_one_package_if_identical(count: int) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        root = Path(directory, "root")
        root.mkdir()

        for i in range(count):
            _, manifest = create_package(root / f"{i}.qpy", "package")

        out = Path(directory, "out")
        result = runner.invoke(structure, ["root", "out"])

        assert result.exit_code == 0
        assert_same_structure(Path(directory, "out"), [
            out / "META.json",
            out / "PACKAGES.json.gz",
            out / manifest.namespace / manifest.short_name / create_normalized_filename(manifest)
        ])


@pytest.mark.parametrize("package_1, package_2", [
    [("namespace_1", "shortname", "1.0.0"), ("namespace_2", "shortname", "1.0.0")],  # diff. namespaces, same names
    [("namespace", "shortname_1", "1.0.0"), ("namespace", "shortname_2", "1.0.0")],  # same namespaces, diff. names
    [("namespace_1", "shortname_1", "1.0.0"), ("namespace_2", "shortname_2", "1.0.0")],  # diff. namespaces and names
    [("namespace", "shortname", "1.0.0"), ("namespace", "shortname", "2.0.0")],  # same package, diff. versions
], ids=["different_namespaces-same_short_names", "same_namespaces-different_short_names",
        "different_namespaces-different_short_names", "same_package-different_versions"])
def test_structure_with_multiple_packages(package_1: tuple[str, str, str], package_2: tuple[str, str, str]) -> None:
    namespace_1, short_name_1, version_1 = package_1
    namespace_2, short_name_2, version_2 = package_2

    runner = CliRunner()
    with runner.isolated_filesystem() as directory:
        root = Path(directory, "root")
        root.mkdir()

        _, manifest_1 = create_package(root / "a.qpy", short_name_1, namespace=namespace_1, version=version_1)
        _, manifest_2 = create_package(root / "b.qpy", short_name_2, namespace=namespace_2, version=version_2)

        out = Path(directory, "out")
        result = runner.invoke(structure, ["root", "out"])

        assert result.exit_code == 0
        assert_same_structure(Path(directory, "out"), [
            out / "META.json",
            out / "PACKAGES.json.gz",
            out / manifest_1.namespace / manifest_1.short_name / create_normalized_filename(manifest_1),
            out / manifest_2.namespace / manifest_2.short_name / create_normalized_filename(manifest_2),
        ])
