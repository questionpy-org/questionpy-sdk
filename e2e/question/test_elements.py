#  This file is part of the QuestionPy SDK. (https://questionpy.org)
#  The QuestionPy SDK is free software released under terms of the MIT license. See LICENSE.md.
#  (c) Technische Universität Berlin, innoCampus <info@isis.tu-berlin.de>

import pytest
from playwright.async_api import Page, expect

from questionpy import form


class RadioOptions(form.OptionEnum):
    FIRST = form.option("First option (radio)")
    SECOND = form.option("Second option (radio)")


class SelectOptions(form.OptionEnum):
    FIRST = form.option("First option (select)")
    SECOND = form.option("Second option (select)")


class GroupModel(form.FormModel):
    text_input: str | None = form.text_input("TextInput label (group)")


class RepeatModel(form.FormModel):
    text_input: str | None = form.text_input("TextInput label (repeat)")


class SectionModel(form.FormModel):
    text_input: str | None = form.text_input("TextInput label (section)")


class PackageForm(form.FormModel):
    checkbox: bool = form.checkbox("Checkbox label", "Checkbox right label", help="Checkbox help")
    file_upload: list[form.OptionsFile] = form.file_upload("FileUpload label", help="FileUpload help")
    generated_id: str = form.generated_id()
    group: GroupModel = form.group("Group label", GroupModel, help="Group help")
    hidden: str = form.hidden("hidden value")
    radio_group: RadioOptions | None = form.radio_group("RadioGroup label", RadioOptions, help="RadioGroup help")
    repeat: list[RepeatModel] = form.repeat(RepeatModel)
    rich_text_editor: form.RichTextEditor = form.rich_text_editor("RichTextEditor label", help="RichTextEditor help")
    section: SectionModel = form.section("Section header", SectionModel)
    select: SelectOptions | None = form.select("Select label", SelectOptions, help="Select help")
    static_text: form.StaticTextElement = form.static_text(
        "StaticText label", "StaticText text", help="StaticText help"
    )
    text_area: str | None = form.text_area("TextArea label", help="TextArea help")
    text_input: str = form.text_input("TextInput label", required=True, help="TextInput help")


@pytest.fixture
def form_options() -> type[form.FormModel]:
    return PackageForm


async def _assert_page_state(page: Page) -> None:
    await expect(page.get_by_text("Edit question")).to_be_visible()
    await expect(page.get_by_role("button", name="Save", exact=True)).to_be_disabled()
    await expect(page.get_by_role("button", name="Save and return", exact=True)).to_be_disabled()
    await expect(page.get_by_role("button", name="Preview", exact=True)).to_be_enabled()
    await expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_enabled()

    await expect(page.get_by_label("Checkbox right label", exact=True)).to_be_checked()
    await expect(page.get_by_text("file.txt", exact=True)).to_be_visible()  # FileUpload thumbnail
    await expect(page.get_by_label("TextInput label (group)", exact=True)).to_have_value("TextInput (group) filled")
    await expect(page.get_by_label("Second option (radio)", exact=True)).to_be_checked()
    await expect(page.get_by_label("TextInput label (repeat)", exact=True)).to_have_count(2)
    await expect(page.get_by_label("TextInput label (repeat)", exact=True).nth(0)).to_have_value(
        "TextInput (repeat) filled 0"
    )
    await expect(page.get_by_label("TextInput label (repeat)", exact=True).nth(1)).to_have_value(
        "TextInput (repeat) filled 2"
    )
    editor_iframe = page.frame_locator(".tox iframe")
    await expect(editor_iframe.locator("body")).to_have_text("RichTextEditor filled")
    option_text = await page.get_by_label("Select label", exact=True).locator("option:checked").inner_text()
    assert option_text == "Second option (select)"
    await expect(page.get_by_label("TextArea label", exact=True)).to_have_value("TextArea filled")
    await expect(page.get_by_label("TextInput label", exact=True)).to_have_value("TextInput filled")
    await expect(page.get_by_label("TextInput label (section)", exact=True)).to_have_value("TextInput (section) filled")


