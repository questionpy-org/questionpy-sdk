#!/bin/sh

exec pytest --config-file=e2e/pytest.ini "$@"
