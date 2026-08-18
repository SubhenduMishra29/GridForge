# ============================================================
# File: ui/canvas/interaction_manager.py
# GridForge V2 — Interaction Manager
# ============================================================

"""
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

InteractionManager is the canvas interaction boundary.

It routes canvas input and exposes the interaction services
required by tools.

ToolManager remains the sole authority for:

    - concrete tool ownership;
    - tool creation;
    - tool activation/deactivation;
    - tool lifecycle;
    - cancellation;
    - reset;
    - disposal.

The frozen concrete tool set is:

    SelectTool
    BusTool
    LineTool

Controller remains authoritative for application tool
selection/request state.

InteractionManager does NOT:

    - create concrete tools;
    - own concrete tool lifecycle;
    - mutate Core directly;
    - perform snapping;
    - implement selection;
    - perform rendering;
    - perform navigation;
    - subscribe to tool-change notifications;
    - replace Controller as the requested-tool authority.

GraphicsView remains the Qt event boundary.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_manager import ToolManager


class InteractionManager:
    """
    Canvas interaction coordinator.

    InteractionManager owns the interaction-layer references and
    delegates concrete tool lifecycle to ToolManager.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *,
        view: Any,
        controller: Any,
        coordinate_system: Any = None,
        snap_system: Any = None,
        preview_layer: Any = None,
        selection_manager: Any = None,
        command_manager: Any = None,
        tool_registry: Any = None,
        activate_default: bool = True,
    ) -> None:
        """
        Initialize the canvas interaction manager.

        Parameters
        ----------
        view:
            GraphicsView owning this interaction manager.

        controller:
            Authoritative application Controller.

        coordinate_system:
            Canvas CoordinateSystem.

        snap_system:
            Canvas SnapSystem.

        preview_layer:
            Canvas PreviewLayer used for transient graphics.

        selection_manager:
            SelectionManager used by interaction services/tools.

        command_manager:
            Optional CommandManager available to the interaction
            layer.

        tool_registry:
            Optional ToolRegistry supplied to ToolManager.

        activate_default:
            When True, ToolManager activates its default tool.
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

        self.coordinate_system = coordinate_system
        self.snap_system = snap_system
        self.preview_layer = preview_layer
        self.selection_manager = selection_manager
        self.command_manager = command_manager
        self.tool_registry = tool_registry

        self._disposed = False

        # ----------------------------------------------------
        # ToolManager is the sole concrete-tool authority.
        #
        # The interaction manager itself is injected so tools
        # can obtain the canvas interaction services without
        # creating their own infrastructure.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=controller,
            interaction_manager=self,
            preview=preview_layer,
            tool_registry=tool_registry,
        )

        if activate_default:
            self.tool_manager.activate_default()

    # ========================================================
    # SERVICE ACCESS
    # ========================================================

    def get_view(
        self,
    ) -> Any:
        """
        Return the owning GraphicsView.
        """

        self._ensure_active()

        return self.view

    # --------------------------------------------------------

    def get_controller(
        self,
    ) -> Any:
        """
        Return the authoritative Controller.
        """

        self._ensure_active()

        return self.controller

    # --------------------------------------------------------

    def get_coordinate_system(
        self,
    ) -> Any:
        """
        Return the canvas CoordinateSystem.
        """

        self._ensure_active()

        return self.coordinate_system

    # --------------------------------------------------------

    def get_snap_system(
        self,
    ) -> Any:
        """
        Return the canvas SnapSystem.
        """

        self._ensure_active()

        return self.snap_system

    # --------------------------------------------------------

    def get_preview_layer(
        self,
    ) -> Any:
        """
        Return the canvas PreviewLayer.
        """

        self._ensure_active()

        return self.preview_layer

    # --------------------------------------------------------

    def get_selection_manager(
        self,
    ) -> Any:
        """
        Return the SelectionManager.
        """

        self._ensure_active()

        return self.selection_manager

    # --------------------------------------------------------

    def get_command_manager(
        self,
    ) -> Any:
        """
        Return the CommandManager.
        """

        self._ensure_active()

        return self.command_manager

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
    ) -> Any:
        """
        Return the currently active concrete tool.
        """

        self._ensure_active()

        return self.tool_manager.active_tool

    # --------------------------------------------------------

    def get_active_tool(
        self,
    ) -> Any:
        """
        Return the currently active concrete tool.
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
        Return True when an active tool exists.
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
        Return True when an active tool exists.
        """

        return self.active

    # ========================================================
    # EVENT ROUTING
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-press event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.mouse_press(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-move event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.mouse_move(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-release event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.mouse_release(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a mouse-double-click event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.mouse_double_click(
                event
            )
        )

    # --------------------------------------------------------

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a key-press event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.key_press(
                event
            )
        )

    # --------------------------------------------------------

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Forward a key-release event to ToolManager.
        """

        self._validate_event(
            event
        )

        return bool(
            self.tool_manager.key_release(
                event
            )
        )

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the active tool interaction.

        ToolManager remains responsible for cancellation and
        transient preview cleanup.
        """

        self._ensure_active()

        return bool(
            self.tool_manager.cancel()
        )

    # --------------------------------------------------------

    def cancel_active_tool(
        self,
    ) -> bool:
        """
        Explicit cancellation alias.
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

        The active tool remains active.
        """

        self._ensure_active()

        self.tool_manager.reset()

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

        active_tool = (
            self.tool_manager.active_tool
        )

        return {
            "disposed": False,
            "active": active_tool is not None,
            "active_tool": (
                type(active_tool).__name__
                if active_tool is not None
                else None
            ),
            "active_tool_id": (
                self.tool_manager.active_tool_id
            ),
            "has_coordinate_system": (
                self.coordinate_system is not None
            ),
            "has_snap_system": (
                self.snap_system is not None
            ),
            "has_preview_layer": (
                self.preview_layer is not None
            ),
            "has_selection_manager": (
                self.selection_manager is not None
            ),
            "has_command_manager": (
                self.command_manager is not None
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
        Dispose the canvas interaction manager.

        Controller and Core are not owned here and are never
        disposed.
        """

        if self._disposed:
            return

        self.tool_manager.dispose()

        self._disposed = True

    # ========================================================
    # VALIDATION
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this interaction manager is not disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "InteractionManager has been disposed."
            )

    # --------------------------------------------------------

    def _validate_event(
        self,
        event: Any,
    ) -> None:
        """
        Validate and prepare an incoming interaction event.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
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
            f"active={self.active}, "
            f"tool={self.active_tool_id!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "InteractionManager",
]
