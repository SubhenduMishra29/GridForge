"""Central presentation-side routing for Canvas interaction input."""

from __future__ import annotations

from typing import Any, Optional

from ui.canvas.mouse_event_adapter import MouseEventAdapter


class InteractionManager:
    """Route semantic Canvas events to the active UI ToolManager.

    Native Qt mouse events are translated here, before tools see them. This
    keeps QGraphicsScene knowledge at the Canvas boundary and leaves tools
    responsible only for interaction semantics.
    """

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
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

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

    def mouse_press(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_press", event)

    def mouse_move(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_move", event)

    def mouse_release(self, event: Any) -> bool:
        return self._mouse_dispatch("mouse_release", event)

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
        result = handler(event)
        return bool(result) if result is not None else True

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


__all__ = ["InteractionManager"]
