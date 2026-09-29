# ============================================================
# GridForge V2 — Application Event Messages Projection
# Author: Subhendu Mishra
# ============================================================
"""Project concise semantic Application events into Messages / Events."""
from __future__ import annotations
from collections import deque
from datetime import datetime
from typing import Any
from core.application.events import (
    ApplicationEvent, ElementCreated, ElementUpdated, ElementRemoved,
    NetworkChanged, TopologyChanged, SimpleWireConnectionCreated,
    SimpleWireConnectionRemoved, ProjectLoaded, ProjectSaved, ProjectClosed,
    ValidationChanged, StudyStarted, StudyCompleted, StudyFailed, StudyCancelled,
    SLDPresentationChanged,
)

class ApplicationEventMessagesProjection:
    """Single read-only event-to-panel adapter using the existing Application event bus."""
    event_types = (
        ElementCreated, ElementUpdated, ElementRemoved, NetworkChanged, TopologyChanged,
        SimpleWireConnectionCreated, SimpleWireConnectionRemoved,
        ProjectLoaded, ProjectSaved, ProjectClosed, ValidationChanged,
        StudyStarted, StudyCompleted, StudyFailed, StudyCancelled, SLDPresentationChanged,
    )
    def __init__(self, *, panel: Any, limit: int = 250) -> None:
        if panel is None or not callable(getattr(panel, "set_event_messages", None)):
            raise TypeError("panel must provide set_event_messages().")
        self._panel=panel
        self._messages=deque(maxlen=max(20,int(limit)))
        self._disposed=False
    @property
    def messages(self) -> tuple[str,...]: return tuple(self._messages)
    def refresh(self,event: ApplicationEvent) -> None:
        if self._disposed: return
        self._messages.append(self._format(event))
        self._panel.set_event_messages(tuple(self._messages))
    def dispose(self) -> None:
        if self._disposed: return
        self._messages.clear()
        self._panel.set_event_messages(())
        self._disposed=True
    @staticmethod
    def _format(event: ApplicationEvent) -> str:
        p = getattr(event, "payload", {}) or {}
        metadata = getattr(event, "metadata", {}) or {}
        severity = str(metadata.get("severity") or p.get("severity") or "INFO").upper()
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        event_type = str(getattr(event, "event_type", type(event).__name__))
        identity = (
            p.get("element_id")
            or p.get("connection_id")
            or p.get("project_id")
            or p.get("study_id")
            or ""
        )
        if isinstance(event, ElementCreated):
            message = f"Element created: {p.get('element_type','element')}"
        elif isinstance(event, ElementUpdated):
            message = f"Element updated: {p.get('element_type','element')}"
        elif isinstance(event, ElementRemoved):
            message = f"Element removed: {p.get('element_type','element')}"
        elif isinstance(event, SimpleWireConnectionCreated):
            message = "Connection created"
        elif isinstance(event, SimpleWireConnectionRemoved):
            message = "Connection removed"
        elif isinstance(event, SLDPresentationChanged):
            message = f"SLD presentation: {p.get('operation','updated')}"
        elif isinstance(event, ValidationChanged):
            message = "Validation state updated"
        elif isinstance(event, ProjectLoaded):
            message = f"Project loaded: {p.get('name') or p.get('project_id','project')}"
        elif isinstance(event, ProjectSaved):
            message = "Project saved"
        elif isinstance(event, ProjectClosed):
            message = "Project closed"
        elif isinstance(event, StudyStarted):
            message = f"Study started: {p.get('study_type',p.get('study_id','study'))}"
        elif isinstance(event, StudyCompleted):
            message = f"Study completed: {p.get('study_type',p.get('study_id','study'))}"
        elif isinstance(event, StudyFailed):
            message = f"Study failed: {p.get('study_type',p.get('study_id','study'))}"
        elif isinstance(event, StudyCancelled):
            message = f"Study cancelled: {p.get('study_type',p.get('study_id','study'))}"
        elif isinstance(event, TopologyChanged):
            message = f"Topology changed: {p.get('operation','updated')}"
        elif isinstance(event, NetworkChanged):
            message = f"Network changed: {p.get('operation','updated')}"
        else:
            message = event_type
        suffix = f" [{identity}]" if identity else ""
        return f"{timestamp} | {severity:<7} | {event_type} | {message}{suffix}"
__all__=["ApplicationEventMessagesProjection"]
