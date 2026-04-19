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
        self._setup_home_screen_widget()
        reviewer_did_answer_card.append(self.reviewer_hooks.on_answer)
        self._setup_sync_hooks()
        self._apply_retrospective_growth()
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
            pass

    def _setup_home_screen_widget(self) -> None:
        try:
            from aqt import gui_hooks

            if hasattr(gui_hooks, "deck_browser_will_render_content"):
                gui_hooks.deck_browser_will_render_content.append(self._inject_home_garden)
            if hasattr(gui_hooks, "overview_will_render_content"):
                gui_hooks.overview_will_render_content.append(self._inject_home_garden)
            if hasattr(gui_hooks, "webview_will_set_content"):
                gui_hooks.webview_will_set_content.append(self._inject_home_garden_webview)
        except Exception:
            pass

    def _inject_home_garden(self, _page: object, content: object) -> None:
        self.engine.rollover_if_needed()
        html = self._build_home_garden_html()
        if hasattr(content, "stats") and isinstance(content.stats, str):
            if "ag-home-root" not in content.stats:
                content.stats += html
            return
        if hasattr(content, "table") and isinstance(content.table, str):
            if "ag-home-root" not in content.table:
                content.table += html

    def _inject_home_garden_webview(self, web_content: object, context: object) -> None:
        context_name = type(context).__name__.lower()
        if "deckbrowser" not in context_name and "overview" not in context_name:
            return
        html = self._build_home_garden_html()
        body = getattr(web_content, "body", None)
        if isinstance(body, str) and "ag-home-root" not in body:
            web_content.body = body + html

    def _build_home_garden_html(self) -> str:
        except Exception:
            pass

    def _inject_home_garden(self, _deck_browser: object, content: object) -> None:
        self.engine.rollover_if_needed()
        self._apply_retrospective_growth()
        state = self.storage.state
        stats = state.daily_stats
        health_pct = int(self.engine.garden_health_index() * 100)
        growth_cap = max(1, int(self.config.value("daily_growth_cap", 220)))
        growth_pct = int(min(100, (stats.growth_earned / growth_cap) * 100))
        weather = str(state.selected_weather).replace("_", " ").title()
        plants = state.plants[:3]
        plant_visual = " ".join(self._plant_emoji_for_stage(p.growth_stage, p.rare_variant) for p in plants) or "🌱"
        event = self.engine.get_weekly_event_summary()
        html = f"""
<style>
.ag-home {{
  margin: 12px 0;
  border-radius: 16px;
  border: 1px solid #2f4652;
  background: linear-gradient(135deg, #0f1e2c 0%, #143b2f 65%, #1f4737 100%);
  color: #ecf8ef;
  box-shadow: 0 6px 20px rgba(0,0,0,0.2);
  overflow: hidden;
}}
.ag-home__head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(0,0,0,0.2);
  font-weight: 700;
}}
.ag-home__plants {{
  font-size: 32px;
  text-align: center;
  letter-spacing: 6px;
  padding: 8px 12px 0;
  text-shadow: 0 0 12px rgba(154, 251, 177, 0.4);
}}
.ag-home__stats {{
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 8px;
  padding: 8px 12px 12px;
}}
.ag-home__pill {{
  border-radius: 12px;
  background: rgba(255,255,255,0.08);
  padding: 8px 10px;
}}
.ag-home__label {{ font-size: 11px; opacity: 0.76; text-transform: uppercase; }}
.ag-home__value {{ font-size: 18px; font-weight: 700; margin-top: 2px; }}
.ag-home__bar {{
  height: 10px;
  border-radius: 99px;
  background: rgba(255,255,255,0.14);
  margin: 2px 12px 12px;
  overflow: hidden;
}}
.ag-home__bar span {{
  display: block;
  height: 100%;
  width: {growth_pct}%;
  border-radius: 99px;
  background: linear-gradient(90deg, #61d984 0%, #cbff8e 100%);
  box-shadow: 0 0 16px rgba(168, 255, 173, 0.75);
}}
.ag-home__event {{
  font-size: 12px;
  opacity: 0.9;
  padding: 0 12px 12px;
}}
</style>
<div id="ag-home-root" class="ag-home">
<div class="ag-home">
  <div class="ag-home__head">
    <span>🌿 Anki Garden</span>
    <span>{state.streak_days}d streak</span>
  </div>
  <div class="ag-home__plants">{plant_visual}</div>
  <div class="ag-home__stats">
    <div class="ag-home__pill"><div class="ag-home__label">Cards Today</div><div class="ag-home__value">{stats.reviewed}</div></div>
    <div class="ag-home__pill"><div class="ag-home__label">Garden Health</div><div class="ag-home__value">{health_pct}%</div></div>
    <div class="ag-home__pill"><div class="ag-home__label">Weather</div><div class="ag-home__value">{weather}</div></div>
  </div>
  <div class="ag-home__bar"><span></span></div>
  <div class="ag-home__event">Growth today: {stats.growth_earned}/{growth_cap} • Event: {event}</div>
</div>
"""
        return html
        if hasattr(content, "stats") and isinstance(content.stats, str):
            content.stats += html

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
