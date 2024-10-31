#!/usr/bin/env python3

#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

# TODO: Remove this entirely as it's not needed anymore when `create` relies on cookiecutter.
#       (Need to update tests which also rely on minimal_example.zip being available.)

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


def build(_setup_kwargs: Any) -> None:
    create_example_zip()


if __name__ == "__main__":
    build({})
