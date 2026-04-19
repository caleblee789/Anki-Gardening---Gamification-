from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "enable_sounds": False,
    "enable_animations": True,
    "daily_growth_cap": 220,
    "daily_goal": 140,
    "points_per_card": {"new": 4, "learning": 3, "review": 2},
    "streak_grace_period_days": 1,
    "quest_difficulty": "normal",
    "deck_specific_growth_mode": False,
    "show_reviewer_button": True,
    "vitality_decay_sensitivity": 0.08,
    "seasonal_visuals": True,
    "image_api": {
        "provider_priority": ["unsplash", "pexels", "pixabay"],
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
