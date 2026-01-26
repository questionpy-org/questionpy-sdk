#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from pydantic import BaseModel, JsonValue


class MigrationQuestionStateWithVersion(BaseModel):
    package_namespace: str
    package_short_name: str
    package_version: str
    options: dict[str, JsonValue]
    state: dict[str, JsonValue]
    state_version: int


class BaseMigration:
    _state: MigrationQuestionStateWithVersion

    def __init__(self, state: MigrationQuestionStateWithVersion):
        self._state = state

    @property
    def state(self) -> dict[str, JsonValue]:
        return self._state.state

    @property
    def options(self) -> dict[str, JsonValue]:
        return self._state.options
