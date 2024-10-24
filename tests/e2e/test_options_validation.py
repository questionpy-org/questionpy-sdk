import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from questionpy import Package, QuestionTypeWrapper
from questionpy.form import FormModel, checkbox, group, repeat, section
from questionpy_common.api.qtype import QuestionTypeInterface

from .conftest import _NoopQuestion, use_package


def package_init(package: Package) -> QuestionTypeInterface:
    class Group(FormModel):
        checkbox: bool = checkbox("Checkbox", required=True)

    class Repetition(FormModel):
        group: Group = group("Group", Group)

    class PackageForm(FormModel):
        checkbox: bool = checkbox("Checkbox", required=True)
        repetition: list[Repetition] = repeat(Repetition)
        group: Group = group("Group", Group)
        section: Group = section("Section", Group)

    class PackageQuestion(_NoopQuestion):
        options: PackageForm

    return QuestionTypeWrapper(PackageQuestion, package)


def assert_hidden(driver: webdriver.Chrome, selector: str) -> None:
    assert not driver.find_element(By.CSS_SELECTOR, f"{selector} .errors").is_displayed()


def await_and_assert_msg(driver: webdriver.Chrome, selector: str) -> None:
    msg_selector = f"{selector} .errors"
    el_error = WebDriverWait(driver, 5).until(ec.visibility_of_element_located((By.CSS_SELECTOR, msg_selector)))
    assert el_error.text == "Field required"


@pytest.mark.usefixtures("_start_runner_thread")
@use_package(package_init)
def test_shows_validation_errors(driver: webdriver.Chrome, url: str) -> None:
    driver.get(url)

    # Assert error messages are hidden.
    assert_hidden(driver, "#general_checkbox")
    assert_hidden(driver, "#general_repetition #general_repetition_1_group")
    assert_hidden(driver, "#general_group #general_group_checkbox")
    assert_hidden(driver, "#section #section_checkbox")

    # Submit form.
    driver.find_element(By.ID, "submit-options-button").click()

    # Assert error messages are shown.
    await_and_assert_msg(driver, "#general_checkbox")
    await_and_assert_msg(driver, "#general_repetition #general_repetition_1_group")
    await_and_assert_msg(driver, "#general_group #general_group_checkbox")
    await_and_assert_msg(driver, "#section #section_checkbox")
