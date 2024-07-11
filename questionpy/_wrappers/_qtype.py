#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json
from collections.abc import Callable, Mapping
from json import JSONDecodeError

from pydantic import JsonValue

from questionpy import Question
from questionpy._wrappers._question import QuestionWrapper
from questionpy_common.api.qtype import InvalidQuestionStateError, QuestionTypeInterface
from questionpy_common.api.question import QuestionInterface
from questionpy_common.elements import OptionsFormDefinition
from questionpy_common.environment import Package
from questionpy_common.manifest import PackageFile


class QuestionTypeWrapper(QuestionTypeInterface):
    def __init__(
        self,
        question_class: type[Question],
        package: Package,
        *,
        wrap_question: Callable[[Question], QuestionInterface] = QuestionWrapper,
    ) -> None:
        """Uses the given question class to provide the [QuestionTypeInterface][questionpy.QuestionTypeInterface].

        Args:
            question_class: Your question subclass.
            package: Package to retrieve metadata from, usually the one owning the question, which is passed to your
                     `init` function.
            wrap_question: Supplying a different question wrapper allows you to customize the question and attempt
                           functionality. This will probably, but not necessarily, be a subclass of the default
                           [QuestionWrapper][questionpy.QuestionWrapper].
        """
        self._question_class = question_class
        self._package = package

        self._wrap_question = wrap_question

    def _get_question_internal(self, json_state: str) -> Question:
        try:
            plain_state = json.loads(json_state)
        except JSONDecodeError as e:
            raise InvalidQuestionStateError from e

        return self._question_class.from_plain_state(plain_state)

    def get_options_form(self, question_state: str | None) -> tuple[OptionsFormDefinition, dict[str, JsonValue]]:
        if question_state is not None:
            question = self._get_question_internal(question_state)
            return question.get_options_form()

        return self._question_class.get_new_question_options_form(), {}

    def create_question_from_options(self, old_state: str | None, form_data: dict[str, JsonValue]) -> QuestionInterface:
        if old_state is None:
            question = self._question_class.new_from_options(form_data)
        else:
            old_question = self._get_question_internal(old_state)
            question = old_question.update_from_options(form_data)

        return self._wrap_question(question)

    def create_question_from_state(self, question_state: str) -> QuestionInterface:
        return self._wrap_question(self._get_question_internal(question_state))

    def get_static_files(self) -> Mapping[str, PackageFile]:
        return self._package.manifest.static_files
