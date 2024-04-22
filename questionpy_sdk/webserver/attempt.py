#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import TypedDict

from questionpy_common.api.attempt import AttemptModel, AttemptUi
from questionpy_sdk.webserver.question_ui import QuestionDisplayOptions, QuestionUIRenderer


class _AttemptRenderContext(TypedDict):
    attempt: AttemptModel
    options: dict
    form_disabled: bool

    formulation: str
    general_feedback: str | None
    specific_feedback: str | None
    right_answer: str | None


def _render_part(
    ui: AttemptUi, part: str, last_attempt_data: dict, display_options: QuestionDisplayOptions, seed: int
) -> str:
    return QuestionUIRenderer(part, ui.placeholders, seed).render(last_attempt_data, display_options)


def get_attempt_render_context(
    attempt: AttemptModel,
    *,
    last_attempt_data: dict,
    display_options: QuestionDisplayOptions,
    seed: int,
    disabled: bool,
) -> _AttemptRenderContext:
    context: _AttemptRenderContext = {
        "options": display_options.model_dump(exclude={"context", "readonly"}),
        "form_disabled": disabled,
        "formulation": _render_part(attempt.ui, attempt.ui.formulation, last_attempt_data, display_options, seed),
        "attempt": attempt,
        "general_feedback": None,
        "specific_feedback": None,
        "right_answer": None,
    }

    if display_options.general_feedback and attempt.ui.general_feedback:
        context["general_feedback"] = _render_part(
            attempt.ui, attempt.ui.general_feedback, last_attempt_data, display_options, seed
        )
    if display_options.feedback and attempt.ui.specific_feedback:
        context["specific_feedback"] = _render_part(
            attempt.ui, attempt.ui.specific_feedback, last_attempt_data, display_options, seed
        )
    if display_options.right_answer and attempt.ui.right_answer:
        context["right_answer"] = _render_part(
            attempt.ui, attempt.ui.right_answer, last_attempt_data, display_options, seed
        )

    return context
