"""Required browser tests against an externally running, disposable staging image."""

import os
import re
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright

BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")
ARTIFACT_DIR = Path(os.environ.get("E2E_ARTIFACT_DIR", "/tmp/wedding-e2e-results"))


@unittest.skipUnless(BASE_URL, "Set E2E_BASE_URL to run the staging suite")
class TestStaging(unittest.TestCase):
    """Exercise the delivered image without importing or starting the app."""

    playwright: Playwright
    browser: Browser
    page: Page
    password: str

    @classmethod
    def setUpClass(cls) -> None:
        """Require credentials and Chromium whenever staging tests are requested."""
        cls.password = os.environ["E2E_ADMIN_PASSWORD"]
        browser_name = os.environ.get("E2E_BROWSER", "chromium")
        if browser_name not in {"chromium", "firefox", "webkit"}:
            raise ValueError(f"Unsupported E2E_BROWSER: {browser_name}")
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = getattr(cls.playwright, browser_name).launch()
        cls.addClassCleanup(cls.browser.close)
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    def setUp(self) -> None:
        """Give each test a fresh unauthenticated browser context."""
        self.context = self.browser.new_context(base_url=BASE_URL, viewport={"width": 1440, "height": 900})
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()

    def tearDown(self) -> None:
        """Retain the final browser state even when an assertion fails."""
        self.page.screenshot(path=str(ARTIFACT_DIR / f"{self._testMethodName}.png"), full_page=True)

    def test_navigation(self) -> None:
        """Follow the public navigation and verify each destination renders."""
        response = self.page.goto("/")
        assert response is not None
        self.assertEqual(response.status, 200)
        for label, path in (("OSA", "/rsvp"), ("Schema", "/itinerary"), ("Bordsplacering", "/seating")):
            self.page.locator("#navbar").get_by_role("link", name=label, exact=True).click()
            expect(self.page).to_have_url(re.compile(re.escape(BASE_URL + path) + r"/?$"))
            expect(self.page.locator("main h1")).to_be_visible()
        self.page.get_by_role("link", name="Kontakta oss", exact=True).click()
        expect(self.page).to_have_url(re.compile(re.escape(BASE_URL + "/contact") + r"/?$"))
        expect(self.page.locator("main h1")).to_be_visible()

    def test_mobile_layout(self) -> None:
        """Check phone-to-desktop overflow and exercise the mobile menu."""
        for width in (320, 375, 768, 1440):
            self.page.set_viewport_size({"width": width, "height": 900})
            for path in ("/", "/rsvp/", "/itinerary/", "/seating/", "/contact/"):
                with self.subTest(width=width, path=path):
                    response = self.page.goto(path)
                    assert response is not None
                    self.assertEqual(response.status, 200)
                    self.assertLessEqual(
                        self.page.evaluate("document.documentElement.scrollWidth"),
                        self.page.evaluate("window.innerWidth") + 1,
                        path,
                    )
        self.page.set_viewport_size({"width": 320, "height": 900})
        toggler = self.page.get_by_role("button", name="Visa/dölj meny")
        expect(toggler).to_be_visible()
        toggler.click()
        expect(self.page.locator("#navbar")).to_be_visible()
        self.page.locator("#navbar").get_by_role("link", name="OSA", exact=True).click()
        expect(self.page.locator('input[name="guest_id"]')).to_be_visible()

    def test_rsvp(self) -> None:
        """Reject invalid lookup, submit a fake invitee's RSVP, and verify it survives reload."""
        self.page.goto("/rsvp/123456")
        expect(self.page).to_have_url(re.compile(re.escape(BASE_URL + "/rsvp") + r"/?$"))
        self.page.locator('input[name="guest_id"]').fill("000000")
        self.page.locator('button[type="submit"]').click()
        expect(self.page.get_by_role("alert")).to_contain_text("Vi hittar ingen inbjudan")
        self.page.locator('input[name="guest_id"]').fill("123456")
        self.page.locator('button[type="submit"]').click()
        expect(self.page).to_have_url(BASE_URL + "/rsvp/123456")
        expect(self.page.locator("main")).to_contain_text("Alex Andersson")
        self.page.locator('input[name="attending"][value="yes"]').check()
        self.page.locator('input[name="bringing_plus_one"][value="yes"]').check()
        self.page.locator("#plus_one_name").fill("Example Test Guest")
        self.page.locator("#dietary_requirements").fill("Example vegetarian meal")
        self.page.locator("#housing_needs").fill("Example overnight stay")
        self.page.get_by_role("button", name="Spara mitt svar").click()
        expect(self.page.get_by_role("status")).to_contain_text("Ditt svar är sparat")
        self.page.reload()
        expect(self.page.locator('input[name="attending"][value="yes"]')).to_be_checked()
        expect(self.page.locator("#plus_one_name")).to_have_value("Example Test Guest")
        expect(self.page.locator("#dietary_requirements")).to_have_value("Example vegetarian meal")
        expect(self.page.locator("#housing_needs")).to_have_value("Example overnight stay")

    def test_admin_authentication(self) -> None:
        """Require authentication, reject a bad password, and allow login/logout."""
        response = self.context.request.get(BASE_URL + "/api/v1/guests")
        self.assertEqual(response.status, 401)
        self.page.goto("/admin")
        expect(self.page).to_have_url(re.compile(r"/admin/login\?next="))
        self.page.get_by_label("Lösenord").fill("incorrect-test-password")
        self.page.get_by_role("button", name="Logga in").click()
        expect(self.page.get_by_role("alert")).to_contain_text("Incorrect password")
        self.page.get_by_label("Lösenord").fill(self.password)
        self.page.get_by_role("button", name="Logga in").click()
        expect(self.page).to_have_url(re.compile(re.escape(BASE_URL + "/admin") + r"/?$"))
        expect(self.page.locator("[data-admin-action]").first).to_be_visible()
        response = self.context.request.post(BASE_URL + "/api/v1/auth/logout", data={})
        self.assertEqual(response.status, 200)
        self.page.goto("/admin")
        expect(self.page).to_have_url(re.compile(r"/admin/login\?next="))
