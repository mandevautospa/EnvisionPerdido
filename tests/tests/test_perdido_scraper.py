# tests/test_perdido_scraper.py
import types
import importlib.util
from pathlib import Path
import pytest

# --- Load the scraper module directly from its file path ---
SCRAPER_PATH = Path(__file__).resolve().parents[1] / "Envision_Perdido_DataCollection.py"
spec = importlib.util.spec_from_file_location("envision_scraper", SCRAPER_PATH)
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)


class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


class DummySession:
    """Minimal stub of requests.Session for deterministic tests."""
    def __init__(self, html_by_url):
        self.html_by_url = html_by_url

    def get(self, url, timeout=30):
        html, code = self.html_by_url.get(url, ("", 404))
        return DummyResponse(html, status_code=code)


@pytest.fixture
def restore_session():
    """Ensure we put the global session back after each test."""
    original = scraper.sess
    try:
        yield
    finally:
        scraper.sess = original


def test_constants_present():
    assert hasattr(scraper, "BASE")
    assert scraper.BASE == "https://business.perdidochamber.com"
    assert hasattr(scraper, "MONTH_URL")
    assert "events/calendar" in scraper.MONTH_URL


def test_get_ics_url_from_event_finds_direct_link(restore_session):
    event_url = "https://business.perdidochamber.com/events/details/some-event-12345"
    ics_href = "/events/ical/some-event-12345.ics"
    html = f"""
    <html><body>
      <a href="{ics_href}">Add to Calendar - iCal</a>
    </body></html>
    """
    scraper.sess = DummySession({event_url: (html, 200)})

    out = scraper.get_ics_url_from_event(event_url)
    assert out == scraper.BASE + ics_href


def test_get_ics_url_from_event_fallback_slug(restore_session):
    # No "Add to Calendar - iCal" link → should build fallback /events/ical/<slug>.ics
    event_url = "https://business.perdidochamber.com/events/details/networking-night-august-99999"
    html = "<html><body><p>No calendar link here</p></body></html>"
    scraper.sess = DummySession({event_url: (html, 200)})

    out = scraper.get_ics_url_from_event(event_url)
    assert out == f"{scraper.BASE}/events/ical/networking-night-august-99999.ics"


def test_get_ics_url_from_event_unexpected_format_returns_none(restore_session):
    # URL that doesn't match /events/details/<slug>
    event_url = "https://business.perdidochamber.com/random-page"
    html = "<html><body><p>No calendar link here</p></body></html>"
    scraper.sess = DummySession({event_url: (html, 200)})

    out = scraper.get_ics_url_from_event(event_url)
    assert out is None


def test_get_ics_url_from_event_http_error_raises(restore_session):
    event_url = "https://business.perdidochamber.com/events/details/fails-000"
    scraper.sess = DummySession({event_url: ("<html></html>", 500)})

    with pytest.raises(Exception):
        scraper.get_ics_url_from_event(event_url)
