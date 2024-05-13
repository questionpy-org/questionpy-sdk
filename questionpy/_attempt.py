from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING

import jinja2
from pydantic import BaseModel

from questionpy_common.api.attempt import (
    AttemptFile,
    AttemptModel,
    AttemptScoredModel,
    AttemptUi,
    BaseAttempt,
    CacheControl,
    ScoreModel,
)

from ._ui import create_jinja2_environment

if TYPE_CHECKING:
    from ._qtype import Question


class BaseAttemptState(BaseModel):
    variant: int


class BaseScoringState(BaseModel):
    pass


class AttemptUiPart(BaseModel):
    content: str
    placeholders: dict[str, str] = {}
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
    all_placeholders: dict[str, str] = {}
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


class Attempt(BaseAttempt, ABC):
    attempt_state: BaseAttemptState
    scoring_state: BaseScoringState | None

    def __init__(
        self,
        question: "Question",
        attempt_state: BaseAttemptState,
        response: dict | None = None,
        scoring_state: BaseScoringState | None = None,
    ) -> None:
        self.question = question
        self.attempt_state = attempt_state
        self.response = response
        self.scoring_state = scoring_state

    @abstractmethod
    def render_formulation(self) -> AttemptUiPart:
        pass

    def render_general_feedback(self) -> AttemptUiPart | None:
        return None

    def render_specific_feedback(self) -> AttemptUiPart | None:
        return None

    def render_right_answer_description(self) -> AttemptUiPart | None:
        return None

    def render_ui(self) -> AttemptUi:
        formulation = self.render_formulation()
        general_feedback = self.render_general_feedback()
        specific_feedback = self.render_specific_feedback()
        right_answer = self.render_right_answer_description()

        return _merge_uis(formulation, general_feedback, specific_feedback, right_answer, self.cache_control)

    @property
    def cache_control(self) -> CacheControl:
        """Specifies if this attempt's UI may be cached and if that cache may be shared with other attempts."""
        return CacheControl.PRIVATE_CACHE

    @cached_property
    def jinja2(self) -> jinja2.Environment:
        return create_jinja2_environment(self, self.question, self.question.qtype)

    def export(self) -> AttemptModel:
        return AttemptModel(variant=self.attempt_state.variant, ui=self.render_ui())

    @abstractmethod
    def export_score(self) -> ScoreModel:
        pass

    def export_scored_attempt(self) -> AttemptScoredModel:
        return AttemptScoredModel(**self.export().model_dump(), **self.export_score().model_dump())

    def export_attempt_state(self) -> str:
        return self.attempt_state.model_dump_json()
