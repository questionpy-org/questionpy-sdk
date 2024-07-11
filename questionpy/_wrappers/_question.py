#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json

from pydantic import JsonValue

from questionpy import Attempt, Question
from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel, AttemptStartedModel, AttemptUi, ScoreModel
from questionpy_common.api.question import QuestionInterface, QuestionModel
from questionpy_common.environment import get_qpy_environment


def _get_output_lang() -> str:
    # TODO: Do something more meaningful per default and allow the package to override.
    env = get_qpy_environment()
    supported_langs = env.main_package.manifest.languages
    preferred_langs = env.request_user.preferred_languages if env.request_user else ()
    supported_and_preferred_langs = [lang for lang in preferred_langs if lang in supported_langs]
    if supported_and_preferred_langs:
        # Use the most preferred supported language if any.
        return supported_and_preferred_langs[0]

    if supported_langs:
        # If no preferred language is supported, use any supported one.
        return next(iter(supported_langs))

    # If the package lists no supported languages, fall back to english.
    return "en"


def _export_question(question: Question) -> QuestionModel:
    return QuestionModel(
        lang=_get_output_lang(),
        num_variants=question.num_variants,
        score_min=question.score_min,
        score_max=question.score_max,
        scoring_method=question.scoring_method,
        penalty=question.penalty,
        random_guess_score=question.random_guess_score,
        response_analysis_by_variant=question.response_analysis_by_variant,
        subquestions=question.subquestions,
    )


def _export_attempt(attempt: Attempt) -> AttemptModel:
    return AttemptModel(
        lang=_get_output_lang(),
        variant=attempt.attempt_state.variant,
        ui=AttemptUi(
            formulation=attempt.formulation,
            general_feedback=attempt.general_feedback,
            specific_feedback=attempt.specific_feedback,
            right_answer=attempt.right_answer_description,
            placeholders=attempt.placeholders,
            css_files=attempt.css_files,
            files=attempt.files,
            cache_control=attempt.cache_control,
        ),
    )


def _export_score(attempt: Attempt) -> ScoreModel:
    plain_scoring_state = attempt.to_plain_scoring_state()
    return ScoreModel(
        scoring_state=None if plain_scoring_state is None else json.dumps(plain_scoring_state),
        scoring_code=attempt.scoring_code,
        score=attempt.score,
        score_final=attempt.score_final,
        scored_inputs=attempt.scored_inputs,
        scored_subquestions={},
    )


class QuestionWrapper(QuestionInterface):
    def __init__(self, question: Question) -> None:
        self._question = question

    def start_attempt(self, variant: int) -> AttemptStartedModel:
        attempt = self._question.start_attempt(variant)
        plain_attempt_state = attempt.to_plain_attempt_state()
        return AttemptStartedModel(
            **_export_attempt(attempt).model_dump(), attempt_state=json.dumps(plain_attempt_state)
        )

    def _get_attempt_internal(
        self,
        attempt_state: str,
        scoring_state: str | None = None,
        response: dict[str, JsonValue] | None = None,
    ) -> Attempt:
        plain_attempt_state = json.loads(attempt_state)
        plain_scoring_state = None
        if scoring_state:
            plain_scoring_state = json.loads(scoring_state)

        return self._question.get_attempt(plain_attempt_state, plain_scoring_state, response)

    def get_attempt(
        self, attempt_state: str, scoring_state: str | None = None, response: dict[str, JsonValue] | None = None
    ) -> AttemptModel:
        return _export_attempt(self._get_attempt_internal(attempt_state, scoring_state, response))

    def score_attempt(
        self,
        attempt_state: str,
        scoring_state: str | None = None,
        response: dict[str, JsonValue] | None = None,
        *,
        try_scoring_with_countback: bool = False,
        try_giving_hint: bool = False,
    ) -> AttemptScoredModel:
        attempt = self._get_attempt_internal(attempt_state, scoring_state, response)
        attempt.score_response(try_scoring_with_countback=try_scoring_with_countback, try_giving_hint=try_giving_hint)
        return AttemptScoredModel(**_export_attempt(attempt).model_dump(), **_export_score(attempt).model_dump())

    def export_question_state(self) -> str:
        plain_state = self._question.to_plain_state()
        return json.dumps(plain_state)

    def export(self) -> QuestionModel:
        return _export_question(self._question)
