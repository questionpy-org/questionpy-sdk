#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import operator
from collections.abc import Iterable, Mapping
from typing import Any

type OptionsFormDataValue = str | int | float | bool | list[str] | None
type OptionsFormData = Mapping[str, OptionsFormDataValue]


def _unflatten(flat_form_data: OptionsFormData) -> dict[str, Any]:
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
        {'general': {'my_hidden': 'foo', 'my_repetition': [{'role': 'OPT_1', 'name': {'first_name': 'John'}}]}}
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

    if len(dictionary.keys()) > 0 and all(key.isnumeric() for key in dictionary):
        # Sort by key (i.e. the index) and put the sorted values into a list.
        return [value for key, value in sorted(dictionary.items(), key=operator.itemgetter(0))]

    return dictionary


def parse_form_data(form_data: OptionsFormData) -> dict[str, Any]:
    """Parses form data from a flat into a nested dictionary to be consumed by Pydantic.

    This function parses a dictionary, where the keys are the references to the Form Elements from the Options Form.
    The references are used to create a nested dictionary with the form data. Elements in the 'general' section are
    moved to the root of the dictionary.

    Args:
        form_data: The flat dictionary representing the form data.

    Returns:
        The nested form data.

    Examples:
        >>> parse_form_data({
        ...     "general[my_hidden]": "foo",
        ...     "general[my_repetition][1][role]": "OPT_1",
        ...     "general[my_repetition][1][name][first_name]": "John",
        ... })
        {'my_hidden': 'foo', 'my_repetition': [{'role': 'OPT_1', 'name': {'first_name': 'John'}}]}
    """
    unflattened_form_data = _unflatten(form_data)
    options = unflattened_form_data.get("general", {})
    for section_name, section in unflattened_form_data.items():
        if section_name != "general":
            options[section_name] = section
    return options


def _flatten_value(value: Any, prefix: str, result: dict[str, OptionsFormDataValue]) -> None:
    # group
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten_value(v, f"{prefix}[{k}]", result)

    # repetition
    elif isinstance(value, list) and len(value) > 0 and all(isinstance(item, dict) for item in value):
        for idx, v in enumerate(value, start=1):
            item_prefix = f"{prefix}[{idx}]"
            _flatten_value(v, item_prefix, result)

    else:
        result[prefix] = value


def flatten_form_data(form_data: dict[str, Any], section_names: Iterable[str]) -> OptionsFormData:
    """Flattens form data from a nested dictionary into a flat dictionary to be consumed by the frontend.

    This function flattens a nested dictionary into a flat dictionary, where the keys are references
    to the Form Elements in the Options Form. Top-level elements are put under the 'general' section,
    while elements under the given `section_names` are put under their respective sections.

    Args:
        form_data: The nested dictionary representing the form data.
        section_names: An iterable of section names that should be treated as sections and not put
                       under 'general'.

    Returns:
        The flat form data.

    Examples:
        >>> flatten_form_data(
        ...     {
        ...         "my_hidden": "foo",
        ...         "my_repetition": [{"input": "foo"}],
        ...     },
        ...     section_names=[],
        ... )
        {'general[my_hidden]': 'foo', 'general[my_repetition][1][input]': 'foo'}
    """
    result: dict[str, OptionsFormDataValue] = {}
    for key, value in form_data.items():
        _flatten_value(value, key if key in section_names else f"general[{key}]", result)
    return result
