from __future__ import annotations

from typing import Optional

from aqt import mw
from aqt.gui_hooks import reviewer_did_answer_card, reviewer_did_show_question
from aqt.qt import QAction, QPushButton
from aqt.utils import showInfo

from .config import ConfigManager
from .game import GardenGameEngine
from .hooks.reviewer import ReviewerHookHandler
from .storage import GardenStorage
from .ui.dashboard import GardenDashboard


class AnkiGardenApp:
    def __init__(self) -> None:
        self.config = ConfigManager(mw)
        self.storage = GardenStorage(mw, self.config)
        self.engine = GardenGameEngine(self.config, self.storage)
        self.reviewer_hooks = ReviewerHookHandler(self.engine, self.storage)
        self.dashboard: Optional[GardenDashboard] = None
        self._reviewer_button: Optional[QPushButton] = None

    def setup(self) -> None:
        self._setup_menu()
        if self.config.value("show_toolbar_button", True):
            self._setup_toolbar()
        self._setup_reviewer_button()
        reviewer_did_answer_card.append(self.reviewer_hooks.on_answer)
        self.engine.rollover_if_needed()

    def _setup_menu(self) -> None:
        action = QAction("Anki Garden", mw)
        action.triggered.connect(self.open_dashboard)
        mw.form.menuTools.addAction(action)

    def _setup_toolbar(self) -> None:
        action = QAction("Garden", mw)
        action.triggered.connect(self.open_dashboard)
        mw.form.toolbar.addAction(action)

    def _setup_reviewer_button(self) -> None:
        if not self.config.value("show_reviewer_button"):
            return

        def add_button() -> None:
            reviewer = mw.reviewer
            if not reviewer or not reviewer.bottom:
                return
            if self._reviewer_button and self._reviewer_button.parent() is reviewer.bottom.web:
                return
            button = QPushButton("🌱 Garden", reviewer.bottom.web)
            button.clicked.connect(self.open_dashboard)
            button.setToolTip("Open Anki Garden")
            reviewer.bottom.hlayout.insertWidget(0, button)
            self._reviewer_button = button

        try:
            reviewer_did_show_question.append(lambda _card: add_button())
        except Exception:
            showInfo("Anki Garden: Unable to add reviewer button.")

    def open_dashboard(self) -> None:
        self.engine.rollover_if_needed()
        if self.dashboard is None:
            self.dashboard = GardenDashboard(mw, self.engine, self.storage, self.config)
        self.dashboard.refresh_all()
        self.dashboard.show()
        self.dashboard.raise_()


_app: Optional[AnkiGardenApp] = None


def setup_addon() -> None:
    global _app
    if mw is None:
        return
    _app = AnkiGardenApp()
    _app.setup()
