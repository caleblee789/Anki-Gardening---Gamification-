from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "enable_sounds": False,
    "enable_animations": True,
    "daily_growth_cap": 220,
    "daily_goal": 140,
    "points_per_card": {"new": 4, "learning": 3, "review": 2},
    "correct_answer_bonus": 1.08,
    "incorrect_answer_penalty": 0.6,
    "difficulty_weight": 0.12,
    "recovery_weight": 0.2,
    "session_quality_weight": 0.25,
    "streak_grace_period_days": 1,
    "quest_difficulty": "normal",
    "default_garden_mode": "unified",
    "show_reviewer_button": True,
    "show_toolbar_button": True,
    "vitality_decay_sensitivity": 0.08,
    "seasonal_visuals": True,
    "time_of_day_bonus": True,
    "allow_streak_freeze": True,
    "max_daily_quests": 3,
    "daily_snapshot": True,
    "snapshot_frequency_days": 1,
    "burnout_detection": True,
    "burnout_volume_threshold": 500,
    "rare_event_frequency": 1.0,
    "image_api": {
        "provider_priority": ["wikimedia", "unsplash", "pexels", "pixabay"],
        "enable_builtin_no_key_sources": True,
        "unsplash_access_key": "",
        "pexels_api_key": "",
        "pixabay_api_key": "",
        "request_timeout_sec": 8,
        "max_retries": 3,
        "rate_limit_seconds": 1.2,
    },
    "initial_slots": 2,
    "max_slots": 6,
    "currency_name": "dew drops",
    "focus_target_bonus": 1.2,
    "focus_mode": {"durations": [25, 45, 60], "growth_multiplier": 1.15},
    "exam_mode": {"deck_weight_boost": 1.25},
    "sound_cues": {"growth": "", "achievement": "", "quest": ""},
    "future_features": {"enable_weekly_events": True},
    "visual_theme": "verdant_dusk",
    "asset_quality": "balanced",
    "theme_overrides": {
        "palette": {
            "sky_top": "#141e33",
            "sky_bottom": "#1d4b55",
            "ground_top": "#3a7a47",
            "ground_bottom": "#223f2b",
            "glow": "#95efae",
            "panel_bg": "#18252e",
            "panel_border": "#2f4652",
            "text_primary": "#e6f0ea",
            "text_muted": "#91a8ae",
        },
        "typography_scale": 1.0,
        "panel_opacity": 0.9,
        "animation_intensity": 0.7,
        "weather_particle_density": 1.0,
    },
}


class ConfigManager:
    def __init__(self, mw: Any) -> None:
        self.mw = mw
        self._config = deepcopy(DEFAULT_CONFIG)
        self.reload()

    def reload(self) -> None:
        if self.mw is None:
            return
        addon_key = self.mw.addonManager.addonFromModule(__name__)
        user_conf = self.mw.addonManager.getConfig(addon_key) or {}
        self._config = self._merge(deepcopy(DEFAULT_CONFIG), user_conf)

    def value(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def nested(self, *keys: str, default: Any = None) -> Any:
        node: Any = self._config
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key)
            if node is None:
                return default
        return node

    @staticmethod
    def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = ConfigManager._merge(base[key], value)
            else:
                base[key] = value
        return base
