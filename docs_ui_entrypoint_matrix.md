# UI Entry Point Catalog & Risk Matrix

## Scope
This catalog covers UI entry points in:
- `ankigarden/ui/dashboard.py`
- `ankigarden/ui/garden_studio.py`
- `ankigarden/ui/scene.py`

## Entry points and surface mapping

### Dashboard header
- **Widget/container hierarchy**: `GardenDashboard._build_ui()` → root `QVBoxLayout` → `top: QFrame(card=true)` → `QHBoxLayout` containing `title_label`, chips (`streak_chip`, `progress_chip`, `health_chip`), and `settings_btn`.
- **Population method(s)**: `refresh_all()` sets chip text; static title set in `_build_ui()`.
- **Data source path(s)**:
  - `storage.state.streak_days`
  - `storage.state.daily_stats.reviewed`
  - `storage.state.daily_stats.accuracy`
  - `engine.garden_health_index()`

### Hero card
- **Widget/container hierarchy**: `GardenDashboard._build_ui()` → `hero_card: QFrame(card=true)` → `QVBoxLayout` with `GardenSceneWidget` (`self.scene`), `hero_summary`, `hero_growth`, `retrospective_note`.
- **Population method(s)**: `refresh_all()` updates `hero_summary`, `hero_growth`, and calls `self.scene.set_scene(payload)`; `show_retrospective_feedback()` updates `retrospective_note`.
- **Data source path(s)**:
  - `storage.state.garden_mode`, `storage.state.selected_weather`, `storage.state.daily_stats.growth_earned`, `storage.state.plants[*]`
  - `engine.get_weekly_event_summary()`, `engine.garden_health_index()`
  - `config.value('daily_growth_cap', 220)`

### Focus card
- **Widget/container hierarchy**: `GardenDashboard._focus_card()` → `QFrame(card=true)` → `QVBoxLayout` with heading `QLabel`, `focus_duration: QComboBox`, button row (`Start`, `Complete`, `Cancel`), `exam_date_input: QLineEdit`, exam toggle buttons.
- **Population method(s)**:
  - Initial combo fill in `_focus_card()`.
  - `refresh_all()` sets `exam_date_input` from state.
  - Button handlers `_start_focus()`, `_complete_focus()`, `_cancel_focus()`, `_set_exam_date()`, `_disable_exam()` mutate engine state and then refresh.
- **Data source path(s)**:
  - `config.nested('focus_mode', 'durations', default=[25,45,60])`
  - `storage.state.exam_mode.exam_date`
  - user text via `exam_date_input.text().strip()`
  - deck IDs from `mw.col.decks.all_names_and_ids()[:3]`

### Quest list
- **Widget/container hierarchy**: `GardenDashboard._build_ui()` mid row → `_simple_card('Daily Quests', self.quest_list)` where `quest_list` is `QListWidget`.
- **Population method(s)**: `refresh_all()` clears and appends items with fallback text if empty.
- **Data source path(s)**:
  - `storage.state.daily_quests[*].completed`
  - `storage.state.daily_quests[*].description`
  - `storage.state.daily_quests[*].progress`
  - `storage.state.daily_quests[*].target`

### Achievement list
- **Widget/container hierarchy**: mid row → `_simple_card('Achievements', self.achievement_list)`.
- **Population method(s)**: `refresh_all()` clears and appends from achievements map with fallback text if empty.
- **Data source path(s)**:
  - `storage.state.achievements.values()[*].unlocked`
  - `storage.state.achievements.values()[*].name`

### Inventory list
- **Widget/container hierarchy**: mid row → `_simple_card('Inventory & Boosts', self.inventory_list)`.
- **Population method(s)**: `refresh_all()` clears and appends first three items per non-empty category with fallback text if empty.
- **Data source path(s)**:
  - `storage.state.inventory.items()` where values are list-like item names

### Roster grid
- **Widget/container hierarchy**: lower card in `_build_ui()` → `QFrame(card=true)` → `QVBoxLayout` with `roster_title` and `QScrollArea` wrapping `roster_wrap`/`self.roster_grid: QGridLayout`; `_refresh_roster_cards()` creates one `QFrame(card=true)` per plant with title/stage/vitality/growth/map labels.
- **Population method(s)**: `refresh_all()` calls `_refresh_roster_cards()`.
- **Data source path(s)**:
  - `storage.state.garden_mode`
  - `storage.state.plants[*].{name,species,growth_stage,rare_variant,vitality,personality,growth_points,plant_id}`
  - `storage.state.deck_plant_map.items()`

### Settings tabs
- **Widget/container hierarchy**: `GardenSettingsDialog.__init__()` → root `QHBoxLayout` → `QTabWidget` tabs: `general` (`QFormLayout`), `mapping` (`QVBoxLayout`), `behavior` (`GardenStudioWidget`), `advanced` (`QVBoxLayout`).
- **Population method(s)**:
  - Init-time population in constructor.
  - Actions via `_apply_mode()`, `_map_deck()`, `_reroll_asset_slot()`.
- **Data source path(s)**:
  - `engine.state.garden_mode`
  - `engine.state.plants[*].{name,plant_id,species,growth_stage,rare_variant}`
  - `mw.col.decks.all_names_and_ids()`
  - behavior tab reads config through `GardenStudioWidget`

