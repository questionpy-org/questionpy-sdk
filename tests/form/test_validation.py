#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import re

import pytest
from questionpy_common.elements import OptionsFormDefinition, StaticTextElement, FormSection, \
    CheckboxElement, RepetitionElement, TextInputElement

from questionpy.form import is_checked, equals
from questionpy.form.validation import FormReferenceError, validate_form, FormError


def test_should_not_raise_when_form_is_valid() -> None:
    form = OptionsFormDefinition(
        general=[CheckboxElement(name="chk1", hide_if=[is_checked("sect[chk2]")])],
        sections=[FormSection(name="sect", header="",
                              elements=[CheckboxElement(name="chk2", disable_if=[equals("..[chk1]", True)])])]
    )

    validate_form(form)


def test_should_raise_FormReferenceError_when_node_doesnt_exist() -> None:
    form_definition = OptionsFormDefinition(
        general=[StaticTextElement(name="static", label="", text="", hide_if=[is_checked("sect[nonexistent]")])],
        sections=[FormSection(name="sect", header="", elements=[])]
    )

    with pytest.raises(FormReferenceError) as exc_info:
        validate_form(form_definition)

    assert exc_info.value.node == "static"
    assert exc_info.value.reference == "sect[nonexistent]"
    assert exc_info.value.container_name == "sect"
    assert exc_info.value.local_name == "nonexistent"


def test_should_allow_reference_out_of_repetition() -> None:
    form_definition = OptionsFormDefinition(general=[
        CheckboxElement(name="chk"),
        RepetitionElement(name="repetition", initial_repetitions=1, increment=1, elements=[
            StaticTextElement(name="static", label="", text="", hide_if=[is_checked("..[chk]")]),
        ])
    ])

    validate_form(form_definition)


def test_should_allow_reference_within_repetition() -> None:
    form_definition = OptionsFormDefinition(general=[
        RepetitionElement(name="repetition", initial_repetitions=1, increment=1, elements=[
            CheckboxElement(name="chk"),
            StaticTextElement(name="static", label="", text="", hide_if=[is_checked("chk")]),
        ])
    ])

    validate_form(form_definition)


def test_should_forbid_reference_into_repetition() -> None:
    form_definition = OptionsFormDefinition(general=[
        StaticTextElement(name="static", label="", text="", hide_if=[is_checked("repetition[chk]")]),
        RepetitionElement(name="repetition", initial_repetitions=1, increment=1, elements=[
            CheckboxElement(name="chk")
        ])
    ])

    with pytest.raises(FormError) as exc_info:
        validate_form(form_definition)

    assert exc_info.match(re.escape("repeated element 'repetition[chk]'"))
    assert exc_info.value.node == "static"


def test_should_forbid_is_checked_on_text_input() -> None:
    form_definition = OptionsFormDefinition(general=[
        StaticTextElement(name="static", label="", text="", hide_if=[is_checked("input")]),
        TextInputElement(name="input", label="")
    ])

    with pytest.raises(FormError) as exc_info:
        validate_form(form_definition)

    assert exc_info.match(r"IsChecked.+is TextInputElement but must be.+CheckboxElement")
    assert exc_info.value.node == "static"
