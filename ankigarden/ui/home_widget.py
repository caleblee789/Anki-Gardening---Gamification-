from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from ..display_telemetry import DISPLAY_TELEMETRY
from .formatters import format_integer, format_percent, format_status_label


@dataclass(frozen=True)
class HomeWidgetData:
    cards_today: int
    health_ratio: float
    growth_earned: int
    growth_cap: int
    streak_days: int
    weather: str
    event: str
    plants_html: str


@dataclass(frozen=True)
class HomeWidgetSnapshot:
    request_id: int
    phase: str
    data: HomeWidgetData | None = None
    error_message: str | None = None


class HomeWidgetStateController:
    """Tracks request lifecycles and protects the UI against stale responses."""

    def __init__(self) -> None:
        self._next_request_id = 0
        self.snapshot = HomeWidgetSnapshot(request_id=0, phase="empty")

    def begin_request(self) -> int:
        self._next_request_id += 1
        req_id = self._next_request_id
        self.snapshot = HomeWidgetSnapshot(request_id=req_id, phase="loading")
        return req_id

    def resolve_success(self, request_id: int, data: HomeWidgetData) -> bool:
        if request_id != self.snapshot.request_id:
            return False
        self.snapshot = HomeWidgetSnapshot(request_id=request_id, phase="success", data=data)
        return True

    def resolve_partial(self, request_id: int, data: HomeWidgetData, error_message: str) -> bool:
        if request_id != self.snapshot.request_id:
            return False
        self.snapshot = HomeWidgetSnapshot(
            request_id=request_id,
            phase="partial",
            data=data,
            error_message=error_message,
        )
        return True

    def resolve_error(self, request_id: int, error_message: str) -> bool:
        if request_id != self.snapshot.request_id:
            return False
        self.snapshot = HomeWidgetSnapshot(request_id=request_id, phase="error", error_message=error_message)
        return True


DEFAULT_ERROR_MESSAGE = "Unable to load garden stats right now. Retry to refresh." 


def render_home_widget(snapshot: HomeWidgetSnapshot) -> str:
    DISPLAY_TELEMETRY.track_render("home_widget")
    phase = snapshot.phase
    if phase == "loading":
        return (
            '<div id="ag-home-root" data-state="loading">'
            '<div data-testid="home-loading">Loading garden…</div>'
            "</div>"
        )
    if phase == "empty":
        return (
            '<div id="ag-home-root" data-state="empty">'
            '<div data-testid="home-empty">No garden data yet. Start reviewing to grow your first plant.</div>'
            "</div>"
        )
    if phase == "error":
        message = escape(snapshot.error_message or DEFAULT_ERROR_MESSAGE)
        return (
            '<div id="ag-home-root" data-state="error">'
            f'<div data-testid="home-error">{message}</div>'
            '<button data-testid="home-retry" type="button">Retry</button>'
            "</div>"
        )

    data = snapshot.data
    if data is None:
        DISPLAY_TELEMETRY.record_missing_or_invalid_field(
            route="home_widget",
            field="payload",
            reason="snapshot_data_missing",
            required=True,
        )
        return (
            '<div id="ag-home-root" data-state="error">'
            '<div data-testid="home-error">Invalid home widget payload.</div>'
            "</div>"
        )
    if not data.event:
        DISPLAY_TELEMETRY.track_fallback(route="home_widget", field="event")
    if not data.weather:
        DISPLAY_TELEMETRY.track_fallback(route="home_widget", field="weather")

    growth_cap = max(1, data.growth_cap)
    growth_pct = int(min(100, (data.growth_earned / growth_cap) * 100))
    partial_banner = ""
    if phase == "partial":
        partial_error = escape(snapshot.error_message or "Some details are temporarily unavailable.")
        partial_banner = f'<div data-testid="home-partial-error">{partial_error}</div>'

    return f"""
<div id=\"ag-home-root\" data-state=\"{escape(phase)}\">
  {partial_banner}
  <div data-testid=\"home-streak\">{format_integer(data.streak_days)}d streak</div>
  <div data-testid=\"home-plants\">{data.plants_html}</div>
  <div data-testid=\"home-cards\">Cards Today: {format_integer(data.cards_today)}</div>
  <div data-testid=\"home-health\">Garden Health: {format_percent(data.health_ratio, places=0)}</div>
  <div data-testid=\"home-weather\">Weather: {format_status_label(data.weather)}</div>
  <div data-testid=\"home-growth\">Growth today: {format_integer(data.growth_earned)}/{format_integer(growth_cap)}</div>
  <div data-testid=\"home-growth-bar\" style=\"width:{growth_pct}%\"></div>
  <div data-testid=\"home-event\">Event: {escape(data.event)}</div>
  <button data-testid=\"home-refresh\" type=\"button\">Refresh</button>
</div>
"""


def build_home_widget_success_data(*, state: Any, cards_today: int, health_ratio: float, growth_cap: int, plants_html: str, event: str) -> HomeWidgetData:
    stats = state.daily_stats
    if getattr(state, "selected_weather", None) in (None, ""):
        DISPLAY_TELEMETRY.record_missing_or_invalid_field(
            route="home_widget",
            field="selected_weather",
            reason="missing_or_empty",
            value=getattr(state, "selected_weather", None),
        )
    if event in (None, ""):
        DISPLAY_TELEMETRY.record_missing_or_invalid_field(
            route="home_widget",
            field="event",
            reason="missing_or_empty",
            value=event,
        )
    return HomeWidgetData(
        cards_today=cards_today,
        health_ratio=health_ratio,
        growth_earned=int(stats.growth_earned),
        growth_cap=int(growth_cap),
        streak_days=int(state.streak_days),
        weather=str(state.selected_weather or "N/A"),
        event=event or "N/A",
        plants_html=plants_html,
    )
