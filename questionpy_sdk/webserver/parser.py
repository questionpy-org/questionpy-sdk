import json
from typing import List, Dict, Any

from questionpy_common.elements import OptionsFormDefinition, FormElement


def to_dict(form_definition: OptionsFormDefinition) -> dict:
    return {
        'general': section_to_dict(form_definition.general),
        'sections': {section.header: section_to_dict(section.elements) for section in form_definition.sections}
    }


def section_to_dict(section: List[FormElement]) -> List[Dict[str, Any]]:
    result = []
    for element in section:
        result.append(element.dict())
        if hasattr(element, 'hide_if'):
            result[-1]['hide_if'] = json.dumps(result[-1]['hide_if'])
        if hasattr(element, 'disable_if'):
            result[-1]['disable_if'] = json.dumps(result[-1]['disable_if'])
    return result
