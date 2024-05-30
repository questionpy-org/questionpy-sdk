#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from typing import Literal, TypedDict

from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel, AttemptStartedModel
from questionpy_sdk.webserver.question_ui import (
    QuestionDisplayOptions,
    QuestionFormulationUIRenderer,
    QuestionUIRenderer,
)
from questionpy_sdk.webserver.question_ui.errors import RenderErrorCollections, log_render_errors


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

    render_errors: RenderErrorCollections


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

    html, errors = QuestionFormulationUIRenderer(attempt.ui.formulation, *renderer_args).render()

    context: _AttemptRenderContext = {
        "attempt_status": (
            "Started"
            if isinstance(attempt, AttemptStartedModel)
            else "Scored"
            if isinstance(attempt, AttemptScoredModel)
            else "In progress"
        ),
        "attempt_state": attempt_state,
        "options": display_options.model_dump(include={"general_feedback", "feedback", "right_answer"}),
        "form_disabled": disabled,
        "formulation": html,
        "attempt": attempt,
        "general_feedback": None,
        "specific_feedback": None,
        "right_answer": None,
        "render_errors": {},
    }

    if errors:
        context["render_errors"]["Formulation"] = errors
    if display_options.general_feedback and attempt.ui.general_feedback:
        html, errors = QuestionUIRenderer(attempt.ui.general_feedback, *renderer_args).render()
        context["general_feedback"] = html
        context["render_errors"]["General Feedback"] = errors
    if display_options.feedback and attempt.ui.specific_feedback:
        html, errors = QuestionUIRenderer(attempt.ui.specific_feedback, *renderer_args).render()
        context["specific_feedback"] = html
        context["render_errors"]["Specific Feedback"] = errors
    if display_options.right_answer and attempt.ui.right_answer:
        html, errors = QuestionUIRenderer(attempt.ui.right_answer, *renderer_args).render()
        context["right_answer"] = html
        context["render_errors"]["Right Answer"] = errors

    log_render_errors(context["render_errors"])

    return context
