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
    QFontMetrics,
    QListWidgetItem,
    QSizePolicy,
)
from .garden_studio import GardenStudioWidget
from .scene import GardenSceneWidget

UI_TEXT = {
    "settings_window_title": "Anki Garden Settings",
    "mode_unified": "Unified All Decks",
    "mode_deck": "Deck-by-Deck",
    "save_mode": "Save Garden Mode",
    "growth_mode_label": "Garden growth mode",
    "select_deck": "Select a deck",
    "assign_deck": "Assign Deck to Plant",
    "advanced_hint": "Use advanced and debug controls here to keep the dashboard focused.",
    "tab_general": "General",
    "tab_mapping": "Deck Mapping",
    "tab_behavior": "Visuals & Behavior",
    "tab_advanced": "Advanced",
    "app_title": "Anki Garden",
    "title_banner": "🌿 Anki Garden",
    "open_settings": "⚙ Open Settings",
    "hero_growth_format": "Daily growth %p%",
    "quest_progress_title": "Quest Progress",
    "achievement_progress_title": "Achievement Progress",
    "focus_exam_title": "Focus and Exam Controls",
    "inventory_boosts_title": "Inventory Boosts",
    "garden_roster_title": "Garden Roster",
    "start_focus": "Start Focus Session",
    "complete_focus": "Complete Focus Session",
    "cancel_focus": "Cancel Focus Session",
    "exam_placeholder": "YYYY-MM-DD (interpreted in your Anki local date)",
    "exam_tooltip": "Enter an exam date like 2026-05-18. The add-on interprets this as your local Anki date and uses it for exam-mode pacing.",
    "set_exam": "Set Exam Date",
    "disable_exam": "Turn Off Exam Mode",
    "garden_mode_updated": "Garden mode updated.",
    "deck_mapping_updated": "Deck mapping updated.",
    "deck_mapping_missing_selection": "Pick both a deck and a plant before assigning a mapping.",
    "deck_mapping_unavailable": "Deck mapping is unavailable right now because deck data could not be loaded.",
    "deck_load_unavailable_option": "Unable to load decks (open a collection and retry)",
    "no_quests": "No quest progress yet today. Review a card to start progress.",
    "no_achievements": "Achievement progress will appear as you keep studying.",
    "no_boosts": "No active inventory boosts yet.",
    "no_roster": "No plants in your roster yet. Add reviews to grow your first companion.",
}


