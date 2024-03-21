#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json
from collections.abc import Generator
from types import SimpleNamespace
from typing import cast

import pytest
from questionpy_common.api.attempt import AttemptModel, AttemptUi, ScoreModel, ScoringCode
from questionpy_common.api.question import QuestionModel, ScoringMethod
from questionpy_common.environment import set_qpy_environment
from questionpy_server.worker.runtime.manager import EnvironmentImpl
from questionpy_server.worker.runtime.package import ImportablePackage

from questionpy import (
    Attempt,
    BaseAttemptState,
    BaseQuestionState,
    Environment,
    Question,
    QuestionType,
    RequestUser,
)
from questionpy.form import FormModel, text_input


@pytest.fixture(autouse=True)
def environment() -> Generator[Environment, None, None]:
    env = EnvironmentImpl(
        type="test",
        limits=None,
        request_user=RequestUser(["en"]),
        main_package=cast(
            ImportablePackage,
            SimpleNamespace(manifest=SimpleNamespace(namespace="test_ns", short_name="test_package", version="1.2.3")),
        ),
        packages={},
        _on_request_callbacks=[],
    )
    set_qpy_environment(env)
    try:
        yield env
    finally:
        set_qpy_environment(None)


class SomeModel(FormModel):
    input: str | None = text_input("Some Label")


class MyQuestionState(BaseQuestionState[SomeModel]):
    my_question_field: int = 42


class MyAttemptState(BaseAttemptState):
    my_attempt_field: int = 17


class SomeAttempt(Attempt):
    attempt_state_class = MyAttemptState

    def export(self) -> AttemptModel:
        return AttemptModel(variant=1, ui=AttemptUi(content=""))

    def export_score(self) -> ScoreModel:
        return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=1)


class QuestionUsingDefaultState(Question):
    attempt_class = SomeAttempt

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class QuestionUsingMyQuestionState(Question):
    attempt_class = SomeAttempt
    state_class = MyQuestionState

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


def test_should_use_init_arguments() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingDefaultState)

    assert qtype.options_class is SomeModel
    assert qtype.question_class is QuestionUsingDefaultState


class SomeModel2(SomeModel):
    # Mypy crashes for some reason if this is local in test_should_raise_with_different_explicit_form_models.
    pass


def test_should_raise_with_different_explicit_form_models() -> None:
    with pytest.raises(TypeError, match="must have the same FormModel as"):
        QuestionType(options_class=SomeModel2, question_class=QuestionUsingMyQuestionState)


QUESTION_STATE_DICT = {
    "package_name": "test_ns.test_package",
    "package_version": "1.2.3",
    "options": {"input": "something"},
    "my_question_field": 42,
}

ATTEMPT_STATE_DICT = {
    "variant": 3,
    "my_attempt_field": 17,
}


def test_should_deserialize_correct_options_when_using_BaseQuestionState() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingDefaultState)

    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert question.state.options == SomeModel(input="something")


def test_should_create_question_from_options() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingMyQuestionState)
    question = qtype.create_question_from_options(None, {"input": "something"})

    assert isinstance(question, QuestionUsingMyQuestionState)
    assert isinstance(question.state, MyQuestionState)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_create_question_from_state() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingMyQuestionState)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert isinstance(question, QuestionUsingMyQuestionState)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_start_attempt() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingDefaultState)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt = question.start_attempt(3)

    assert isinstance(attempt, SomeAttempt)
    assert json.loads(attempt.export_attempt_state()) == ATTEMPT_STATE_DICT


def test_should_get_attempt() -> None:
    qtype = QuestionType(SomeModel, QuestionUsingDefaultState)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt = question.get_attempt(json.dumps(ATTEMPT_STATE_DICT))

    assert isinstance(attempt, SomeAttempt)
    assert json.loads(attempt.export_attempt_state()) == ATTEMPT_STATE_DICT
