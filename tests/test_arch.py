from pytest_archon import archrule


def test_questionpy_should_not_import_sdk() -> None:
    (
        archrule("questionpy_should_not_import_sdk", comment="The questionpy package must work without the SDK.")
        .match("questionpy*")
        .should_not_import("questionpy_sdk*")
        .check("questionpy")
    )
