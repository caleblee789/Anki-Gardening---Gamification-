import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ankigarden.asset_manager import AssetManager
from ankigarden.config import DEFAULT_CONFIG, ConfigManager


class DummyConfig:
    def __init__(self, overrides=None):
        self.cfg = DEFAULT_CONFIG.copy()
        if overrides:
            for k, v in overrides.items():
                if isinstance(v, dict) and isinstance(self.cfg.get(k), dict):
                    self.cfg[k] = {**self.cfg[k], **v}
                else:
                    self.cfg[k] = v

    def value(self, key, default=None):
        return self.cfg.get(key, default)

    def nested(self, *keys, default=None):
        node = self.cfg
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
    assert scored["reason"] == "dimensions"


def test_background_quality_thresholds_are_stricter(tmp_path):
    manager = AssetManager(DummyConfig(), DummyStorage(tmp_path))
    weak_detail = manager.score_asset_candidate(
        {"url": "x", "width": 1920, "height": 1080, "detail_score": 0.34, "compression_penalty": 0.2},
        "backgrounds",
    )
    acceptable_plant = manager.score_asset_candidate(
        {"url": "x", "width": 1024, "height": 1024, "detail_score": 0.34, "compression_penalty": 0.2},
        "plants",
    )
    assert weak_detail["accepted"] is False
    assert weak_detail["reason"] == "detail"
    assert acceptable_plant["accepted"] is True


def test_prefers_high_resolution_and_aspect_fit(tmp_path):
    manager = AssetManager(DummyConfig(), DummyStorage(tmp_path))
    good = manager.score_asset_candidate(
        {"url": "x", "width": 1920, "height": 1080, "style_tags": ["natural"], "detail_score": 0.8, "compression_penalty": 0.2},
        "backgrounds",
    )
    meh = manager.score_asset_candidate(
        {"url": "y", "width": 1800, "height": 1000, "style_tags": ["stock"], "detail_score": 0.65, "compression_penalty": 0.25},
        "backgrounds",
    )
    assert good["accepted"]
    assert meh["accepted"]
    assert good["quality_score"] > meh["quality_score"]


def test_empty_keys_no_key_provider_still_succeeds(tmp_path, monkeypatch):
    storage = DummyStorage(tmp_path)
    starter = storage.assets_root / "starter_pack" / "backgrounds"
    starter.mkdir(parents=True, exist_ok=True)
    (starter / "verdant_dusk_hill.svg").write_text("<svg></svg>", encoding="utf-8")

    manager = AssetManager(DummyConfig(), storage)

    monkeypatch.setattr(manager, "_from_wikimedia", lambda query: [])
    path = manager.get_or_fetch("backgrounds", "bg_main", "forest trail")

    assert path is not None
    assert path.exists()
    meta = storage._meta["backgrounds:bg_main"]
    assert meta["source_kind"] == "starter_pack"


def test_no_key_provider_fetches_remote_end_to_end(tmp_path, monkeypatch):
    storage = DummyStorage(tmp_path)
    manager = AssetManager(DummyConfig(), storage)

    monkeypatch.setattr(
        manager,
        "_from_wikimedia",
        lambda query: [
            {
                "url": "https://example.com/image.jpg",
                "provider": "wikimedia",
                "width": 1920,
                "height": 1080,
                "style_tags": ["natural"],
                "detail_score": 0.9,
                "compression_penalty": 0.1,
            }
        ],
    )

    def fake_download(category, key, url):
        target = storage.assets_root / category / f"{key}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fake")
        return target

    monkeypatch.setattr(manager, "_download", fake_download)
    monkeypatch.setattr(manager, "_generate_derivatives", lambda original, category, key: {"preview": original, "thumbnail": original, "full": original})

    path = manager.get_or_fetch("backgrounds", "bg_remote", "forest trail")

    assert path is not None
    assert path.exists()
    meta = storage._meta["backgrounds:bg_remote"]
    assert meta["source_kind"] == "remote"
    assert meta["provider"] == "wikimedia"


def test_remote_failure_falls_back_deterministically(tmp_path, monkeypatch):
    storage = DummyStorage(tmp_path)
    curated = storage.assets_root / "starter_pack" / "decorations"
    curated.mkdir(parents=True, exist_ok=True)
    (curated / "stone_path.svg").write_text("<svg id='stone'></svg>", encoding="utf-8")
    (curated / "bench_corner.svg").write_text("<svg id='bench'></svg>", encoding="utf-8")

    manager = AssetManager(DummyConfig(), storage)
    monkeypatch.setattr(manager, "_from_wikimedia", lambda query: [])

    first = manager.get_or_fetch("decorations", "d1", "cozy bench", reroll=True)
    second = manager.get_or_fetch("decorations", "d1", "cozy bench", reroll=True)

    assert first is not None and second is not None
    assert first == second
    assert storage._meta["decorations:d1"]["source_kind"] == "starter_pack"


def test_config_merge_keeps_new_visual_defaults():
    merged = ConfigManager._merge(DEFAULT_CONFIG.copy(), {"enable_sounds": True})
    assert merged["enable_sounds"] is True
    assert merged["visual_theme"] == "verdant_dusk"
    assert "weather_particle_density" in merged["theme_overrides"]
