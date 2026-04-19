"""Anki Garden add-on entrypoint."""

try:
    from .addon import setup_addon

    setup_addon()
except Exception:
    # Allows local unit tests/imports outside Anki runtime.
    pass
