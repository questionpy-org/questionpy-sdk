#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import traceback

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from pydantic_core import ErrorDetails


class StateError(Exception):
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class MissingStateError(StateError):
    pass


class MissingQuestionStateError(MissingStateError):
    message = "The question state is missing."


class DuplicateQuestionError(StateError):
    message = "The question already exists."


class MissingOptionsFileError(MissingStateError):
    message = "An options file is missing."


class MissingAttemptStateError(MissingStateError):
    message = "The attempt state is missing."


class MissingAttemptSeedError(MissingStateError):
    message = "The attempt seed is missing."


class MissingAttemptScoreError(MissingStateError):
    message = "The attempt score is missing."


class MissingAttemptDataError(MissingStateError):
    message = "The attempt data is missing."


class DuplicateAttemptError(StateError):
    message = "The attempt already exists."


class EnvironmentVariablesMissingError(Exception):
    def __init__(self, missing: set[str]) -> None:
        self.missing = missing


@dataclass(config=ConfigDict(use_attribute_docstrings=True))
class DetailedServerError:
    """Represents a server-side error serialized for client display."""

    error: str
    """The name of the exception."""

    details: str | list[ErrorDetails] | None = None
    """Optional detailed error information, which may include a stack trace or Pydantic validation errors."""


def format_error(err: Exception) -> str:
    return "".join(traceback.format_exception(err))
