import json
from abc import ABC, abstractmethod
from collections import UserString
from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, Protocol

import jinja2
from pydantic import BaseModel, JsonValue

from questionpy_common.api.attempt import (
    AttemptFile,
    AttemptUi,
    CacheControl,
    DisplayRole,
    FeedbackType,
    JsModuleCall,
    ScoredInputModel,
    ScoringCode,
)

from ._ui import create_jinja2_environment
from ._util import get_package_by_attempt, reify_type_hint

if TYPE_CHECKING:
    from ._qtype import Question


class BaseAttemptState(BaseModel):
    variant: int


class BaseScoringState(BaseModel):
    pass


class AttemptUiPart(BaseModel):
    content: str | UserString
    placeholders: dict[str, str | UserString] = {}
    """Names and values of the ``<?p`` placeholders that appear in content."""
    css_files: Sequence[str] = ()
    files: dict[str, AttemptFile] = {}


def _merge_uis(
    formulation: AttemptUiPart,
    general_feedback: AttemptUiPart | None,
    specific_feedback: AttemptUiPart | None,
    right_answer: AttemptUiPart | None,
    cache_control: CacheControl,
) -> AttemptUi:
    all_placeholders: dict[str, str | UserString] = {}
    all_css_files: list[str] = []
    all_files: dict[str, AttemptFile] = {}
    for partial_ui in (formulation, general_feedback, specific_feedback, right_answer):
        if not partial_ui:
            continue
        all_placeholders.update(partial_ui.placeholders)
        all_css_files.extend(partial_ui.css_files)
        all_files.update(partial_ui.files)

    return AttemptUi(
        formulation=formulation and formulation.content,
        general_feedback=general_feedback and general_feedback.content,
        specific_feedback=specific_feedback and specific_feedback.content,
        right_answer=right_answer and right_answer.content,
        placeholders=all_placeholders,
        css_files=all_css_files,
        files=all_files,
        cache_control=cache_control,
    )


class AttemptProtocol(Protocol):
    """Defines the properties and methods an attempt must always contain."""

    @property
    def cache_control(self) -> CacheControl:
        pass

    @property
    def placeholders(self) -> dict[str, str | UserString]:
        pass

    @property
    def css_files(self) -> list[str]:
        pass

    @property
    def javascript_calls(self) -> list[JsModuleCall]:
        pass

    @property
    def files(self) -> dict[str, AttemptFile]:
        pass

    @property
    def variant(self) -> int:
        pass

    @property
    def formulation(self) -> str | UserString:
        pass

    @property
    def general_feedback(self) -> str | UserString | None:
        pass

    @property
    def specific_feedback(self) -> str | UserString | None:
        pass

    @property
    def right_answer_description(self) -> str | UserString | None:
        pass


class AttemptStartedProtocol(AttemptProtocol, Protocol):
    """In addition to [AttemptProtocol][], defines that a newly started attempt must provide its attempt state.

    The attempt state is only generated at attempt start and immutable afterwards, so it must only be defined on the
    object returned by [Question.start_attempt][].
    """

    def to_plain_attempt_state(self) -> dict[str, JsonValue]:
        """Return a jsonable representation of this attempt's state."""


class AttemptScoredProtocol(AttemptProtocol, Protocol):
    """In addition to [AttemptProtocol][], defines properties and methods which must be set after scoring."""

    @property
    def scoring_code(self) -> ScoringCode:
        pass

    @property
    def scored_inputs(self) -> Mapping[str, ScoredInputModel]:
        pass

    @property
    def score(self) -> float | None:
        pass

    @property
    def score_final(self) -> float | None:
        pass

    def to_plain_scoring_state(self) -> Mapping[str, JsonValue] | None:
        """Return a jsonable representation of this attempt's scoring state, if any."""


