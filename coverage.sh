#!/bin/sh

printf -- 'running flake8 \n'
flake8 questionpy questionpy_sdk tests

printf -- 'running pylint \n'
pylint questionpy questionpy_sdk tests

printf -- 'running pytest \n'
coverage run -m pytest tests
coverage report

printf -- 'running mypy \n'
mypy questionpy questionpy_sdk tests
