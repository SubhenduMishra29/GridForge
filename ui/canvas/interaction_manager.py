# ============================================================
# File: ui/canvas/interaction_manager.py
# GridForge Canvas Interaction Manager
# ============================================================
#
# PURPOSE
# -------
# Central input-routing layer for the GridForge canvas.
#
# The InteractionManager sits between:
#
#     QGraphicsView
#          │
#          │ raw Qt mouse events
#          ▼
#     InteractionManager
#          │
#          │ delegates
#          ▼
#     Active Tool
#
#
# RESPONSIBILITIES
# ----------------
#
# The InteractionManager:
#
#     - receives canvas mouse events
#     - converts viewport coordinates to scene coordinates
#     - obtains the active tool from the Controller
#     - forwards events to that tool
#     - owns transient interaction state
#     - owns the preview layer
#     - tracks the last scene position
#
#
# IT DOES NOT:
# ------------
#
#     - implement BusTool logic
#     - implement LineTool logic
#     - implement SelectTool logic
#     - modify the electrical model directly
#     - render permanent model graphics
#     - know which concrete tools exist
#     - import individual tools
#
#
# TOOL ARCHITECTURE
# -----------------
#
# Controller
#     │
#     │ current_tool_id
#     ▼
# ToolRegistry
#     │
#     │ tool instance
#     ▼
# InteractionManager
#     │
#     ▼
# Active Tool
#
#
# PREVIEW ARCHITECTURE
# --------------------
#
# InteractionManager owns the PreviewLayer because preview
# graphics are temporary interaction feedback.
#
# They are NOT part of the persistent model.
#
#
# IMPORTANT
# ---------
#
# This file uses the GridForge Qt abstraction:
#
#     ui/core/qt.py
#
# It must never import PySide6, PyQt6, or PyQt5 directly.
#
# ============================================================

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QObject

from ui.canvas.preview_layer import PreviewLayer


