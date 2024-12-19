from typing import Any

from questionpy import Attempt, Question, ResponseNotScorableError

from .form import ChoiceMode, SinglechoiceFormModel


class SinglechoiceAttempt(Attempt):
    def _compute_score(self) -> float:
        if not self.response or "choice" not in self.response:
            msg = "'choice' is missing"
            raise ResponseNotScorableError(msg)

        chosen_id = self.response["choice"]
        correct_choice_ids = [choice.id for choice in self.question.options.choices if choice.correct]

        if chosen_id in correct_choice_ids:
            return 1

        return 0

    def __init__(self, *args: Any):
        super().__init__(*args)

        self.placeholders["description"] = self.question.options.description

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render(ChoiceMode=ChoiceMode)


class SinglechoiceQuestion(Question):
    attempt_class = SinglechoiceAttempt

    options: SinglechoiceFormModel
