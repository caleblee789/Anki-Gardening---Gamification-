from __future__ import annotations

import math
from typing import Any

from aqt import mw
from aqt.qt import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPainter,
    QPainterPath,
    QPen,
    QProgressBar,
    QPushButton,
    QRectF,
    QScrollArea,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
    QColor,
    QLinearGradient,
    QSizePolicy,
)


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
        self.phase += 0.06
        self.update()

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        try:
            sky = QLinearGradient(0, 0, 0, r.height())
            health = float(self.scene.get("health", 0.7))
            glow = min(255, 90 + int(120 * health))
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
            if weather in ("gentle_rain", "cloudy"):
                pen = QPen(QColor(170, 205, 255, 90), 1)
                painter.setPen(pen)
                for i in range(34):
                    x = (i * 41 + int(self.phase * 65)) % max(1, r.width())
                    y = (i * 17 + int(self.phase * 95)) % max(1, r.height())
                    painter.drawLine(int(x), int(y), int(x - 5), int(y + 12))
            elif weather == "fireflies":
                painter.setPen(Qt.PenStyle.NoPen)
                for i in range(22):
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


class GardenSettingsDialog(QDialog):
    def __init__(self, parent: QWidget, engine: Any, config: Any) -> None:
        super().__init__(parent)
        self.engine = engine
        self.config = config
        self.setWindowTitle("Anki Garden Settings")
        self.setMinimumSize(760, 520)
        root = QHBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        general = QWidget()
        g_layout = QFormLayout(general)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Unified All Decks", "unified")
        self.mode_combo.addItem("Deck-by-Deck", "deck-by-deck")
        current_mode = "deck-by-deck" if self.engine.state.garden_mode == "deck-by-deck" else "unified"
        self.mode_combo.setCurrentIndex(1 if current_mode == "deck-by-deck" else 0)
        save_mode = QPushButton("Apply Garden Mode")
        save_mode.clicked.connect(self._apply_mode)
        g_layout.addRow("Growth mode", self.mode_combo)
        g_layout.addRow(save_mode)

        mapping = QWidget()
        m_layout = QVBoxLayout(mapping)
        self.deck_combo = QComboBox()
        self.deck_combo.addItem("Choose deck", None)
        self.plant_combo = QComboBox()
        for plant in self.engine.state.plants:
            self.plant_combo.addItem(plant.name, plant.plant_id)
        try:
            for deck in mw.col.decks.all_names_and_ids():
                self.deck_combo.addItem(deck.name, deck.id)
        except Exception:
            pass
        map_btn = QPushButton("Map selected deck to plant")
        map_btn.clicked.connect(self._map_deck)
        m_layout.addWidget(self.deck_combo)
        m_layout.addWidget(self.plant_combo)
        m_layout.addWidget(map_btn)
        m_layout.addStretch(1)

        behavior = QWidget()
        b_layout = QVBoxLayout(behavior)
        b_layout.addWidget(QLabel("Visual pipeline: Procedural Qt rendering is enabled by default."))
        b_layout.addWidget(QLabel("External image APIs are optional enhancements only."))
        b_layout.addWidget(QLabel("Notifications, focus mode, and exam mode remain configurable from this dashboard."))
        b_layout.addStretch(1)

        advanced = QWidget()
        a_layout = QVBoxLayout(advanced)
        a_layout.addWidget(QLabel("Advanced / debug controls stay here to keep the home screen clean."))
        a_layout.addStretch(1)

        tabs.addTab(general, "General")
        tabs.addTab(mapping, "Deck Mapping")
        tabs.addTab(behavior, "Visuals & Behavior")
        tabs.addTab(advanced, "Advanced")

    def _apply_mode(self) -> None:
        self.engine.set_garden_mode(str(self.mode_combo.currentData()))
        QMessageBox.information(self, "Anki Garden", "Garden mode updated.")

    def _map_deck(self) -> None:
        deck_id = self.deck_combo.currentData()
        plant_id = self.plant_combo.currentData()
        if deck_id and plant_id:
            self.engine.assign_deck_to_plant(int(deck_id), str(plant_id))
            QMessageBox.information(self, "Anki Garden", "Deck mapping updated.")


