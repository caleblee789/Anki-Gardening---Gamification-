# Anki Garden 🌿

Anki Garden is an Anki add-on that rewards consistent reviews with a calm, visual gardening loop.

Core loop:

> review cards → earn growth energy → advance plant stages → unlock more garden expression.

The add-on is fully local-first: state, assets, and metadata are all stored on disk in the add-on folder.

---

## What’s currently implemented

- **Core progression engine**
  - Daily growth economy with configurable caps, weights, and penalties.
  - Plant lifecycle stages: `seed`, `sprout`, `young`, `mature`, `flowering`, `rare`.
  - Multi-slot garden progression with unlockable slots.
- **Habit and motivation systems**
  - Daily quests and achievement tracking.
  - Streak/recovery-aware growth logic.
  - Burnout detection and adaptive feedback.
  - Focus mode and exam mode multipliers.
- **UI integrations**
  - Tools menu entry (**Tools → Anki Garden**).
  - Optional toolbar action and optional reviewer button.
  - Home-screen garden widget injection (Deck Browser / Overview webview contexts).
  - Dashboard and Garden Studio UI modules.
- **Asset pipeline (new local SVG workflow)**
  - Manifest-driven deterministic local asset selection.
  - Versioned SVG catalog under `assets/v2_cozy_handpainted/...`.
  - Seasonal backgrounds, weather variants, decorations, and per-stage plant SVGs.
  - Migration manifest and migration scripts for SVG/background variant expansion.
- **Persistence and reliability**
  - JSON-based local persistence with atomic writes.
  - Metadata cache for resolved visual assets.
  - Local snapshot files for future sync/export flows.

---

## Repository layout

```text
ankigarden/
  addon.py
  asset_manager.py
  config.py
  game.py
  storage.py
  hooks/
    reviewer.py
  models/
    state.py
  ui/
    dashboard.py
    garden_studio.py
    scene.py
  assets/
    manifest.json
    migration_manifest_v2.json
    v2_cozy_handpainted/

docs/
  README.md
  asset_migration_checklist.md
  svg_asset_migration.md
  asset_visual_diff_report.md
  background_adequacy_report.md
  ui/
    entrypoint_matrix.md
    state_scenarios.md

scripts/
  migrate_svg_assets.py
  enhance_background_variants.py

tests/
  test_engine.py
  test_addon_startup_and_home.py
  test_asset_selection.py
  test_svg_guardrails.py

anki_garden_cozy_handpainted_v2/
  starter_pack/

sample_config.json
README.md
```

---

## Configuration

Configuration is loaded through `ConfigManager` and merged with user config overrides at runtime.

High-impact keys:

- **Growth tuning**
  - `daily_growth_cap`
  - `points_per_card`
  - `correct_answer_bonus`
  - `incorrect_answer_penalty`
  - `difficulty_weight`
  - `recovery_weight`
  - `session_quality_weight`
- **Engagement systems**
  - `streak_grace_period_days`
  - `burnout_detection`
  - `burnout_volume_threshold`
  - `rare_event_frequency`
  - `focus_mode`
  - `exam_mode`
- **UI toggles**
  - `show_toolbar_button`
  - `show_reviewer_button`
  - `enable_animations`
  - `seasonal_visuals`
  - `time_of_day_bonus`
- **Assets**
  - `assets.mode` (`local_only`)
  - `assets.quality_preference` (`ultra` / `balanced` / `performance`)
  - `assets.allow_fallback_placeholder`

Use `sample_config.json` as a practical editing template.

---

## Local asset behavior

Asset rendering is deterministic and local-only:

1. A gameplay/UI slot is resolved (e.g., plant species+stage, weather, background theme).
2. Candidate files are looked up in `ankigarden/assets/manifest.json`.
3. A best-fit local candidate is selected using quality preference and slot matching.
4. Resolution metadata is persisted to `ankigarden/assets/metadata/asset_metadata.json`.

Guardrails in tests verify:

- all manifest SVG paths exist,
- manifest refs are versioned (`assets/v2_cozy_handpainted/...`),
- no duplicate file refs,
- SVGs retain required shape metadata (e.g., `viewBox`) and avoid unwanted comments.

---

## Development runtime pins

This repo includes version-pin files to keep local tooling aligned:

- `.nvmrc`
- `.node-version`
- `.swift-version`
- `.php-version`
- `.java-version`
- `.tool-versions`

---

## Installation (Anki)

1. Copy `ankigarden/` to your Anki add-ons directory.
2. Restart Anki.
3. Open **Tools → Anki Garden**.
4. Review cards to drive growth progression.

---

## Testing

From the repository root:

```bash
pytest -q
```

Targeted suites:

```bash
pytest -q tests/test_engine.py tests/test_asset_selection.py
pytest -q tests/test_addon_startup_and_home.py tests/test_svg_guardrails.py
```

---

## Known limitations

- Sync/export flows are still local-file oriented (no remote sync service).
- Home-screen widget injection depends on available Anki hook surfaces by version.
- Visual polish is intentionally performance-conscious over heavy animation.
