from importlib.resources import files

from questionpy import (
    Attempt,
    AttemptModel,
    AttemptUi,
    Question,
    QuestionType,
    ScoringCode,
)
from questionpy_common.api.attempt import ScoreModel
from questionpy_common.api.question import QuestionModel, ScoringMethod

from .form import MyModel


class ExampleAttempt(Attempt):
    def export_score(self) -> ScoreModel:
        if "choice" not in self.response:
            return ScoreModel(scoring_code=ScoringCode.RESPONSE_NOT_SCORABLE, score=None)

        if self.response["choice"] == "B":
            return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=1)

        return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=0)

    def export(self) -> AttemptModel:
        return AttemptModel(
            variant=1,
            ui=AttemptUi(
                content=(files(__package__) / "multiple-choice.xhtml").read_text(),
                placeholders={"description": "Welcher ist der zweite Buchstabe im deutschen Alphabet?"},
            ),
        )


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class ExampleQuestionType(QuestionType):
    question_class = ExampleQuestion
    options_class = MyModel
