from questionpy import Attempt, NeedsManualScoringError, Question


class I18NAttempt(Attempt):
    def _compute_score(self) -> float:
        raise NeedsManualScoringError

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render()


class I18NQuestion(Question):
    attempt_class = I18NAttempt
