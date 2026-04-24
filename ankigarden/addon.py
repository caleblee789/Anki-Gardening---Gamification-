from __future__ import annotations

import logging
from html import escape
from pathlib import Path
from typing import Optional

from aqt import mw
from aqt.gui_hooks import reviewer_did_answer_card, reviewer_did_show_question
from aqt.qt import QAction, QPushButton
from aqt.utils import showInfo

from .config import ConfigManager
from .display_telemetry import DISPLAY_TELEMETRY
from .game import GardenGameEngine
from .hooks.reviewer import ReviewerHookHandler
from .storage import GardenStorage
from .ui.dashboard import GardenDashboard
from .ui.home_widget import (
    HomeWidgetStateController,
    build_home_widget_success_data,
    render_home_widget,
)

logger = logging.getLogger(__name__)


class AnkiGardenApp:
    def __init__(self) -> None:
        self.config = ConfigManager(mw)
        self.storage = GardenStorage(mw, self.config)
        self.engine = GardenGameEngine(self.config, self.storage)
        self.reviewer_hooks = ReviewerHookHandler(self.engine, self.storage)
        self.dashboard: Optional[GardenDashboard] = None
        self._reviewer_button: Optional[QPushButton] = None
        self._menu_action: Optional[QAction] = None
        self._home_widget_hooked = False
        self._home_widget_controller = HomeWidgetStateController()

    def setup(self) -> None:
        self._setup_menu()
        if self.config.value("show_toolbar_button", True):
            self._setup_toolbar()
        self._setup_reviewer_button()
        self._setup_home_screen_widget()
        reviewer_did_answer_card.append(self.reviewer_hooks.on_answer)
        self._setup_sync_hooks()
        self._apply_retrospective_growth()
        self.engine.rollover_if_needed()

    def _setup_menu(self) -> None:
        if self._menu_action is not None:
            return

        existing_actions = []
        menu_tools = getattr(getattr(mw, "form", None), "menuTools", None)
        if menu_tools is not None and hasattr(menu_tools, "actions"):
            try:
                existing_actions = list(menu_tools.actions())
            except Exception:
                existing_actions = []

        for action in existing_actions:
            if getattr(action, "text", lambda: "")() == "Anki Garden":
                self._menu_action = action
                logger.debug("Anki Garden menu action already registered.")
                return

        action = QAction("Anki Garden", mw)
        action.triggered.connect(self.open_dashboard)
        mw.form.menuTools.addAction(action)
        self._menu_action = action

    def _setup_toolbar(self) -> None:
        action = QAction("Garden", mw)
        action.triggered.connect(self.open_dashboard)
        toolbar = getattr(getattr(mw, "form", None), "toolbar", None)
        if toolbar is None:
            logger.warning("Anki Garden: toolbar not available on this Anki version; skipping toolbar action")
            return
        toolbar.addAction(action)

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
        self._apply_retrospective_growth()
        self.engine.rollover_if_needed()
        if self.dashboard is None:
            self.dashboard = GardenDashboard(mw, self.engine, self.storage, self.config)
        self.dashboard.refresh_all()
        self.dashboard.show()
        self.dashboard.raise_()

    def _setup_sync_hooks(self) -> None:
        try:
            from aqt import gui_hooks

            if hasattr(gui_hooks, "sync_did_finish"):
                gui_hooks.sync_did_finish.append(lambda *_args, **_kwargs: self._apply_retrospective_growth())
        except Exception:
            logger.exception("Anki Garden: failed to attach sync hooks")

    def _setup_home_screen_widget(self) -> None:
        if self._home_widget_hooked:
            return

        try:
            from aqt import gui_hooks
        except Exception:
            logger.exception("Anki Garden: unable to import gui_hooks for home-screen injection")
            return

        attached_hooks: list[str] = []

        # Prefer the modern webview hook to avoid duplicate rendering on versions
        # where both legacy render hooks and webview hook fire for the same screen.
        if hasattr(gui_hooks, "webview_will_set_content"):
            gui_hooks.webview_will_set_content.append(self._inject_home_garden_webview)
            attached_hooks.append("webview_will_set_content")
        else:
            if hasattr(gui_hooks, "deck_browser_will_render_content"):
                gui_hooks.deck_browser_will_render_content.append(self._inject_home_garden)
                attached_hooks.append("deck_browser_will_render_content")
            if hasattr(gui_hooks, "overview_will_render_content"):
                gui_hooks.overview_will_render_content.append(self._inject_home_garden)
                attached_hooks.append("overview_will_render_content")

        if attached_hooks:
            self._home_widget_hooked = True
            logger.info("Anki Garden attached home-screen hooks: %s", ", ".join(attached_hooks))
        else:
            logger.warning("Anki Garden: no supported home-screen hooks available on this Anki version")

    def _inject_home_garden(self, _page: object, content: object) -> None:
        self.engine.rollover_if_needed()
        self._apply_retrospective_growth()

        html = self._build_home_garden_html()
        if hasattr(content, "stats") and isinstance(content.stats, str):
            if "ag-home-root" not in content.stats:
                content.stats += html
            return

        if hasattr(content, "table") and isinstance(content.table, str):
            if "ag-home-root" not in content.table:
                content.table += html

    def _context_name(self, context: object) -> str:
        cls = type(context)
        module = getattr(cls, "__module__", "")
        qualname = getattr(cls, "__qualname__", cls.__name__)
        return f"{module}.{qualname}".lower()

    def _is_main_screen_context(self, context: object) -> bool:
        context_name = self._context_name(context)
        is_primary_home_context = any(name in context_name for name in ("deckbrowser", "overview", "homescreen"))
        is_lower_bar_context = any(name in context_name for name in ("bottom", "toolbar", "statusbar", "footer"))
        return is_primary_home_context and not is_lower_bar_context

    def _inject_home_garden_webview(self, web_content: object, context: object) -> None:
        context_name = self._context_name(context)
        if not self._is_main_screen_context(context):
            logger.debug("Anki Garden: skipping home injection for non-primary context %s", context_name)
            return

        logger.debug("Anki Garden: injecting home garden into context %s", context_name)
        self.engine.rollover_if_needed()
        self._apply_retrospective_growth()
        html = self._build_home_garden_html()

        body = getattr(web_content, "body", None)
        if isinstance(body, str) and "ag-home-root" not in body:
            web_content.body = body + html

    def _build_home_garden_html(self) -> str:
        request_id = self._home_widget_controller.begin_request()
        try:
            state = self.storage.state
            data = build_home_widget_success_data(
                state=state,
                cards_today=self._cards_reviewed_today(),
                health_ratio=self.engine.garden_health_index(),
                growth_cap=max(1, int(self.config.value("daily_growth_cap", 220))),
                plants_html=self._plant_badges_html(),
                event=self.engine.get_weekly_event_summary(),
            )
            self._home_widget_controller.resolve_success(request_id, data)
        except Exception:
            logger.exception("Anki Garden: failed to build home garden html")
            self._home_widget_controller.resolve_error(request_id, "Unable to load garden stats right now. Retry to refresh.")
        return render_home_widget(self._home_widget_controller.snapshot)

    def _plant_badges_html(self) -> str:
        plants = self.storage.state.plants[:4]
        if not plants:
            return '<div class="ag-home__plant"><div class="ag-home__plant-emoji">🌱</div><div class="ag-home__plant-name">Seedling</div></div>'
        badges = []
        for plant in plants:
            emoji = self._plant_emoji_for_stage(plant.growth_stage, plant.rare_variant)
            plant_name = escape(str(plant.name))
            image_html = self._plant_badge_image_html(plant)
            if not image_html:
                image_html = f'<div class="ag-home__plant-emoji">{emoji}</div>'
            badges.append(
                f'<div class="ag-home__plant">{image_html}'
                f'<div class="ag-home__plant-name">{plant_name}</div></div>'
            )
        return "".join(badges)

    def _plant_badge_image_html(self, plant: object) -> str:
        resolver = getattr(self.engine, "resolve_plant_image", None)
        if resolver is None:
            return ""
        try:
            path = resolver(plant.species, plant.growth_stage, plant.rare_variant)
        except Exception:
            logger.debug("Anki Garden: unable to resolve home widget plant image", exc_info=True)
            return ""
        if not path:
            return ""
        try:
            image_path = Path(str(path)).expanduser()
            if not image_path.exists() or not image_path.is_file() or image_path.suffix.lower() != ".svg":
                return ""
            src = escape(image_path.resolve().as_uri(), quote=True)
        except Exception:
            return ""
        plant_name = escape(str(getattr(plant, "name", "Plant")), quote=True)
        return f'<img class="ag-home__plant-thumb" src="{src}" alt="{plant_name}">'

    def _cards_reviewed_today(self) -> int:
        fallback = int(getattr(self.storage.state.daily_stats, "reviewed", 0))
        try:
            collection = getattr(mw, "col", None)
            if collection is None or getattr(collection, "db", None) is None:
                DISPLAY_TELEMETRY.record_missing_or_invalid_field(
                    route="home_widget",
                    field="collection.db",
                    reason="missing_collection_db",
                    required=True,
                )
                DISPLAY_TELEMETRY.track_fallback(route="home_widget", field="cards_today")
                return fallback
            sched = getattr(collection, "sched", None)
            day_cutoff = getattr(sched, "day_cutoff", None)
            if day_cutoff is None:
                day_cutoff = getattr(sched, "dayCutoff", None)
            if day_cutoff is None:
                DISPLAY_TELEMETRY.record_missing_or_invalid_field(
                    route="home_widget",
                    field="scheduler.day_cutoff",
                    reason="missing_day_cutoff",
                    required=True,
                )
                DISPLAY_TELEMETRY.track_fallback(route="home_widget", field="cards_today")
                return fallback
            cutoff_ms = int(day_cutoff) * 1000
            count = collection.db.scalar("select count(distinct cid) from revlog where id > ?", cutoff_ms)
            return max(0, int(count or 0))
        except Exception as exc:
            DISPLAY_TELEMETRY.track_parsing_exception(route="home_widget", field="cards_today", exc=exc)
            DISPLAY_TELEMETRY.track_fallback(route="home_widget", field="cards_today")
            return fallback

    def _plant_emoji_for_stage(self, stage: str, rare: bool) -> str:
        if rare:
            return "🌟"
        return {
            "seed": "🟤",
            "sprout": "🌱",
            "young": "🌿",
            "mature": "🌳",
            "flowering": "🌸",
            "rare": "✨",
        }.get(stage, "🌱")

    def _apply_retrospective_growth(self) -> None:
        last_id = int(self.storage.state.retrospective_last_revlog_id or 0)
        rows = self.storage.load_new_revlog_entries(last_id)
        if not rows:
            if last_id == 0:
                self.storage.state.retrospective_last_revlog_id = self.storage.max_revlog_id()
                self.storage.save()
            return

        payloads = []
        latest_id = last_id
        for rid, cid, ease, ivl, last_ivl, factor, _ms, qtype in rows:
            latest_id = max(latest_id, int(rid))
            deck_id = None
            try:
                card = mw.col.get_card(int(cid))
                deck_id = int(card.did)
            except Exception:
                pass
            delta_ivl = max(0, int(ivl) - max(0, int(last_ivl)))
            difficulty = max(0.1, min(1.0, (3000 - int(factor or 2500)) / 2000))
            if int(ease) == 1:
                difficulty = min(1.0, difficulty + 0.15)
            payloads.append(
                {
                    "ease": int(ease),
                    "deck_id": deck_id,
                    "difficulty": difficulty,
                    "lapse_count": 1 if int(ease) == 1 else 0,
                    "queue": 2 if int(qtype) in (1, 2, 3) else 0,
                    "interval_delta": delta_ivl,
                }
            )
        gained = self.engine.apply_retrospective_reviews(payloads)
        self.storage.state.retrospective_last_revlog_id = latest_id
        self.storage.save()
        if self.dashboard:
            self.dashboard.show_retrospective_feedback(len(payloads), gained)


_app: Optional[AnkiGardenApp] = None


def setup_addon() -> None:
    global _app
    if mw is None:
        return
    _app = AnkiGardenApp()
    _app.setup()
