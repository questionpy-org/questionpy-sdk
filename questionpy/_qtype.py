#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from abc import ABC
from typing import Generic, TypeVar, cast

from pydantic import BaseModel, ValidationError

from questionpy_common.api.attempt import BaseAttempt
from questionpy_common.api.qtype import BaseQuestionType, OptionsFormValidationError
from questionpy_common.api.question import BaseQuestion
from questionpy_common.environment import get_qpy_environment

from ._attempt import Attempt
from .form import FormModel, OptionsFormDefinition

_F = TypeVar("_F", bound=FormModel)
_QS = TypeVar("_QS", bound="BaseQuestionState")
_A = TypeVar("_A", bound=Attempt)
_Q = TypeVar("_Q", bound="Question")


class BaseQuestionState(BaseModel, Generic[_F]):
    package_name: str
    package_version: str
    options: _F


class Question(BaseQuestion, ABC, Generic[_QS, _A]):
    state_class: type[BaseQuestionState] = BaseQuestionState
    attempt_class: type["Attempt"]

    def __init__(self, qtype: BaseQuestionType, state: _QS) -> None:
        self.qtype = qtype
        self.state = state

    def start_attempt(self, variant: int) -> BaseAttempt:
        attempt_state = self.attempt_class.attempt_state_class(variant=variant)
        return self.attempt_class(self, attempt_state)

    def get_attempt(
        self,
        attempt_state: str,
        scoring_state: str | None = None,
        response: dict | None = None,
        *,
        compute_score: bool = False,
        generate_hint: bool = False,
    ) -> BaseAttempt:
        attempt_state_obj = self.attempt_class.attempt_state_class.model_validate_json(attempt_state)
        scoring_state_obj = None
        if scoring_state is not None:
            scoring_state_obj = self.attempt_class.scoring_state_class.model_validate_json(scoring_state)
        return self.attempt_class(self, attempt_state_obj, response, scoring_state_obj)

    def export_question_state(self) -> str:
        return self.state.model_dump_json()

    def __init_subclass__(cls, *args: object, **kwargs: object) -> None:
        super().__init_subclass__(*args, **kwargs)

        if not hasattr(cls, "attempt_class"):
            msg = f"Missing '{cls.__name__}.attempt_class' attribute. It should point to your attempt implementation"
            raise TypeError(msg)


class QuestionType(BaseQuestionType, Generic[_F, _Q]):
    """A question type.

    This class is intended to be used in one of two ways:

    - If you don't need to override any of the default [`QuestionType`][questionpy.QuestionType] methods, you should
      provide your [`FormModel`][questionpy.form.FormModel] and [`Question`][questionpy.Question] subclasses as
      constructor arguments.

    - If you do, you should inherit from [`QuestionType`][questionpy.QuestionType], specifying your
      [`FormModel`][questionpy.form.FormModel] and [`Question`][questionpy.Question] as type arguments.

    Examples:
        This example shows how to subclass [`QuestionType`][questionpy.QuestionType]:

        >>> class MyOptions(FormModel): ...
        >>> class MyAttempt(Attempt): ...
        >>> class MyQuestion(Question):
        ...     attempt_class = MyAttempt
        >>> class MyQuestionType(QuestionType):
        ...     question_class = MyQuestion
        ...     # Your code goes here.
    """

    # We'd declare these using _F and _Q ideally, but that leads to "Access to generic instance variables via class is
    # ambiguous". And PEP 526 forbids TypeVars in ClassVars for some reason.
    options_class: type[FormModel] = FormModel
    question_class: type["Question"]

    def __init__(self, options_class: type[_F] | None = None, question_class: type[_Q] | None = None) -> None:
        """Initializes a new question.

        Args:
            options_class: The :class:`FormModel` for the question options. Can be set as a class variable as well.
            question_class: The :class:`Question`-class used by this type. Can be set as a class variable as well.
        """
        if options_class:
            self.options_class = options_class
        if question_class:
            self.question_class = question_class

        if not hasattr(self, "question_class"):
            msg = (
                f"Missing '{type(self).__name__}.question_class' attribute. It should point to your question "
                f"implementation"
            )
            raise TypeError(msg)

        # We handle questions using the default state separately in create_question_from_state.
        if (
            self.question_class.state_class is not BaseQuestionState
            and self.options_class != self.question_class.state_class.model_fields["options"].annotation
        ):
            msg = f"{type(self).__name__} must have the same FormModel as {self.question_class.state_class.__name__}."
            raise TypeError(msg)

    def get_options_form(self, question_state: str | None) -> tuple[OptionsFormDefinition, dict[str, object]]:
        if question_state:
            question = self.create_question_from_state(question_state)
            form_data = question.state.options.model_dump(mode="json")
        else:
            form_data = {}

        return (self.options_class.qpy_form, form_data)

    def create_question_from_options(self, old_state: str | None, form_data: dict[str, object]) -> _Q:
        try:
            parsed_form_data = self.options_class.model_validate(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

        if old_state:
            state = self.question_class.state_class.model_validate_json(old_state)
            # TODO: Should we also update package_name and package_version here? Or check that they match?
            state.options = parsed_form_data
        else:
            env = get_qpy_environment()
            state = self.question_class.state_class(
                package_name=f"{env.main_package.manifest.namespace}.{env.main_package.manifest.short_name}",
                package_version=env.main_package.manifest.version,
                options=parsed_form_data,
            )

        return cast(_Q, self.question_class(self, state))

    def create_question_from_state(self, question_state: str) -> _Q:
        state_class = self.question_class.state_class
        if state_class is BaseQuestionState:
            # If the question is using the default question state, the "options" attribute will deserialize to an empty
            # FormModel, but we want the correct options class.
            state_class = state_class[self.options_class]  # type: ignore[index]

        parsed_state = state_class.model_validate_json(question_state)
        return cast(_Q, self.question_class(self, parsed_state))
