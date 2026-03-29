from __future__ import annotations

import base64
import json

from pirate_garmin.auth import (
    CONNECT_API_BASE_URL,
    DI_TOKEN_URL,
    IT_TOKEN_URL,
    AuthManager,
    Credentials,
    NativeOAuth2Session,
    NativeTokenSlot,
    OAuth2Token,
)
from pirate_garmin.client import GarminClient


def _jwt(payload: dict[str, object]) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.sig"


def _oauth_payload(access_token: str, refresh_token: str) -> dict[str, object]:
    return {
        "scope": "read",
        "token_type": "Bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 3600,
        "refresh_token_expires_in": 7200,
    }


def test_native_login_bootstrap_saves_di_and_it_tokens(httpx_mock, tmp_path):
    manager = AuthManager(credentials=Credentials("user", "pass"), app_dir=tmp_path)

    httpx_mock.add_response(
        method="GET",
        url="https://sso.garmin.com/mobile/sso/en_US/sign-in?clientId=GCM_ANDROID_DARK&service=https%3A%2F%2Fmobile.integration.garmin.com%2Fgcm%2Fandroid",
        text="ok",
    )
    httpx_mock.add_response(
        method="GET",
        url="https://sso.garmin.com/mobile/api/checkLogin?clientId=GCM_ANDROID_DARK&locale=en-US&service=https%3A%2F%2Fmobile.integration.garmin.com%2Fgcm%2Fandroid",
        json={"ok": True},
    )
    httpx_mock.add_response(
        method="POST",
        url="https://sso.garmin.com/mobile/api/login?clientId=GCM_ANDROID_DARK&locale=en-US&service=https%3A%2F%2Fmobile.integration.garmin.com%2Fgcm%2Fandroid",
        json={"responseStatus": {"type": "SUCCESSFUL"}, "serviceTicketId": "ticket-123"},
    )
    httpx_mock.add_response(
        method="POST",
        url=DI_TOKEN_URL,
        json=_oauth_payload(
            _jwt({"client_id": "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"}),
            "di-refresh",
        ),
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{IT_TOKEN_URL}?grant_type=connect2_exchange",
        json=_oauth_payload("it-access", "it-refresh"),
    )

    session = manager.ensure_authenticated()

    assert session.di.client_id == "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"
    assert session.it.client_id == "GARMIN_CONNECT_MOBILE_ANDROID_2025Q2"
    assert manager.native_oauth2_path.exists()


def test_refresh_connectapi_token_after_401(httpx_mock, tmp_path):
    manager = AuthManager(app_dir=tmp_path)

    manager.save_native_session(
        NativeOAuth2Session(
            created_at="2026-03-28T00:00:00+00:00",
            login_client_id="GCM_ANDROID_DARK",
            service_url="https://mobile.integration.garmin.com/gcm/android",
            di=NativeTokenSlot(
                client_id="GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
                token=OAuth2Token(
                    scope="read",
                    token_type="Bearer",
                    access_token=_jwt({"client_id": "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"}),
                    refresh_token="di-refresh",
                    expires_in=3600,
                    expires_at=4102444800,
                    refresh_token_expires_in=7200,
                    refresh_token_expires_at=4102448400,
                ),
            ),
            it=NativeTokenSlot(
                client_id="GARMIN_CONNECT_MOBILE_ANDROID_2025Q2",
                token=OAuth2Token(
                    scope="read",
                    token_type="Bearer",
                    access_token="it-access",
                    refresh_token="it-refresh",
                    expires_in=3600,
                    expires_at=4102444800,
                    refresh_token_expires_in=7200,
                    refresh_token_expires_at=4102448400,
                ),
            ),
        )
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{CONNECT_API_BASE_URL}/hrv-service/hrv/2026-03-28",
        status_code=401,
        text="expired",
    )
    httpx_mock.add_response(
        method="POST",
        url=DI_TOKEN_URL,
        json=_oauth_payload(
            _jwt({"client_id": "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2"}),
            "di-refresh-2",
        ),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{CONNECT_API_BASE_URL}/hrv-service/hrv/2026-03-28",
        json={"status": "ok"},
    )

    client = GarminClient(auth=manager)
    payload = client.request_json("connectapi", "/hrv-service/hrv/2026-03-28")

    assert payload == {"status": "ok"}
