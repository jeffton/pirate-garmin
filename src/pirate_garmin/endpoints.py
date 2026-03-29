from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pirate_garmin.auth import ProfileBundle
from pirate_garmin.client import Host


@dataclass(frozen=True, slots=True)
class Endpoint:
    key: str
    host: Host
    path: str
    description: str
    defaults: dict[str, str] = field(default_factory=dict)

    @property
    def placeholders(self) -> tuple[str, ...]:
        placeholders: list[str] = []
        for chunk in self.path.split("{"):
            if "}" not in chunk:
                continue
            placeholders.append(chunk.split("}", 1)[0])
        return tuple(placeholders)


ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint(
        "profile.social",
        "connectapi",
        "/userprofile-service/socialProfile",
        "Native social profile",
    ),
    Endpoint(
        "profile.settings",
        "connectapi",
        "/userprofile-service/userprofile/settings",
        "Garmin user settings",
    ),
    Endpoint(
        "sleep.daily",
        "connectapi",
        "/sleep-service/sleep/dailySleepData",
        "Daily sleep data",
        defaults={"nonSleepBufferMinutes": "60"},
    ),
    Endpoint(
        "activities.search",
        "connectapi",
        "/activitylist-service/activities/search/activities",
        "Activity list and date-filtered search",
    ),
    Endpoint(
        "activities.count",
        "connectapi",
        "/activitylist-service/activities/count",
        "Activity count",
    ),
    Endpoint(
        "activities.summary",
        "connectapi",
        "/activity-service/activity/{activity_id}",
        "Activity summary",
    ),
    Endpoint(
        "activities.details",
        "connectapi",
        "/activity-service/activity/{activity_id}/details",
        "Detailed activity data",
        defaults={"maxChartSize": "2000", "maxPolylineSize": "4000"},
    ),
    Endpoint(
        "activities.exercise-sets",
        "connectapi",
        "/activity-service/activity/{activity_id}/exerciseSets",
        "Activity exercise sets",
    ),
    Endpoint(
        "activities.hr-time-in-zones",
        "connectapi",
        "/activity-service/activity/{activity_id}/hrTimeInZones",
        "Activity heart-rate time in zones",
    ),
    Endpoint(
        "activities.power-time-in-zones",
        "connectapi",
        "/activity-service/activity/{activity_id}/powerTimeInZones",
        "Activity power time in zones",
    ),
    Endpoint(
        "activities.splits",
        "connectapi",
        "/activity-service/activity/{activity_id}/splits",
        "Activity splits",
    ),
    Endpoint(
        "activities.typed-splits",
        "connectapi",
        "/activity-service/activity/{activity_id}/typedsplits",
        "Typed splits for activity",
    ),
    Endpoint(
        "activities.split-summaries",
        "connectapi",
        "/activity-service/activity/{activity_id}/split_summaries",
        "Activity split summaries",
    ),
    Endpoint(
        "activities.weather",
        "connectapi",
        "/activity-service/activity/{activity_id}/weather",
        "Activity weather",
    ),
    Endpoint("hrv.daily", "connectapi", "/hrv-service/hrv/{date}", "Daily HRV data"),
    Endpoint(
        "metrics.training-readiness",
        "connectapi",
        "/metrics-service/metrics/trainingreadiness/{date}",
        "Training readiness",
    ),
    Endpoint(
        "metrics.endurance-score.daily",
        "connectapi",
        "/metrics-service/metrics/endurancescore",
        "Endurance score for a single day",
    ),
    Endpoint(
        "metrics.endurance-score.stats",
        "connectapi",
        "/metrics-service/metrics/endurancescore/stats",
        "Endurance score stats across a range",
        defaults={"aggregation": "weekly"},
    ),
    Endpoint(
        "metrics.hill-score.daily",
        "connectapi",
        "/metrics-service/metrics/hillscore",
        "Hill score for a single day",
    ),
    Endpoint(
        "metrics.hill-score.stats",
        "connectapi",
        "/metrics-service/metrics/hillscore/stats",
        "Hill score stats across a range",
        defaults={"aggregation": "daily"},
    ),
    Endpoint(
        "metrics.running-tolerance.stats",
        "connectapi",
        "/metrics-service/metrics/runningtolerance/stats",
        "Running tolerance stats across a range",
        defaults={"aggregation": "weekly"},
    ),
    Endpoint(
        "metrics.race-predictions.latest",
        "connectapi",
        "/metrics-service/metrics/racepredictions/latest/{display_name}",
        "Latest race predictions",
    ),
    Endpoint(
        "metrics.race-predictions.daily",
        "connectapi",
        "/metrics-service/metrics/racepredictions/daily/{display_name}",
        "Daily race predictions across a range",
    ),
    Endpoint(
        "metrics.race-predictions.monthly",
        "connectapi",
        "/metrics-service/metrics/racepredictions/monthly/{display_name}",
        "Monthly race predictions across a range",
    ),
    Endpoint(
        "metrics.training-status",
        "connectapi",
        "/metrics-service/metrics/trainingstatus/aggregated/{date}",
        "Training status",
    ),
    Endpoint(
        "metrics.maxmet.daily",
        "connectapi",
        "/metrics-service/metrics/maxmet/daily/{date}/{date}",
        "Daily max metrics / VO2 max-related payload",
    ),
    Endpoint(
        "fitnessage.daily",
        "connectapi",
        "/fitnessage-service/fitnessage/{date}",
        "Fitness age payload",
    ),
    Endpoint(
        "wellness.body-battery.daily",
        "connectapi",
        "/wellness-service/wellness/bodyBattery/reports/daily",
        "Body battery daily range",
    ),
    Endpoint(
        "wellness.body-battery.events",
        "connectapi",
        "/wellness-service/wellness/bodyBattery/events/{date}",
        "Body battery events for a day",
    ),
    Endpoint(
        "wellness.stress.daily",
        "connectapi",
        "/wellness-service/wellness/dailyStress/{date}",
        "Daily stress data",
    ),
    Endpoint(
        "wellness.stress.weekly",
        "connectapi",
        "/usersummary-service/stats/stress/weekly/{end}/{weeks}",
        "Weekly stress aggregates",
    ),
    Endpoint(
        "wellness.heart-rate.daily",
        "connectapi",
        "/wellness-service/wellness/dailyHeartRate/{display_name}",
        "Daily heart-rate graph payload",
    ),
    Endpoint(
        "wellness.respiration.daily",
        "connectapi",
        "/wellness-service/wellness/daily/respiration/{date}",
        "Daily respiration / breathing data",
    ),
    Endpoint(
        "wellness.spo2.daily",
        "connectapi",
        "/wellness-service/wellness/daily/spo2/{date}",
        "Daily SpO2 data",
    ),
    Endpoint(
        "wellness.floors.daily",
        "connectapi",
        "/wellness-service/wellness/floorsChartData/daily/{date}",
        "Daily floors data",
    ),
    Endpoint(
        "wellness.intensity.daily",
        "connectapi",
        "/wellness-service/wellness/daily/im/{date}",
        "Daily intensity minutes",
    ),
    Endpoint(
        "wellness.daily-events",
        "connectapi",
        "/wellness-service/wellness/dailyEvents",
        "All-day events for a date",
    ),
    Endpoint(
        "usersummary.daily",
        "connectapi",
        "/usersummary-service/usersummary/daily/{display_name}",
        "Daily user summary (steps, calories, etc.)",
    ),
    Endpoint(
        "usersummary.steps.chart",
        "connectapi",
        "/wellness-service/wellness/dailySummaryChart/{display_name}",
        "Step chart payload for a day",
    ),
    Endpoint(
        "usersummary.steps.daily",
        "connectapi",
        "/usersummary-service/stats/steps/daily/{start}/{end}",
        "Daily steps range",
    ),
    Endpoint(
        "usersummary.steps.weekly",
        "connectapi",
        "/usersummary-service/stats/steps/weekly/{end}/{weeks}",
        "Weekly steps aggregates",
    ),
    Endpoint(
        "usersummary.intensity.weekly",
        "connectapi",
        "/usersummary-service/stats/im/weekly/{start}/{end}",
        "Weekly intensity minutes aggregates",
    ),
    Endpoint(
        "usersummary.hydration.daily",
        "connectapi",
        "/usersummary-service/usersummary/hydration/daily/{date}",
        "Daily hydration data",
    ),
    Endpoint(
        "userstats.rhr.daily",
        "connectapi",
        "/userstats-service/wellness/daily/{display_name}",
        "Resting heart-rate payload for a day",
        defaults={"metricId": "60"},
    ),
    Endpoint(
        "weight.body-composition",
        "connectapi",
        "/weight-service/weight/dateRange",
        "Weight and body composition range",
    ),
    Endpoint(
        "biometric.cycling-ftp.latest",
        "connectapi",
        "/biometric-service/biometric/latestFunctionalThresholdPower/CYCLING",
        "Latest cycling FTP",
    ),
    Endpoint(
        "lifestyle.daily-log",
        "connectapi",
        "/lifestylelogging-service/dailyLog/{date}",
        "Daily lifestyle logging payload",
    ),
    Endpoint(
        "goals.list",
        "connectapi",
        "/goal-service/goal/goals",
        "Goals list",
    ),
    Endpoint(
        "devices.list",
        "connectapi",
        "/device-service/deviceregistration/devices",
        "Registered devices",
    ),
    Endpoint(
        "devices.last-used",
        "connectapi",
        "/device-service/deviceservice/mylastused",
        "Last-used device",
    ),
    Endpoint(
        "devices.primary-training-device",
        "connectapi",
        "/web-gateway/device-info/primary-training-device",
        "Primary training device",
    ),
    Endpoint(
        "weight.range",
        "connectapi",
        "/weight-service/weight/range/{start}/{end}",
        "Weigh-ins in a date range",
        defaults={"includeAll": "true"},
    ),
    Endpoint(
        "weight.dayview",
        "connectapi",
        "/weight-service/weight/dayview/{date}",
        "Weigh-ins for a day",
        defaults={"includeAll": "true"},
    ),
)

ENDPOINT_INDEX = {endpoint.key: endpoint for endpoint in ENDPOINTS}


def resolve_endpoint(key: str) -> Endpoint:
    try:
        return ENDPOINT_INDEX[key]
    except KeyError as exc:
        raise KeyError(f"Unknown endpoint: {key}") from exc


def render_endpoint(
    endpoint: Endpoint,
    path_values: dict[str, str],
    query_values: dict[str, str],
    profile: ProfileBundle | None,
) -> tuple[str, dict[str, Any]]:
    values = dict(path_values)
    if profile and profile.display_name and "display_name" not in values:
        values["display_name"] = profile.display_name

    missing = [name for name in endpoint.placeholders if name not in values]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing path values for {endpoint.key}: {missing_text}")

    path = endpoint.path
    for key, value in values.items():
        path = path.replace("{" + key + "}", value)

    params: dict[str, Any] = dict(endpoint.defaults)
    params.update(query_values)
    return path, params


def parse_kv_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Expected key=value, got: {value}")
        key, raw = value.split("=", 1)
        parsed[key] = raw
    return parsed
