# Plan: add browser-driven fresh login to `pirate-garmin`

Date: 2026-03-29

## Why this is needed

Fresh username/password login in the Python CLI currently gets `429` from Garmin, while the real Android app still succeeds from the same IP.

Latest reverse-engineering result from `../pirate-garmin-internal`:

- the Garmin Connect Android app performs fresh sign-in inside a **real WebView**
- Garmin's frontend JavaScript drives `/mobile/api/checkLogin` and `/mobile/api/login`
- the frontend bundle includes:
  - XSRF handling (`XSRF-TOKEN` / `X-XSRF-TOKEN`)
  - captcha / reCAPTCHA Enterprise hooks
  - browser/WebView-managed state we are currently skipping
- after that WebView login succeeds, the native flow continues exactly as expected:
  - `serviceTicketId`
  - DI OAuth2 via `diauth.garmin.com`
  - IT OAuth2 via `services.garmin.com`

Conclusion:

**The problem is not mainly the DI/IT exchange. The problem is the synthetic direct Python POST to Garmin mobile SSO login.**

## High-level implementation strategy

Use a real browser runtime only for the fresh login bootstrap.
Keep the existing HTTP token exchange and refresh logic for everything else.

Target flow:

1. browser opens Garmin mobile SSO sign-in page
2. browser fills username/password in the real frontend
3. browser submits the real sign-in form
4. extract `serviceTicketId` from Garmin's frontend/network flow
5. continue with existing Python code:
   - `serviceTicketId -> DI OAuth2`
   - `DI OAuth2 -> IT OAuth2`
6. cache tokens in `.garmin/native-oauth2.json`
7. use refresh tokens afterward without browser involvement

## Dependency choice

Preferred choice: **Playwright for Python**.

Why:

- good Python ergonomics
- easy network interception
- easy headed/headless support
- easy DOM form fill / submit
- easiest way to capture the `/mobile/api/login` response JSON and extract `serviceTicketId`

Do **not** use raw HTTP for fresh login anymore.

## Packaging approach

Keep browser support optional.

Suggested `pyproject.toml` shape:

```toml
[project.optional-dependencies]
browser = [
  "playwright>=1.54.0",
]
```

Base package stays lightweight.
Browser login is enabled when the extra is installed.

## Code structure plan

### 1. Add a new browser login module

Create:

- `src/pirate_garmin/browser_login.py`

Suggested responsibilities:

- launch browser/context
- navigate to Garmin mobile SSO sign-in page
- fill credentials
- click Sign In
- wait for successful login result
- capture and return `serviceTicketId`

Suggested result type:

```python
@dataclass(slots=True)
class FreshLoginResult:
    service_ticket: str
```

We probably do not need to persist browser cookies after this step.
The service ticket is enough.

### 2. Refactor `AuthManager.create_native_session()`

Current behavior mixes:

- synthetic SSO HTTP login
- DI exchange
- IT exchange

Change it to:

- browser-driven fresh login bootstrap
- existing DI exchange
- existing IT exchange

Desired shape:

```python
def create_native_session(self) -> NativeOAuth2Session:
    credentials = self.require_credentials()
    fresh = login_via_browser(
        username=credentials.username,
        password=credentials.password,
        timeout=self.timeout,
    )
    di_slot = self.exchange_service_ticket_for_di_token(...)
    it_slot = self.exchange_di_token_for_it_token(...)
    return NativeOAuth2Session(...)
```

### 3. Keep existing token logic

Keep and reuse as much as possible:

- `exchange_service_ticket_for_di_token()`
- `exchange_di_token_for_it_token()`
- `refresh_di_token_slot()`
- `refresh_it_token_slot()`
- `ensure_authenticated()`

These are still valid and useful.

## Browser login details

### Sign-in URL

Use:

```text
https://sso.garmin.com/mobile/sso/en_US/sign-in?clientId=GCM_ANDROID_DARK&service=https://mobile.integration.garmin.com/gcm/android
```

### Browser context hints

Start with:

- mobile-ish user agent matching Android WebView as closely as practical
- locale `en-US`
- mobile viewport

But do **not** overfit immediately.
The most important thing is using a real JS/browser runtime.

### Success detection

Primary success signal:

- intercept the network response for:
  - `https://sso.garmin.com/mobile/api/login?...`
- parse the JSON response
- read:
  - `responseStatus.type == "SUCCESSFUL"`
  - `serviceTicketId`

Secondary success signals if needed:

- navigation or load of `https://sso.garmin.com/portal/sso/embed`
- Garmin portal event equivalents observed in page/network state

### Failure cases

Handle explicitly:

- `CAPTCHA_REQUIRED`
- MFA-required paths
- login denied / locked account / password change required
- browser dependency not installed

Do not hide Garmin responses.
Surface the real failure.

## CLI plan

Add login mode selection centered around browser fresh login.

Suggested behavior:

- if cached tokens exist and can be refreshed: no browser
- if a true fresh login is needed: use browser login automatically

Possible future CLI options:

- `--login-mode browser`
- `--login-mode browser-headed`
- `--login-mode browser-headless`

For first implementation, simplest is fine:

- default to browser-based fresh login
- probably start with **headed** mode locally until stability is confirmed

## Headless vs headed

Do not assume headless works identically.

Recommended rollout:

1. implement headed first
2. verify service ticket extraction works reliably
3. test headless after that

If Garmin fingerprints headless more aggressively, headed may be necessary.

## Tests to add

### Unit tests

Mock browser login result and verify:

- `create_native_session()` uses returned `serviceTicketId`
- DI and IT exchanges still produce the stored session format

### Integration-ish tests with mocks

- browser module parses successful `/mobile/api/login` response correctly
- browser module surfaces unsuccessful login states correctly

### Manual validation

Use a fresh temp app dir and verify:

1. no cached auth present
2. browser login succeeds
3. `.garmin/native-oauth2.json` created
4. subsequent command reuses cached tokens without browser
5. refresh path still works without browser

## Implementation order

1. add browser extra dependency in `pyproject.toml`
2. add `browser_login.py` with Playwright-based fresh login bootstrap
3. refactor `AuthManager.create_native_session()` to call browser login
4. keep DI/IT code unchanged unless headers need small updates
5. add tests for the new orchestration
6. update `README.md` to explain browser requirement for fresh login

## Important non-goals

For the first pass, do **not** try to:

- fully emulate Android app internals beyond what the browser already does
- replace token refresh with browser automation
- preserve backward compatibility with the direct-HTTP fresh login path

The direct-HTTP fresh login path now looks fundamentally wrong for Garmin's current anti-bot expectations.

## Notes from the latest fresh capture

Useful confirmed values:

- login client ID: `GCM_ANDROID_DARK`
- service URL: `https://mobile.integration.garmin.com/gcm/android`
- DI client ID in current app: `GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2`
- IT client ID in current app: `GARMIN_CONNECT_MOBILE_ANDROID_2025Q2`
- DI uses Basic auth with empty password
- DI includes `app-validation-error: CANNOT_BIND_TO_SERVICE`
- app uses additional native UA/header details after login

Those values remain relevant after browser login succeeds.

## Relevant docs

- `../pirate-garmin-internal/docs/fresh-login-webview-gap.md`
- `../pirate-garmin-internal/docs/emulator-hook-login-findings.md`
- `/tmp/garmin-frida-hooks-fresh.log`
