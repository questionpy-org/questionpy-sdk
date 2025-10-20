import logging
import re
from itertools import chain
from pathlib import Path

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_common.manifest import Bcp47LanguageTag, Manifest, PackageType

_log = logging.getLogger(__name__)


KNOWN_LMS_ATTRIBUTES: set[str] = {
    # LMS
    "course_id",
    "attempt_id",
    "attempt_started_at",
    "submissions_at",
    # Group
    "group_id",
    "group_name",
    # User
    "user_id",
    "login_identifier",
    "emaildisplay_name",
    "first_name",
    "last_name",
}

KNOWN_CUSTOM_LMS_ATTRIBUTE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^lms_[a-z\d]+_[a-z\d_]+$"),
    re.compile(r"^profile_field_[a-z\d_]+$"),
]


def _get_required_file_globs(manifest: Manifest) -> dict[str, str]:
    rules = {MANIFEST_FILENAME: "Package does not contain a manifest."}

    # This should allow for Asset-only packages once those are implemented.
    # https://github.com/questionpy-org/questionpy-sdk/issues/202
    if manifest.type in {PackageType.QUESTIONTYPE, PackageType.QUESTION, PackageType.LIBRARY}:
        rules.update({
            f"python/{manifest.namespace}/{manifest.short_name}/**/*.py":
                f"Package does not contain any Python code under '{manifest.namespace}.{manifest.short_name}'."
        })  # fmt: skip

    return rules


def _get_allowed_file_globs() -> tuple[str, ...]:
    return (
        "templates/**/*",
        "static/js/**/*",
        "static/css/**/*",
        "static/assets/**/*",
        "resources/**/*",
        "dependencies/site-packages/**/*",
        "dependencies/qpy/*-*-*/**/*",
        "locale/*/LC_MESSAGES/*.*.mo",
    )


def _get_allowed_dir_globs(manifest: Manifest) -> tuple[str, ...]:
    return (
        "python",
        f"python/{manifest.namespace}",
        f"python/{manifest.namespace}/{manifest.short_name}/**",
        "templates/**",
        "static",
        "static/js/**",
        "static/css/**",
        "static/assets/**",
        "resources/**",
        "dependencies",
        "dependencies/site-packages/**",
        "dependencies/qpy",
        "dependencies/qpy/*-*-*/**",
        "locale",
        "locale/*",
        "locale/*/LC_MESSAGES",
    )


def validate_dist_structure(manifest: Manifest, dist: Path) -> None:
    if not _log.isEnabledFor(logging.WARNING):
        return

    required_file_globs = _get_required_file_globs(manifest)
    allowed_file_globs = {*required_file_globs.keys(), *_get_allowed_file_globs()}
    allowed_dir_globs = _get_allowed_dir_globs(manifest)

    for glob, missing_message in required_file_globs.items():
        if next(dist.glob(glob), None) is None:
            _log.warning("%s", missing_message)

    extra_paths = set(dist.glob("**/*"))
    allowed_path: Path
    for allowed_path in chain.from_iterable(dist.glob(glob) for glob in allowed_file_globs):
        if allowed_path.is_file():
            extra_paths.discard(allowed_path)
    for allowed_path in chain.from_iterable(dist.glob(glob) for glob in allowed_dir_globs):
        if allowed_path.is_dir():
            extra_paths.discard(allowed_path)

    if extra_paths:
        path_list = "\n".join(f"\t- {path.relative_to(dist)}" for path in extra_paths)
        _log.warning(
            "The following files and dirs are unexpected in the built package.\n"
            "%s\n"
            "This may indicate a bad build script.",
            path_list,
        )


def _is_known_attribute(attribute: str) -> bool:
    return attribute in KNOWN_LMS_ATTRIBUTES or any(
        pattern.fullmatch(attribute) for pattern in KNOWN_CUSTOM_LMS_ATTRIBUTE_PATTERNS
    )


def validate_requested_lms_attributes(manifest: Manifest) -> None:
    if not (_log.isEnabledFor(logging.WARNING) and manifest.permissions and manifest.permissions.lms_attributes):
        return

    unknown_attributes = [
        attribute for attribute in manifest.permissions.lms_attributes if not _is_known_attribute(attribute)
    ]

    if unknown_attributes:
        unknown_attribute_list = "\n\t- " + "\n\t- ".join(unknown_attributes)
        _log.warning("The following LMS attributes are requested but unknown:%s", unknown_attribute_list)


def validate_package_name_and_description(manifest: Manifest) -> None:
    if not _log.isEnabledFor(logging.WARNING):
        return

    declared_translations = set(manifest.languages)
    name_translations = set(manifest.name.keys())
    description_translations = set(manifest.description.keys())

    if missing_name_translations := name_translations.difference(declared_translations):
        missing_translations_list = "\n\t- " + "\n\t- ".join(missing_name_translations)
        _log.warning("The following package name translations are missing:%s", missing_translations_list)

    if unused_name_translations := declared_translations.difference(name_translations):
        unused_translations_list = "\n\t- " + "\n\t- ".join(unused_name_translations)
        _log.warning(
            "The following package name translations are given but missing in the languages list:%s",
            unused_translations_list,
        )

    if description_translations:
        if missing_description_translations := description_translations.difference(declared_translations):
            missing_translations_list = "\n\t- " + "\n\t- ".join(missing_description_translations)
            _log.warning("The following package description translations are missing:%s", missing_translations_list)

        if unused_description_translations := declared_translations.difference(description_translations):
            unused_translations_list = "\n\t- " + "\n\t- ".join(unused_description_translations)
            message = "The following package description translations are given but missing in the languages list:%s"
            if Bcp47LanguageTag("en") in unused_description_translations:
                message += "\nThe package description should be available in English as it is used as a fallback."
            _log.warning(
                message,
                unused_translations_list,
            )
