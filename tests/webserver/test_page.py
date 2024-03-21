#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>
from collections.abc import Callable
from typing import Any, TypeVar, cast

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from questionpy import Attempt, Question, QuestionType
from questionpy.form import FormModel, checkbox, repeat
from questionpy_common.api.attempt import AttemptUi, ScoreModel, ScoringCode
from questionpy_common.api.qtype import BaseQuestionType
from questionpy_common.api.question import QuestionModel, ScoringMethod
from questionpy_common.environment import PackageInitFunction
from questionpy_common.manifest import Manifest
from questionpy_server.worker.runtime.package_location import FunctionPackageLocation


class _NoopAttempt(Attempt):
    def export_score(self) -> ScoreModel:
        return ScoreModel(scoring_code=ScoringCode.NEEDS_MANUAL_SCORING, score=None)

    def render_formulation(self) -> AttemptUi:
        return AttemptUi(content="")


class _NoopQuestion(Question):
    attempt_class = _NoopAttempt

    def export(self) -> QuestionModel:
        return QuestionModel(scoring_method=ScoringMethod.AUTOMATICALLY_SCORABLE)


def package_1_init() -> BaseQuestionType:
    class Package1Form(FormModel):
        optional_checkbox: bool = checkbox("Optional Checkbox")

    return QuestionType(Package1Form, _NoopQuestion)


def package_2_init() -> BaseQuestionType:
    class Package2Form(FormModel):
        required_checkbox: bool = checkbox("Required Checkbox", required=True)

    return QuestionType(Package2Form, _NoopQuestion)


def package_3_init() -> BaseQuestionType:
    class SubModel(FormModel):
        optional_checkbox: bool = checkbox("Optional Checkbox { qpy:repno }")

    class Package3Form(FormModel):
        repetition: list[SubModel] = repeat(SubModel, initial=2, increment=3)

    return QuestionType(Package3Form, _NoopQuestion)


_C = TypeVar("_C", bound=Callable)


def use_package(init_fun: PackageInitFunction, manifest: Manifest | None = None) -> Callable[[_C], _C]:
    def decorator(wrapped: _C) -> _C:
        cast(Any, wrapped).qpy_package_location = FunctionPackageLocation.from_function(init_fun, manifest)
        return wrapped

    return decorator


@pytest.mark.usefixtures("_start_runner_thread")
class TestTemplates:
    @use_package(package_1_init)
    def test_page_contains_correct_page_title(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)
        assert "QPy Webserver" in driver.title

    @use_package(package_1_init)
    def test_form_without_required_fields_should_submit(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)
        driver.find_element(By.ID, "submit-options-button").click()

        assert driver.find_element(By.ID, "submit_success_info").is_displayed()

    @use_package(package_2_init)
    def test_form_with_required_fields_should_not_submit(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)
        driver.find_element(By.ID, "submit-options-button").click()

        WebDriverWait(driver, 1).until(expected_conditions.alert_is_present())
        assert driver.switch_to.alert

    @use_package(package_3_init)
    def test_repeat_element_if_present(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)

        repetition_element = driver.find_element(By.NAME, "general[repetition]")

        # Initially, there should be 2 reps.
        assert len(repetition_element.find_elements(By.CLASS_NAME, "repetition-content")) == 2

        repetition_element.find_element(By.CLASS_NAME, "repetition-button").click()
        WebDriverWait(driver, 2).until(expected_conditions.staleness_of(repetition_element))
        repetition_element = driver.find_element(By.NAME, "general[repetition]")

        # After clicking increment once, there should be 5.
        assert len(repetition_element.find_elements(By.CLASS_NAME, "repetition-content")) == 5

    @use_package(
        package_1_init,
        manifest=Manifest(short_name="my_short_name", version="7.3.1", api_version="9.4", author="Testy McTestface"),
    )
    def test_page_contains_correct_manifest_information(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)

        assert driver.title.startswith("my_short_name")
        assert "my_short_name" in driver.find_element(By.CLASS_NAME, "header").find_element(By.TAG_NAME, "h1").text
        assert "7.3.1" in driver.find_element(By.CLASS_NAME, "manifest-version").text
        assert "9.4" in driver.find_element(By.CLASS_NAME, "manifest-apiversion").text
