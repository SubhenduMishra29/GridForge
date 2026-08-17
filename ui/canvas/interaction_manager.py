# ============================================================
# File: ui/canvas/interaction_manager.py
# GridForge V2 — Interaction Manager
# ============================================================

"""
GridForge V2 Interaction Manager
================================

Canvas interaction coordinator for GridForge V2.

Architecture
------------

    GraphicsView
         │
         ▼
    InteractionManager
         │
         ▼
      ToolManager
         │
         ▼
      Active Tool
         │
         ▼
      Controller
         │
         ▼
        Core

Responsibilities
----------------

InteractionManager:

    - own the ToolManager used by the canvas;
    - route raw canvas interaction events to ToolManager;
    - expose the active tool;
    - expose the active tool identifier;
    - expose interaction state;
    - coordinate reset/cancellation;
    - provide deterministic diagnostics;
    - manage its own lifecycle.

InteractionManager does NOT:

    - implement concrete tool behavior;
    - construct individual tools directly;
    - perform electrical calculations;
    - modify Core objects directly;
    - perform navigation;
    - implement rendering;
    - own persistent application selection;
    - interpret Qt-specific event semantics beyond forwarding them.

Tool ownership
--------------

ToolManager remains the concrete tool authority.

The frozen GridForge V2 tool set is:

    SelectTool
    BusTool
    LineTool

Navigation ownership remains with NavigationController.

GraphicsView remains the Qt event boundary.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_manager import ToolManager


# ============================================================
# INTERACTION MANAGER
# ============================================================


class InteractionManager:
    """
    Coordinate canvas interaction through ToolManager.

    InteractionManager is the authoritative interaction-layer
    owner for the canvas. Tool lifecycle and concrete tool ownership
    remain delegated to ToolManager.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *,
        view: Any,
        controller: Any,
        command_manager: Optional[Any] = None,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
        renderer_registry: Optional[Any] = None,
        activate_default: bool = True,
    ) -> None:
        """
        Initialize the canvas interaction manager.

        Parameters
        ----------
        view:
            GraphicsView owning this interaction manager.

        controller:
            Authoritative application/UI controller.

        command_manager:
            Optional CommandManager supplied to ToolManager.

        selection_manager:
            Optional SelectionManager supplied to ToolManager.

        snap_system:
            Optional SnapSystem supplied to ToolManager.

        renderer_registry:
            Optional RendererRegistry supplied to ToolManager.

        activate_default:
            When True, ToolManager activates SelectTool during
            initialization.
        """

        if view is None:
            raise ValueError(
                "view must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self.view = view
        self.controller = controller

        self.command_manager = command_manager
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self.renderer_registry = renderer_registry

        self._disposed = False

        self.tool_manager = ToolManager(
            controller=controller,
            command_manager=command_manager,
            selection_manager=selection_manager,
            snap_system=snap_system,
            renderer_registry=renderer_registry,
            activate_default=activate_default,
        )

    # ========================================================
    # TOOL MANAGER ACCESS
    # ========================================================

    def get_tool_manager(
        self,
    ) -> ToolManager:
        """
        Return the underlying ToolManager.
        """

        self._ensure_active()

        return self.tool_manager

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    @property
    def active_tool(
        self,
    ):
        """
        Return the currently active concrete tool.
        """

        self._ensure_active()

        return self.tool_manager.active_tool

    # --------------------------------------------------------

    def get_active_tool(
        self,
    ):
        """
        Return the currently active concrete tool.

        Returns None when no tool is active.
        """

        self._ensure_active()

        return self.tool_manager.active_tool

    # --------------------------------------------------------

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the currently active tool.
        """

        self._ensure_active()

        return self.tool_manager.active_tool_id

    # --------------------------------------------------------

    def get_active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the identifier of the currently active tool.
        """

        self._ensure_active()

        return self.tool_manager.active_tool_id

    # ========================================================
    # INTERACTION STATE
    # ========================================================

    @property
    def active(
        self,
    ) -> bool:
        """
        Return True when an active tool is available.
        """

        if self._disposed:
            return False

        return (
            self.tool_manager.active_tool is not None
        )

    # --------------------------------------------------------

    def is_active(
        self,
    ) -> bool:
        """
        Return True when an active tool is available.
        """

        return self.active

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
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.mouse_press(
                event
            )
        )

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
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.mouse_move(
                event
            )
        )

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route a mouse-release event to the active tool.

        Returns
        -------
        bool
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.mouse_release(
                event
            )
        )

    # ========================================================
    # MOUSE DOUBLE CLICK
    # ========================================================

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Route a mouse-double-click event to the active tool.

        Returns
        -------
        bool
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.mouse_double_click(
                event
            )
        )

    # ========================================================
    # KEY PRESS
    # ========================================================

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route a keyboard-press event to the active tool.

        Returns
        -------
        bool
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.key_press(
                event
            )
        )

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
            True when the active tool consumes the event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        return bool(
            self.tool_manager.key_release(
                event
            )
        )

    # ========================================================
    # TOOL SWITCHING
    # ========================================================

    def activate_tool(
        self,
        tool_id: str,
    ):
        """
        Activate a registered tool through ToolManager.
        """

        self._ensure_active()

        return self.tool_manager.activate_tool(
            tool_id
        )

    # --------------------------------------------------------

    def select_tool(
        self,
    ):
        """
        Activate SelectTool.
        """

        self._ensure_active()

        return self.tool_manager.select_tool()

    # --------------------------------------------------------

    def bus_tool(
        self,
    ):
        """
        Activate BusTool.
        """

        self._ensure_active()

        return self.tool_manager.bus_tool()

    # --------------------------------------------------------

    def line_tool(
        self,
    ):
        """
        Activate LineTool.
        """

        self._ensure_active()

        return self.tool_manager.line_tool()

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the active tool's transient interaction.

        Returns
        -------
        bool
            True when an active tool handled cancellation.
        """

        self._ensure_active()

        return bool(
            self.tool_manager.cancel_active_tool()
        )

    # --------------------------------------------------------

    def cancel_active_tool(
        self,
    ) -> bool:
        """
        Cancel the active tool.

        This is an explicit alias for ``cancel()``.
        """

        return self.cancel()

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient interaction state.

        Tool ownership and lifecycle remain delegated to
        ToolManager.
        """

        self._ensure_active()

        self.tool_manager.reset_active_tool()

    # ========================================================
    # TOOL STATE
    # ========================================================

    def get_active_tool_state(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Return diagnostic state for the active tool.
        """

        self._ensure_active()

        return (
            self.tool_manager.get_active_tool_state()
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a deterministic interaction diagnostic snapshot.
        """

        if self._disposed:
            return {
                "disposed": True,
                "active": False,
                "active_tool": None,
                "active_tool_id": None,
                "tool_manager": None,
            }

        return {
            "disposed": False,
            "active": self.is_active(),
            "active_tool": (
                type(self.active_tool).__name__
                if self.active_tool is not None
                else None
            ),
            "active_tool_id": (
                self.active_tool_id
            ),
            "tool_manager": (
                self.tool_manager.get_state()
            ),
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose the canvas-owned interaction manager.

        The application controller and Core are not owned here and
        are therefore not disposed.
        """

        if self._disposed:
            return

        self.tool_manager.dispose()

        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the interaction manager has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "InteractionManager has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        if self._disposed:
            return (
                "InteractionManager("
                "disposed=True"
                ")"
            )

        return (
            "InteractionManager("
            f"active={self.is_active()}, "
            f"tool={self.active_tool_id!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "InteractionManager",
]
