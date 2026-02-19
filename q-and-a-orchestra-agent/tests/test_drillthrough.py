"""
Unit tests for RECA drillthrough email extraction.
All HTTP requests are mocked — no live RECA calls.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from integrations.reca_scraper_logic import RECAHttpScraper


# ---------------------------------------------------------------------------
# Sample HTML fragments
# ---------------------------------------------------------------------------

DETAIL_PAGE_WITH_MAILTO = """
<html><body>
<table>
  <tr><td>Name</td><td>Jane Doe</td></tr>
  <tr><td>Email</td><td><a href="mailto:jane.doe@broker.ca">jane.doe@broker.ca</a></td></tr>
  <tr><td>Phone</td><td>(403) 555-1234</td></tr>
</table>
</body></html>
"""

DETAIL_PAGE_WITH_RAW_EMAIL = """
<html><body>
<div class="agentInfo">
  Contact: john.smith@realestate.ab.ca | Phone: 780-555-9876
</div>
</body></html>
"""

DETAIL_PAGE_NO_EMAIL = """
<html><body>
<table>
  <tr><td>Name</td><td>No Email Agent</td></tr>
  <tr><td>Phone</td><td>(403) 555-0000</td></tr>
</table>
</body></html>
"""

ERROR_PAGE = """
<html><body>
<h1>Server Error in '/' Application.</h1>
<h2><i>Runtime Error</i></h2>
</body></html>
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scraper():
    """RECAHttpScraper with initialization bypassed."""
    s = RECAHttpScraper()
    s._initialized = True
    s._base_form_data = {
        "__VIEWSTATE": "fake",
        "__EVENTVALIDATION": "fake",
    }
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_drillthrough_extracts_mailto(scraper):
    """Should extract email from mailto: link."""
    mock_resp = MagicMock()
    mock_resp.text = DETAIL_PAGE_WITH_MAILTO

    with patch.object(scraper.session, "post", return_value=mock_resp):
        email = scraper.perform_drillthrough("DRILL123")

    assert email == "jane.doe@broker.ca"


def test_drillthrough_extracts_raw_email(scraper):
    """Should fall back to regex when no mailto: link."""
    mock_resp = MagicMock()
    mock_resp.text = DETAIL_PAGE_WITH_RAW_EMAIL

    with patch.object(scraper.session, "post", return_value=mock_resp):
        email = scraper.perform_drillthrough("DRILL456")

    assert email == "john.smith@realestate.ab.ca"


def test_drillthrough_no_email(scraper):
    """Should return None when no email found."""
    mock_resp = MagicMock()
    mock_resp.text = DETAIL_PAGE_NO_EMAIL

    with patch.object(scraper.session, "post", return_value=mock_resp):
        email = scraper.perform_drillthrough("DRILL789")

    assert email is None


def test_drillthrough_sends_correct_form_data(scraper):
    """Verify that EVENTTARGET and EVENTARGUMENT are set correctly."""
    mock_resp = MagicMock()
    mock_resp.text = DETAIL_PAGE_NO_EMAIL

    with patch.object(scraper.session, "post", return_value=mock_resp) as mock_post:
        scraper.perform_drillthrough("ABC$XYZ")

    call_kwargs = mock_post.call_args
    posted_data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data") or call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None
    # If called positionally
    if posted_data is None:
        posted_data = call_kwargs[0][1] if len(call_kwargs[0]) > 1 else call_kwargs.kwargs.get("data")

    assert posted_data["__EVENTTARGET"] == "ReportViewer1$ctl13$ReportControl$ctl00"
    assert posted_data["__EVENTARGUMENT"] == "Drillthrough$ABC$XYZ"


def test_drillthrough_initialises_if_needed():
    """If not initialised, drillthrough should call _fetch_initial_state."""
    s = RECAHttpScraper()
    assert s._initialized is False

    mock_resp = MagicMock()
    mock_resp.text = DETAIL_PAGE_WITH_MAILTO

    with patch.object(s, "_fetch_initial_state") as mock_init, \
         patch.object(s.session, "post", return_value=mock_resp):
        # After _fetch_initial_state, _initialized and _base_form_data are set
        def init_side_effect():
            s._initialized = True
            s._base_form_data = {"__VIEWSTATE": "x", "__EVENTVALIDATION": "y"}

        mock_init.side_effect = init_side_effect
        email = s.perform_drillthrough("DRILL_INIT")

    mock_init.assert_called_once()
    assert email == "jane.doe@broker.ca"


def test_search_error_detection(scraper):
    """_is_error_response should catch runtime errors."""
    assert scraper._is_error_response(ERROR_PAGE) is True
    assert scraper._is_error_response(DETAIL_PAGE_WITH_MAILTO) is False
    assert scraper._is_error_response("Too Many Requests - slow down") is True
