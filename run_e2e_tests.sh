#!/bin/sh

# https://playwright.dev/python/docs/test-runners#async-fixtures
exec pytest \
    --override-ini asyncio_default_test_loop_scope=session \
    --override-ini asyncio_default_fixture_loop_scope=session \
    e2e/ \
    "$@"
