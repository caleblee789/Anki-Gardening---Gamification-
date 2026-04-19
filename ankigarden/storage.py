from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

from .models.state import GardenState, Plant


class GardenStorage:
    def __init__(self, mw: Any, config: Any) -> None:
        self.mw = mw
        self.config = config
        self.addon_dir = Path(__file__).parent
        self.data_path = self.addon_dir / "garden_state.json"
        self.assets_root = self.addon_dir / "assets"
        self.metadata_dir = self.assets_root / "metadata"
        self.cache_dir = self.assets_root / "cache"
        self.asset_metadata = self.metadata_dir / "asset_metadata.json"
        self.cloud_state_path = self.addon_dir / "cloud_state.json"
        self.social_hub_path = self.addon_dir / "social_hub.json"
        self.state = self._load()
        self._ensure_defaults()

    def _load(self) -> GardenState:
        try:
            if self.data_path.exists():
                return GardenState.from_dict(json.loads(self.data_path.read_text("utf-8")))
        except Exception:
            pass
        return GardenState()

    def _atomic_write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tf:
            json.dump(payload, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name
        Path(temp_name).replace(path)

    def save(self) -> None:
        self._atomic_write_json(self.data_path, self.state.to_dict())

    def _ensure_defaults(self) -> None:
        self.assets_root.mkdir(parents=True, exist_ok=True)
        for folder in ["plants", "backgrounds", "decorations", "weather", "ui", "cache", "metadata"]:
            (self.assets_root / folder).mkdir(exist_ok=True)
        if not self.state.plants:
            starters = [("bonsai", "streak"), ("rose", "accuracy")]
            for idx, species in enumerate(starters[: self.config.value("initial_slots", 2)]):
                name, personality = species
                self.state.plants.append(
                    Plant(
                        plant_id=f"plant_{idx+1}",
                        species=name,
                        name=name.capitalize(),
                        slot_index=idx,
                        personality=personality,
                    )
                )
        self.save()

    def load_asset_metadata(self) -> dict:
        if not self.asset_metadata.exists():
            return {}
        try:
            return json.loads(self.asset_metadata.read_text("utf-8"))
        except Exception:
            return {}

    def save_asset_metadata(self, data: dict) -> None:
        self._atomic_write_json(self.asset_metadata, data)

    def load_cloud_snapshot(self) -> Optional[Dict[str, Any]]:
        if not self.cloud_state_path.exists():
            return None
        try:
            return json.loads(self.cloud_state_path.read_text("utf-8"))
        except Exception:
            return None

    def save_cloud_snapshot(self, state_dict: Dict[str, Any], reason: str = "manual") -> None:
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "state": state_dict,
        }
        self._atomic_write_json(self.cloud_state_path, payload)

    def load_social_hub(self) -> Dict[str, Any]:
        if not self.social_hub_path.exists():
            return {"gardens": {}}
        try:
            data = json.loads(self.social_hub_path.read_text("utf-8"))
            if isinstance(data, dict) and isinstance(data.get("gardens"), dict):
                return data
        except Exception:
            pass
        return {"gardens": {}}

    def save_social_hub(self, data: Dict[str, Any]) -> None:
        self._atomic_write_json(self.social_hub_path, data)
