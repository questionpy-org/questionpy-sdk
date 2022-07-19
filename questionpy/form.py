from abc import ABC, abstractmethod
from typing import Annotated, List, Literal, Union, Any, Tuple, Optional, Set

from pydantic import BaseModel, Field


class _BaseElement(BaseModel):
    kind: str
    label: str


class Submittable(BaseModel, ABC):
    name: str

    @abstractmethod
    def to_model_field(self) -> Tuple[Any, Any]:
        """
        Returns the (type, default value) tuple as used by :meth:`create_model` for this form element.
        """


class TextElement(_BaseElement):
    kind: Literal["text"] = "text"
    text: str


class TextInputElement(_BaseElement, Submittable):
    kind: Literal["input"] = "input"
    required: bool = False

    def to_model_field(self) -> Tuple[Any, Any]:
        return (str, ...) if self.required else (Optional[str], None)


class ButtonElement(_BaseElement):
    kind: Literal["button"] = "button"


class CheckboxElement(_BaseElement, Submittable):
    kind: Literal["checkbox"] = "checkbox"
    required: bool = False

    def to_model_field(self) -> Tuple[Any, Any]:
        return (Literal[True], ...) if self.required else (bool, False)


class CheckboxGroupElement(BaseModel):
    kind: Literal["checkbox_group"] = "checkbox_group"
    checkboxes: List[CheckboxElement]


class RadioGroupElement(_BaseElement, Submittable):
    class Option(BaseModel):
        label: str
        value: str

    kind: Literal["radio_group"] = "radio_group"
    buttons: List[Option]
    required: bool = False

    def to_model_field(self) -> Tuple[Any, Any]:
        option_types = tuple(Literal[option.value] for option in self.buttons)
        if self.required:
            return Union[option_types], ...
        return Optional[Union[option_types]], None


class SelectElement(_BaseElement, Submittable):
    class Option(BaseModel):
        label: str
        value: str
        selected: bool = False

    kind: Literal["select"] = "select"
    multiple: bool = False
    options: List[Option]
    required: bool = False

    def to_model_field(self) -> Tuple[Any, Any]:
        option_types = tuple(Literal[option.value] for option in self.options)
        if self.multiple:
            if self.required:
                return Set[Union[option_types]], ...  # type: ignore[valid-type]
            return Set[Union[option_types]], None  # type: ignore[valid-type]

        if self.required:
            return Union[option_types], ...
        return Optional[Union[option_types]], None


class HiddenElement(Submittable):
    kind: Literal["hidden"] = "hidden"
    value: str

    def to_model_field(self) -> Tuple[Any, Any]:
        return Literal[self.value], ...


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
