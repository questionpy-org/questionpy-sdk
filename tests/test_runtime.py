from io import StringIO
from typing import List

import pytest
from pydantic import ValidationError

from questionpy import Manifest, QuestionType
from questionpy.form import Form, TextInputElement, RadioGroupElement, SelectElement
from questionpy_sdk.messages import Message, CreateQuestionMessage, RenderEditForm, PingMessage, PongMessage
from questionpy_sdk.runtime import run_qtype
from questionpy_sdk.server import QPyPackageServer


class MockServer(QPyPackageServer):
    def __init__(self, queue: List[Message]):
        super().__init__(StringIO(), StringIO())
        self.queue: List[Message] = queue
        self.sent: List[Message] = []

    def __next__(self) -> Message:
        try:
            return self.queue.pop()
        except IndexError as e:
            raise StopIteration from e

    def send(self, message: Message) -> None:
        self.sent.append(message)


A_MANIFEST = Manifest(short_name="test", version="0.1.0", api_version="0.1", author="Alice Sample <alice@example.org>")


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


def test_valid_options() -> None:
    options = {
        "required": "123",
        "radio_group": "selected_value"
    }

    server = MockServer([CreateQuestionMessage(form_data=options)])

    class QType(QuestionType):
        def render_edit_form(self) -> Form:
            return Form(general=[
                TextInputElement(name="required", label="", required=True),
                TextInputElement(name="optional", label=""),
                RadioGroupElement(
                    name="radio_group",
                    label="",
                    buttons=[RadioGroupElement.Option(label="", value="selected_value")]
                )
            ])

    run_qtype(A_MANIFEST, QType, server)

    assert len(server.sent) == 1
    assert isinstance(server.sent[0], CreateQuestionMessage.Response)
    assert server.sent[0].state.dict() == {
        "required": "123",
        "optional": None,
        "radio_group": "selected_value"
    }


def test_missing_option() -> None:
    options = {
        "optional": "123"
    }

    class QType(QuestionType):
        def render_edit_form(self) -> Form:
            return Form(general=[
                TextInputElement(name="required", label="", required=True),
                TextInputElement(name="optional", label="")
            ])

    server = MockServer([CreateQuestionMessage(form_data=options)])

    with pytest.raises(ValidationError):
        run_qtype(A_MANIFEST, QType, server)

    assert not server.sent


def test_select_wrong_value() -> None:
    options = {
        "select": "anothervalue"
    }

    class QType(QuestionType):
        def render_edit_form(self) -> Form:
            return Form(general=[
                SelectElement(name="select", label="", options=[SelectElement.Option(label="", value="value1"),
                                                                SelectElement.Option(label="", value="value2")])
            ])

    server = MockServer([CreateQuestionMessage(form_data=options)])

    with pytest.raises(ValidationError):
        run_qtype(A_MANIFEST, QType, server)

    assert not server.sent


def test_select_multiple_wrong_value() -> None:
    options = {
        "select": {"value1", "anothervalue"}
    }

    class QType(QuestionType):
        def render_edit_form(self) -> Form:
            return Form(general=[
                SelectElement(name="select", label="", multiple=True,
                              options=[SelectElement.Option(label="", value="value1"),
                                       SelectElement.Option(label="", value="value2")])
            ])

    server = MockServer([CreateQuestionMessage(form_data=options)])

    with pytest.raises(ValidationError):
        run_qtype(A_MANIFEST, QType, server)

    assert not server.sent


def test_unsupported_message_type(caplog: pytest.LogCaptureFixture) -> None:
    server = MockServer([object()])  # type: ignore[list-item]

    run_qtype(A_MANIFEST, NoopQType, server)

    assert any("Unsupported message type: object" in record.message for record in caplog.records)
