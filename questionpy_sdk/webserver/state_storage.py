#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from pathlib import Path
from typing import Any

from questionpy_server.worker.runtime.package_location import PackageLocation


def _unflatten(flat_form_data: dict[str, str]) -> dict[str, Any]:
    """Splits the keys of a dictionary to form a new nested dictionary.

    Each key of the input dictionary is a reference string of a FormElements from the Options Form.
    These strings are split to create a nested dictionary, where each key is one part of the reference.
    Additionally: Dictionaries with only numerical keys (Repetition Elements) are replaced by lists.

    Example:
        This::

            {
                'general[my_hidden]': 'foo',
                'general[my_repetition][1][role]': 'OPT_1',
                'general[my_repetition][1][name][first_name]': 'John '
            }
        becomes::

            {
                "my_hidden": "foo",
                "my_repetition": [{"name": {"first_name": "John "}, "role": "OPT_1"}],
            }
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
        return [value for key, value in sorted(dictionary.items(), key=lambda item: item[0])]

    return dictionary


def parse_form_data(form_data: dict) -> dict:
    """Form data from a flat dictionary is parsed into a nested dictionary.

    This function parses a dictionary, where the keys are the references to the Form Element from the Options Form.
    The references are used to create a nested dictionary with the form data. Elements in the 'general' section are
    moved to the root of the dictionary.

    Example:
        This::

            {
                'general[my_hidden]': 'foo',\n
                'general[my_repetition][1][role]': 'OPT_1',\n
                'general[my_repetition][1][name][first_name]': 'John '
            }
        becomes::

            {
                'my_hidden': 'foo',\n
                'my_repetition': [{'name': {'first_name': 'John '}, 'role': 'OPT_1'}]
            }
    """
    unflattened_form_data = _unflatten(form_data)
    options = unflattened_form_data.get("general", {})
    for section_name, section in unflattened_form_data.items():
        if section_name != "general":
            options[section_name] = section
    return options


def add_repetition(form_data: dict[str, Any], reference: list, increment: int) -> dict[str, Any]:
    """Adds repetitions of the referenced RepetitionElement to the form_data.

    Args:
        form_data: Current form data to which new repetitions should be added.
        reference: Reference (list of names forming a path into `form_data`) of the repetition.
        increment: Number of new repetitions to add.

    Returns:
        `form_data` modified in-place.
    """
    current_element = form_data

    if ref := reference.pop(0) != "general":
        current_element = current_element[ref]
    while reference:
        ref = reference.pop(0)
        current_element = current_element[ref]

    if not isinstance(current_element, list):
        return form_data

    # Add "increment" number of repetitions.
    for _ in range(increment):
        current_element.append(current_element[-1])

    return form_data


class QuestionStateStorage:
    def __init__(self, storage_path: Path) -> None:
        # Mapping of package path to question state path
        self.paths: dict[str, Path] = {}
        self.storage_path = storage_path

    def insert(self, key: PackageLocation, question_state: dict) -> None:
        path = self._state_path_for_package(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.paths[str(key)] = path
        with path.open("w") as file:
            json.dump(question_state, file, indent=2)

    def get(self, key: PackageLocation) -> dict | None:
        if str(key) in self.paths:
            path = self.paths.get(str(key))
            if path and path.exists():
                return json.loads(path.read_text())
        path = self._state_path_for_package(key)
        if not path.exists():
            return None
        self.paths[str(key)] = path
        return json.loads(path.read_text())

    def _state_path_for_package(self, package_location: PackageLocation) -> Path:
        filename = str(package_location) + ".json"
        return self.storage_path / filename
