import pytest
from playwright.sync_api import Browser, Error, Page
from ravelights import RaveLightsApp

BASE_URL = "http://localhost:80"


@pytest.fixture(scope="module")
def ui_page(browser: Browser) -> Page:
    app = RaveLightsApp()
    app.rest_api.start()

    page = browser.new_page(base_url=BASE_URL)
    page.on("pageerror", raise_exception)
    return page


@pytest.mark.playwright
def test_audio(ui_page: Page):
    ui_page.goto("http://localhost")


def raise_exception(exception_message: Error):
    raise Exception(exception_message.message)
