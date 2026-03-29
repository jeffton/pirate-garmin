from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from pirate_garmin.auth import (
    CONNECT_API_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    SERVICES_BASE_URL,
    AuthManager,
    Credentials,
    GarminAuthError,
    build_native_headers,
)

Host = Literal["connectapi", "services"]
BASE_URLS: dict[Host, str] = {
    "connectapi": CONNECT_API_BASE_URL,
    "services": SERVICES_BASE_URL,
}


@dataclass(slots=True)
class GarminClient:
    auth: AuthManager
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_credentials(
        cls,
        username: str | None = None,
        password: str | None = None,
        app_dir: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> GarminClient:
        credentials = None
        if username is not None or password is not None:
            if not username or not password:
                raise GarminAuthError("Both username and password must be provided together")
            credentials = Credentials(username=username, password=password)
        return cls(
            auth=AuthManager(credentials=credentials, app_dir=app_dir, timeout=timeout),
            timeout=timeout,
        )

    def whoami(self) -> dict[str, Any]:
        bundle = self.auth.ensure_profile_bundle()
        if bundle.social_profile is None:
            raise GarminAuthError("Garmin profile could not be loaded")
        return bundle.social_profile

    def get_profile_bundle(self) -> dict[str, Any]:
        bundle = self.auth.ensure_profile_bundle()
        return bundle.to_dict()

    def request_json(
        self,
        host: Host,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        session = self.auth.ensure_authenticated()
        token = (
            session.di.token.access_token if host == "connectapi" else session.it.token.access_token
        )
        response = self._get_json(host, token, path, params)
        if response.status_code == 401:
            session = self.auth.refresh_for_host(host)
            token = (
                session.di.token.access_token
                if host == "connectapi"
                else session.it.token.access_token
            )
            response = self._get_json(host, token, path, params)
        if not response.is_success:
            raise GarminAuthError(
                f"{path} failed: {response.status_code} {' '.join(response.text.split())[:240]}"
            )
        return response.json()

    def _get_json(
        self,
        host: Host,
        access_token: str,
        path: str,
        params: dict[str, Any] | None,
    ) -> httpx.Response:
        with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
            return client.get(
                f"{BASE_URLS[host]}{path}",
                headers=build_native_headers(
                    {
                        "authorization": f"Bearer {access_token}",
                        "accept": "application/json",
                    }
                ),
                params=params,
            )