class GardenDashboard(QDialog):
    def __init__(self, mw_window: Any, engine: Any, storage: Any, config: Any) -> None:
        super().__init__(mw_window)
        self.engine = engine
        self.storage = storage
        self.config = config
        self.settings_dialog: GardenSettingsDialog | None = None
        self.setWindowTitle("Anki Garden")
        self.setMinimumSize(1080, 720)
        self.resize(1240, 840)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QDialog { background: #101820; color: #e6f0ea; }
            QFrame[card='true'] { background: #18252e; border: 1px solid #2f4652; border-radius: 14px; }
            QLabel[muted='true'] { color: #91a8ae; }
            QLabel[title='true'] { font-size: 15px; font-weight: 700; letter-spacing: 0.2px; }
            QPushButton { background: #264456; border: 1px solid #3d6174; border-radius: 10px; padding: 7px 12px; font-weight: 600; }
            QPushButton:hover { background: #2f5468; }
            QProgressBar { border-radius: 7px; border: 1px solid #2f4652; background: #132029; }
            QProgressBar::chunk { background: #56ba7f; border-radius: 6px; }
            QListWidget { background: #12202a; border-radius: 10px; border: 1px solid #2a404d; padding: 4px; }
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        top = QFrame()
        top.setProperty("card", True)
        t_layout = QHBoxLayout(top)
        self.title_label = QLabel("🌿 Anki Garden")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 0.3px;")
        self.streak_chip = QLabel()
        self.progress_chip = QLabel()
        self.health_chip = QLabel()
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        t_layout.addWidget(self.title_label)
        t_layout.addStretch(1)
        for chip in (self.streak_chip, self.progress_chip, self.health_chip):
            chip.setStyleSheet("padding: 5px 10px; background:#213847; border-radius:12px;")
            t_layout.addWidget(chip)
        t_layout.addWidget(self.settings_btn)
        root.addWidget(top)

        hero_card = QFrame()
        hero_card.setProperty("card", True)
        h_layout = QVBoxLayout(hero_card)
        self.scene = GardenSceneWidget()
        self.hero_summary = QLabel()
        self.hero_summary.setWordWrap(True)
        self.hero_summary.setProperty("muted", True)
        self.hero_summary.setStyleSheet("line-height: 1.35;")
        self.hero_growth = QProgressBar()
        self.hero_growth.setMaximum(100)
        self.hero_growth.setFormat("Daily growth %p%")
        self.hero_growth.setStyleSheet(
            "QProgressBar{height:18px;font-weight:700;} QProgressBar::chunk{background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5fd484, stop:1 #d7ff8f);}"
        )
        self.retrospective_note = QLabel("")
        self.retrospective_note.setStyleSheet("color:#9ef3b0;")
        h_layout.addWidget(self.scene)
        h_layout.addWidget(self.hero_summary)
        h_layout.addWidget(self.hero_growth)
        h_layout.addWidget(self.retrospective_note)
        root.addWidget(hero_card, 2)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)
        self.quest_list = QListWidget()
        self.quest_list.setAlternatingRowColors(True)
        self.achievement_list = QListWidget()
        self.achievement_list.setAlternatingRowColors(True)
        self.focus_card = self._focus_card()
        self.inventory_list = QListWidget()
        self.inventory_list.setAlternatingRowColors(True)
        mid_row.addWidget(self._simple_card("Daily Quests", self.quest_list), 1)
        mid_row.addWidget(self._simple_card("Achievements", self.achievement_list), 1)
        mid_row.addWidget(self.focus_card, 1)
        mid_row.addWidget(self._simple_card("Inventory & Boosts", self.inventory_list), 1)
        root.addLayout(mid_row, 1)

        lower = QFrame()
        lower.setProperty("card", True)
        l_layout = QVBoxLayout(lower)
        self.roster_title = QLabel("Garden Roster")
        self.roster_title.setProperty("title", True)
        self.roster_grid = QGridLayout()
        self.roster_grid.setSpacing(10)
        roster_wrap = QWidget()
        roster_wrap.setLayout(self.roster_grid)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(roster_wrap)
        l_layout.addWidget(self.roster_title)
        l_layout.addWidget(scroll)
        root.addWidget(lower, 2)

    def _simple_card(self, title: str, body: QWidget) -> QFrame:
        f = QFrame()
        f.setProperty("card", True)
        l = QVBoxLayout(f)
        label = QLabel(title)
        label.setProperty("title", True)
        l.addWidget(label)
        l.addWidget(body)
        return f

    def _focus_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        heading = QLabel("Focus / Exam")
        heading.setProperty("title", True)
        layout.addWidget(heading)
        self.focus_duration = QComboBox()
        for minutes in self.config.nested("focus_mode", "durations", default=[25, 45, 60]):
            self.focus_duration.addItem(f"{minutes} min", int(minutes))
        btn_row = QHBoxLayout()
        start_focus = QPushButton("Start")
        complete_focus = QPushButton("Complete")
        cancel_focus = QPushButton("Cancel")
        start_focus.clicked.connect(self._start_focus)
        complete_focus.clicked.connect(self._complete_focus)
        cancel_focus.clicked.connect(self._cancel_focus)
        btn_row.addWidget(start_focus)
        btn_row.addWidget(complete_focus)
        btn_row.addWidget(cancel_focus)
        self.exam_date_input = QLineEdit()
        self.exam_date_input.setPlaceholderText("YYYY-MM-DD")
        exam_set = QPushButton("Set Exam")
        exam_off = QPushButton("Disable Exam")
        exam_set.clicked.connect(self._set_exam_date)
        exam_off.clicked.connect(self._disable_exam)
        layout.addWidget(self.focus_duration)
        layout.addLayout(btn_row)
        layout.addWidget(self.exam_date_input)
        layout.addWidget(exam_set)
        layout.addWidget(exam_off)
        layout.addStretch(1)
        return card

    def refresh_all(self) -> None:
        state = self.storage.state
        stats = state.daily_stats
        health = self.engine.garden_health_index()
        self.streak_chip.setText(f"Streak {state.streak_days}d")
        self.progress_chip.setText(f"Today {stats.reviewed} • {int(stats.accuracy * 100)}%")
        self.health_chip.setText(f"Health {int(health * 100)}")
        mode_text = "Unified all-decks" if state.garden_mode == "unified" else "Deck-by-deck"
        self.hero_summary.setText(
            f"{mode_text} mode • Weather: {state.selected_weather} • Event: {self.engine.get_weekly_event_summary()}\n"
            f"Keep accuracy high and complete quests to unlock flowering and rare forms. Every review visibly powers your garden."
        )
        growth_pct = int(min(100, (stats.growth_earned / max(1, self.config.value('daily_growth_cap', 220))) * 100))
        self.hero_growth.setValue(growth_pct)

        self.scene.set_scene(
            {
                "weather": state.selected_weather,
                "health": health,
                "growth": min(1.0, stats.growth_earned / max(1, self.config.value("daily_growth_cap", 220))),
                "plants": [
                    {
                        "name": p.name,
                        "species": p.species,
                        "stage": p.growth_stage,
                        "vitality": p.vitality,
                        "rare_variant": p.rare_variant,
                    }
                    for p in state.plants
                ],
            }
        )

        self.quest_list.clear()
        for quest in state.daily_quests:
            marker = "✅" if quest.completed else "🌱"
            self.quest_list.addItem(f"{marker} {quest.description}  {quest.progress}/{quest.target}")
        if self.quest_list.count() == 0:
            self.quest_list.addItem("No quests yet today. Review a card to generate progress.")

        self.achievement_list.clear()
        for ach in state.achievements.values():
            marker = "🏅" if ach.unlocked else "🔒"
            self.achievement_list.addItem(f"{marker} {ach.name}")
        if self.achievement_list.count() == 0:
            self.achievement_list.addItem("Achievements will appear as you keep studying.")

        self.inventory_list.clear()
        for category, items in state.inventory.items():
            if items:
                self.inventory_list.addItem(f"{category}: {', '.join(items[:3])}")
        if self.inventory_list.count() == 0:
            self.inventory_list.addItem("No active boosts yet.")

        self.exam_date_input.setText(state.exam_mode.exam_date or "")
        self._refresh_roster_cards()

    def show_retrospective_feedback(self, review_count: int, growth_gain: int) -> None:
        if review_count <= 0:
            self.retrospective_note.setText("")
            return
        self.retrospective_note.setText(f"✨ Catch-up applied from synced reviews: +{growth_gain} growth from {review_count} reviews.")

    def _refresh_roster_cards(self) -> None:
        while self.roster_grid.count():
            item = self.roster_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        state = self.storage.state
        self.roster_title.setText("Garden Regions" if state.garden_mode == "unified" else "Deck Mapped Plants")
        for idx, plant in enumerate(state.plants):
            card = QFrame()
            card.setProperty("card", True)
            effect = QGraphicsDropShadowEffect(card)
            effect.setBlurRadius(16)
            effect.setColor(QColor(0, 0, 0, 120))
            effect.setOffset(0, 4)
            card.setGraphicsEffect(effect)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            l = QVBoxLayout(card)
            deck_label = "All-decks contributor"
            for deck_id, plant_id in state.deck_plant_map.items():
                if plant_id == plant.plant_id:
                    deck_label = f"Deck #{deck_id}"
                    break
            title = QLabel(f"{plant.name} • {plant.species.title()}")
            title.setStyleSheet("font-weight:700;")
            stage = QLabel(f"Stage: {plant.growth_stage.title()} {'✨' if plant.rare_variant else ''}")
            stage.setProperty("muted", True)
            vit = QProgressBar()
            vit.setMaximum(100)
            vit.setValue(int(plant.vitality * 100))
            vit.setFormat("Vitality %p%")
            growth = QLabel(f"Growth source: {plant.personality} • GP {plant.growth_points}")
            growth.setProperty("muted", True)
            map_info = QLabel(deck_label)
            map_info.setProperty("muted", True)
            l.addWidget(title)
            l.addWidget(stage)
            l.addWidget(vit)
            l.addWidget(growth)
            l.addWidget(map_info)
            self.roster_grid.addWidget(card, idx // 3, idx % 3)

    def _open_settings(self) -> None:
        if self.settings_dialog is None:
            self.settings_dialog = GardenSettingsDialog(self, self.engine, self.config)
        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def _start_focus(self) -> None:
        ok, msg = self.engine.start_focus_session(int(self.focus_duration.currentData()))
        QMessageBox.information(self, "Anki Garden", msg)
        if ok:
            self.refresh_all()

    def _complete_focus(self) -> None:
        _ok, msg = self.engine.complete_focus_session()
        QMessageBox.information(self, "Anki Garden", msg)
        self.refresh_all()

    def _cancel_focus(self) -> None:
        self.engine.cancel_focus_session()
        self.refresh_all()

    def _set_exam_date(self) -> None:
        value = self.exam_date_input.text().strip()
        deck_ids: list[int] = []
        try:
            for deck in mw.col.decks.all_names_and_ids()[:3]:
                deck_ids.append(deck.id)
        except Exception:
            pass
        self.engine.configure_exam_mode(True, value, deck_ids)
        self.refresh_all()

    def _disable_exam(self) -> None:
        self.engine.configure_exam_mode(False, None, [])
        self.refresh_all()
