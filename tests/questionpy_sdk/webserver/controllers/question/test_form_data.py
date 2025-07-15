#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_sdk.webserver.controllers.question._form_data import OptionsFormData, flatten_form_data, parse_form_data

FORM_DATA: OptionsFormData = {
    "general[input]": "Foo",
    "general[chk]": False,
    "general[radio]": "OPT_1",
    "general[my_select]": "OPT_2",
    "general[my_select_multi]": ["OPT_1", "OPT_2"],
    "general[my_hidden]": "foo",
    "general[my_repetition][1][id]": "49d9828f-9c9c-49fa-9d2e-b6fd83943eb3",
    "general[my_repetition][1][role]": "OPT_1",
    "general[my_repetition][1][name][first_name]": "Jane",
    "general[my_repetition][1][name][last_name]": "Doe",
    "general[my_repetition][2][id]": "0b803039-09db-4831-8866-9940ff3c10de",
    "general[my_repetition][2][role]": "OPT_2",
    "general[my_repetition][2][name][first_name]": "",
    "general[my_repetition][2][name][last_name]": "",
    "general[has_name]": False,
    "general[name_group][first_name]": "John",
    "general[name_group][last_name]": "Doe",
    "another_section[some_input]": "Bar",
}

PARSED_FORM_DATA = {
    "input": "Foo",
    "chk": False,
    "radio": "OPT_1",
    "my_select": "OPT_2",
    "my_select_multi": ["OPT_1", "OPT_2"],
    "my_hidden": "foo",
    "my_repetition": [
        {
            "id": "49d9828f-9c9c-49fa-9d2e-b6fd83943eb3",
            "role": "OPT_1",
            "name": {
                "first_name": "Jane",
                "last_name": "Doe",
            },
        },
        {
            "id": "0b803039-09db-4831-8866-9940ff3c10de",
            "role": "OPT_2",
            "name": {
                "first_name": "",
                "last_name": "",
            },
        },
    ],
    "has_name": False,
    "name_group": {
        "first_name": "John",
        "last_name": "Doe",
    },
    "another_section": {
        "some_input": "Bar",
    },
}


def test_parse_form_data() -> None:
    assert parse_form_data(FORM_DATA) == PARSED_FORM_DATA


def test_parse_form_data_empty_dict() -> None:
    assert parse_form_data({}) == {}


def test_flatten_form_data() -> None:
    assert flatten_form_data(PARSED_FORM_DATA, ["another_section"]) == FORM_DATA
