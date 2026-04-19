from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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
    growth_earned: int = 0
    completed_due_cards: bool = False

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


@dataclass
class GardenState:
    version: int = 2
    streak_days: int = 0
    total_reviews: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    currency: int = 0
    unlocked_slots: int = 2
    selected_background: str = "default"
    selected_weather: str = "sunny"
    plants: List[Plant] = field(default_factory=list)
    achievements: Dict[str, Achievement] = field(default_factory=dict)
    daily_quests: List[Quest] = field(default_factory=list)
    daily_stats: DailyStats = field(default_factory=DailyStats)
    journal: Dict[str, str] = field(default_factory=dict)
    inventory: Dict[str, List[str]] = field(default_factory=lambda: {
        "plants": ["bonsai", "rose"],
        "pots": ["ceramic_minimal"],
        "backgrounds": ["default"],
        "decorations": ["stone_lantern"],
        "weather": ["sunny"],
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

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "streak_days": self.streak_days,
            "total_reviews": self.total_reviews,
            "total_correct": self.total_correct,
            "total_wrong": self.total_wrong,
            "currency": self.currency,
            "unlocked_slots": self.unlocked_slots,
            "selected_background": self.selected_background,
            "selected_weather": self.selected_weather,
            "plants": [p.__dict__ for p in self.plants],
            "achievements": {k: v.__dict__ for k, v in self.achievements.items()},
            "daily_quests": [q.__dict__ for q in self.daily_quests],
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
        }

    @staticmethod
    def from_dict(data: dict) -> "GardenState":
        state = GardenState()
        for key in [
            "version",
            "streak_days",
            "total_reviews",
            "total_correct",
            "total_wrong",
            "currency",
            "unlocked_slots",
            "selected_background",
            "selected_weather",
            "journal",
            "inventory",
            "equipped",
            "purchased_items",
            "streak_freeze_tokens",
            "recovery_mode",
            "last_active_day",
            "focus_plant_id",
            "deck_plant_map",
        ]:
            if key in data:
                setattr(state, key, data[key])
        state.plants = [Plant(**p) for p in data.get("plants", [])]
        state.achievements = {
            k: Achievement(**v) for k, v in data.get("achievements", {}).items()
        }
        parsed_quests: List[Quest] = []
        for q in data.get("daily_quests", []):
            if "metric" not in q:
                q["metric"] = q.get("quest_id", "reviewed")
            parsed_quests.append(Quest(**q))
        state.daily_quests = parsed_quests
        if "daily_stats" in data:
            state.daily_stats = DailyStats(**data["daily_stats"])
        return state
