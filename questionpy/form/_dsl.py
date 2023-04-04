from typing import cast, TypeVar, Any, overload, Literal, Optional, Set, Union, Type, Callable

from questionpy_common.conditions import Condition, IsChecked, IsNotChecked, Equals, DoesNotEqual, In
from questionpy_common.elements import TextInputElement, StaticTextElement, CheckboxElement, RadioGroupElement, \
    SelectElement, HiddenElement, GroupElement, Option, RepetitionElement
from typing_extensions import TypeAlias

from questionpy.form._model import FormModel, _FieldInfo, _SectionInfo, OptionEnum, _OptionInfo, _StaticElementInfo

__all__ = ["text_input", "static_text", "checkbox", "radio_group", "select", "option", "hidden", "section", "group",
           "repeat", "is_checked", "is_not_checked", "equals", "does_not_equal", "is_in"]

_S = TypeVar("_S", bound=str)
_F = TypeVar("_F", bound=FormModel)
_E = TypeVar("_E", bound=OptionEnum)

_OneOrMoreConditions: TypeAlias = Union[Condition, list[Condition]]
_ZeroOrMoreConditions: TypeAlias = Optional[_OneOrMoreConditions]


def _listify(value: _ZeroOrMoreConditions) -> list[Condition]:
    if value is None:
        return []
    if isinstance(value, Condition):
        return [value]
    return value


@overload
def text_input(label: str, required: Literal[False] = False, *,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Optional[str]:
    pass


@overload
def text_input(label: str, required: Literal[True], *,
               disable_if: None = None, hide_if: None = None) -> str:
    pass


@overload
def text_input(label: str, required: bool = False, *,
               disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> Optional[str]:
    pass


@overload
def text_input(label: str, required: bool = False, *,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> Optional[str]:
    pass


def text_input(label: str, required: bool = False, *,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    return _FieldInfo(
        lambda name: TextInputElement(name=name, label=label, required=required,
                                      disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[str] if not required or disable_if or hide_if else str,
        None if not required or disable_if or hide_if else ...,
    )


def static_text(label: str, text: str, *,
                disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> StaticTextElement:
    return cast(
        StaticTextElement,
        _StaticElementInfo(lambda name: StaticTextElement(name=name, label=label, text=text,
                                                          disable_if=_listify(disable_if), hide_if=_listify(hide_if)))
    )


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: Literal[True], selected: bool = False,
             disable_if: None = None, hide_if: None = None) -> Literal[True]:
    pass


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: Literal[False] = False, selected: bool = False,
             disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> bool:
    pass


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: bool = False, selected: bool = False,
             disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> bool:
    pass


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: bool = False, selected: bool = False,
             disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> bool:
    pass


def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: bool = False, selected: bool = False,
             disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    return _FieldInfo(
        lambda name: CheckboxElement(name=name, left_label=left_label, right_label=right_label, required=required,
                                     selected=selected, disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        bool if not required or disable_if or hide_if else Literal[True],
        False if not required or disable_if or hide_if else ...
    )


@overload
def radio_group(label: str, enum: Type[_E], *, required: Literal[False] = False,
                disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Optional[_E]:
    pass


@overload
def radio_group(label: str, enum: Type[_E], *, required: Literal[True],
                disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> Optional[_E]:
    pass


@overload
def radio_group(label: str, enum: Type[_E], *, required: Literal[True],
                disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> Optional[_E]:
    pass


@overload
def radio_group(label: str, enum: Type[_E], *, required: Literal[True],
                disable_if: None = None, hide_if: None = None) -> _E:
    pass


def radio_group(label: str, enum: Type[_E], *, required: bool = False,
                disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    # enum type passed
    options = [Option(label=variant.label, value=variant.value, selected=variant.selected) for variant in enum]
    base_type = enum

    return _FieldInfo(
        lambda name: RadioGroupElement(name=name, label=label, options=options, required=required,
                                       disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[base_type] if not required or disable_if or hide_if else base_type,
        None if not required or disable_if or hide_if else ...
    )


@overload
def select(label: str, enum: Type[_E], *,
           required: Literal[False] = False, multiple: Literal[False] = False,
           disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Optional[_E]:
    pass


@overload
def select(label: str, enum: Type[_E], *,
           required: Literal[True], multiple: Literal[False] = False,
           disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> Optional[_E]:
    pass


@overload
def select(label: str, enum: Type[_E], *,
           required: Literal[True], multiple: Literal[False] = False,
           disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> Optional[_E]:
    pass


@overload
def select(label: str, enum: Type[_E], *,
           required: Literal[True], multiple: Literal[False] = False,
           disable_if: None = None, hide_if: None = None) -> _E:
    pass


@overload
def select(label: str, enum: Type[_E], *,
           required: bool = False, multiple: Literal[True],
           disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Set[_E]:
    pass


def select(label: str, enum: Type[_E], *,
           required: bool = False, multiple: bool = False,
           disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    # enum type passed
    options = [Option(label=variant.label, value=variant.value, selected=variant.selected) for variant in enum]

    expected_type: Type
    default: object
    if multiple:
        expected_type = Set[enum]  # type: ignore[valid-type]
        if not required or disable_if or hide_if:
            default = set()
        else:
            default = ...
    elif not required or disable_if or hide_if:
        expected_type = Optional[enum]  # type: ignore[valid-type, assignment]
        default = None
    else:
        expected_type = enum  # type: ignore[valid-type]
        default = ...

    return _FieldInfo(
        lambda name: SelectElement(name=name, label=label, multiple=multiple, required=required, options=options,
                                   disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        expected_type,
        default
    )


def option(label: str, selected: bool = False) -> _OptionInfo:
    return _OptionInfo(label, selected)


@overload
def hidden(value: _S, *,
           disable_if: None = None, hide_if: None = None) -> _S:
    pass


@overload
def hidden(value: _S, *,
           disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> Optional[_S]:
    pass


@overload
def hidden(value: _S, *,
           disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> Optional[_S]:
    pass


def hidden(value: _S, *, disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    return cast(_S, _FieldInfo(
        lambda name: HiddenElement(name=name, value=value,
                                   disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[Literal[value]] if disable_if or hide_if else Literal[value],
        None if disable_if or hide_if else ...
    ))


def section(header: str, model: Type[_F]) -> _F:
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast(_F, _SectionInfo(header, model))


def group(label: str, model: Type[_F], *,
          disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> _F:
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast(_F, _FieldInfo(
        lambda name: GroupElement(name=name, label=label, elements=list(model.form_elements()),
                                  disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        model
    ))


def repeat(model: Type[_F], *, initial: int = 1, increment: int = 1, button_label: Optional[str] = None) -> list[_F]:
    return cast(list[_F], _FieldInfo(
        lambda name: RepetitionElement(name=name, initial_elements=initial, increment=increment,
                                       button_label=button_label, elements=list(model.form_elements())),
        list[model]  # type: ignore[valid-type]
    ))


_C = TypeVar("_C", bound=Condition)


def _condition_factory(model: Type[_C]) -> Callable[[str], _C]:
    return lambda name: model(name=name)


def _condition_with_value_factory(model: Type[_C]) -> Callable[[str, Any], _C]:
    return lambda name, value: model(name=name, value=value)


is_checked = _condition_factory(IsChecked)
is_not_checked = _condition_factory(IsNotChecked)
equals = _condition_with_value_factory(Equals)
does_not_equal = _condition_with_value_factory(DoesNotEqual)
is_in = _condition_with_value_factory(In)