### Attribution cards
- **Widget/container hierarchy**: `GardenStudioWidget._build_ui()` → `attribution_frame: QFrame` → `QVBoxLayout`; per slot (`background`, `plant`, `weather`) card `QFrame` + `QHBoxLayout` containing attribution `QLabel` and reroll button.
- **Population method(s)**: `set_asset_attributions(attributions)` mutates each label; defaults set in `_build_ui()`.
- **Data source path(s)**:
  - method argument `attributions[slot]` fields: `page_url`, `source_url`, `author`, `license`
  - fallback literals for missing fields (`unknown source/author`, `license unknown`)

### Custom scene canvas
- **Widget/container hierarchy**:
  - Dashboard hero embeds `GardenSceneWidget`.
  - Garden Studio preview embeds separate `GardenSceneWidget`.
- **Population method(s)**:
  - `GardenSceneWidget.set_scene(payload)` for both callers.
  - Dashboard: `GardenDashboard.refresh_all()` builds payload from runtime state.
  - Studio: `_apply_preview()` builds synthetic payload from preview controls.
- **Data source path(s)**:
  - Scene payload fields consumed by painter: `weather`, `health`, `growth`, `plants`, optional `night_mode`, `animation_intensity`, `weather_particle_density`
  - Plant fields consumed by painter: `stage`, `vitality`, `rare_variant`

## One-page matrix

| Surface | File / Class / Method | Data dependency | Risk level |
|---|---|---|---|
| Dashboard header | `dashboard.py` / `GardenDashboard` / `_build_ui`, `refresh_all` | `storage.state.streak_days`, `daily_stats.reviewed`, `daily_stats.accuracy`, `engine.garden_health_index()` | **Medium** (runtime stats can be stale/missing; no guardrails) |
| Hero card | `dashboard.py` / `GardenDashboard` / `refresh_all`, `show_retrospective_feedback` | `storage.state.garden_mode`, `selected_weather`, `daily_stats.growth_earned`, `plants[*]`, `config.daily_growth_cap`, `engine.get_weekly_event_summary()` | **High** (long/malformed event text; divide-by-cap assumptions; large plant payload) |
| Focus card | `dashboard.py` / `GardenDashboard` / `_focus_card`, `refresh_all`, `_set_exam_date` | `config.focus_mode.durations`, `storage.state.exam_mode.exam_date`, user-entered date string, deck query from Anki collection | **High** (free-text date; optional/missing deck data; no input validation in UI) |
| Quest list | `dashboard.py` / `GardenDashboard` / `refresh_all` | `storage.state.daily_quests[*].description/progress/target/completed` | **High** (description length/malformed types; empty list fallback only) |
| Achievement list | `dashboard.py` / `GardenDashboard` / `refresh_all` | `storage.state.achievements.values()[*].name/unlocked` | **Medium** (empty map handled; long names can overflow) |
| Inventory list | `dashboard.py` / `GardenDashboard` / `refresh_all` | `storage.state.inventory` dict of category→list[str] | **Medium** (non-string items/join errors possible; truncates to 3 silently) |
| Roster grid | `dashboard.py` / `GardenDashboard` / `_refresh_roster_cards` | `storage.state.plants[*]`, `deck_plant_map`, `garden_mode` | **High** (large rosters, missing plant fields, unbounded card creation/perf) |
| Settings tabs | `dashboard.py` / `GardenSettingsDialog` / `__init__`, `_apply_mode`, `_map_deck`, `_reroll_asset_slot` | `engine.state.garden_mode`, `engine.state.plants`, `mw.col.decks.*`, config via `GardenStudioWidget` | **Medium** (deck access wrapped by broad exceptions; silent failures) |
| Attribution cards | `garden_studio.py` / `GardenStudioWidget` / `_build_ui`, `set_asset_attributions` | `attributions[slot].page_url/source_url/author/license` | **Medium** (missing fields handled, but long URLs/text can bloat labels) |
| Custom scene canvas | `scene.py` / `GardenSceneWidget` / `set_scene`, `paintEvent`; plus callers `refresh_all` and `_apply_preview` | payload dict keys with numeric/string coercion, plant subfields | **High** (malformed payload types can trigger fallback; broad exception masks issues) |

## Dynamic text sources with edge-case risk

Potentially empty / long / malformed / missing sources:
- `engine.get_weekly_event_summary()` in hero summary (could be empty or arbitrarily long).
- `daily_quests[*].description`, `progress`, `target` (type/format risk; very long descriptions).
- `achievements[*].name` (long/empty names).
- `inventory` category names and item entries used in `', '.join(...)` (non-string or long values).
- Plant display fields (`name`, `species`, `growth_stage`, `personality`) in roster labels (empty/long/malformed).
- `exam_date_input` free text and `state.exam_mode.exam_date` echo (invalid date strings; empty allowed).
- Attribution metadata fields (`author`, `license`, URLs) in `set_asset_attributions` (missing handled, but malformed/very long URLs render verbatim).
- Scene payload text-like enum fields (`weather`, plant `stage`) and numeric-like fields (`growth`, `health`, `vitality`) that may arrive malformed; `paintEvent` catches exceptions and falls back.
