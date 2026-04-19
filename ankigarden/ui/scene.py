from __future__ import annotations

import math
from typing import Any

from aqt.qt import QLinearGradient, QPainter, QPainterPath, QPen, QRectF, QTimer, QWidget, Qt, QColor


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
        self.scene = payload
        self.update()

    def _tick(self) -> None:
        intensity = max(0.1, float(self.scene.get("animation_intensity", 0.7)))
        self.phase += 0.02 + (0.06 * intensity)
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        try:
            sky = QLinearGradient(0, 0, 0, r.height())
            health = float(self.scene.get("health", 0.7))
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
            growth = max(0.0, min(1.0, float(self.scene.get("growth", 0.0))))

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
            density = max(0.2, float(self.scene.get("weather_particle_density", 1.0)))
            if weather in ("gentle_rain", "cloudy"):
                pen = QPen(QColor(170, 205, 255, 90), 1)
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
                    painter.setBrush(QColor(247, 237, 130, 125))
                    painter.drawEllipse(QRectF(x, y, 3.5, 3.5))

            painter.setPen(QColor(210, 245, 222, glow))
            painter.drawText(18, 32, "Your live study garden")
            painter.drawText(18, 52, f"Daily growth energy: {int(growth * 100)}%")
        except Exception:
            self._draw_fallback_scene(painter, r)

    def _draw_plant(self, painter: QPainter, x: float, y: float, plant: dict[str, Any], idx: int) -> None:
        stage_scale = {"seed": 0.35, "sprout": 0.5, "young": 0.72, "mature": 0.93, "flowering": 1.08, "rare": 1.15}
        stage = plant.get("stage", "seed")
        scale = stage_scale.get(stage, 0.6)
        vitality = max(0.2, float(plant.get("vitality", 0.8)))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(62, 45, 38))
        painter.drawEllipse(QRectF(x - 27, y - 14, 54, 23))

        painter.setPen(QPen(QColor(72, 138, 72), 3))
        stem_h = 95 * scale
        painter.drawLine(int(x), int(y), int(x), int(y - stem_h))

        leaf_color = QColor(45, 160, 96)
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
            painter.setBrush(QColor(106, 186, 88, 190))
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
        painter.fillRect(rect, QColor(27, 48, 44))
        painter.setPen(QColor(223, 237, 223))
        painter.drawText(rect.adjusted(20, 20, -20, -20), Qt.AlignmentFlag.AlignCenter, "Garden rendering fallback\nYour growth data is still active.")
