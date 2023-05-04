"""This module contains DSL-like functions for defining the contents of :class:`FormModel` s.

In order to allow for correct type inference of the resulting fields, most functions are typed to return what will later
be part of the expected for data.
In reality, they return internal objects containing field metadata, which is combined in the :class:`FormModel`
metaclass with the field name.
This is analogous to Pydantic's own ``Field`` function.

References:
    Many elements can be hidden or disabled on the client-side based on the state of other inputs. These *conditions*
    are created using :func:`is_checked`, :func:`is_not_checked`, :func:`equals`, :func:`does_not_equal` and
    :func:`is_in`, and passed to the conditional element in ``hide_if`` or ``disable_if``. See the documentation of the
    various function for details and examples.

    A condition always includes a reference to an input element. These references have the following format::

        segment_1[segment_2][segment_3][...

    Where each segment is either:

    - An element name, or
    - ``..``, which resolves to the parent element

    A reference is always relative to the element which defines it. For example, the condition
    ``is_checked(..[foo][bar])`` is resolved as follows:

    - Get the parent of the model in which the reference is made. If the reference is made at the top level, it is
      invalid, since there is no parent for ``..`` to select.
    - From there, get the element ``foo``. If there is no element named  ``foo`` here, the reference is
      invalid.
    - If ``foo`` is not a group or section, the reference is also invalid, since it cannot contain another element.
    - Within ``foo``, get the element ``bar``.
    - Ensure that ``bar`` is a valid target for ``is_checked``, i.e. a checkbox. Otherwise, the reference is invalid.

    All conditions in an :class:`OptionsFormDefinition` are validated by :func:`validate_form`, which is notably called
    by :meth:`QuestionType.__init_subclass__`.

Todo:
    - Add support for numeric inputs (and maybe others?)
    - Make labels optional
"""

