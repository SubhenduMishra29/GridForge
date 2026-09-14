from __future__ import annotations

from core.application.events import ValidationChanged


class ValidationProjection:
    event_types = (ValidationChanged,)

    def __init__(self, *, panel) -> None:
        self._panel = panel
        self._messages = ()
        self._disposed = False

    def refresh(self, event) -> None:
        if self._disposed:
            return
        payload = getattr(event, "payload", {})
        raw = payload.get("messages", ()) if hasattr(payload, "get") else ()
        self._messages = (str(raw),) if isinstance(raw, str) else tuple(str(item) for item in raw)
        self._panel.set_messages(self._messages)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._panel.set_messages(())
        self._messages = ()
        self._disposed = True


__all__ = ["ValidationProjection"]
