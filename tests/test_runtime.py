import pytest

from questionpy import QuestionType
from questionpy.form import Form, TextInputElement
from questionpy_sdk.messages import RenderEditForm, PingMessage, PongMessage
from questionpy_sdk.runtime import run_qtype
from tests.mocks import MockServer, A_MANIFEST


class NoopQType(QuestionType):
    def render_edit_form(self) -> Form:
        return Form()


def test_ping() -> None:
    server = MockServer([PingMessage()])

    run_qtype(A_MANIFEST, NoopQType, server)

    assert server.sent == [PongMessage()]


def test_render_edit_form() -> None:
    server = MockServer([RenderEditForm()])

    form = Form(general=[
        TextInputElement(name="required", label="", required=True),
        TextInputElement(name="optional", label="")
    ])

    class QType(QuestionType):
        def render_edit_form(self) -> Form:
            return form

    run_qtype(A_MANIFEST, QType, server)

    assert server.sent == [RenderEditForm.Response(form=form)]


def test_unsupported_message_type(caplog: pytest.LogCaptureFixture) -> None:
    server = MockServer([object()])  # type: ignore[list-item]

    run_qtype(A_MANIFEST, NoopQType, server)

    assert any("Unsupported message type: object" in record.message for record in caplog.records)
