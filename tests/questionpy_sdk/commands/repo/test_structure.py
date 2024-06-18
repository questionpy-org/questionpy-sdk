#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path

import pytest
from click.testing import CliRunner

from questionpy_sdk.commands.repo.structure import structure
from questionpy_sdk.package._helper import create_normalized_filename

from .conftest import assert_same_structure, create_package


def test_structure_no_arguments_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(structure)
    assert result.exit_code != 0
    assert "Error: Missing argument 'ROOT'." in result.stdout


def test_structure_with_not_existing_root_path_raises_error(runner: CliRunner) -> None:
    result = runner.invoke(structure, ["root"])
    assert result.exit_code != 0
    assert "Error: Invalid value for 'ROOT': Directory 'root' does not exist." in result.stdout


def test_structure_with_file_as_root_path_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "root").touch()

    result = runner.invoke(structure, ["root"])

    assert result.exit_code != 0
    assert "Error: Invalid value for 'ROOT': Directory 'root' is a file." in result.stdout


def test_structure_with_missing_out_path_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "root").mkdir()

    result = runner.invoke(structure, ["root"])

    assert result.exit_code != 0
    assert "Error: Missing argument 'OUT_PATH'" in result.stdout


def test_structure_with_existing_out_path_raises_error(runner: CliRunner, cwd: Path) -> None:
    (cwd / "root").mkdir()
    (cwd / "out").mkdir()

    result = runner.invoke(structure, ["root", "out"])

    assert result.exit_code != 0
    assert "Error: Invalid value for 'OUT_PATH': Path 'out' is a directory." in result.stdout


def test_structure_with_empty_folder(runner: CliRunner, cwd: Path) -> None:
    (cwd / "root").mkdir()
    out_path = cwd / "out"

    result = runner.invoke(structure, ["root", "out"])

    assert result.exit_code == 0
    assert out_path.exists()
    assert_same_structure(
        out_path,
        (
            out_path / "META.json",
            out_path / "PACKAGES.json.gz",
        ),
    )


@pytest.mark.parametrize("count", [1, 3])
def test_structure_creates_only_one_package_if_identical(count: int, runner: CliRunner, cwd: Path) -> None:
    root = cwd / "root"
    root.mkdir()
    for i in range(count):
        _, config = create_package(root / f"{i}.qpy", "package")
    out = cwd / "out"

    result = runner.invoke(structure, ["root", "out"])

    assert result.exit_code == 0
    assert_same_structure(
        out,
        (
            out / "META.json",
            out / "PACKAGES.json.gz",
            out / config.namespace / config.short_name / create_normalized_filename(config),
        ),
    )


@pytest.mark.parametrize(
    ("package_1", "package_2"),
    [
        (("namespace_1", "shortname", "1.0.0"), ("namespace_2", "shortname", "1.0.0")),  # diff. namespaces, same names
        (("namespace", "shortname_1", "1.0.0"), ("namespace", "shortname_2", "1.0.0")),  # same namespaces, diff. names
        (
            ("namespace_1", "shortname_1", "1.0.0"),
            ("namespace_2", "shortname_2", "1.0.0"),
        ),  # diff. namespaces and names
        (("namespace", "shortname", "1.0.0"), ("namespace", "shortname", "2.0.0")),  # same package, diff. versions
    ],
    ids=[
        "different_namespaces-same_short_names",
        "same_namespaces-different_short_names",
        "different_namespaces-different_short_names",
        "same_package-different_versions",
    ],
)
def test_structure_with_multiple_packages(
    package_1: tuple[str, str, str], package_2: tuple[str, str, str], runner: CliRunner, cwd: Path
) -> None:
    namespace_1, short_name_1, version_1 = package_1
    namespace_2, short_name_2, version_2 = package_2

    out = cwd / "out"
    root = cwd / "root"
    root.mkdir()

    _, config_1 = create_package(root / "a.qpy", short_name_1, namespace=namespace_1, version=version_1)
    _, config_2 = create_package(root / "b.qpy", short_name_2, namespace=namespace_2, version=version_2)

    result = runner.invoke(structure, ["root", "out"])

    assert result.exit_code == 0
    assert_same_structure(
        out,
        (
            out / "META.json",
            out / "PACKAGES.json.gz",
            out / config_1.namespace / config_1.short_name / create_normalized_filename(config_1),
            out / config_2.namespace / config_2.short_name / create_normalized_filename(config_2),
        ),
    )
