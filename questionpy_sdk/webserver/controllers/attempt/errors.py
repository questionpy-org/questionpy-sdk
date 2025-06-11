#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import logging
from abc import ABC, abstractmethod
from bisect import insort
from collections.abc import Collection, Iterator, MutableMapping, Sequence
from operator import attrgetter
from typing import Annotated, Literal

from lxml import etree
from pydantic import BaseModel, ConfigDict, Field, RootModel, computed_field

_log = logging.getLogger(__name__)

type TemplateKwargs = Annotated[
    MutableMapping[str, str | Sequence[str]],
    Field(
        description="A mapping of placeholder keys to values for a template.",
        json_schema_extra={"default": {}},
    ),
]


type ErrorSectionKey = Annotated[
    Literal["formulation", "general_feedback", "specific_feedback", "right_answer"], Field(title="ErrorSectionKey")
]


type SectionErrorMap = Annotated[
    MutableMapping[ErrorSectionKey, RenderErrorCollection],
    Field(
        description="A mapping of sections to their associated render errors.",
        json_schema_extra={"default": {}},
    ),
]


type RenderError = Annotated[
    InvalidAttributeValueError
    | ConversionError
    | PlaceholderReferenceError
    | InvalidCleanOptionError
    | InvalidContentError
    | ExpectedAncestorError
    | UnknownElementError
    | UnknownAttributeError
    | DuplicateNameError
    | XMLSyntaxError,
    Field(discriminator="kind"),
]


class BaseRenderError(BaseModel, ABC):
    """Represents a generic error which occurred during rendering."""

    model_config = ConfigDict(frozen=True)

    template: str
    """A template string that defines the structure of the error message.

    It can contain placeholders corresponding to the keys in `template_kwargs`.
    These placeholders are identified by braces (`{` and `}`), similar to `str.format`.
    """

    template_kwargs: TemplateKwargs = {}
    """A mapping containing the values of the placeholders in `template`.

    If a value is of type `Sequence[str]`, it will be formatted as a human-readable list.
    """

    @computed_field  # type: ignore[prop-decorator]
    @property
    def type(self) -> str:
        return self.__class__.__name__

    @computed_field  # type: ignore[prop-decorator]
    @property
    @abstractmethod
    def line(self) -> int | None:
        """Original line number where the error occurred or None if unknown."""

    @property
    def order(self) -> int:
        """Can be used to order multiple errors."""
        return self.line or 0

    @property
    def message(self) -> str:
        """A human-readable, formatted description of the error."""
        template_kwargs = {}
        for key, values in self.template_kwargs.items():
            collection = (values,) if isinstance(values, str) else values
            template_kwargs[key] = self._format_human_readable_list(collection)

        return self.template.format_map(template_kwargs)

    @staticmethod
    def _format_human_readable_list(values: Sequence[str]) -> str:
        if not values:
            return ""

        *values, last_value = values
        last_value = f"'{last_value}'"
        if not values:
            return last_value

        joined_values = "', '".join(values)
        return f"'{joined_values}' and {last_value}"


class RenderElementError(BaseRenderError, ABC):
    """A generic element error which occurred during rendering."""

    _element: etree._Element
    """The element where the error occurred."""

    def __init__(self, element: etree._Element, template: str, template_kwargs: TemplateKwargs | None = None):
        template_kwargs = template_kwargs or {}
        template_kwargs["element"] = self._element_representation(element)
        super().__init__(template=template, template_kwargs=template_kwargs)
        self._element = element

    @property
    def line(self) -> int | None:
        """Original line number as found by the parser or None if unknown."""
        return self._element.sourceline  # type: ignore[return-value]

    @staticmethod
    def _element_representation(element: etree._Element) -> str:
        """Generate a human-readable string representation of an XML element."""
        # Return the whole element if it is a PI.
        if isinstance(element, etree._ProcessingInstruction):
            return str(element)

        # Create the prefix of an element. We do not want to keep 'html' as a prefix.
        prefix = f"{element.prefix}:" if element.prefix and element.prefix != "html" else ""
        return f"{prefix}{etree.QName(element).localname}"


class InvalidAttributeValueError(RenderElementError):
    """Invalid attribute value(s)."""

    kind: Literal["invalid_attribute_value"] = "invalid_attribute_value"

    def __init__(
        self,
        element: etree._Element,
        attribute: str,
        value: str | Sequence[str],
        expected: Sequence[str] | None = None,
    ):
        template_kwargs = {"value": value, "attribute": attribute}
        expected_str = ""
        if expected:
            template_kwargs["expected"] = expected
            expected_str = " Expected values are {expected}."

        super().__init__(
            element,
            f"Invalid value {{value}} for attribute {{attribute}} on element {{element}}.{expected_str}",
            template_kwargs,
        )


