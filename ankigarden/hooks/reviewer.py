from __future__ import annotations

from typing import Any

from aqt import mw


class ReviewerHookHandler:
    def __init__(self, engine: Any, storage: Any) -> None:
        self.engine = engine
        self.storage = storage

    def on_answer(self, reviewer: Any, card: Any, ease: int) -> None:
        payload = {
            "queue": getattr(card, "queue", 2),
            "ease": ease,
            "deck_id": card.did,
        }
        self.engine.register_review(payload)

        # lightweight check for due completion for achievement
        try:
            due = mw.col.sched.counts()
            self.engine.set_due_completion(sum(due) == 0)
        except Exception:
            pass
