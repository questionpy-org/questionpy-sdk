#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import Generator
from types import SimpleNamespace
from typing import cast

import pytest

from questionpy import Attempt, BaseAttemptState, BaseQuestionState, Question
from questionpy.form import FormModel, text_input
from questionpy_common.environment import Environment, RequestUser, set_qpy_environment
from questionpy_common.manifest import Manifest, PackageFile
from questionpy_server.worker.runtime.manager import EnvironmentImpl
from questionpy_server.worker.runtime.package import ImportablePackage

STATIC_FILES = {
    "css/my-styles.css": PackageFile(mime_type="text/css", size=42),
    "js/main.js": PackageFile(mime_type="text/javascript", size=534),
    "static/logo.svg": PackageFile(mime_type="image/svg+xml", size=1253),
}


@pytest.fixture
def package() -> ImportablePackage:
    return cast(
        ImportablePackage,
        SimpleNamespace(
            manifest=Manifest(
                namespace="test_ns",
                short_name="test_package",
                version="1.2.3",
                author="Testy McTestface",
                api_version="0.3",
                languages={"en"},
                static_files=STATIC_FILES,
            )
        ),
    )


@pytest.fixture(autouse=True)
def environment(package: ImportablePackage) -> Generator[Environment, None, None]:
    env = EnvironmentImpl(
        type="test",
        limits=None,
        request_user=RequestUser(["en"]),
        main_package=package,
        packages={},
        _on_request_callbacks=[],
    )
    set_qpy_environment(env)
    try:
        yield env
    finally:
        set_qpy_environment(None)


class SomeModel(FormModel):
    input: str | None = text_input("Some Label")


class MyQuestionState(BaseQuestionState):
    my_question_field: int = 42


class MyAttemptState(BaseAttemptState):
    my_attempt_field: int = 17


class SomeAttempt(Attempt):
    attempt_state: MyAttemptState

    formulation = ""

    def _compute_score(self) -> float:
        return 1


class QuestionUsingDefaultState(Question):
    attempt_class = SomeAttempt

    options: SomeModel


class QuestionUsingMyQuestionState(Question):
    attempt_class = SomeAttempt

    question_state: MyQuestionState
    options: SomeModel


QUESTION_STATE_DICT = {
    "package_name": "test_ns.test_package",
    "package_version": "1.2.3",
    "options": {"input": "something"},
    "state": {
        "my_question_field": 42,
    },
}

ATTEMPT_STATE_DICT = {
    "variant": 3,
    "my_attempt_field": 17,
}
