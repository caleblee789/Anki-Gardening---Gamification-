# SVG Asset Migration (Cozy Handpainted v2)

## What changed
- Canonical asset references now point to `assets/v2_cozy_handpainted/...` in `ankigarden/assets/manifest.json`.
- Legacy generated asset trees (`assets/plants`, `assets/backgrounds`, `assets/decorations`, `assets/weather`, and deprecated UI SVG folders) were removed after the manifest remap.
- The migration mapping source of truth is `ankigarden/assets/migration_manifest_v2.json`.

## Naming and placement guardrails
- Keep production SVGs under `ankigarden/assets/v2_cozy_handpainted/<category>/...`.
- Use lowercase snake_case filenames.
- Ensure every new asset is referenced by `ankigarden/assets/manifest.json`.
- Avoid duplicate SVG basenames across the versioned tree.
- SVGs must include `viewBox` and be stripped of XML comments.

## Rollback instructions
1. Revert manifest and asset tree:
   - `git checkout -- ankigarden/assets/manifest.json ankigarden/assets`
2. Restore pre-migration files from Git history if partial cleanup occurred:
   - `git restore --source=HEAD~1 ankigarden/assets/plants ankigarden/assets/backgrounds ankigarden/assets/decorations ankigarden/assets/weather ankigarden/assets/ui`
3. Re-run tests:
   - `pytest tests/test_svg_guardrails.py tests/test_asset_selection.py`

## CI checks
Use `tests/test_svg_guardrails.py` to enforce:
- no broken manifest references
- no duplicate SVG basenames
- no unoptimized/commented SVG files and missing `viewBox`
