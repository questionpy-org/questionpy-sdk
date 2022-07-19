from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field


class _BaseElement(BaseModel):
    kind: str
    name: str
    label: str


class TextElement(_BaseElement):
    kind: Literal["text"] = "text"
    text: str


class TextInputElement(_BaseElement):
    kind: Literal["input"] = "input"


class ButtonElement(_BaseElement):
    kind: Literal["button"] = "button"


class CheckboxElement(_BaseElement):
    kind: Literal["checkbox"] = "checkbox"


class CheckboxGroupElement(BaseModel):
    kind: Literal["checkbox_group"] = "checkbox_group"
    checkboxes: List[CheckboxElement]


class RadioGroupElement(_BaseElement):
    class Option(BaseModel):
        label: str
        value: str

    kind: Literal["radio_group"] = "radio_group"
    buttons: List[Option]


class SelectElement(_BaseElement):
    class Option(BaseModel):
        label: str
        value: str
        selected: bool = False

    kind: Literal["select"] = "select"
    multiple: bool = False
    options: List[Option]


class HiddenElement(BaseModel):
    kind: Literal["hidden"] = "hidden"
    name: str
    value: str


FormElement = Annotated[
    Union[
        TextElement, TextInputElement, ButtonElement, CheckboxElement, CheckboxGroupElement,
        RadioGroupElement, SelectElement, HiddenElement
    ],
    Field(discriminator="kind")
]


class FormSection(BaseModel):
    header: str
    elements: List[FormElement] = []


class Form(BaseModel):
    general: List[FormElement] = []
    sections: List[FormSection] = []
