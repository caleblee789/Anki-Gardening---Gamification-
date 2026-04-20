# SVG Asset Migration Checklist

- [x] Source staged locally from `anki_garden_cozy_handpainted_v2`.
- [x] SVG intake assembled in `.tmp_asset_migration/intake`.
- [x] Migration manifest generated: `ankigarden/assets/migration_manifest_v2.json`.
- [x] References remapped in `ankigarden/assets/manifest.json`.
- [x] All mapped SVGs normalized (viewBox, width/height, id prefixing).
- [x] Accessibility defaults applied (`title`, `aria-hidden`, `focusable`).
- [x] Deprecated directories removed after remap (plants/backgrounds/decorations/weather/ui except fallback).
- [x] Redundant legacy source bundle removed (`anki_garden_cozy_handpainted_v2/assets`) to avoid duplicated assets.
- [x] Guardrail tests added for broken refs, duplicate names, and optimization.

## Visual verification

- Automated repository-only run; no browser-based screenshot tooling is configured in this environment.
- Before/after evidence recorded as checksum diff summary in `docs/asset_visual_diff_report.md`.
