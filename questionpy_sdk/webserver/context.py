#  This file is part of QuestionPy. (https://questionpy.org)
#  QuestionPy is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import List, Any, Optional, Dict

from questionpy_common.elements import StaticTextElement, CheckboxElement, TextInputElement, FormElement, \
    GroupElement, RepetitionElement, OptionsFormDefinition, CheckboxGroupElement, RadioGroupElement, SelectElement, \
    HiddenElement

from questionpy_sdk.webserver.elements import CxdOptionsFormDefinition, CxdFormSection, CxdFormElement, \
    CxdGroupElement, CxdRepetitionElement, CxdStaticTextElement, CxdTextInputElement, \
    CxdCheckboxElement, CxdCheckboxGroupElement, CxdRadioGroupElement, CxdSelectElement, CxdHiddenElement

element_mapping: Dict[type, type] = {
    StaticTextElement: CxdStaticTextElement,
    TextInputElement: CxdTextInputElement,
    CheckboxElement: CxdCheckboxElement,
    CheckboxGroupElement: CxdCheckboxGroupElement,
    RadioGroupElement: CxdRadioGroupElement,
    SelectElement: CxdSelectElement,
    HiddenElement: CxdHiddenElement
}


def _contextualize_element(element: FormElement, form_data: Optional[dict[str, Any]], path: List[str],
                           context: Optional[dict[str, object]] = None) -> CxdFormElement:
    path.append(element.name)
    element_form_data = None
    if form_data:
        element_form_data = form_data.get(element.name)

    if isinstance(element, GroupElement):
        cxd_gr_element = CxdGroupElement(path=path.copy(), **element.model_dump(exclude={'elements'}))
        cxd_gr_element.cxd_elements = _contextualize_element_list(element.elements, element_form_data, path, context)
        path.pop()
        return cxd_gr_element

    if isinstance(element, RepetitionElement):
        cxd_rep_element = CxdRepetitionElement(path=path.copy(), **element.model_dump(exclude={'elements'}))
        if not element_form_data:
            for i in range(1, element.initial_repetitions + 1):
                path.append(str(i))
                element_list = _contextualize_element_list(element.elements, None, path, {'repno': i})
                cxd_rep_element.cxd_elements.append(element_list)
                path.pop()
            path.pop()
            return cxd_rep_element
        for i, repetition in enumerate(element_form_data, 1):
            path.append(str(i))
            element_list = _contextualize_element_list(element.elements, repetition, path, {'repno': i})
            cxd_rep_element.cxd_elements.append(element_list)
            path.pop()
        path.pop()
        return cxd_rep_element

    if type(element) not in element_mapping:
        raise ValueError(f"No corresponding CxdFormElement found for {element.__class__}")

    cxd_element_class = element_mapping[element.__class__]
    cxd_element = cxd_element_class(**element.model_dump(), path=path)
    if context:
        cxd_element.contextualize(r'\{\s?qpy:repno\s?\}', str(context.get('repno')))
    cxd_element.add_form_data_value(element_form_data)

    path.pop()
    return cxd_element


def _contextualize_element_list(element_list: List[FormElement], form_data: Optional[dict[str, Any]],
                                path: list[str], context: Optional[dict[str, object]] = None) -> List[CxdFormElement]:
    cxd_element_list: List[CxdFormElement] = []
    for element in element_list:
        cxd_element = _contextualize_element(element, form_data, path, context)
        cxd_element_list.append(cxd_element)
    return cxd_element_list


def contextualize(form_definition: OptionsFormDefinition, form_data: Optional[dict[str, Any]]) \
        -> CxdOptionsFormDefinition:
    path: list[str] = ['general']
    cxd_options_form = CxdOptionsFormDefinition()
    cxd_options_form.general = _contextualize_element_list(form_definition.general, form_data, path)
    for section in form_definition.sections:
        path = [section.name]
        cxd_section = CxdFormSection(name=section.name, header=section.header)
        section_data = None
        if form_data:
            section_data = form_data.get(section.name)
        cxd_section.cxd_elements = _contextualize_element_list(section.elements, section_data, path)
        cxd_options_form.sections.append(cxd_section)
    return cxd_options_form
