#!/bin/sh

#
# This file is part of the QuestionPy SDK. (https://questionpy.org)
# The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
# (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
#

printf -- 'running flake8 \n'
flake8 questionpy questionpy_sdk tests

printf -- 'running pylint \n'
pylint questionpy questionpy_sdk tests

printf -- 'running pytest \n'
coverage run -m pytest tests
coverage report

printf -- 'running mypy \n'
mypy questionpy questionpy_sdk tests
