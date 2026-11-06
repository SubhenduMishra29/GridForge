# ============================================================
# File: ui/canvas/canvas_framework.py
# GridForge V2 — Shared Canvas Framework
# Author: Subhendu Mishra
# ============================================================
"""Domain-neutral shared canvas interaction infrastructure.

This module owns presentation interaction state only. It deliberately does
not know about electrical equipment, Control components, terminals, topology,
or Core objects.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class CanvasInteractionState(str, Enum):
    IDLE = "IDLE"
    SELECTING = "SELECTING"
    PLACING_PREVIEW = "PLACING_PREVIEW"
    EQUIPMENT_COMMITTED = "EQUIPMENT_COMMITTED"
    WIRE_START = "WIRE_START"
    WIRE_ROUTING = "WIRE_ROUTING"
    CONNECTION_COMMITTED = "CONNECTION_COMMITTED"
    PANNING = "PANNING"
    ZOOMING = "ZOOMING"


class CanvasStateMachine:
    """Small explicit state machine shared by graphical workspaces."""

    _TRANSITIONS = {
        CanvasInteractionState.IDLE: {
            CanvasInteractionState.SELECTING,
            CanvasInteractionState.PLACING_PREVIEW,
            CanvasInteractionState.WIRE_START,
            CanvasInteractionState.PANNING,
            CanvasInteractionState.ZOOMING,
        },
        CanvasInteractionState.SELECTING: {
            CanvasInteractionState.IDLE,
            CanvasInteractionState.PLACING_PREVIEW,
            CanvasInteractionState.WIRE_START,
            CanvasInteractionState.PANNING,
        },
        CanvasInteractionState.PLACING_PREVIEW: {
            CanvasInteractionState.EQUIPMENT_COMMITTED,
            CanvasInteractionState.IDLE,
            CanvasInteractionState.SELECTING,
        },
        CanvasInteractionState.EQUIPMENT_COMMITTED: {
            CanvasInteractionState.IDLE,
            CanvasInteractionState.SELECTING,
            CanvasInteractionState.WIRE_START,
            CanvasInteractionState.PLACING_PREVIEW,
        },
        CanvasInteractionState.WIRE_START: {
            CanvasInteractionState.WIRE_ROUTING,
            CanvasInteractionState.IDLE,
            CanvasInteractionState.SELECTING,
        },
        CanvasInteractionState.WIRE_ROUTING: {
            CanvasInteractionState.CONNECTION_COMMITTED,
            CanvasInteractionState.IDLE,
            CanvasInteractionState.WIRE_START,
        },
        CanvasInteractionState.CONNECTION_COMMITTED: {
            CanvasInteractionState.IDLE,
            CanvasInteractionState.SELECTING,
            CanvasInteractionState.WIRE_START,
        },
        CanvasInteractionState.PANNING: {
            CanvasInteractionState.IDLE,
        },
        CanvasInteractionState.ZOOMING: {
            CanvasInteractionState.IDLE,
        },
    }

    def __init__(self, *, workspace_id: str) -> None:
        if not isinstance(workspace_id, str) or not workspace_id.strip():
            raise ValueError("workspace_id must be a non-empty string.")
        self._workspace_id = workspace_id.strip()
        self._state = CanvasInteractionState.IDLE

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    @property
    def state(self) -> CanvasInteractionState:
        return self._state

    def transition(self, state: CanvasInteractionState) -> CanvasInteractionState:
        if not isinstance(state, CanvasInteractionState):
            state = CanvasInteractionState(str(state))
        if state is self._state:
            return self._state
        allowed = self._TRANSITIONS[self._state]
        if state not in allowed:
            raise ValueError(
                f"Invalid {self._workspace_id} canvas transition: "
                f"{self._state.value} -> {state.value}"
            )
        self._state = state
        return self._state

    def cancel(self) -> CanvasInteractionState:
        """Return any transient interaction to the stable idle state."""
        self._state = CanvasInteractionState.IDLE
        return self._state

    def snapshot(self) -> dict[str, Any]:
        return {"workspace_id": self._workspace_id, "state": self._state.value}


__all__ = ["CanvasInteractionState", "CanvasStateMachine"]
