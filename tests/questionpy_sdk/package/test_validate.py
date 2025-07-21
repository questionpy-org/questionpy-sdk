import logging
import shutil
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_common.manifest import Manifest
from questionpy_sdk._package import DirBuildTarget, build_qpy_package
from questionpy_sdk._package._validate import validate_dist_structure
from questionpy_sdk._package.source import PackageSource


@pytest.fixture
def dist_dir(source_path: Path) -> Path:
    target = DirBuildTarget.in_source(source_path)
    build_qpy_package(PackageSource(source_path), target)
    return target.dist


@pytest.fixture
def manifest(dist_dir: Path) -> Manifest:
    return Manifest.model_validate_json((dist_dir / MANIFEST_FILENAME).read_text())


def test_should_not_warn_for_valid_package(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    validate_dist_structure(manifest, dist_dir)
    for record in caplog.records:
        assert record.levelno < logging.WARNING


def test_warn_when_dist_contains_another_python_package(
    dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture
) -> None:
    (dist_dir / "python" / "another" / "package").mkdir(parents=True)
    (dist_dir / "python" / "another" / "package" / "__init__.py").touch()

    validate_dist_structure(manifest, dist_dir)

    warn_messages = [record.message for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warn_messages) == 1
    assert "- python/another/package\n" in warn_messages[0]
    assert "- python/another/package/__init__.py\n" in warn_messages[0]


def test_warn_when_dist_contains_wrong_js_dir(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    # In source, JS should be in <source dir>/js directly, which might lead build hook authors to write into dist/js as
    # well. This tests that that mistake is caught by the validation.
    (dist_dir / "js").mkdir(parents=True)
    (dist_dir / "js" / "bundle.js").touch()

    validate_dist_structure(manifest, dist_dir)

    warn_messages = [record.message for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warn_messages) == 1
    assert "- js\n" in warn_messages[0]
    assert "- js/bundle.js\n" in warn_messages[0]


def test_warn_when_dist_is_missing_python_dir(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    shutil.rmtree(dist_dir / "python")

    validate_dist_structure(manifest, dist_dir)

    assert "does not contain any Python code" in caplog.text
