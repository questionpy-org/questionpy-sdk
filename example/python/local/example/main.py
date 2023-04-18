from questionpy import QuestionType
from questionpy.form import *


class NameGroup(FormModel):
    first_name = text_input("First Name")
    last_name = text_input("Last Name")


class MyOptions(OptionEnum):
    OPT_1 = option("Option 1", selected=True)
    OPT_2 = option("Option 2")


class MyModel(FormModel):
    static = static_text("Some static text", """Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
    nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam
    et justo duo dolores et ea rebum.""")
    input = text_input("My second Input", required=True, hide_if=[is_checked("chk")])
    chk = checkbox("Left label", None)
    radio = radio_group("My Radio Group", MyOptions)
    my_select = select("My select box", MyOptions, multiple=True)
    my_hidden = hidden("foo")

    has_name = checkbox(None, "I have a name.")
    name_group = group("Name", NameGroup, disable_if=[is_not_checked("has_name")])


class ExampleQuestionType(QuestionType[MyModel]):
    None
