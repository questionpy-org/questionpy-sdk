import logging
from typing import Type, Union

from questionpy import Manifest, QuestionType
from questionpy.form import CheckboxElement, HiddenElement, RadioGroupElement, SelectElement, \
    TextInputElement
from questionpy_sdk.messages import PingMessage, PongMessage, RenderEditForm, CreateQuestionMessage
from questionpy_sdk.server import QPyPackageServer

log = logging.getLogger(__name__)

RelevantFormElement = Union[TextInputElement, CheckboxElement, HiddenElement, RadioGroupElement, SelectElement]
"""
Union of the form elements which produce options on submission.
"""


def run_qtype(manifest: Manifest, qtype: Type[QuestionType], server: QPyPackageServer) -> None:
    qtype_instance = qtype(manifest=manifest)

    log.info("Running question type '%s:%s' with manifest '%s'",
             qtype.__module__, qtype.__name__, manifest)

    for message in server:
        if isinstance(message, PingMessage):
            server.send(PongMessage())
        elif isinstance(message, RenderEditForm):
            server.send(RenderEditForm.Response(form=qtype_instance.render_edit_form()))
        elif isinstance(message, CreateQuestionMessage):
            server.send(CreateQuestionMessage.Response(state=qtype_instance.validate_options(message.form_data)))
        else:
            log.error("Unsupported message type: %s", type(message).__name__)
