from questionpy import Attempt, FeedbackType, Question, ResponseNotScorableError

from .form import MyModel


class ExampleAttempt(Attempt):
    def _init_attempt(self) -> None:
        self.call_js("@local/static_files_example/test.js", "initButton", ["mybutton", "hiddenInput", "secret"])
        self.call_js("@local/static_files_example/test.js", "hello", "world", if_feedback_type=FeedbackType.GENERAL_FEEDBACK)

    def _compute_score(self) -> float:
        if not self.response or "hidden_value" not in self.response:
            msg = "'hidden_value' is missing"
            raise ResponseNotScorableError(msg)

        if self.response["hidden_value"] == "secret":
            return 1

        return 0

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render()


class ExampleQuestion(Question):
    attempt_class = ExampleAttempt

    options: MyModel
