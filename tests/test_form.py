from typing import Optional, List, Literal, Set, Any

import pytest
from pydantic import ValidationError

from questionpy.form import *  # pylint: disable=wildcard-import


class MyOptionEnum(OptionEnum):
    OPT_1 = option("Label 1")


class SimpleFormModel(FormModel):
    input: str = text_input("My Text Input", True)


class NestedFormModel(FormModel):
    general_field: Optional[str] = text_input("General Text Input", False)

    sect = section("My Header", SimpleFormModel)
    grp = group("My Group", SimpleFormModel)


def test_SimpleFormModel_should_render_correct_form() -> None:
    assert SimpleFormModel.form() == Form(
        general=[TextInputElement(name="input", label="My Text Input", required=True)]
    )


def test_NestedFormModel_should_render_correct_form() -> None:
    assert NestedFormModel.form() == Form(
        general=[
            TextInputElement(name="general_field", label="General Text Input", required=False),
            GroupElement(
                name="grp",
                label="My Group",
                elements=[TextInputElement(name="input", label="My Text Input", required=True)]
            )
        ],
        sections=[FormSection(
            header="My Header",
            elements=[TextInputElement(name="input", label="My Text Input", required=True)]
        )]
    )


def test_NestedFormModel_should_parse_correctly() -> None:
    parsed = NestedFormModel(general_field="Valid value", sect=SimpleFormModel(input="Valid value"),
                             grp=SimpleFormModel(input=b"Coercible to valid value"))

    assert parsed.general_field == "Valid value"
    assert parsed.sect.input == "Valid value"
    assert parsed.grp.input == "Coercible to valid value"


def test_should_raise_ValidationError_when_required_option_is_missing() -> None:
    with pytest.raises(ValidationError):
        SimpleFormModel.parse_obj({})


RADIO_OPTIONS = [
    RadioGroupElement.Option(label="", value="opt1"),
    RadioGroupElement.Option(label="", value="opt2")
]

SELECT_OPTIONS = [
    SelectElement.Option(label="", value="opt1"),
    SelectElement.Option(label="", value="opt2"),
]


@pytest.mark.parametrize("initializer,expected_elements", [
    (text_input("Label", required=True), [TextInputElement(name="field", label="Label", required=True)]),
    (static_text("Label", "Lorem ipsum dolor sit amet."),
     [StaticTextElement(name="field", label="Label", text="Lorem ipsum dolor sit amet.")]),
    (checkbox("Left Label", "Right Label", required=True),
     [CheckboxElement(name="field", left_label="Left Label", right_label="Right Label", required=True)]),
    (radio_group("Label", [RadioGroupElement.Option(label="Label", value="opt1", selected=True)], required=True),
     [RadioGroupElement(name="field", label="Label",
                        options=[RadioGroupElement.Option(label="Label", value="opt1", selected=True)],
                        required=True)]),
    (radio_group("Label", MyOptionEnum, required=True),
     [RadioGroupElement(name="field", label="Label",
                        options=[RadioGroupElement.Option(label="Label 1", value="OPT_1")],
                        required=True)]),
    (select("Label", [SelectElement.Option(label="Label", value="opt1", selected=True)], required=True, multiple=True),
     [SelectElement(name="field", label="Label",
                    options=[SelectElement.Option(label="Label", value="opt1", selected=True)],
                    required=True, multiple=True)]),
    (select("Label", MyOptionEnum, required=True, multiple=True),
     [SelectElement(name="field", label="Label", options=[SelectElement.Option(label="Label 1", value="OPT_1")],
                    required=True, multiple=True)]),
    (hidden("value"), [HiddenElement(name="field", value="value")]),
])
def test_should_render_correct_form(initializer: object, expected_elements: List[FormElement]) -> None:
    class TheModel(FormModel):
        # mypy crashes without the type annotation
        field: Any = initializer

    form = TheModel.form()
    assert form.general == expected_elements


