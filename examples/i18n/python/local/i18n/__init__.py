#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy import Attempt, NeedsManualScoringError, Question, i18n, make_question_type_init
from questionpy.form import FormModel, OptionEnum, checkbox, option, radio_group, section, static_text, text_input
from questionpy_common import TranslatableString
from questionpy_common.elements import StaticTextElement

__ = i18n.get_for(__package__)

dynamic_message = __.gettext_noop("I'm marked using a no-op function and later dynamically translated.")


class ContextSection(FormModel):
    file_status: StaticTextElement = static_text(__("Status of the file"), __.pgettext("File", "Opened"))
    amusement_park_status: StaticTextElement = static_text(
        __("Status of the amusement park"), __.pgettext("Amusement Park", "Opened")
    )

    home_depot: bool = checkbox(
        left_label=__("npgettext combines pluralization support and contextualization."),
        right_label=__.npgettext("Home Depot", "There is a light.", "There are {} lights!", 74).format(74),
    )
    picard: bool = checkbox(right_label=__.np("Picard", "There is a light.", "There are {} lights!", 4).format(4))


class MyOptions(OptionEnum):
    FIRST = option(__("First Option"))
    SECOND = option(__("Second Option"))
    THIRD = option(__("Third Option"))


class I18NModel(FormModel):
    txt: StaticTextElement = static_text(
        # TRANSLATORS: This comment will be shown in the .pot file.
        __("This is a localized FormModel."),
        __("The FormModel is defined before any initialization, so message translation needs to be deferred!"),
    )

    input: str = text_input(
        __("This is a text_input, and its label is localized!"),
        required=True,
        placeholder=__("Even this placeholder is localized!"),
        help=__("Now you can get help in your language!"),
    )

    radio_group: MyOptions = radio_group(
        __.ngettext("Choose exactly one option.", "Choose exactly {} options.", 1).format(1), MyOptions, required=True
    )

    context: ContextSection = section(__("This section shows contextualized messages."), ContextSection)


class I18NAttempt(Attempt):
    def _compute_score(self) -> float:
        raise NeedsManualScoringError

    @property
    def formulation(self) -> str:
        return self.jinja2.get_template("formulation.xhtml.j2").render()

    @property
    def general_feedback(self) -> str | TranslatableString | None:
        return "<div>" + __("Programmatic translation!", defer=False) + "</div>"

    @property
    def specific_feedback(self) -> str | TranslatableString | None:
        return "<div>" + __(dynamic_message, defer=False) + "</div>"


class I18NQuestion(Question):
    attempt_class = I18NAttempt

    options: I18NModel


init = make_question_type_init(I18NQuestion)