class InteractionManager(QObject):
    """
    Central input-routing system for the GridForge canvas.

    The InteractionManager does not implement tool behavior.

    It simply determines which tool is active and forwards
    interaction events to that tool.
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

            The view is used for coordinate conversion and
            access to the graphics scene.

        controller:
            GridForge Controller.

            The Controller provides:

                - active tool state
                - tool registry
                - application events
        """

        super().__init__()

        # ----------------------------------------------------
        # Core references
        # ----------------------------------------------------

        self.view = view
        self.controller = controller

        # ----------------------------------------------------
        # Active tool
        # ----------------------------------------------------
        #
        # This stores the actual runtime tool instance.
        #
        # The Controller remains responsible for deciding which
        # tool ID is active.
        #
        # InteractionManager resolves that ID through:
        #
        #     controller.get_current_tool()
        # ----------------------------------------------------

        self.current_tool: Optional[Any] = None

        # ----------------------------------------------------
        # Interaction state
        # ----------------------------------------------------
        #
        # These values describe temporary interaction state.
        #
        # They must NOT be stored in the domain model.
        # ----------------------------------------------------

        self.dragging: bool = False

        self.last_scene_pos = None

        # ----------------------------------------------------
        # Preview layer
        # ----------------------------------------------------
        #
        # Preview graphics are transient.
        #
        # Examples:
        #
        #     LineTool:
        #         start bus → mouse cursor
        #
        #     BusTool:
        #         placement preview
        #
        #     Future:
        #         transformer preview
        #         selection rectangle
        # ----------------------------------------------------

        self.preview = PreviewLayer(
            self.view.scene()
        )

        # ----------------------------------------------------
        # Subscribe to controller tool changes.
        # ----------------------------------------------------

        self.controller.subscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        # ----------------------------------------------------
        # Resolve the initial tool if one was already selected.
        #
        # This is useful when Controller state is configured
        # before InteractionManager is created.
        # ----------------------------------------------------

        initial_tool_id = (
            self.controller.get_current_tool_id()
        )

        if initial_tool_id is not None:
            self._on_tool_changed(
                initial_tool_id
            )

    # ========================================================
    # TOOL MANAGEMENT
    # ========================================================

    def _on_tool_changed(
        self,
        tool_id: str,
    ) -> None:
        """
        React to a Controller tool-change event.

        The InteractionManager does not construct tools itself.

        It asks the Controller for the active runtime instance.

        This preserves the separation:

            Controller
                ↓
            ToolRegistry
                ↓
            Tool instance
                ↓
            InteractionManager
        """

        # ----------------------------------------------------
        # Clear state belonging to the previous tool.
        # ----------------------------------------------------

        self._clear_interaction_state()

        # ----------------------------------------------------
        # Resolve active tool from Controller.
        # ----------------------------------------------------

        self.current_tool = (
            self.controller.get_current_tool()
        )

        # ----------------------------------------------------
        # Notify the newly activated tool if it provides an
        # optional activation hook.
        #
        # This is intentionally duck-typed.
        #
        # Tools do not have to implement activate().
        # ----------------------------------------------------

        if self.current_tool is not None:

            activate = getattr(
                self.current_tool,
                "activate",
                None,
            )

            if callable(activate):
                activate()

    # ========================================================
    # INTERACTION STATE
    # ========================================================

    def _clear_interaction_state(self) -> None:
        """
        Clear transient interaction state.

        Called whenever the active tool changes.
        """

        self.dragging = False
        self.last_scene_pos = None

        # ----------------------------------------------------
        # Preview belongs to interaction state and therefore
        # must disappear when the active tool changes.
        # ----------------------------------------------------

        if self.preview is not None:
            self.preview.clear()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-press event to the active tool.

        The InteractionManager does not interpret the event.

        Tool-specific behavior belongs entirely to the active
        tool.
        """

        # ----------------------------------------------------
        # Update scene position.
        # ----------------------------------------------------

        self.last_scene_pos = self.map_to_scene(
            event
        )

        # ----------------------------------------------------
        # Track interaction state.
        # ----------------------------------------------------

        self.dragging = True

        # ----------------------------------------------------
        # Delegate to active tool.
        # ----------------------------------------------------

        tool = self.current_tool

        if tool is None:
            return

        tool.mouse_press(event)

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-move event to the active tool.

        The last scene position is updated before the tool
        receives the event.

        This allows tools such as LineTool to implement:

            snap-to-bus
            hover detection
            preview lines
        """

        self.last_scene_pos = self.map_to_scene(
            event
        )

        tool = self.current_tool

        if tool is None:
            return

        tool.mouse_move(event)

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-release event to the active tool.
        """

        self.last_scene_pos = self.map_to_scene(
            event
        )

        tool = self.current_tool

        if tool is None:
            self.dragging = False
            return

        tool.mouse_release(event)

        # ----------------------------------------------------
        # The tool has received the complete release event.
        # InteractionManager can now reset generic drag state.
        # ----------------------------------------------------

        self.dragging = False

    # ========================================================
    # COORDINATE CONVERSION
    # ========================================================

    def map_to_scene(
        self,
        event: Any,
    ):
        """
        Convert a Qt mouse event position from viewport
        coordinates into scene coordinates.

        This method centralizes coordinate conversion so tools
        do not need direct knowledge of QGraphicsView.

        Example
        -------

            pos = interaction_manager.map_to_scene(event)
        """

        return self.view.mapToScene(
            event.pos()
        )

    # ========================================================
    # CURRENT POSITION
    # ========================================================

    def get_scene_position(self):
        """
        Return the most recently known scene position.

        Returns
        -------
        QPointF | None
            Last scene position.
        """

        return self.last_scene_pos

    # ========================================================
    # PREVIEW CONTROL
    # ========================================================

    def clear_preview(self) -> None:
        """
        Clear all temporary preview graphics.

        Tools may use this instead of accessing the PreviewLayer
        directly when appropriate.
        """

        self.preview.clear()

    # ========================================================
    # DEACTIVATE CURRENT TOOL
    # ========================================================

    def deactivate_tool(self) -> None:
        """
        Deactivate the currently active tool if it provides
        an optional deactivate() method.

        This is useful when switching tools or shutting down
        interaction.
        """

        tool = self.current_tool

        if tool is not None:

            deactivate = getattr(
                tool,
                "deactivate",
                None,
            )

            if callable(deactivate):
                deactivate()

        self._clear_interaction_state()

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        tool_name = (
            type(self.current_tool).__name__
            if self.current_tool is not None
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
```
