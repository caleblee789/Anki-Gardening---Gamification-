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
        self.setMinimumSize(1080, 760)
        self.setStyleSheet("QGroupBox { font-weight: 600; }")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.bg_label = QLabel()
        self.bg_label.setFrameShape(QFrame.Shape.Box)
        self.bg_label.setMinimumHeight(220)
        self.bg_label.setScaledContents(True)

        self.streak_label = QLabel()
        self.daily_label = QLabel()
        self.mode_label = QLabel()
        self.growth_bar = QProgressBar()
        self.growth_bar.setFormat("Daily Growth %v/%m")

        header = QHBoxLayout()
        header.addWidget(self.streak_label)
        header.addStretch(1)
        header.addWidget(self.daily_label)

        layout.addWidget(self.bg_label)
        layout.addLayout(header)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.growth_bar)

        splitter = QSplitter()
        splitter.addWidget(self._build_plant_panel())
        splitter.addWidget(self._build_side_panel())
        splitter.setSizes([700, 360])
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

        shop_btn = QPushButton("Buy Selected Item")
        shop_btn.clicked.connect(self._purchase_selected)

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
        layout.addWidget(QLabel("Inventory"))
        layout.addWidget(self.inventory)
        layout.addWidget(QLabel("Garden Shop"))
        layout.addWidget(self.shop)
        layout.addWidget(shop_btn)
        layout.addWidget(journal_box)
        return panel

    def refresh_all(self) -> None:
        state = self.storage.state
        stats = state.daily_stats

        self.streak_label.setText(
            f"Streak: {state.streak_days} days  •  Currency: {state.currency} {self.config.value('currency_name')}"
        )
        self.daily_label.setText(f"Today: {stats.reviewed} cards • Accuracy {int(stats.accuracy * 100)}%")
        mode = "Recovery mode active: resume a few sessions to revive plant vitality." if state.recovery_mode else "Garden mode: steady growth focus"
        self.mode_label.setText(mode)
        self.growth_bar.setMaximum(self.config.value("daily_growth_cap", 220))
        self.growth_bar.setValue(stats.growth_earned)

        bg = self.engine.resolve_background_image()
        if bg:
            self.bg_label.setPixmap(QPixmap(bg))
        else:
            self.bg_label.setText("Connect an image API key to enable live garden visuals.")

        self._refresh_slot_cards()
        self._refresh_quest_list()
        self._refresh_achievements()
        self._refresh_inventory_and_shop()
        self._refresh_focus_and_deck_controls()

        today = date.today().isoformat()
        self.journal_day.setText(today)
        self.journal_note.setPlainText(state.journal.get(today, ""))

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
            if plant:
                card = self._plant_card(plant)
            else:
                card = self._empty_slot_card(slot)
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
            self.shop.addItem(f"{key} — {cost}{purchased}")

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
        species.addItems(["bonsai", "rose", "cactus", "orchid", "moonflower", "sunbloom"])
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
