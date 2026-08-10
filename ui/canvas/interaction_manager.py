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
#          │ raw Qt events
#          ▼
#     InteractionManager
#          │
#          │ delegates
#          ▼
#     ToolManager
#          │
#          ▼
#     Active Tool
#
#
# RESPONSIBILITIES
# ----------------
#
# The InteractionManager:
#
# - receives canvas mouse events
# - converts viewport coordinates to scene coordinates
# - forwards events to the active tool
# - owns transient interaction state
# - owns the PreviewLayer
# - tracks the last scene position
# - provides access to the SnapSystem
# - delegates tool lifecycle to ToolManager
#
#
# IT DOES NOT
# ------------
#
# - implement BusTool logic
# - implement LineTool logic
# - implement SelectTool logic
# - modify the electrical model directly
# - render permanent model graphics
# - import individual tools
# - create tool instances
# - destroy tool instances
#
#
# TOOL OWNERSHIP
# --------------
#
# ToolManager is the SINGLE owner of tool lifecycle.
#
# Therefore this class must NEVER do:
#
#     create_tool(...)
#
# Instead:
#
#     ToolManager
#          │
#          ▼
#     current_tool
#          │
#          ▼
#     InteractionManager
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
# SNAP ARCHITECTURE
# -----------------
#
# InteractionManager exposes a SnapSystem instance.
#
# Tools can use:
#
#     self.im.snap_system.snap_to_bus(...)
#
# instead of implementing independent snapping algorithms.
#
#
# QT RULE
# --------
#
# This file uses the GridForge Qt abstraction:
#
#     ui/core/qt.py
#
# It must NEVER import:
#
#     PySide6
#     PyQt6
#     PyQt5
#
# directly.
#
# ============================================================


from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QObject, Qt

from ui.canvas.preview_layer import PreviewLayer

from ui.core.snap_system import SnapSystem

from ui.core.tool_manager import ToolManager


