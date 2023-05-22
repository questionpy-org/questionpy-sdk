from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Callable, Tuple, Type, Iterable, Any, get_origin, get_args, Literal, TYPE_CHECKING, Dict, \
    Optional, cast

from pydantic import BaseModel, Field
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from questionpy_common.elements import FormElement, FormSection, OptionsFormDefinition


@dataclass
class _OptionInfo:
    label: str
    selected: bool
    value: Optional[str] = None
    """Set by :meth:`_OptionEnumMeta.__new__` because __set_name__ doesn't get called for enum members."""


class _OptionEnumMeta(EnumMeta):
    """
    This metaclass is necessary in order to make :class:`OptionEnum`\\ s subclasses of str without losing the ``label``
    and ``selected`` attributes. Making them subclasses of str means they will be serialized to their value without any
    custom json encoders.
    """

    def __new__(mcs, cls_name: str, bases: tuple[type, ...], namespace: dict, **kwargs: object) -> "_OptionEnumMeta":
        for key, member in namespace.items():
            if not (key.startswith("_") and key.endswith("_")):
                if not isinstance(member, _OptionInfo):
                    raise TypeError("Please use option(label, selected) to create OptionEnum members")

                member.value = key

        return super().__new__(mcs, cls_name, bases, cast(Any, namespace), **kwargs)


class OptionEnum(str, Enum, metaclass=_OptionEnumMeta):
    """Enum specifying the possible options for radio groups and drop-downs.

    Specify options using `option`.

    Implementation Note:
        When serialized by ``json.dump(s)`` or Pydantic's ``.json()``, we want :class:`OptionEnum` members to produce
        their value as a string. Pydantic supports this with some drawbacks using ``json_encoders``, but
        ``json.dump(s)`` does not. Instead, we make :class:`OptionEnum` a subclass of ``str``, so it is automatically
        serialized as a string.

        >>> from questionpy.form import option
        >>> class MyEnum(OptionEnum):
        ...     OPT_1 = option("Some Label")
        >>> isinstance(MyEnum.OPT_1, str)
        True
        >>> MyEnum.OPT_1 == "OPT_1"
        True

        Here, Python will pass the :class:`_OptionInfo` returned by :func:`option` to :meth:`OptionEnum.__new__`.
        However, :class:`_OptionInfo` does not contain the name of the enum member, which we want the str value to be.
        Apart from passing `"OPT_1"` again to :func:`option`, the solution to this is a custom metaclass extending
        :class:`EnumMeta`. The metaclass adds the member name to the :class:`_OptionInfo`, allowing
        :meth:`OptionEnum.__new__` to use it as the string value (by passing it to :meth:`str.__new__`).

        :meth:`OptionEnum.__init__` then sets the ``label`` and ``selected`` flag on the enum member.

        >>> MyEnum.OPT_1.label
        'Some Label'
        >>> MyEnum.OPT_1.selected
        False
    """

    def __new__(cls, option: _OptionInfo) -> "OptionEnum":
        return super().__new__(cls, option.value)

    def __init__(self, option: _OptionInfo) -> None:
        super().__init__()
        self._value_ = option.value
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
