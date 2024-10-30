from questionpy import Attempt, Question, ResponseNotScorableError

from .form import MyModel


class ExampleAttempt(Attempt):
    def _compute_score(self) -> float:
        if not self.response or "choice" not in self.response:
            msg = "'choice' is missing"
            raise ResponseNotScorableError(msg)

        if self.response["choice"] == "B":
            return 1

        return 0

    @property
    def formulation(self) -> str:
        self.placeholders["description"] = "Welcher ist der zweite Buchstabe im deutschen Alphabet?"
        return self.jinja2.get_template("local.minimal_example/formulation.xhtml.j2").render()


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel
