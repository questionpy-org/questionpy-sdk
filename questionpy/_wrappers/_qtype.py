#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
import json
from collections.abc import Callable, Mapping
from functools import cached_property
from json import JSONDecodeError

from pydantic import JsonValue

from questionpy import Question
from questionpy._migration import MigrationQuestionStateWithVersion, Migrations, get_migrations
from questionpy._migration.errors import (
    MigrationFailedError,
    MigrationNotImplementedError,
    MigrationNotPossibleError,
    MigrationPackageMissmatchError,
    MigrationQuestionStateInvalidError,
    SpecificMigrationFailedError,
)
from questionpy._wrappers._question import QuestionWrapper
from questionpy.form.validation import validate_form
from questionpy_common.api.qtype import InvalidQuestionStateError, QuestionTypeInterface
from questionpy_common.api.question import QuestionInterface
from questionpy_common.elements import OptionsFormDefinition
from questionpy_common.environment import Package
from questionpy_common.manifest import PackageFile


def _get_migration_question_state(state: str) -> MigrationQuestionStateWithVersion:
    try:
        return MigrationQuestionStateWithVersion.model_validate_json(state)
    except Exception as e:
        raise MigrationQuestionStateInvalidError from e


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
        # A form may have unresolved references when it is intended to be used as a repetition, group, section, etc.
        # Only the complete form must pass validation, so the validation has to happen here instead of in FormModel or
        # OptionsFormDefinition.
        # We also can't do this in Question.__init_subclass__ since the type hint of options may be a forward reference.
        validate_form(question_class.options_class.qpy_form)

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

    @cached_property
    def migrations(self) -> Migrations:
        """Returns the possible migrations of this question type."""
        return get_migrations(self._package.manifest.namespace, self._package.manifest.short_name)

    def _migration_assert_same_package(self, state: MigrationQuestionStateWithVersion) -> None:
        if (
            state.package_namespace != self._package.manifest.namespace
            or state.package_short_name != self._package.manifest.short_name
        ):
            raise MigrationPackageMissmatchError(self._package, state)

    def upgrade(self, state: str) -> str:
        migration_state = _get_migration_question_state(state)
        self._migration_assert_same_package(migration_state)

        steps = self._package.manifest.state_version - migration_state.state_version
        if steps < 0:
            raise MigrationNotPossibleError

        for step, migration in enumerate(self.migrations.package[-steps:], start=1):
            try:
                migration(migration_state).upgrade()
                migration_state.state_version += 1
            except Exception as e:
                raise SpecificMigrationFailedError(
                    migration_state.state_version, migration_state.state_version + 1, step
                ) from e

        migration_state.package_version = self._package.manifest.version
        return migration_state.model_dump_json()

    def sidegrade(self, state: str) -> str:
        migration_state = _get_migration_question_state(state)

        if (
            (packages := self.migrations.side.get(migration_state.package_namespace))
            and (migrations := packages.get(migration_state.package_short_name))
            and (migration := migrations.get(migration_state.state_version))
        ):
            try:
                migration(migration_state).sidegrade()
            except MigrationNotPossibleError:
                raise
            except Exception as e:
                raise MigrationFailedError from e

            migration_state.package_namespace = self._package.manifest.namespace
            migration_state.package_short_name = self._package.manifest.short_name
            migration_state.package_version = self._package.manifest.version
            migration_state.state_version = self._package.manifest.state_version

            return migration_state.model_dump_json()

        raise MigrationNotImplementedError
