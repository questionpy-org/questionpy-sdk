from questionpy import Attempt, Question

from .form import MyModel


class ExampleAttempt(Attempt):
    def _compute_score(self) -> float:
        return 0

    @property
    def formulation(self) -> str:
        self.call_js("main.js", "init", "QuestionPy")
        return self.jinja2.get_template("formulation.xhtml.j2").render()


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel
