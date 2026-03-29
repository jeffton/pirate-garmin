import pytest

from pirate_garmin.browser_login import (
    BrowserLoginError,
    FreshLoginResult,
    parse_login_response_payload,
)


def test_parse_login_response_payload_returns_service_ticket():
    assert parse_login_response_payload(
        {
            "responseStatus": {"type": "SUCCESSFUL"},
            "serviceTicketId": "ticket-123",
        }
    ) == FreshLoginResult(service_ticket="ticket-123")


def test_parse_login_response_payload_surfaces_captcha_requirement():
    with pytest.raises(BrowserLoginError, match="CAPTCHA"):
        parse_login_response_payload(
            {
                "responseStatus": {"type": "CAPTCHA_REQUIRED"},
                "detail": "recaptcha enterprise required",
            }
        )
