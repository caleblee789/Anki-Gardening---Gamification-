from __future__ import annotations

import random
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from .asset_manager import AssetManager
from .models.state import Achievement, GardenState, Quest


class GardenGameEngine:
    def __init__(self, config: Any, storage: Any) -> None:
        self.config = config
        self.storage = storage
        self.state: GardenState = storage.state
        self.assets = AssetManager(config, storage)
        self._ensure_achievements()
        self._ensure_daily_quests()

    def rollover_if_needed(self) -> None:
        today = date.today().isoformat()
        if self.state.daily_stats.day == today:
            return
        self._apply_streak_rollover(today)
        self.state.daily_stats.day = today
        self.state.daily_stats.reviewed = 0
        self.state.daily_stats.correct = 0
        self.state.daily_stats.wrong = 0
        self.state.daily_stats.new_count = 0
        self.state.daily_stats.learning_count = 0
        self.state.daily_stats.review_count = 0
        self.state.daily_stats.growth_earned = 0
        self.state.daily_stats.completed_due_cards = False
        self._ensure_daily_quests(force_refresh=True)
        self.storage.save()

    def _apply_streak_rollover(self, today: str) -> None:
        last = date.fromisoformat(self.state.last_active_day)
        now = date.fromisoformat(today)
        missed = (now - last).days - 1
        grace = self.config.value("streak_grace_period_days", 1)
        if missed <= grace:
            pass
        elif missed > 0:
            self.state.streak_days = max(0, self.state.streak_days - min(missed, 3))
            decay = float(self.config.value("vitality_decay_sensitivity", 0.08))
            for plant in self.state.plants:
                plant.vitality = max(0.45, plant.vitality - decay * missed)
        self.state.last_active_day = today

    def register_review(self, review_payload: Dict[str, Any]) -> None:
        self.rollover_if_needed()
        today = self.state.daily_stats
        today.reviewed += 1
        self.state.total_reviews += 1

        queue = review_payload.get("queue", 2)
        ease = int(review_payload.get("ease", 1))
        deck_id = review_payload.get("deck_id")

        is_correct = ease > 1
        if is_correct:
            today.correct += 1
        else:
            today.wrong += 1

        card_type = "review"
        if queue == 0:
            card_type = "new"
            today.new_count += 1
        elif queue in (1, 3):
            card_type = "learning"
            today.learning_count += 1
        else:
            today.review_count += 1

        growth = self._calculate_growth(card_type, is_correct)
        if growth > 0:
            self._apply_growth(growth, deck_id)
            today.growth_earned += growth
        self._update_quests(card_type, is_correct)
        self._update_achievements()
        self._maybe_unlock_slot()
        self.storage.save()

    def _calculate_growth(self, card_type: str, is_correct: bool) -> int:
        cap = int(self.config.value("daily_growth_cap", 220))
        if self.state.daily_stats.growth_earned >= cap:
            return 0
        mapping = self.config.value("points_per_card", {})
        base = int(mapping.get(card_type, 2))
        if not is_correct:
            base = max(1, int(base * 0.5))
        if self.state.focus_plant_id and self.state.daily_stats.reviewed < self.config.value("daily_goal", 140):
            base = int(base * self.config.value("focus_target_bonus", 1.2))
        available = cap - self.state.daily_stats.growth_earned
        return min(base, available)

    def _apply_growth(self, growth: int, deck_id: Optional[int]) -> None:
        plants = self.state.plants
        if self.config.value("deck_specific_growth_mode") and deck_id is not None:
            matched = [p for p in plants if p.assigned_deck_id == deck_id]
            if matched:
                plants = matched
        if not plants:
            return
        gain = max(1, growth // len(plants))
        for plant in plants:
            plant.growth_points += gain
            plant.vitality = min(1.0, plant.vitality + 0.02)
            if plant.growth_stage == "flowering" and self.state.streak_days >= 10 and random.random() < 0.004:
                plant.rare_variant = True

    def _ensure_achievements(self) -> None:
        defs = {
            "streak_7": ("7-Day Rhythm", "Study seven days in a row."),
            "reviews_100_day": ("Century Day", "Complete 100 reviews in one day."),
            "reviews_1000_total": ("Deep Roots", "Complete 1000 total reviews."),
            "retention_90": ("Clear Recall", "Reach at least 90% accuracy in a day."),
            "all_due_done": ("Inbox Zero", "Finish all due cards for today."),
            "moonflower": ("Moonflower", "Study after 10 PM."),
            "sunbloom": ("Sunbloom", "Study before 7 AM."),
        }
        for aid, (name, desc) in defs.items():
            if aid not in self.state.achievements:
                self.state.achievements[aid] = Achievement(aid, name, desc)

    def _ensure_daily_quests(self, force_refresh: bool = False) -> None:
        if self.state.daily_quests and not force_refresh:
            return
        difficulty = self.config.value("quest_difficulty", "normal")
        targets = {
            "easy": (35, 20),
            "normal": (50, 30),
            "hard": (80, 45),
        }.get(difficulty, (50, 30))
        self.state.daily_quests = [
            Quest("reviews", f"Complete {targets[0]} reviews", targets[0], reward_growth=20, reward_currency=12),
            Quest("accuracy", "Maintain 85%+ accuracy", 85, reward_growth=15, reward_currency=8),
            Quest("learning", f"Finish {targets[1]} learning/review cards", targets[1], reward_growth=18, reward_currency=10),
        ]

    def _update_quests(self, card_type: str, is_correct: bool) -> None:
        stats = self.state.daily_stats
        for quest in self.state.daily_quests:
            if quest.completed:
                continue
            if quest.quest_id == "reviews":
                quest.progress = stats.reviewed
            elif quest.quest_id == "accuracy":
                quest.progress = int(stats.accuracy * 100)
            elif quest.quest_id == "learning":
                quest.progress = stats.review_count + stats.learning_count

            if quest.progress >= quest.target:
                quest.completed = True
                self.state.currency += quest.reward_currency
                self._apply_growth(quest.reward_growth, None)

    def set_due_completion(self, completed: bool) -> None:
        self.state.daily_stats.completed_due_cards = completed
        self._update_achievements()
        self.storage.save()

    def set_journal_note(self, day: str, note: str) -> None:
        self.state.journal[day] = note.strip()
        self.storage.save()

    def _update_achievements(self) -> None:
        stats = self.state.daily_stats
        now = datetime.now().hour
        checks = {
            "streak_7": self.state.streak_days >= 7,
            "reviews_100_day": stats.reviewed >= 100,
            "reviews_1000_total": self.state.total_reviews >= 1000,
            "retention_90": stats.reviewed >= 20 and stats.accuracy >= 0.9,
            "all_due_done": stats.completed_due_cards,
            "moonflower": now >= 22,
            "sunbloom": now <= 7,
        }
        for aid, achieved in checks.items():
            ach = self.state.achievements[aid]
            if achieved:
                ach.unlocked = True
                if aid in ("moonflower", "sunbloom"):
                    self.state.currency += 3
            ach.progress = 1.0 if ach.unlocked else 0.0

    def _maybe_unlock_slot(self) -> None:
        unlocked = self.state.unlocked_slots
        max_slots = self.config.value("max_slots", 6)
        if unlocked >= max_slots:
            return
        milestones = [250, 700, 1500, 2600]
        if unlocked - self.config.value("initial_slots", 2) < len(milestones):
            idx = unlocked - self.config.value("initial_slots", 2)
            if idx >= 0 and self.state.total_reviews >= milestones[idx]:
                self.state.unlocked_slots += 1

    def seasonal_theme(self) -> str:
        if not self.config.value("seasonal_visuals", True):
            return "default"
        month = date.today().month
        if month in (12, 1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        return "autumn"

    def resolve_plant_image(self, species: str, stage: str, rare: bool) -> Optional[str]:
        stage_query = {
            "seed": "seed in soil macro photography",
            "sprout": f"{species} sprout plant",
            "young": f"young {species} potted plant",
            "mature": f"mature healthy {species} plant",
            "flowering": f"flowering {species} plant",
            "rare": f"rare variegated {species} botanical",
        }
        effective_stage = "rare" if rare else stage
        key = f"{species}_{effective_stage}"
        path = self.assets.get_or_fetch("plants", key, stage_query[effective_stage])
        return str(path) if path else None

    def resolve_background_image(self) -> Optional[str]:
        theme = self.seasonal_theme()
        query = {
            "winter": "minimal winter japanese garden",
            "spring": "lush spring garden courtyard",
            "summer": "sunny botanical garden landscape",
            "autumn": "autumn garden with warm tones",
            "default": "calm garden courtyard",
        }[theme]
        path = self.assets.get_or_fetch("backgrounds", f"bg_{theme}", query)
        return str(path) if path else None
