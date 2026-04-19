from __future__ import annotations

import math
from typing import Any

from aqt.qt import QLinearGradient, QPainter, QPainterPath, QPen, QRectF, QTimer, QWidget, Qt, QColor

SCENE_TEXT = {
    "live_garden_label": "Your live study garden",
    "growth_energy_label": "Daily growth energy: {growth}%",
    "fallback_message": (
        "We couldn't render the animated garden view.\n"
        "Your study progress, growth updates, and rewards are still being tracked."
    ),
}


class GardenSceneWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(320)
        self.phase = 0.0
        self.scene: dict[str, Any] = {"plants": [], "weather": "breeze", "health": 0.7, "growth": 0.2}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(42)

    def set_scene(self, payload: dict[str, Any]) -> None:
        self.scene = self._sanitize_scene_payload(payload)
        self.update()

    def _coerce_float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _clamp(self, value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _sanitize_scene_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        safe_scene = dict(payload or {})
        safe_scene["growth"] = self._clamp(self._coerce_float(safe_scene.get("growth", 0.0), 0.0), 0.0, 1.0)
        safe_scene["health"] = self._clamp(self._coerce_float(safe_scene.get("health", 0.7), 0.7), 0.0, 1.0)
        safe_scene["animation_intensity"] = self._clamp(
            self._coerce_float(safe_scene.get("animation_intensity", 0.7), 0.7), 0.1, 1.6
        )
        safe_scene["weather_particle_density"] = self._clamp(
            self._coerce_float(safe_scene.get("weather_particle_density", 1.0), 1.0), 0.2, 1.25
        )
        plants = safe_scene.get("plants", [])
        safe_scene["plants"] = plants if isinstance(plants, list) else []
        return safe_scene

    def _tick(self) -> None:
        intensity = self._clamp(self._coerce_float(self.scene.get("animation_intensity", 0.7), 0.7), 0.1, 1.6)
        self.phase += 0.02 + (0.06 * intensity)
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        try:
            sky = QLinearGradient(0, 0, 0, r.height())
            health = self._clamp(self._coerce_float(self.scene.get("health", 0.7), 0.7), 0.0, 1.0)
            glow = min(255, 90 + int(120 * health))
            night = bool(self.scene.get("night_mode", False))
            if night:
                sky.setColorAt(0.0, QColor(11, 18, 38))
                sky.setColorAt(0.55, QColor(20, 38, 64))
                sky.setColorAt(1.0, QColor(12, 24, 30))
            else:
                sky.setColorAt(0.0, QColor(18, 26, 46))
                sky.setColorAt(0.55, QColor(27, 60, 72))
                sky.setColorAt(1.0, QColor(16, 30, 26))
            painter.fillRect(r, sky)
            growth = self._clamp(self._coerce_float(self.scene.get("growth", 0.0), 0.0), 0.0, 1.0)

            sun_x = r.width() * (0.75 + 0.02 * math.sin(self.phase / 4))
            sun_y = r.height() * 0.2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 220, 130, 95 if self.scene.get("weather") != "cloudy" else 35))
            painter.drawEllipse(QRectF(sun_x - 55, sun_y - 55, 110, 110))
            painter.setBrush(QColor(150, 255, 170, int(18 + growth * 40)))
            painter.drawEllipse(QRectF(sun_x - 80, sun_y - 80, 160, 160))

            ground = QLinearGradient(0, r.height() * 0.56, 0, r.height())
            ground.setColorAt(0.0, QColor(45, 90, 54))
            ground.setColorAt(1.0, QColor(26, 54, 32))
            painter.setBrush(ground)
            painter.drawRoundedRect(QRectF(0, r.height() * 0.56, r.width(), r.height() * 0.44), 0, 0)

            for i in range(26):
                x = (i * 67 + int(self.phase * 15)) % max(1, r.width())
                y = r.height() * 0.7 + 26 * math.sin(self.phase + i / 2)
                painter.setBrush(QColor(255, 255, 255, 18))
                painter.drawEllipse(QRectF(x, y, 2.5, 2.5))

            plants = self.scene.get("plants", [])
            if not plants:
                self._draw_fallback_scene(painter, r)
                return

            for idx, plant in enumerate(plants):
                x = (idx + 1) * (r.width() / (len(plants) + 1))
                base_y = r.height() * 0.76
                sway = 6 * math.sin(self.phase + idx)
                self._draw_plant(painter, x + sway, base_y, plant, idx)
                if growth > 0.05:
                    painter.setPen(Qt.PenStyle.NoPen)
                    pulse_alpha = int(25 + 40 * (0.5 + 0.5 * math.sin(self.phase * 2 + idx)))
                    painter.setBrush(QColor(142, 247, 158, pulse_alpha))
                    painter.drawEllipse(QRectF(x - 26, base_y - 130, 52, 52))

            weather = self.scene.get("weather", "breeze")
            density = self._clamp(self._coerce_float(self.scene.get("weather_particle_density", 1.0), 1.0), 0.2, 1.25)
            if weather in ("gentle_rain", "cloudy"):
                weather_alpha = int(56 + (26 * density))
                pen = QPen(QColor(170, 205, 255, weather_alpha), 1)
                painter.setPen(pen)
                for i in range(int(34 * density)):
                    x = (i * 41 + int(self.phase * 65)) % max(1, r.width())
                    y = (i * 17 + int(self.phase * 95)) % max(1, r.height())
                    painter.drawLine(int(x), int(y), int(x - 5), int(y + 12))
            elif weather == "fireflies":
                painter.setPen(Qt.PenStyle.NoPen)
                for i in range(int(22 * density)):
                    x = (i * 59 + int(self.phase * 28)) % max(1, r.width())
                    y = r.height() * 0.22 + ((i * 31) % int(r.height() * 0.58))
                    firefly_alpha = int(75 + (25 * density))
                    painter.setBrush(QColor(247, 237, 130, firefly_alpha))
                    painter.drawEllipse(QRectF(x, y, 3.5, 3.5))

            text_outline = QColor(6, 18, 15, 185 if night else 165)
            painter.setPen(QPen(text_outline, 2.2))
            painter.drawText(18, 32, SCENE_TEXT["live_garden_label"])
            painter.drawText(18, 52, SCENE_TEXT["growth_energy_label"].format(growth=int(growth * 100)))
            painter.setPen(QColor(222, 249, 233, glow))
            painter.drawText(18, 32, SCENE_TEXT["live_garden_label"])
            painter.drawText(18, 52, SCENE_TEXT["growth_energy_label"].format(growth=int(growth * 100)))
        except Exception:
            self._draw_fallback_scene(painter, r)

    def _draw_plant(self, painter: QPainter, x: float, y: float, plant: dict[str, Any], idx: int) -> None:
        stage_scale = {"seed": 0.35, "sprout": 0.5, "young": 0.72, "mature": 0.93, "flowering": 1.08, "rare": 1.15}
        stage = plant.get("stage", "seed")
        scale = stage_scale.get(stage, 0.6)
        vitality = self._clamp(self._coerce_float(plant.get("vitality", 0.8), 0.8), 0.2, 1.0)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(62, 45, 38))
        painter.drawEllipse(QRectF(x - 27, y - 14, 54, 23))

        stem_width = 2.2 + (1.7 * scale)
        stem_color = QColor(72, 138, 72) if stage != "seed" else QColor(104, 120, 88)
        painter.setPen(QPen(stem_color, stem_width))
        stem_h = 95 * scale
        painter.drawLine(int(x), int(y), int(x), int(y - stem_h))

        leaf_palette = {
            "seed": QColor(126, 114, 90),
            "sprout": QColor(86, 162, 102),
            "young": QColor(54, 168, 102),
            "mature": QColor(42, 158, 94),
            "flowering": QColor(52, 176, 108),
            "rare": QColor(86, 198, 126),
        }
        leaf_color = leaf_palette.get(stage, QColor(45, 160, 96))
        leaf_color.setAlphaF(vitality)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(leaf_color)
        for side in (-1, 1):
            path = QPainterPath()
            path.moveTo(x, y - stem_h * 0.58)
            path.quadTo(x + side * 34 * scale, y - stem_h * 0.5, x + side * 16 * scale, y - stem_h * 0.28)
            path.quadTo(x + side * 6 * scale, y - stem_h * 0.38, x, y - stem_h * 0.58)
            painter.drawPath(path)

        if stage in ("mature", "flowering", "rare"):
            canopy_color = QColor(106, 186, 88, 190) if stage != "rare" else QColor(98, 203, 126, 205)
            painter.setBrush(canopy_color)
            painter.drawEllipse(QRectF(x - 18 * scale, y - stem_h - 26 * scale, 36 * scale, 34 * scale))
        if stage in ("flowering", "rare"):
            painter.setBrush(QColor(246, 126 + (idx * 20) % 85, 180, 220))
            for a in range(6):
                angle = (math.pi * 2 * a / 6.0) + self.phase / 5
                fx = x + math.cos(angle) * 11 * scale
                fy = y - stem_h - 14 * scale + math.sin(angle) * 11 * scale
                painter.drawEllipse(QRectF(fx - 5, fy - 5, 10, 10))
            painter.setBrush(QColor(255, 232, 148, 230))
            painter.drawEllipse(QRectF(x - 4, y - stem_h - 18 * scale, 8, 8))
        if stage == "rare" or plant.get("rare_variant"):
            painter.setPen(QPen(QColor(255, 230, 138, 190), 1.7))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(x - 30 * scale, y - stem_h - 42 * scale, 60 * scale, 54 * scale))

    def _draw_fallback_scene(self, painter: QPainter, rect: Any) -> None:
        fallback_gradient = QLinearGradient(0, 0, 0, rect.height())
        fallback_gradient.setColorAt(0.0, QColor(18, 35, 48))
        fallback_gradient.setColorAt(0.65, QColor(24, 55, 56))
        fallback_gradient.setColorAt(1.0, QColor(19, 44, 38))
        painter.fillRect(rect, fallback_gradient)
        painter.setPen(QPen(QColor(6, 18, 15, 170), 2))
        painter.drawText(
            rect.adjusted(20, 20, -20, -20),
            Qt.AlignmentFlag.AlignCenter,
            SCENE_TEXT["fallback_message"],
        )
        painter.setPen(QColor(223, 237, 223))
        painter.drawText(
            rect.adjusted(20, 20, -20, -20),
            Qt.AlignmentFlag.AlignCenter,
            SCENE_TEXT["fallback_message"],
        )
