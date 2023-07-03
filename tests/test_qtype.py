#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Optional

import pytest

from questionpy import QuestionType
from questionpy.form import FormModel, text_input


class SomeModel(FormModel):
    input: Optional[str] = text_input("Some Label")


def test_should_detect_generic_parameter_when_given() -> None:
    class MyQType(QuestionType[SomeModel]):
        pass

    assert MyQType.form_model is SomeModel


def test_should_use_FormModel_when_no_parameter_is_given() -> None:
    class MyQType(QuestionType):
        pass

    assert MyQType.form_model is FormModel


def test_should_use_FormModel_when_no_parameter_is_given_and_another_base_exists() -> None:
    class AnotherBase:
        # pylint: disable=too-few-public-methods
        pass

    class MyQType(QuestionType, AnotherBase):
        pass

    assert MyQType.form_model is FormModel


def test_should_raise_when_unrelated_parameter_is_given() -> None:
    with pytest.raises(TypeError, match="is not a subclass of FormModel"):
        class MyQType(QuestionType[int]):  # type: ignore[type-var] # (intentionally wrong)
            # pylint: disable=unused-variable
            pass
