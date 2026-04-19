from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .models.state import GardenState, Plant


class GardenStorage:
    def __init__(self, mw: Any, config: Any) -> None:
        self.mw = mw
        self.config = config
        self.addon_dir = Path(__file__).parent
        self.data_path = self.addon_dir / "garden_state.json"
        self.assets_root = self.addon_dir / "assets"
        self.asset_metadata = self.assets_root / "asset_metadata.json"
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

    def save(self) -> None:
        self.data_path.write_text(
            json.dumps(self.state.to_dict(), indent=2, ensure_ascii=False), "utf-8"
        )

    def _ensure_defaults(self) -> None:
        self.assets_root.mkdir(parents=True, exist_ok=True)
        for folder in ["plants", "backgrounds", "decorations", "weather", "ui"]:
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
        self.asset_metadata.write_text(json.dumps(data, indent=2), "utf-8")

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
        self.cloud_state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")

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
        self.social_hub_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
