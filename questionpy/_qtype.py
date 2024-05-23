#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from abc import ABC
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from questionpy_common.api.attempt import BaseAttempt
from questionpy_common.api.qtype import BaseQuestionType, InvalidQuestionStateError, OptionsFormValidationError
from questionpy_common.api.question import BaseQuestion
from questionpy_common.environment import get_qpy_environment

from ._attempt import Attempt, BaseAttemptState, BaseScoringState
from ._util import get_mro_type_hint
from .form import FormModel, OptionsFormDefinition

_F = TypeVar("_F", bound=FormModel)


class BaseQuestionState(BaseModel, Generic[_F]):
    package_name: str
    package_version: str
    options: _F


class Question(BaseQuestion, ABC):
    attempt_class: type["Attempt"]

    options: FormModel
    state: BaseQuestionState

    def __init__(self, qtype: BaseQuestionType, state: BaseQuestionState) -> None:
        self.qtype = qtype
        self.state = state

    def start_attempt(self, variant: int) -> BaseAttempt:
        attempt_state = get_mro_type_hint(self.attempt_class, "attempt_state", BaseAttemptState)(variant=variant)
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
        attempt_state_obj = get_mro_type_hint(
            self.attempt_class, "attempt_state", BaseAttemptState
        ).model_validate_json(attempt_state)
        scoring_state_obj = None
        if scoring_state is not None:
            scoring_state_obj = get_mro_type_hint(
                self.attempt_class, "scoring_state", BaseScoringState
            ).model_validate_json(scoring_state)
        return self.attempt_class(self, attempt_state_obj, response, scoring_state_obj)

    def export_question_state(self) -> str:
        return self.state.model_dump_json()

    def __init_subclass__(cls, *args: object, **kwargs: object) -> None:
        super().__init_subclass__(*args, **kwargs)

        if not hasattr(cls, "attempt_class"):
            msg = f"Missing '{cls.__name__}.attempt_class' attribute. It should point to your attempt implementation"
            raise TypeError(msg)

        state_class = _get_state_class(cls)
        options_class = get_mro_type_hint(cls, "options", FormModel)
        # We handle questions using the default state separately in create_question_from_state.
        if state_class is not BaseQuestionState and options_class != state_class.model_fields["options"].annotation:
            msg = f"{cls.__name__} must have the same FormModel as {state_class.__name__}."
            raise TypeError(msg)

    @property  # type: ignore[no-redef]
    def options(self) -> FormModel:
        return self.state.options

    @options.setter
    def options(self, value: FormModel) -> None:
        self.state.options = value


def _get_state_class(question_class: type[Question]) -> type[BaseQuestionState]:
    state_class = get_mro_type_hint(question_class, "state", BaseQuestionState)

    if state_class is BaseQuestionState:
        return state_class[get_mro_type_hint(question_class, "options", FormModel)]  # type: ignore[misc]

    return state_class


class QuestionType(BaseQuestionType):
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

    question_class: type["Question"]

    def __init__(self, question_class: type[Question] | None = None) -> None:
        """Initializes a new question.

        Args:
            question_class: The :class:`Question`-class used by this type. Can be set as a class variable as well.
        """
        if question_class:
            self.question_class = question_class

        if not hasattr(self, "question_class"):
            msg = (
                f"Missing '{type(self).__name__}.question_class' attribute. It should point to your question "
                f"implementation"
            )
            raise TypeError(msg)

    def get_options_form(self, question_state: str | None) -> tuple[OptionsFormDefinition, dict[str, object]]:
        if question_state:
            question = self.create_question_from_state(question_state)
            form_data = question.options.model_dump(mode="json")
        else:
            form_data = {}

        return (get_mro_type_hint(self.question_class, "options", FormModel).qpy_form, form_data)

    def create_question_from_options(self, old_state: str | None, form_data: dict[str, object]) -> Question:
        try:
            parsed_form_data = get_mro_type_hint(self.question_class, "options", FormModel).model_validate(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

        if old_state:
            state = _get_state_class(self.question_class).model_validate_json(old_state)
            # TODO: Should we also update package_name and package_version here? Or check that they match?
            state.options = parsed_form_data
        else:
            env = get_qpy_environment()
            state = _get_state_class(self.question_class)(
                package_name=f"{env.main_package.manifest.namespace}.{env.main_package.manifest.short_name}",
                package_version=env.main_package.manifest.version,
                options=parsed_form_data,
            )

        return self.question_class(self, state)

    def create_question_from_state(self, question_state: str) -> Question:
        state_class = _get_state_class(self.question_class)
        try:
            parsed_state = state_class.model_validate_json(question_state)
        except ValidationError as e:
            raise InvalidQuestionStateError from e
        return self.question_class(self, parsed_state)
