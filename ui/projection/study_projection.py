# ============================================================
# GridForge V2 — Study Projection
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from typing import Any
from uuid import UUID

from core.application.events import (
    ProjectClosed,
    ProjectLoaded,
    StudyCancelled,
    StudyCompleted,
    StudyFailed,
    StudyStarted,
)


class StudyProjection:
    """Project Application-owned study lifecycle and results into Study Cases."""

    event_types = (
        ProjectLoaded,
        ProjectClosed,
        StudyStarted,
        StudyCompleted,
        StudyFailed,
        StudyCancelled,
    )

    def __init__(self, *, application: Any, panel: Any) -> None:
        if application is None or not callable(getattr(application, "study_result", None)):
            raise TypeError("application must provide study_result().")
        if panel is None or not callable(getattr(panel, "set_cases", None)):
            raise TypeError("panel must provide set_cases().")
        self._application = application
        self._panel = panel
        self._cases: tuple[str, ...] = ()
        self._active: dict[str, dict[str, str]] = {}
        self._disposed = False

    @property
    def cases(self) -> tuple[str, ...]:
        return self._cases

    def refresh(self, event: Any) -> None:
        if self._disposed:
            return
        if isinstance(event, (ProjectLoaded, ProjectClosed)):
            self._active.clear()
            self._cases = ()
            self._panel.set_cases(())
            return

        payload = getattr(event, "payload", {})
        study_id = payload.get("study_id") if hasattr(payload, "get") else None
        study_type = payload.get("study_type") if hasattr(payload, "get") else None
        if study_id is None:
            return

        status = event.event_type.rsplit(".", 1)[-1]
        entry = {
            "study_id": str(study_id),
            "study_type": str(study_type or "study"),
            "status": status,
        }
        if status in {"completed", "failed", "cancelled"}:
            try:
                result = self._application.study_result(UUID(str(study_id)))
            except (TypeError, ValueError):
                result = None
            if result is not None:
                entry["study_type"] = str(result.study_type)
                entry["status"] = str(result.status)
                if getattr(result, "message", ""):
                    entry["message"] = str(result.message)
        self._active[str(study_id)] = entry
        self._render()

    def _render(self) -> None:
        rows = []
        for entry in self._active.values():
            message = entry.get("message")
            suffix = f" — {message}" if message else ""
            rows.append(
                f"{entry['study_type']} [{entry['status']}] {entry['study_id']}{suffix}"
            )
        self._cases = tuple(rows)
        self._panel.set_cases(self._cases)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._active.clear()
        self._cases = ()
        self._panel.set_cases(())
        self._disposed = True


__all__ = ["StudyProjection"]
