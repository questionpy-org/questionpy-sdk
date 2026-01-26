#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import pytest
from playwright.async_api import Page, expect

from questionpy import form


class RepeatModel(form.FormModel):
    checkbox_a: bool = form.checkbox("Checkbox A", "Disable TextInput A")
    text_input_a: str | None = form.text_input("TextInput A", disable_if=form.is_checked("checkbox_a"))
    text_input_b: str | None = form.text_input("TextInput B", disable_if=form.is_checked("..[checkbox_3]"))


class GroupModel(form.FormModel):
    checkbox_b: bool = form.checkbox("Checkbox B", "Disable TextInput 3 (group)")
    checkbox_c: bool = form.checkbox("Checkbox C", "Disable TextInput C")
    text_input_c: str | None = form.text_input("TextInput C", disable_if=form.is_checked("checkbox_c"))
    text_input_d: str | None = form.text_input("TextInput D", disable_if=form.is_checked("..[checkbox_4]"))


class SectionModel(form.FormModel):
    checkbox_d: bool = form.checkbox("Checkbox D", "Disable TextInput 3 (section)")
    checkbox_e: bool = form.checkbox("Checkbox E", "Disable TextInput E")
    text_input_e: str | None = form.text_input("TextInput E", disable_if=form.is_checked("checkbox_e"))
    text_input_f: str | None = form.text_input("TextInput F", disable_if=form.is_checked("..[checkbox_5]"))


class PackageForm(form.FormModel):
    checkbox_1: bool = form.checkbox("Checkbox 1", "Disable TextInput 1")
    text_input_1: str | None = form.text_input("TextInput 1", disable_if=form.is_checked("checkbox_1"))

    checkbox_2: bool = form.checkbox("Checkbox 2", "Hide TextInput 2")
    text_input_2: str | None = form.text_input("TextInput 2", hide_if=form.is_checked("checkbox_2"))

    checkbox_3: bool = form.checkbox("Checkbox 3", "Disable TextInput B")
    checkbox_4: bool = form.checkbox("Checkbox 4", "Disable TextInput D")
    checkbox_5: bool = form.checkbox("Checkbox 5", "Disable TextInput F")
    text_input_3: str | None = form.text_input(
        "TextInput 3", disable_if=[form.is_checked("group[checkbox_b]"), form.is_checked("section[checkbox_d]")]
    )

    repeat: list[RepeatModel] = form.repeat(RepeatModel, minimum=2)
    checkbox_disable_group: bool = form.checkbox("Checkbox Disable Group", "Disable Group")
    checkbox_hide_group: bool = form.checkbox("Checkbox Hide Group", "Hide Group")
    group: GroupModel = form.group(
        "Group",
        GroupModel,
        disable_if=form.is_checked("checkbox_disable_group"),
        hide_if=form.is_checked("checkbox_hide_group"),
    )
    section: SectionModel = form.section("Section", SectionModel)

    checkbox_6: bool = form.checkbox("Checkbox 6", "Enable TextInput 4")
    text_input_4: str | None = form.text_input("TextInput 4", disable_if=form.is_not_checked("checkbox_6"))

    text_input_equals: str | None = form.text_input("TextInput (equals)")
    text_input_5: str | None = form.text_input(
        "TextInput 5", disable_if=form.equals("text_input_equals", value="foo bar")
    )

    text_input_does_not_equal: str | None = form.text_input("TextInput (does_not_equal)")
    text_input_6: str | None = form.text_input(
        "TextInput 6", disable_if=form.does_not_equal("text_input_does_not_equal", value="foo bar")
    )

    text_input_is_in: str | None = form.text_input("TextInput (is_in)")
    text_input_7: str | None = form.text_input(
        "TextInput 7", disable_if=form.is_in("text_input_is_in", values=["foo", "bar"])
    )


@pytest.fixture
def form_options() -> type[form.FormModel]:
    return PackageForm


