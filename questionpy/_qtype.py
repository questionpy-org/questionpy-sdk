#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from abc import ABC
from typing import Optional, Type, Generic, TypeVar, ClassVar, get_args, get_origin, Literal, Union, cast

from pydantic import BaseModel, ValidationError
from questionpy_common.qtype import OptionsFormDefinition, BaseQuestionType, BaseQuestion, OptionsFormValidationError, \
    BaseAttempt

from questionpy.form import FormModel

_T = TypeVar("_T")
_F = TypeVar("_F", bound=FormModel)
_QS = TypeVar("_QS", bound="BaseQuestionState")
_AS = TypeVar("_AS", bound="BaseAttemptState")
_A = TypeVar("_A", bound="Attempt")
_Q = TypeVar("_Q", bound="Question")


def _get_type_arg(derived: type, generic_base: type, arg_index: int, *,
                  bound: type = object, default: Union[_T, Literal["nodefault"]] = "nodefault") -> Union[type, _T]:
    """Finds a type arg used by `derived` when inheriting from `generic_base`.

    Args:
        derived: The type which directly inherits from `generic_base`.
        generic_base: One of the direct bases of `derived`.
        arg_index: Among the type arguments accepted by `generic_base`, this is the index of the type argument to
                   return.
        bound: Raises :class:`TypeError` if the type argument is not a subclass of this.
        default: Returns this when the type argument isn't given. If unset, an error is raised instead.

    Raises:
        TypeError: Upon any of the following:
            - `derived` is not a direct subclass of `generic_base` (transitive subclasses are not supported),
            - the type argument is not given and `default` is unset, or
            - the type argument is not a subclass of `bound`
    """
    # __orig_bases__ is only present when at least one base is a parametrized generic.
    # See PEP 560 https://peps.python.org/pep-0560/
    if "__orig_bases__" in derived.__dict__:
        bases = derived.__dict__["__orig_bases__"]
    else:
        bases = derived.__bases__

    for base in bases:
        origin = get_origin(base) or base
        if origin is generic_base:
            args = get_args(base)
            if not args or arg_index >= len(args):
                # No type argument provided.
                if default == "nodefault":
                    raise TypeError(f"Missing type argument on {generic_base.__name__} (type arg #{arg_index})")

                return default

            arg = args[arg_index]
            if not isinstance(arg, type) or not issubclass(arg, bound):
                raise TypeError(f"Type parameter '{arg!r}' of {generic_base.__name__} is not a subclass of "
                                f"{bound.__name__}")
            return arg

    raise TypeError(f"{derived.__name__} is not a direct subclass of {generic_base.__name__}")


class BaseAttemptState(BaseModel, Generic[_QS]):
    question: _QS


class BaseQuestionState(BaseModel, Generic[_F]):
    package_name: str
    package_version: str
    options: _F


class Attempt(BaseAttempt, ABC, Generic[_AS]):
    state_class: Type[BaseAttemptState] = BaseAttemptState

    def __init__(self, state: _AS):
        self.state = state

    def export_attempt_state(self) -> str:
        return self.state.model_dump_json()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.state_class = _get_type_arg(cls, Attempt, 0, bound=BaseAttemptState, default=BaseAttemptState)


class Question(BaseQuestion, ABC, Generic[_QS, _A]):
    state_class: Type[BaseQuestionState] = BaseQuestionState
    attempt_class: Type["Attempt"]

    def __init__(self, state: _QS):
        self.state = state

    def start_attempt(self, variant: int) -> BaseAttempt:
        state = self.attempt_class.state_class(question=self.state)
        return self.attempt_class(state)

    def view_attempt(self, attempt_state: str,
                     scoring_state: Optional[str] = None,
                     response: Optional[dict] = None) -> BaseAttempt:
        # TODO: Implement scoring_state and response.
        state = self.attempt_class.state_class.model_validate_json(attempt_state)
        return self.attempt_class(state)

    def export_question_state(self) -> str:
        return self.state.model_dump_json()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.state_class = _get_type_arg(cls, Question, 0, bound=BaseQuestionState, default=BaseQuestionState)
        cls.attempt_class = _get_type_arg(cls, Question, 1, bound=Attempt)


class QuestionType(BaseQuestionType, Generic[_F, _Q]):
    """A question type.

    This class is intended to be used in one of two ways:
    - If you don't need to override any of the default :class:`QuestionType` methods, you should provide your
      :class:`FormModel` and :class:`Question` subclasses as constructor arguments.
    - If you do, you should inherit from :class:`QuestionType`, specifying your :class:`FormModel` and :class:`Question`
      as type arguments:

      >>> class MyOptions(FormModel): ...
      >>> class MyAttempt(Attempt): ...
      >>> class MyQuestion(Question[BaseQuestionState, MyAttempt]): ...
      >>> class MyQuestionType(QuestionType[MyOptions, MyQuestion]):
      ...   ...  # Your code goes here.
    """

    # We'd declare these using _F and _Q ideally, but that leads to "Access to generic instance variables via class is
    # ambiguous". And PEP 526 forbids TypeVars in ClassVars for some reason.
    options_class: Type[FormModel] = FormModel
    question_class: Type["Question"]

    # TODO: questionpy-server#67: Replace with global init() function.
    implementation: ClassVar[Optional[Type["QuestionType"]]] = None

    def __init__(self, options_class: Optional[Type[_F]] = None, question_class: Optional[Type[_Q]] = None) -> None:
        """Initializes a new question.

        Args:
            options_class: Override the :class:`FormModel` for the question options.
            question_class: Override the :class:`Question`-class used by this type.
        """
        if options_class:
            self.options_class = options_class
        if question_class:
            self.question_class = question_class

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        cls.options_class = _get_type_arg(cls, QuestionType, 0, bound=FormModel, default=FormModel)
        cls.question_class = _get_type_arg(cls, QuestionType, 1, bound=Question)

        QuestionType.implementation = cls

    def get_options_form(self, question_state: Optional[str]) -> tuple[OptionsFormDefinition, dict[str, object]]:
        if question_state:
            question = self.create_question_from_state(question_state)
            form_data = question.state.options.model_dump(mode="json")
        else:
            form_data = {}

        return (self.options_class.qpy_form, form_data)

    def create_question_from_options(self, old_state: Optional[str], form_data: dict[str, object]) -> _Q:
        try:
            parsed_form_data = self.options_class.model_validate(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

        if old_state:
            state = self.question_class.state_class.model_validate_json(old_state)
            # TBD: Should we also update package_name and package_version here? Or check that they match?
            state.options = parsed_form_data
        else:
            state = self.question_class.state_class(
                # TODO: Replace these placeholders with values from the environment.
                package_name="TODO",
                package_version="1.2.3",
                options=parsed_form_data,
            )

        return cast(_Q, self.question_class(state))

    def create_question_from_state(self, question_state: str) -> _Q:
        return cast(_Q, self.question_class(self.question_class.state_class.model_validate_json(question_state)))
