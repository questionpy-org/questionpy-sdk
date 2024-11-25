from questionpy import Attempt, Question, ResponseNotScorableError

from .form import MultichoiceFormModel


class MultichoiceAttempt(Attempt):
    question: "MultichoiceQuestion"

    def _compute_score(self) -> float:
        if not self.response or "choice" not in self.response:
            msg = "'choice' is missing"
            raise ResponseNotScorableError(msg)

        choice_value = self.response["choice"]
        choice = next(choice for choice in self.question.options.choices if choice.score)


        return 0

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("local.multichoice/formulation.xhtml.j2").render()


class MultichoiceQuestion(Question):
    attempt_class = MultichoiceAttempt

    options: MultichoiceFormModel
