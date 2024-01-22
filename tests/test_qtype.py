#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json
from collections.abc import Generator
from types import SimpleNamespace
from typing import Optional, cast

import pytest
from questionpy_common.environment import set_qpy_environment
from questionpy_common.models import QuestionModel, ScoringMethod, AttemptModel, AttemptUi
from questionpy_server.worker.runtime.manager import EnvironmentImpl
from questionpy_server.worker.runtime.package import ImportablePackage

from questionpy import QuestionType, Question, BaseQuestionState, Attempt, BaseAttemptState, Environment, RequestUser
from questionpy.form import FormModel, text_input


@pytest.fixture(autouse=True)
def environment() -> Generator[Environment, None, None]:
    env = EnvironmentImpl(
        type="test",
        limits=None,
        request_user=RequestUser(["en"]),
        main_package=cast(ImportablePackage, SimpleNamespace(manifest=SimpleNamespace(
            namespace="test_ns", short_name="test_package",
            version="1.2.3"
        ))),
        packages={},
        _on_request_callbacks=[]
    )
    set_qpy_environment(env)
    try:
        yield env
    finally:
        set_qpy_environment(None)


class SomeModel(FormModel):
    input: Optional[str] = text_input("Some Label")


class MyQuestionState(BaseQuestionState[SomeModel]):
    my_question_field: int = 42


class MyAttemptState(BaseAttemptState):
    my_attempt_field: int = 17


class SomeAttempt(Attempt["SomeQuestion", MyAttemptState]):
    def export(self) -> AttemptModel:
        return AttemptModel(variant=1, ui=AttemptUi(content=""))


class SomeQuestion(Question[MyQuestionState, SomeAttempt]):
    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


def test_should_use_type_arguments() -> None:
    class MyQType(QuestionType[SomeModel, SomeQuestion]):
        pass

    assert MyQType.options_class is SomeModel
    assert MyQType.question_class is SomeQuestion


def test_should_use_type_arguments_when_other_bases_exist() -> None:
    class AnotherBase:
        pass

    class YetAnotherBase:
        pass

    class MyQType(AnotherBase, QuestionType[SomeModel, SomeQuestion], YetAnotherBase):
        pass

    assert MyQType.options_class is SomeModel
    assert MyQType.question_class is SomeQuestion


def test_should_use_init_arguments() -> None:
    qtype = QuestionType(SomeModel, SomeQuestion)

    assert qtype.options_class is SomeModel
    assert qtype.question_class is SomeQuestion


def test_should_raise_when_unrelated_type_arg_is_given() -> None:
    with pytest.raises(TypeError, match="is not a subclass of FormModel"):
        # pylint: disable=unused-variable
        class MyQType(QuestionType[int, Question]):  # type: ignore[type-var] # (intentionally wrong)
            pass


def test_should_raise_when_type_args_are_missing() -> None:
    with pytest.raises(TypeError, match=r"Missing type argument on QuestionType \(type arg #1\)"):
        # pylint: disable=unused-variable
        class MyQType(QuestionType):
            pass


def test_should_raise_when_transitive_inheritance() -> None:
    # TODO: We should probably support this case in some way in the future.
    class Direct(QuestionType[SomeModel, SomeQuestion]):
        pass

    with pytest.raises(TypeError, match="Transitive is not a direct subclass of QuestionType"):
        # pylint: disable=unused-variable
        class Transitive(Direct):
            pass


def test_should_raise_with_different_form_models() -> None:
    class SomeModel2(SomeModel):
        pass

    with pytest.raises(TypeError, match="must have the same FormModel as"):
        # pylint: disable=unused-variable
        class MyQType(QuestionType[SomeModel2, SomeQuestion]):
            pass

    class SomeQuestion2(Question[BaseQuestionState[SomeModel2], SomeAttempt]):
        def export(self) -> QuestionModel:
            return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)

    with pytest.raises(TypeError, match="must have the same FormModel as"):
        # pylint: disable=unused-variable
        class MyQType2(QuestionType[SomeModel, SomeQuestion2]):
            pass


def test_should_raise_with_generic_form_model() -> None:
    with pytest.raises(TypeError, match="BaseQuestionState must declare a specific FormModel."):
        # pylint: disable=unused-variable
        class SomeQuestion2(Question[BaseQuestionState, SomeAttempt]):
            def export(self) -> QuestionModel:
                return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


QUESTION_STATE_DICT = {
    "package_name": "test_ns.test_package",
    "package_version": "1.2.3",
    "options": {
        "input": "something"
    },
    "my_question_field": 42
}

ATTEMPT_STATE_DICT = {
    "my_attempt_field": 17,
}


def test_should_create_question_from_options() -> None:
    qtype = QuestionType(SomeModel, SomeQuestion)
    question = qtype.create_question_from_options(None, {
        "input": "something"
    })

    assert isinstance(question, SomeQuestion)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_create_question_from_state() -> None:
    qtype = QuestionType(SomeModel, SomeQuestion)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert isinstance(question, SomeQuestion)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_start_attempt() -> None:
    qtype = QuestionType(SomeModel, SomeQuestion)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt = question.start_attempt(1)

    assert isinstance(attempt, SomeAttempt)
    assert json.loads(attempt.export_attempt_state()) == ATTEMPT_STATE_DICT


def test_should_view_attempt() -> None:
    qtype = QuestionType(SomeModel, SomeQuestion)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))
    attempt = question.view_attempt(json.dumps(ATTEMPT_STATE_DICT))

    assert isinstance(attempt, SomeAttempt)
    assert json.loads(attempt.export_attempt_state()) == ATTEMPT_STATE_DICT
