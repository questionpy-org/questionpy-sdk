#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

from typing import Any, cast

import pytest
from playwright.async_api import Page, expect

from questionpy import Attempt, form

FORMULATION = """
<div xmlns="http://www.w3.org/1999/xhtml"
     xmlns:qpy="http://questionpy.org/ns/question">
    <fieldset qpy:shuffle-contents="">
        <legend><?p question ?></legend>
        {% for choice in question.options.choices %}
            <div>
                <label>
                    <input type="checkbox" name="{{ choice.id }}" />
                    {{ choice.label }}
                </label>
            </div>
        {% endfor %}
    </fieldset>
</div>
"""


class ChoiceModel(form.FormModel):
    id: str = form.generated_id()
    label: str = form.text_input("Option", required=True)
    is_correct: bool = form.checkbox(right_label="Correct answer")


class DynamicChoicesFormModel(form.FormModel):
    question_text: str = form.text_input("Question", required=True)
    choices: list[ChoiceModel] = form.repeat(ChoiceModel, button_label="Add option", minimum=2)


class DynamicChoicesAttempt(Attempt):
    def __init__(self, *args: Any):
        super().__init__(*args)

        self.placeholders["question"] = self.options.question_text

    def _compute_score(self) -> float:
        assert self.response
        chosen_ids = {k for k, v in self.response.items() if v == "on"}
        correct_ids = {choice.id for choice in self.options.choices if choice.is_correct}
        total_correct = len(correct_ids)
        num_correct_chosen = len(correct_ids & chosen_ids)
        return num_correct_chosen / total_correct if total_correct > 0 else 0.0

    @property
    def formulation(self) -> str:
        return self.jinja2.from_string(FORMULATION).render()

    @property
    def options(self) -> DynamicChoicesFormModel:
        return cast("DynamicChoicesFormModel", self.question.options)


@pytest.fixture
def form_options() -> type[form.FormModel]:
    return DynamicChoicesFormModel


@pytest.fixture
def attempt() -> type[Attempt]:
    return DynamicChoicesAttempt


async def test_dynamic_choices(page: Page) -> None:
    # Create question
    await page.get_by_role("button", name="New question", exact=True).click()
    await page.get_by_label("Question", exact=True).fill("Best programming languages?")
    await page.get_by_label("Option", exact=True).nth(0).fill("Python")
    await page.get_by_label("Correct answer", exact=True).nth(0).check()
    await page.get_by_label("Option", exact=True).nth(1).fill("Java")
    await page.get_by_role("button", name="Add option", exact=True).click()
    await page.get_by_label("Option", exact=True).nth(2).fill("Swift")
    await page.get_by_role("button", name="Add option", exact=True).click()
    await page.get_by_label("Option", exact=True).nth(3).fill("Rust")
    await page.get_by_label("Correct answer", exact=True).nth(3).check()
    await page.get_by_role("button", name="Create and preview", exact=True).click()

    # 1st Attempt
    await page.get_by_role("button", name="New attempt", exact=True).click()
    await expect(page.get_by_text("Not yet scored", exact=True)).to_be_visible()
    formulation = page.frame_locator("iframe")
    await expect(formulation.get_by_text("Best programming languages?")).to_be_visible()
    await formulation.get_by_label("Java", exact=True).check()
    await page.get_by_role("button", name="Save and submit", exact=True).click()
    await expect(page.get_by_text("Score: 0.0", exact=True)).to_be_visible()

    # 2nd Attempt
    await page.get_by_role("button", name="Restart", exact=True).click()
    await expect(page.get_by_text("Not yet scored", exact=True)).to_be_visible()
    await formulation.get_by_label("Python", exact=True).check()
    await page.get_by_role("button", name="Save and submit", exact=True).click()
    await expect(page.get_by_text("Score: 0.5", exact=True)).to_be_visible()

    # 3rd Attempt
    await page.get_by_role("button", name="Restart", exact=True).click()
    await expect(page.get_by_text("Not yet scored", exact=True)).to_be_visible()
    await formulation.get_by_label("Python", exact=True).check()
    await formulation.get_by_label("Rust", exact=True).check()
    await page.get_by_role("button", name="Save and submit", exact=True).click()
    await expect(page.get_by_text("Score: 1.0", exact=True)).to_be_visible()
