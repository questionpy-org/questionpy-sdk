#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Literal, TypedDict

from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel
from questionpy_sdk.webserver.question_ui import (
    QuestionDisplayOptions,
    QuestionFormulationUIRenderer,
    QuestionUIRenderer,
)
from questionpy_server.api.models import AttemptStarted


class _AttemptRenderContext(TypedDict):
    attempt_status: Literal["Started", "In progress", "Scored"]

    attempt: AttemptModel
    attempt_state: str

    options: dict
    form_disabled: bool

    formulation: str
    general_feedback: str | None
    specific_feedback: str | None
    right_answer: str | None


def get_attempt_render_context(
    attempt: AttemptModel,
    attempt_state: str,
    *,
    last_attempt_data: dict,
    display_options: QuestionDisplayOptions,
    seed: int,
    disabled: bool,
) -> _AttemptRenderContext:
    renderer_args = (attempt.ui.placeholders, display_options, seed, last_attempt_data)

    context: _AttemptRenderContext = {
        "attempt_status": (
            "Started"
            if isinstance(attempt, AttemptStarted)
            else "Scored"
            if isinstance(attempt, AttemptScoredModel)
            else "In progress"
        ),
        "attempt_state": attempt_state,
        "options": display_options.model_dump(exclude={"context", "readonly"}),
        "form_disabled": disabled,
        "formulation": QuestionFormulationUIRenderer(attempt.ui.formulation, *renderer_args).html,
        "attempt": attempt,
        "general_feedback": None,
        "specific_feedback": None,
        "right_answer": None,
    }

    if display_options.general_feedback and attempt.ui.general_feedback:
        context["general_feedback"] = QuestionUIRenderer(attempt.ui.general_feedback, *renderer_args).html
    if display_options.feedback and attempt.ui.specific_feedback:
        context["specific_feedback"] = QuestionUIRenderer(attempt.ui.specific_feedback, *renderer_args).html
    if display_options.right_answer and attempt.ui.right_answer:
        context["right_answer"] = QuestionUIRenderer(attempt.ui.right_answer, *renderer_args).html

    return context
