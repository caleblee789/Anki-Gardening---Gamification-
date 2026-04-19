from __future__ import annotations

from datetime import date
from typing import Any

from aqt.qt import (
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
    QPixmap,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class GardenDashboard(QDialog):
    def __init__(self, mw: Any, engine: Any, storage: Any, config: Any) -> None:
        super().__init__(mw)
        self.engine = engine
        self.storage = storage
        self.config = config
        self.setWindowTitle("Anki Garden")
        self.setMinimumSize(980, 720)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.bg_label = QLabel()
        self.bg_label.setFrameShape(QFrame.Shape.Box)
        self.bg_label.setMinimumHeight(220)
        self.bg_label.setScaledContents(True)

        self.streak_label = QLabel()
        self.daily_label = QLabel()
        self.growth_bar = QProgressBar()
        self.growth_bar.setFormat("Daily Growth %v/%m")

        header = QHBoxLayout()
        header.addWidget(self.streak_label)
        header.addStretch(1)
        header.addWidget(self.daily_label)

        layout.addWidget(self.bg_label)
        layout.addLayout(header)
        layout.addWidget(self.growth_bar)

        body = QHBoxLayout()
        body.addWidget(self._build_plant_panel(), stretch=3)
        body.addWidget(self._build_side_panel(), stretch=2)
        layout.addLayout(body)

    def _build_plant_panel(self) -> QWidget:
        box = QGroupBox("Garden Slots")
        outer = QVBoxLayout(box)

        self.slot_grid = QGridLayout()
        outer.addLayout(self.slot_grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.slot_grid_container = QVBoxLayout(content)
        self.slot_grid_container.addLayout(self.slot_grid)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return box

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.quests = QListWidget()
        self.achievements = QListWidget()
        self.inventory = QListWidget()
        self.inventory.addItems([
            "Pots: Ceramic Minimal",
            "Decoration: Stone Lantern",
            "Weather: Fireflies",
        ])

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
        layout.addWidget(QLabel("Unlockables"))
        layout.addWidget(self.inventory)
        layout.addWidget(journal_box)
        return panel

    def refresh_all(self) -> None:
        state = self.storage.state
        stats = state.daily_stats
        self.streak_label.setText(f"Streak: {state.streak_days} days   •   Currency: {state.currency} {self.config.value('currency_name')}")
        self.daily_label.setText(f"Today: {stats.reviewed} cards • Accuracy {int(stats.accuracy * 100)}%")
        self.growth_bar.setMaximum(self.config.value("daily_growth_cap", 220))
        self.growth_bar.setValue(stats.growth_earned)

        bg = self.engine.resolve_background_image()
        if bg:
            self.bg_label.setPixmap(QPixmap(bg))
        else:
            self.bg_label.setText("Connect an image API key to enable live garden visuals.")

        while self.slot_grid.count():
            item = self.slot_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for idx, plant in enumerate(state.plants[: state.unlocked_slots]):
            card = self._plant_card(plant)
            self.slot_grid.addWidget(card, idx // 2, idx % 2)

        self.quests.clear()
        for quest in state.daily_quests:
            marker = "✅" if quest.completed else "•"
            self.quests.addItem(QListWidgetItem(f"{marker} {quest.description} ({quest.progress}/{quest.target})"))

        self.achievements.clear()
        for ach in state.achievements.values():
            marker = "🏅" if ach.unlocked else "○"
            self.achievements.addItem(QListWidgetItem(f"{marker} {ach.name} — {ach.description}"))

        today = date.today().isoformat()
        self.journal_day.setText(today)
        self.journal_note.setPlainText(state.journal.get(today, ""))

    def _plant_card(self, plant: Any) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(frame)

        img_label = QLabel()
        img_label.setMinimumHeight(130)
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

        layout.addWidget(QLabel(f"{plant.name} • {plant.growth_stage.title()}"))
        layout.addWidget(img_label)
        layout.addWidget(QLabel(f"Growth: {plant.growth_points}"))
        layout.addWidget(vitality)
        return frame

    def _save_journal(self) -> None:
        self.engine.set_journal_note(self.journal_day.text(), self.journal_note.toPlainText())
