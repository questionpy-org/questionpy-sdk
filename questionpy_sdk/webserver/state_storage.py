#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from pathlib import Path
from typing import Optional, Any, Union


def _unflatten(flat_form_data: dict[str, str]) -> dict[str, Any]:
    unflattened_dict: dict[str, Any] = {}
    for key, value in flat_form_data.items():
        keys = key.replace(']', '').split('[')[:-1]
        current_dict = unflattened_dict
        for k in keys:
            if k not in current_dict:
                current_dict[k] = {}
            current_dict = current_dict[k]
        current_dict[key.split('[')[-1][:-1]] = value

    result = _convert_repetition_dict_to_list(unflattened_dict)
    if isinstance(result, dict):
        return result
    else:
        raise ValueError("The result is not a dictionary.")


def _convert_repetition_dict_to_list(dictionary: dict[str, Any]) -> Union[dict[str, Any], list[Any]]:
    if not isinstance(dictionary, dict):
        return dictionary

    if all(key.isnumeric() for key in dictionary.keys()):
        return list(dictionary.values())

    for key, value in dictionary.items():
        dictionary[key] = _convert_repetition_dict_to_list(value)

    return dictionary


def parse_form_data(form_data: dict) -> dict:
    unflattened_form_data = _unflatten(form_data)
    options = unflattened_form_data['general']
    for section_name, section in unflattened_form_data.items():
        if not section_name == 'general':
            options[section_name] = section
    return options


def add_repetition(form_data: dict[str, Any], reference: list, increment: int) -> dict[str, Any]:
    """Adds repetitions of the referenced RepetitionElement to the form_data."""
    current_element = form_data

    if ref := reference.pop(0) != 'general':
        current_element = current_element[ref]
    while reference:
        ref = reference.pop(0)
        current_element = current_element[ref]

    if not isinstance(current_element, list):
        return form_data

    # Add "increment" number of repetitions.
    for i in range(increment):
        current_element.append(current_element[-1])

    return form_data


class QuestionStateStorage:

    def __init__(self) -> None:
        # Mapping of package path to question state path
        self.paths: dict[Path, Path] = {}
        self.storage_path: Path = Path(__file__).parent / 'question_state_storage'

    def insert(self, key: Path, question_state: dict) -> None:
        path = self.storage_path / key.with_suffix('.json')
        self.paths[key] = path
        with path.open('w') as file:
            json.dump(question_state, file)

    def get(self, key: Path) -> Optional[dict]:
        if key in self.paths:
            path = self.paths.get(key)
            if path and path.exists():
                return json.loads(path.read_text())
        path = self.storage_path / key.with_suffix('.json')
        if not path.exists():
            return None
        self.paths[key] = path
        return json.loads(path.read_text())