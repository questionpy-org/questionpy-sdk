#  This file is part of the QuestionPy Server. (https://questionpy.org)
#  The QuestionPy Server is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from questionpy_common.manifest import Manifest


@pytest.mark.usefixtures('start_runner_thread')
class TestTemplates:

    def test_page_contains_correct_page_title(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)
        assert "QPy Webserver" in driver.title

    def test_submit_without_form_content(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)
        elements = driver.find_elements(By.CLASS_NAME, 'content')

        contains_required = False
        for element in elements:
            required_elements = element.find_elements(By.CSS_SELECTOR, 'required')
            if required_elements:
                contains_required = True

        driver.find_element(By.ID, 'options_form').submit()

        hidden = driver.find_element(By.ID, 'submit_success_info').get_property('hidden')
        assert hidden == contains_required  # If there are required elements, the success info should remain hidden.

    def test_repeat_element_if_present(self, driver: webdriver.Chrome, url: str) -> None:
        driver.get(url)

        repetition_elements = driver.find_elements(By.CLASS_NAME, 'repetition')

        for repetition_element in repetition_elements:
            repetition_element_id = repetition_element.get_attribute('id')
            initial_repetitions = len(repetition_element.find_elements(By.CLASS_NAME, 'repetition-content'))
            button = repetition_element.find_element(By.CLASS_NAME, 'repetition-button')
            increment_attribute = button.get_attribute('data-repetition_increment')

            wait = WebDriverWait(driver, timeout=2)
            button.click()
            wait.until(lambda _: repetition_element.is_displayed())

            driver.get(url)

            final_repetitions = len(driver.find_element(
                By.ID, repetition_element_id).find_elements(By.CLASS_NAME, 'repetition-content'))

            assert initial_repetitions > 0
            assert increment_attribute is not None
            assert final_repetitions - initial_repetitions == int(increment_attribute)

    def test_page_contains_correct_manifest_information(self, driver: webdriver.Chrome, url: str, manifest: Manifest) \
            -> None:
        driver.get(url)

        assert driver.title.startswith(manifest.short_name)
        assert manifest.short_name in driver.find_element(By.CLASS_NAME, 'header').find_element(By.TAG_NAME, 'h1').text
        assert manifest.version in driver.find_element(By.CLASS_NAME, 'manifest-version').text
        assert manifest.api_version in driver.find_element(By.CLASS_NAME, 'manifest-apiversion').text
