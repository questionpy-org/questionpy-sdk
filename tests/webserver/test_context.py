#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import pytest
from questionpy_common.elements import CheckboxElement, FormSection, StaticTextElement, RepetitionElement, \
    TextInputElement, CheckboxGroupElement, Option, RadioGroupElement, SelectElement, GroupElement

from questionpy.form import is_checked, equals
from questionpy_sdk.webserver.context import _contextualize_element, _contextualize_element_list, contextualize, \
    FormElement, CxdFormElement, OptionsFormDefinition, CxdOptionsFormDefinition
from questionpy_sdk.webserver.elements import CxdStaticTextElement


text = TextInputElement()
static = StaticTextElement()
checkbox = CheckboxElement()
checkbox_group = CheckboxGroupElement()
option = Option()
radio_group = RadioGroupElement()
select = SelectElement()
group = GroupElement()
repetition = RepetitionElement()



@pytest.fixture
def example_form_definition():
    return OptionsFormDefinition(
        general=[RepetitionElement(name="my_repetition", initial_repetitions=2, increment=1, elements=[
            StaticTextElement(name="my_static", label="Static", text="Sample text { qpy:repno }")
                 ])],
        sections=[])


@pytest.fixture
def example_form_data(n: int):
    # Create example form data
    # Replace this with the appropriate test data for your use case
    return {"my_repetition": [
        {"my_static"}
    ]}


# Write tests for _contextualize_element function
def test_contextualize_element(example_form_definition: OptionsFormDefinition, example_form_data):
    cxd_options_form = contextualize(example_form_definition, example_form_data)
    print(cxd_options_form)


# Write tests for _contextualize_element_list function
def test_contextualize_element_list():
    # Write test cases for _contextualize_element_list function
    # Test different scenarios and assertions
    pass


# Write tests for contextualize function
def test_contextualize(example_form_definition, example_form_data):
    # Test the contextualize function with different scenarios
    # Ensure expected output and behavior for the given input
    pass


def test_contextualize_static_element():
    # Create a sample FormElement
    element = StaticTextElement(name="example", label="Example", text="Sample text")

    # Create a sample form_data
    form_data = {"example": "example_value"}

    # Call _contextualize_element function
    cxd_element = _contextualize_element(element, form_data, [], context={"repno": "123"})

    # Assertions based on expected behavior
    assert isinstance(cxd_element, CxdStaticTextElement)
    assert cxd_element.label == "Example"
    # Add more assertions based on the expected behavior

