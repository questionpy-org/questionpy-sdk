#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Any, Literal, Optional

import pytest
from pydantic import TypeAdapter, ValidationError

from questionpy import form


class MyOptionEnum(form.OptionEnum):
    OPT_1 = form.option("Label 1")


class SimpleFormModel(form.FormModel):
    input: str = form.text_input("My Text Input", required=True)


class NestedFormModel(form.FormModel):
    general_field: str | None = form.text_input("General Text Input")

    sect: SimpleFormModel = form.section("My Header", SimpleFormModel)
    grp: SimpleFormModel = form.group("My Group", SimpleFormModel)
    rep: list[SimpleFormModel] = form.repeat(SimpleFormModel, initial=1)


def test_simple_form_model_should_render_correct_form() -> None:
    assert SimpleFormModel.qpy_form == form.OptionsFormDefinition(
        general=[form.TextInputElement(name="input", label="My Text Input", required=True)]
    )


def test_nested_form_model_should_render_correct_form() -> None:
    assert NestedFormModel.qpy_form == form.OptionsFormDefinition(
        general=[
            form.TextInputElement(name="general_field", label="General Text Input", required=False),
            form.GroupElement(
                name="grp",
                label="My Group",
                elements=[form.TextInputElement(name="input", label="My Text Input", required=True)],
            ),
            form.RepetitionElement(
                name="rep",
                initial_repetitions=1,
                increment=1,
                elements=[form.TextInputElement(name="input", label="My Text Input", required=True)],
            ),
        ],
        sections=[
            form.FormSection(
                name="sect",
                header="My Header",
                elements=[form.TextInputElement(name="input", label="My Text Input", required=True)],
            )
        ],
    )


def test_nested_form_model_should_parse_correctly() -> None:
    parsed = NestedFormModel(
        general_field="Valid value",
        sect=SimpleFormModel(input="Valid value"),
        grp=SimpleFormModel(input=b"Coercible to valid value"),
        rep=[SimpleFormModel(input="abcdefg")],
    )

    assert parsed.general_field == "Valid value"
    assert parsed.sect.input == "Valid value"
    assert parsed.grp.input == "Coercible to valid value"
    assert len(parsed.rep) == 1
    assert parsed.rep[0].input == "abcdefg"


def test_should_raise_validation_error_when_required_option_is_missing() -> None:
    with pytest.raises(ValidationError):
        SimpleFormModel.model_validate({})


@pytest.mark.parametrize(
    ("initializer", "expected_elements"),
    [
        (
            form.text_input("Label", required=True, help="Help"),
            [form.TextInputElement(name="field", label="Label", required=True, help="Help")],
        ),
        (
            form.text_area("Label", help="Help", default="Default"),
            [form.TextAreaElement(name="field", label="Label", help="Help", default="Default")],
        ),
        (
            form.static_text("Label", "Lorem ipsum dolor sit amet.", help="Help"),
            [form.StaticTextElement(name="field", label="Label", text="Lorem ipsum dolor sit amet.", help="Help")],
        ),
        (
            form.checkbox("Left Label", "Right Label", required=True, help="Help"),
            [
                form.CheckboxElement(
                    name="field", left_label="Left Label", right_label="Right Label", required=True, help="Help"
                )
            ],
        ),
        (
            form.radio_group("Label", MyOptionEnum, required=True, help="Help"),
            [
                form.RadioGroupElement(
                    name="field",
                    label="Label",
                    options=[form.Option(label="Label 1", value="OPT_1")],
                    required=True,
                    help="Help",
                )
            ],
        ),
        (
            form.select("Label", MyOptionEnum, required=True, multiple=True, help="Help"),
            [
                form.SelectElement(
                    name="field",
                    label="Label",
                    options=[form.Option(label="Label 1", value="OPT_1")],
                    required=True,
                    multiple=True,
                    help="Help",
                )
            ],
        ),
        (form.hidden("value"), [form.HiddenElement(name="field", value="value")]),
        (
            form.repeat(SimpleFormModel, initial=1),
            [
                form.RepetitionElement(
                    name="field",
                    initial_repetitions=1,
                    increment=1,
                    elements=[form.TextInputElement(name="input", label="My Text Input", required=True)],
                )
            ],
        ),
    ],
)
def test_should_render_correct_form(initializer: object, expected_elements: list[form.FormElement]) -> None:
    class TheModel(form.FormModel):
        # mypy crashes without the type annotation
        field: Any = initializer

    assert expected_elements == TheModel.qpy_form.general


