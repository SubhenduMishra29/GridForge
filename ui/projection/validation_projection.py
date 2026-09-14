# ============================================================
# GridForge V2 — Validation Projection
# ============================================================
# Author: Subhendu Mishra
# ============================================================
from __future__ import annotations

from typing import Any

from core.application.events import ValidationChanged


class ValidationProjection:
    event_types = (ValidationChanged,)

    def __init__(self, *, application: Any, panel: Any) -> None:
        self._application = application
        self._panel = panel
        self._messages: tuple[str, ...] = ()
        self._disposed = False
        self.refresh_from_application()

    @property
    def messages(self) -> tuple[str, ...]:
        return self._messages

    def refresh(self, event: Any) -> None:
        del event
        if not self._disposed:
            self.refresh_from_application()

    def refresh_from_application(self) -> None:
        if self._disposed:
            return
        result = self._application.read_validation()
        if result is None:
            self._messages = ()
        else:
            summary = result.summary
            self._messages = tuple(
                [f"Validation - errors: {summary.errors}, warnings: {summary.warnings}, info: {summary.infos}"]
                + [
                    f"{issue.severity.value.upper()} {issue.code}"
                    f" [{issue.element_type or 'element'}:{issue.element_id}]"
                    f": {issue.message}"
                    for issue in result.issues
                ]
            )
        self._panel.set_messages(self._messages)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._panel.set_messages(())
        self._messages = ()
        self._disposed = True


__all__ = ["ValidationProjection"]
