# Anki Garden 🌿

Anki Garden is a production-ready Anki add-on that gamifies study consistency with a calm garden progression loop:

**review cards consistently → earn growth energy → grow plants and unlock a richer garden**.

It is designed for students and professionals who want motivation without distraction.

## Key Features

- **Daily growth loop** tied to real Anki reviews.
- **Multi-slot garden** with unlocking slots over long-term milestones.
- **Plant species personalities** and stage progression:
  - seed
  - sprout
  - young plant
  - mature plant
  - flowering plant
  - rare variant
- **Gentle vitality decay** and recovery mode feel (missed days reduce vitality but do not wipe progress).
- **Daily quests** with growth/currency rewards.
- **Achievement system** (streak, volume, retention, due-clear, morning/night unlocks).
- **Currency and unlockables** (pots, weather, decorations).
- **Optional deck-specific growth mode**.
- **Seasonal background visuals**.
- **Optional reflection journal** stored locally.
- **Real image sourcing and caching** (no placeholder graphics):
  - Unsplash API
  - Pexels API
  - Pixabay API

## Real Image Sourcing (No Placeholders)

Anki Garden includes an **AssetManager** that:

1. Receives semantic queries (e.g. `young bonsai potted plant`).
2. Tries APIs in configured priority order.
3. Applies rate-limiting and retry logic.
4. Downloads real photos on first use.
5. Caches them in local `assets/` folders.
6. Saves attribution/source metadata in `assets/asset_metadata.json`.
7. Reuses cached files for fast/offline rendering.
8. Falls back gracefully to cache-only mode when APIs are unavailable.

### Asset Folder Structure

```text
ankigarden/assets/
  plants/
  backgrounds/
  decorations/
  weather/
  ui/
  asset_metadata.json   # created after first successful download
```

## Installation

1. Copy the `ankigarden/` folder into your Anki add-ons directory.
2. Restart Anki.
3. Open **Tools → Anki Garden**.
4. Add API keys in add-on config (recommended at least one provider).

## API Key Setup

Open Anki → **Tools → Add-ons → Anki Garden → Config** and set keys:

```json
"image_api": {
  "provider_priority": ["unsplash", "pexels", "pixabay"],
  "unsplash_access_key": "YOUR_UNSPLASH_KEY",
  "pexels_api_key": "YOUR_PEXELS_KEY",
  "pixabay_api_key": "YOUR_PIXABAY_KEY"
}
```

You can use one provider, or several with fallback priority.

## Config Options

`ankigarden/config.json` (and Anki add-on config) supports:

- `enable_sounds`
- `enable_animations`
- `daily_growth_cap`
- `daily_goal`
- `points_per_card.new|learning|review`
- `streak_grace_period_days`
- `quest_difficulty` (`easy|normal|hard`)
- `deck_specific_growth_mode`
- `show_reviewer_button`
- `vitality_decay_sensitivity`
- `seasonal_visuals`
- `image_api.*`
- `initial_slots`
- `max_slots`
- `currency_name`
- `focus_target_bonus`

## How Systems Work

### Review Event Integration

The add-on hooks into `reviewer_did_answer_card` and records:

- cards reviewed
- correctness
- queue type (new/learning/review)
- deck ID

These values feed growth points, quests, achievements, vitality, and streak updates.

### Progression & Balance

- Daily growth has a configurable **cap** to discourage unhealthy grinding.
- Correct answers give full growth; incorrect answers give reduced growth.
- Missed days reduce vitality/streak gently.
- Quest and achievement rewards provide extra growth and currency.
- Rare plant variants can appear during strong consistency periods.

### Persistence

All progress persists locally in `ankigarden/garden_state.json`, including:

- plants and slots
- growth and vitality
- streaks/history rollovers
- quests and achievements
- unlockables/currency
- journal entries
- totals and daily stats

### Error Handling

- Corrupt/missing state files auto-recover to defaults.
- API/image fetch failures fail gracefully and keep cached assets.
- UI remains usable even when offline.

## File Tree

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
    __init__.py
    reviewer.py
  models/
    __init__.py
    state.py
  ui/
    __init__.py
    dashboard.py
  assets/
    plants/
    backgrounds/
    decorations/
    weather/
    ui/
```

## Notes

- This add-on intentionally uses a calm, minimal UI and progression pacing.
- If no API key is configured and no cached image exists, the UI shows informative text and continues functioning.
- For distribution, zip the `ankigarden/` folder as your add-on package.
