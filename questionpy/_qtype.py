#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from abc import ABC
from typing import ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel, JsonValue, ValidationError

from questionpy_common.api.qtype import OptionsFormValidationError
from questionpy_common.api.question import ScoringMethod, SubquestionModel
from questionpy_common.environment import get_qpy_environment

from ._attempt import Attempt, BaseAttemptState, BaseScoringState
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

    scoring_method = ScoringMethod.AUTOMATICALLY_SCORABLE

    options_class: ClassVar[type[FormModel]]
    question_state_class: ClassVar[type[BaseQuestionState]]
    question_state_with_version_class: ClassVar[type[QuestionStateWithVersion]]

    def __init__(self, qswv: QuestionStateWithVersion) -> None:
        self.question_state_with_version = qswv

        self.num_variants = 1
        self.score_min: float = 0
        self.score_max: float = 1
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
    def from_options(cls, old_qswv: QuestionStateWithVersion | None, form_data: dict[str, JsonValue]) -> Self:
        try:
            parsed_form_data = cls.options_class.model_validate(form_data)
        except ValidationError as e:
            error_dict = {".".join(map(str, error["loc"])): error["msg"] for error in e.errors()}
            raise OptionsFormValidationError(error_dict) from e

        if old_qswv:
            new_qswv = old_qswv.model_copy(update={"options": parsed_form_data})
        else:
            env = get_qpy_environment()
            new_qswv = QuestionStateWithVersion(
                package_name=f"{env.main_package.manifest.namespace}.{env.main_package.manifest.short_name}",
                package_version=env.main_package.manifest.version,
                options=parsed_form_data,
                state=cls.make_question_state(parsed_form_data),
            )

        return cls(new_qswv)

    @classmethod
    def from_state(cls, qswv: QuestionStateWithVersion) -> Self:
        return cls(qswv)

    @classmethod
    def make_question_state(cls, options: FormModel) -> BaseQuestionState:
        return cls.question_state_class()

    @classmethod
    def validate_options(cls, raw_options: dict[str, JsonValue]) -> FormModel:
        return cls.options_class.model_validate(raw_options)

    def get_options_form(self) -> tuple[OptionsFormDefinition, dict[str, JsonValue]]:
        return self.options_class.qpy_form, self.options.model_dump()

    def start_attempt(self, variant: int) -> Attempt:
        attempt_state = self.attempt_class.attempt_state_class(variant=variant)
        return self.attempt_class(self, attempt_state)

    def get_attempt(
        self,
        attempt_state: BaseAttemptState,
        scoring_state: BaseScoringState | None = None,
        response: dict[str, JsonValue] | None = None,
        *,
        compute_score: bool = False,
        generate_hint: bool = False,
    ) -> Attempt:
        return self.attempt_class(self, attempt_state, scoring_state, response)

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
