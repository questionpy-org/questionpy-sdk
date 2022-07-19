from typing import Annotated, Any, Dict, Literal, Union

from pydantic import BaseModel, Field

from questionpy.form import Form


class PingMessage(BaseModel):
    kind: Literal["ping"] = "ping"


class PongMessage(BaseModel):
    kind: Literal["pong"] = "pong"


class RenderEditForm(BaseModel):
    kind: Literal["render_edit_form"] = "render_edit_form"

    class Response(BaseModel):
        kind: Literal["edit_form_response"] = "edit_form_response"
        form: Form


class CreateQuestionMessage(BaseModel):
    kind: Literal["create_question"] = "create_question"
    form_data: Dict[str, Any]

    class Response(BaseModel):
        kind: Literal["question_state"] = "question_state"
        state: BaseModel


Message = Annotated[
    Union[
        PingMessage, PongMessage,
        RenderEditForm, RenderEditForm.Response,
        CreateQuestionMessage, CreateQuestionMessage.Response
    ],
    Field(discriminator="kind")
]
