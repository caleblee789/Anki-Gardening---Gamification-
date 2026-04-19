from __future__ import annotations

import random
from datetime import date, datetime
from typing import Any, Dict, Optional

from .asset_manager import AssetManager
from .models.state import Achievement, GardenState, Plant, Quest


class GardenGameEngine:
    SPECIES_PERSONALITY = {
        "bonsai": "streak",
        "rose": "accuracy",
        "cactus": "volume",
        "orchid": "difficult",
        "moonflower": "night",
        "sunbloom": "morning",
    }

    SHOP_ITEMS = {
        "plants:cactus": 140,
        "plants:orchid": 220,
        "plants:moonflower": 280,
        "plants:sunbloom": 280,
        "pots:charcoal_modern": 80,
        "backgrounds:zen_path": 120,
        "decorations:butterflies": 130,
        "weather:fireflies": 160,
    }

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
        self.state.daily_stats.difficult_count = 0
        self.state.daily_stats.growth_earned = 0
        self.state.daily_stats.completed_due_cards = False
        self._ensure_daily_quests(force_refresh=True)
        self._update_weather()
        self.storage.save()

    def _apply_streak_rollover(self, today: str) -> None:
        last = date.fromisoformat(self.state.last_active_day)
        now = date.fromisoformat(today)
        missed = max(0, (now - last).days - 1)
        grace = self.config.value("streak_grace_period_days", 1)
        if missed <= grace:
            self.state.recovery_mode = False
        elif missed > 0:
            if self.state.streak_freeze_tokens > 0:
                self.state.streak_freeze_tokens -= 1
            else:
                self.state.streak_days = max(0, self.state.streak_days - min(missed, 4))
                decay = float(self.config.value("vitality_decay_sensitivity", 0.08))
                for plant in self.state.plants:
                    plant.vitality = max(0.42, plant.vitality - decay * missed)
                self.state.recovery_mode = True
        self.state.last_active_day = today

    def register_review(self, review_payload: Dict[str, Any]) -> None:
        self.rollover_if_needed()
        today = self.state.daily_stats
        first_review_today = today.reviewed == 0
        if first_review_today:
            self.state.streak_days += 1
            self.state.last_active_day = date.today().isoformat()

        today.reviewed += 1
        self.state.total_reviews += 1

        queue = review_payload.get("queue", 2)
        ease = int(review_payload.get("ease", 1))
        deck_id = review_payload.get("deck_id")

        is_correct = ease > 1
        if is_correct:
            today.correct += 1
            self.state.total_correct += 1
        else:
            today.wrong += 1
            self.state.total_wrong += 1
            today.difficult_count += 1

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
        self._update_quests()
        self._update_achievements()
        self._maybe_unlock_slot()
        self._update_weather()
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

    def _eligible_plants(self, deck_id: Optional[int]) -> list[Plant]:
        plants = self.state.plants
        if self.config.value("deck_specific_growth_mode") and deck_id is not None:
            mapped = self.state.deck_plant_map.get(str(deck_id))
            if mapped:
                selected = [p for p in plants if p.plant_id == mapped]
                if selected:
                    return selected
        return plants

    def _apply_growth(self, growth: int, deck_id: Optional[int]) -> None:
        plants = self._eligible_plants(deck_id)
        if not plants:
            return
        gain = max(1, growth // len(plants))
        hour = datetime.now().hour
        for plant in plants:
            personality = plant.personality or "balanced"
            adjusted = gain
            if personality == "volume" and self.state.daily_stats.reviewed >= 100:
                adjusted += 1
            elif personality == "streak" and self.state.streak_days >= 7:
                adjusted += 1
            elif personality == "accuracy" and self.state.daily_stats.accuracy >= 0.88:
                adjusted += 1
            elif personality == "difficult" and self.state.daily_stats.difficult_count >= 8:
                adjusted += 1
            elif personality == "night" and hour >= 22:
                adjusted += 2
            elif personality == "morning" and hour <= 7:
                adjusted += 2

            plant.growth_points += adjusted
            plant.vitality = min(1.0, plant.vitality + 0.03)
            if plant.growth_stage == "flowering" and self.state.streak_days >= 10 and random.random() < 0.006:
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
        review_target, learning_target = {
            "easy": (35, 20),
            "normal": (50, 30),
            "hard": (80, 45),
        }.get(difficulty, (50, 30))
        rng = random.Random(date.today().toordinal())
        quest_pool = [
            Quest("reviews", f"Complete {review_target} reviews", review_target, "reviewed", reward_growth=20, reward_currency=12),
            Quest("accuracy", "Maintain at least 85% accuracy", 85, "accuracy", reward_growth=15, reward_currency=8),
            Quest("learning", f"Finish {learning_target} learning/review cards", learning_target, "lr_total", reward_growth=18, reward_currency=10),
            Quest("difficult", "Recover 8 failed cards", 8, "difficult", reward_growth=16, reward_currency=9),
        ]
        self.state.daily_quests = rng.sample(quest_pool, k=3)

    def _metric_value(self, metric: str) -> int:
        stats = self.state.daily_stats
        if metric == "reviewed":
            return stats.reviewed
        if metric == "accuracy":
            return int(stats.accuracy * 100)
        if metric == "lr_total":
            return stats.learning_count + stats.review_count
        if metric == "difficult":
            return stats.difficult_count
        return 0

    def _update_quests(self) -> None:
        for quest in self.state.daily_quests:
            if quest.completed:
                continue
            quest.progress = self._metric_value(quest.metric)
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

    def assign_focus_plant(self, plant_id: Optional[str]) -> None:
        self.state.focus_plant_id = plant_id
        self.storage.save()

    def assign_deck_to_plant(self, deck_id: int, plant_id: str) -> None:
        self.state.deck_plant_map[str(deck_id)] = plant_id
        self.storage.save()

    def purchase_item(self, item_key: str) -> tuple[bool, str]:
        cost = self.SHOP_ITEMS.get(item_key)
        if cost is None:
            return False, "Item not found"
        if item_key in self.state.purchased_items:
            return False, "Already purchased"
        if self.state.currency < cost:
            return False, "Not enough currency"
        self.state.currency -= cost
        self.state.purchased_items.append(item_key)
        category, item = item_key.split(":", 1)
        self.state.inventory.setdefault(category, [])
        if item not in self.state.inventory[category]:
            self.state.inventory[category].append(item)
        self.storage.save()
        return True, "Purchased"

    def add_plant_to_slot(self, species: str, slot_index: int) -> bool:
        if slot_index >= self.state.unlocked_slots:
            return False
        if any(p.slot_index == slot_index for p in self.state.plants):
            return False
        personality = self.SPECIES_PERSONALITY.get(species, "balanced")
        plant = Plant(
            plant_id=f"plant_{len(self.state.plants)+1}",
            species=species,
            name=species.capitalize(),
            slot_index=slot_index,
            personality=personality,
        )
        self.state.plants.append(plant)
        self.storage.save()
        return True

    def _update_achievements(self) -> None:
        stats = self.state.daily_stats
        hour = datetime.now().hour
        checks = {
            "streak_7": self.state.streak_days >= 7,
            "reviews_100_day": stats.reviewed >= 100,
            "reviews_1000_total": self.state.total_reviews >= 1000,
            "retention_90": stats.reviewed >= 20 and stats.accuracy >= 0.9,
            "all_due_done": stats.completed_due_cards,
            "moonflower": hour >= 22,
            "sunbloom": hour <= 7,
        }
        for aid, achieved in checks.items():
            ach = self.state.achievements[aid]
            was_unlocked = ach.unlocked
            if achieved:
                ach.unlocked = True
                if not was_unlocked:
                    self.state.currency += 24
            ach.progress = 1.0 if ach.unlocked else 0.0

    def _maybe_unlock_slot(self) -> None:
        unlocked = self.state.unlocked_slots
        max_slots = self.config.value("max_slots", 6)
        if unlocked >= max_slots:
            return
        milestones = [250, 700, 1500, 2600, 4200]
        idx = unlocked - self.config.value("initial_slots", 2)
        if 0 <= idx < len(milestones) and self.state.total_reviews >= milestones[idx]:
            self.state.unlocked_slots += 1

    def _update_weather(self) -> None:
        s = self.state.daily_stats
        if self.state.recovery_mode:
            self.state.selected_weather = "gentle_rain"
        elif s.reviewed >= 120:
            self.state.selected_weather = "sunny"
        elif self.state.streak_days >= 7:
            self.state.selected_weather = "fireflies"
        elif s.wrong > s.correct and s.reviewed > 25:
            self.state.selected_weather = "cloudy"
        else:
            self.state.selected_weather = "breeze"

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
        effective = "rare" if rare else stage
        query_map = {
            "seed": "seed in soil macro photography botanical",
            "sprout": f"{species} sprout close up botanical",
            "young": f"young {species} potted plant natural light",
            "mature": f"mature healthy {species} houseplant",
            "flowering": f"flowering {species} botanical garden",
            "rare": f"rare variegated {species} plant specimen",
        }
        path = self.assets.get_or_fetch("plants", f"{species}_{effective}", query_map[effective])
        return str(path) if path else None

    def resolve_background_image(self) -> Optional[str]:
        seasonal = self.seasonal_theme()
        weather = self.state.selected_weather
        query = {
            "winter": "minimal winter japanese courtyard garden",
            "spring": "serene spring zen garden pathway",
            "summer": "sunny botanical garden courtyard",
            "autumn": "autumn courtyard garden warm leaves",
            "default": "calm minimalist garden courtyard",
        }[seasonal]
        if weather == "fireflies":
            query = "night garden with fireflies calm"
        elif weather == "gentle_rain":
            query = "soft rainy garden pathway"
        return str(self.assets.get_or_fetch("backgrounds", f"bg_{seasonal}_{weather}", query) or "") or None

    def resolve_weather_overlay(self) -> Optional[str]:
        query = {
            "sunny": "soft sunlight bokeh transparent background",
            "cloudy": "light cloud texture overlay",
            "fireflies": "fireflies night bokeh",
            "gentle_rain": "gentle rain droplets bokeh",
            "breeze": "soft floating pollen particles",
        }.get(self.state.selected_weather, "soft sunlight bokeh")
        path = self.assets.get_or_fetch("weather", f"weather_{self.state.selected_weather}", query)
        return str(path) if path else None

    def resolve_decoration_image(self, decoration: str) -> Optional[str]:
        query = f"garden decoration {decoration.replace('_', ' ')}"
        path = self.assets.get_or_fetch("decorations", f"decor_{decoration}", query)
        return str(path) if path else None
