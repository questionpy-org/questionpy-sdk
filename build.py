#!/usr/bin/env python3

#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from pathlib import Path
from typing import Any
from zipfile import ZipFile

from questionpy_sdk.resources import EXAMPLE_PACKAGE


def create_example_zip():
    """ Creates the example.zip required by the `create` command."""
    example = Path("example")
    with ZipFile(EXAMPLE_PACKAGE, "w") as zip_file:
        for file in example.rglob("*"):
            zip_file.write(file, file.relative_to(example))


def build(_setup_kwargs: Any):
    create_example_zip()


if __name__ == '__main__':
    build({})
