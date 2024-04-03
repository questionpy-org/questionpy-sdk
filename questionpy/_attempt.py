from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import cached_property
from typing import TYPE_CHECKING

import jinja2
from pydantic import BaseModel

from questionpy_common.api.attempt import (
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


def _merge_uis(complete_content: str, uis: Sequence[AttemptUi | None]) -> AttemptUi:
    all_placeholders = {}
    complete_inline_css = ""
    all_files = []
    for partial_ui in uis:
        if not partial_ui:
            continue
        all_placeholders.update(partial_ui.placeholders)
        if partial_ui.include_inline_css:
            complete_inline_css += partial_ui.include_inline_css + "\n"
        all_files.extend(partial_ui.files)

    # TODO: How to merge css files and cache control?
    return AttemptUi(
        content=complete_content,
        placeholders=all_placeholders,
        include_inline_css=complete_inline_css or None,
        cache_control=CacheControl.NO_CACHE,
        files=all_files,
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
    def render_formulation(self) -> AttemptUi:
        pass

    def render_general_feedback(self) -> AttemptUi | None:
        return None

    def render_specific_feedback(self) -> AttemptUi | None:
        return None

    def render_right_answer_description(self) -> AttemptUi | None:
        return None

    def _render_all(self, template: str) -> AttemptUi:
        formulation = self.render_formulation()
        # pylint: disable=assignment-from-none
        general_feedback = self.render_general_feedback()
        specific_feedback = self.render_specific_feedback()

        complete_content = self.jinja2.get_template(template).render(
            formulation=formulation,
            general_feedback=general_feedback,
            specific_feedback=specific_feedback,
        )
        return _merge_uis(complete_content, [formulation, general_feedback, specific_feedback])

    def render_ui(self) -> AttemptUi:
        return self._render_all("qpy/question.xhtml.j2")

    def render_subquestion(self) -> AttemptUi:
        return self._render_all("qpy/subquestion.xhtml.j2")

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
