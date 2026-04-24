from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertThresholds:
    api_contract_failures: int = 5
    empty_state_spike: int = 5
    parsing_exceptions: int = 3


class DisplayTelemetry:
    """In-memory UI/display telemetry for operational debugging and alerting."""

    def __init__(self, thresholds: AlertThresholds | None = None) -> None:
        self.thresholds = thresholds or AlertThresholds()
        self._render_count_by_route: Counter[str] = Counter()
        self._fallback_count_by_field: Counter[tuple[str, str]] = Counter()
        self._api_contract_failures_by_field: Counter[tuple[str, str]] = Counter()
        self._empty_state_count_by_view: Counter[tuple[str, str]] = Counter()
        self._parsing_exceptions_by_field: Counter[tuple[str, str]] = Counter()
        self._last_alert_count: defaultdict[str, int] = defaultdict(int)

    def track_render(self, route: str) -> None:
        self._render_count_by_route[route] += 1

    def record_missing_or_invalid_field(
        self,
        *,
        route: str,
        field: str,
        reason: str,
        value: Any = None,
        required: bool = True,
    ) -> None:
        self._api_contract_failures_by_field[(route, field)] += 1
        payload = {
            "kind": "display_contract_failure",
            "route": route,
            "field": field,
            "reason": reason,
            "required": required,
            "value": value,
        }
        logger.warning("Anki Garden telemetry %s", json.dumps(payload, default=str, sort_keys=True))
        self._emit_spike_alert_if_needed("api_contract_failures", self.total_api_contract_failures)

    def track_fallback(self, *, route: str, field: str, fallback: str = "N/A") -> None:
        self._fallback_count_by_field[(route, field)] += 1
        payload = {
            "kind": "display_fallback_used",
            "route": route,
            "field": field,
            "fallback": fallback,
            "fallback_count": self._fallback_count_by_field[(route, field)],
            "fallback_rate": self.fallback_rate(route=route, field=field),
        }
        logger.info("Anki Garden telemetry %s", json.dumps(payload, default=str, sort_keys=True))

    def track_empty_state(self, *, route: str, view: str, expected_non_empty: bool) -> None:
        self._empty_state_count_by_view[(route, view)] += 1
        payload = {
            "kind": "display_empty_state",
            "route": route,
            "view": view,
            "expected_non_empty": expected_non_empty,
            "empty_state_count": self._empty_state_count_by_view[(route, view)],
        }
        logger.info("Anki Garden telemetry %s", json.dumps(payload, default=str, sort_keys=True))
        if expected_non_empty:
            self._emit_spike_alert_if_needed("empty_state_spike", self.total_empty_state_expected_non_empty)

    def track_parsing_exception(self, *, route: str, field: str, exc: Exception) -> None:
        self._parsing_exceptions_by_field[(route, field)] += 1
        payload = {
            "kind": "display_parsing_exception",
            "route": route,
            "field": field,
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "exception_count": self._parsing_exceptions_by_field[(route, field)],
        }
        logger.warning("Anki Garden telemetry %s", json.dumps(payload, default=str, sort_keys=True))
        self._emit_spike_alert_if_needed("parsing_exceptions", self.total_parsing_exceptions)

    @property
    def total_api_contract_failures(self) -> int:
        return sum(self._api_contract_failures_by_field.values())

    @property
    def total_empty_state_expected_non_empty(self) -> int:
        return sum(self._empty_state_count_by_view.values())

    @property
    def total_parsing_exceptions(self) -> int:
        return sum(self._parsing_exceptions_by_field.values())

    def fallback_rate(self, *, route: str, field: str) -> float:
        renders = max(1, self._render_count_by_route.get(route, 0))
        return self._fallback_count_by_field.get((route, field), 0) / renders

    def _emit_spike_alert_if_needed(self, alert_kind: str, current_count: int) -> None:
        threshold = getattr(self.thresholds, alert_kind)
        previous = self._last_alert_count[alert_kind]
        if current_count < threshold:
            return
        if current_count - previous < threshold:
            return
        self._last_alert_count[alert_kind] = current_count
        logger.error(
            "Anki Garden alert %s",
            json.dumps({"kind": alert_kind, "count": current_count, "threshold": threshold}, sort_keys=True),
        )

    def report_lines(self, limit: int = 8) -> list[str]:
        lines = [
            f"API contract failures: {self.total_api_contract_failures}",
            f"Expected-non-empty empty states: {self.total_empty_state_expected_non_empty}",
            f"Parsing/formatting exceptions: {self.total_parsing_exceptions}",
            "Top failing fields by route:",
        ]
        aggregate = Counter()
        aggregate.update(self._api_contract_failures_by_field)
        aggregate.update(self._fallback_count_by_field)
        aggregate.update(self._parsing_exceptions_by_field)
        for (route, field), count in aggregate.most_common(limit):
            rate = self.fallback_rate(route=route, field=field)
            lines.append(f"- {route}.{field}: {count} issues, fallback rate {rate:.1%}")
        if len(lines) == 4:
            lines.append("- No issues detected yet.")
        return lines


DISPLAY_TELEMETRY = DisplayTelemetry()
