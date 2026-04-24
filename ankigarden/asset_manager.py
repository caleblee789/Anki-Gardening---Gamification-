from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional


class AssetManager:
    MIN_DIMENSIONS = {
        "plants": (640, 640),
        "backgrounds": (1280, 720),
        "decorations": (512, 512),
        "weather": (512, 512),
        "ui": (256, 256),
    }

    QUALITY_ORDER = {"performance": 0, "balanced": 1, "ultra": 2}

    def __init__(self, config: Any, storage: Any) -> None:
        self.config = config
        self.storage = storage
        self.metadata = self.storage.load_asset_metadata()
        self._catalog = self._load_catalog()
        self._migrate_legacy_metadata()

    def get_or_fetch(
        self,
        category: str,
        key: str,
        query: str,
        provider_hint: Optional[str] = None,
        theme: Optional[str] = None,
        reroll: bool = False,
    ) -> Optional[Path]:
        del query, provider_hint
        cache_key = f"{category}:{key}"
        slot = self._slot_for(category, key, theme)
        quality_pref = str(self.config.nested("assets", "quality_preference", default="balanced") or "balanced")

        candidates = self._select_candidates(category, slot, quality_pref)
        if not candidates:
            if self.config.nested("assets", "allow_fallback_placeholder", default=True):
                candidates = self._placeholder_candidates()
            else:
                return None

        candidate_paths = [self.storage.addon_dir / entry["file"] for entry in candidates]
        candidate_paths = [p for p in candidate_paths if self._valid_local_asset(p, category)]
        if not candidate_paths:
            if not self.config.nested("assets", "allow_fallback_placeholder", default=True):
                return None
            candidate_paths = [self._ensure_placeholder_asset()]

        idx = self._pick_index(cache_key, key, candidate_paths, reroll)
        picked = candidate_paths[idx]
        rel = str(picked.relative_to(self.storage.addon_dir))
        self.metadata[cache_key] = {
            "provider": "local_catalog",
            "source_kind": "local_catalog",
            "source_url": "local://manifest",
            "query": "",
            "downloaded_at": int(time.time()),
            "local_path": rel,
            "quality_score": self._quality_score_for(rel),
            "dimensions": self._manifest_dimensions_for(rel),
            "derivatives": {"thumbnail": rel, "preview": rel, "full": rel},
            "catalog_slot": slot,
            "catalog_cycle_index": idx,
            "legacy_remote_preserved": bool(self.metadata.get(cache_key, {}).get("legacy_remote_preserved", False)),
        }
        self.storage.save_asset_metadata(self.metadata)
        return picked

    def _load_catalog(self) -> dict[str, list[dict[str, Any]]]:
        manifest = self.storage.assets_root / "manifest.json"
        if not manifest.exists():
            return {}
        try:
            payload = json.loads(manifest.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        entries = payload.get("assets", [])
        by_category: dict[str, list[dict[str, Any]]] = {}
        for row in entries:
            if not isinstance(row, dict):
                continue
            category = str(row.get("category", ""))
            if not category:
                continue
            by_category.setdefault(category, []).append(row)
        return by_category

    def _migrate_legacy_metadata(self) -> None:
        changed = False
        for _, row in list(self.metadata.items()):
            if not isinstance(row, dict):
                continue
            if row.get("source_kind") in {"remote", "starter_pack"}:
                row["legacy_remote_preserved"] = True
                changed = True
        if changed:
            self.storage.save_asset_metadata(self.metadata)

    def _slot_for(self, category: str, key: str, theme: Optional[str]) -> dict[str, str]:
        if category == "plants":
            species, stage = (key.split("_", 1) + ["mature"])[:2]
            return {"species": species, "stage": stage}
        if category == "backgrounds":
            _, season, weather = (key.split("_", 2) + ["default", "breeze"])[0:3]
            return {"season": season, "weather": weather, "theme": theme or str(self.config.value("visual_theme", "verdant_dusk"))}
        if category == "weather":
            weather = key.replace("weather_", "", 1)
            return {"weather": weather}
        if category == "decorations":
            return {"decoration_id": key.replace("decor_", "", 1)}
        if category == "ui":
            return {"ui_id": key.replace("ui_", "", 1)}
        return {"key": key}

    def _select_candidates(self, category: str, slot: dict[str, str], quality_pref: str) -> list[dict[str, Any]]:
        entries = self._catalog.get(category, [])
        preferred: list[dict[str, Any]] = []
        for entry in entries:
            entry_slot = entry.get("slot", {})
            if all(str(entry_slot.get(k)) == str(v) for k, v in slot.items() if v):
                preferred.append(entry)

        if not preferred and category == "backgrounds":
            preferred = [e for e in entries if (e.get("slot", {}) or {}).get("season") == slot.get("season") and (e.get("slot", {}) or {}).get("weather") == slot.get("weather")]
        if not preferred and category in {"plants", "weather", "decorations", "ui"}:
            k = next(iter(slot.keys()))
            preferred = [e for e in entries if (e.get("slot", {}) or {}).get(k) == slot.get(k)]

        target_rank = self.QUALITY_ORDER.get(quality_pref, self.QUALITY_ORDER["balanced"])
        preferred.sort(
            key=lambda e: (
                -min(self.QUALITY_ORDER.get(str(e.get("quality_tier", "balanced")), 1), target_rank),
                -float(e.get("quality_score", 0.0)),
                str(e.get("file", "")),
            )
        )
        return preferred

    def _pick_index(self, cache_key: str, key: str, candidates: list[Path], reroll: bool) -> int:
        if len(candidates) == 1:
            return 0
        existing = self.metadata.get(cache_key, {})
        if reroll:
            previous = int(existing.get("catalog_cycle_index", -1))
            return (previous + 1) % len(candidates)
        del key
        return 0

    def _manifest_dimensions_for(self, rel_path: str) -> dict[str, int]:
        for rows in self._catalog.values():
            for row in rows:
                if row.get("file") == rel_path:
                    return {"width": int(row.get("width", 0)), "height": int(row.get("height", 0))}
        return {"width": 0, "height": 0}

    def _quality_score_for(self, rel_path: str) -> float:
        for rows in self._catalog.values():
            for row in rows:
                if row.get("file") == rel_path:
                    return round(float(row.get("quality_score", 0.75)), 4)
        return 0.75

    def _valid_local_asset(self, path: Path, category: str) -> bool:
        try:
            resolved = path.resolve()
            addon_root = self.storage.addon_dir.resolve()
            resolved.relative_to(addon_root)
        except (OSError, ValueError):
            return False
        if not resolved.exists() or not resolved.is_file():
            return False
        if resolved.suffix.lower() != ".svg":
            return False
        try:
            rel_path = str(resolved.relative_to(self.storage.addon_dir.resolve()))
        except ValueError:
            return False
        dims = self._manifest_dimensions_for(rel_path)
        min_w, min_h = self.MIN_DIMENSIONS.get(category, (1, 1))
        return int(dims.get("width", 0)) >= min_w and int(dims.get("height", 0)) >= min_h

    def _placeholder_candidates(self) -> list[dict[str, Any]]:
        rel = str(self._ensure_placeholder_asset().relative_to(self.storage.addon_dir))
        return [{"file": rel, "width": 1200, "height": 675, "quality_tier": "performance", "quality_score": 0.5, "slot": {"fallback": "placeholder"}}]

    def _ensure_placeholder_asset(self) -> Path:
        placeholder = self.storage.assets_root / "ui" / "fallback_placeholder.svg"
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        if not placeholder.exists():
            placeholder.write_text(
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 675'><rect width='1200' height='675' fill='#1a2733'/><text x='50%' y='50%' text-anchor='middle' fill='#e6f0ea' font-size='46'>Anki Garden</text></svg>",
                encoding="utf-8",
            )
        return placeholder

    def export_metadata_json(self) -> str:
        return json.dumps(self.metadata, indent=2)
