from __future__ import annotations

from core.application.events import StudyCancelled, StudyCompleted, StudyFailed, StudyStarted


class StudyProjection:
    """Project study lifecycle facts into the Study Cases presentation surface."""

    event_types = (StudyStarted, StudyCompleted, StudyFailed, StudyCancelled)

    def __init__(self, *, panel) -> None:
        if panel is None or not callable(getattr(panel, "set_cases", None)):
            raise TypeError("panel must provide set_cases().")
        self._panel = panel
        self._cases: tuple[str, ...] = ()
        self._disposed = False

    @property
    def cases(self) -> tuple[str, ...]:
        return self._cases

    def refresh(self, event) -> None:
        if self._disposed:
            return
        payload = getattr(event, "payload", {})
        study = payload.get("study", payload.get("study_id", payload.get("operation", event.event_type))) if hasattr(payload, "get") else event.event_type
        status = event.event_type.rsplit(".", 1)[-1]
        entry = f"{study} — {status}"
        self._cases = (entry,)
        self._panel.set_cases(self._cases)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._cases = ()
        self._panel.set_cases(())
        self._disposed = True


__all__ = ["StudyProjection"]
