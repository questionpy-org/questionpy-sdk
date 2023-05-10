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
        options = {}
        unflattened_form_data = _unflatten(form_data)
        options['general'] = self._parse_section(form_definition.general, unflattened_form_data['general'])
        for section in form_definition.sections:
            options[section.name] = self._parse_section(section.elements, unflattened_form_data[section.name])
        return options

    def _parse_section(self, section: List[FormElement], section_form_data: dict) -> dict:
        options = {}
        for form_element in section:
            if not isinstance(form_element, StaticTextElement) \
                    and (form_element.name in section_form_data or isinstance(form_element, GroupElement)):
                options[form_element.name] = self._parse_form_element(form_element, section_form_data)
        return options

    def _parse_form_element(self, form_element: FormElement, form_data: dict) \
            -> Union[str, int, list, dict, FormElement]:
        if isinstance(form_element, SelectElement):
            if form_element.multiple:
                return [form_data[form_element.name]]
            return form_data[form_element.name]
        elif isinstance(form_element, GroupElement):
            group = {}
            for child in form_element.elements:
                if not isinstance(child, StaticTextElement) and child.name in form_data:
                    group[child.name] = self._parse_form_element(child, form_data)
            return group
        elif isinstance(form_element, RepetitionElement):
            repetition = {}
            for key, value in form_data[form_element.name].items():
                repetition[key] = self._parse_section(form_element.elements, value)
            return repetition
        else:
            return form_data[form_element.name]
