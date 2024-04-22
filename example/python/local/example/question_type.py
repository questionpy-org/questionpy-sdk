from questionpy import Attempt, AttemptUiPart, Question, QuestionType, ScoringCode
from questionpy_common.api.attempt import ScoreModel
from questionpy_common.api.question import QuestionModel, ScoringMethod

from .form import MyModel


class ExampleAttempt(Attempt):
    def export_score(self) -> ScoreModel:
        if not self.response or "choice" not in self.response:
            return ScoreModel(scoring_code=ScoringCode.RESPONSE_NOT_SCORABLE, score=None)

        if self.response["choice"] == "B":
            return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=1)

        return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=0)

    def render_formulation(self) -> AttemptUiPart:
        return AttemptUiPart(
            content=self.jinja2.get_template("local.example/formulation.xhtml.j2").render(),
            placeholders={"description": "Welcher ist der zweite Buchstabe im deutschen Alphabet?"},
        )


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class ExampleQuestionType(QuestionType):
    question_class = ExampleQuestion
