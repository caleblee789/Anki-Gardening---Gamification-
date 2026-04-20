# Anki Garden Starter Pack

This pack contains source SVGs used to build the local catalog in `ankigarden/assets/manifest.json`.

## Local-only pipeline

- Runtime selection is manifest-driven (no remote fetching).
- Catalog entries map deterministic slots (plant/background/weather/decoration/ui) to local files.
- Metadata records `source_kind: "local_catalog"`.

## Adding/replacing art

1. Add the file under a deterministic taxonomy folder (for example `assets/plants/<species>/<stage>/...`).
2. Add/update a row in `assets/manifest.json` with:
   - slot selectors
   - dimensions, format
   - source/attribution
   - quality tier/score
3. Ensure each active gameplay slot has at least one local candidate.

## Minimum specs

- Plants/decorations/weather/ui: at least 512px effective size (plants target 640+).
- Backgrounds: at least 1280×720.
- Preferred formats: SVG/WebP where supported, then high-quality PNG/JPEG.

License: CC0 for bundled generated vectors.
