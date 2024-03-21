from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from pydantic import BaseModel

from questionpy_common.api.attempt import AttemptScoredModel, BaseAttempt, ScoreModel

if TYPE_CHECKING:
    from ._qtype import Question


class BaseAttemptState(BaseModel):
    variant: int


class BaseScoringState(BaseModel):
    pass


_AS = TypeVar("_AS", bound=BaseAttemptState)
_SS = TypeVar("_SS", bound=BaseScoringState)

_Q = TypeVar("_Q", bound="Question")


class Attempt(BaseAttempt, ABC, Generic[_Q, _AS, _SS]):
    attempt_state_class: ClassVar[type[BaseAttemptState]] = BaseAttemptState
    scoring_state_class: ClassVar[type[BaseScoringState]] = BaseScoringState

    def __init__(
        self, question: _Q, attempt_state: _AS, response: dict | None = None, scoring_state: _SS | None = None
    ) -> None:
        self.question = question
        self.attempt_state = attempt_state
        self.response = response
        self.scoring_state = scoring_state

    @abstractmethod
    def export_score(self) -> ScoreModel:
        pass

    def export_scored_attempt(self) -> AttemptScoredModel:
        return AttemptScoredModel(**self.export().model_dump(), **self.export_score().model_dump())

    def export_attempt_state(self) -> str:
        return self.attempt_state.model_dump_json()
