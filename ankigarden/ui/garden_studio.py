from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from aqt.qt import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    Qt,
)

from .scene import GardenSceneWidget


class GardenStudioWidget(QWidget):
    def __init__(self, config: Any, on_reroll: Callable[[str], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.on_reroll = on_reroll
        self.preview = self._default_preview()
        self.scene = GardenSceneWidget()
        self.attribution_cards: dict[str, QLabel] = {}
        self._build_ui()
        self._apply_preview()

    def _default_preview(self) -> dict[str, Any]:
        palette = deepcopy(self.config.nested("theme_overrides", "palette", default={}))
        return {
            "theme": self.config.value("visual_theme", "verdant_dusk"),
            "weather": "breeze",
            "growth_stage": "young",
            "night_mode": False,
            "animation_intensity": float(self.config.nested("theme_overrides", "animation_intensity", default=0.7)),
            "weather_particle_density": float(
                self.config.nested("theme_overrides", "weather_particle_density", default=1.0)
            ),
            "panel_opacity": float(self.config.nested("theme_overrides", "panel_opacity", default=0.9)),
            "palette": palette,
        }

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        controls = QFrame()
        form = QFormLayout(controls)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Verdant Dusk", "verdant_dusk")
        self.theme_combo.addItem("Morning Bloom", "morning_bloom")
        self.theme_combo.addItem("Moonlit Study", "moonlit_study")
        self.theme_combo.setCurrentText(self.config.value("visual_theme", "verdant_dusk").replace("_", " ").title())
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        self.asset_quality_combo = QComboBox()
        self.asset_quality_combo.addItem("Balanced", "balanced")
        self.asset_quality_combo.addItem("Performance", "performance")
        self.asset_quality_combo.addItem("Ultra", "ultra")
        current_quality = self.config.value("asset_quality", "balanced")
        idx = max(0, self.asset_quality_combo.findData(current_quality))
        self.asset_quality_combo.setCurrentIndex(idx)

        self.day_night = QCheckBox("Night mode preview")
        self.day_night.toggled.connect(self._on_preview_toggle)

        self.weather_combo = QComboBox()
        for weather in ["breeze", "cloudy", "gentle_rain", "fireflies", "sunny"]:
            self.weather_combo.addItem(weather.replace("_", " ").title(), weather)
        self.weather_combo.currentIndexChanged.connect(self._on_preview_toggle)

        self.growth_stage_combo = QComboBox()
        for stage in ["seed", "sprout", "young", "mature", "flowering", "rare"]:
            self.growth_stage_combo.addItem(stage.title(), stage)
        self.growth_stage_combo.setCurrentIndex(2)
        self.growth_stage_combo.currentIndexChanged.connect(self._on_preview_toggle)

        self.anim_slider = QSlider(Qt.Orientation.Horizontal)
        self.anim_slider.setRange(0, 100)
        self.anim_slider.setValue(int(self.preview["animation_intensity"] * 100))
        self.anim_slider.valueChanged.connect(self._on_slider_changed)

        self.particle_slider = QSlider(Qt.Orientation.Horizontal)
        self.particle_slider.setRange(10, 200)
        self.particle_slider.setValue(int(self.preview["weather_particle_density"] * 100))
        self.particle_slider.valueChanged.connect(self._on_slider_changed)

        form.addRow("Visual theme", self.theme_combo)
        form.addRow("Asset quality", self.asset_quality_combo)
        form.addRow("Preview day/night", self.day_night)
        form.addRow("Preview weather", self.weather_combo)
        form.addRow("Preview growth stage", self.growth_stage_combo)
        form.addRow("Animation intensity", self.anim_slider)
        form.addRow("Weather particle density", self.particle_slider)

        root.addWidget(controls)
        root.addWidget(self.scene, 1)

        attribution_frame = QFrame()
        attribution_layout = QVBoxLayout(attribution_frame)
        attribution_layout.addWidget(QLabel("Asset attribution"))
        for slot in ["background", "plant", "weather"]:
            card = QFrame()
            card_layout = QHBoxLayout(card)
            label = QLabel(f"{slot.title()}: source unavailable")
            label.setWordWrap(True)
            reroll = QPushButton(f"Re-roll {slot}")
            reroll.clicked.connect(lambda _checked=False, s=slot: self._reroll_slot(s))
            card_layout.addWidget(label, 1)
            card_layout.addWidget(reroll)
            attribution_layout.addWidget(card)
            self.attribution_cards[slot] = label
        root.addWidget(attribution_frame)

    def _on_theme_changed(self) -> None:
        self.preview["theme"] = str(self.theme_combo.currentData())
        self._apply_preview()

    def _on_preview_toggle(self) -> None:
        self.preview["night_mode"] = self.day_night.isChecked()
        self.preview["weather"] = str(self.weather_combo.currentData())
        self.preview["growth_stage"] = str(self.growth_stage_combo.currentData())
        self._apply_preview()

    def _on_slider_changed(self) -> None:
        self.preview["animation_intensity"] = self.anim_slider.value() / 100.0
        self.preview["weather_particle_density"] = self.particle_slider.value() / 100.0
        self._apply_preview()

    def _apply_preview(self) -> None:
        growth = 0.85 if self.preview["growth_stage"] in ("flowering", "rare") else 0.45
        if self.preview["growth_stage"] in ("seed", "sprout"):
            growth = 0.15
        scene_payload = {
            "weather": self.preview["weather"],
            "growth": growth,
            "health": 0.85,
            "theme": self.preview["theme"],
            "night_mode": self.preview["night_mode"],
            "animation_intensity": self.preview["animation_intensity"],
            "weather_particle_density": self.preview["weather_particle_density"],
            "plants": [
                {
                    "name": "Preview Plant",
                    "species": "rose",
                    "stage": self.preview["growth_stage"],
                    "vitality": 0.95,
                }
            ],
        }
        self.scene.set_scene(scene_payload)

    def set_asset_attributions(self, attributions: dict[str, dict[str, str]]) -> None:
        for slot, label in self.attribution_cards.items():
            attr = attributions.get(slot, {})
            source = attr.get("page_url") or attr.get("source_url") or "unknown source"
            author = attr.get("author") or "unknown author"
            license_name = attr.get("license") or "license unknown"
            label.setText(f"{slot.title()}: {author} • {license_name} • {source}")

    def _reroll_slot(self, slot: str) -> None:
        if self.on_reroll:
            self.on_reroll(slot)

    def build_theme_payload(self) -> dict[str, Any]:
        return {
            "visual_theme": str(self.theme_combo.currentData()),
            "asset_quality": str(self.asset_quality_combo.currentData()),
            "theme_overrides": {
                "animation_intensity": self.anim_slider.value() / 100.0,
                "weather_particle_density": self.particle_slider.value() / 100.0,
                "panel_opacity": self.preview["panel_opacity"],
                "typography_scale": 1.0,
            },
        }
