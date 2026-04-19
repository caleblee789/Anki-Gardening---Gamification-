from __future__ import annotations

from typing import Any

from aqt import mw


class ReviewerHookHandler:
    def __init__(self, engine: Any, storage: Any) -> None:
        self.engine = engine
        self.storage = storage

    def on_answer(self, reviewer: Any, card: Any, ease: int) -> None:
        factor = getattr(card, "factor", 2500)
        difficulty = max(0.1, min(1.0, (3000 - factor) / 2000))
        payload = {
            "queue": getattr(card, "queue", 2),
            "ease": ease,
            "deck_id": getattr(card, "did", None),
            "difficulty": difficulty,
            "lapse_count": int(getattr(card, "lapses", 0)),
        }
        self.engine.register_review(payload)
        latest = self.storage.max_revlog_id() if hasattr(self.storage, "max_revlog_id") else 0
        self.storage.state.retrospective_last_revlog_id = max(int(self.storage.state.retrospective_last_revlog_id or 0), int(latest or 0))
        self.storage.save()

        try:
            due = mw.col.sched.counts()
            self.engine.set_due_completion(sum(due) == 0)
        except Exception:
            pass
