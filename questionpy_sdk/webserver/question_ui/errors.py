#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import html
import logging
from abc import ABC, abstractmethod
from bisect import insort
from collections.abc import Iterable, Iterator, Sized
from dataclasses import dataclass
from functools import cached_property
from operator import attrgetter
from typing import TypeAlias

from lxml import etree

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenderError(ABC):
    """Represents a generic error which occurred during rendering."""

    @cached_property
    @abstractmethod
    def line(self) -> int | None:
        """Original line number where the error occurred or None if unknown."""

    @cached_property
    def order(self) -> int:
        """Can be used to order multiple errors."""
        return self.line or 0

    @cached_property
    @abstractmethod
    def message(self) -> str:
        pass

    @cached_property
    def html_message(self) -> str:
        return html.escape(self.message)


@dataclass(frozen=True)
class RenderElementError(RenderError, ABC):
    element: etree._Element

    @cached_property
    def element_representation(self) -> str:
        # Create the prefix of an element. We do not want to keep 'html' as a prefix.
        prefix = f"{self.element.prefix}:" if self.element.prefix and self.element.prefix != "html" else ""
        return prefix + etree.QName(self.element).localname

    @cached_property
    def line(self) -> int | None:
        """Original line number as found by the parser or None if unknown."""
        return self.element.sourceline  # type: ignore[return-value]


@dataclass(frozen=True)
class InvalidAttributeValueError(RenderElementError):
    """Invalid attribute value."""

    attribute: str
    value: str
    expected: Iterable[str] | None = None

    def _message(self, *, as_html: bool) -> str:
        if as_html:
            (opening, closing) = ("<code>", "</code>")
            value = html.escape(self.value)
        else:
            (opening, closing) = ("'", "'")
            value = self.value

        expected = ""
        if self.expected:
            expected = f" Expected one of [{opening}" + f"{closing}, {opening}".join(self.expected) + f"{closing}]."

        return (
            f"Invalid value {opening}{value}{closing} for attribute {opening}{self.attribute}{closing} "
            f"on element {opening}{self.element_representation}{closing}.{expected}"
        )

    @cached_property
    def message(self) -> str:
        return self._message(as_html=False)

    @cached_property
    def html_message(self) -> str:
        return self._message(as_html=True)


@dataclass(frozen=True)
class XMLSyntaxError(RenderError):
    """Syntax error while parsing the XML."""

    error: etree.XMLSyntaxError

    @cached_property
    def line(self) -> int | None:
        return self.error.lineno

    @cached_property
    def order(self) -> int:
        # Syntax errors can lead to a multitude of other errors therefore we want them to be the first in order.
        return -1

    @cached_property
    def message(self) -> str:
        return f"Syntax error: {self.error.msg}"

    @cached_property
    def html_message(self) -> str:
        return f"Invalid syntax: <samp>{html.escape(self.error.msg)}</samp>"


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
            errors_string += f"\n\t- {line}{error.message}"
        _log.warning(f"{len(errors)} error(s) occurred while rendering {section}:{errors_string}")
