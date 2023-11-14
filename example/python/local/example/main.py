#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from importlib.resources import files

from questionpy_common.models import QuestionModel, ScoringMethod, AttemptModel, AttemptUi

from questionpy import QuestionType, Attempt, Question, BaseQuestionState, BaseAttemptState
from questionpy.form import *


class NameGroup(FormModel):
    first_name = text_input("First Name")
    last_name = text_input("Last Name")


class MyOptions(OptionEnum):
    OPT_1 = option("Option 1", selected=True)
    OPT_2 = option("Option 2")


class Participants(FormModel):
    role = select("Role:", MyOptions)
    name = group("Name", NameGroup)


class MyModel(FormModel):
    static = static_text("Some static text", """Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
    nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam
    et justo duo dolores et ea rebum.""")
    input = text_input("My second Input", required=True, hide_if=[is_checked("chk")])
    chk = checkbox("Left label", None, help="""Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
    nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.""")
    radio = radio_group("My Radio Group", MyOptions)
    my_select = select("My select box", MyOptions, multiple=True)
    my_hidden = hidden("foo")
    my_repetition = repeat(Participants)

    has_name = checkbox(None, "I have a name.")
    name_group = group("Name", NameGroup, disable_if=[is_not_checked("has_name")])


class ExampleAttempt(Attempt["ExampleQuestion", BaseAttemptState]):
    def export(self) -> AttemptModel:
        return AttemptModel(variant=1, ui=AttemptUi(
            content=(files(__package__) / "multiple-choice.xhtml").read_text()
        ))


class ExampleQuestion(Question[BaseQuestionState[MyModel], ExampleAttempt]):
    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


class ExampleQuestionType(QuestionType[MyModel, ExampleQuestion]):
    pass
