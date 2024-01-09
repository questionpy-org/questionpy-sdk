#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from itertools import chain
from typing import Union

import pytest
from _pytest.fixtures import SubRequest

from questionpy_common.elements import CheckboxElement, FormSection, StaticTextElement, RepetitionElement, \
    TextInputElement, CheckboxGroupElement, Option, RadioGroupElement, SelectElement, GroupElement, \
    OptionsFormDefinition, FormElement

from questionpy_sdk.webserver.context import contextualize, CxdFormElement
from questionpy_sdk.webserver.elements import CxdRepetitionElement, CxdGroupElement, CxdOption, CxdRadioGroupElement, \
    CxdSelectElement, CxdCheckboxGroupElement


@pytest.fixture(params=[(
    TextInputElement(name="text", label="Text", default="Df { qpy:repno }", placeholder="Ph { qpy:repno }"),
    StaticTextElement(name="static", label="Static", text="Sample text { qpy:repno }"),
    CheckboxElement(name="chk", left_label="ll { qpy:repno }", right_label="rr { qpy:repno }"),
    CheckboxGroupElement(name="chk_group", checkboxes=[
        CheckboxElement(name="chk1", left_label="l1 { qpy:repno }", right_label="r1 { qpy:repno }", ),
        CheckboxElement(name="chk2", left_label="l2 { qpy:repno }", right_label="r2 { qpy:repno }", )
    ]),
    RadioGroupElement(name="radio", label="Text", options=[
        Option(label="opt1 { qpy:repno }", value="opt1"),
        Option(label="opt2 { qpy:repno }", value="opt2")
    ]),
    SelectElement(name="select", label="Text { qpy:repno }", options=[
        Option(label="opt1 { qpy:repno }", value="opt1"),
        Option(label="opt2 { qpy:repno }", value="opt2")
    ]),
    GroupElement(name="group", label="Text", elements=[
        CheckboxElement(name="chk", left_label="ll { qpy:repno }", right_label="rr { qpy:repno }")
    ])
)])
def form_elements_fixture(request: SubRequest) -> tuple[FormElement]:
    return request.param


@pytest.fixture
def repetition_element_fixture(form_elements_fixture: tuple[FormElement]) -> RepetitionElement:
    return RepetitionElement(name="repetition", initial_repetitions=1, increment=1, elements=form_elements_fixture)


@pytest.fixture
def form_definition_fixture(repetition_element_fixture: RepetitionElement) -> OptionsFormDefinition:
    return OptionsFormDefinition(
        general=[repetition_element_fixture],
        sections=[FormSection(name="section", header="Section", elements=[repetition_element_fixture])])


def _substring_in_cxd_element(element: Union[CxdFormElement, CxdOption], substring: str) -> bool:
    for _, value in element.model_dump().items():
        if not isinstance(value, str):
            continue
        if substring in value:
            return True

    if isinstance(element, (CxdRadioGroupElement, CxdSelectElement)):
        return any(_substring_in_cxd_element(opt, substring) for opt in element.cxd_options)
    if isinstance(element, CxdGroupElement):
        return any(_substring_in_cxd_element(el, substring) for el in element.cxd_elements)
    if isinstance(element, CxdCheckboxGroupElement):
        return any(_substring_in_cxd_element(chk, substring) for chk in element.cxd_checkboxes)

    return False


def test_contextualize_should_not_replace_identifier_in_group(form_elements_fixture: tuple[FormElement]) -> None:
    form_definition = OptionsFormDefinition(
        general=[RepetitionElement(name="repetition", initial_repetitions=1, increment=1, elements=[
            GroupElement(name="group { qpy:repno }", label="Text { qpy:repno }", elements=[form_elements_fixture[0]])
        ])],
        sections=[])
    cxd_form = contextualize(form_definition, form_data=None)

    cxd_repetition = cxd_form.general[0]
    assert isinstance(cxd_repetition, CxdRepetitionElement)

    cxd_group = cxd_repetition.cxd_elements[0][0]
    assert isinstance(cxd_group, CxdGroupElement)
    assert _substring_in_cxd_element(cxd_group, "qpy:repno")


def test_contextualize_should_replace_identifiers(form_definition_fixture: OptionsFormDefinition) -> None:
    repetition_element = form_definition_fixture.general[0]
    assert isinstance(repetition_element, RepetitionElement)
    repetition_element.initial_repetitions = 5

    cxd_form = contextualize(form_definition_fixture, form_data=None)
    cxd_repetition = cxd_form.general[0]
    assert isinstance(cxd_repetition, CxdRepetitionElement)

    # the "qpy:repno" identifier should not be in any model fields
    elements = chain.from_iterable(cxd_repetition.cxd_elements)
    for element in elements:
        assert not _substring_in_cxd_element(element, "qpy:repno")

    # the identifier should be replaced with the running number
    for index, repetition in enumerate(cxd_repetition.cxd_elements, 1):
        for element in repetition:
            assert _substring_in_cxd_element(element, str(index))


def test_contextualize_should_not_replace_outside_repetition(form_elements_fixture: tuple[FormElement]) -> None:
    form_definition = OptionsFormDefinition(
        general=form_elements_fixture,
        sections=[])
    cxd_form = contextualize(form_definition, form_data=None)

    # the "qpy:repno" identifier should still be in the model fields
    for element in cxd_form.general:
        assert _substring_in_cxd_element(element, "qpy:repno")
