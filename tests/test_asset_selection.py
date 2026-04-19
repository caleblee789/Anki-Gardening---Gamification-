import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ankigarden.asset_manager import AssetManager
from ankigarden.config import DEFAULT_CONFIG, ConfigManager


class DummyConfig:
    def value(self, key, default=None):
        return DEFAULT_CONFIG.get(key, default)

    def nested(self, *keys, default=None):
        node = DEFAULT_CONFIG
        for key in keys:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                return default
        return node


class DummyStorage:
    def __init__(self, root: Path):
        self.addon_dir = root
        self.assets_root = root / "assets"
        self.cache_dir = self.assets_root / "cache"
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._meta = {}

    def load_asset_metadata(self):
        return self._meta

    def save_asset_metadata(self, data):
        self._meta = data


def test_rejects_too_small_candidate(tmp_path):
    manager = AssetManager(DummyConfig(), DummyStorage(tmp_path))
    scored = manager.score_asset_candidate({"url": "x", "width": 100, "height": 120}, "backgrounds", theme="verdant_dusk")
    assert scored["accepted"] is False


def test_prefers_high_resolution_and_aspect_fit(tmp_path):
    manager = AssetManager(DummyConfig(), DummyStorage(tmp_path))
    good = manager.score_asset_candidate({"url": "x", "width": 1920, "height": 1080, "style_tags": ["natural"]}, "backgrounds")
    meh = manager.score_asset_candidate({"url": "y", "width": 1280, "height": 1280, "style_tags": ["stock"]}, "backgrounds")
    assert good["accepted"]
    assert meh["accepted"]
    assert good["quality_score"] > meh["quality_score"]


def test_config_merge_keeps_new_visual_defaults():
    merged = ConfigManager._merge(DEFAULT_CONFIG.copy(), {"enable_sounds": True})
    assert merged["enable_sounds"] is True
    assert merged["visual_theme"] == "verdant_dusk"
    assert "weather_particle_density" in merged["theme_overrides"]
