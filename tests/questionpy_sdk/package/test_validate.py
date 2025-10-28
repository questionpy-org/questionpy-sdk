import logging
import shutil
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_common.manifest import Bcp47LanguageTag, Manifest, PartialPackagePermissions
from questionpy_sdk._package import DirBuildTarget, build_qpy_package
from questionpy_sdk._package._validate import (
    validate_dist_structure,
    validate_package_name_and_description,
    validate_requested_lms_attributes,
)
from questionpy_sdk._package.source import PackageSource


@pytest.fixture
def dist_dir(source_path: Path) -> Path:
    target = DirBuildTarget.in_source(source_path)
    build_qpy_package(PackageSource(source_path), target)
    return target.dist


@pytest.fixture
def manifest(dist_dir: Path) -> Manifest:
    return Manifest.model_validate_json((dist_dir / MANIFEST_FILENAME).read_text())


def get_warnings(caplog: LogCaptureFixture) -> list[str]:
    return [record.message for record in caplog.records if record.levelno == logging.WARNING]


def test_should_not_warn_for_valid_package(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    validate_dist_structure(manifest, dist_dir)
    assert len(get_warnings(caplog)) == 0


def test_warn_when_dist_contains_another_python_package(
    dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture
) -> None:
    (dist_dir / "python" / "another" / "package").mkdir(parents=True)
    (dist_dir / "python" / "another" / "package" / "__init__.py").touch()

    validate_dist_structure(manifest, dist_dir)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "- python/another/package\n" in warn_messages[0]
    assert "- python/another/package/__init__.py\n" in warn_messages[0]


def test_warn_when_dist_contains_wrong_js_dir(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    # In source, JS should be in <source dir>/js directly, which might lead build hook authors to write into dist/js as
    # well. This tests that that mistake is caught by the validation.
    (dist_dir / "js").mkdir(parents=True)
    (dist_dir / "js" / "bundle.js").touch()

    validate_dist_structure(manifest, dist_dir)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "- js\n" in warn_messages[0]
    assert "- js/bundle.js\n" in warn_messages[0]


def test_warn_when_dist_is_missing_python_dir(dist_dir: Path, manifest: Manifest, caplog: LogCaptureFixture) -> None:
    shutil.rmtree(dist_dir / "python")

    validate_dist_structure(manifest, dist_dir)

    assert "does not contain any Python code" in caplog.text


def test_should_not_warn_when_requesting_no_lms_attributes(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    validate_requested_lms_attributes(manifest)

    assert len(get_warnings(caplog)) == 0


def test_should_not_warn_when_requesting_known_lms_attributes(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.permissions = PartialPackagePermissions(lms_attributes={"attempt_id", "lms_sdk_xyz", "profile_field_xyz"})

    validate_requested_lms_attributes(manifest)

    assert len(get_warnings(caplog)) == 0


def test_warn_when_requesting_unknown_lms_attributes(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.permissions = PartialPackagePermissions(lms_attributes={"foo", "bar"})

    validate_requested_lms_attributes(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "- foo" in warn_messages[0]
    assert "- bar" in warn_messages[0]


def test_warn_when_name_translations_are_missing(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.languages = [Bcp47LanguageTag("en"), Bcp47LanguageTag("de")]
    manifest.name = {Bcp47LanguageTag("en"): "Test Name"}

    validate_package_name_and_description(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "translations are missing" in warn_messages[0]
    assert "- de" in warn_messages[0]
    assert "- en" not in warn_messages[0]


def test_warn_when_description_translations_are_missing(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.languages = [Bcp47LanguageTag("en"), Bcp47LanguageTag("de")]
    manifest.name = {Bcp47LanguageTag("en"): "Test Name", Bcp47LanguageTag("de"): "Test Name"}
    manifest.description = {Bcp47LanguageTag("en"): "Test Name"}

    validate_package_name_and_description(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "translations are missing" in warn_messages[0]
    assert "- de" in warn_messages[0]
    assert "- en" not in warn_messages[0]


def test_warn_when_name_translation_is_give_in_missing_language(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.languages = [Bcp47LanguageTag("en")]
    manifest.name = {Bcp47LanguageTag("en"): "Test Name", Bcp47LanguageTag("de"): "Test Name"}

    validate_package_name_and_description(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "translations are given but missing" in warn_messages[0]
    assert "- de" in warn_messages[0]
    assert "- en" not in warn_messages[0]


def test_warn_when_description_translation_is_give_in_missing_language(
    manifest: Manifest, caplog: LogCaptureFixture
) -> None:
    manifest.languages = [Bcp47LanguageTag("en")]
    manifest.name = {Bcp47LanguageTag("en"): "Test Name"}
    manifest.description = {Bcp47LanguageTag("en"): "Test Description", Bcp47LanguageTag("de"): "Test Beschreibung"}

    validate_package_name_and_description(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "translations are given but missing" in warn_messages[0]
    assert "- de" in warn_messages[0]
    assert "- en" not in warn_messages[0]


def test_warn_when_description_is_given_but_not_in_english(manifest: Manifest, caplog: LogCaptureFixture) -> None:
    manifest.languages = [Bcp47LanguageTag("en"), Bcp47LanguageTag("de")]
    manifest.name = {Bcp47LanguageTag("en"): "Test Name", Bcp47LanguageTag("de"): "Test Name"}
    manifest.description = {Bcp47LanguageTag("de"): "Beschreibung"}

    validate_package_name_and_description(manifest)

    warn_messages = get_warnings(caplog)
    assert len(warn_messages) == 1
    assert "translations are missing" in warn_messages[0]
    assert "description should be available in English" in warn_messages[0]