class Attempt(ABC):
    attempt_state: BaseAttemptState
    scoring_state: BaseScoringState | None

    attempt_state_class: ClassVar[type[BaseAttemptState]] = reify_type_hint("attempt_state", BaseAttemptState)
    scoring_state_class: ClassVar[type[BaseScoringState]] = reify_type_hint("scoring_state", BaseScoringState)

    def __init__(
        self,
        question: "Question",
        attempt_state: BaseAttemptState,
        scoring_state: BaseScoringState | None = None,
        response: dict[str, JsonValue] | None = None,
    ) -> None:
        self.question = question
        self.attempt_state = attempt_state
        self.response = response
        self.scoring_state = scoring_state

        self.cache_control = CacheControl.PRIVATE_CACHE
        self.placeholders: dict[str, str | UserString] = {}
        self.css_files: list[str] = []
        self._javascript_calls: list[JsModuleCall] = []
        """LMS has to call these JS modules/functions."""

        self.files: dict[str, AttemptFile] = {}

        self.scoring_code: ScoringCode | None = None
        """When scoring is completed, set this to the outcome.

        This is set by [score_response][questionpy.Attempt.score_response] depending on if
        [_compute_score][questionpy.Attempt._compute_score] and
        [_compute_final_score][questionpy.Attempt._compute_final_score] raise any errors.

        Note that when rescoring an attempt, the previous scoring information is not filled in and this field should
        only be viewed as an output.
        """
        self.scored_inputs: dict[str, ScoredInputModel] = {}
        """Optionally, granular scores for the attempt's input fields can be added to this dict.

        Note that when rescoring an attempt, the previous scoring information is not filled in and this field should
        only be viewed as an output.
        """
        self.score: float | None = None
        """Score calculated by [_score_response][questionpy.Attempt._score_response].

        Note that when rescoring an attempt, the previous scoring information is not filled in and this field should
        only be viewed as an output.
        """
        self.score_final: float | None = None
        """Score calculated by [_score_final_response][questionpy.Attempt._score_response].

        Note that when rescoring an attempt, the previous scoring information is not filled in and this field should
        only be viewed as an output.
        """

        self._init_attempt()

    def _init_attempt(self) -> None:  # noqa: B027
        """A place for the question to initialize the attempt (set up fields, JavaScript calls, etc.)."""

    @property
    @abstractmethod
    def formulation(self) -> str:
        pass

    @property
    def general_feedback(self) -> str | UserString | None:
        return None

    @property
    def specific_feedback(self) -> str | UserString | None:
        return None

    @property
    def right_answer_description(self) -> str | UserString | None:
        return None

    def score_response(self, *, try_scoring_with_countback: bool = False, try_giving_hint: bool = False) -> None:
        try:
            self.score = self._compute_score()
            self.score_final = self._compute_final_score()
        except _ScoringError as e:
            self.scoring_code = e.scoring_code
        else:
            self.scoring_code = ScoringCode.AUTOMATICALLY_SCORED

    def to_plain_attempt_state(self) -> dict[str, JsonValue]:
        """Return a jsonable representation of this attempt's state."""
        return self.attempt_state.model_dump(mode="json")

    def to_plain_scoring_state(self) -> dict[str, JsonValue] | None:
        """Return a jsonable representation of this attempt's scoring state, if any."""
        if self.scoring_state is None:
            return None
        return self.scoring_state.model_dump(mode="json")

    @classmethod
    def make_attempt_state(cls, question: "Question", variant: int) -> BaseAttemptState:
        """Create your attempt state."""
        return cls.attempt_state_class(variant=variant)

    @abstractmethod
    def _compute_score(self) -> float:
        pass

    def _compute_final_score(self) -> float:
        return self._compute_score() if self.score is None else self.score

    @cached_property
    def jinja2(self) -> jinja2.Environment:
        return create_jinja2_environment(self, self.question)

    @property
    def variant(self) -> int:
        return self.attempt_state.variant

    def call_js(
        self,
        module: str,
        function: str,
        data: JsonValue = None,
        *,
        if_role: DisplayRole | None = None,
        if_feedback_type: FeedbackType | None = None,
    ) -> None:
        """Call a javascript function when the LMS displays this question attempt.

        The function is called when both the `if_role` and `if_feedback_type` conditions are met.

        Args:
            module: JS module name specified as:
                @[package namespace]/[package short name]/[subdir]/[module name] (full reference) or
                [subdir]/[module name] (referencing a module within the package where this class is subclassed)
            function: Name of a callable value within the JS module
            data: arbitrary data to pass to the function
            if_role: Function is only called if the user has this role.
            if_feedback_type: Function is only called if the user is allowed to view this feedback type.
        """
        if not module.startswith("@"):
            # Get current package namespace and short name.
            package = get_package_by_attempt(self)
            module = f"@{package.manifest.namespace}/{package.manifest.short_name}/{module.lstrip('/')}"

        data_json = None if data is None else json.dumps(data)
        call = JsModuleCall(
            module=module, function=function, data=data_json, if_role=if_role, if_feedback_type=if_feedback_type
        )
        self._javascript_calls.append(call)

    @property
    def javascript_calls(self) -> list[JsModuleCall]:
        return self._javascript_calls

    def __init_subclass__(cls, *args: object, **kwargs: object):
        super().__init_subclass__(*args, **kwargs)


class _ScoringError(Exception):
    def __init__(self, scoring_code: ScoringCode, *args: object) -> None:
        self.scoring_code = scoring_code
        super().__init__(*args)


class ResponseNotScorableError(_ScoringError):
    def __init__(self, *args: object) -> None:
        super().__init__(ScoringCode.RESPONSE_NOT_SCORABLE, *args)


class InvalidResponseError(_ScoringError):
    def __init__(self, *args: object) -> None:
        super().__init__(ScoringCode.INVALID_RESPONSE, *args)


class NeedsManualScoringError(_ScoringError):
    def __init__(self, *args: object) -> None:
        super().__init__(ScoringCode.NEEDS_MANUAL_SCORING, *args)
