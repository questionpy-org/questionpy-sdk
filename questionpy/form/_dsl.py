from typing import cast, TypeVar, Any, overload, Literal, Optional, Set, Union, List, Type

from questionpy.form._elements import TextInputElement, StaticTextElement, CheckboxElement, RadioGroupElement, \
    SelectElement, HiddenElement, GroupElement
from questionpy.form._model import FormModel, _FieldInfo, _SectionInfo, OptionEnum, _OptionInfo, _StaticElementInfo

__all__ = ["text_input", "static_text", "checkbox", "radio_group", "select", "option", "hidden", "section", "group"]

_S = TypeVar("_S", bound=str)
_F = TypeVar("_F", bound=FormModel)
_E = TypeVar("_E", bound=OptionEnum)


@overload
def text_input(label: str, required: Literal[False] = False) -> Optional[str]:
    pass


@overload
def text_input(label: str, required: Literal[True]) -> str:
    pass


def text_input(label: str, required: bool = False) -> Any:
    return _FieldInfo(
        lambda name: TextInputElement(name=name, label=label, required=required),
        str if required else Optional[str],
        ... if required else None
    )


def static_text(label: str, text: str) -> StaticTextElement:
    return cast(
        StaticTextElement,
        _StaticElementInfo(lambda name: StaticTextElement(name=name, label=label, text=text))
    )


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: Literal[True], selected: bool = False) -> Literal[True]:
    pass


@overload
def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: Literal[False] = False, selected: bool = False) -> bool:
    pass


def checkbox(left_label: Optional[str] = None, right_label: Optional[str] = None, *,
             required: bool = False, selected: bool = False) -> Any:
    return _FieldInfo(
        lambda name: CheckboxElement(name=name, left_label=left_label, right_label=right_label, required=required,
                                     selected=selected),
        Literal[True] if required else bool,
        ... if required else False
    )


@overload
def radio_group(label: str, options: List[RadioGroupElement.Option], /,
                required: Literal[True]) -> str:
    pass


@overload
def radio_group(label: str, options: List[RadioGroupElement.Option], /,
                required: Literal[False] = False) -> Optional[str]:
    pass


@overload
def radio_group(label: str, enum: Type[_E], /, required: Literal[False] = False) -> Optional[_E]:
    pass


@overload
def radio_group(label: str, enum: Type[_E], /, required: Literal[True]) -> _E:
    pass


def radio_group(label: str, enum_or_options: Union[List[RadioGroupElement.Option], Type[_E]], /,
                required: bool = False) -> Any:
    if isinstance(enum_or_options, list):
        # raw options passed, not an enum
        options = enum_or_options
        base_type = Literal[tuple(option.value for option in enum_or_options)]  # type: ignore[misc]
    else:
        # enum type passed
        options = [RadioGroupElement.Option(label=variant.label, value=variant.value, selected=variant.selected)
                   for variant in enum_or_options]
        base_type = enum_or_options

    return _FieldInfo(
        lambda name: RadioGroupElement(name=name, label=label, options=options, required=required),
        base_type if required else Optional[base_type],
        ... if required else None
    )


@overload
def select(label: str, options: List[SelectElement.Option], /, *,
           required: Literal[False] = False, multiple: Literal[False] = False) -> Optional[str]:
    pass


@overload
def select(label: str, options: List[SelectElement.Option], /, *,
           required: Literal[True], multiple: Literal[False] = False) -> str:
    pass


@overload
def select(label: str, options: List[SelectElement.Option], /, *,
           required: bool = False, multiple: Literal[True]) -> Set[str]:
    pass


@overload
def select(label: str, options: Type[_E], /, *,
           required: Literal[False] = False, multiple: Literal[False] = False) -> Optional[_E]:
    pass


@overload
def select(label: str, options: Type[_E], /, *,
           required: Literal[True], multiple: Literal[False] = False) -> _E:
    pass


@overload
def select(label: str, options: Type[_E], /, *,
           required: bool = False, multiple: Literal[True]) -> Set[_E]:
    pass


def select(label: str, enum_or_options: Union[List[SelectElement.Option], Type[_E]], /, *,
           required: bool = False, multiple: bool = False) -> Any:
    if isinstance(enum_or_options, list):
        # raw options passed, not an enum
        options = enum_or_options
        base_type = Literal[tuple(option.value for option in enum_or_options)]  # type: ignore[misc]
    else:
        # enum type passed
        options = [SelectElement.Option(label=variant.label, value=variant.value, selected=variant.selected)
                   for variant in enum_or_options]
        base_type = enum_or_options

    return _FieldInfo(
        lambda name: SelectElement(name=name, label=label, multiple=multiple, required=required, options=options),
        Set[base_type] if multiple else base_type if required else Optional[base_type],  # type: ignore[valid-type]
        ... if required else set() if multiple else None
    )


def option(label: str, selected: bool = False) -> _OptionInfo:
    return _OptionInfo(label, selected)


def hidden(value: _S) -> _S:
    return cast(_S, _FieldInfo(
        lambda name: HiddenElement(name=name, value=value),
        Literal[value]
    ))


def section(header: str, model: Type[_F]) -> _F:
    # we pretend to return an instance of the model so the type of the section field can be inferred
    return cast(_F, _SectionInfo(header, model))


def group(label: str, model: Type[_F]) -> _F:
    # we pretend to return an instance of the model so the type of the section field can be inferred
    return cast(_F, _FieldInfo(
        lambda name: GroupElement(name=name, label=label, elements=list(model.form_elements())),
        model
    ))
