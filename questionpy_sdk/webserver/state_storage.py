#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import json
from pathlib import Path
from typing import Optional, Union, List, Any

from questionpy_common.elements import StaticTextElement, SelectElement, GroupElement, OptionsFormDefinition, \
    FormElement, RepetitionElement


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
    return unflattened_dict


def add_repetition(form_data: dict[str, Any], form_definition: OptionsFormDefinition, reference: list) \
        -> dict[str, Any]:
    """Adds repetitions of the referenced RepetitionElement to the form_data."""
    # Find RepetitionElement in the FormDefinition.
    definition_element = form_definition.general
    form_data_element = form_data

    if ref := reference.pop(0) != 'general':
        section = next(filter(lambda s: s.name == ref, form_definition.sections))
        definition_element = section.elements
        form_data_element = form_data_element[section.name]
    while reference:
        ref = reference.pop(0)
        element = next(filter(lambda e: (e.name == ref), definition_element))
        if not (isinstance(element, GroupElement) or isinstance(element, RepetitionElement)):
            return form_data
        definition_element = element.elements
        form_data_element = form_data_element[ref]

    if not isinstance(element, RepetitionElement) or not isinstance(form_data_element, list):
        return form_data

    # Add "increment" number of repetitions.
    for i in range(element.increment):
        form_data_element.append(form_data_element[-1])

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

    def parse_form_data(self, form_definition: OptionsFormDefinition, form_data: dict) -> dict:
        unflattened_form_data = _unflatten(form_data)
        options = self._parse_section(form_definition.general, unflattened_form_data['general'])
        for section in form_definition.sections:
            options[section.name] = self._parse_section(section.elements, unflattened_form_data[section.name])
        return options

    def _parse_section(self, section: List[FormElement], section_form_data: dict) -> dict:
        options = {}
        for form_element in section:
            if not isinstance(form_element, StaticTextElement) \
                    and (form_element.name in section_form_data or isinstance(form_element, GroupElement)):
                parsed_element = self._parse_form_element(form_element, section_form_data)
                if parsed_element:
                    options[form_element.name] = parsed_element
        return options

    def _parse_form_element(self, form_element: FormElement, form_data: dict) \
            -> Optional[Union[str, int, list, dict, FormElement]]:
        if isinstance(form_element, SelectElement):
            return form_data[form_element.name]
        elif isinstance(form_element, GroupElement):
            if form_element.name not in form_data:
                return None
            group = {}
            for child in form_element.elements:
                if not isinstance(child, StaticTextElement) and child.name in form_data[form_element.name]:
                    group[child.name] = self._parse_form_element(child, form_data[form_element.name])
            return group
        elif isinstance(form_element, RepetitionElement):
            repetition = []
            for key, value in form_data[form_element.name].items():
                repetition.append(self._parse_section(form_element.elements, value))
            return repetition
        else:
            return form_data[form_element.name]
