#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from importlib.resources import as_file, files


with as_file(files(__package__)) as directory:
    EXAMPLE_PACKAGE = directory / "example.zip"
