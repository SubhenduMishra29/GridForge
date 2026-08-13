"""
GridForge V2 — Canvas Interaction Manager
=========================================

File:
    ui/canvas/interaction_manager.py

Purpose
-------
Central input-routing layer for the GridForge canvas.

The InteractionManager receives normalized canvas input from
GraphicsView and delegates interaction to the currently active
tool.

Architecture
------------

    QGraphicsView
         │
         │ raw Qt events
         ▼
    InteractionManager
         │
         ├── PreviewLayer
         │
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
    - converts viewport coordinates to scene coordinates;
    - routes events to the active tool;
    - owns transient interaction state;
    - owns the PreviewLayer;
    - exposes the central SnapSystem;
    - delegates tool lifecycle to ToolManager;
    - handles generic ESC cancellation;
    - provides interaction diagnostics.

The InteractionManager does NOT:

    - implement tool logic;
    - create individual tools;
    - destroy individual tools;
    - modify the Core model directly;
    - render permanent model graphics;
    - import concrete tools;
    - perform electrical calculations;
    - own tool lifecycle.

Tool Ownership
--------------
ToolManager is the single owner of tool creation and lifecycle.

InteractionManager obtains the active tool from ToolManager
and routes events to it.

Controller Ownership
--------------------
Controller owns application-level tool selection.

The Controller stores:

    current_tool_id

ToolManager resolves that identifier to the actual tool
instance.

Qt Architecture
---------------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QObject,
    Qt,
)

from ui.canvas.preview_layer import PreviewLayer
from ui.core.snap_system import SnapSystem
from ui.core.tool_manager import ToolManager


class InteractionManager(QObject):
    """
    Central input-routing system for the GridForge canvas.

    The InteractionManager is deliberately thin.

    It translates canvas-level input into calls on the active
    tool while keeping transient interaction services such as
    preview graphics and snapping centralized.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        view: Any,
        controller: Any,
    ) -> None:
        """
        Initialize the InteractionManager.

        Parameters
        ----------
        view:
            GridForge GraphicsView instance.

        controller:
            GridForge UI Controller.
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

        self.view = view
        self.controller = controller

        # ----------------------------------------------------
        # Generic transient interaction state
        # ----------------------------------------------------

        self.dragging: bool = False

        self.last_scene_pos: Optional[Any] = None

        # ----------------------------------------------------
        # Preview layer
        # ----------------------------------------------------
        #
        # Preview graphics are transient.
        #
        # They are not part of the domain model and must not
        # be placed under RenderSystem ownership.
        # ----------------------------------------------------

        scene = self.view.scene()

        if scene is None:
            raise RuntimeError(
                "InteractionManager requires a QGraphicsScene"
            )

        self.preview = PreviewLayer(
            scene
        )

        # ----------------------------------------------------
        # Central snapping service
        # ----------------------------------------------------
        #
        # Tools obtain snapping through InteractionManager.
        #
        # Individual tools must not create competing snap
        # systems.
        # ----------------------------------------------------

        self.snap_system = SnapSystem(
            controller=controller
        )

        # ----------------------------------------------------
        # Tool manager
        # ----------------------------------------------------
        #
        # ToolManager owns tool instances and lifecycle.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=controller,
            interaction_manager=self,
            preview=self.preview,
        )

        # ----------------------------------------------------
        # Controller subscription
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
        React to a Controller tool-change event.

        Controller owns the requested tool ID.

        ToolManager owns actual tool activation and lifecycle.

        InteractionManager only resets transient interaction
        state and asks ToolManager to activate the requested
        tool.
        """

        # ----------------------------------------------------
        # Switching tools invalidates transient interaction
        # state belonging to the previous tool.
        # ----------------------------------------------------

        self._clear_interaction_state()

        # ----------------------------------------------------
        # None means no active tool.
        # ----------------------------------------------------

        if tool_id is None:
            self.tool_manager.deactivate()
            return

        # ----------------------------------------------------
        # ToolManager owns activation.
        # ----------------------------------------------------

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

        ToolManager remains authoritative.
        """

        return self.tool_manager.get_current_tool()

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the ID of the currently active tool.
        """

        return self.tool_manager.get_current_tool_id()

    # ========================================================
    # INTERACTION STATE
    # ========================================================

    def _clear_interaction_state(
        self,
    ) -> None:
        """
        Clear transient interaction state.
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
    ) -> None:
        """
        Route a mouse-press event to the active tool.

        The event itself remains owned by the input layer;
        coordinate conversion is exposed through
        map_to_scene().
        """

        self.last_scene_pos = self.map_to_scene(
            event
        )

        tool = self.get_current_tool()

        if tool is None:
            self.dragging = False
            return

        self.dragging = True

        handler = getattr(
            tool,
            "mouse_press",
            None,
        )

        if callable(handler):
            handler(event)

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-move event to the active tool.
        """

        self.last_scene_pos = self.map_to_scene(
            event
        )

        tool = self.get_current_tool()

        if tool is None:
            return

        handler = getattr(
            tool,
            "mouse_move",
            None,
        )

        if callable(handler):
            handler(event)

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-release event to the active tool.

        Generic drag state ends after the release regardless
        of whether the active tool implements mouse_release().
        """

        self.last_scene_pos = self.map_to_scene(
            event
        )

        tool = self.get_current_tool()

        if tool is not None:

            handler = getattr(
                tool,
                "mouse_release",
                None,
            )

            if callable(handler):
                handler(event)

        self.dragging = False

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

        Returns
        -------
        bool
            True when the event was handled.
        """

        if event.key() == Qt.Key_Escape:
            return self.cancel_tool()

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

        result = handler(event)

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

        Returns
        -------
        bool
            True when the event was handled.
        """

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

        result = handler(event)

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # CANCEL TOOL
    # ========================================================

    def cancel_tool(
        self,
    ) -> bool:
        """
        Cancel the current tool operation.

        ToolManager owns the actual cancellation lifecycle.

        Transient InteractionManager state is always cleared.
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
        Convert a viewport event position into scene coordinates.

        This is the canonical coordinate conversion boundary
        for canvas interaction.
        """

        if event is None:
            raise ValueError(
                "event must not be None"
            )

        pos = getattr(
            event,
            "pos",
            None,
        )

        if not callable(pos):
            raise TypeError(
                "event must provide callable pos()"
            )

        return self.view.mapToScene(
            pos()
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
    # PREVIEW CONTROL
    # ========================================================

    def clear_preview(
        self,
    ) -> None:
        """
        Clear all transient preview graphics.
        """

        if self.preview is not None:
            self.preview.clear()

    # ========================================================
    # DEACTIVATE TOOL
    # ========================================================

    def deactivate_tool(
        self,
    ) -> None:
        """
        Deactivate the current tool through ToolManager.

        InteractionManager does not invoke tool lifecycle
        methods directly.
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
        Reset the complete transient interaction state.

        Intended for:

            - loading a new model;
            - resetting a canvas;
            - closing a workspace;
            - recovering from invalid interaction.
        """

        self.tool_manager.reset()

        self._clear_interaction_state()

    # ========================================================
    # SNAP ACCESS
    # ========================================================

    def get_snap_system(
        self,
    ) -> SnapSystem:
        """
        Return the central SnapSystem.

        Tools should use this service instead of implementing
        independent snapping systems.
        """

        return self.snap_system

    # ========================================================
    # PREVIEW ACCESS
    # ========================================================

    def get_preview(
        self,
    ) -> PreviewLayer:
        """
        Return the transient PreviewLayer.
        """

        return self.preview

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
            "connected": self._connected,
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release interaction resources and disconnect from the
        Controller.

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
