#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import Collection
from typing import Any, Literal, cast, overload

from pydantic import BeforeValidator
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from questionpy_common import TranslatableString
from questionpy_common.conditions import Condition, DoesNotEqual, Equals, In, IsChecked, IsNotChecked
from questionpy_common.elements import (
    CheckboxElement,
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

from ._model import FormModel, OptionEnum, _FieldInfo, _OptionInfo, _SectionInfo, _StaticElementInfo

# TODO: - Add support for numeric inputs (and maybe others?)
#       - Make labels optional

type _OneOrMoreConditions = Condition | list[Condition]
type _ZeroOrMoreConditions = _OneOrMoreConditions | None


@overload
def _wrap_in[T](coll_type: type[set], value: T | Collection[T] | None) -> set[T]: ...


@overload
def _wrap_in[T](coll_type: type[list], value: T | Collection[T] | None) -> list[T]: ...


def _wrap_in[T](coll_type: type[set] | type[list], value: T | Collection[T] | None) -> Collection[T]:
    if value is None:
        return coll_type()
    if isinstance(value, coll_type):
        return cast("Collection[T]", value)
    if isinstance(value, Collection) and not isinstance(value, str):  # (str is a subclass of Collection)
        return coll_type(value)

    return coll_type((cast("T", value),))  # MyPy gets confused here without the cast.


@overload
def text_input(
    label: str | TranslatableString,
    *,
    required: Literal[False] = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> str | None:
    pass


@overload
def text_input(
    label: str | TranslatableString,
    *,
    required: Literal[True],
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: None = None,
    hide_if: None = None,
) -> str:
    pass


@overload
def text_input(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _OneOrMoreConditions,
    hide_if: _ZeroOrMoreConditions = None,
) -> str | None:
    pass


@overload
def text_input(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _OneOrMoreConditions,
) -> str | None:
    pass


def text_input(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> Any:
    """Adds a single-line text input field.

    Args:
        label: Text describing the element, shown verbatim.
        required: Require some non-empty input to be entered before the form can be submitted.
        default: Default value of the input when first loading the form. Part of the submitted form data.
        placeholder: Placeholder to show when no value has been entered yet. Not part of the submitted form data.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return _FieldInfo(
        type=str | None if not required or disable_if or hide_if else str,
        build=lambda name: TextInputElement(
            name=name,
            label=label,
            required=required,
            default=default,
            placeholder=placeholder,
            help=help,
            disable_if=_wrap_in(list, disable_if),
            hide_if=_wrap_in(list, hide_if),
        ),
        pydantic_field_info=FieldInfo(
            default=None if not required or disable_if or hide_if else PydanticUndefined,
            min_length=1 if required else None,
        ),
    )


@overload
def text_area(
    label: str | TranslatableString,
    *,
    required: Literal[False] = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> str | None:
    pass


@overload
def text_area(
    label: str | TranslatableString,
    *,
    required: Literal[True],
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: None = None,
    hide_if: None = None,
) -> str:
    pass


@overload
def text_area(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _OneOrMoreConditions,
    hide_if: _ZeroOrMoreConditions = None,
) -> str | None:
    pass


@overload
def text_area(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _OneOrMoreConditions,
) -> str | None:
    pass


def text_area(
    label: str | TranslatableString,
    *,
    required: bool = False,
    default: str | TranslatableString | None = None,
    placeholder: str | TranslatableString | None = None,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> Any:
    """Adds a multi-line text area field.

    Args:
        label: Text describing the element, shown verbatim.
        required: Require some non-empty input to be entered before the form can be submitted.
        default: Default value of the input when first loading the form. Part of the submitted form data.
        placeholder: Placeholder to show when no value has been entered yet. Not part of the submitted form data.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return _FieldInfo(
        type=str | None if not required or disable_if or hide_if else str,
        build=lambda name: TextAreaElement(
            name=name,
            label=label,
            required=required,
            default=default,
            placeholder=placeholder,
            help=help,
            disable_if=_wrap_in(list, disable_if),
            hide_if=_wrap_in(list, hide_if),
        ),
        pydantic_field_info=FieldInfo(
            default=None if not required or disable_if or hide_if else PydanticUndefined,
            min_length=1 if required else None,
        ),
    )


def static_text(
    label: str | TranslatableString,
    text: str | TranslatableString,
    *,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> StaticTextElement:
    """Adds a line with a label and some static text.

    Args:
        label: Text describing the element, shown verbatim.
        text: Main text described by the label, shown verbatim.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        The element.
    """
    return cast(
        "StaticTextElement",
        _StaticElementInfo(
            lambda name: StaticTextElement(
                name=name,
                label=label,
                text=text,
                help=help,
                disable_if=_wrap_in(list, disable_if),
                hide_if=_wrap_in(list, hide_if),
            )
        ),
    )


@overload
def checkbox(
    left_label: str | TranslatableString | None = None,
    right_label: str | TranslatableString | None = None,
    *,
    required: Literal[True],
    selected: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: None = None,
    hide_if: None = None,
) -> Literal[True]:
    pass


@overload
def checkbox(
    left_label: str | TranslatableString | None = None,
    right_label: str | TranslatableString | None = None,
    *,
    required: Literal[False] = False,
    selected: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> bool:
    pass


@overload
def checkbox(
    left_label: str | TranslatableString | None = None,
    right_label: str | TranslatableString | None = None,
    *,
    required: bool = False,
    selected: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _OneOrMoreConditions,
    hide_if: _ZeroOrMoreConditions = None,
) -> bool:
    pass


@overload
def checkbox(
    left_label: str | TranslatableString | None = None,
    right_label: str | TranslatableString | None = None,
    *,
    required: bool = False,
    selected: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _OneOrMoreConditions,
) -> bool:
    pass


def checkbox(
    left_label: str | TranslatableString | None = None,
    right_label: str | TranslatableString | None = None,
    *,
    required: bool = False,
    selected: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> Any:
    """Adds a checkbox.

    Args:
        left_label: Label shown the same way as labels on other element types.
        right_label: Additional label shown to the right of the checkbox.
        required: Require this checkbox to be selected before the form can be submitted.
        selected: Default state of the checkbox.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return _FieldInfo(
        type=bool if not required or disable_if or hide_if else Literal[True],
        build=lambda name: CheckboxElement(
            name=name,
            left_label=left_label,
            right_label=right_label,
            required=required,
            help=help,
            selected=selected,
            disable_if=_wrap_in(list, disable_if),
            hide_if=_wrap_in(list, hide_if),
        ),
        pydantic_field_info=FieldInfo(default=False if not required or disable_if or hide_if else PydanticUndefined),
    )


@overload
def radio_group[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[False] = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> E | None:
    pass


@overload
def radio_group[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    help: str | TranslatableString | None = None,
    disable_if: _OneOrMoreConditions,
    hide_if: _ZeroOrMoreConditions = None,
) -> E | None:
    pass


@overload
def radio_group[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _OneOrMoreConditions,
) -> E | None:
    pass


@overload
def radio_group[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    help: str | TranslatableString | None = None,
    disable_if: None = None,
    hide_if: None = None,
) -> E:
    pass


def radio_group[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> Any:
    """Adds a group of radio buttons, of which at most one can be selected at a time.

    Args:
        label: Text describing the element, shown verbatim.
        enum (type[OptionEnum]): An `OptionEnum` subclass containing the available options.
        required: Require one of the options to be selected before the form can be submitted.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    options = [Option(label=variant.label, value=variant.value, selected=variant.selected) for variant in enum]

    return _FieldInfo(
        type=enum | None if not required or disable_if or hide_if else enum,
        build=lambda name: RadioGroupElement(
            name=name,
            label=label,
            options=options,
            required=required,
            help=help,
            disable_if=_wrap_in(list, disable_if),
            hide_if=_wrap_in(list, hide_if),
        ),
        pydantic_field_info=FieldInfo(default=None if not required or disable_if or hide_if else PydanticUndefined),
    )


@overload
def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[False] = False,
    multiple: Literal[False] = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> E | None:
    pass


@overload
def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    multiple: Literal[False] = False,
    help: str | TranslatableString | None = None,
    disable_if: _OneOrMoreConditions,
    hide_if: _ZeroOrMoreConditions = None,
) -> E | None:
    pass


@overload
def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    multiple: Literal[False] = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _OneOrMoreConditions,
) -> E | None:
    pass


@overload
def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: Literal[True],
    multiple: Literal[False] = False,
    help: str | TranslatableString | None = None,
    disable_if: None = None,
    hide_if: None = None,
) -> E:
    pass


@overload
def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: bool = False,
    multiple: Literal[True],
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> set[E]:
    pass


def select[E: OptionEnum](
    label: str | TranslatableString,
    enum: type[E],
    *,
    required: bool = False,
    multiple: bool = False,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> Any:
    """Adds a drop-down list.

    Args:
        label: Text describing the element, shown verbatim.
        enum (type[OptionEnum]): An `OptionEnum` subclass containing the available options.
        required: Require at least one of the options to be selected before the form can be submitted.
        multiple: Allow the selection of multiple options.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    options = [Option(label=variant.label, value=variant.value, selected=variant.selected) for variant in enum]

    expected_type: type
    default: object
    annotate_with: tuple[object, ...] = ()
    if multiple:
        expected_type = set[enum]  # type: ignore[valid-type]
        default = set() if not required or disable_if or hide_if else PydanticUndefined
        annotate_with = (BeforeValidator(lambda value: _wrap_in(set, value)),)
    elif not required or disable_if or hide_if:
        expected_type = enum | None  # type: ignore[assignment]
        default = None
    else:
        expected_type = enum
        default = PydanticUndefined

    return _FieldInfo(
        type=expected_type,
        build=lambda name: SelectElement(
            name=name,
            label=label,
            multiple=multiple,
            required=required,
            options=options,
            help=help,
            disable_if=_wrap_in(list, disable_if),
            hide_if=_wrap_in(list, hide_if),
        ),
        pydantic_field_info=FieldInfo(default=default),
        annotate_with=annotate_with,
    )


def option(label: str | TranslatableString, *, selected: bool = False, value: str | None = None) -> _OptionInfo:
    """Adds an option to an [`OptionEnum`][questionpy.form.OptionEnum].

    Args:
        label: Text describing the option, shown verbatim.
        selected: Default state of the option.
        value: By default, the name of the option is used as its value as well. You can set a different value here,
               which will then be used in rendering as well as (de)serialization.

    Returns:
        An internal object containing metadata about the option.

    Examples:
        >>> class ColorEnum(OptionEnum):
        ...     RED = option("Red", value="R")
        ...     GREEN = option("Green", value="G")
        ...     BLUE = option("Blue", value="B")
        ...     NONE = option("None", selected=True)
    """
    return _OptionInfo(label, selected, value=value)


@overload
def hidden[S: str](value: S, *, disable_if: None = None, hide_if: None = None) -> S:
    pass


@overload
def hidden[S: str](value: S, *, disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> S | None:
    pass


@overload
def hidden[S: str](value: S, *, disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> S | None:
    pass


def hidden[S: str](value: S, *, disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    """Adds a hidden element with a fixed value.

    Args:
        value (str): Fixed value.
        disable_if (Condition | list[Condition] | None): Disable this element if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return cast(
        "S",
        _FieldInfo(
            type=Literal[value] | None if disable_if or hide_if else Literal[value],
            build=lambda name: HiddenElement(
                name=name, value=value, disable_if=_wrap_in(list, disable_if), hide_if=_wrap_in(list, hide_if)
            ),
            pydantic_field_info=FieldInfo(default=None if disable_if or hide_if else PydanticUndefined),
        ),
    )


def section[F: FormModel](header: str | TranslatableString, model: type[F]) -> F:
    """Adds a form section that can be expanded and collapsed.

    Args:
        header: Header to be shown at the top of the section.
        model (type[FormModel]): A `FormModel` subclass containing the fields of the section.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        The following replicates Moodle's "Combined feedback" section. We define a separate `FormModel` subclass
        containing three text inputs.

        >>> class FeedbackSection(FormModel):
        ...     correct = text_input("For any correct response", required=True)
        ...     partial = text_input("For any partially correct response")
        ...     incorrect = text_input("For any incorrect response", required=True)

        In our main options class, we use the `section` function, giving a header to the section and referencing our
        sub-model.

        >>> class Options(FormModel):
        ...     feedback = section("Combined feedback", FeedbackSection)
    """
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast("F", _SectionInfo(header, model))


def group[F: FormModel](
    label: str | TranslatableString,
    model: type[F],
    *,
    help: str | TranslatableString | None = None,
    disable_if: _ZeroOrMoreConditions = None,
    hide_if: _ZeroOrMoreConditions = None,
) -> F:
    """Groups multiple elements horizontally with a common label.

    Args:
        label: Label of the group.
        model (type[FormModel]): A `FormModel` subclass containing the fields of the group.
        help: Element help text.
        disable_if (Condition | list[Condition] | None): Disable this group if some condition(s) match.
        hide_if (Condition | list[Condition] | None): Hide this group if some condition(s) match.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        This example shows a text input field directly followed by a drop-down with possible units. We define a separate
        `FormModel` subclass that will contain our grouped inputs.

        >>> class SizeGroup(FormModel):
        ...     amount = text_input("Amount")
        ...     unit = select("Unit", OptionEnum)

        In our main options class, we use the `group` function, giving a label to the group and referencing our
        sub-model.

        >>> class Options(FormModel):
        ...     size = group("Size", SizeGroup)
    """
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast(
        "F",
        _FieldInfo(
            type=model,
            build=lambda name: GroupElement(
                name=name,
                label=label,
                elements=model.qpy_form.general,
                help=help,
                disable_if=_wrap_in(list, disable_if),
                hide_if=_wrap_in(list, hide_if),
            ),
            # When the group dict is not provided at all in the form data, we want Pydantic to use the default values
            # for all grouped fields and raise if there are any required ones. Creating the nested model in a
            # default_factory would achieve that, but the error location in the ValidationError would not be complete,
            # since it would occur in a separate validation. Instead, we use an empty dict as default and tell Pydantic
            # to validate it, which will allow Pydantic to use the full location in case of error, while leading to
            # the same result if there isn't a validation error.
            pydantic_field_info=FieldInfo(default={}, validate_default=True),
        ),
    )


def repeat[F: FormModel](
    model: type[F],
    *,
    initial: int = 1,
    minimum: int = 1,
    increment: int = 1,
    button_label: str | TranslatableString | None = None,
) -> list[F]:
    """Repeats a sub-model, allowing the user to add new repetitions with the click of a button.

    Be aware that the index of repetitions may change when earlier ones are removed. In order to distinguish
    repetitions, look into adding a [generated_id][] field to the repeated model.

    Args:
        model (type[FormModel]): A `FormModel` subclass containing the fields to repeat.
        initial: Number of repetitions to show when the form is first loaded.
        minimum: Minimum number of repetitions, at or below which removal is not possible.
        increment: Number of repetitions to add with each click of the button.
        button_label: Label for the button that adds more repetitions, or None to use default provided by LMS.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        The following shows part of a simplified multiple-choice question. A separate sub-model defines the elements
        that should be repeated.

        >>> class Choice(FormModel):
        ...     text = text_input("Choice")
        ...     correct = checkbox("Correct")

        The sub-model is referenced in the main model using the `repeat` function. In this case, we set it to repeat 3
        times initially, and add 3 new repetitions whith each click of the button. We also customize the button's label.

        >>> class Options(FormModel):
        ...     choices = repeat(Choice, initial=3, increment=3, button_label="Add 3 more choices")
    """
    return cast(
        "list[F]",
        _FieldInfo(
            type=list[model],  # type: ignore[valid-type]
            build=lambda name: RepetitionElement(
                name=name,
                initial_repetitions=initial,
                minimum_repetitions=minimum,
                increment=increment,
                button_label=button_label,
                elements=model.qpy_form.general,
            ),
            annotate_with=(BeforeValidator(lambda value: _wrap_in(list, value)),),
        ),
    )


def generated_id() -> str:
    """Generates a unique ID which won't change across form saves.

    This is especially useful to distinguish repetitions without relying on their index, which may change when
    repetitions are removed.
    """
    return cast(
        "str",
        _FieldInfo(
            type=str, build=lambda name: GeneratedIdElement(name=name), pydantic_field_info=FieldInfo(frozen=True)
        ),
    )


def is_checked(name: str) -> IsChecked:
    """Condition on a checkbox being checked.

    Many elements can be hidden or disabled client-side by passing conditions to `hide_if` or `disable_if`. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to a checkbox element. If the reference points to nothing or to something other than a
            checkbox element, [`validate_form`][questionpy.form.validation.validate_form] will fail.

    Examples:
        In the following, the `email` input will be hidden whenever `opt_out` is checked.

        >>> class MyModel(FormModel):
        ...     opt_out = checkbox("I DO NOT want to receive updates via email.")
        ...     email = text_input("Email address", hide_if=is_checked("opt_out"))
    """
    return IsChecked(name=name)


def is_not_checked(name: str) -> IsNotChecked:
    """Condition on a checkbox being unchecked.

    Many elements can be hidden or disabled client-side by passing conditions to `hide_if` or `disable_if`. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to a checkbox element. If the reference points to nothing or to something other than a
            checkbox element, [`validate_form`][questionpy.form.validation.validate_form] will fail.

    Examples:
        In the following, the `email` input will be shown only when `opt_in` is checked.

        >>> class MyModel(FormModel):
        ...     opt_in = checkbox("I want to receive updates via email.")
        ...     email = text_input("Email address", hide_if=is_not_checked("opt_in"))
    """
    return IsNotChecked(name=name)


def equals(name: str, *, value: str | int | bool) -> Equals:
    """Condition on the value of another field being equal to some static value.

    Many elements can be hidden or disabled client-side by passing conditions to `hide_if` or `disable_if`. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are
            [`TextInputElement`][questionpy.form.TextInputElement],
            [`CheckboxElement`][questionpy.form.CheckboxElement],
            [`RadioGroupElement`][questionpy.form.RadioGroupElement], [`SelectElement`][questionpy.form.SelectElement],
            and [`HiddenElement`][questionpy.form.HiddenElement]. If the reference points to nothing or to an
            element not listed, [`validate_form`][questionpy.form.validation.validate_form] will fail.
        value: Static value to compare with. When the referent is a checkbox, a boolean can be passed here to emulate
            `is(_not)_checked`.

    Examples:
        >>> class MyModel(FormModel):
        ...     email = text_input("Email address")
        ...     send_spam = checkbox("Yes, send me lots of spam!", required=True, hide_if=equals("email", value=""))
    """
    return Equals(name=name, value=value)


def does_not_equal(name: str, *, value: str | int | bool) -> DoesNotEqual:
    """Condition on the value of another field *not* being equal to some static value.

    Many elements can be hidden or disabled client-side by passing conditions to `hide_if` or `disable_if`. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are
            [`TextInputElement`][questionpy.form.TextInputElement],
            [`CheckboxElement`][questionpy.form.CheckboxElement],
            [`RadioGroupElement`][questionpy.form.RadioGroupElement], [`SelectElement`][questionpy.form.SelectElement],
            and [`HiddenElement`][questionpy.form.HiddenElement]. If the reference points to nothing or to an
            element not listed, [`validate_form`][questionpy.form.validation.validate_form] will fail.
        value: Static value to compare with. When the referent is a checkbox, a boolean can be passed here to emulate
            `is(_not)_checked`.

    Examples:
        >>> class MyModel(FormModel):
        ...     email = text_input("Email address")
        ...     warning = static_text(
        ...         "Warning",
        ...         "If you don't give us your email address, we can't send you any spam!",
        ...         hide_if=does_not_equal("email", value=""),
        ...     )
    """
    return DoesNotEqual(name=name, value=value)


def is_in(name: str, values: list[str | int | bool]) -> In:
    """Condition on the value of another field being one of a number of static values.

    Many elements can be hidden or disabled client-side by passing conditions to `hide_if` or `disable_if`. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are
            [`TextInputElement`][questionpy.form.TextInputElement],
            [`CheckboxElement`][questionpy.form.CheckboxElement],
            [`RadioGroupElement`][questionpy.form.RadioGroupElement], [`SelectElement`][questionpy.form.SelectElement],
            and [`HiddenElement`][questionpy.form.HiddenElement]. If the reference points to nothing or to an
            element not listed, [`validate_form`][questionpy.form.validation.validate_form] will fail.
        values: Static values to compare with.
    """
    return In(name=name, value=values)
