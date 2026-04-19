# UI State Scenarios and Expected Rendering

This document defines concrete UI expectations for high-risk runtime states in the dashboard and settings flow.

## Rendering contract references
- Header chips are rendered in `GardenDashboard.refresh_all()` as:
  - `Streak {state.streak_days}d`
  - `Today {stats.reviewed} • {int(stats.accuracy * 100)}%`
  - `Health {int(engine.garden_health_index() * 100)}`
- Hero summary and growth are rendered in `GardenDashboard.refresh_all()`.
- Focus/exam controls are rendered in `_focus_card()` and hydrated in `refresh_all()`.
- Roster composition is rendered in `_refresh_roster_cards()`.
- Scene payload is sent through `GardenSceneWidget.set_scene(...)`.

---

## Scenario 1: Fresh user
**State shape**
- `streak_days = 0`
- `daily_stats.reviewed = 0`, `daily_stats.accuracy = 0.0`, `daily_stats.growth_earned = 0`
- `plants = []`, `daily_quests = []`, `achievements = {}`, `inventory = {}`
- `exam_mode.exam_date = None`

**Expected output**
- **Header chips**
  - `Streak 0d`
  - `Today 0 • 0%`
  - `Health <0-100>` (human-facing numeric health score; no internal key names)
- **Hero summary/progress**
  - Summary starts with `Unified all-decks mode` or `Deck-by-deck mode` and includes weather/event in prose.
  - Progress bar shows `Daily growth 0%`.
- **Focus/exam card controls**
  - Duration combo populated from configured durations.
  - Exam field is empty and placeholder shows `YYYY-MM-DD...` guidance.
- **Roster composition**
  - Single empty-state message: `No plants in your roster yet. Add reviews to grow your first companion.`
- **`GardenSceneWidget.set_scene` payload**
  - `weather`: selected weather string.
  - `health`: computed float from engine.
  - `growth`: `0.0`.
  - `plants`: empty list.

---

## Scenario 2: Active streak
**State shape**
- `streak_days > 0`, `reviewed > 0`, `accuracy` in `(0, 1]`
- at least one plant in `plants`

**Expected output**
- **Header chips**
  - Human-readable streak/progress/health values (no Python repr, no internal field names).
- **Hero summary/progress**
  - Motivational sentence remains present after weather/event line.
  - Progress bar is clamped to `0..100` and reflects daily growth cap.
- **Focus/exam card controls**
  - Start/Complete/Cancel buttons available.
  - Exam date field mirrors current exam date (or empty string if none).
- **Roster composition**
  - One card per plant with title (`name • Species`), stage label, vitality progress, growth source line, deck mapping label.
- **Scene payload**
  - `plants` contains one entry per plant with: `name`, `species`, `stage`, `vitality`, `rare_variant`.

---

## Scenario 3: Burnout / recovery
**State shape**
- Low health index and low vitality plants, optionally low accuracy.

**Expected output**
- **Header chips**: `Health` chip numerically reflects low health (still human readable).
- **Hero summary/progress**: summary still presents plain-language guidance (never raw JSON/state dumps).
- **Focus/exam controls**: remain functional; no control text changes to internal values.
- **Roster composition**: vitality bars visibly lower values, but labels stay friendly (`Vitality %p%`).
- **Scene payload**
  - `health` and `plants[*].vitality` carry low floats; rendering adapts glow/leaf alpha accordingly.

---

## Scenario 4: Empty deck mapping (deck-by-deck mode)
**State shape**
- `garden_mode = "deck-by-deck"`
- `deck_plant_map = {}`

**Expected output**
- **Header chips / hero / focus**: unchanged format.
- **Roster composition**
  - Roster title: `Deck-Mapped Plants`.
  - Each plant card mapping line falls back to `All-Deck Contributor` when no deck is assigned.
- **Scene payload**: unaffected; still driven by plant list and growth/health values.

---

## Scenario 5: Exam mode enabled
**State shape**
- `exam_mode.exam_date` is non-empty (`YYYY-MM-DD` expected by UI copy).

**Expected output**
- **Focus/exam controls**
  - Date field is prefilled with stored date.
  - `Set Exam Date` applies chosen date/decks via engine.
  - `Turn Off Exam Mode` clears active exam targeting on refresh.
- **Other surfaces**
  - Header/hero/roster formats remain plain-language and stable.
- **Scene payload**
  - No exam-specific fields injected by dashboard payload (expected).

---

## Scenario 6: Exam mode disabled
**State shape**
- `exam_mode.exam_date = None`.

**Expected output**
- **Focus/exam controls**
  - Empty date field with explicit date placeholder and tooltip example.
  - Disable action keeps field empty after refresh.
- **Scene payload**: unchanged relative to non-exam states.

---

## Scenario 7: No plants
**State shape**
- `plants = []` (regardless of mode).

**Expected output**
- **Roster composition**: empty-state helper text shown instead of empty cards.
- **Scene payload**: `plants: []`.
- **Scene rendering**: widget draws fallback scene content while preserving tracked progress language.

---

## Scenario 8: Multiple plants
**State shape**
- `len(plants) >= 2`.

**Expected output**
- **Roster composition**
  - Card grid shows one card per plant in row/column layout.
  - Each card keeps human-friendly labels for stage, vitality, growth source, and mapping.
- **Scene payload**
  - `plants` includes all visible plants with per-plant stage/vitality/rare flags.

---

## Scenario 9: Missing asset attribution
**State shape**
- Studio attribution payload omits one or more of: `page_url`, `source_url`, `author`, `license`.

**Expected output**
- **Behavior tab attribution cards**
  - Missing fields fall back to user-readable phrases (`unknown source`, `unknown author`, `license unknown`).
  - Link CTA text remains human-facing (`view page`, `source`).
- **Scene payload**
  - No direct payload impact; dashboard scene remains stable.

---

## Human-readable messaging verification
Across the scenarios above, dashboard/settings surfaces avoid raw internal fields and use user-facing copy:
- Chips and cards use prose labels (`Streak`, `Today`, `Health`, `Stage`, `Growth Source`, etc.).
- Empty states are explicit (`No quest progress yet today...`, `No plants in your roster yet...`).
- Mapping and mode controls provide confirmation/warning dialogs instead of silent failures.

## Settings confirmations and failure paths
### Positive confirmations
- Saving mode shows `Garden mode updated.` confirmation dialog.
- Successful deck mapping shows `Deck mapping updated.` confirmation dialog.

### Clear failure paths
- If deck data cannot be loaded, mapping action warns: `Deck mapping is unavailable right now because deck data could not be loaded.`
- If either deck or plant is missing selection, mapping action warns: `Pick both a deck and a plant before assigning a mapping.`
- Deck selector includes a readable unavailable option when deck loading fails.
