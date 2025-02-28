#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import operator
from typing import Any


def _unflatten(flat_form_data: dict[str, str]) -> dict[str, Any]:
    """Splits the keys of a dictionary to form a new nested dictionary.

    Each key of the input dictionary is a reference string of a FormElements from the Options Form.
    These strings are split to create a nested dictionary, where each key is one part of the reference.
    Additionally: Dictionaries with only numerical keys (Repetition Elements) are replaced by lists.

    Examples:
        >>> _unflatten({
        ...     "general[my_hidden]": "foo",
        ...     "general[my_repetition][1][role]": "OPT_1",
        ...     "general[my_repetition][1][name][first_name]": "John",
        ... })
        {'general': {'my_hidden': 'foo', 'my_repetition': {'1': {'role': 'OPT_1', 'name': {'first_name': 'John'}}}}}
    """
    unflattened_dict: dict[str, Any] = {}
    for flat_key, value in flat_form_data.items():
        key_path = flat_key.replace("]", "").split("[")
        current_dict = unflattened_dict
        for key_part in key_path[:-1]:
            current_dict = current_dict.setdefault(key_part, {})
        current_dict[key_path[-1]] = value

    result = _convert_repetition_dict_to_list(unflattened_dict)
    if not isinstance(result, dict):
        msg = "The result is not a dictionary."
        raise TypeError(msg)

    return result


def _convert_repetition_dict_to_list(dictionary: dict[str, Any]) -> dict[str, Any] | list[Any]:
    """Recursively transforms a dict with only numerical keys to a list."""
    if not isinstance(dictionary, dict):
        return dictionary

    for key, value in dictionary.items():
        dictionary[key] = _convert_repetition_dict_to_list(value)

    if dictionary.pop("qpy_repetition_marker", ...) is not ...:
        # Sort by key (i.e. the index) and put the sorted values into a list.
        return [value for key, value in sorted(dictionary.items(), key=operator.itemgetter(0))]

    return dictionary


def parse_form_data(form_data: dict) -> dict:
    """Parses form data from a flat dictionary into a nested dictionary.

    This function parses a dictionary, where the keys are the references to the Form Element from the Options Form.
    The references are used to create a nested dictionary with the form data. Elements in the 'general' section are
    moved to the root of the dictionary.

    Examples:
        >>> parse_form_data({
        ...     "general[my_hidden]": "foo",
        ...     "general[my_repetition][1][role]": "OPT_1",
        ...     "general[my_repetition][1][name][first_name]": "John",
        ... })
        {'my_hidden': 'foo', 'my_repetition': {'1': {'role': 'OPT_1', 'name': {'first_name': 'John'}}}}
    """
    unflattened_form_data = _unflatten(form_data)
    options = unflattened_form_data.get("general", {})
    for section_name, section in unflattened_form_data.items():
        if section_name != "general":
            options[section_name] = section
    return options


def get_nested_form_data(form_data: dict[str, Any], reference: str) -> object:
    current_element = form_data
    parts = reference.replace("]", "").split("[")

    ref = parts.pop(0)
    if ref != "general":
        current_element = current_element[ref]
    while parts:
        ref = parts.pop(0)
        current_element = current_element[ref]

    return current_element