class ConversionError(RenderElementError):
    """Could not convert a value to another type."""

    kind: Literal["conversion"] = "conversion"

    def __init__(self, element: etree._Element, value: str, to_type: type, attribute: str | None = None):
        template_kwargs: TemplateKwargs = {"value": value, "type": to_type.__name__}

        in_attribute = ""
        if attribute:
            template_kwargs["attribute"] = attribute
            in_attribute = " in attribute {attribute}"
        template = f"Unable to convert {{value}} to {{type}}{in_attribute} at element {{element}}."

        super().__init__(element, template, template_kwargs)


class PlaceholderReferenceError(RenderElementError):
    """An unknown or no placeholder was referenced."""

    kind: Literal["placeholder_reference"] = "placeholder_reference"

    def __init__(self, element: etree._Element, placeholder: str | None, available: Sequence[str]):
        template_kwargs: TemplateKwargs = {}

        if placeholder is None:
            template = "No placeholder was referenced."
        else:
            template = "Referenced placeholder {placeholder} was not found."
            template_kwargs["placeholder"] = placeholder

            if len(available) == 0:
                template += " No placeholders were provided."
            else:
                template += " These are the provided placeholders: {available}."
                template_kwargs["available"] = available

        super().__init__(element, template, template_kwargs)


class InvalidCleanOptionError(RenderElementError):
    """Invalid clean option."""

    kind: Literal["invalid_clean_option"] = "invalid_clean_option"

    def __init__(self, element: etree._Element, option: str, expected: Sequence[str]):
        super().__init__(
            element,
            "Invalid cleaning option {option}. Available options are {expected}.",
            {"option": option, "expected": expected},
        )


class InvalidContentError(RenderElementError):
    """Invalid content placement."""

    kind: Literal["invalid_content"] = "invalid_content"

    def __init__(self, element: etree._Element, attribute: str):
        super().__init__(
            element,
            "Avoid placing text or processing instructions directly inside {element} with the {attribute} "
            "attribute. Wrap the content in an element instead.",
            {"attribute": attribute},
        )


class ExpectedAncestorError(RenderElementError):
    """Invalid element placement."""

    kind: Literal["expected_ancestor"] = "expected_ancestor"

    def __init__(self, element: etree._Element, expected_ancestor_attribute: str):
        super().__init__(
            element,
            "{element} must be placed inside an element with the {expected_ancestor_attribute} attribute.",
            {"expected_ancestor_attribute": expected_ancestor_attribute},
        )


class UnknownElementError(RenderElementError):
    """Unknown element with qpy-namespace."""

    kind: Literal["unknown_element"] = "unknown_element"

    def __init__(self, element: etree._Element):
        super().__init__(element, "Unknown element {element}.")


class UnknownAttributeError(RenderElementError):
    """Unknown attribute with qpy-namespace."""

    kind: Literal["unknown_attribute"] = "unknown_attribute"

    def __init__(self, element: etree._Element, attributes: Sequence[str]):
        s = "" if len(attributes) == 1 else "s"
        super().__init__(
            element,
            f"Unknown attribute{s} {{attributes}} on element {{element}}.",
            {"attributes": attributes},
        )


class DuplicateNameError(RenderElementError):
    """Invalid duplicate input name."""

    kind: Literal["duplicate_name"] = "duplicate_name"

    def __init__(self, element: etree._Element, name: str, other_element: etree._Element):
        super().__init__(
            element,
            "{element} should not have the same name ({name}) like {other_element} at line {line}.",
            {
                "name": name,
                "other_element": self._element_representation(other_element),
                "line": str(other_element.sourceline or "?"),
            },
        )


class XMLSyntaxError(BaseRenderError):
    """Syntax error while parsing the XML."""

    kind: Literal["xml_syntax"] = "xml_syntax"

    _error: etree.XMLSyntaxError

    def __init__(self, error: etree.XMLSyntaxError):
        super().__init__(template=error.msg)
        self._error = error

    @property
    def line(self) -> int | None:
        return self._error.lineno

    @property
    def order(self) -> int:
        # Syntax errors can lead to a multitude of other errors therefore we want them to be the first in order.
        return -1


class RenderErrorCollection(RootModel[list[RenderError]], Collection[RenderError]):
    """Collects render errors and provides a sorted iterator."""

    root: list[RenderError] = []

    def insert(self, error: RenderError) -> None:
        insort(self.root, error, key=attrgetter("order"))

    def __contains__(self, value: object) -> bool:
        return value in self.root

    def __iter__(self) -> Iterator[BaseRenderError]:  # type: ignore[override]
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.root})"


def log_render_errors(error_map: SectionErrorMap) -> None:
    for section, errors in error_map.items():
        errors_string = ""
        for error in errors:
            line = f"Line {error.line}: " if error.line else ""
            errors_string += f"\n\t- {line}{error.type} - {error.message}"
        error_count = len(errors)
        s = "" if error_count == 1 else "s"
        _log.warning(f"{error_count} error{s} occurred while rendering {section}:{errors_string}")
