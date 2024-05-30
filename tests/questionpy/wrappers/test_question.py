#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json
from unittest.mock import ANY, patch

import pytest

from questionpy import (
    InvalidResponseError,
    NeedsManualScoringError,
    QuestionTypeWrapper,
    QuestionWrapper,
    ResponseNotScorableError,
)
from questionpy_common.api.attempt import AttemptModel, AttemptScoredModel, AttemptStartedModel, AttemptUi, ScoringCode
from questionpy_common.api.question import QuestionModel, ScoringMethod
from questionpy_common.environment import Package
from tests.questionpy.wrappers.conftest import (
    ATTEMPT_STATE_DICT,
    QUESTION_STATE_DICT,
    QuestionUsingMyQuestionState,
    SomeAttempt,
)


def test_should_start_attempt(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt_started_model = question.start_attempt(3)

    assert attempt_started_model == AttemptStartedModel.model_construct(
        attempt_state=ANY, lang="en", variant=3, ui=AttemptUi(formulation="")
    )
    assert json.loads(attempt_started_model.attempt_state) == ATTEMPT_STATE_DICT


def test_should_get_attempt(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt_model = question.get_attempt(json.dumps(ATTEMPT_STATE_DICT))

    assert attempt_model == AttemptModel(lang="en", variant=3, ui=AttemptUi(formulation=""))


def test_score_attempt_should_return_automatically_scored(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt_scored_model = question.score_attempt(json.dumps(ATTEMPT_STATE_DICT))

    assert attempt_scored_model == AttemptScoredModel(
        lang="en",
        variant=3,
        ui=AttemptUi(formulation=""),
        scoring_code=ScoringCode.AUTOMATICALLY_SCORED,
        score=1,
        score_final=1,
    )


@pytest.mark.parametrize(
    ("error", "expected_scoring_code"),
    [
        (ResponseNotScorableError(), ScoringCode.RESPONSE_NOT_SCORABLE),
        (InvalidResponseError(), ScoringCode.INVALID_RESPONSE),
        (NeedsManualScoringError(), ScoringCode.NEEDS_MANUAL_SCORING),
    ],
)
def test_score_attempt_should_handle_scoring_error(
    package: Package, error: Exception, expected_scoring_code: ScoringCode
) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert isinstance(question, QuestionWrapper)
    with patch.object(SomeAttempt, "_compute_score") as method:
        method.side_effect = error
        attempt_scored_model = question.score_attempt(json.dumps(ATTEMPT_STATE_DICT))

    assert attempt_scored_model == AttemptScoredModel(
        lang="en",
        variant=3,
        ui=AttemptUi(formulation=""),
        scoring_code=expected_scoring_code,
        score=None,
        score_final=None,
    )


def test_should_export_question_state(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    question_state = question.export_question_state()

    assert json.loads(question_state) == QUESTION_STATE_DICT


def test_should_export_question_model(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    question_model = question.export()

    assert question_model == QuestionModel(lang="en", scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)
