from io import StringIO

import pytest

from questionpy_sdk.messages import PingMessage
from questionpy_sdk.server import QPyPackageServer


def create_server(in_text: str) -> QPyPackageServer:
    in_stream = StringIO(in_text)
    out_stream = StringIO()
    return QPyPackageServer(in_stream, out_stream)


def test_read_message() -> None:
    server = create_server('{ "kind": "ping" }')
    assert next(server) == PingMessage()


@pytest.mark.parametrize("in_text", ("", "\n", " \t", " \t\n"))
def test_read_ignore(in_text: str) -> None:
    server = create_server(in_text)
    with pytest.raises(StopIteration):
        # We expect the server to ignore the input, skipping straight to EOF
        next(server)


# should ignore like test_read_ignore, but also log
@pytest.mark.parametrize("in_text", ("not json at all\n", '{ "kind": "unknown_kind" }\n'))
def test_read_invalid(in_text: str, caplog: pytest.LogCaptureFixture) -> None:
    server = create_server(in_text)
    with pytest.raises(StopIteration):
        # We expect the server to ignore the input, skipping straight to EOF
        next(server)

    assert any("invalid message" in record.message for record in caplog.records)
