from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

GROWTH_STAGES = ["seed", "sprout", "young", "mature", "flowering", "rare"]


@dataclass
class Plant:
    plant_id: str
    species: str
    name: str
    slot_index: int
    growth_points: int = 0
    vitality: float = 1.0
    rare_variant: bool = False
    assigned_deck_id: Optional[int] = None
    personality: str = "balanced"

    @property
    def growth_stage(self) -> str:
        thresholds = [0, 80, 220, 480, 900, 1400]
        for idx, threshold in enumerate(reversed(thresholds)):
            if self.growth_points >= threshold:
                return GROWTH_STAGES[len(thresholds) - 1 - idx]
        return "seed"


@dataclass
class DailyStats:
    day: str = field(default_factory=lambda: date.today().isoformat())
    reviewed: int = 0
    correct: int = 0
    wrong: int = 0
    new_count: int = 0
    learning_count: int = 0
    review_count: int = 0
    difficult_count: int = 0
    recovered_lapses: int = 0
    growth_earned: int = 0
    completed_due_cards: bool = False
    focus_sessions_completed: int = 0

    @property
    def accuracy(self) -> float:
        total = self.correct + self.wrong
        return 0 if total == 0 else self.correct / total


@dataclass
class Quest:
    quest_id: str
    description: str
    target: int
    metric: str
    progress: int = 0
    reward_growth: int = 0
    reward_currency: int = 0
    completed: bool = False


@dataclass
class Achievement:
    achievement_id: str
    name: str
    description: str
    unlocked: bool = False
    progress: float = 0.0
    unlocked_at: Optional[str] = None


@dataclass
class FocusSession:
    active: bool = False
    started_at: Optional[str] = None
    duration_minutes: int = 25
    deep_work_streak: int = 0


@dataclass
class ExamMode:
    enabled: bool = False
    exam_date: Optional[str] = None
    target_deck_ids: List[int] = field(default_factory=list)
    focus_species: str = "bonsai"


@dataclass
class SessionSummary:
    day: str
    summary: str
    quality_score: float
    growth: int


@dataclass
class Snapshot:
    day: str
    streak_days: int
    health_index: float
    total_reviews: int
    plant_stages: Dict[str, str]


