import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ankigarden.display_telemetry import AlertThresholds, DisplayTelemetry


def test_fallback_rate_is_tracked_per_route_and_field() -> None:
    telemetry = DisplayTelemetry()
    telemetry.track_render("home_widget")
    telemetry.track_render("home_widget")
    telemetry.track_fallback(route="home_widget", field="event")

    assert telemetry.fallback_rate(route="home_widget", field="event") == 0.5


def test_report_lines_include_top_failing_fields() -> None:
    telemetry = DisplayTelemetry()
    telemetry.track_render("dashboard")
    telemetry.record_missing_or_invalid_field(route="dashboard", field="weather", reason="missing")
    telemetry.track_fallback(route="dashboard", field="weather")

    lines = telemetry.report_lines()

    assert any("Top failing fields by route" in line for line in lines)
    assert any("dashboard.weather" in line for line in lines)


def test_alert_emits_after_threshold_crossed(caplog) -> None:
    telemetry = DisplayTelemetry(thresholds=AlertThresholds(api_contract_failures=2))

    telemetry.record_missing_or_invalid_field(route="home_widget", field="event", reason="missing")
    telemetry.record_missing_or_invalid_field(route="home_widget", field="event", reason="missing")

    assert '"kind": "api_contract_failures"' in caplog.text
