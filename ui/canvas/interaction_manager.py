"""Central presentation-side routing for Canvas interaction input.

Author: Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Optional

from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.canvas.canvas_framework import CanvasInteractionState, CanvasStateMachine


class InteractionManager:
    """Route semantic Canvas events to the active UI ToolManager."""

    def __init__(
        self,
        *,
        view: Any = None,
        controller: Any = None,
        tool_manager: Any,
        coordinate_system: Any = None,
        snap_system: Any = None,
        preview_layer: Any = None,
        selection_manager: Any = None,
        command_manager: Any = None,
        workspace_id: str = "sld",
        discipline: str | None = None,
        input_adapter: Optional[MouseEventAdapter] = None,
    ) -> None:
        if tool_manager is None:
            raise ValueError("InteractionManager requires an existing ToolManager.")

        self.view = view
        self.controller = controller
        self.tool_manager = tool_manager
        self.coordinate_system = coordinate_system
        self.snap_system = snap_system
        self.preview_layer = preview_layer
        self.selection_manager = selection_manager
        self.command_manager = command_manager
        self.input_adapter = input_adapter
        if not isinstance(workspace_id, str) or not workspace_id.strip():
            raise ValueError("workspace_id must be a non-empty string.")
        self.workspace_id = workspace_id.strip()
        self.discipline = (discipline or self.workspace_id).strip()
        if not self.discipline:
            raise ValueError("discipline must be a non-empty string.")
        self._disposed = False
        self._state_machine = CanvasStateMachine(workspace_id=self.workspace_id)

    @property
    def context(self) -> dict[str, str]:
        return {"workspace_id": self.workspace_id, "discipline": self.discipline}

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def state(self) -> CanvasInteractionState:
        return self._state_machine.state

    @property
    def active_tool(self) -> Optional[Any]:
        if self._disposed:
            return None
        manager = self.tool_manager
        value = getattr(manager, "active_tool", None)
        if value is not None:
            return value
        getter = getattr(manager, "get_active_tool", None)
        return getter() if callable(getter) else None

    def synchronize_tool_state(self) -> CanvasInteractionState:
        """Reconcile presentation state with the authoritative active tool."""
        tool_id = str(getattr(self.tool_manager, "active_tool_id", "") or "")
        if not tool_id:
            return self._state_machine.cancel()
        if tool_id == "wire":
            target = CanvasInteractionState.WIRE_START
        elif tool_id == "select":
            target = CanvasInteractionState.SELECTING
        else:
            target = CanvasInteractionState.PLACING_PREVIEW
        self._force_transition(target)
        return self._state_machine.state

    def mouse_press(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_press", event)

    def mouse_move(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_move", event)

    def mouse_release(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_release", event)

    def mouse_double_click(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_double_click", event)

    def key_press(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("key_press", event)

    def key_release(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("key_release", event)

    def _mouse_dispatch(self, method_name: str, event: Any) -> bool:
        if self._disposed:
            return False
        semantic_event = self.input_adapter.adapt(event) if self.input_adapter is not None else event
        return self._dispatch_event(method_name, semantic_event)

    def _dispatch_event(self, method_name: str, event: Any) -> bool:
        manager = self.tool_manager
        handler = getattr(manager, method_name, None)
        if not callable(handler):
            return False

        tool_id = str(getattr(manager, "active_tool_id", "") or "")
        tool = getattr(manager, "active_tool", None)
        wire_has_source = (
            tool_id == "wire"
            and tool is not None
            and getattr(getattr(tool, "_preview", None), "source_endpoint", None) is not None
        )

        if method_name == "key_press" and self._is_escape(event):
            self._state_machine.cancel()
        elif method_name == "mouse_press":
            self._transition_for_press(tool_id, wire_has_source)

        result = handler(event)
        accepted = bool(result) if result is not None else True
        self._reconcile_outcome(method_name, tool_id, accepted, wire_has_source)
        return accepted

    def _transition_for_press(self, tool_id: str, wire_has_source: bool) -> None:
        if not tool_id:
            self._state_machine.cancel()
            return
        if tool_id == "select":
            target = CanvasInteractionState.SELECTING
        elif tool_id == "wire":
            target = CanvasInteractionState.WIRE_ROUTING if wire_has_source else CanvasInteractionState.WIRE_START
        else:
            target = CanvasInteractionState.PLACING_PREVIEW
        self._force_transition(target)

    def _reconcile_outcome(
        self,
        method_name: str,
        tool_id: str,
        accepted: bool,
        wire_had_source: bool,
    ) -> None:
        if method_name == "key_press":
            return
        if not accepted:
            return

        if tool_id == "wire":
            if method_name == "mouse_press":
                if wire_had_source:
                    self._force_transition(CanvasInteractionState.CONNECTION_COMMITTED)
                    self._state_machine.cancel()
                else:
                    self._force_transition(CanvasInteractionState.WIRE_ROUTING)
            return

        if tool_id == "select":
            if method_name == "mouse_release":
                self._force_transition(CanvasInteractionState.IDLE)
            return

        if method_name == "mouse_release":
            # The tool return value is the authoritative creation outcome:
            # commit state is a milestone, then the shared interaction state
            # returns immediately to the stable idle state.
            self._force_transition(CanvasInteractionState.EQUIPMENT_COMMITTED)
            self._state_machine.cancel()

    def _force_transition(self, target: CanvasInteractionState) -> None:
        if self._state_machine.state is target:
            return
        try:
            self._state_machine.transition(target)
        except ValueError:
            self._state_machine.cancel()
            self._state_machine.transition(target)

    @staticmethod
    def _is_escape(event: Any) -> bool:
        key = getattr(event, "key", None) if event is not None else None
        if callable(key):
            key = key()
        if isinstance(event, dict):
            key = event.get("key", key)
        return key in ("Escape", "escape", 0x01000000, 16777216, "Key_Escape")

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        if self.input_adapter is not None:
            self.input_adapter.dispose()
        self.input_adapter = None
        self.view = None
        self.controller = None
        self.coordinate_system = None
        self.snap_system = None
        self.preview_layer = None
        self.selection_manager = None
        self.command_manager = None
        self._state_machine.cancel()


__all__ = ["InteractionManager"]
