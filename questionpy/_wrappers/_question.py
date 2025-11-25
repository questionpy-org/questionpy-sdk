#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json

from pydantic import JsonValue

from questionpy import Question, i18n
from questionpy._attempt import AttemptProtocol, AttemptScoredProtocol
from questionpy_common import TranslatableString
from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel, AttemptStartedModel, AttemptUi
from questionpy_common.api.files import EditorData, ResponseFile
from questionpy_common.api.question import QuestionInterface, QuestionModel
from questionpy_common.environment import get_qpy_environment
from questionpy_common.manifest import Bcp47LanguageTag


def _get_output_lang() -> Bcp47LanguageTag:
    return i18n.get_primary_language(get_qpy_environment().main_package)


def _str_or_none(string: str | TranslatableString | None) -> str | None:
    if string is None:
        return None
    return str(string)


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


def _export_attempt(attempt: AttemptProtocol) -> dict:
    return {
        "lang": _get_output_lang(),
        "variant": attempt.variant,
        "ui": AttemptUi(
            formulation=str(attempt.formulation),
            general_feedback=_str_or_none(attempt.general_feedback),
            specific_feedback=_str_or_none(attempt.specific_feedback),
            right_answer=_str_or_none(attempt.right_answer_description),
            placeholders={key: str(value) for key, value in attempt.placeholders.items()},
            css_files=attempt.css_files,
            javascript_calls=attempt.javascript_calls,
            files=attempt.files,
            cache_control=attempt.cache_control,
        ),
    }


def _export_score(attempt: AttemptScoredProtocol) -> dict:
    plain_scoring_state = attempt.to_plain_scoring_state()
    return {
        "scoring_state": None if plain_scoring_state is None else json.dumps(plain_scoring_state),
        "scoring_code": attempt.scoring_code,
        "score": attempt.score,
        "score_adjusted": attempt.score_adjusted,
        "scored_inputs": attempt.scored_inputs,
        "scored_subquestions": {},
    }


class QuestionWrapper(QuestionInterface):
    def __init__(self, question: Question) -> None:
        self._question = question

    def start_attempt(self, variant: int) -> AttemptStartedModel:
        attempt = self._question.start_attempt(variant)
        plain_attempt_state = attempt.to_plain_attempt_state()
        return AttemptStartedModel(**_export_attempt(attempt), attempt_state=json.dumps(plain_attempt_state))

    def get_attempt(
        self,
        attempt_state: str,
        scoring_state: str | None = None,
        response: dict[str, JsonValue] | None = None,
        uploads: dict[str, list[ResponseFile]] | None = None,
        editors: dict[str, EditorData[ResponseFile]] | None = None,
    ) -> AttemptModel:
        parsed_attempt_state = json.loads(attempt_state)
        parsed_scoring_state = None
        if scoring_state:
            parsed_scoring_state = json.loads(scoring_state)

        attempt = self._question.get_attempt(parsed_attempt_state, parsed_scoring_state, response, uploads, editors)
        return AttemptModel(**_export_attempt(attempt))

    def score_attempt(
        self,
        attempt_state: str,
        scoring_state: str | None,
        response: dict[str, JsonValue],
        uploads: dict[str, list[ResponseFile]],
        editors: dict[str, EditorData[ResponseFile]],
        *,
        compute_adjusted_score: bool = False,
        generate_hint: bool = False,
    ) -> AttemptScoredModel:
        parsed_attempt_state = json.loads(attempt_state)
        parsed_scoring_state = None
        if scoring_state:
            parsed_scoring_state = json.loads(scoring_state)

        attempt = self._question.score_attempt(
            parsed_attempt_state,
            parsed_scoring_state,
            response,
            uploads,
            editors,
            compute_adjusted_score=compute_adjusted_score,
            generate_hint=generate_hint,
        )
        return AttemptScoredModel(**_export_attempt(attempt), **_export_score(attempt))

    def export_question_state(self) -> str:
        plain_state = self._question.to_plain_state()
        return json.dumps(plain_state)

    def export(self) -> QuestionModel:
        return _export_question(self._question)
