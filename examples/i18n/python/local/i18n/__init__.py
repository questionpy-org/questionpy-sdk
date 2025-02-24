#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy import Attempt, NeedsManualScoringError, Question, i18n, make_question_type_init
from questionpy.form import FormModel, OptionEnum, checkbox, option, radio_group, section, static_text, text_input
from questionpy_common import TranslatableString
from questionpy_common.elements import StaticTextElement

_, _N = i18n.get_for(__package__)


class ContextSection(FormModel):
    file_status: StaticTextElement = static_text(_("Status of the file"), _.pgettext("File", "Opened"))
    amusement_park_status: StaticTextElement = static_text(
        _("Status of the amusement park"), _.pgettext("Amusement Park", "Opened")
    )

    home_depot: bool = checkbox(
        left_label=_("npgettext combines pluralization support and contextualization."),
        right_label=_.npgettext("Home Depot", "There is a light.", "There are {} lights!", 74).format(74),
    )
    picard: bool = checkbox(right_label=_.npgettext("Picard", "There is a light.", "There are {} lights!", 4).format(4))


class MyOptions(OptionEnum):
    FIRST = option(_("First Option"))
    SECOND = option(_("Second Option"))
    THIRD = option(_("Third Option"))


class I18NModel(FormModel):
    txt: StaticTextElement = static_text(
        # TRANSLATORS: This comment will be shown in the .pot file.
        _("This is a localized FormModel."),
        _("The FormModel is defined before any initialization, so message translation needs to be deferred!"),
    )

    input: str = text_input(
        _("This is a text_input, and its label is localized!"),
        required=True,
        placeholder=_("Even this placeholder is localized!"),
        help=_("Now you can get help in your language!"),
    )

    radio_group: MyOptions = radio_group(
        _.ngettext("Choose exactly one option.", "Choose exactly {} options.", 1).format(1), MyOptions, required=True
    )

    context: ContextSection = section(_("This section shows contextualized messages."), ContextSection)


class I18NAttempt(Attempt):
    def _compute_score(self) -> float:
        raise NeedsManualScoringError

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render()

    @property
    def general_feedback(self) -> str | TranslatableString | None:
        return "<div>" + _("Programmatic translation!", defer=False) + "</div>"


class I18NQuestion(Question):
    attempt_class = I18NAttempt

    options: I18NModel


init = make_question_type_init(I18NQuestion)
