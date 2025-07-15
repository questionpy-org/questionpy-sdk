#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from enum import StrEnum
from typing import TypedDict

from pydantic import JsonValue
from pydantic.dataclasses import dataclass

from questionpy import AttemptModel, AttemptScoredModel, AttemptStartedModel
from questionpy_common.api.attempt import JsModuleCall, ScoringCode
from questionpy_sdk.webserver.controllers.attempt.question_ui import QuestionDisplayOptions

from .errors import SectionErrorMap


class AttemptStatus(StrEnum):
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SCORED = "SCORED"

    @classmethod
    def from_attempt(cls, attempt: AttemptModel) -> "AttemptStatus":
        if isinstance(attempt, AttemptStartedModel):
            return cls.STARTED
        if isinstance(attempt, AttemptScoredModel):
            return cls.SCORED
        return cls.IN_PROGRESS


class AttemptTemplateContext(TypedDict):
    formulation: str
    general_feedback: str | None
    specific_feedback: str | None
    right_answer: str | None
    display_options: QuestionDisplayOptions
    import_map: dict[str, str]
    javascript_calls: list[JsModuleCall]
    stylesheet_urls: list[str]
    data: dict[str, JsonValue]


@dataclass
class AttemptData:
    """Represents the API response data for an attempt in the frontend."""

    attempt_status: AttemptStatus
    attempt_state: str
    variant: int
    scoring_state: str | None = None
    scoring_code: ScoringCode | None = None
    score: float | None = None

    @classmethod
    def from_attempt(cls, attempt: AttemptModel, attempt_state: str) -> "AttemptData":
        data = AttemptData(
            attempt_status=AttemptStatus.from_attempt(attempt),
            attempt_state=attempt_state,
            variant=attempt.variant,
            scoring_state=None,
            scoring_code=None,
            score=None,
        )

        if isinstance(attempt, AttemptScoredModel):
            data.scoring_state = attempt.scoring_state
            data.scoring_code = attempt.scoring_code
            data.score = attempt.score

        return data


@dataclass
class AttemptRenderData:
    """Represents the API response data for rendering an attempt in the frontend."""

    attempt_data: AttemptData
    attempt_html: str
    render_errors: SectionErrorMap
