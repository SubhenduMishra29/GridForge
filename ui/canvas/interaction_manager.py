"""
GridForge V2 — Canvas Interaction Manager
=========================================

File:
    ui/canvas/interaction_manager.py

Purpose
-------
Central input-routing layer for the GridForge canvas.

The InteractionManager receives raw canvas input from
GraphicsView, converts input into canonical canvas coordinates,
and delegates interaction to the active tool.

Architecture
------------

    GraphicsView
         │
         │ raw Qt events
         ▼
    InteractionManager
         │
         ├── CoordinateSystem
         ├── PreviewLayer
         ├── SnapSystem
         │
         ▼
      ToolManager
         │
         ▼
      Active Tool


Responsibilities
----------------
The InteractionManager:

    - receives canvas mouse events;
    - receives keyboard events;
    - maintains transient interaction state;
    - owns the PreviewLayer;
    - provides the central SnapSystem;
    - uses CoordinateSystem for coordinate conversion;
    - routes events to the active tool;
    - delegates tool lifecycle to ToolManager;
    - handles generic ESC cancellation;
    - provides interaction diagnostics.

The InteractionManager does NOT:

    - implement tool logic;
    - create concrete tools;
    - directly modify the Core model;
    - render permanent model graphics;
    - perform electrical calculations;
    - perform selection;
    - own application-level tool selection;
    - own the ToolManager lifecycle contract.

Tool Ownership
--------------
ToolManager is the single owner of tool creation, activation,
deactivation, and lifecycle.

InteractionManager only asks ToolManager for the active tool
and routes input to it.

Controller Ownership
--------------------
Controller owns application-level tool selection.

The Controller stores the requested tool identifier.

ToolManager resolves that identifier to the corresponding tool
instance.

Coordinate Ownership
--------------------
CoordinateSystem is the canonical UI coordinate conversion
boundary.

InteractionManager must not independently implement viewport
to scene conversion.

Preview Ownership
-----------------
PreviewLayer owns transient preview graphics.

Preview graphics are never part of the Core model and are not
persisted.

Snapping Ownership
------------------
SnapSystem is the centralized spatial snapping service.

Tools must obtain snapping through the InteractionManager's
SnapSystem rather than implementing independent spatial-query
logic.

Qt Architecture
---------------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QObject, Qt

from ui.canvas.coordinate_system import CoordinateSystem
from ui.canvas.preview_layer import PreviewLayer
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager


class InteractionManager(QObject):
    """
    Central input-routing service for the GridForge canvas.

    The class deliberately remains thin:

        raw input
            ↓
        coordinate conversion
            ↓
        active tool

    Transient preview and snapping services are centralized
    here so individual tools do not create competing UI
    infrastructure.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        view: Any,
        controller: Any,
        coordinate_system: Optional[CoordinateSystem] = None,
        snap_system: Optional[SnapSystem] = None,
    ) -> None:
        """
        Initialize the InteractionManager.

        Parameters
        ----------
        view:
            GridForge GraphicsView.

        controller:
            GridForge UI Controller.

        coordinate_system:
            Optional shared CoordinateSystem.

            If omitted, one is created for the supplied view.

        snap_system:
            Optional shared SnapSystem.

            If omitted, one is created for the supplied
            controller.

        Notes
        -----
        Optional dependency injection keeps this class compatible
        with the existing GraphicsView construction while allowing
        the final Canvas composition layer to provide shared
        services explicitly.
        """

        super().__init__()

        if view is None:
            raise ValueError(
                "view must not be None"
            )

        if controller is None:
            raise ValueError(
                "controller must not be None"
            )

        if not callable(
            getattr(
                controller,
                "subscribe",
                None,
            )
        ):
            raise TypeError(
                "controller must provide subscribe()"
            )

        scene = view.scene()

        if scene is None:
            raise RuntimeError(
                "InteractionManager requires a QGraphicsScene"
            )

        self.view = view
        self.controller = controller

        # ----------------------------------------------------
        # Coordinate service
        # ----------------------------------------------------
        #
        # CoordinateSystem is the single coordinate conversion
        # boundary for the canvas.
        #
        # It is intentionally independent of tool logic.
        # ----------------------------------------------------

        self.coordinate_system = (
            coordinate_system
            if coordinate_system is not None
            else CoordinateSystem(view)
        )

        # ----------------------------------------------------
        # Generic transient interaction state.
        # ----------------------------------------------------

        self.dragging: bool = False

        self.last_scene_pos: Optional[Any] = None

        # ----------------------------------------------------
        # Preview layer.
        # ----------------------------------------------------
        #
        # PreviewLayer owns temporary graphics.
        # ----------------------------------------------------

        self.preview = PreviewLayer(
            scene
        )

        # ----------------------------------------------------
        # Central snapping service.
        # ----------------------------------------------------
        #
        # The final canvas composition layer may inject a
        # SnapSystem so that CoordinateSystem/GridSystem and
        # SnapSystem share the same GridSystem instance.
        # ----------------------------------------------------

        self.snap_system = (
            snap_system
            if snap_system is not None
            else SnapSystem(
                controller=controller
            )
        )

        # ----------------------------------------------------
        # Tool manager.
        # ----------------------------------------------------
        #
        # ToolManager owns concrete tool instances and their
        # lifecycle.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=controller,
            interaction_manager=self,
            preview=self.preview,
        )

        # ----------------------------------------------------
        # Controller subscription.
        # ----------------------------------------------------

        self._connected = False

        self.controller.subscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        self._connected = True

        # ----------------------------------------------------
        # Synchronize with an already-selected tool.
        # ----------------------------------------------------

        get_tool_id = getattr(
            self.controller,
            "get_current_tool_id",
            None,
        )

        if not callable(get_tool_id):
            raise TypeError(
                "controller must provide "
                "get_current_tool_id()"
            )

        initial_tool_id = get_tool_id()

        if initial_tool_id is not None:
            self._on_tool_changed(
                initial_tool_id
            )

    # ========================================================
    # TOOL MANAGEMENT
    # ========================================================

    def _on_tool_changed(
        self,
        tool_id: Optional[str],
    ) -> None:
        """
        Handle a Controller tool-change notification.

        Controller selects the requested tool ID.

        ToolManager owns the actual tool activation lifecycle.

        InteractionManager only clears transient interaction
        state and delegates activation.
        """

        self._clear_interaction_state()

        if tool_id is None:
            self.tool_manager.deactivate()
            return

        self.tool_manager.activate(
            tool_id
        )

    # ========================================================
    # ACTIVE TOOL ACCESS
    # ========================================================

    def get_current_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the currently active tool.
        """

        return self.tool_manager.get_current_tool()

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the currently active tool.
        """

        return self.tool_manager.get_current_tool_id()

    # ========================================================
    # TRANSIENT INTERACTION STATE
    # ========================================================

    def _clear_interaction_state(
        self,
    ) -> None:
        """
        Clear all transient interaction state.

        This does not deactivate the active tool.
        """

        self.dragging = False
        self.last_scene_pos = None

        self.clear_preview()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route a mouse-press event to the active tool.

        Returns
        -------
        bool
            True when an active tool handled the event.
        """

        scene_pos = self.map_to_scene(
            event
        )

        self.last_scene_pos = scene_pos

        tool = self.get_current_tool()

        if tool is None:
            self.dragging = False
            return False

        self.dragging = True

        handler = getattr(
            tool,
            "mouse_press",
            None,
        )

        if not callable(handler):
            return False

        result = handler(
            event
        )

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Route a mouse-move event to the active tool.

        Returns
        -------
        bool
            True when an active tool handled the event.
        """

        scene_pos = self.map_to_scene(
            event
        )

        self.last_scene_pos = scene_pos

        tool = self.get_current_tool()

        if tool is None:
            return False

        handler = getattr(
            tool,
            "mouse_move",
            None,
        )

        if not callable(handler):
            return False

        result = handler(
            event
        )

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route a mouse-release event to the active tool.

        Generic drag state is cleared after the release.
        """

        scene_pos = self.map_to_scene(
            event
        )

        self.last_scene_pos = scene_pos

        tool = self.get_current_tool()

        handled = False

        if tool is not None:

            handler = getattr(
                tool,
                "mouse_release",
                None,
            )

            if callable(handler):

                result = handler(
                    event
                )

                handled = (
                    True
                    if result is None
                    else bool(result)
                )

        self.dragging = False

        return handled

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route a keyboard-press event.

        ESC is handled centrally as cancellation.

        Other keys are delegated to the active tool.
        """

        if event is None:
            raise ValueError(
                "event must not be None"
            )

        if event.key() == Qt.Key_Escape:
            handled = self.cancel_tool()

            event.accept()

            return handled

        tool = self.get_current_tool()

        if tool is None:
            return False

        handler = getattr(
            tool,
            "key_press",
            None,
        )

        if not callable(handler):
            return False

        result = handler(
            event
        )

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # KEY RELEASE
    # ========================================================

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route a keyboard-release event to the active tool.
        """

        if event is None:
            raise ValueError(
                "event must not be None"
            )

        tool = self.get_current_tool()

        if tool is None:
            return False

        handler = getattr(
            tool,
            "key_release",
            None,
        )

        if not callable(handler):
            return False

        result = handler(
            event
        )

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_tool(
        self,
    ) -> bool:
        """
        Cancel the current tool operation.

        ToolManager remains responsible for tool cancellation.

        InteractionManager always clears transient interaction
        state.
        """

        result = self.tool_manager.cancel()

        self.dragging = False
        self.last_scene_pos = None

        self.clear_preview()

        return bool(result)

    # ========================================================
    # COORDINATE CONVERSION
    # ========================================================

    def map_to_scene(
        self,
        event: Any,
    ) -> Any:
        """
        Convert a canvas mouse event position to scene space.

        CoordinateSystem is the canonical conversion service.

        No direct QGraphicsView coordinate conversion is
        performed here.
        """

        if event is None:
            raise ValueError(
                "event must not be None"
            )

        pos = getattr(
            event,
            "position",
            None,
        )

        # ----------------------------------------------------
        # Qt 6 mouse events normally expose position().
        # ----------------------------------------------------

        if callable(pos):

            return self.coordinate_system.viewport_to_scene(
                pos()
            )

        # ----------------------------------------------------
        # Compatibility with event implementations exposing
        # pos().
        # ----------------------------------------------------

        pos = getattr(
            event,
            "pos",
            None,
        )

        if callable(pos):

            return self.coordinate_system.viewport_to_scene(
                pos()
            )

        raise TypeError(
            "event must provide position() or pos()"
        )

    # ========================================================
    # CURRENT SCENE POSITION
    # ========================================================

    def get_scene_position(
        self,
    ) -> Optional[Any]:
        """
        Return the most recently known scene position.
        """

        return self.last_scene_pos

    # ========================================================
    # COORDINATE SERVICE
    # ========================================================

    def get_coordinate_system(
        self,
    ) -> CoordinateSystem:
        """
        Return the canonical CoordinateSystem.
        """

        return self.coordinate_system

    # ========================================================
    # SNAP SERVICE
    # ========================================================

    def get_snap_system(
        self,
    ) -> SnapSystem:
        """
        Return the centralized SnapSystem.

        Tools should use this service instead of implementing
        independent snapping logic.
        """

        return self.snap_system

    # ========================================================
    # PREVIEW SERVICE
    # ========================================================

    def get_preview(
        self,
    ) -> PreviewLayer:
        """
        Return the transient PreviewLayer.
        """

        return self.preview

    # --------------------------------------------------------

    def clear_preview(
        self,
    ) -> None:
        """
        Remove all transient preview graphics.
        """

        self.preview.clear()

    # ========================================================
    # TOOL DEACTIVATION
    # ========================================================

    def deactivate_tool(
        self,
    ) -> None:
        """
        Deactivate the current tool through ToolManager.

        Tool lifecycle methods are never invoked directly here.
        """

        self.tool_manager.deactivate()

        self._clear_interaction_state()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset the interaction subsystem.

        Intended for:

            - loading a new model;
            - resetting a canvas;
            - closing a workspace;
            - recovering from invalid interaction.
        """

        self.tool_manager.reset()

        self._clear_interaction_state()

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of interaction state.
        """

        active_tool = self.get_current_tool()

        return {
            "active_tool": (
                self.get_current_tool_id()
            ),
            "has_active_tool": (
                active_tool is not None
            ),
            "dragging": self.dragging,
            "last_scene_pos": (
                self.last_scene_pos
            ),
            "preview_active": (
                self.preview is not None
            ),
            "snap_system": (
                self.snap_system is not None
            ),
            "coordinate_system": (
                self.coordinate_system is not None
            ),
            "connected": self._connected,
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release interaction resources.

        Controller subscription is removed when supported.

        Tool lifecycle remains delegated to ToolManager.
        """

        if self._connected:

            unsubscribe = getattr(
                self.controller,
                "unsubscribe",
                None,
            )

            if callable(unsubscribe):

                unsubscribe(
                    "tool_changed",
                    self._on_tool_changed,
                )

            self._connected = False

        self.tool_manager.reset()

        self._clear_interaction_state()

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        tool = self.get_current_tool()

        tool_name = (
            type(tool).__name__
            if tool is not None
            else "None"
        )

        return (
            "InteractionManager("
            f"tool={tool_name}, "
            f"dragging={self.dragging}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "InteractionManager",
]
