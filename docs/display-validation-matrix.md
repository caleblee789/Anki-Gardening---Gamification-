# Display Validation Matrix

This matrix inventories dynamic/user-visible fields in Anki Garden and maps each to its source of truth.

## Source system legend
- **Garden state store:** `GardenStorage.state` loaded from `ankigarden/garden_state.json` via `GardenState.from_dict`.
- **Anki collection API/DB:** `mw.col...` calls (deck list, revlog counts, card/deck lookups).
- **Engine-derived values:** `GardenGameEngine` methods that compute aggregates from state/config.

## Verification matrix

| Priority | UI location (route/component) | Label shown to user | Backend/API source (endpoint + response key) | Local transform / format function | Fallback / null-empty behavior |
|---|---|---|---|---|---|
| **High** | Home widget (`AnkiGardenApp._build_home_garden_html`) | `Xd streak` (header) | Local state store (`garden_state.json` -> `streak_days`) via `self.storage.state.streak_days` | Integer interpolated into header string | If widget render fails, generic fallback block only (`Anki Garden`), streak hidden |
| **High** | Home widget | `Cards Today` | Anki DB query: `select count(distinct cid) from revlog where id > ?` (derived from `mw.col.sched.day_cutoff`); fallback local state `daily_stats.reviewed` | `_cards_reviewed_today()` casts to int and clamps `>=0`; formatted with thousands separator `{cards_today:,}` | If collection/scheduler unavailable or query fails, uses local `daily_stats.reviewed` |
| **High** | Home widget | `Garden Health` | Engine aggregate (`garden_health_index()`), using daily stats + plants + streak + recency | Multiplied by 100 and cast to int (`health_pct`) | On widget exception, entire widget falls back to minimal static block |
| **High** | Home widget | `Weather` | Local state store key `selected_weather` | `str(...).replace('_',' ').title()` | On widget exception, weather omitted in fallback block |
| **High** | Home widget | `Growth today: X/Y` | Local state key `daily_stats.growth_earned`; config `daily_growth_cap` | `growth_cap=max(1, cap)`; string interpolation | If exception, hidden by widget-level fallback |
| Medium | Home widget | `Event: ...` | Engine method `get_weekly_event_summary()` -> `current_weekly_event()` from config-driven weekly event list | Direct string interpolation | If exception, hidden by widget-level fallback |
| Medium | Home widget plant badges | Plant emoji for each plant | Local state `plants[].growth_points` (through `growth_stage`) + `plants[].rare_variant` | `_plant_emoji_for_stage(stage, rare)` mapping | If no plants, shows default seedling badge (`🌱 Seedling`) |
| Medium | Home widget plant badges | Plant name | Local state `plants[].name` | direct | If no plants, default seedling badge name |
| **High** | Dashboard top chips (`GardenDashboard.refresh_all`) | `Streak Nd` | Local state key `streak_days` | `f"Streak {state.streak_days}d"` | If missing, dataclass default `0` |
| **High** | Dashboard top chips | `Today reviewed • accuracy%` | Local state `daily_stats.reviewed`; computed property `daily_stats.accuracy` | Accuracy multiplied by 100 and int-cast | If no reviews accuracy property returns `0` |
| **High** | Dashboard top chips | `Health NN` | Engine `garden_health_index()` | `int(health * 100)` | Engine uses conservative defaults (`acc=0.7`, `max(1,len(plants))`) to avoid nulls |
| **High** | Hero summary text | `Unified all-decks` / `Deck-by-deck` mode token | Local state key `garden_mode` | conditional mapping to display text | Defaults to unified text if value not `deck-by-deck` |
| Medium | Hero summary text | `Weather: ...` | Local state `selected_weather` | direct interpolation | State default `sunny` |
| Medium | Hero summary text | `Event: ...` | Engine `get_weekly_event_summary()` | direct interpolation | If weekly events disabled, engine emits `No Active Event: Weekly events disabled.` |
| **High** | Hero growth progress bar | `Daily growth %p%` value + fill | Local state `daily_stats.growth_earned`; config `daily_growth_cap` | `growth_pct = int(min(100, earned / max(1,cap) * 100))` | Cap guarded with `max(1, ...)`; 0 growth renders 0% |
| **High** | Live scene overlay (`GardenSceneWidget`) | `Daily growth energy: N%` | Scene payload key `growth` set from `daily_stats.growth_earned / cap` | `_sanitize_scene_payload` clamps 0..1 then `int(growth * 100)` | On render exceptions or no plants, fallback scene message rendered |
| Medium | Live scene overlay | `Your live study garden` | Static label (no backend key) | none | Always shown unless paint fallback; then fallback message shown |
| Medium | Quest list | Quest entries (`✅/🌱 description progress/target`) | Local state `daily_quests[].{completed,description,progress,target}` | Marker mapping (`completed` -> ✅ else 🌱), string concatenation, `_add_list_entry` elide/truncate | If no quests, shows `No quest progress yet today...` empty-state item |
| Medium | Achievement list | Achievement entries (`🏅/🔒 name`) | Local state `achievements[*].{unlocked,name}` | Marker mapping (`unlocked` -> 🏅 else 🔒), `_add_list_entry` elide/truncate | If none, shows `Achievement progress will appear...` |
| **High** | Inventory list | Category boosts (`category: item1, item2...`) | Local state `inventory` dict | Includes first 3 items per non-empty category; `_add_list_entry` elide/truncate | If no non-empty categories, shows `No active inventory boosts yet.` |
| **High** | Focus/Exam card | Focus duration options (`N min`) | Config key `focus_mode.durations` | each entry cast to int and displayed as `"{minutes} min"` | If config missing, defaults `[25,45,60]` |
| **High** | Focus/Exam card | Exam date input current value | Local state `exam_mode.exam_date` | `self.exam_date_input.setText(value or "")` | `None` becomes empty string |
| **High** | Focus/Exam card | Exam date validation tooltip/errors | Input text (user-entered), validated by regex/date parse | `_validate_exam_value`: `YYYY-MM-DD` regex + `date.fromisoformat`; set tooltip + border style | Empty input disables Set button and restores default tooltip; invalid format/date disables Set button |
| Medium | Retrospective note | `Applied catch-up ... +growth from N reviews` | Runtime values from retrospective sync (`review_count`, `growth_gain`) | String interpolation in `show_retrospective_feedback` | If `review_count<=0`, label cleared to empty |
| Medium | Roster section title | `Garden Regions` / `Deck-Mapped Plants` | Local state `garden_mode` | conditional label | If unknown mode, falls to `Deck-Mapped Plants` branch only when exact deck mode; otherwise `Garden Regions` |
| Medium | Roster card | `PlantName • Species` | Local state `plants[].{name,species}` | `species.title()` | No roster -> global empty-state message |
| Medium | Roster card | `Stage: ...` (+✨ rare) | Local state `plants[].growth_points` via `growth_stage` property and `rare_variant` flag | `growth_stage.title()` and suffix sparkle if rare | No roster -> empty-state message |
| **High** | Roster card vitality bar | `Vitality %p%` + value | Local state `plants[].vitality` | `int(vitality * 100)` | Dataclass default vitality `1.0`; engine clamps in scene usage |
| **High** | Roster card growth/source line | `Growth Source: personality • GP growth_points` | Local state `plants[].{personality,growth_points}` | direct interpolation | Defaults exist (`personality="balanced"`, `growth_points=0`) |
| Medium | Roster card deck mapping line | `Deck #id` or `All-Deck Contributor` | Local state `deck_plant_map{deck_id: plant_id}` matched against current plant | Iterates map and first matching deck id wins | No mapping match -> `All-Deck Contributor` |
| Medium | Settings > General (`GardenSettingsDialog`) | Garden growth mode selected value | Local state `garden_mode` | maps `unified/deck-by-deck` to combo index and labels | Invalid value treated as unified |
| Medium | Settings > Deck Mapping | Plant dropdown options | Local state `plants[].{name,plant_id}` | each plant added as combo item | If no plants, combo effectively empty |
| Medium | Settings > Deck Mapping | Deck dropdown options | Anki Collection API: `mw.col.decks.all_names_and_ids()` -> each `{name,id}` | direct add to combo | On exception, set `_deck_load_failed=True` and show `Unable to load decks...` |
| Medium | Settings > Visuals & Behavior (GardenStudioWidget) | Theme selection current value | Config `visual_theme` | humanized text via `replace('_',' ').title()` and combo current text | Defaults to `verdant_dusk` |
| Medium | Settings > Visuals & Behavior | Asset quality current value | Config `asset_quality` | combo lookup `findData(current_quality)` with `max(0, idx)` | unknown value falls back to first option (`Balanced`) |
| Medium | Settings > Visuals & Behavior | Animation intensity slider | Config nested `theme_overrides.animation_intensity` | float 0-1 mapped to 0-100 slider | Default 0.7 if missing |
| Medium | Settings > Visuals & Behavior | Weather particle density slider | Config nested `theme_overrides.weather_particle_density` | float 0-1 mapped to slider (10-200) | Default 1.0 if missing |
| Medium | Settings > Visuals & Behavior | Preview scene weather/stage/night | Local preview state (`self.preview`) driven by controls | `_apply_preview()` maps stage -> growth scalar, builds `scene_payload` | Scene widget sanitizes/clamps payload; missing plants replaced by preview plant |
| Medium | Settings > Visuals & Behavior > Asset Sources | Source attribution line per slot (`Background/Plant/Weather source: author • license • source`) | Input dict to `set_asset_attributions(attributions)` using keys per slot: `page_url/source_url`, `author`, `license` | Builds full label, truncates to max chars, elides by pixel width; tooltip contains full text when truncated | Missing keys replaced with `unknown source/author/license unknown`; if absent altogether, card starts with `Source details unavailable...` |

## Critical strict-validation checklist

The following should be treated as **strict/high-priority validation fields** in QA sign-off:

1. **Scores & performance indicators**
   - `Today reviewed • accuracy%` chip
   - `Garden Health` (home + dashboard)
2. **Progress indicators**
   - Hero growth bar `%`
   - Scene `Daily growth energy: N%`
   - Quest `progress/target`
3. **Streaks**
   - Home header streak
   - Dashboard streak chip
4. **Timestamps / date-sensitive fields**
   - Exam date input (format + parsing + enablement)
   - Cards-today calculation based on Anki day cutoff
5. **Reward counts / economy-affecting fields**
   - Inventory boosts list content
   - Focus completion outcomes that alter growth/currency (reflected in refreshed dashboard state)

## Notes for product/dev/QA

- This project currently has **no remote HTTP backend endpoints** for the displayed fields above; sources are local persisted state, computed engine outputs, and Anki collection APIs.
- For test-case design, treat `garden_state.json` keys as the equivalent of API response keys for field provenance.
