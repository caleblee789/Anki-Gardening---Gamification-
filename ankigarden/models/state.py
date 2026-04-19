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
    version: int = 1
    streak_days: int = 0
    total_reviews: int = 0
    currency: int = 0
    unlocked_slots: int = 2
    selected_background: str = "default"
    selected_weather: str = "sunny"
    plants: List[Plant] = field(default_factory=list)
    achievements: Dict[str, Achievement] = field(default_factory=dict)
    daily_quests: List[Quest] = field(default_factory=list)
    daily_stats: DailyStats = field(default_factory=DailyStats)
    journal: Dict[str, str] = field(default_factory=dict)
    last_active_day: str = field(default_factory=lambda: date.today().isoformat())
    focus_plant_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "streak_days": self.streak_days,
            "total_reviews": self.total_reviews,
            "currency": self.currency,
            "unlocked_slots": self.unlocked_slots,
            "selected_background": self.selected_background,
            "selected_weather": self.selected_weather,
            "plants": [p.__dict__ for p in self.plants],
            "achievements": {k: v.__dict__ for k, v in self.achievements.items()},
            "daily_quests": [q.__dict__ for q in self.daily_quests],
            "daily_stats": self.daily_stats.__dict__,
            "journal": self.journal,
            "last_active_day": self.last_active_day,
            "focus_plant_id": self.focus_plant_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "GardenState":
        state = GardenState()
        for key in [
            "version",
            "streak_days",
            "total_reviews",
            "currency",
            "unlocked_slots",
            "selected_background",
            "selected_weather",
            "last_active_day",
            "focus_plant_id",
        ]:
            if key in data:
                setattr(state, key, data[key])
        state.plants = [Plant(**p) for p in data.get("plants", [])]
        state.achievements = {
            k: Achievement(**v) for k, v in data.get("achievements", {}).items()
        }
        state.daily_quests = [Quest(**q) for q in data.get("daily_quests", [])]
        if "daily_stats" in data:
            state.daily_stats = DailyStats(**data["daily_stats"])
        state.journal = data.get("journal", {})
        return state
