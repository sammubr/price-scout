from pathlib import Path

import pytest
from playwright.async_api import async_playwright

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
async def offline_page():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context(java_script_enabled=False)
        await context.route("**/*", lambda route: route.abort())
        page = await context.new_page()
        yield page
        await browser.close()


@pytest.fixture
def load_fixture(offline_page):
    async def load(name: str):
        await offline_page.set_content((FIXTURES / name).read_text(encoding="utf-8"))
        return offline_page

    return load
