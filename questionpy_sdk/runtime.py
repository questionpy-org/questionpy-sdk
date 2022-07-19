import logging
from itertools import chain
from typing import Type, Any, Dict, Union

from pydantic import BaseModel, create_model

from questionpy import Manifest, QuestionType
from questionpy.form import Form, CheckboxElement, HiddenElement, RadioGroupElement, SelectElement, \
    TextInputElement, Submittable
from questionpy_sdk.messages import PingMessage, PongMessage, RenderEditForm, CreateQuestionMessage
from questionpy_sdk.server import QPyPackageServer

log = logging.getLogger(__name__)

RelevantFormElement = Union[TextInputElement, CheckboxElement, HiddenElement, RadioGroupElement, SelectElement]
"""
Union of the form elements which produce options on submission.
"""


def _form_to_model(form: Form) -> Type[BaseModel]:
    """
    Generates a pydantic model from the given form describing the expected options when the form is submitted.
    The model can be used for validation of submitted form data.
    """
    all_elements = [*form.general, *chain.from_iterable(section.elements for section in form.sections)]
    fields: Dict[str, Any] = {element.name: element.to_model_field() for element in all_elements if
                              isinstance(element, Submittable)}
    return create_model("Options", **fields)


def _parse_options(qtype: QuestionType, options: Dict[str, Any]) -> BaseModel:
    # FIXME: We use a new form here, but a question type may choose to generate a new form on each invocation, so we
    #        should get the one which was submitted instead.
    form = qtype.render_edit_form()
    model = _form_to_model(form)
    return model.parse_obj(options)


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
            parsed_options = _parse_options(qtype_instance, message.form_data)
            server.send(CreateQuestionMessage.Response(state=qtype_instance.validate_options(parsed_options)))
        else:
            log.error("Unsupported message type: %s", type(message).__name__)
