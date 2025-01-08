#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json

import pytest

from questionpy import OptionsFormValidationError, Question, QuestionTypeWrapper, QuestionWrapper
from questionpy.form import FormModel, is_not_checked, text_input
from questionpy.form.validation import FormError
from questionpy_common.elements import OptionsFormDefinition, TextInputElement
from questionpy_common.environment import Package
from tests.questionpy.wrappers.conftest import (
    QUESTION_STATE_DICT,
    STATIC_FILES,
    QuestionUsingDefaultState,
    QuestionUsingMyQuestionState,
    SomeAttempt,
)

_EXPECTED_FORM = OptionsFormDefinition(general=[TextInputElement(name="input", label="Some Label")])


def test_should_get_options_form_for_new_question(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)

    form, data = qtype.get_options_form(None)

    assert form == _EXPECTED_FORM
    assert data == {}


def test_should_get_options_form_for_existing_question(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)

    form, data = qtype.get_options_form(json.dumps(QUESTION_STATE_DICT))

    assert form == _EXPECTED_FORM
    assert data == {"input": "something"}


def test_should_create_question_from_options(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_options(None, {"input": "something"})

    assert isinstance(question, QuestionWrapper)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_raise_options_form_validation_error_when_creating_question_from_invalid_options(
    package: Package,
) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    with pytest.raises(OptionsFormValidationError) as exc_info:
        qtype.create_question_from_options(None, {"input": 1})

    assert exc_info.value.errors == {"input": "Input should be a valid string"}


def test_should_create_question_from_state(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingMyQuestionState, package)
    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert isinstance(question, QuestionWrapper)
    assert json.loads(question.export_question_state()) == QUESTION_STATE_DICT


def test_should_preserve_options_when_using_default_question_state(package: Package) -> None:
    qtype = QuestionTypeWrapper(QuestionUsingDefaultState, package)

    question = qtype.create_question_from_state(json.dumps(QUESTION_STATE_DICT))

    assert json.loads(question.export_question_state())["options"] == QUESTION_STATE_DICT["options"]


def test_should_get_static_files(package: Package) -> None:
    package.manifest.static_files = STATIC_FILES


def test_should_raise_when_form_is_invalid(package: Package) -> None:
    class ModelWithUnresolvedReference(FormModel):
        my_text: str | None = text_input("Label", hide_if=is_not_checked("nonexistent_checkbox"))

    class MyQuestion(Question):
        attempt_class = SomeAttempt
        options: ModelWithUnresolvedReference

    # There are more detailed validation tests in test_validation.py, here we just ensure that validate_form is called
    # at the correct place.
    with pytest.raises(FormError):
        QuestionTypeWrapper(MyQuestion, package)