async def test_elements(page: Page) -> None:
    await page.get_by_role("button", name="New question", exact=True).click()
    await expect(page.get_by_text("Create question")).to_be_visible()
    await expect(page.get_by_role("button", name="Create", exact=True)).to_be_enabled()
    await expect(page.get_by_role("button", name="Create and return", exact=True)).to_be_enabled()
    await expect(page.get_by_role("button", name="Create and preview", exact=True)).to_be_enabled()
    await expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_enabled()

    # Checkbox
    await expect(page.get_by_text("Checkbox label", exact=True)).to_be_visible()
    await expect(page.get_by_text("Checkbox help", exact=True)).to_be_visible()
    await page.get_by_label("Checkbox right label", exact=True).check()

    # FileUpload
    await expect(page.get_by_text("FileUpload label", exact=True)).to_be_visible()
    await expect(page.get_by_text("FileUpload help", exact=True)).to_be_visible()
    await page.locator("input[type='file']").set_input_files({
        "name": "file.txt",
        "mimeType": "text/plain",
        "buffer": b"file content",
    })
    await expect(page.get_by_text("file.txt", exact=True)).to_be_visible()  # thumbnail

    # Group
    await expect(page.get_by_text("Group label", exact=True)).to_be_visible()
    await expect(page.get_by_text("Group help", exact=True)).to_be_visible()
    await expect(page.get_by_text("TextInput label (group)", exact=True)).to_be_visible()
    await page.get_by_label("TextInput label (group)", exact=True).fill("TextInput (group) filled")

    # RadioGroup
    await expect(page.get_by_text("RadioGroup help", exact=True)).to_be_visible()
    await expect(page.get_by_text("RadioGroup label", exact=True)).to_be_visible()
    await expect(page.get_by_label("First option (radio)", exact=True)).to_be_visible()
    await page.get_by_label("Second option (radio)", exact=True).check()

    # Repeat
    await page.get_by_label("TextInput label (repeat)", exact=True).fill("TextInput (repeat) filled 0")
    await expect(page.get_by_role("button", name="Remove", exact=True)).to_be_disabled()
    await page.get_by_role("button", name="Add repetition", exact=True).click()
    await page.get_by_label("TextInput label (repeat)", exact=True).nth(1).fill("TextInput (repeat) filled 1")
    await page.get_by_role("button", name="Add repetition", exact=True).click()
    await page.get_by_label("TextInput label (repeat)", exact=True).nth(2).fill("TextInput (repeat) filled 2")
    await page.get_by_role("button", name="Remove", exact=True).nth(1).click()
    await expect(page.get_by_label("TextInput label (repeat)", exact=True)).to_have_count(2)
    await expect(page.locator("input[value='TextInput (repeat) filled 0']")).to_have_count(1)
    await expect(page.locator("input[value='TextInput (repeat) filled 1']")).to_have_count(0)
    await expect(page.locator("input[value='TextInput (repeat) filled 2']")).to_have_count(1)

    # RichTextEditor
    await expect(page.get_by_text("RichTextEditor label", exact=True)).to_be_visible()
    await expect(page.get_by_text("RichTextEditor help", exact=True)).to_be_visible()
    editor_iframe = page.frame_locator(".tox iframe")
    await editor_iframe.locator("body").fill("RichTextEditor filled")

    # Select
    await expect(page.get_by_text("Select help", exact=True)).to_be_visible()
    await page.get_by_label("Select label", exact=True).select_option("Second option (select)")

    # StaticText
    await expect(page.get_by_text("StaticText label", exact=True)).to_be_visible()
    await expect(page.get_by_text("StaticText text", exact=True)).to_be_visible()
    await expect(page.get_by_text("StaticText help", exact=True)).to_be_visible()

    # TextArea
    await page.get_by_label("TextArea label", exact=True).fill("TextArea filled")
    await expect(page.get_by_text("TextArea help", exact=True)).to_be_visible()

    # TextInput
    await page.get_by_label("TextInput label", exact=True).fill("TextInput filled")
    await expect(page.get_by_text("TextInput help", exact=True)).to_be_visible()

    # Section
    await expect(page.get_by_text("Section header", exact=True)).to_be_visible()
    await page.get_by_label("TextInput label (section)", exact=True).fill("TextInput (section) filled")

    # Create question and assert data
    await page.get_by_role("button", name="Create", exact=True).click()
    await _assert_page_state(page)

    # Assert state is restored after page reload
    await page.reload()
    await _assert_page_state(page)