@pytest.mark.parametrize(
    ("annotation", "initializer", "input_value", "expected_result"),
    [
        # text_input
        (str, form.text_input("", required=True), "valid", "valid"),
        (str, form.text_input("", required=True), b"coercible", "coercible"),
        (str | None, form.text_input(""), "valid", "valid"),
        (str | None, form.text_input(""), None, None),
        (str | None, form.text_input(""), ..., None),
        # text_area
        (str, form.text_area("", required=True), "valid", "valid"),
        (str, form.text_area("", required=True), b"coercible", "coercible"),
        (str | None, form.text_area(""), "valid", "valid"),
        (str | None, form.text_area(""), None, None),
        (str | None, form.text_area(""), ..., None),
        # checkbox
        (bool, form.checkbox("", "", required=True), True, True),
        (bool, form.checkbox("", "", required=False), True, True),
        (bool, form.checkbox("", "", required=False), False, False),
        (bool, form.checkbox("", "", required=False), ..., False),
        # radio_group
        (MyOptionEnum | None, form.radio_group("", MyOptionEnum), ..., None),
        (MyOptionEnum, form.radio_group("", MyOptionEnum, required=True), "OPT_1", MyOptionEnum.OPT_1),
        (
            MyOptionEnum | None,
            form.radio_group("", MyOptionEnum, required=True, disable_if=form.is_checked("field")),
            "OPT_1",
            MyOptionEnum.OPT_1,
        ),
        # select
        (MyOptionEnum, form.select("", MyOptionEnum, required=True, multiple=False), "OPT_1", MyOptionEnum.OPT_1),
        (MyOptionEnum | None, form.select("", MyOptionEnum, required=False, multiple=False), ..., None),
        (
            MyOptionEnum | None,
            form.select("", MyOptionEnum, required=True, multiple=False, disable_if=form.is_checked("field")),
            ...,
            None,
        ),
        (
            set[MyOptionEnum],
            form.select("", MyOptionEnum, required=False, multiple=True),
            ["OPT_1"],
            {MyOptionEnum.OPT_1},
        ),
        (set[MyOptionEnum], form.select("", MyOptionEnum, required=False, multiple=True), ..., set()),
        # hidden
        (str, form.hidden("value"), "value", "value"),
        (Literal["value"], form.hidden("value"), "value", "value"),
        (Optional[Literal["value"]], form.hidden("value", disable_if=form.is_checked("field")), ..., None),  # noqa: UP007
        # group
        (SimpleFormModel, form.group("", SimpleFormModel), {"input": "abc"}, SimpleFormModel(input="abc")),
        # repetition
        (
            list[SimpleFormModel],
            form.repeat(SimpleFormModel, initial=1),
            [{"input": "abc"}, {"input": "def"}],
            [SimpleFormModel(input="abc"), SimpleFormModel(input="def")],
        ),
        # section
        (SimpleFormModel, form.section("", SimpleFormModel), {"input": "abc"}, SimpleFormModel(input="abc")),
    ],
)
def test_should_parse_correctly_when_input_is_valid(
    annotation: object, initializer: object, input_value: object, expected_result: object
) -> None:
    class TheModel(form.FormModel):
        field: annotation = initializer  # type: ignore[valid-type]

    parsed = TheModel.model_validate({} if input_value is Ellipsis else {"field": input_value})

    assert parsed.field == expected_result


