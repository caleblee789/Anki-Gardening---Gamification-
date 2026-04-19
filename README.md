# Anki Garden 🌿

Anki Garden is a production-oriented Anki add-on that turns review consistency into long-term visual progress.

Core loop:

> study cards consistently → earn growth energy → grow plants and garden layers → unlock new cosmetics/species.

The system is designed to support serious learners with calm reinforcement, recovery-friendly streak handling, and quality-aware growth (not raw grinding).

---

## Features

- Multi-slot garden with unlockable plant slots.
- Growth stages per plant: seed, sprout, young, mature, flowering, rare.
- Adaptive species personalities (bonsai, rose, cactus, orchid, moonflower, sunbloom, ivy, fern).
- Deck-to-plant mapping (optional) and deck difficulty weighting hooks.
- Daily quests with adaptive generation.
- Achievement system (streak, volume, accuracy, recovery, deep-work, exam mode).
- Focus/deep work sessions (25/45/60 min).
- Recovery momentum logic after missed days.
- Burnout detection and lightweight guidance.
- Garden health index.
- Seasonal visuals and time-of-day bonuses.
- Rare event system (golden bloom, meteor shower, rainfall blessing, etc.).
- Journal notes and timeline snapshots.
- Local cloud snapshot readiness + share/export summary.
- Real online image sourcing + deterministic starter-pack fallback + persistent local caching.

---

## Installation

1. Copy `ankigarden/` into your Anki add-ons directory.
2. Restart Anki.
3. Open **Tools → Anki Garden**.
4. Start reviewing cards; garden progress updates automatically.

Optional entries:
- Toolbar button (`show_toolbar_button`)
- Reviewer button (`show_reviewer_button`)

---

## Folder tree

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
    cache/
    metadata/
sample_config.json
README.md
```

---

## Configuration

Primary config keys include:

- Gameplay balance:
  - `daily_growth_cap`
  - `points_per_card`
  - `correct_answer_bonus`
  - `incorrect_answer_penalty`
  - `difficulty_weight`
  - `recovery_weight`
  - `session_quality_weight`
- Habit tuning:
  - `streak_grace_period_days`
  - `vitality_decay_sensitivity`
  - `burnout_detection`
  - `burnout_volume_threshold`
- Visual systems:
  - `seasonal_visuals`
  - `time_of_day_bonus`
  - `enable_animations`
- Advanced systems:
  - `focus_mode`
  - `exam_mode`
  - `rare_event_frequency`
  - `daily_snapshot`
  - `snapshot_frequency_days`
- Default no-setup images:
  - `image_api.provider_priority` (defaults to Wikimedia only)
  - `image_api.enable_builtin_no_key_sources`

Use `sample_config.json` as a full reference.

---

## Image behavior (no setup required)

By default, image rendering works out of the box with **zero API keys**:

1. Cache-first reuse of existing image assets.
2. No-key remote fetch via Wikimedia Commons.
3. Deterministic fallback to curated local `assets/starter_pack/*` art if network fetch fails.

This default path is deterministic and offline-resilient. Metadata records whether an image came from a remote source or the starter pack for future upgrade/refresh logic.

### Optional advanced providers (opt-in)

Unsplash, Pexels, and Pixabay are available but disabled in default first-run behavior unless you explicitly add them to `image_api.provider_priority` and provide keys.

```json
"image_api": {
  "provider_priority": ["wikimedia", "unsplash"],
  "unsplash_access_key": "YOUR_KEY",
  "pexels_api_key": "",
  "pixabay_api_key": ""
}
```

### Caching behavior

- First request attempts remote no-key fetch and then stores local copies.
- File is cached under `assets/<category>/`.
- Metadata is written to `assets/metadata/asset_metadata.json`.
- Future requests reuse cached files.
- If remote fetch is unavailable, curated starter-pack assets are used automatically.

---

## Deck mapping

When `deck_specific_growth_mode` is enabled:
- Each review contributes only to mapped plant(s).
- Configure mapping from dashboard (`Map Deck → Plant`).

If disabled, growth is shared across all active plants.

---

## Exam mode

Dashboard exam panel supports setting/clearing exam date.

Exam mode:
- Tracks countdown.
- Optionally emphasizes target decks.
- Applies configurable deck weight boost during growth calculation.

---

## Persistence and safety

Local files:
- `garden_state.json` (primary state)
- `cloud_state.json` (optional snapshot sync simulation)
- `social_hub.json` (local social/share hub)
- `assets/metadata/asset_metadata.json` (asset attribution/cache metadata)

Writes are atomic (`NamedTemporaryFile` + replace) for resilience.

---

## Troubleshooting

- **No images showing**: starter-pack fallback should always display something even offline; if not, check add-on asset paths and `assets/starter_pack/` contents.
- **Config ignored**: reload Anki after editing add-on config.
- **Slow downloads**: defaults already use bounded retries/timeouts; keep provider list short (Wikimedia-only is recommended for no-key mode).
- **Import/share unavailable**: ensure `future_features.enable_social_gardens` is true.

---

## Known limitations

- Cloud sync is local snapshot architecture (not remote SaaS sync).
- Export is JSON summary (not a rendered garden screenshot image yet).
- Micro-animations are intentionally minimal for review performance.

---

## Packaging

To package as `.ankiaddon`:

1. Zip the `ankigarden/` folder contents.
2. Rename resulting zip to `ankigarden.ankiaddon`.
3. Install via Anki add-on installer or copy into add-ons directory.

