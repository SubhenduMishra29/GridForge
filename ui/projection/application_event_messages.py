# ============================================================
# GridForge V2 — Application Event Messages Projection
# Author: Subhendu Mishra
# ============================================================
"""Project concise semantic Application events into Messages / Events."""
from __future__ import annotations
from collections import deque
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
        p=getattr(event,"payload",{}) or {}
        if isinstance(event,ElementCreated): return f"Element created: {p.get('element_type','element')} {p.get('element_id','')}".strip()
        if isinstance(event,ElementUpdated): return f"Element updated: {p.get('element_type','element')} {p.get('element_id','')}".strip()
        if isinstance(event,ElementRemoved): return f"Element removed: {p.get('element_type','element')} {p.get('element_id','')}".strip()
        if isinstance(event,SimpleWireConnectionCreated): return f"Connection created: {p.get('connection_id','wire')}"
        if isinstance(event,SimpleWireConnectionRemoved): return f"Connection removed: {p.get('connection_id','wire')}"
        if isinstance(event,SLDPresentationChanged): return f"SLD presentation: {p.get('operation','updated')}"
        if isinstance(event,ValidationChanged): return "Validation state updated"
        if isinstance(event,ProjectLoaded): return f"Project loaded: {p.get('name') or p.get('project_id','project')}"
        if isinstance(event,ProjectSaved): return "Project saved"
        if isinstance(event,ProjectClosed): return "Project closed"
        if isinstance(event,StudyStarted): return f"Study started: {p.get('study_type',p.get('study_id','study'))}"
        if isinstance(event,StudyCompleted): return f"Study completed: {p.get('study_type',p.get('study_id','study'))}"
        if isinstance(event,StudyFailed): return f"Study failed: {p.get('study_type',p.get('study_id','study'))}"
        if isinstance(event,StudyCancelled): return f"Study cancelled: {p.get('study_type',p.get('study_id','study'))}"
        if isinstance(event,TopologyChanged): return f"Topology changed: {p.get('operation','updated')}"
        if isinstance(event,NetworkChanged): return f"Network changed: {p.get('operation','updated')}"
        return event.event_type
__all__=["ApplicationEventMessagesProjection"]
