from dataclasses import dataclass
from enum import Enum
from typing import Callable, Tuple, Type, Iterable, Any, get_origin, get_args, Literal, TYPE_CHECKING, Dict

from pydantic import BaseModel, Field
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from questionpy_common.elements import FormElement, FormSection, OptionsFormDefinition


@dataclass
class _OptionInfo:
    label: str
    selected: bool


class OptionEnum(str, Enum):
    """Enum specifying the possible options for radio groups and drop-downs.

    Specify options using `option`.
    """

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
    """We want to use the name of the model field as the name of the form element, but that isn't known when the dsl
    functions are called. So they provide a callable instead that takes the name and returns the complete form element.
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


def _is_valid_annotation(annotation: object, expected: object) -> bool:
    """Checks if `annotation` is valid for a form element that produces values of type `expected`."""

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

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict, **kwargs: object) -> "_FormModelMeta":
        annotations = namespace.get("__annotations__", {}).copy()
        new_namespace = {}

        for key, value in namespace.items():
            if isinstance(value, _FieldInfo):
                expected_type = value.type
                new_namespace[key] = Field(default=value.default, form_element=value.build(key))
            elif isinstance(value, _SectionInfo):
                section = FormSection(name=key, header=value.header, elements=value.model.qpy_form.general)
                expected_type = value.model
                new_namespace[key] = Field(form_section=section)
            elif isinstance(value, _StaticElementInfo):
                element = value.build(key)
                expected_type = type(element)
                new_namespace[key] = Field(default=element, const=True, form_element=element, exclude=True)
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

    def __init__(cls, name: str, bases: Tuple[type, ...], namespace: dict):
        super().__init__(name, bases, namespace)

        cls.qpy_form = OptionsFormDefinition(
            general=[field.field_info.extra["form_element"] for field in cls.__fields__.values()
                     if "form_element" in field.field_info.extra],
            sections=[field.field_info.extra["form_section"] for field in cls.__fields__.values()
                      if "form_section" in field.field_info.extra]
        )
        """The form defined by this declarative model."""


class FormModel(BaseModel, metaclass=_FormModelMeta):
    """Declarative form definition.

    Use the DSL functions to define your elements as fields, and have submitted form data automatically validated into a
    type-safe instance of your model.
    """
    __slots__ = ()
