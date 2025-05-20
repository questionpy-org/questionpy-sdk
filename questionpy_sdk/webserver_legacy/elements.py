#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from re import Pattern, sub
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from questionpy_common.elements import (
    CheckboxElement,
    FormElement,  # noqa: F401
    FormSection,
    GeneratedIdElement,
    GroupElement,
    HiddenElement,
    Option,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
)


class _CxdFormElement(BaseModel):
    path: list[str]

    @computed_field
    def id(self) -> str:
        return "_".join(self.path)

    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        """Replaces patterns in model fields.

        QuestionPy form elements can contain a pattern in their model fields which is replaced with a value when the
        OptionsForm is presented to add additional context for the user. Replaces the QPy pattern with the replacement
        string in model fields which can contain such a pattern.

        Args:
            pattern: The QPy Pattern to be replaced. A valid QPy Pattern matches `{qpy:<identifier>}` e.g. `{qpy:repno}`
            replacement: The replacement string
        Returns:
            None
        """

    def add_form_data_value(self, element_form_data: Any) -> None:
        """If there is prior form data available, this it is used to set the `CxdFormElement` value or `selected` state.

        Args:
            element_form_data: Any form data fitting this `CxdFormElement`

        Returns:
            None
        """


class CxdTextInputElement(TextInputElement, _CxdFormElement):
    value: str | None = None

    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))
        if self.default:
            self.default = sub(pattern, replacement, str(self.default))
        if self.placeholder:
            self.placeholder = sub(pattern, replacement, str(self.placeholder))

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.value = element_form_data


class CxdTextAreaElement(TextAreaElement, _CxdFormElement):
    value: str | None = None

    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))
        if self.default:
            self.default = sub(pattern, replacement, str(self.default))
        if self.placeholder:
            self.placeholder = sub(pattern, replacement, str(self.placeholder))

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.value = element_form_data


class CxdStaticTextElement(StaticTextElement, _CxdFormElement):
    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))
        self.text = sub(pattern, replacement, str(self.text))


class CxdCheckboxElement(CheckboxElement, _CxdFormElement):
    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        if self.left_label:
            self.left_label = sub(pattern, replacement, str(self.left_label))
        if self.right_label:
            self.right_label = sub(pattern, replacement, str(self.right_label))

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.selected = element_form_data


class CxdOption(Option, _CxdFormElement):
    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))


class CxdRadioGroupElement(RadioGroupElement, _CxdFormElement):
    cxd_options: list[CxdOption] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        for option in self.options:
            path = data.get("path")
            if not isinstance(path, list):
                msg = f"Path should be of type list but is {type(path)}"
                raise TypeError(msg)
            path.append(option.value)
            self.cxd_options.append(CxdOption(**option.model_dump(), path=path))
            path.pop()
        self.options = []

    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))
        for cxd_option in self.cxd_options:
            cxd_option.contextualize(pattern, replacement)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if not element_form_data:
            return

        for option in self.cxd_options:
            option.selected = option.value == element_form_data


class CxdSelectElement(SelectElement, _CxdFormElement):
    cxd_options: list[CxdOption] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        for option in self.options:
            path = data.get("path")
            if not isinstance(path, list):
                msg = f"Path should be of type list but is {type(path)}"
                raise TypeError(msg)
            path.append(option.value)
            self.cxd_options.append(CxdOption(**option.model_dump(), path=path))
            path.pop()
        self.options = []

    def contextualize(self, pattern: Pattern[str], replacement: str) -> None:
        self.label = sub(pattern, replacement, str(self.label))
        for cxd_option in self.cxd_options:
            cxd_option.contextualize(pattern, replacement)

    def add_form_data_value(self, element_form_data: Any) -> None:
        if not element_form_data:
            return

        for option in self.cxd_options:
            option.selected = option.value in element_form_data


class CxdHiddenElement(HiddenElement, _CxdFormElement):
    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.value = element_form_data


class CxdGroupElement(GroupElement, _CxdFormElement):
    cxd_elements: list["CxdFormElement"] = []

    def __init__(self, **data: Any):
        super().__init__(**data, elements=[])


class CxdRepetitionElement(RepetitionElement, _CxdFormElement):
    cxd_elements: list[list["CxdFormElement"]] = []

    def __init__(self, **data: Any):
        super().__init__(**data, elements=[])


class CxdGeneratedIdElement(GeneratedIdElement, _CxdFormElement):
    cxd_value: str | None = None

    def add_form_data_value(self, element_form_data: Any) -> None:
        if element_form_data:
            self.cxd_value = element_form_data
        else:
            self.cxd_value = str(uuid4())


type CxdFormElement = Annotated[
    CxdStaticTextElement
    | CxdTextInputElement
    | CxdTextAreaElement
    | CxdCheckboxElement
    | CxdRadioGroupElement
    | CxdSelectElement
    | CxdHiddenElement
    | CxdGroupElement
    | CxdRepetitionElement
    | CxdGeneratedIdElement,
    Field(discriminator="kind"),
]


class CxdFormSection(FormSection):
    cxd_elements: list[CxdFormElement] = []
    """Elements contained in the section."""


class CxdOptionsFormDefinition(BaseModel):
    general: list[CxdFormElement] = []
    """Elements to add to the main section, after the LMS' own elements."""
    sections: list[CxdFormSection] = []
    """Sections to add after the main section."""
