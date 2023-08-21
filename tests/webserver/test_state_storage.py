#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import pytest

from questionpy_sdk.webserver.state_storage import parse_form_data, add_repetition

RAW_FORM_DATA = {'general[input]': 'my input ',
                 'general[radio]': 'OPT_1',
                 'general[my_hidden]': 'foo',
                 'general[my_repetition][1][role]': 'OPT_1',
                 'general[my_repetition][1][name][first_name]': 'John ',
                 'general[my_repetition][1][name][last_name]': 'Doe',
                 'general[my_repetition][2][role]': 'OPT_2',
                 'general[my_repetition][2][name][first_name]': 'Max',
                 'general[my_repetition][2][name][last_name]': 'Mustermann',
                 'general[my_select]': ['OPT_1', 'OPT_2']}
REPETITION_REF = 'general[my_repetition]'


def test_parse_form_data_should_not_raise_if_valid() -> None:
    parsed_form_data = parse_form_data(RAW_FORM_DATA)

    assert isinstance(parsed_form_data['my_repetition'], list)  # Repetition Element should be List
    assert isinstance(parsed_form_data['my_select'], list)  # Multi Select should be List
    assert 'general' not in parsed_form_data  # Elements in 'general' should be at the root


def test_parse_form_data_should_raise_error_if_no_general_section_present() -> None:
    """Tests parsing a non-valid form_data dictionary (section 'general' missing)."""
    data = ({'some_key': 1})

    with pytest.raises(KeyError) as exc_info:
        parse_form_data(data)

    assert isinstance(exc_info.value, KeyError)  # Form data needs a 'general' section.


@pytest.mark.parametrize('increment', (
    1,
    2,
    100,
    0,
    -1
))
def test_add_repetition_should_add_repetition_for_valid_input(increment: int) -> None:
    """Test if add_repetition adds 'increment' amount of repetitions to the referenced repetition element."""
    reference = REPETITION_REF.replace(']', '').split('[')
    old_element = parse_form_data(RAW_FORM_DATA)
    new_element = add_repetition(parse_form_data(RAW_FORM_DATA), reference.copy(), increment)

    # Find the repetition element
    if (ref := reference.pop(0)) != 'general':
        old_element = old_element[ref]
        new_element = new_element[ref]
    while reference:
        ref = reference.pop(0)
        old_element = old_element[ref]
        new_element = new_element[ref]

    assert isinstance(old_element, list)
    assert isinstance(new_element, list)
    assert len(new_element) == len(old_element) + max(increment, 0)
