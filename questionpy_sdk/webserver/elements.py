#  This file is part of QuestionPy. (https://questionpy.org)
#  QuestionPy is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import re
from typing import List, Union, Annotated, Any, Optional
from typing_extensions import TypeAlias
from pydantic import Field, BaseModel

from questionpy_common.elements import StaticTextElement, GroupElement, HiddenElement, RepetitionElement, \
    SelectElement, RadioGroupElement, Option, CheckboxGroupElement, CheckboxElement, TextInputElement, FormSection
# pylint: disable=unused-import
from questionpy_common.elements import FormElement  # noqa: F401


class _CxdFormElement(BaseModel):
    path: list[str]
    id: str = ''

    def contextualize(self, text: str) -> None:
        pass

    def add_form_data_value(self, element_form_data: Any) -> None:
        pass


class CxdTextInputElement(TextInputElement, _CxdFormElement):
    value: Optional[str] = None

    def contextualize(self, text: str) -> None:
        self.label = re.sub(r'\{ qpy:repno }', f'{text}', self.label)
        self.default = re.sub(r'\{ qpy:repno }', f'{text}', self.default)
        self.placeholder = re.sub(r'\{ qpy:repno }', f'{text}', self.placeholder)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.value = element_form_data


class CxdStaticTextElement(StaticTextElement, _CxdFormElement):

    def contextualize(self, text: str) -> None:
        self.label = re.sub(r'\{ qpy:repno }', f'{text}', self.label)
        self.text = re.sub(r'\{ qpy:repno }', f'{text}', self.text)


class CxdCheckboxElement(CheckboxElement, _CxdFormElement):
    def contextualize(self, text: str) -> None:
        self.left_label = re.sub(r'\{ qpy:repno }', f'{text}', self.left_label)
        self.right_label = re.sub(r'\{ qpy:repno }', f'{text}', self.right_label)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.selected = element_form_data


class CxdCheckboxGroupElement(CheckboxGroupElement, _CxdFormElement):
    cxd_checkboxes: List[CxdCheckboxElement] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        for checkbox in self.checkboxes:
            path = data.get('path')
            if not isinstance(path, list):
                raise TypeError(f"Path should be of type list but is {type(path)}")
            path.append(checkbox.name)
            self.cxd_checkboxes.append(CxdCheckboxElement(**checkbox.model_dump(), path=path))
            path.pop()
        self.checkboxes = []

    def contextualize(self, text: str) -> None:
        for cxd_checkbox in self.cxd_checkboxes:
            cxd_checkbox.contextualize(text)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if not element_form_data:
            return
        selected_checkboxes = [chk for chk in self.cxd_checkboxes if chk.name in element_form_data]

        for checkbox in self.cxd_checkboxes:
            checkbox.selected = checkbox in selected_checkboxes


class CxdOption(Option, _CxdFormElement):
    def contextualize(self, text: str) -> None:
        self.label = re.sub(r'\{ qpy:repno }', f'{text}', self.label)


class CxdRadioGroupElement(RadioGroupElement, _CxdFormElement):
    cxd_options: List[CxdOption] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        for option in self.options:
            path = data.get('path')
            if not isinstance(path, list):
                raise TypeError(f"Path should be of type list but is {type(path)}")
            path.append(option.value)
            self.cxd_options.append(CxdOption(**option.model_dump(), path=path))
            path.pop()
        self.options = []

    def contextualize(self, text: str) -> None:
        self.label = re.sub(r'\{ qpy:repno }', f'{text}', self.label)
        for cxd_option in self.cxd_options:
            cxd_option.contextualize(text)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if not element_form_data:
            return

        for option in self.cxd_options:
            option.selected = option.value == element_form_data


class CxdSelectElement(SelectElement, _CxdFormElement):
    cxd_options: List[CxdOption] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        for option in self.options:
            path = data.get('path')
            if not isinstance(path, list):
                raise TypeError(f"Path should be of type list but is {type(path)}")
            path.append(option.value)
            self.cxd_options.append(CxdOption(**option.model_dump(), path=path))
            path.pop()
        self.options = []

    def contextualize(self, text: str) -> None:
        self.label = re.sub(r'\{ qpy:repno }', f'{text}', self.label)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if not element_form_data:
            return
        selected_options = [opt for opt in self.cxd_options if opt.value in element_form_data]

        for option in self.cxd_options:
            option.selected = option in selected_options


class CxdHiddenElement(HiddenElement, _CxdFormElement):
    def contextualize(self, text: str) -> None:
        pass

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.value = element_form_data


class CxdGroupElement(GroupElement, _CxdFormElement):
    cxd_elements: List["CxdFormElement"] = []

    def __init__(self, **data: Any):
        super().__init__(**data, elements=[])


class CxdRepetitionElement(RepetitionElement, _CxdFormElement):
    cxd_elements: list[list["CxdFormElement"]] = []

    def __init__(self, **data: Any):
        super().__init__(**data, elements=[])


CxdFormElement: TypeAlias = Annotated[Union[
    CxdStaticTextElement, CxdTextInputElement, CxdCheckboxElement, CxdCheckboxGroupElement,
    CxdRadioGroupElement, CxdSelectElement, CxdHiddenElement, CxdGroupElement, CxdRepetitionElement
], Field(discriminator="kind")]


class CxdFormSection(FormSection):
    cxd_elements: List[CxdFormElement] = []
    """Elements contained in the section."""


class CxdOptionsFormDefinition(BaseModel):
    general: List[CxdFormElement] = []
    """Elements to add to the main section, after the LMS' own elements."""
    sections: List[CxdFormSection] = []
    """Sections to add after the main section."""
