#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from abc import ABC
from typing import ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel, JsonValue, ValidationError

from questionpy_common.api.qtype import InvalidQuestionStateError, OptionsFormValidationError
from questionpy_common.api.question import ScoringMethod, SubquestionModel
from questionpy_common.environment import get_qpy_environment

from ._attempt import Attempt
from ._util import get_mro_type_hint
from .form import FormModel, OptionsFormDefinition

_F = TypeVar("_F", bound=FormModel)
_S = TypeVar("_S", bound="BaseQuestionState")


class QuestionStateWithVersion(BaseModel, Generic[_F, _S]):
    package_name: str
    package_version: str
    options: _F
    state: _S


class BaseQuestionState(BaseModel):
    pass


class Question(ABC):
    attempt_class: type["Attempt"]

    options: FormModel
    question_state: BaseQuestionState

    options_class: ClassVar[type[FormModel]]
    question_state_class: ClassVar[type[BaseQuestionState]]
    question_state_with_version_class: ClassVar[type[QuestionStateWithVersion]]

    def __init__(self, qswv: QuestionStateWithVersion) -> None:
        self.question_state_with_version = qswv

        self.num_variants = 1
        self.score_min: float = 0
        self.score_max: float = 1
        self.scoring_method = ScoringMethod.AUTOMATICALLY_SCORABLE
        self.penalty: float | None = None
        self.random_guess_score: float | None = None
        self.response_analysis_by_variant = False
        self.hints_available = False
        self.subquestions: list[SubquestionModel] = []

    @classmethod
    def get_new_question_options_form(cls) -> OptionsFormDefinition:
        """Get the form used to create a new question."""
        return cls.options_class.qpy_form

    @classmethod
    def new_from_options(cls, form_data: dict[str, JsonValue]) -> Self:
        """Create a new question from the given options.

        The default implementation of [update_from_options][] also delegates to this method.
        """
        options = cls.validate_options(form_data)
        question_state = cls.make_question_state(options)

        env = get_qpy_environment()
        new_qswv: QuestionStateWithVersion = QuestionStateWithVersion(
            package_name=f"{env.main_package.manifest.namespace}.{env.main_package.manifest.short_name}",
            package_version=env.main_package.manifest.version,
            options=options,
            state=question_state,
        )

        return cls(new_qswv)

    def update_from_options(self, form_data: dict[str, JsonValue]) -> Self:
        """Update this question with the given form data. By default, this just creates a new question."""
        return self.new_from_options(form_data)

    @classmethod
    def from_plain_state(cls, plain_state: dict[str, JsonValue]) -> Self:
        """Validate the given plain QSVW and return a question.

        This is the reverse operation of [to_plain_state][], so `Q.from_plain_state(q.to_plain_state())` should always
        be equivalent to `q`.

        Raises:
            InvalidQuestionStateError: If the given state is semantically or syntactically invalid for this question.
        """
        try:
            return cls(cls.question_state_with_version_class.model_validate(plain_state))
        except ValidationError as e:
            raise InvalidQuestionStateError from e

    def to_plain_state(self) -> dict[str, JsonValue]:
        """Return a jsonable representation of this question's QSWV.

        This is the reverse operation of [from_plain_state][], so `Q.from_plain_state(s).to_plain_state()` should always
        be equivalent to `s`.
        """
        return self.question_state_with_version.model_dump(mode="json")

    @classmethod
    def make_question_state(cls, options: FormModel) -> BaseQuestionState:
        """Create your question state.

        Override if your question state has attributes whose values depend on the options. Note that you needn't
        override this method if you merely need access to the options in the future, they are accessible separately
        through the [options][] property.
        """
        return cls.question_state_class()

    @classmethod
    def validate_options(cls, form_data: dict[str, JsonValue]) -> FormModel:
        """Validate/parse the given plain form data into your [FormModel][] subclass."""
        try:
            return cls.options_class.model_validate(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

    def get_options_form(self) -> tuple[OptionsFormDefinition, dict[str, JsonValue]]:
        """Return the options form and field values for viewing or editing this question."""
        return self.options_class.qpy_form, self.options.model_dump()

    def start_attempt(self, variant: int) -> Attempt:
        attempt_state = self.attempt_class.make_attempt_state(self, variant)
        return self.attempt_class(self, attempt_state)

    def get_attempt(
        self,
        attempt_state: dict[str, JsonValue],
        scoring_state: dict[str, JsonValue] | None = None,
        response: dict[str, JsonValue] | None = None,
    ) -> Attempt:
        parsed_attempt_state = self.attempt_class.attempt_state_class.model_validate(attempt_state)
        parsed_scoring_state = None
        if scoring_state is not None:
            parsed_scoring_state = self.attempt_class.scoring_state_class.model_validate(scoring_state)

        return self.attempt_class(self, parsed_attempt_state, parsed_scoring_state, response)

    def __init_subclass__(cls, *args: object, **kwargs: object) -> None:
        super().__init_subclass__(*args, **kwargs)

        if not hasattr(cls, "attempt_class"):
            msg = f"Missing '{cls.__name__}.attempt_class' attribute. It should point to your attempt implementation"
            raise TypeError(msg)

        cls.question_state_class = get_mro_type_hint(cls, "question_state", BaseQuestionState)
        cls.options_class = get_mro_type_hint(cls, "options", FormModel)
        cls.question_state_with_version_class = QuestionStateWithVersion[  # type: ignore[misc]
            cls.options_class, cls.question_state_class  # type: ignore[name-defined]
        ]

    @property  # type: ignore[no-redef]
    def options(self) -> FormModel:
        return self.question_state_with_version.options

    @property  # type: ignore[no-redef]
    def question_state(self) -> BaseQuestionState:
        return self.question_state_with_version.state
