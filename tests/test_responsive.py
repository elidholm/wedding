"""Responsive-layout tests.

These render the real pages in a headless browser at several viewport widths and
assert that nothing forces the document wider than the viewport (which is what
made the site unusable on phones: a Google Maps ``<iframe>`` with a hard-coded
``width="600"``).

Screenshots of every page/width combination are written to the directory given
by ``WEDDING_SCREENSHOT_DIR`` (default: a ``screenshots/`` folder next to this
file) so the layout can be eyeballed.

The whole module is skipped when Playwright or its browser binaries are not
available, so ``make test`` still works on a machine that has not run
``uv run playwright install chromium``.
"""

import os
import threading
import unittest
from pathlib import Path

from playwright.sync_api import Browser, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from werkzeug.serving import make_server

from main import app

# Widest phone-to-desktop range the layout must survive. 320px is the narrowest
# screen we support (iPhone SE and older small Androids).
VIEWPORT_WIDTHS = (320, 375, 768, 1440)

# Pages restyled in the responsive pass, plus the stubs that inherit base.html.
PAGES = {
    "home": "/",
    "rsvp": "/rsvp/",
    "rsvp-guest": "/rsvp/123456",
    "contact": "/contact/",
    "itinerary": "/itinerary/",
    "seating": "/seating/",
}

# Sub-pixel rounding of fluid widths can make scrollWidth exceed the viewport by
# a fraction, which is not a real overflow.
OVERFLOW_TOLERANCE_PX = 1

SCREENSHOT_DIR = Path(os.environ.get("WEDDING_SCREENSHOT_DIR", Path(__file__).parent / "screenshots"))


class _LiveServer:
    """A Flask app served on an ephemeral port in a background thread."""

    def __init__(self, flask_app):
        self._server = make_server("127.0.0.1", 0, flask_app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        """Return the root URL the server is listening on."""
        host, port = self._server.server_address[0], self._server.server_address[1]
        return f"http://{host}:{port}"

    def start(self) -> None:
        """Start serving requests in the background."""
        self._thread.start()

    def stop(self) -> None:
        """Shut the server down and join its thread."""
        self._server.shutdown()
        self._thread.join(timeout=5)


def _browser_is_available() -> bool:
    """Return True if a Chromium build Playwright can drive is installed."""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            browser.close()
    except PlaywrightError:
        return False

    return True


@unittest.skipUnless(_browser_is_available(), "Playwright chromium is not installed")
class TestResponsiveLayout(unittest.TestCase):
    """Verify no page overflows horizontally between 320px and 1440px."""

    server: _LiveServer
    browser: Browser
    _playwright: Playwright

    @classmethod
    def setUpClass(cls):
        """Start a live server, launch Chromium, and enable the map embed."""
        cls.config = app.config["CONFIG"]
        cls._original_maps_key = cls.config.googlemaps_key
        # Force the Google Maps embed to render so the iframe is included in the
        # overflow measurement -- it is the element that used to break mobile.
        cls.config.googlemaps_key = cls._original_maps_key or "fake-test-key"

        cls.server = _LiveServer(app)
        cls.server.start()

        cls._playwright = sync_playwright().start()
        cls.browser = cls._playwright.chromium.launch()

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Tear down the browser, the live server, and restore configuration."""
        cls.browser.close()
        cls._playwright.stop()
        cls.server.stop()
        cls.config.googlemaps_key = cls._original_maps_key

    def _measure(self, page_name: str, path: str, width: int) -> tuple[int, int]:
        """Load a page at a given width, screenshot it, and return (scrollWidth, innerWidth)."""
        context = self.browser.new_context(viewport={"width": width, "height": 900})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}{path}", wait_until="domcontentloaded")
            page.screenshot(path=str(SCREENSHOT_DIR / f"{page_name}-{width}.png"), full_page=True)
            return (
                page.evaluate("document.documentElement.scrollWidth"),
                page.evaluate("window.innerWidth"),
            )
        finally:
            context.close()

    def test_no_horizontal_overflow(self):
        """Test that no page scrolls horizontally at any supported viewport width."""
        for page_name, path in PAGES.items():
            for width in VIEWPORT_WIDTHS:
                with self.subTest(page=page_name, width=width):
                    scroll_width, inner_width = self._measure(page_name, path, width)

                    self.assertLessEqual(
                        scroll_width,
                        inner_width + OVERFLOW_TOLERANCE_PX,
                        f"{path} overflows horizontally at {width}px "
                        f"(scrollWidth={scroll_width}, innerWidth={inner_width})",
                    )

    def test_navbar_collapses_on_mobile_and_expands_on_desktop(self):
        """Test that the nav toggler is shown on phones and hidden on wide screens."""
        context = self.browser.new_context(viewport={"width": 320, "height": 900})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}/", wait_until="domcontentloaded")
            self.assertTrue(page.locator(".navbar-toggler").is_visible())
        finally:
            context.close()

        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}/", wait_until="domcontentloaded")
            self.assertFalse(page.locator(".navbar-toggler").is_visible())
            self.assertTrue(page.locator("#navbar").is_visible())
        finally:
            context.close()

    def test_navbar_stays_pinned_when_scrolling(self):
        """Test that the navbar remains pinned to the top of the viewport while scrolling.

        `position: sticky` is easy to break silently -- e.g. by putting the sticky
        class on an element whose parent is no taller than it is, or by adding
        `overflow-x: hidden` to an ancestor.
        """
        context = self.browser.new_context(viewport={"width": 375, "height": 700})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}/", wait_until="domcontentloaded")
            page.evaluate("window.scrollTo(0, 1200)")
            page.wait_for_timeout(300)

            self.assertGreater(page.evaluate("window.scrollY"), 0, "The page did not scroll")

            navbar_box = page.locator("nav.wed-navbar").bounding_box()
            self.assertIsNotNone(navbar_box)
            self.assertGreaterEqual(
                navbar_box["y"],
                0,
                f"The navbar scrolled out of view (y={navbar_box['y']}); it should stay pinned",
            )
        finally:
            context.close()

    def test_countdown_renders_all_four_units(self):
        """Test that the JS countdown replaces its placeholder with day/hour/minute/second values."""
        context = self.browser.new_context(viewport={"width": 375, "height": 700})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector(".wed-countdown__item")

            self.assertEqual(page.locator(".wed-countdown__item").count(), 4)

            for index in range(4):
                value = page.locator(".wed-countdown__value").nth(index).text_content()
                self.assertTrue(value.isdigit(), f"Countdown unit {index} rendered {value!r}, expected a number")
        finally:
            context.close()

    def test_map_embed_fits_within_content_column(self):
        """Test that the map embed never exceeds the width of its containing column."""
        context = self.browser.new_context(viewport={"width": 320, "height": 900})
        page = context.new_page()
        try:
            page.goto(f"{self.server.base_url}/", wait_until="domcontentloaded")
            map_box = page.locator(".wed-map").bounding_box()

            self.assertIsNotNone(map_box, "The map embed did not render")
            self.assertLessEqual(map_box["width"], 320)
        finally:
            context.close()


if __name__ == "__main__":
    unittest.main()
