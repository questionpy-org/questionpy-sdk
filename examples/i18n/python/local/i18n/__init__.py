#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy import Attempt, NeedsManualScoringError, Question, i18n, make_question_type_init
from questionpy.form import FormModel, static_text
from questionpy_common.elements import StaticTextElement

_, _N = i18n.get_for(__package__)


class I18NModel(FormModel):
    txt: StaticTextElement = static_text(
        # TRANSLATORS: This comment will be shown in the .pot file.
        _("Important Notice"),
        _("If you or a loved one has been diagnosed with mesothelioma, you may be entitled to financial compensation."),
    )


class I18NAttempt(Attempt):
    def _compute_score(self) -> float:
        raise NeedsManualScoringError

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render()

    @property
    def general_feedback(self) -> str | None:
        return "<div>" + _("It's all wrong!") + "</div>"


class I18NQuestion(Question):
    attempt_class = I18NAttempt

    options: I18NModel


init = make_question_type_init(I18NQuestion)