class InteractionManager(QObject):
    """
    Central input-routing system for the GridForge canvas.

    InteractionManager is deliberately a thin layer.

    It receives raw canvas events and forwards them to the
    active tool managed by ToolManager.

    It does not contain electrical or graphical business logic.
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

            Used for:
                - coordinate conversion
                - access to QGraphicsScene

        controller:
            GridForge Controller.

            Used for:
                - application state
                - event notifications
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
        # This is only a reference to the tool owned by
        # ToolManager.
        #
        # InteractionManager does NOT create the tool.
        # ----------------------------------------------------

        self.current_tool: Optional[Any] = None

        # ----------------------------------------------------
        # Interaction state
        # ----------------------------------------------------
        #
        # These values are transient UI state.
        #
        # They must NEVER be stored in the electrical model.
        # ----------------------------------------------------

        self.dragging: bool = False

        self.last_scene_pos = None

        # ----------------------------------------------------
        # Preview layer
        # ----------------------------------------------------
        #
        # Preview graphics are temporary interaction feedback.
        #
        # Examples:
        #
        #   LineTool:
        #       start bus → cursor
        #
        #   BusTool:
        #       placement preview
        #
        #   SelectTool:
        #       selection rectangle
        #
        # Future:
        #
        #   transformer preview
        #   measurement preview
        #   connection preview
        # ----------------------------------------------------

        self.preview = PreviewLayer(
            self.view.scene()
        )

        # ----------------------------------------------------
        # Snap system
        # ----------------------------------------------------
        #
        # Centralized spatial snapping service.
        #
        # Tools should use this service instead of duplicating
        # snap calculations.
        # ----------------------------------------------------

        self.snap_system = SnapSystem(
            controller
        )

        # ----------------------------------------------------
        # Tool manager
        # ----------------------------------------------------
        #
        # ToolManager owns:
        #
        #   - tool creation
        #   - activation
        #   - deactivation
        #   - cancellation
        #   - tool switching
        #
        # InteractionManager only routes events.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=controller,
            interaction_manager=self,
            preview=self.preview,
        )

        # ----------------------------------------------------
        # Listen for Controller tool changes.
        #
        # Controller remains the source of the requested tool
        # ID.
        #
        # ToolManager owns the actual tool lifecycle.
        # ----------------------------------------------------

        self.controller.subscribe(
            "tool_changed",
            self._on_tool_changed,
        )

        # ----------------------------------------------------
        # If a tool was already selected before this manager
        # was created, synchronize with it.
        #
        # We intentionally inspect the Controller's existing
        # public state instead of requiring Controller to
        # construct or own tool instances.
        # ----------------------------------------------------

        initial_tool_id = getattr(
            self.controller,
            "current_tool",
            None,
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

        ToolManager is responsible for creating and activating
        the actual tool.

        InteractionManager only updates its reference.
        """

        # ----------------------------------------------------
        # Clear transient state from previous interaction.
        # ----------------------------------------------------

        self._clear_interaction_state()

        # ----------------------------------------------------
        # ToolManager owns the tool lifecycle.
        # ----------------------------------------------------

        self.current_tool = (
            self.tool_manager.activate(
                tool_id
            )
        )

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    def get_current_tool(self):
        """
        Return the currently active tool instance.

        Returns
        -------
        object | None
            Active tool owned by ToolManager.
        """

        return (
            self.tool_manager
            .get_current_tool()
        )

    # --------------------------------------------------------

    def get_current_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the ID of the currently active tool.
        """

        return (
            self.tool_manager
            .get_current_tool_id()
        )

    # ========================================================
    # INTERACTION STATE
    # ========================================================

    def _clear_interaction_state(
        self,
    ) -> None:
        """
        Clear temporary interaction state.

        This is called when switching tools.
        """

        self.dragging = False

        self.last_scene_pos = None

        # ----------------------------------------------------
        # Preview graphics are temporary interaction state.
        # ----------------------------------------------------

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
        """

        # ----------------------------------------------------
        # Update scene position before delegating.
        # ----------------------------------------------------

        self.last_scene_pos = (
            self.map_to_scene(event)
        )

        # ----------------------------------------------------
        # Generic interaction state.
        # ----------------------------------------------------

        self.dragging = True

        # ----------------------------------------------------
        # Obtain the active tool from ToolManager.
        # ----------------------------------------------------

        tool = (
            self.tool_manager
            .get_current_tool()
        )

        if tool is None:
            return

        # ----------------------------------------------------
        # Delegate event.
        # ----------------------------------------------------

        mouse_press = getattr(
            tool,
            "mouse_press",
            None,
        )

        if callable(mouse_press):
            mouse_press(event)

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouse_move(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-move event to the active tool.

        The scene position is updated before the tool receives
        the event.
        """

        # ----------------------------------------------------
        # Update scene position.
        # ----------------------------------------------------

        self.last_scene_pos = (
            self.map_to_scene(event)
        )

        # ----------------------------------------------------
        # Obtain active tool.
        # ----------------------------------------------------

        tool = (
            self.tool_manager
            .get_current_tool()
        )

        if tool is None:
            return

        # ----------------------------------------------------
        # Delegate event.
        # ----------------------------------------------------

        mouse_move = getattr(
            tool,
            "mouse_move",
            None,
        )

        if callable(mouse_move):
            mouse_move(event)

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

        # ----------------------------------------------------
        # Update scene position.
        # ----------------------------------------------------

        self.last_scene_pos = (
            self.map_to_scene(event)
        )

        tool = (
            self.tool_manager
            .get_current_tool()
        )

        if tool is None:
            self.dragging = False
            return

        # ----------------------------------------------------
        # Delegate event.
        # ----------------------------------------------------

        mouse_release = getattr(
            tool,
            "mouse_release",
            None,
        )

        if callable(mouse_release):
            mouse_release(event)

        # ----------------------------------------------------
        # Generic drag state ends after mouse release.
        # ----------------------------------------------------

        self.dragging = False

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route keyboard events.

        ESC is handled centrally by ToolManager.

        Other keys are optionally forwarded to the active
        tool.
        """

        # ----------------------------------------------------
        # ESC → cancel active tool operation.
        # ----------------------------------------------------

        if event.key() == Qt.Key_Escape:

            return self.cancel_tool()

        # ----------------------------------------------------
        # Other keyboard events.
        # ----------------------------------------------------

        tool = (
            self.tool_manager
            .get_current_tool()
        )

        if tool is None:
            return False

        key_press = getattr(
            tool,
            "key_press",
            None,
        )

        if not callable(key_press):
            return False

        result = key_press(event)

        # ----------------------------------------------------
        # Tools may return:
        #
        #     True  → event handled
        #     False → event not handled
        #     None  → considered handled
        # ----------------------------------------------------

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
        Route keyboard-release events to the active tool.

        This is optional and future-proofing for tools that
        need keyboard state.
        """

        tool = (
            self.tool_manager
            .get_current_tool()
        )

        if tool is None:
            return False

        key_release = getattr(
            tool,
            "key_release",
            None,
        )

        if not callable(key_release):
            return False

        result = key_release(event)

        if result is None:
            return True

        return bool(result)

    # ========================================================
    # CANCEL TOOL
    # ========================================================

    def cancel_tool(self) -> bool:
        """
        Cancel the current tool operation.

        This is the standard entry point for:

            ESC

        ToolManager performs the actual cancellation and
        preview cleanup.
        """

        result = (
            self.tool_manager.cancel()
        )

        # ----------------------------------------------------
        # Generic interaction state must also be reset.
        # ----------------------------------------------------

        self.dragging = False

        self.last_scene_pos = None

        return result

    # ========================================================
    # COORDINATE CONVERSION
    # ========================================================

    def map_to_scene(
        self,
        event: Any,
    ):
        """
        Convert a mouse event position from viewport
        coordinates to scene coordinates.

        Tools should use:

            self.im.map_to_scene(event)

        instead of directly accessing QGraphicsView.
        """

        return self.view.mapToScene(
            event.pos()
        )

    # ========================================================
    # CURRENT SCENE POSITION
    # ========================================================

    def get_scene_position(self):
        """
        Return the most recently known scene position.

        Returns
        -------
        QPointF | None
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

        Tool lifecycle must NOT be handled directly here.
        """

        self.tool_manager.deactivate()

        self.current_tool = None

        self._clear_interaction_state()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Completely reset interaction state.

        Used when:

            - loading a new model
            - resetting a canvas
            - closing a workspace
            - recovering from invalid interaction
        """

        self.tool_manager.reset()

        self.current_tool = None

        self.dragging = False

        self.last_scene_pos = None

        self.clear_preview()

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict:
        """
        Return diagnostic interaction state.
        """

        return {
            "active_tool": (
                self.get_current_tool_id()
            ),
            "has_active_tool": (
                self.get_current_tool()
                is not None
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
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return concise diagnostic representation.
        """

        tool = (
            self.get_current_tool()
        )

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
