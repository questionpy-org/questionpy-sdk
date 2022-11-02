from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Callable, Tuple, Type, Iterable, Any, get_origin, get_args, Literal, TYPE_CHECKING, Dict

from pydantic import BaseModel, Field
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from questionpy_common.elements import FormElement, FormSection, CheckboxGroupElement, GroupElement, \
    CanHaveConditions, OptionsFormDefinition


@dataclass
class _OptionInfo:
    label: str
    selected: bool


class OptionEnum(Enum):
    def __init__(self, option: _OptionInfo):
        super().__init__()
        self._value_ = self.name
        self.label = option.label
        self.selected = option.selected

    @classmethod
    def __get_validators__(cls) -> Iterable[Callable[[Any], "OptionEnum"]]:
        """This allows pydantic to convert a string to the enum member with that name."""

        def validate(value: Any) -> "OptionEnum":
            if isinstance(value, cls):
                return value

            if isinstance(value, str):
                try:
                    return cls[value]
                except KeyError as e:
                    raise ValueError(f"Not a valid {cls.__name__} value: '{value}'") from e

            raise TypeError(f"str or {cls.__name__} required, got '{value}'")

        yield validate


@dataclass
class _FieldInfo:
    build: Callable[[str], FormElement]
    """
    We want to use the name of the model field as the name of the form element, but that isn't known when the dsl
    functions are called. So they provide a callable instead which takes the name and returns the complete form element.
    """
    type: object
    """The type of the field."""
    default: object = ...
    """The default value of the field, with `...` meaning no default."""


@dataclass
class _StaticElementInfo:
    build: Callable[[str], FormElement]


@dataclass
class _SectionInfo:
    header: str
    model: Type["FormModel"]


def _flatten_elements(elements: Iterable[FormElement], sections: Iterable[FormSection] = ()) -> Iterable[FormElement]:
    for element in elements:
        yield element
        if isinstance(element, CheckboxGroupElement):
            yield from _flatten_elements(element.checkboxes)
        elif isinstance(element, GroupElement):
            yield from _flatten_elements(element.elements)

    for section in sections:
        yield from _flatten_elements(section.elements)


def _is_valid_annotation(annotation: object, expected: object) -> bool:
    """
    Checks if `annotation` is valid for a form element which produces values of type `expected`.
    """

    # TODO: pydantic is able to coerce many input values, such as strings to floats, so better logic may be
    #       needed here

    if annotation == expected or annotation is Any:
        return True

    expected_origin = get_origin(expected)
    expected_args = get_args(expected)

    annotation_origin = get_origin(annotation)
    annotation_args = get_args(annotation)

    if expected_origin is Literal and isinstance(annotation, type):
        # An annotation t and an expected type Literal[x] are valid if x is an instance of t
        # Example: bool and Literal[True]
        return isinstance(expected_args[0], annotation)

    if expected_origin and expected_origin is annotation_origin:
        # For an arbitrary generic G and an expected type G[x],
        # an annotation G[y] is valid if _is_valid_annotation(x, y) (recursively)
        return len(expected_args) == len(annotation_args) \
            and all(_is_valid_annotation(arg_a, arg_e) for arg_a, arg_e in zip(annotation_args, expected_args))

    return False


class _FormModelMeta(ModelMetaclass):
    # Gives false positives in metaclasses: https://github.com/PyCQA/pylint/issues/3268
    # pylint: disable=no-value-for-parameter

    if TYPE_CHECKING:
        # this is set by ModelMetaclass, but mypy doesn't know
        __fields__: Dict[str, ModelField]

    __slots__ = ()

    def __new__(mcs, name: str, bases: Tuple[type, ...], namespace: dict, **kwargs: object) -> "_FormModelMeta":
        annotations = namespace.get("__annotations__", {}).copy()
        new_namespace = {}

        for key, value in namespace.items():
            if isinstance(value, _FieldInfo):
                expected_type = value.type
                new_namespace[key] = Field(default=value.default, form_element=value.build(key))
            elif isinstance(value, _SectionInfo):
                expected_type = value.model
                new_namespace[key] = Field(form_section=value)
            elif isinstance(value, _StaticElementInfo):
                element = value.build(key)
                expected_type = type(element)
                new_namespace[key] = Field(default=element, const=True, form_element=element)
            else:
                # not one of our special types, use as is
                new_namespace[key] = value
                continue

            if key in annotations:
                # explicit type defined, check its validity
                if not _is_valid_annotation(annotations[key], expected_type):
                    raise TypeError(f"The element '{key}' produces values of type '{expected_type}', but is annotated "
                                    f"with '{annotations[key]}'")
            else:
                # no explicit type defined, set the default
                # this won't help type checkers or code completion, but will allow pydantic to validate inputs
                annotations[key] = expected_type

        new_namespace["__annotations__"] = annotations
        return super().__new__(mcs, name, bases, new_namespace, **kwargs)

    def __init__(cls, name: str, bases: Tuple[type, ...], namespace: dict, **kwargs: object):
        super().__init__(name, bases, namespace, **kwargs)
        cls._validate_conditions()

    def _validate_conditions(cls) -> None:
        elements = list(_flatten_elements(cls.form_elements(), cls.form_sections()))
        # mypy doesn't narrow the type after hasattr, hence the false positive
        names = {element.name for element in elements if hasattr(element, "name")}  # type: ignore[union-attr]

        for element in elements:
            if not isinstance(element, CanHaveConditions):
                continue

            for condition in chain(element.disable_if, element.hide_if):
                if condition.name not in names:
                    raise ValueError(f"Element '{element}' has a condition of kind '{condition.kind}' which references "
                                     f"nonexistent element '{condition.name}'")

    def form_elements(cls) -> Iterable[FormElement]:
        for field in cls.__fields__.values():
            if "form_element" in field.field_info.extra:
                yield field.field_info.extra["form_element"]

    def form_sections(cls) -> Iterable[FormSection]:
        for field in cls.__fields__.values():
            if "form_section" in field.field_info.extra:
                info: _SectionInfo = field.field_info.extra["form_section"]
                yield FormSection(header=info.header, elements=list(info.model.form_elements()))

    def form(cls) -> OptionsFormDefinition:
        return OptionsFormDefinition(
            general=list(cls.form_elements()),
            sections=list(cls.form_sections())
        )


class FormModel(BaseModel, metaclass=_FormModelMeta):
    __slots__ = ()
