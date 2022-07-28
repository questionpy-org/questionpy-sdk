from typing import Callable, Generic, TypeVar

from pydantic import BaseModel, Field

from questionpy.form import Submittable, TextInputElement

T = TypeVar("T", bound=Submittable)


class _FieldBuilder(Generic[T]):
    def __init__(self, factory: Callable[[str], T]):
        self.build = factory


class _FormModelMeta(type(BaseModel), type):
    def __new__(mcs, name: str, bases, namespace: dict, **kwargs):
        for key, value in namespace.items():
            if isinstance(value, Submittable):
                namespace[key] = Field(default=value.to_model_field()[1], form_element=value)
            elif isinstance(value, _FieldBuilder):
                element = value.build(key)
                namespace[key] = Field(default=element.to_model_field()[1], form_element=element)
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class FormModel(BaseModel, metaclass=_FormModelMeta):
    pass


def text_input(label: str, required: bool = False) -> _FieldBuilder[TextInputElement]:
    return _FieldBuilder(lambda name: TextInputElement(name=name, label=label, required=required))
