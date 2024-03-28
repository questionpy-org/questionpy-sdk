#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel
from questionpy_sdk.webserver.question_ui import QuestionDisplayOptions, QuestionUIRenderer


def get_attempt_started_context(
    attempt: AttemptModel, last_attempt_data: dict, display_options: QuestionDisplayOptions, seed: int
) -> dict:
    renderer = QuestionUIRenderer(xml=attempt.ui.content, placeholders=attempt.ui.placeholders, seed=seed)
    return {
        "question_html": renderer.render_formulation(
            attempt=last_attempt_data, options=QuestionDisplayOptions(general_feedback=False, feedback=False)
        ),
        "options": display_options.model_dump(exclude={"context", "readonly"}),
        "form_disabled": False,
        "attempt": attempt,
    }


def get_attempt_scored_context(
    attempt: AttemptScoredModel, last_attempt_data: dict, display_options: QuestionDisplayOptions, seed: int
) -> dict:
    renderer = QuestionUIRenderer(xml=attempt.ui.content, placeholders=attempt.ui.placeholders, seed=seed)
    context = {
        "question_html": renderer.render_formulation(attempt=last_attempt_data, options=display_options),
        "options": display_options.model_dump(exclude={"context", "readonly"}),
        "form_disabled": True,
        "attempt": attempt,
    }

    if display_options.general_feedback:
        context["general_feedback"] = renderer.render_general_feedback(
            attempt=last_attempt_data, options=display_options
        )
    if display_options.feedback:
        context["specific_feedback"] = renderer.render_specific_feedback(
            attempt=last_attempt_data, options=display_options
        )
    if display_options.right_answer:
        context["right_answer"] = renderer.render_right_answer(attempt=last_attempt_data, options=display_options)
    return context