@pytest.mark.parametrize(
    ("annotation", "initializer", "input_value"),
    [
        # text_input
        (str, form.text_input("", required=True), ...),
        (str, form.text_input("", required=True), None),
        (str | None, form.text_input(""), {}),
        # text_area
        (str, form.text_area("", required=True), ...),
        (str, form.text_area("", required=True), None),
        (str | None, form.text_area(""), {}),
        # checkbox
        (bool, form.checkbox("", "", required=False), 42),
        # radio_group
        (MyOptionEnum | None, form.radio_group("", MyOptionEnum), "not an option"),
        (MyOptionEnum, form.radio_group("", MyOptionEnum, required=True), ...),
        # select
        (MyOptionEnum | None, form.select("", MyOptionEnum), "not an option"),
        (MyOptionEnum, form.select("", MyOptionEnum, required=True), ...),
        (set[MyOptionEnum], form.select("", MyOptionEnum, multiple=True), ["not an option"]),
        # hidden
        (Literal["value"], form.hidden("value"), "something else"),
        (str, form.hidden("value"), ...),
        # group
        (SimpleFormModel, form.group("", SimpleFormModel), ...),
        # repetition
        (list[SimpleFormModel], form.repeat(SimpleFormModel, initial=1), {"input": "def"}),
        (list[SimpleFormModel], form.repeat(SimpleFormModel, initial=1), ...),
        # section
        (SimpleFormModel, form.section("", SimpleFormModel), {}),
    ],
)
def test_should_raise_validation_error_when_input_is_invalid(
    annotation: object, initializer: object, input_value: object
) -> None:
    class TheModel(form.FormModel):
        field: annotation = initializer  # type: ignore[valid-type]

    with pytest.raises(ValidationError):
        TheModel.model_validate({} if input_value is Ellipsis else {"field": input_value})


@pytest.mark.parametrize(
    ("annotation", "initializer"),
    [
        # text_input
        (str, form.text_input("", required=False)),
        (str | None, form.text_input("", required=True)),
        (str, form.text_input("", required=True, disable_if=form.is_checked("field"))),  # Required, but conditional
        # text_area
        (str, form.text_area("", required=False)),
        (str | None, form.text_area("", required=True)),
        (str, form.text_area("", required=True, disable_if=form.is_checked("field"))),  # Required, but conditional
        # checkbox
        (str, form.checkbox("", "")),
        # radio_group
        (str, form.radio_group("", MyOptionEnum, required=True)),
        (MyOptionEnum, form.radio_group("", MyOptionEnum)),
        (MyOptionEnum | None, form.radio_group("", MyOptionEnum, required=True)),
        # select
        (str, form.select("", MyOptionEnum, required=True)),
        (set[MyOptionEnum], form.select("", MyOptionEnum)),
        (set[MyOptionEnum], form.select("", MyOptionEnum, required=True)),
        (MyOptionEnum, form.select("", MyOptionEnum, multiple=True)),
        # hidden
        (str | None, form.hidden("value")),
        # group
        (dict, form.group("", SimpleFormModel)),
        # repetition
        (SimpleFormModel, form.repeat(SimpleFormModel, initial=1)),
        (list, form.repeat(SimpleFormModel, initial=1)),
        (list[str], form.repeat(SimpleFormModel, initial=1)),
        # section
        (dict, form.section("", SimpleFormModel)),
    ],
)
def test_should_raise_type_error_when_annotation_is_wrong(annotation: object, initializer: object) -> None:
    with pytest.raises(TypeError):

        class TheModel(form.FormModel):
            field: annotation = initializer  # type: ignore[valid-type]


def test_option_enum_should_serialize_to_value() -> None:
    type_adapter = TypeAdapter(MyOptionEnum)
    assert type_adapter.dump_json(MyOptionEnum.OPT_1) == b'"OPT_1"'


def test_option_enum_should_deserialize_from_value() -> None:
    type_adapter = TypeAdapter(MyOptionEnum)
    assert type_adapter.validate_python("OPT_1") is MyOptionEnum.OPT_1
    assert type_adapter.validate_json('"OPT_1"') is MyOptionEnum.OPT_1


def test_group_without_required_fields_can_be_omitted() -> None:
    class Inner(form.FormModel):
        optional: str | None = form.text_input("")

    class Outer(form.FormModel):
        grp: Inner = form.group("", Inner)

    parsed = Outer.model_validate({})
    assert isinstance(parsed.grp, Inner)
    assert parsed.grp.optional is None


def test_group_with_required_field_cannot_be_omitted() -> None:
    class Inner(form.FormModel):
        optional: str = form.text_input("", required=True)

    class Outer(form.FormModel):
        grp: Inner = form.group("", Inner)

    with pytest.raises(ValidationError):
        Outer.model_validate({})
