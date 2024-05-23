#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from questionpy_sdk.webserver._form_data import parse_form_data

RAW_FORM_DATA = {
    "general[input]": "my input ",
    "general[radio]": "OPT_1",
    "general[my_hidden]": "foo",
    "general[my_repetition][qpy_repetition_marker]": "",
    "general[my_repetition][1][qpy_repetition_item_marker]": "",
    "general[my_repetition][1][role]": "OPT_1",
    "general[my_repetition][1][name][first_name]": "John ",
    "general[my_repetition][1][name][last_name]": "Doe",
    "general[my_repetition][2][qpy_repetition_item_marker]": "",
    "general[my_repetition][2][role]": "OPT_2",
    "general[my_repetition][2][name][first_name]": "Max",
    "general[my_repetition][2][name][last_name]": "Mustermann",
    "general[my_select]": ["OPT_1", "OPT_2"],
}
REPETITION_REF = "general[my_repetition]"


def test_parse_form_data_should_not_raise_if_valid() -> None:
    parsed_form_data = parse_form_data(RAW_FORM_DATA)

    assert isinstance(parsed_form_data["my_repetition"], list)  # Repetition Element should be List
    assert isinstance(parsed_form_data["my_select"], list)  # Multi Select should be List
    assert "general" not in parsed_form_data  # Elements in 'general' should be at the root
