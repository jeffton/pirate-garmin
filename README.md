# pirate-garmin

Thin Garmin Connect CLI in Python, built around Garmin's new auth flow.

This repo is intentionally a thin wrapper:

- Python package with a modern `pyproject.toml`
- `uv` for local workflows and locking
- `hatchling` as the build backend
- `httpx` for HTTP
- `typer` for the CLI
- native Garmin auth with cached DI + IT OAuth2 tokens
- raw Garmin JSON payloads back out, with as little reshaping as possible

## What is implemented

- New Garmin login flow
- Cached Garmin auth in `.garmin/native-oauth2.json`
- Cached profile/settings in `.garmin/profile.json`
- Token reuse and refresh before falling back to username/password
- Endpoint registry for the Garmin Connect endpoints that matter here
- Generic raw requests for arbitrary `connectapi` / `services` paths

## Auth flow

The CLI implements this native flow:

1. mobile SSO login via `GCM_ANDROID_DARK`
2. service ticket -> DI OAuth2
3. DI OAuth2 -> IT OAuth2
4. cache both token families locally
5. refresh cached tokens whenever possible on later runs

Cache files:

- `.garmin/native-oauth2.json`
- `.garmin/profile.json`

## Credentials

Use either CLI flags or env vars:

- `GARMIN_USERNAME`
- `GARMIN_PASSWORD`

Flags always work too:

```bash
pirate-garmin login --username you@example.com --password 'secret'
```

Even if credentials are passed every time, the CLI will still reuse cached tokens first.

## Install / run

### With uv

```bash
uv sync --extra dev
uv run pirate-garmin version
```

### Build / install

```bash
uv build
uv tool install .
```

## Commands

### Bootstrap auth

```bash
uv run pirate-garmin login
uv run pirate-garmin whoami
uv run pirate-garmin profile
```

### List supported endpoint shortcuts

```bash
uv run pirate-garmin endpoints
uv run pirate-garmin endpoints --json
```

### Fetch a registered endpoint

```bash
uv run pirate-garmin get sleep.daily --query date=2026-03-28
uv run pirate-garmin get activities.search --query start=0 --query limit=5
uv run pirate-garmin get activities.details --path activity_id=123456789 --query maxChartSize=2000
uv run pirate-garmin get wellness.body-battery.daily --query startDate=2026-03-01 --query endDate=2026-03-28
uv run pirate-garmin get metrics.training-status --path date=2026-03-28
```

### Hit a raw Garmin path directly

```bash
uv run pirate-garmin raw /sleep-service/sleep/dailySleepData --query date=2026-03-28 --query nonSleepBufferMinutes=60
uv run pirate-garmin raw /api/oauth/token --host services --query grant_type=refresh_token
```

## Endpoint shortcuts

These are currently registered:

- `profile.social`
- `profile.settings`
- `sleep.daily`
- `activities.search`
- `activities.count`
- `activities.summary`
- `activities.details`
- `activities.exercise-sets`
- `activities.hr-time-in-zones`
- `activities.power-time-in-zones`
- `activities.splits`
- `activities.typed-splits`
- `activities.split-summaries`
- `activities.weather`
- `hrv.daily`
- `metrics.training-readiness`
- `metrics.training-status`
- `metrics.maxmet.daily`
- `metrics.endurance-score.daily`
- `metrics.endurance-score.stats`
- `metrics.hill-score.daily`
- `metrics.hill-score.stats`
- `metrics.running-tolerance.stats`
- `metrics.race-predictions.latest`
- `metrics.race-predictions.daily`
- `metrics.race-predictions.monthly`
- `fitnessage.daily`
- `wellness.body-battery.daily`
- `wellness.body-battery.events`
- `wellness.stress.daily`
- `wellness.stress.weekly`
- `wellness.heart-rate.daily`
- `wellness.respiration.daily`
- `wellness.spo2.daily`
- `wellness.floors.daily`
- `wellness.intensity.daily`
- `wellness.daily-events`
- `usersummary.daily`
- `usersummary.steps.chart`
- `usersummary.steps.daily`
- `usersummary.steps.weekly`
- `usersummary.intensity.weekly`
- `usersummary.hydration.daily`
- `userstats.rhr.daily`
- `weight.body-composition`
- `weight.range`
- `weight.dayview`
- `biometric.cycling-ftp.latest`
- `lifestyle.daily-log`
- `goals.list`
- `devices.list`
- `devices.last-used`
- `devices.primary-training-device`

`display_name` path placeholders are auto-filled from the cached Garmin profile.

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```
