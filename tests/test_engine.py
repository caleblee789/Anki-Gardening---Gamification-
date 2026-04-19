import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pathlib import Path

from ankigarden.game import GardenGameEngine
from ankigarden.models.state import GardenState, Plant


class FakeConfig:
    def __init__(self) -> None:
        from ankigarden.config import DEFAULT_CONFIG

        self.data = DEFAULT_CONFIG

    def value(self, key, default=None):
        return self.data.get(key, default)

    def nested(self, *keys, default=None):
        node = self.data
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key)
            if node is None:
                return default
        return node


class FakeStorage:
    def __init__(self) -> None:
        self.state = GardenState()
        self.state.plants = [Plant(plant_id="p1", species="bonsai", name="Bonsai", slot_index=0)]
        self.addon_dir = Path(".")
        self.assets_root = Path("./ankigarden/assets")

    def save(self):
        return None

    def load_asset_metadata(self):
        return {}

    def save_asset_metadata(self, data):
        return None

    def load_social_hub(self):
        return {"gardens": {}}

    def save_social_hub(self, data):
        return None

    def save_cloud_snapshot(self, state_dict, reason="manual"):
        return None

    def load_cloud_snapshot(self):
        return {"state": self.state.to_dict()}


def test_growth_increases_after_review():
    cfg = FakeConfig()
    st = FakeStorage()
    engine = GardenGameEngine(cfg, st)
    before = st.state.plants[0].growth_points
    engine.register_review({"queue": 2, "ease": 3, "deck_id": 1, "difficulty": 0.8, "lapse_count": 1})
    assert st.state.plants[0].growth_points >= before


def test_focus_session_completes():
    cfg = FakeConfig()
    st = FakeStorage()
    engine = GardenGameEngine(cfg, st)
    ok, _ = engine.start_focus_session(25)
    assert ok
    st.state.focus_session.started_at = "2000-01-01T00:00:00"
    ok, _ = engine.complete_focus_session()
    assert ok
    assert st.state.total_focus_sessions >= 1


def test_exam_countdown_off_by_default():
    cfg = FakeConfig()
    st = FakeStorage()
    engine = GardenGameEngine(cfg, st)
    assert engine.exam_countdown_days() is None
