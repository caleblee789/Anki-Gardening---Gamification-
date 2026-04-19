# Anki Garden 🌿

Anki Garden is a complete Anki add-on that turns daily studying into a calm, long-term garden habit loop:

**study cards consistently → earn growth energy → grow a multi-slot garden with real photographic assets**.

This add-on is designed to feel rewarding and polished without being noisy, childish, or manipulative.

## What’s Implemented

### Core gameplay loop
- Real review activity drives growth points (new/learning/review configurable values).
- Daily growth cap prevents unhealthy over-grinding.
- Daily goal and focus-plant bonus support exam periods.
- Gentle missed-day handling with streak grace and recovery mode.

### Garden simulation
- Multiple plant slots with milestone slot unlocks.
- Plant growth stages:
  - seed
  - sprout
  - young
  - mature
  - flowering
  - rare variant
- Species personalities (streak / accuracy / volume / difficult / morning / night) influence growth patterns.
- Plant vitality rises with consistency and decays gently with missed days.

### Quests, achievements, progression
- 1–3 daily quests selected from a quest pool based on difficulty.
- Achievement milestones:
  - 7 day streak
  - 100 reviews/day
  - 1000 total reviews
  - 90% daily retention
  - finish all due cards
  - moonflower (late-night studying)
  - sunbloom (early study)
- Currency (“dew drops”) and shop unlockables.

### Deck integration and focus tools
- Optional deck-specific mode.
- Deck-to-plant assignment UI.
- Focus plant assignment UI.

### Recovery and sustainable design
- Missed days do not reset progress.
- Streak freeze token support.
- Recovery mode messaging for fast comeback.
- Weather mood adapts to study consistency (sunny/cloudy/fireflies/rain/breeze).

## Real Image Sourcing (No Placeholders)

No static mock image assets are bundled.

Anki Garden uses a live `AssetManager` with:
- Unsplash API
- Pexels API
- Pixabay API

System behavior:
1. Build semantic search query for requested visual (plant stage/background/decoration/weather).
2. Query providers in configured priority order.
3. Apply request rate limiting.
4. Retry failed requests.
5. Download first matching real image.
6. Cache locally and reuse offline.
7. Save attribution/source metadata to `assets/asset_metadata.json`.
8. Never re-download same source URL unnecessarily.

## Add-on Structure

```text
ankigarden/
  __init__.py
  addon.py
  asset_manager.py
  config.py
  config.json
  game.py
  storage.py
  meta.json
  hooks/
    reviewer.py
  models/
    state.py
  ui/
    dashboard.py
  assets/
    plants/
    backgrounds/
    decorations/
    weather/
    ui/
```

## Installation

1. Copy `ankigarden/` into your Anki add-ons directory.
2. Restart Anki.
3. Open **Tools → Anki Garden**.
4. Add at least one image provider API key in add-on config.

## API Keys Setup

In Anki: **Tools → Add-ons → Anki Garden → Config**

```json
"image_api": {
  "provider_priority": ["unsplash", "pexels", "pixabay"],
  "unsplash_access_key": "YOUR_UNSPLASH_KEY",
  "pexels_api_key": "YOUR_PEXELS_KEY",
  "pixabay_api_key": "YOUR_PIXABAY_KEY",
  "request_timeout_sec": 8,
  "max_retries": 3,
  "rate_limit_seconds": 1.2
}
```

## Config Overview

`config.json` includes:
- visual toggles (`enable_animations`, `seasonal_visuals`, `show_reviewer_button`, `show_toolbar_button`)
- growth balancing (`daily_growth_cap`, `daily_goal`, `points_per_card`, `focus_target_bonus`)
- habit safety (`streak_grace_period_days`, `allow_streak_freeze`, `vitality_decay_sensitivity`)
- progression (`quest_difficulty`, `max_daily_quests`, `initial_slots`, `max_slots`)
- asset settings (`image_api.*`)
- optional future flags (`future_features.*`)

## Persistence

Local state file: `ankigarden/garden_state.json`

Persisted data includes:
- plant inventory and slot placements
- growth, vitality, rare variants
- streak history and daily stats
- quests, achievements, currency, purchases
- deck mappings, focus plant
- journal entries
- equipped cosmetics/weather

## Future-ready feature flags

The add-on already ships config flags for planned extensions:
- cloud sync scaffold
- social/shared gardens
- weekly event rotations

These are disabled by default and non-invasive.

## Packaging

Zip the `ankigarden/` directory to distribute/test as an Anki add-on package.
