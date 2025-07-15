import re

from playwright.async_api import Page, expect


async def test_package(page: Page) -> None:
    await expect(page).to_have_title(re.compile(r"QuestionPy SDK"))
    await expect(page.get_by_text("e2e_conftest/default_init")).to_be_visible()
    await expect(page.get_by_text("0.1.0-debug")).to_be_visible()
    await expect(page.get_by_text("Debug Modulovitch")).to_be_visible()

    await page.get_by_role("button", name="New question").click()
    await page.get_by_role("textbox", name="Static text label").fill("foo bar")
    await page.get_by_role("button", name="Create and preview").click()

    await expect(page).to_have_title(re.compile(r"Question Preview"))
    await page.get_by_role("button", name="New attempt").click()
    await expect(page.frame_locator("iframe").get_by_text("Formulation text")).to_be_visible()
