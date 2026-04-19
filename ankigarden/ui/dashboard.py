from __future__ import annotations

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
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Qt,
    QColor,
    QSizePolicy,
)
from .garden_studio import GardenStudioWidget
from .scene import GardenSceneWidget


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

        behavior = GardenStudioWidget(config, on_reroll=self._reroll_asset_slot)

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

    def _reroll_asset_slot(self, slot: str) -> None:
        try:
            if slot == "background":
                self.engine.resolve_background_image()
            elif slot == "weather":
                self.engine.resolve_weather_overlay()
            else:
                first = self.engine.state.plants[0] if self.engine.state.plants else None
                if first:
                    self.engine.resolve_plant_image(first.species, first.growth_stage, first.rare_variant)
        except Exception:
            pass


class GardenDashboard(QDialog):
    ROOT_MARGINS = (18, 18, 18, 18)
    ROOT_SPACING = 12
    CARD_SPACING = 10
    CARD_PADDING = (12, 12, 12, 12)
    CARD_BORDER_RADIUS = 14
    CHIP_BORDER_RADIUS = 12
    CHIP_PADDING = (5, 10)
    CHIP_SPACING = 8
    MID_ROW_SPACING = 12
    ROSTER_GRID_SPACING = 12
    CARD_BG = "#18252e"
    CARD_BORDER = "#2f4652"
    APP_BG = "#101820"
    TEXT_PRIMARY = "#e6f0ea"
    TEXT_MUTED = "#b2c4c8"
    CHIP_BG = "#213847"

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
            f"""
            QDialog {{ background: {self.APP_BG}; color: {self.TEXT_PRIMARY}; }}
            QFrame[card='true'] {{ background: {self.CARD_BG}; border: 1px solid {self.CARD_BORDER}; border-radius: {self.CARD_BORDER_RADIUS}px; }}
            QLabel[typography='title'] {{ font-size: 20px; font-weight: 800; letter-spacing: 0.3px; }}
            QLabel[typography='section-title'] {{ font-size: 15px; font-weight: 700; letter-spacing: 0.2px; }}
            QLabel[typography='muted-body'] {{ font-size: 13px; color: {self.TEXT_MUTED}; }}
            QLabel[typography='status-chip'] {{ font-size: 12px; font-weight: 600; letter-spacing: 0.1px; }}
            QLabel[chip='true'] {{ padding: {self.CHIP_PADDING[0]}px {self.CHIP_PADDING[1]}px; background:{self.CHIP_BG}; border-radius:{self.CHIP_BORDER_RADIUS}px; }}
            QPushButton {{ background: #264456; border: 1px solid #3d6174; border-radius: 10px; padding: 7px 12px; font-weight: 600; }}
            QPushButton:hover {{ background: #2f5468; }}
            QProgressBar {{ border-radius: 7px; border: 1px solid {self.CARD_BORDER}; background: #132029; }}
            QProgressBar::chunk {{ background: #56ba7f; border-radius: 6px; }}
            QListWidget {{ background: #12202a; border-radius: 10px; border: 1px solid #2a404d; padding: 4px; }}
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(*self.ROOT_MARGINS)
        root.setSpacing(self.ROOT_SPACING)

        top = self._card_frame()
        t_layout = QHBoxLayout(top)
        t_layout.setContentsMargins(*self.CARD_PADDING)
        t_layout.setSpacing(self.CHIP_SPACING)
        self.title_label = QLabel("🌿 Anki Garden")
        self._apply_typography(self.title_label, "title")
        self.streak_chip = QLabel()
        self.progress_chip = QLabel()
        self.health_chip = QLabel()
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        t_layout.addWidget(self.title_label)
        t_layout.addStretch(1)
        for chip in (self.streak_chip, self.progress_chip, self.health_chip):
            chip.setProperty("chip", True)
            self._apply_typography(chip, "status-chip")
            t_layout.addWidget(chip)
        t_layout.addWidget(self.settings_btn)
        root.addWidget(top)

        hero_card = self._card_frame()
        h_layout = QVBoxLayout(hero_card)
        h_layout.setContentsMargins(*self.CARD_PADDING)
        h_layout.setSpacing(self.CARD_SPACING)
        self.scene = GardenSceneWidget()
        self.hero_summary = QLabel()
        self.hero_summary.setWordWrap(True)
        self._apply_typography(self.hero_summary, "muted-body")
        self.hero_summary.setStyleSheet("line-height: 1.35;")
        self.hero_growth = QProgressBar()
        self.hero_growth.setMaximum(100)
        self.hero_growth.setFormat("Daily growth %p%")
        self.hero_growth.setStyleSheet(
            "QProgressBar{height:18px;font-weight:700;} QProgressBar::chunk{background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5fd484, stop:1 #d7ff8f);}"
        )
        self.retrospective_note = QLabel("")
        self._apply_typography(self.retrospective_note, "muted-body")
        self.retrospective_note.setStyleSheet("color:#9ef3b0; font-size:13px;")
        h_layout.addWidget(self.scene)
        h_layout.addWidget(self.hero_summary)
        h_layout.addWidget(self.hero_growth)
        h_layout.addWidget(self.retrospective_note)
        root.addWidget(hero_card, 2)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(self.MID_ROW_SPACING)
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

        lower = self._card_frame()
        l_layout = QVBoxLayout(lower)
        l_layout.setContentsMargins(*self.CARD_PADDING)
        l_layout.setSpacing(self.CARD_SPACING)
        self.roster_title = QLabel("Garden Roster")
        self._apply_typography(self.roster_title, "section-title")
        self.roster_grid = QGridLayout()
        self.roster_grid.setSpacing(self.ROSTER_GRID_SPACING)
        roster_wrap = QWidget()
        roster_wrap.setLayout(self.roster_grid)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(roster_wrap)
        l_layout.addWidget(self.roster_title)
        l_layout.addWidget(scroll)
        root.addWidget(lower, 2)

    def _card_frame(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("card", True)
        return frame

    def _apply_typography(self, label: QLabel, level: str) -> None:
        label.setProperty("typography", level)

    def _simple_card(self, title: str, body: QWidget) -> QFrame:
        f = self._card_frame()
        l = QVBoxLayout(f)
        l.setContentsMargins(*self.CARD_PADDING)
        l.setSpacing(self.CARD_SPACING)
        label = QLabel(title)
        self._apply_typography(label, "section-title")
        l.addWidget(label)
        l.addWidget(body)
        return f

    def _focus_card(self) -> QFrame:
        card = self._card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(*self.CARD_PADDING)
        layout.setSpacing(self.CARD_SPACING)
        heading = QLabel("Focus / Exam")
        self._apply_typography(heading, "section-title")
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
            self._apply_typography(title, "section-title")
            stage = QLabel(f"Stage: {plant.growth_stage.title()} {'✨' if plant.rare_variant else ''}")
            self._apply_typography(stage, "muted-body")
            vit = QProgressBar()
            vit.setMaximum(100)
            vit.setValue(int(plant.vitality * 100))
            vit.setFormat("Vitality %p%")
            growth = QLabel(f"Growth source: {plant.personality} • GP {plant.growth_points}")
            self._apply_typography(growth, "muted-body")
            map_info = QLabel(deck_label)
            self._apply_typography(map_info, "muted-body")
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
