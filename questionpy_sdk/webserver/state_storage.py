import json
from pathlib import Path
from typing import Optional, Union, List

from questionpy_common.elements import StaticTextElement, TextInputElement, CheckboxElement, \
    RadioGroupElement, SelectElement, HiddenElement, GroupElement, OptionsFormDefinition, FormElement, RepetitionElement


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
        path = self.paths.get(key)
        if not path or not path.exists():
            return None
        return json.loads(path.read_text())

    def parse_form_data(self, form_definition: OptionsFormDefinition, form_data: dict) -> dict:
        options = self._parse_section(form_definition.general, form_data)
        return options

    def _parse_section(self, section: List[FormElement], form_data: dict) -> dict:
        options = {}
        for form_element in section:
            if not isinstance(form_element, StaticTextElement):
                options[form_element.name] = self._parse_form_element(form_element, form_data)
        return options

    def _parse_form_element(self, form_element: FormElement, form_data: dict) \
            -> Union[str, int, list, dict, FormElement]:
        if isinstance(form_element, SelectElement):
            if form_element.name not in form_data or form_data[form_element.name] == '':
                return [form_element.options[0].value]
            return [form_data[form_element.name]]
        elif isinstance(form_element, GroupElement):
            group = {}
            for child in form_element.elements:
                if not isinstance(child, StaticTextElement):
                    group[child.name] = self._parse_form_element(child, form_data)
            return group
        elif isinstance(form_element, RepetitionElement):
            # TODO: RepetitionElement -> next PR
            return ''
        elif isinstance(form_element, HiddenElement):
            return form_data[form_element.name] if form_element.name in form_data else ''
        elif isinstance(form_element, TextInputElement):
            return form_data[form_element.name] if form_element.name in form_data else ''
        elif isinstance(form_element, CheckboxElement):
            return form_data[form_element.name] if form_element.name in form_data else 0
        elif isinstance(form_element, RadioGroupElement):
            return form_data[form_element.name] if form_element.name in form_data else form_element.options[0].value
        else:
            return ""
