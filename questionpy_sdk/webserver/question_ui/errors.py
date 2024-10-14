#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import html
import logging
from abc import ABC, abstractmethod
from bisect import insort
from collections.abc import Collection, Iterable, Iterator, Mapping, Sized
from dataclasses import dataclass, field
from operator import attrgetter
from typing import TypeAlias

from lxml import etree

_log = logging.getLogger(__name__)


def _format_human_readable_list(values: Collection[str], opening: str, closing: str) -> str:
    *values, last_value = values
    last_value = f"{opening}{last_value}{closing}"
    if not values:
        return last_value

    return opening + f"{closing}, {opening}".join(values) + f"{closing} and {last_value}"


@dataclass(frozen=True)
class RenderError(ABC):
    """Represents a generic error which occurred during rendering."""

    @property
    def type(self) -> str:
        return self.__class__.__name__

    @property
    @abstractmethod
    def line(self) -> int | None:
        """Original line number where the error occurred or None if unknown."""

    @property
    def order(self) -> int:
        """Can be used to order multiple errors."""
        return self.line or 0

    @property
    @abstractmethod
    def message(self) -> str:
        pass

    @property
    def html_message(self) -> str:
        return html.escape(self.message)


@dataclass(frozen=True)
class RenderElementError(RenderError, ABC):
    """A generic element error which occurred during rendering.

    Attributes:
        element: The element where the error occurred.
        template: A template string that defines the structure of the error message.
            It can contain placeholders corresponding to the keys in `template_kwargs`.
            These placeholders are identified by braces ('{' and '}'), similar to `str.format`.
            The '{element}' placeholder is predefined and resolves to a human-readable representation of `element`.
            Providing a value with the key 'element' in `template_kwargs` will overwrite this behaviour.
        template_kwargs: A mapping containing the values of the placeholders in `template`.
            If a value is of type `Collection[str]`, it will be formatted as a human-readable list.
    """

    element: etree._Element
    template: str
    template_kwargs: Mapping[str, str | Collection[str]] = field(default_factory=dict)

    def _message(self, *, as_html: bool) -> str:
        (opening, closing) = ("<code>", "</code>") if as_html else ("'", "'")
        template_kwargs = {"element": f"{opening}{self.element_representation}{closing}"}

        for key, values in self.template_kwargs.items():
            collection = {values} if isinstance(values, str) else values
            template_kwargs[key] = _format_human_readable_list(collection, opening, closing)

        return self.template.format_map(template_kwargs)

    @property
    def message(self) -> str:
        return self._message(as_html=False)

    @property
    def html_message(self) -> str:
        return self._message(as_html=True)

    @property
    def element_representation(self) -> str:
        # Return the whole element if it is a PI.
        if isinstance(self.element, etree._ProcessingInstruction):
            return str(self.element)

        # Create the prefix of an element. We do not want to keep 'html' as a prefix.
        prefix = f"{self.element.prefix}:" if self.element.prefix and self.element.prefix != "html" else ""
        return prefix + etree.QName(self.element).localname

    @property
    def line(self) -> int | None:
        """Original line number as found by the parser or None if unknown."""
        return self.element.sourceline  # type: ignore[return-value]


@dataclass(frozen=True)
class InvalidAttributeValueError(RenderElementError):
    """Invalid attribute value(s)."""

    def __init__(
        self,
        element: etree._Element,
        attribute: str,
        value: str | Collection[str],
        expected: Collection[str] | None = None,
    ):
        template_kwargs = {"value": value, "attribute": attribute}
        expected_str = ""
        if expected:
            template_kwargs["expected"] = expected
            expected_str = " Expected values are {expected}."

        super().__init__(
            element=element,
            template=f"Invalid value {{value}} for attribute {{attribute}} on element {{element}}.{expected_str}",
            template_kwargs=template_kwargs,
        )


@dataclass(frozen=True)
class ConversionError(RenderElementError):
    """Could not convert a value to another type."""

    def __init__(self, element: etree._Element, value: str, to_type: type, attribute: str | None = None):
        template_kwargs = {"value": value, "type": to_type.__name__}

        in_attribute = ""
        if attribute:
            template_kwargs["attribute"] = attribute
            in_attribute = " in attribute {attribute}"

        template = f"Unable to convert {{value}} to {{type}}{in_attribute} at element {{element}}."
        super().__init__(element=element, template=template, template_kwargs=template_kwargs)


@dataclass(frozen=True)
class PlaceholderReferenceError(RenderElementError):
    """An unknown or no placeholder was referenced."""

    def __init__(self, element: etree._Element, placeholder: str | None, available: Collection[str]):
        if placeholder is None:
            template = "No placeholder was referenced."
            template_kwargs = {}
        else:
            if len(available) == 0:
                provided = "No placeholders were provided."
            else:
                provided = "These are the provided placeholders: {available}."
            template = f"Referenced placeholder {{placeholder}} was not found. {provided}"
            template_kwargs = {"placeholder": placeholder, "available": available}

        super().__init__(
            element=element,
            template=template,
            template_kwargs=template_kwargs,
        )


@dataclass(frozen=True)
class InvalidCleanOptionError(RenderElementError):
    """Invalid clean option."""

    def __init__(self, element: etree._Element, option: str, expected: Collection[str]):
        super().__init__(
            element=element,
            template="Invalid cleaning option {option}. Available options are {expected}.",
            template_kwargs={"option": option, "expected": expected},
        )


@dataclass(frozen=True)
class UnknownElementError(RenderElementError):
    """Unknown element with qpy-namespace."""

    def __init__(self, element: etree._Element):
        super().__init__(
            element=element,
            template="Unknown element {element}.",
        )


@dataclass(frozen=True)
class XMLSyntaxError(RenderError):
    """Syntax error while parsing the XML."""

    error: etree.XMLSyntaxError

    @property
    def line(self) -> int | None:
        return self.error.lineno

    @property
    def order(self) -> int:
        # Syntax errors can lead to a multitude of other errors therefore we want them to be the first in order.
        return -1

    @property
    def message(self) -> str:
        return f"{self.error.msg}"

    @property
    def html_message(self) -> str:
        return f"<samp>{html.escape(self.error.msg)}</samp>"


class RenderErrorCollection(Iterable, Sized):
    """Collects render errors and provides a sorted iterator."""

    _errors: list[RenderError]

    def __init__(self) -> None:
        self._errors = []

    def insert(self, error: RenderError) -> None:
        insort(self._errors, error, key=attrgetter("order"))

    def __iter__(self) -> Iterator[RenderError]:
        return iter(self._errors)

    def __len__(self) -> int:
        return len(self._errors)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._errors})"


RenderErrorCollections: TypeAlias = dict[str, RenderErrorCollection]
"""Section to RenderErrorCollection map."""


def log_render_errors(render_errors: RenderErrorCollections) -> None:
    for section, errors in render_errors.items():
        errors_string = ""
        for error in errors:
            line = f"Line {error.line}: " if error.line else ""
            errors_string += f"\n\t- {line}{error.type} - {error.message}"
        error_count = len(errors)
        s = "s" if error_count > 1 else ""
        _log.warning(f"{error_count} error{s} occurred while rendering {section}:{errors_string}")
