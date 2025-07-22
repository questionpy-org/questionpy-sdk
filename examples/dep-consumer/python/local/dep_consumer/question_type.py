from questionpy import Attempt, Question

from .form import MyModel


class ExampleAttempt(Attempt):
    def _compute_score(self) -> float:
        return 0

    @property
    def formulation(self) -> str:
        return "<div>Nothing to see here :)</div>"


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel
