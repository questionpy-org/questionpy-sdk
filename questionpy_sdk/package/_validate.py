import logging
from itertools import chain
from pathlib import Path

from questionpy_common.constants import MANIFEST_FILENAME
from questionpy_common.manifest import Manifest, PackageType

_log = logging.getLogger(__name__)


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
        f"python/{manifest.namespace}/{manifest.short_name}",
        "templates",
        "templates/**",
        "static",
        "static/js",
        "static/js/**",
        "static/css",
        "static/css/**",
        "static/assets",
        "static/assets/**",
        "resources",
        "resources/**",
        "dependencies",
        "dependencies/site-packages",
        "dependencies/site-packages/**",
        "dependencies/qpy",
        "dependencies/qpy/*-*-*",
        "dependencies/qpy/*-*-*/**",
        "locale",
        "locale/*",
        "locale/*/LC_MESSAGES",
    )


def validate_dist_structure(manifest: Manifest, dist: Path) -> None:
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

    if extra_paths and _log.isEnabledFor(logging.WARNING):
        path_list = "\n".join(f"\t- {path.relative_to(dist)}" for path in extra_paths)
        _log.warning(
            "The following files and dirs are unexpected in the built package.\n"
            "%s\n"
            "This may indicate a bad build script.",
            path_list,
        )