@pytest.mark.parametrize("annotation,initializer,input_value,expected_result", [
    # text_input
    (str, text_input("", True), "valid", "valid"),
    (str, text_input("", True), b"coercible", "coercible"),
    (Optional[str], text_input("", False), "valid", "valid"),
    (Optional[str], text_input("", False), None, None),
    (Optional[str], text_input("", False), ..., None),
    # checkbox
    (bool, checkbox("", "", required=True), True, True),
    (bool, checkbox("", "", required=False), True, True),
    (bool, checkbox("", "", required=False), False, False),
    (bool, checkbox("", "", required=False), ..., False),
    # radio_group
    (Optional[Literal["opt1", "opt2"]], radio_group("", RADIO_OPTIONS), ..., None),
    (Literal["opt1", "opt2"], radio_group("", RADIO_OPTIONS, required=True), "opt2", "opt2"),
    (Optional[str], radio_group("", RADIO_OPTIONS), ..., None),
    (Optional[MyOptionEnum], radio_group("", MyOptionEnum), ..., None),
    (MyOptionEnum, radio_group("", MyOptionEnum, required=True), "OPT_1", MyOptionEnum.OPT_1),
    # select
    (Optional[str], select("", SELECT_OPTIONS), ..., None),
    (str, select("", SELECT_OPTIONS, required=True), "opt2", "opt2"),
    (Set[str], select("", SELECT_OPTIONS, multiple=True), ..., set()),
    (Set[Literal["opt1", "opt2"]], select("", SELECT_OPTIONS, required=True, multiple=True), ["opt1", "opt2"],
     {"opt1", "opt2"}),
    (MyOptionEnum, select("", MyOptionEnum, required=True, multiple=False), "OPT_1", MyOptionEnum.OPT_1),
    (Optional[MyOptionEnum], select("", MyOptionEnum, required=False, multiple=False), ..., None),
    (Set[MyOptionEnum], select("", MyOptionEnum, required=False, multiple=True), ["OPT_1"], {MyOptionEnum.OPT_1}),
    (Set[MyOptionEnum], select("", MyOptionEnum, required=False, multiple=True), ..., set()),
    # hidden
    (str, hidden("value"), "value", "value"),
    (Literal["value"], hidden("value"), "value", "value"),
    # group
    (SimpleFormModel, group("", SimpleFormModel), {"input": "abc"}, SimpleFormModel(input="abc")),
    # section
    (SimpleFormModel, section("", SimpleFormModel), {"input": "abc"}, SimpleFormModel(input="abc")),
])
def test_should_parse_correctly_when_input_is_valid(annotation: object, initializer: object, input_value: object,
                                                    expected_result: object) -> None:
    class TheModel(FormModel):
        field: annotation = initializer  # type: ignore[valid-type]

    parsed = TheModel.parse_obj({} if input_value is Ellipsis else {
        "field": input_value
    })

    assert parsed.dict() == {
        "field": expected_result
    }


@pytest.mark.parametrize("annotation,initializer,input_value", [
    # text_input
    (str, text_input("", True), ...),
    (str, text_input("", True), None),
    (Optional[str], text_input("", False), {}),
    # checkbox
    (bool, checkbox("", "", required=False), 42),
    # radio_group
    (Optional[Literal["opt1", "opt2"]], radio_group("", RADIO_OPTIONS), "opt3"),
    (Literal["opt1", "opt2"], radio_group("", RADIO_OPTIONS, required=True), None),
    (Literal["opt1", "opt2"], radio_group("", RADIO_OPTIONS, required=True), ...),
    (Optional[MyOptionEnum], radio_group("", MyOptionEnum), "not an option"),
    (MyOptionEnum, radio_group("", MyOptionEnum, required=True), ...),
    # select
    (Optional[Literal["opt1", "opt2"]], select("", SELECT_OPTIONS), "opt3"),
    (Literal["opt1", "opt2"], select("", SELECT_OPTIONS, required=True), ...),
    (Set[Literal["opt1", "opt2"]], select("", SELECT_OPTIONS, multiple=True), "opt1"),
    (Optional[MyOptionEnum], select("", MyOptionEnum), "not an option"),
    (MyOptionEnum, select("", MyOptionEnum, required=True), ...),
    (Set[MyOptionEnum], select("", MyOptionEnum, multiple=True), ["not an option"]),
    # hidden
    (Literal["value"], hidden("value"), "something else"),
    (str, hidden("value"), ...),
    # group
    (SimpleFormModel, group("", SimpleFormModel), ...),
    # section
    (SimpleFormModel, section("", SimpleFormModel), {}),
])
def test_should_raise_ValidationError_when_input_is_invalid(annotation: object, initializer: object,
                                                            input_value: object) -> None:
    class TheModel(FormModel):
        field: annotation = initializer  # type: ignore[valid-type]

    with pytest.raises(ValidationError):
        TheModel.parse_obj({} if input_value is Ellipsis else {
            "field": input_value
        })


@pytest.mark.parametrize("annotation,initializer", [
    # text_input
    (str, text_input("", required=False)),
    (Optional[str], text_input("", required=True)),
    # checkbox
    (str, checkbox("", "")),
    # radio_group
    (str, radio_group("", RADIO_OPTIONS)),
    (Optional[str], radio_group("", RADIO_OPTIONS, required=True)),
    (str, radio_group("", MyOptionEnum, required=True)),
    (MyOptionEnum, radio_group("", MyOptionEnum)),
    (Optional[MyOptionEnum], radio_group("", MyOptionEnum, required=True)),
    # select
    (Set[str], select("", SELECT_OPTIONS)),
    (Set[str], select("", SELECT_OPTIONS, required=True)),
    (str, select("", SELECT_OPTIONS, multiple=True)),
    (str, select("", MyOptionEnum, required=True)),
    (Set[MyOptionEnum], select("", MyOptionEnum)),
    (Set[MyOptionEnum], select("", MyOptionEnum, required=True)),
    (MyOptionEnum, select("", MyOptionEnum, multiple=True)),
    # hidden
    (Optional[str], hidden("value")),
    # group
    (dict, group("", SimpleFormModel)),
    # section
    (dict, section("", SimpleFormModel)),
])
def test_should_raise_TypeError_when_annotation_is_wrong(annotation: object, initializer: object) -> None:
    with pytest.raises(TypeError):
        class TheModel(FormModel):
            # pylint: disable=unused-variable
            field: annotation = initializer  # type: ignore[valid-type]
