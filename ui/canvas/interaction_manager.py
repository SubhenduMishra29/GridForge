"""
GridForge V2 — Canvas Interaction Manager
=========================================

File:
    ui/canvas/interaction_manager.py

Purpose
-------
Central interaction routing boundary for the GridForge SLD Canvas.

InteractionManager translates view-level input events into calls to the
already-created UI ToolManager.

Architectural role
------------------
    GraphicsView
         │
         ▼
    InteractionManager
         │
         ▼
     UI ToolManager
         │
         ▼
      Active UI Tool
         │
         ▼
    Presentation Controller
         │
         ▼
    [future explicit UI ↔ Application interface]
         │
         ▼
      Application
         │
         ▼
         Core

Ownership rules
---------------
- InteractionManager does NOT create ToolManager.
- InteractionManager does NOT own ToolManager.
- InteractionManager does NOT dispose ToolManager.
- ToolManager is supplied by the UI composition/plugin boundary.
- InteractionManager only routes interaction events.
- InteractionManager does not implement tool behaviour.
- InteractionManager does not implement snapping.
- InteractionManager does not implement selection.
- InteractionManager does not implement navigation.
- InteractionManager does not implement rendering.
- InteractionManager does not modify the electrical Core directly.
- InteractionManager does not bypass the future Application boundary.
"""

from __future__ import annotations

from typing import Any, Optional


class InteractionManager:
    """Route Canvas input events to the shared UI ToolManager.

    This is a Presentation-layer routing service. It is deliberately
    thin and does not become an Application/Core bridge.
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
    ) -> None:
        """Construct an InteractionManager.

        Parameters are Presentation/UI services supplied by the
        composition boundary. The Application layer is the future
        explicit Core↔UI integration boundary.
        """
        if tool_manager is None:
            raise ValueError(
                "InteractionManager requires an existing ToolManager."
            )

        self.view = view
        self.controller = controller
        self.tool_manager = tool_manager
        self.coordinate_system = coordinate_system
        self.snap_system = snap_system
        self.preview_layer = preview_layer
        self.selection_manager = selection_manager
        self.command_manager = command_manager
        self._disposed = False

    @property
    def disposed(self) -> bool:
        """Return whether this interaction manager has been disposed."""
        return self._disposed

    @property
    def active_tool(self) -> Optional[Any]:
        """Return the active UI tool from ToolManager."""
        if self._disposed:
            return None

        manager = self.tool_manager
        value = getattr(manager, "active_tool", None)
        if value is not None:
            return value

        getter = getattr(manager, "get_active_tool", None)
        if callable(getter):
            return getter()

        return None

    def mouse_press(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("mouse_press", event)

    def mouse_move(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("mouse_move", event)

    def mouse_release(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("mouse_release", event)

    def key_press(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("key_press", event)

    def key_release(self, event: Any) -> bool:
        if self._disposed:
            return False
        return self._dispatch_event("key_release", event)

    def _dispatch_event(self, method_name: str, event: Any) -> bool:
        manager = self.tool_manager
        handler = getattr(manager, method_name, None)
        if not callable(handler):
            return False

        result = handler(event)
        return bool(result) if result is not None else True

    def dispose(self) -> None:
        """Dispose this routing service without disposing shared services."""
        if self._disposed:
            return
        self._disposed = True
        self.view = None
        self.controller = None
        self.coordinate_system = None
        self.snap_system = None
        self.preview_layer = None
        self.selection_manager = None
        self.command_manager = None


__all__ = ["InteractionManager"]
