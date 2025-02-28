#!/usr/bin/env python3

#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from questionpy_sdk.resources import EXAMPLE_PACKAGE

COMPRESS_TYPE = zipfile.ZIP_DEFLATED


def create_example_zip() -> None:
    """Creates the minimal_example.zip required by the `create` command."""
    minimal_example = Path(__file__).parent / "examples" / "minimal"
    with zipfile.ZipFile(EXAMPLE_PACKAGE, "w", COMPRESS_TYPE) as zip_file:
        for file in minimal_example.rglob("*"):
            if "__pycache__" not in file.parts:
                zip_file.write(file, file.relative_to(minimal_example), COMPRESS_TYPE)


def _run_command(args: list[str], rel_path: str) -> None:
    cwd = Path(__file__).parent.absolute() / rel_path
    try:
        subprocess.run(args, cwd=cwd, check=True, text=True, stdout=sys.stdout, stderr=sys.stderr)  # noqa: S603
    except subprocess.CalledProcessError as e:
        msg = f"npm build failed with exit code {e.returncode}"
        raise RuntimeError(msg) from e


def build_frontend() -> None:
    _run_command(["npm", "ci", "--ignore-scripts"], "frontend")
    _run_command(["npm", "run", "build"], "frontend")


def build(_setup_kwargs: Any) -> None:
    create_example_zip()
    build_frontend()


if __name__ == "__main__":
    build({})
