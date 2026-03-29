# Mapping to the data you asked for

## Covered directly by registered endpoints

- body battery
  - `wellness.body-battery.daily`
  - `wellness.body-battery.events`
- stress
  - `wellness.stress.daily`
  - `wellness.stress.weekly`
- sleep
  - `sleep.daily`
- activities
  - `activities.search`
  - `activities.summary`
  - `activities.details`
  - splits / zones / weather / exercise sets
- HRV
  - `hrv.daily`
- heart rate
  - `wellness.heart-rate.daily`
  - `userstats.rhr.daily`
- training status / readiness / VO2-ish metrics
  - `metrics.training-status`
  - `metrics.training-readiness`
  - `metrics.maxmet.daily`
  - `metrics.endurance-score.daily`
  - `metrics.endurance-score.stats`
  - `metrics.hill-score.daily`
  - `metrics.hill-score.stats`
  - `metrics.running-tolerance.stats`
  - `metrics.race-predictions.latest`
  - `metrics.race-predictions.daily`
  - `metrics.race-predictions.monthly`
- intensity minutes
  - `wellness.intensity.daily`
  - `usersummary.intensity.weekly`
- steps
  - `usersummary.steps.chart`
  - `usersummary.steps.daily`
  - `usersummary.steps.weekly`
- fitness age
  - `fitnessage.daily`
- calories
  - `usersummary.daily`
- weight / body composition
  - `weight.body-composition`
  - `weight.range`
  - `weight.dayview`
- breathing
  - `wellness.respiration.daily`
- other useful bits
  - `wellness.spo2.daily`
  - `wellness.floors.daily`
  - `usersummary.hydration.daily`
  - `biometric.cycling-ftp.latest`
  - `lifestyle.daily-log`
  - `goals.list`
  - `devices.list`
  - `devices.last-used`
  - `devices.primary-training-device`

## Important gaps from the `python-garminconnect` endpoint list

These do **not** show up as dedicated endpoints in the extracted `python-garminconnect` endpoint list used for this project:

- training load, acute/chronic load, anaerobic load vs goals
- a clearly separate max-heart-rate history endpoint
- a clearly separate sleep-history range endpoint
- a clearly separate HRV-history range endpoint
- a clearly separate training-readiness history endpoint

For the daily-only items above, the current CLI stays thin and exposes the per-day endpoint instead of inventing a custom fan-out/history layer.

If we want richer history commands or training-load-specific endpoints, we'll likely need to dig further into the Android app traffic / APK analysis.
