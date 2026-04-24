# UI Data Contracts (Garden State Boundary)

This document defines the response contract consumed by the UI from `GardenState.from_dict()`.
The boundary is the persisted payload loaded from `ankigarden/garden_state.json`.

## Endpoint: `garden_state.json` payload

### Root fields used by UI

- `streak_days` (required, `int`)
- `selected_weather` (required, `str`, enum: `sunny|cloudy|breeze|gentle_rain|fireflies`)
- `garden_mode` (required, `str`, enum: `unified|deck-by-deck`)
- `last_active_day` (required, `str`, ISO date `YYYY-MM-DD`)
- `plants` (required, `list[object]`)
- `daily_quests` (required, `list[object]`)
- `achievements` (required, `dict[str, object]`)
- `daily_stats` (required, `object`)
- `inventory` (required, `dict[str, list[str]]`)
- `deck_plant_map` (required, `dict[str, str]`)
- `focus_session` (required, `object`)
- `exam_mode` (required, `object`)

### Nested contracts

#### `plants[]`

Required:
- `plant_id: str`
- `species: str`
- `name: str`
- `slot_index: int`

Optional:
- `growth_points: int`
- `vitality: float`
- `rare_variant: bool`
- `assigned_deck_id: int | null`
- `personality: str`

Behavior:
- Invalid item shape -> item is dropped.
- Optional invalid type -> field falls back to default.

#### `daily_stats`

Required keys:
- `day: str` (ISO date)
- `reviewed, correct, wrong, new_count, learning_count, review_count, difficult_count, recovered_lapses, growth_earned, focus_sessions_completed: int`
- `completed_due_cards: bool`

Behavior:
- Missing/invalid keys fall back to default values.
- Malformed `day` falls back to current local date.

#### `focus_session`

Required keys:
- `active: bool`
- `duration_minutes: int`
- `deep_work_streak: int`

Optional:
- `started_at: str | null`

Behavior:
- Invalid fields fall back to defaults.

#### `exam_mode`

Required keys:
- `enabled: bool`
- `target_deck_ids: list[int]`
- `focus_species: str`

Optional:
- `exam_date: str | null` (ISO date if string)

Behavior:
- Malformed `exam_date` -> `null`.
- Invalid `target_deck_ids` item types -> `[]`.

## Validation and mismatch handling

- Validation is run in `GardenState.from_dict()` before model hydration.
- Unknown or wrong-typed fields are ignored/sanitized.
- Field-level contract mismatches are logged as one aggregated error record.

## CI protection

Regression tests in `tests/test_state_contract_validation.py` cover:
- missing keys
- null values
- unexpected enum/status
- type mismatch
- malformed date

These tests are expected to run in CI and fail on contract-breaking changes affecting UI-visible fields.
