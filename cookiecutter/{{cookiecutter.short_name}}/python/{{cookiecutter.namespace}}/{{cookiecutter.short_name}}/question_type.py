from questionpy import Attempt, Question, ResponseNotScorableError

from .form import MyFormModel


class ExampleAttempt(Attempt):
    def _compute_score(self) -> float:
        if not self.response or "choice" not in self.response:
            msg = "'choice' is missing"
            raise ResponseNotScorableError(msg)

        return 1 if self.response["choice"] == "B" else 0

    @property
    def formulation(self) -> str:
        self.placeholders["description"] = "Which is the second letter in the alphabet?"
        return self.jinja2.get_template(
            "{{ cookiecutter.namespace }}.{{ cookiecutter.short_name }}/formulation.xhtml.j2"
        ).render()


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt
    options: MyFormModel
