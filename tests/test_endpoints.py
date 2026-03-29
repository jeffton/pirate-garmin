from pirate_garmin.auth import ProfileBundle
from pirate_garmin.endpoints import parse_kv_pairs, render_endpoint, resolve_endpoint


def test_render_endpoint_autofills_display_name_and_defaults():
    endpoint = resolve_endpoint("wellness.heart-rate.daily")
    path, params = render_endpoint(
        endpoint,
        {},
        {"date": "2026-03-28"},
        ProfileBundle(social_profile={"displayName": "captain-hook"}, settings=None),
    )

    assert path == "/wellness-service/wellness/dailyHeartRate/captain-hook"
    assert params == {"date": "2026-03-28"}


def test_parse_kv_pairs_parses_repeatable_options():
    assert parse_kv_pairs(["date=2026-03-28", "limit=20"]) == {
        "date": "2026-03-28",
        "limit": "20",
    }
