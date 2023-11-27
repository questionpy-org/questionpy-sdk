from importlib.resources import files

from questionpy_common.models import AttemptModel, AttemptUi, QuestionModel, ScoringMethod

from questionpy import Attempt, BaseAttemptState, Question, BaseQuestionState, QuestionType
from .form import MyModel


class ExampleAttempt(Attempt["ExampleQuestion", BaseAttemptState]):
    def export(self) -> AttemptModel:
        return AttemptModel(variant=1, ui=AttemptUi(
            content=(files(__package__) / "multiple-choice.xhtml").read_text()
        ))


class ExampleQuestion(Question[BaseQuestionState[MyModel], ExampleAttempt]):
    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class ExampleQuestionType(QuestionType[MyModel, ExampleQuestion]):
    pass