from typing import cast, TypeVar, Any, overload, Literal, Optional, Set, Union, Type

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
def text_input(label: str, *, required: Literal[False] = False,
               default: Optional[str] = None, placeholder: Optional[str] = None,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Optional[str]:
    pass


@overload
def text_input(label: str, *, required: Literal[True],
               default: Optional[str] = None, placeholder: Optional[str] = None,
               disable_if: None = None, hide_if: None = None) -> str:
    pass


@overload
def text_input(label: str, *, required: bool = False,
               default: Optional[str] = None, placeholder: Optional[str] = None,
               disable_if: _OneOrMoreConditions, hide_if: _ZeroOrMoreConditions = None) -> Optional[str]:
    pass


@overload
def text_input(label: str, *, required: bool = False,
               default: Optional[str] = None, placeholder: Optional[str] = None,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _OneOrMoreConditions) -> Optional[str]:
    pass


def text_input(label: str, *, required: bool = False,
               default: Optional[str] = None, placeholder: Optional[str] = None,
               disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> Any:
    """Adds a text input field.

    Args:
        label: Text describing the element, shown verbatim.
        required: Require some non-empty input to be entered before the form can be submitted.
        default: Default value of the input when first loading the form. Part of the submitted form data.
        placeholder: Placeholder to show when no value has been entered yet. Not part of the submitted form data.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return _FieldInfo(
        lambda name: TextInputElement(name=name, label=label, required=required,
                                      default=default, placeholder=placeholder,
                                      disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[str] if not required or disable_if or hide_if else str,
        None if not required or disable_if or hide_if else ...,
    )


def static_text(label: str, text: str, *,
                disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> StaticTextElement:
    """Adds a line with a label and some static text.

    Args:
        label: Text describing the element, shown verbatim.
        text: Main text described by the label, shown verbatim.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        The element.
    """
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
    """Adds a checkbox.

    Args:
        left_label: Label shown the same way as labels on other element types.
        right_label: Additional label shown to the right of the checkbox.
        required: Require this checkbox to be selected before the form can be submitted.
        selected: Default state of the checkbox.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
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
    """Adds a group of radio buttons, of which at most one can be selected at a time.

    Args:
        label: Text describing the element, shown verbatim.
        enum: An ``OptionEnum`` subclass containing the available options.
        required: Require one of the options to be selected before the form can be submitted.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    options = [Option(label=variant.label, value=variant.value, selected=variant.selected) for variant in enum]

    return _FieldInfo(
        lambda name: RadioGroupElement(name=name, label=label, options=options, required=required,
                                       disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[enum] if not required or disable_if or hide_if else enum,
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
    """Adds a drop-down list.

    Args:
        label: Text describing the element, shown verbatim.
        enum: An ``OptionEnum`` subclass containing the available options.
        required: Require at least one of the options to be selected before the form can be submitted.
        multiple: Allow the selection of multiple options.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
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
    """Adds an option to an ``OptionEnum``.

    Args:
        label: Text describing the option, shown verbatim.
        selected: Default state of the option.

    Returns:
        An internal object containing metadata about the option.

    Examples:
        >>> class ColorEnum(OptionEnum):
        ...     RED = option("Red")
        ...     GREEN = option("Green")
        ...     BLUE = option("Blue")
        ...     NONE = option("None", selected=True)
    """
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
    """Adds a hidden element with a fixed value.

    Args:
        value: Fixed value.
        disable_if: Disable this element if some condition(s) match.
        hide_if: Hide this element if some condition(s) match.

    Returns:
        An internal object containing metadata about the field.
    """
    return cast(_S, _FieldInfo(
        lambda name: HiddenElement(name=name, value=value,
                                   disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        Optional[Literal[value]] if disable_if or hide_if else Literal[value],
        None if disable_if or hide_if else ...
    ))


def section(header: str, model: Type[_F]) -> _F:
    """Adds a form section which can be expanded and collapsed.

    Args:
        header: Header to be shown at the top of the section.
        model: Sub-FormModel containing the fields of the section.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        The following replicates Moodle's "Combined feedback" section. We define a separate ``FormModel`` subclass
        containing three text inputs.

        >>> class FeedbackSection(FormModel):
        ...     correct = text_input("For any correct response", required=True)
        ...     partial = text_input("For any partially correct response")
        ...     incorrect = text_input("For any incorrect response", required=True)

        In our main options class, we use the ``section`` function, giving a header to the section and referencing our
        sub-model.

        >>> class Options(FormModel):
        ...     feedback = section("Combined feedback", FeedbackSection)
    """
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast(_F, _SectionInfo(header, model))


def group(label: str, model: Type[_F], *,
          disable_if: _ZeroOrMoreConditions = None, hide_if: _ZeroOrMoreConditions = None) -> _F:
    """Groups multiple elements horizontally with a common label.

    Args:
        label: Label of the group.
        model: Sub-FormModel containing the fields of the group.
        disable_if: Disable this group if some condition(s) match.
        hide_if: Hide this group if some condition(s) match.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        This example shows a text input field directly followed by a drop-down with possible units. We define a separate
        ``FormModel`` subclass which will contain our grouped inputs.

        >>> class SizeGroup(FormModel):
        ...     amount = text_input("Amount")
        ...     unit = select("Unit", OptionEnum)

        In our main options class, we use the ``group`` function, giving a label to the group and referencing our
        sub-model.

        >>> class Options(FormModel):
        ...     size = group("Size", SizeGroup)
    """
    # We pretend to return an instance of the model so the type of the section field can be inferred.
    return cast(_F, _FieldInfo(
        lambda name: GroupElement(name=name, label=label, elements=list(model.form_elements()),
                                  disable_if=_listify(disable_if), hide_if=_listify(hide_if)),
        model
    ))


def repeat(model: Type[_F], *, initial: int = 1, increment: int = 1, button_label: Optional[str] = None) -> list[_F]:
    """Repeats a sub-model, allowing the user to add new repetitions with the click of a button.

    Args:
        model: Sub-FormModel containing the fields to repeat.
        initial: Number of repetitions to show when the form is first loaded.
        increment: Number of repetitions to add with each click of the button.
        button_label: Label for the button which adds more repetitions, or None to use default provided by LMS.

    Returns:
        An internal object containing metadata about the section.

    Examples:
        The following shows part of a simplified multiple-choice question. A separate sub-model defines the elements
        which should be repeated.

        >>> class Choice(FormModel):
        ...     text = text_input("Choice")
        ...     correct = checkbox("Correct")

        The sub-model is referenced in the main model using the ``repeat`` function. In this case, we set it to repeat 3
        times initially, and add 3 new repetitions whith each click of the button. We also customize the button's label.

        >>> class Options(FormModel):
        ...     choices = repeat(Choice, initial=3, increment=3, button_label="Add 3 more choices")
    """
    return cast(list[_F], _FieldInfo(
        lambda name: RepetitionElement(name=name, initial_elements=initial, increment=increment,
                                       button_label=button_label, elements=list(model.form_elements())),
        list[model]  # type: ignore[valid-type]
    ))


def is_checked(name: str) -> IsChecked:
    """Condition on a checkbox being checked.

    Many elements can be hidden or disabled client-side by passing conditions to ``hide_if`` or ``disable_if``. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to a checkbox element. If the reference points to nothing or to something other than a
            checkbox element, ``validate_form`` will fail.

    Examples:
        In the following, the ``email`` input will be hidden whenever ``opt_out`` is checked.

        >>> class MyModel(FormModel):
        ...     opt_out = checkbox("I DO NOT want to receive updates via email.")
        ...     email = text_input("Email address", hide_if=is_checked("opt_out"))
    """
    return IsChecked(name=name)


def is_not_checked(name: str) -> IsNotChecked:
    """Condition on a checkbox being unchecked.

    Many elements can be hidden or disabled client-side by passing conditions to ``hide_if`` or ``disable_if``. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to a checkbox element. If the reference points to nothing or to something other than a
            checkbox element, ``validate_form`` will fail.

    Examples:
        In the following, the ``email`` input will be shown only when ``opt_in`` is checked.

        >>> class MyModel(FormModel):
        ...     opt_in = checkbox("I want to receive updates via email.")
        ...     email = text_input("Email address", hide_if=is_not_checked("opt_in"))
    """
    return IsNotChecked(name=name)


def equals(name: str, value: Union[str, int, bool]) -> Equals:
    """Condition on the value of another field being equal to some static value.

    Many elements can be hidden or disabled client-side by passing conditions to ``hide_if`` or ``disable_if``. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are ``TextInputElement``, ``CheckboxElement``,
            ``RadioGroupElement``, ``SelectElement`` and ``HiddenElement``. If the reference points to nothing or to an
            element not listed, ``validate_form`` will fail.
        value: Static value to compare with. When the referent is a checkbox, a boolean can be passed here to emulate
            ``is(_not)_checked``.

    Examples:
        >>> class MyModel(FormModel):
        ...     email = text_input("Email address")
        ...     send_spam = checkbox("Yes, send me lots of spam!", required=True, hide_if=equals("email", ""))
    """
    return Equals(name=name, value=value)


def does_not_equal(name: str, value: Union[str, int, bool]) -> DoesNotEqual:
    """Condition on the value of another field NOT being equal to some static value.

    Many elements can be hidden or disabled client-side by passing conditions to ``hide_if`` or ``disable_if``. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are ``TextInputElement``, ``CheckboxElement``,
            ``RadioGroupElement``, ``SelectElement`` and ``HiddenElement``. If the reference points to nothing or to an
            element not listed, ``validate_form`` will fail.
        value: Static value to compare with. When the referent is a checkbox, a boolean can be passed here to emulate
            ``is(_not)_checked``.

    Examples:
        >>> class MyModel(FormModel):
        ...     email = text_input("Email address")
        ...     warning = static_text("Warning", "If you don't give us your email address, we can't send you any spam!",
        ...                           hide_if=does_not_equal("email", ""))
    """
    return DoesNotEqual(name=name, value=value)


def is_in(name: str, values: list[Union[str, int, bool]]) -> In:
    """Condition on the value of another field being one of a number of static values.

    Many elements can be hidden or disabled client-side by passing conditions to ``hide_if`` or ``disable_if``. See the
    module-level documentation for how references work in general.

    Args:
        name: Reference pointing to an input element. Valid referents are ``TextInputElement``, ``CheckboxElement``,
            ``RadioGroupElement``, ``SelectElement`` and ``HiddenElement``. If the reference points to nothing or to an
            element not listed, ``validate_form`` will fail.
        values: Static values to compare with.
    """
    return In(name=name, value=values)
