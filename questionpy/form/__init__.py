"""This module contains DSL-like functions for defining the contents of [`FormModel`][questionpy.form.FormModel].

In order to allow for correct type inference of the resulting fields, most functions are typed to return what will later
be part of the expected data. In reality, they return internal objects containing field metadata, which is combined in
the [`FormModel`][questionpy.form._model.FormModel] metaclass with the field name. This is analogous to Pydantic's own
`Field` function.

References:
    Many elements can be hidden or disabled on the client-side based on the state of other inputs. These *conditions*
    are created using [`is_checked`][questionpy.form.is_checked], [`is_not_checked`][questionpy.form.is_not_checked],
    [`equals`][questionpy.form.equals], [`does_not_equal`][questionpy.form.does_not_equal] and
    [`is_in`][questionpy.form.is_in], and passed to the conditional element in `hide_if` or `disable_if`. See the
    documentation of the various function for details and examples.

    A condition always includes a reference to an input element. These references have the following format:

        segment_1[segment_2][segment_3][...

    Where each segment is either:

    - An element name, or
    - `..`, which resolves to the parent element

    A reference is always relative to the element that defines it. For example, the condition
    `is_checked(..[foo][bar])` is resolved as follows:

    - Get the parent of the model in which the reference is made. If the reference is made at the top level, it is
      invalid, since there is no parent for `..` to select.
    - From there, get the element `foo`. If there is no element named  `foo` here, the reference is invalid.
    - If `foo` is not a group or section, the reference is also invalid, since it cannot contain another element.
    - Within `foo`, get the element `bar`.
    - Ensure that `bar` is a valid target for `is_checked`, i.e. a checkbox. Otherwise, the reference is invalid.

    All conditions in an [`OptionsFormDefinition`][questionpy_common.elements.OptionsFormDefinition] are validated by
    [`validate_form`][questionpy.form.validation.validate_form], which is notably called by
    [`QuestionType.__init_subclass__`][questionpy.QuestionType].
"""

#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from questionpy_common.elements import (
    CanHaveConditions,
    CheckboxElement,
    CheckboxGroupElement,
    FormElement,
    FormSection,
    GroupElement,
    HiddenElement,
    Option,
    OptionsFormDefinition,
    RadioGroupElement,
    RepetitionElement,
    SelectElement,
    StaticTextElement,
    TextAreaElement,
    TextInputElement,
    is_form_element,
)

from ._dsl import (
    checkbox,
    does_not_equal,
    equals,
    group,
    hidden,
    is_checked,
    is_in,
    is_not_checked,
    option,
    radio_group,
    repeat,
    section,
    select,
    static_text,
    text_area,
    text_input,
)
from ._model import FormModel, OptionEnum

__all__ = [
    "CanHaveConditions",
    "CheckboxElement",
    "CheckboxGroupElement",
    "FormElement",
    "FormModel",
    "FormSection",
    "GroupElement",
    "HiddenElement",
    "Option",
    "OptionEnum",
    "OptionsFormDefinition",
    "RadioGroupElement",
    "RepetitionElement",
    "SelectElement",
    "StaticTextElement",
    "TextAreaElement",
    "TextInputElement",
    "checkbox",
    "does_not_equal",
    "equals",
    "group",
    "hidden",
    "is_checked",
    "is_form_element",
    "is_in",
    "is_not_checked",
    "option",
    "radio_group",
    "repeat",
    "section",
    "select",
    "static_text",
    "text_area",
    "text_input",
]