async def test_conditions_root(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()

    # Disable within root
    await expect(page.get_by_text("TextInput 1", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput 1", exact=True).check()
    await expect(page.get_by_text("TextInput 1", exact=True)).to_be_disabled()

    # Hide within root
    await expect(page.get_by_text("TextInput 2", exact=True)).to_be_visible()
    await page.get_by_label("Hide TextInput 2", exact=True).check()
    await expect(page.get_by_text("TextInput 2", exact=True)).to_be_hidden()


async def test_conditions_repetition(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()

    # Disable within repetition
    await expect(page.get_by_label("TextInput A", exact=True)).to_have_count(2)
    await expect(page.get_by_label("TextInput A", exact=True).nth(0)).to_be_enabled()
    await expect(page.get_by_label("TextInput A", exact=True).nth(1)).to_be_enabled()
    await page.get_by_label("Disable TextInput A", exact=True).nth(0).check()
    await expect(page.get_by_label("TextInput A", exact=True).nth(0)).to_be_disabled()
    await expect(page.get_by_label("TextInput A", exact=True).nth(1)).to_be_enabled()
    await page.get_by_label("Disable TextInput A", exact=True).nth(1).check()
    await expect(page.get_by_label("TextInput A", exact=True).nth(0)).to_be_disabled()
    await expect(page.get_by_label("TextInput A", exact=True).nth(1)).to_be_disabled()

    # Disable in repetition
    await expect(page.get_by_label("TextInput B", exact=True)).to_have_count(2)
    await expect(page.get_by_label("TextInput B", exact=True).nth(0)).to_be_enabled()
    await expect(page.get_by_label("TextInput B", exact=True).nth(1)).to_be_enabled()
    await page.get_by_label("Disable TextInput B", exact=True).check()
    await expect(page.get_by_label("TextInput B", exact=True).nth(0)).to_be_disabled()
    await expect(page.get_by_label("TextInput B", exact=True).nth(1)).to_be_disabled()

    # Note: Disable from repetition is not supported


async def test_conditions_group(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()

    # Disable within group
    await expect(page.get_by_text("TextInput C", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput C", exact=True).check()
    await expect(page.get_by_text("TextInput C", exact=True)).to_be_disabled()

    # Disable in group
    await expect(page.get_by_text("TextInput D", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput D", exact=True).check()
    await expect(page.get_by_text("TextInput D", exact=True)).to_be_disabled()

    # Disable from group
    await expect(page.get_by_text("TextInput 3", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput 3 (group)", exact=True).check()
    await expect(page.get_by_text("TextInput 3", exact=True)).to_be_disabled()
    await page.get_by_label("Disable TextInput 3 (group)", exact=True).uncheck()

    # Disable group
    await page.get_by_label("Disable Group", exact=True).check()
    await expect(page.get_by_text("Disable TextInput 3 (group)", exact=True)).to_be_disabled()
    await expect(page.get_by_text("Disable TextInput C", exact=True)).to_be_disabled()
    await expect(page.get_by_text("TextInput C", exact=True)).to_be_disabled()
    await expect(page.get_by_text("TextInput D", exact=True)).to_be_disabled()
    await page.get_by_label("Disable Group", exact=True).uncheck()

    # Hide group
    await expect(page.get_by_text("Group", exact=True)).to_be_visible()
    await page.get_by_label("Hide Group", exact=True).check()
    await expect(page.get_by_text("Group", exact=True)).to_be_hidden()
    await expect(page.get_by_text("Checkbox B", exact=True)).to_be_hidden()
    await expect(page.get_by_text("Checkbox C", exact=True)).to_be_hidden()
    await expect(page.get_by_text("TextInput C", exact=True)).to_be_hidden()
    await expect(page.get_by_text("TextInput D", exact=True)).to_be_hidden()


async def test_conditions_section(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()

    # Disable within section
    await expect(page.get_by_text("TextInput E", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput E", exact=True).check()
    await expect(page.get_by_text("TextInput E", exact=True)).to_be_disabled()

    # Disable in section
    await expect(page.get_by_text("TextInput F", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput F", exact=True).check()
    await expect(page.get_by_text("TextInput F", exact=True)).to_be_disabled()

    # Disable from section
    await expect(page.get_by_text("TextInput 3", exact=True)).to_be_enabled()
    await page.get_by_label("Disable TextInput 3 (section)", exact=True).check()
    await expect(page.get_by_text("TextInput 3", exact=True)).to_be_disabled()


async def test_conditions_variants(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()

    # disable_if
    await expect(page.get_by_text("TextInput 4", exact=True)).to_be_disabled()
    await page.get_by_label("Enable TextInput 4", exact=True).check()
    await expect(page.get_by_text("TextInput 4", exact=True)).to_be_enabled()

    # equals
    await expect(page.get_by_text("TextInput 5", exact=True)).to_be_enabled()
    await page.get_by_text("TextInput (equals)", exact=True).fill("foo")
    await expect(page.get_by_text("TextInput 5", exact=True)).to_be_enabled()
    await page.get_by_text("TextInput (equals)", exact=True).fill("foo bar")
    await expect(page.get_by_text("TextInput 5", exact=True)).to_be_disabled()

    # does_not_equal
    await expect(page.get_by_text("TextInput 6", exact=True)).to_be_disabled()
    await page.get_by_text("TextInput (does_not_equal)", exact=True).fill("foo")
    await expect(page.get_by_text("TextInput 6", exact=True)).to_be_disabled()
    await page.get_by_text("TextInput (does_not_equal)", exact=True).fill("foo bar")
    await expect(page.get_by_text("TextInput 6", exact=True)).to_be_enabled()

    # is_in
    await expect(page.get_by_text("TextInput 7", exact=True)).to_be_enabled()
    await page.get_by_text("TextInput (is_in)", exact=True).fill("foo")
    await expect(page.get_by_text("TextInput 7", exact=True)).to_be_disabled()
    await page.get_by_text("TextInput (is_in)", exact=True).fill("foo bar")
    await expect(page.get_by_text("TextInput 7", exact=True)).to_be_enabled()
    await page.get_by_text("TextInput (is_in)", exact=True).fill("bar")
    await expect(page.get_by_text("TextInput 7", exact=True)).to_be_disabled()
    await page.get_by_text("TextInput (is_in)", exact=True).fill("baz")
    await expect(page.get_by_text("TextInput 7", exact=True)).to_be_enabled()
