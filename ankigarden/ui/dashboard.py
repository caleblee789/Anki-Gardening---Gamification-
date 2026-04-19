from __future__ import annotations

from datetime import date
from typing import Any

from aqt import mw
from aqt.qt import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QInputDialog,
    QPixmap,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class GardenDashboard(QDialog):
    def __init__(self, mw_window: Any, engine: Any, storage: Any, config: Any) -> None:
        super().__init__(mw_window)
        self.engine = engine
        self.storage = storage
        self.config = config
        self.setWindowTitle("Anki Garden")
        self.setMinimumSize(1200, 780)
        self.setStyleSheet("QGroupBox { font-weight: 600; }")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.bg_label = QLabel()
        self.bg_label.setFrameShape(QFrame.Shape.Box)
        self.bg_label.setMinimumHeight(230)
        self.bg_label.setScaledContents(True)

        self.streak_label = QLabel()
        self.daily_label = QLabel()
        self.mode_label = QLabel()
        self.event_label = QLabel()
        self.health_label = QLabel()
        self.exam_label = QLabel()
        self.growth_bar = QProgressBar()
        self.growth_bar.setFormat("Daily Growth %v/%m")

        header = QHBoxLayout()
        header.addWidget(self.streak_label)
        header.addStretch(1)
        header.addWidget(self.daily_label)

        layout.addWidget(self.bg_label)
        layout.addLayout(header)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.health_label)
        layout.addWidget(self.exam_label)
        layout.addWidget(self.event_label)
        layout.addWidget(self.growth_bar)

        splitter = QSplitter()
        splitter.addWidget(self._build_plant_panel())
        splitter.addWidget(self._build_side_panel())
        splitter.setSizes([740, 430])
        layout.addWidget(splitter)

    def _build_plant_panel(self) -> QWidget:
        box = QGroupBox("Garden Slots")
        outer = QVBoxLayout(box)

        controls = QHBoxLayout()
        self.focus_combo = QComboBox()
        self.focus_combo.currentIndexChanged.connect(self._on_focus_change)
        controls.addWidget(QLabel("Focus Plant"))
        controls.addWidget(self.focus_combo)

        self.deck_combo = QComboBox()
        self.plant_combo = QComboBox()
        map_button = QPushButton("Map Deck → Plant")
        map_button.clicked.connect(self._map_deck_to_plant)
        controls.addWidget(self.deck_combo)
        controls.addWidget(self.plant_combo)
        controls.addWidget(map_button)
        outer.addLayout(controls)

        self.slot_grid = QGridLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid_wrap = QVBoxLayout(content)
        grid_wrap.addLayout(self.slot_grid)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return box

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.quests = QListWidget()
        self.achievements = QListWidget()
        self.inventory = QListWidget()
        self.shop = QListWidget()
        self.social_list = QListWidget()
        self.timeline = QListWidget()

        shop_btn = QPushButton("Buy Selected Item")
        shop_btn.clicked.connect(self._purchase_selected)
        publish_btn = QPushButton("Publish Garden")
        publish_btn.clicked.connect(self._publish_garden)
        import_btn = QPushButton("Import Shared Garden")
        import_btn.clicked.connect(self._import_shared_garden)
        cloud_push_btn = QPushButton("Cloud Push")
        cloud_push_btn.clicked.connect(self._cloud_push)
        cloud_pull_btn = QPushButton("Cloud Pull")
        cloud_pull_btn.clicked.connect(self._cloud_pull)
        set_name_btn = QPushButton("Set Gardener Name")
        set_name_btn.clicked.connect(self._set_gardener_name)
        export_btn = QPushButton("Export Summary")
        export_btn.clicked.connect(self._export_summary)

        focus_box = QGroupBox("Focus Session")
        focus_layout = QHBoxLayout(focus_box)
        self.focus_duration = QComboBox()
        for minutes in self.config.nested("focus_mode", "durations", default=[25, 45, 60]):
            self.focus_duration.addItem(f"{minutes} min", int(minutes))
        start_focus = QPushButton("Start")
        start_focus.clicked.connect(self._start_focus)
        complete_focus = QPushButton("Complete")
        complete_focus.clicked.connect(self._complete_focus)
        cancel_focus = QPushButton("Cancel")
        cancel_focus.clicked.connect(self._cancel_focus)
        focus_layout.addWidget(self.focus_duration)
        focus_layout.addWidget(start_focus)
        focus_layout.addWidget(complete_focus)
        focus_layout.addWidget(cancel_focus)

        exam_box = QGroupBox("Exam Mode")
        exam_layout = QFormLayout(exam_box)
        self.exam_date_input = QLineEdit()
        exam_set = QPushButton("Set Exam Date")
        exam_set.clicked.connect(self._set_exam_date)
        exam_off = QPushButton("Disable")
        exam_off.clicked.connect(self._disable_exam)
        exam_layout.addRow("Date (YYYY-MM-DD)", self.exam_date_input)
        exam_layout.addRow(exam_set, exam_off)

        journal_box = QGroupBox("Reflection Journal")
        journal_layout = QFormLayout(journal_box)
        self.journal_day = QLineEdit(date.today().isoformat())
        self.journal_note = QTextEdit()
        self.journal_note.setPlaceholderText("Optional: one sentence about today's study session.")
        save_note = QPushButton("Save Note")
        save_note.clicked.connect(self._save_journal)
        journal_layout.addRow("Day", self.journal_day)
        journal_layout.addRow("Note", self.journal_note)
        journal_layout.addRow(save_note)

        layout.addWidget(QLabel("Daily Quests"))
        layout.addWidget(self.quests)
        layout.addWidget(QLabel("Achievements"))
        layout.addWidget(self.achievements)
        layout.addWidget(focus_box)
        layout.addWidget(exam_box)
        layout.addWidget(QLabel("Inventory"))
        layout.addWidget(self.inventory)
        layout.addWidget(QLabel("Garden Shop"))
        layout.addWidget(self.shop)
        layout.addWidget(shop_btn)
        layout.addWidget(QLabel("Snapshots / Timeline"))
        layout.addWidget(self.timeline)
        layout.addWidget(QLabel("Social / Shared Gardens"))
        layout.addWidget(self.social_list)
        layout.addWidget(publish_btn)
        layout.addWidget(import_btn)
        layout.addWidget(set_name_btn)
        layout.addWidget(cloud_push_btn)
        layout.addWidget(cloud_pull_btn)
        layout.addWidget(export_btn)
        layout.addWidget(journal_box)
        return panel

    def refresh_all(self) -> None:
        state = self.storage.state
        stats = state.daily_stats
        health = self.engine.garden_health_index()

        self.streak_label.setText(f"Streak: {state.streak_days} days • Currency: {state.currency} {self.config.value('currency_name')}")
        self.daily_label.setText(f"Today: {stats.reviewed} cards • Accuracy {int(stats.accuracy * 100)}%")
        self.mode_label.setText("Recovery mode active" if state.recovery_mode else "Steady growth mode")
        burnout = "⚠ burnout risk" if self.engine.burnout_risk() else "balanced load"
        self.health_label.setText(f"Garden health index: {health:.2f} • {burnout}")
        countdown = self.engine.exam_countdown_days()
        self.exam_label.setText("Exam mode: off" if countdown is None else f"Exam mode active • {countdown} days remaining")
        self.event_label.setText(f"Weekly Event: {self.engine.get_weekly_event_summary()}")
        self.growth_bar.setMaximum(self.config.value("daily_growth_cap", 220))
        self.growth_bar.setValue(stats.growth_earned)

        bg = self.engine.resolve_background_image()
        if bg:
            self.bg_label.setPixmap(QPixmap(bg))
        else:
            self.bg_label.setText("Connect an image API key or use Wikimedia source for live visuals.")

        self._refresh_slot_cards()
        self._refresh_quest_list()
        self._refresh_achievements()
        self._refresh_inventory_and_shop()
        self._refresh_social()
        self._refresh_timeline()
        self._refresh_focus_and_deck_controls()

        today = date.today().isoformat()
        self.journal_day.setText(today)
        self.journal_note.setPlainText(state.journal.get(today, ""))
        self.exam_date_input.setText(state.exam_mode.exam_date or "")

    def _refresh_slot_cards(self) -> None:
        state = self.storage.state
        while self.slot_grid.count():
            item = self.slot_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        plants_by_slot = {p.slot_index: p for p in state.plants}
        for slot in range(state.unlocked_slots):
            plant = plants_by_slot.get(slot)
            card = self._plant_card(plant) if plant else self._empty_slot_card(slot)
            self.slot_grid.addWidget(card, slot // 2, slot % 2)

    def _refresh_quest_list(self) -> None:
        self.quests.clear()
        for quest in self.storage.state.daily_quests:
            marker = "✅" if quest.completed else "•"
            self.quests.addItem(QListWidgetItem(f"{marker} {quest.description} ({quest.progress}/{quest.target})"))

    def _refresh_achievements(self) -> None:
        self.achievements.clear()
        for ach in self.storage.state.achievements.values():
            marker = "🏅" if ach.unlocked else "○"
            self.achievements.addItem(QListWidgetItem(f"{marker} {ach.name} — {ach.description}"))

    def _refresh_inventory_and_shop(self) -> None:
        state = self.storage.state
        self.inventory.clear()
        for category, items in state.inventory.items():
            for item in items:
                self.inventory.addItem(f"{category}: {item}")

        self.shop.clear()
        for key, cost in sorted(self.engine.SHOP_ITEMS.items()):
            purchased = " (owned)" if key in state.purchased_items else ""
            effective = self.engine.get_shop_price(key)
            self.shop.addItem(f"{key} — {effective} (base {cost}){purchased}")

    def _refresh_social(self) -> None:
        state = self.storage.state
        self.social_list.clear()
        self.social_list.addItem(f"You: {state.gardener_name} ({state.share_code})")
        self.social_list.addItem(f"Cloud sync: {state.cloud_last_sync or 'never'}")
        for code, shared in sorted(state.shared_gardens.items()):
            summary = f"{shared.get('gardener_name', 'Unknown')} • streak {shared.get('streak_days', 0)} • code {code}"
            self.social_list.addItem(summary)

    def _refresh_timeline(self) -> None:
        self.timeline.clear()
        for snap in self.storage.state.snapshots[-20:]:
            self.timeline.addItem(f"{snap.day} • health {snap.health_index:.2f} • streak {snap.streak_days}")
        for summary in self.storage.state.recent_summaries[-5:]:
            self.timeline.addItem(f"{summary.day} • {summary.summary}")

    def _refresh_focus_and_deck_controls(self) -> None:
        state = self.storage.state
        self.focus_combo.blockSignals(True)
        self.focus_combo.clear()
        self.focus_combo.addItem("None", None)
        for plant in state.plants:
            self.focus_combo.addItem(f"{plant.name} ({plant.personality})", plant.plant_id)
        selected_idx = 0
        if state.focus_plant_id:
            for i in range(self.focus_combo.count()):
                if self.focus_combo.itemData(i) == state.focus_plant_id:
                    selected_idx = i
                    break
        self.focus_combo.setCurrentIndex(selected_idx)
        self.focus_combo.blockSignals(False)

        self.plant_combo.clear()
        for plant in state.plants:
            self.plant_combo.addItem(plant.name, plant.plant_id)

        self.deck_combo.clear()
        self.deck_combo.addItem("Choose deck", None)
        try:
            for deck in mw.col.decks.all_names_and_ids():
                self.deck_combo.addItem(deck.name, deck.id)
        except Exception:
            pass

    def _plant_card(self, plant: Any) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        img_label = QLabel()
        img_label.setMinimumHeight(140)
        img_label.setScaledContents(True)
        image = self.engine.resolve_plant_image(plant.species, plant.growth_stage, plant.rare_variant)
        if image:
            img_label.setPixmap(QPixmap(image))
        else:
            img_label.setText(f"{plant.species} ({plant.growth_stage})\nNo cached image yet")

        vitality = QProgressBar()
        vitality.setMaximum(100)
        vitality.setValue(int(plant.vitality * 100))
        vitality.setFormat("Vitality %p%")

        layout.addWidget(QLabel(f"{plant.name} • {plant.growth_stage.title()} • {plant.personality}"))
        layout.addWidget(img_label)
        layout.addWidget(QLabel(f"Growth: {plant.growth_points}"))
        layout.addWidget(vitality)
        return frame

    def _empty_slot_card(self, slot_idx: int) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel(f"Slot {slot_idx + 1} is empty"))
        species = QComboBox()
        species.addItems(["bonsai", "rose", "cactus", "orchid", "moonflower", "sunbloom", "ivy", "fern"])
        add_btn = QPushButton("Plant Here")

        def add() -> None:
            ok = self.engine.add_plant_to_slot(species.currentText(), slot_idx)
            if not ok:
                QMessageBox.information(self, "Anki Garden", "Unable to plant in this slot.")
            self.refresh_all()

        add_btn.clicked.connect(add)
        layout.addWidget(species)
        layout.addWidget(add_btn)
        return frame

    def _on_focus_change(self) -> None:
        self.engine.assign_focus_plant(self.focus_combo.currentData())

    def _map_deck_to_plant(self) -> None:
        deck_id = self.deck_combo.currentData()
        plant_id = self.plant_combo.currentData()
        if deck_id and plant_id:
            self.engine.assign_deck_to_plant(int(deck_id), str(plant_id))
            QMessageBox.information(self, "Anki Garden", "Deck mapping saved.")

    def _purchase_selected(self) -> None:
        item = self.shop.currentItem()
        if not item:
            return
        key = item.text().split(" — ")[0]
        ok, msg = self.engine.purchase_item(key)
        QMessageBox.information(self, "Anki Garden", msg)
        if ok:
            self.refresh_all()

    def _save_journal(self) -> None:
        self.engine.set_journal_note(self.journal_day.text(), self.journal_note.toPlainText())

    def _publish_garden(self) -> None:
        code = self.engine.publish_shared_garden()
        QMessageBox.information(self, "Anki Garden", f"Garden published with share code: {code}")
        self.refresh_all()

    def _import_shared_garden(self) -> None:
        code, ok = QInputDialog.getText(self, "Import Shared Garden", "Enter share code:")
        if not ok:
            return
        success, message = self.engine.import_shared_garden(code)
        QMessageBox.information(self, "Anki Garden", message)
        if success:
            self.refresh_all()

    def _cloud_push(self) -> None:
        success, message = self.engine.cloud_push()
        QMessageBox.information(self, "Anki Garden", message)
        if success:
            self.refresh_all()

    def _cloud_pull(self) -> None:
        success, message = self.engine.cloud_pull()
        QMessageBox.information(self, "Anki Garden", message)
        if success:
            self.refresh_all()

    def _set_gardener_name(self) -> None:
        name, ok = QInputDialog.getText(self, "Gardener Name", "Choose your display name:")
        if not ok:
            return
        self.engine.set_gardener_name(name)
        self.refresh_all()

    def _start_focus(self) -> None:
        ok, msg = self.engine.start_focus_session(int(self.focus_duration.currentData()))
        QMessageBox.information(self, "Anki Garden", msg)
        if ok:
            self.refresh_all()

    def _complete_focus(self) -> None:
        ok, msg = self.engine.complete_focus_session()
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

    def _export_summary(self) -> None:
        QMessageBox.information(self, "Anki Garden", self.engine.export_progress_summary())