class GardenSettingsDialog(QDialog):
    def __init__(self, parent: QWidget, engine: Any, config: Any) -> None:
        super().__init__(parent)
        self.engine = engine
        self.config = config
        self.setWindowTitle(UI_TEXT["settings_window_title"])
        self.setMinimumSize(760, 520)
        root = QHBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        general = QWidget()
        g_layout = QFormLayout(general)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(UI_TEXT["mode_unified"], "unified")
        self.mode_combo.addItem(UI_TEXT["mode_deck"], "deck-by-deck")
        current_mode = "deck-by-deck" if self.engine.state.garden_mode == "deck-by-deck" else "unified"
        self.mode_combo.setCurrentIndex(1 if current_mode == "deck-by-deck" else 0)
        save_mode = QPushButton(UI_TEXT["save_mode"])
        save_mode.clicked.connect(self._apply_mode)
        g_layout.addRow(UI_TEXT["growth_mode_label"], self.mode_combo)
        g_layout.addRow(save_mode)

        mapping = QWidget()
        m_layout = QVBoxLayout(mapping)
        self.deck_combo = QComboBox()
        self.deck_combo.addItem(UI_TEXT["select_deck"], None)
        self._deck_load_failed = False
        self.plant_combo = QComboBox()
        for plant in self.engine.state.plants:
            self.plant_combo.addItem(plant.name, plant.plant_id)
        try:
            for deck in mw.col.decks.all_names_and_ids():
                self.deck_combo.addItem(deck.name, deck.id)
        except Exception:
            self._deck_load_failed = True
            self.deck_combo.addItem(UI_TEXT["deck_load_unavailable_option"], None)
        map_btn = QPushButton(UI_TEXT["assign_deck"])
        map_btn.clicked.connect(self._map_deck)
        m_layout.addWidget(self.deck_combo)
        m_layout.addWidget(self.plant_combo)
        m_layout.addWidget(map_btn)
        m_layout.addStretch(1)

        behavior = GardenStudioWidget(config, on_reroll=self._reroll_asset_slot)

        advanced = QWidget()
        a_layout = QVBoxLayout(advanced)
        a_layout.addWidget(QLabel(UI_TEXT["advanced_hint"]))
        a_layout.addStretch(1)

        tabs.addTab(general, UI_TEXT["tab_general"])
        tabs.addTab(mapping, UI_TEXT["tab_mapping"])
        tabs.addTab(behavior, UI_TEXT["tab_behavior"])
        tabs.addTab(advanced, UI_TEXT["tab_advanced"])

    def _apply_mode(self) -> None:
        self.engine.set_garden_mode(str(self.mode_combo.currentData()))
        QMessageBox.information(self, UI_TEXT["app_title"], UI_TEXT["garden_mode_updated"])

    def _map_deck(self) -> None:
        deck_id = self.deck_combo.currentData()
        plant_id = self.plant_combo.currentData()
        if self._deck_load_failed:
            QMessageBox.warning(self, UI_TEXT["app_title"], UI_TEXT["deck_mapping_unavailable"])
            return
        if not deck_id or not plant_id:
            QMessageBox.warning(self, UI_TEXT["app_title"], UI_TEXT["deck_mapping_missing_selection"])
            return
        self.engine.assign_deck_to_plant(int(deck_id), str(plant_id))
        QMessageBox.information(self, UI_TEXT["app_title"], UI_TEXT["deck_mapping_updated"])

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
    LIST_ELIDE_WIDTH = 340
    LIST_MAX_LENGTH = 170

    def __init__(self, mw_window: Any, engine: Any, storage: Any, config: Any) -> None:
        super().__init__(mw_window)
        self.engine = engine
        self.storage = storage
        self.config = config
        self.settings_dialog: GardenSettingsDialog | None = None
        self.setWindowTitle(UI_TEXT["app_title"])
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
        self.title_label = QLabel(UI_TEXT["title_banner"])
        self._apply_typography(self.title_label, "title")
        self.streak_chip = QLabel()
        self.progress_chip = QLabel()
        self.health_chip = QLabel()
        self.settings_btn = QPushButton(UI_TEXT["open_settings"])
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
        self.hero_summary.setMinimumHeight(48)
        self.hero_summary.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._apply_typography(self.hero_summary, "muted-body")
        self.hero_summary.setStyleSheet("line-height: 1.35;")
        self.hero_growth = QProgressBar()
        self.hero_growth.setMaximum(100)
        self.hero_growth.setFormat(UI_TEXT["hero_growth_format"])
        self.hero_growth.setStyleSheet(
            "QProgressBar{height:18px;font-weight:700;} QProgressBar::chunk{background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5fd484, stop:1 #d7ff8f);}"
        )
        self.retrospective_note = QLabel("")
        self.retrospective_note.setWordWrap(True)
        self.retrospective_note.setMinimumHeight(24)
        self.retrospective_note.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
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
        self.quest_list.setMinimumHeight(180)
        self.achievement_list = QListWidget()
        self.achievement_list.setAlternatingRowColors(True)
        self.achievement_list.setMinimumHeight(180)
        self.focus_card = self._focus_card()
        self.inventory_list = QListWidget()
        self.inventory_list.setAlternatingRowColors(True)
        self.inventory_list.setMinimumHeight(180)
        mid_row.addWidget(self._simple_card(UI_TEXT["quest_progress_title"], self.quest_list), 1)
        mid_row.addWidget(self._simple_card(UI_TEXT["achievement_progress_title"], self.achievement_list), 1)
        mid_row.addWidget(self.focus_card, 1)
        mid_row.addWidget(self._simple_card(UI_TEXT["inventory_boosts_title"], self.inventory_list), 1)
        root.addLayout(mid_row, 1)

        lower = self._card_frame()
        l_layout = QVBoxLayout(lower)
        l_layout.setContentsMargins(*self.CARD_PADDING)
        l_layout.setSpacing(self.CARD_SPACING)
        self.roster_title = QLabel(UI_TEXT["garden_roster_title"])
        self._apply_typography(self.roster_title, "section-title")
        self.roster_grid = QGridLayout()
        self.roster_grid.setSpacing(self.ROSTER_GRID_SPACING)
        roster_wrap = QWidget()
        roster_wrap.setLayout(self.roster_grid)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(210)
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
        f.setMinimumWidth(240)
        f.setMinimumHeight(240)
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
        card.setMinimumWidth(280)
        card.setMinimumHeight(240)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(*self.CARD_PADDING)
        layout.setSpacing(self.CARD_SPACING)
        heading = QLabel(UI_TEXT["focus_exam_title"])
        self._apply_typography(heading, "section-title")
        layout.addWidget(heading)
        self.focus_duration = QComboBox()
        for minutes in self.config.nested("focus_mode", "durations", default=[25, 45, 60]):
            self.focus_duration.addItem(f"{minutes} min", int(minutes))
        btn_row = QHBoxLayout()
        start_focus = QPushButton(UI_TEXT["start_focus"])
        complete_focus = QPushButton(UI_TEXT["complete_focus"])
        cancel_focus = QPushButton(UI_TEXT["cancel_focus"])
        start_focus.clicked.connect(self._start_focus)
        complete_focus.clicked.connect(self._complete_focus)
        cancel_focus.clicked.connect(self._cancel_focus)
        btn_row.addWidget(start_focus)
        btn_row.addWidget(complete_focus)
        btn_row.addWidget(cancel_focus)
        self.exam_date_input = QLineEdit()
        self.exam_date_input.setPlaceholderText(UI_TEXT["exam_placeholder"])
        self.exam_date_input.setToolTip(UI_TEXT["exam_tooltip"])
        exam_set = QPushButton(UI_TEXT["set_exam"])
        exam_off = QPushButton(UI_TEXT["disable_exam"])
        exam_set.clicked.connect(self._set_exam_date)
        exam_off.clicked.connect(self._disable_exam)
        layout.addWidget(self.focus_duration)
        layout.addLayout(btn_row)
        layout.addWidget(self.exam_date_input)
        layout.addWidget(exam_set)
        layout.addWidget(exam_off)
        layout.addStretch(1)
        return card

    def _add_list_entry(self, widget: QListWidget, text: str, *, empty_state: bool = False) -> None:
        item = QListWidgetItem()
        full_text = text if len(text) <= self.LIST_MAX_LENGTH else f"{text[: self.LIST_MAX_LENGTH - 1]}…"
        max_width = max(140, widget.viewport().width() - 24, self.LIST_ELIDE_WIDTH)
        metrics = QFontMetrics(widget.font())
        display_text = metrics.elidedText(full_text, Qt.TextElideMode.ElideRight, max_width)
        item.setText(display_text)
        if display_text != full_text:
            item.setToolTip(full_text)
        if empty_state:
            item.setFlags(Qt.ItemFlag.NoItemFlags)
        widget.addItem(item)

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
            self._add_list_entry(
                self.quest_list,
                f"{marker} {quest.description}  {quest.progress}/{quest.target}",
            )
        if self.quest_list.count() == 0:
            self._add_list_entry(self.quest_list, UI_TEXT["no_quests"], empty_state=True)

        self.achievement_list.clear()
        for ach in state.achievements.values():
            marker = "🏅" if ach.unlocked else "🔒"
            self._add_list_entry(self.achievement_list, f"{marker} {ach.name}")
        if self.achievement_list.count() == 0:
            self._add_list_entry(self.achievement_list, UI_TEXT["no_achievements"], empty_state=True)

        self.inventory_list.clear()
        for category, items in state.inventory.items():
            if items:
                self._add_list_entry(self.inventory_list, f"{category}: {', '.join(items[:3])}")
        if self.inventory_list.count() == 0:
            self._add_list_entry(self.inventory_list, UI_TEXT["no_boosts"], empty_state=True)

        self.exam_date_input.setText(state.exam_mode.exam_date or "")
        self._refresh_roster_cards()

    def show_retrospective_feedback(self, review_count: int, growth_gain: int) -> None:
        if review_count <= 0:
            self.retrospective_note.setText("")
            return
        self.retrospective_note.setText(
            f"✨ Applied catch-up from synced reviews: +{growth_gain} growth from {review_count} reviews."
        )

    def _refresh_roster_cards(self) -> None:
        while self.roster_grid.count():
            item = self.roster_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        state = self.storage.state
        self.roster_title.setText("Garden Regions" if state.garden_mode == "unified" else "Deck-Mapped Plants")
        if not state.plants:
            empty = QLabel(UI_TEXT["no_roster"])
            self._apply_typography(empty, "muted-body")
            empty.setWordWrap(True)
            self.roster_grid.addWidget(empty, 0, 0, 1, 3)
            return
        for idx, plant in enumerate(state.plants):
            card = QFrame()
            card.setProperty("card", True)
            effect = QGraphicsDropShadowEffect(card)
            effect.setBlurRadius(16)
            effect.setColor(QColor(0, 0, 0, 120))
            effect.setOffset(0, 4)
            card.setGraphicsEffect(effect)
            card.setMinimumSize(220, 160)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            l = QVBoxLayout(card)
            deck_label = "All-Deck Contributor"
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
            growth = QLabel(f"Growth Source: {plant.personality} • GP {plant.growth_points}")
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
        QMessageBox.information(self, UI_TEXT["app_title"], msg)
        if ok:
            self.refresh_all()

    def _complete_focus(self) -> None:
        _ok, msg = self.engine.complete_focus_session()
        QMessageBox.information(self, UI_TEXT["app_title"], msg)
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
