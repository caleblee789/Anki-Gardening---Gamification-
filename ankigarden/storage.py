from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models.state import GardenState, Plant


class GardenStorage:
    def __init__(self, mw: Any, config: Any) -> None:
        self.mw = mw
        self.config = config
        self.addon_dir = Path(__file__).parent
        self.data_path = self.addon_dir / "garden_state.json"
        self.assets_root = self.addon_dir / "assets"
        self.asset_metadata = self.assets_root / "asset_metadata.json"
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
            starters = ["bonsai", "rose"]
            for idx, species in enumerate(starters[: self.config.value("initial_slots", 2)]):
                self.state.plants.append(
                    Plant(
                        plant_id=f"plant_{idx+1}",
                        species=species,
                        name=species.capitalize(),
                        slot_index=idx,
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
