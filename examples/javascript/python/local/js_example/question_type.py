from questionpy import Attempt, AttemptUiPart, Question, QuestionType
from questionpy_common.api.attempt import ScoreModel, ScoringCode
from questionpy_common.api.question import QuestionModel, ScoringMethod

from .form import MyModel


class ExampleAttempt(Attempt):
    def export_score(self) -> ScoreModel:
        return ScoreModel(scoring_code=ScoringCode.AUTOMATICALLY_SCORED, score=0)

    def render_formulation(self) -> AttemptUiPart:
        ui_part = AttemptUiPart(content=self.jinja2.get_template("local.js_example/formulation.xhtml.j2").render())
        # TODO: implement call_js method
        # ui_part.call_js("test", "init", {"data": "Hello world!"})  # noqa: ERA001
        return ui_part  # noqa: RET504


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class ExampleQuestionType(QuestionType):
    question_class = ExampleQuestion
