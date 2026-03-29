from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

MOBILE_SSO_BASE_URL = "https://sso.garmin.com"
DEFAULT_LOGIN_CLIENT_ID = "GCM_ANDROID_DARK"
DEFAULT_SERVICE_URL = "https://mobile.integration.garmin.com/gcm/android"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; sdk_gphone64_arm64 Build/TE1A.220922.025; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.0.0 Mobile Safari/537.36"
)
USERNAME_SELECTORS = (
    'input[name="username"]',
    'input[name="email"]',
    'input[type="email"]',
    '#username',
)
PASSWORD_SELECTORS = (
    'input[name="password"]',
    'input[type="password"]',
    '#password',
)
SUBMIT_SELECTORS = (
    'button[type="submit"]',
    'button:has-text("Sign In")',
    'button:has-text("Log In")',
    'input[type="submit"]',
)


class BrowserLoginError(RuntimeError):
    pass


class BrowserDependencyError(BrowserLoginError):
    pass


@dataclass(slots=True)
class FreshLoginResult:
    service_ticket: str


def build_sign_in_url(client_id: str, service_url: str) -> str:
    return (
        f"{MOBILE_SSO_BASE_URL}/mobile/sso/en_US/sign-in?"
        + urlencode({"clientId": client_id, "service": service_url})
    )


def parse_login_response_payload(payload: dict[str, Any]) -> FreshLoginResult:
    response_status = payload.get("responseStatus")
    response_type = ""
    if isinstance(response_status, dict):
        raw_type = response_status.get("type")
        response_type = str(raw_type).upper() if raw_type else ""

    service_ticket = payload.get("serviceTicketId")
    if response_type == "SUCCESSFUL" and service_ticket:
        return FreshLoginResult(service_ticket=str(service_ticket))

    serialized = _serialize_payload(payload)
    if response_type == "SUCCESSFUL":
        raise BrowserLoginError(
            f"Garmin browser login succeeded without serviceTicketId: {serialized}"
        )
    if response_type == "CAPTCHA_REQUIRED":
        raise BrowserLoginError(f"Garmin browser login requires CAPTCHA: {serialized}")
    if "MFA" in response_type or "TWO_FACTOR" in response_type:
        raise BrowserLoginError(f"Garmin browser login requires MFA: {serialized}")
    if response_type:
        raise BrowserLoginError(f"Garmin browser login failed ({response_type}): {serialized}")
    raise BrowserLoginError(f"Garmin browser login returned unexpected payload: {serialized}")


def login_via_browser(
    username: str,
    password: str,
    timeout: float,
    client_id: str = DEFAULT_LOGIN_CLIENT_ID,
    service_url: str = DEFAULT_SERVICE_URL,
    user_agent: str = DEFAULT_USER_AGENT,
    headless: bool = False,
) -> FreshLoginResult:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserDependencyError(
            "Fresh Garmin login requires Playwright. Install the optional browser extra "
            "and Chromium with: `uv sync --extra browser` and `uv run playwright install chromium`."
        ) from exc

    timeout_ms = max(int(timeout * 1000), 1000)
    sign_in_url = build_sign_in_url(client_id, service_url)
    login_api_prefix = f"{MOBILE_SSO_BASE_URL}/mobile/api/login"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=user_agent,
            locale="en-US",
            viewport={"width": 412, "height": 915},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        try:
            try:
                page.goto(sign_in_url, wait_until="domcontentloaded", timeout=timeout_ms)
                _fill_first(page, USERNAME_SELECTORS, username, timeout_ms, PlaywrightError)
                _fill_first(page, PASSWORD_SELECTORS, password, timeout_ms, PlaywrightError)
                try:
                    with page.expect_response(
                        lambda response: response.request.method == "POST"
                        and response.url.startswith(login_api_prefix),
                        timeout=timeout_ms,
                    ) as response_info:
                        _submit_login_form(page, timeout_ms, PlaywrightError)
                except PlaywrightTimeoutError as exc:
                    raise BrowserLoginError(
                        "Timed out waiting for Garmin mobile login response. "
                        f"Current page: {page.url}. Page snippet: {_page_snippet(page)}"
                    ) from exc

                response = response_info.value
                if not response.ok:
                    raise BrowserLoginError(
                        f"Garmin browser login failed with HTTP {response.status}: "
                        f"{_safe_snippet(_response_text(response))}"
                    )
                try:
                    payload = response.json()
                except Exception as exc:
                    raise BrowserLoginError(
                        "Garmin browser login returned a non-JSON response: "
                        f"{_safe_snippet(_response_text(response))}"
                    ) from exc
                return parse_login_response_payload(payload)
            except PlaywrightError as exc:
                raise BrowserLoginError(f"Garmin browser login automation failed: {exc}") from exc
        finally:
            context.close()
            browser.close()


def _fill_first(
    page: Any,
    selectors: tuple[str, ...],
    value: str,
    timeout_ms: int,
    playwright_error: type[Exception],
) -> None:
    locator = _first_visible_locator(page, selectors, timeout_ms, playwright_error)
    if locator is None:
        raise BrowserLoginError(
            f"Could not find Garmin login field. Tried selectors: {', '.join(selectors)}"
        )
    locator.fill(value)


def _submit_login_form(
    page: Any,
    timeout_ms: int,
    playwright_error: type[Exception],
) -> None:
    locator = _first_visible_locator(page, SUBMIT_SELECTORS, timeout_ms, playwright_error)
    if locator is not None:
        locator.click()
        return

    password_locator = _first_visible_locator(
        page,
        PASSWORD_SELECTORS,
        timeout_ms,
        playwright_error,
    )
    if password_locator is None:
        raise BrowserLoginError("Could not find Garmin password field to submit the login form")
    password_locator.press("Enter")


def _first_visible_locator(
    page: Any,
    selectors: tuple[str, ...],
    timeout_ms: int,
    playwright_error: type[Exception],
) -> Any | None:
    probe_timeout_ms = min(timeout_ms, 1500)
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=probe_timeout_ms)
        except playwright_error:
            continue
        return locator
    return None


def _response_text(response: Any) -> str:
    try:
        return str(response.text())
    except Exception:
        return ""


def _page_snippet(page: Any) -> str:
    try:
        return _safe_snippet(str(page.locator("body").inner_text(timeout=1000)))
    except Exception:
        return ""


def _serialize_payload(payload: dict[str, Any]) -> str:
    try:
        return json.dumps(payload, sort_keys=True)
    except TypeError:
        return str(payload)


def _safe_snippet(text: str, length: int = 400) -> str:
    return " ".join(text.split())[:length]