@dataclass
class GardenState:
    version: int = 3
    streak_days: int = 0
    total_reviews: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    total_focus_sessions: int = 0
    currency: int = 0
    unlocked_slots: int = 2
    selected_background: str = "default"
    selected_weather: str = "sunny"
    plants: List[Plant] = field(default_factory=list)
    achievements: Dict[str, Achievement] = field(default_factory=dict)
    daily_quests: List[Quest] = field(default_factory=list)
    quest_history: List[str] = field(default_factory=list)
    daily_stats: DailyStats = field(default_factory=DailyStats)
    journal: Dict[str, str] = field(default_factory=dict)
    inventory: Dict[str, List[str]] = field(default_factory=lambda: {
        "plants": ["bonsai", "rose", "ivy", "fern"],
        "pots": ["ceramic_minimal"],
        "backgrounds": ["default"],
        "decorations": ["stone_lantern"],
        "weather": ["sunny"],
        "sounds": [],
        "skins": [],
    })
    equipped: Dict[str, str] = field(default_factory=lambda: {
        "pot": "ceramic_minimal",
        "background": "default",
        "decoration": "stone_lantern",
        "weather": "sunny",
    })
    purchased_items: List[str] = field(default_factory=list)
    streak_freeze_tokens: int = 1
    recovery_mode: bool = False
    last_active_day: str = field(default_factory=lambda: date.today().isoformat())
    focus_plant_id: Optional[str] = None
    deck_plant_map: Dict[str, str] = field(default_factory=dict)
    deck_difficulty_map: Dict[str, float] = field(default_factory=dict)
    cloud_enabled: bool = False
    cloud_last_sync: Optional[str] = None
    cloud_device_id: str = "local-device"
    gardener_name: str = "Gardener"
    share_code: str = ""
    shared_gardens: Dict[str, Dict[str, object]] = field(default_factory=dict)
    weekly_event_id: str = ""
    weekly_event_applied_for_day: str = ""
    mastery_tree: Dict[str, int] = field(default_factory=lambda: {
        "consistency": 0,
        "accuracy": 0,
        "volume": 0,
        "recovery": 0,
    })
    rare_event_log: List[str] = field(default_factory=list)
    focus_session: FocusSession = field(default_factory=FocusSession)
    exam_mode: ExamMode = field(default_factory=ExamMode)
    snapshots: List[Snapshot] = field(default_factory=list)
    recent_summaries: List[SessionSummary] = field(default_factory=list)
    passive_reward_days: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "streak_days": self.streak_days,
            "total_reviews": self.total_reviews,
            "total_correct": self.total_correct,
            "total_wrong": self.total_wrong,
            "total_focus_sessions": self.total_focus_sessions,
            "currency": self.currency,
            "unlocked_slots": self.unlocked_slots,
            "selected_background": self.selected_background,
            "selected_weather": self.selected_weather,
            "plants": [p.__dict__ for p in self.plants],
            "achievements": {k: v.__dict__ for k, v in self.achievements.items()},
            "daily_quests": [q.__dict__ for q in self.daily_quests],
            "quest_history": self.quest_history,
            "daily_stats": self.daily_stats.__dict__,
            "journal": self.journal,
            "inventory": self.inventory,
            "equipped": self.equipped,
            "purchased_items": self.purchased_items,
            "streak_freeze_tokens": self.streak_freeze_tokens,
            "recovery_mode": self.recovery_mode,
            "last_active_day": self.last_active_day,
            "focus_plant_id": self.focus_plant_id,
            "deck_plant_map": self.deck_plant_map,
            "deck_difficulty_map": self.deck_difficulty_map,
            "cloud_enabled": self.cloud_enabled,
            "cloud_last_sync": self.cloud_last_sync,
            "cloud_device_id": self.cloud_device_id,
            "gardener_name": self.gardener_name,
            "share_code": self.share_code,
            "shared_gardens": self.shared_gardens,
            "weekly_event_id": self.weekly_event_id,
            "weekly_event_applied_for_day": self.weekly_event_applied_for_day,
            "mastery_tree": self.mastery_tree,
            "rare_event_log": self.rare_event_log,
            "focus_session": self.focus_session.__dict__,
            "exam_mode": {
                "enabled": self.exam_mode.enabled,
                "exam_date": self.exam_mode.exam_date,
                "target_deck_ids": self.exam_mode.target_deck_ids,
                "focus_species": self.exam_mode.focus_species,
            },
            "snapshots": [s.__dict__ for s in self.snapshots],
            "recent_summaries": [s.__dict__ for s in self.recent_summaries],
            "passive_reward_days": self.passive_reward_days,
        }

    @staticmethod
    def from_dict(data: dict) -> "GardenState":
        state = GardenState()
        for key in [
            "version", "streak_days", "total_reviews", "total_correct", "total_wrong", "total_focus_sessions",
            "currency", "unlocked_slots", "selected_background", "selected_weather", "journal", "inventory",
            "equipped", "purchased_items", "streak_freeze_tokens", "recovery_mode", "last_active_day",
            "focus_plant_id", "deck_plant_map", "deck_difficulty_map", "cloud_enabled", "cloud_last_sync",
            "cloud_device_id", "gardener_name", "share_code", "shared_gardens", "weekly_event_id",
            "weekly_event_applied_for_day", "mastery_tree", "rare_event_log", "quest_history", "passive_reward_days",
        ]:
            if key in data:
                setattr(state, key, data[key])
        state.plants = [Plant(**p) for p in data.get("plants", [])]
        state.achievements = {k: Achievement(**v) for k, v in data.get("achievements", {}).items()}
        state.daily_quests = [Quest(**q) for q in data.get("daily_quests", []) if isinstance(q, dict)]
        if "daily_stats" in data and isinstance(data["daily_stats"], dict):
            state.daily_stats = DailyStats(**data["daily_stats"])
        if isinstance(data.get("focus_session"), dict):
            state.focus_session = FocusSession(**data["focus_session"])
        if isinstance(data.get("exam_mode"), dict):
            state.exam_mode = ExamMode(**data["exam_mode"])
        state.snapshots = [Snapshot(**s) for s in data.get("snapshots", []) if isinstance(s, dict)]
        state.recent_summaries = [SessionSummary(**s) for s in data.get("recent_summaries", []) if isinstance(s, dict)]
        return state


def iso_now() -> str:
    return datetime.now().isoformat()
