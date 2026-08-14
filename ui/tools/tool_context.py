# ============================================================
# File: ui/tools/tool_context.py
# GridForge V2 — Tool Context
# ============================================================
"""
Shared dependency context for GridForge V2 UI tools.

ToolContext provides the explicit composition boundary through
which tools receive application services.

The context is a dependency container only. It does not own
application state and does not implement tool lifecycle.

Architecture
------------

    UI Composition / Plugin
              │
              ▼
         ToolContext
          ┌──┼───────┬─────────────┐
          ▼  ▼       ▼             ▼
       Controller  CommandManager  SelectionManager
                              │
                         SnapSystem
                              │
                       RendererRegistry
                              │
                              ▼
                         Concrete Tool

Responsibilities
----------------
ToolContext:

    - hold shared UI/application dependencies;
    - provide explicit dependency injection;
    - prevent concrete tools from constructing global services;
    - provide a stable composition contract.

ToolContext does NOT:

    - mutate Core;
    - execute commands;
    - manage tool activation;
    - manage tool registration;
    - own selection;
    - render graphics;
    - perform navigation;
    - discover plugins.

The concrete tool set remains frozen to:

    SelectTool
    BusTool
    LineTool

Qt
--
This module intentionally contains no direct Qt dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class ToolContext:
    """
    Immutable dependency context shared by UI tools.

    Parameters
    ----------
    controller:
        Authoritative application/controller boundary.

    command_manager:
        CommandManager used by mutating tools.

    selection_manager:
        SelectionManager used by SelectTool.

    snap_system:
        SnapSystem used by tools requiring topology-aware
        connection snapping.

    renderer_registry:
        RendererRegistry available to tools when renderer
        coordination is explicitly required.

    canvas_controller:
        Optional CanvasController for canvas-level interaction
        coordination.

    interaction_controller:
        Optional InteractionController for interaction routing.

    navigation_controller:
        Optional NavigationController for tools that need to
        request navigation through the controller layer.

    Notes
    -----
    Optional dependencies are intentionally explicit. A tool
    should fail clearly when it requires a dependency that was
    not supplied rather than constructing or discovering it.
    """

    controller: Any

    command_manager: Optional[Any] = None
    selection_manager: Optional[Any] = None
    snap_system: Optional[Any] = None
    renderer_registry: Optional[Any] = None

    canvas_controller: Optional[Any] = None
    interaction_controller: Optional[Any] = None
    navigation_controller: Optional[Any] = None

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(
        self,
    ) -> None:
        """
        Validate mandatory dependencies.
        """

        if self.controller is None:
            raise ValueError(
                "ToolContext.controller must not be None."
            )

    # ========================================================
    # REQUIRED DEPENDENCY ACCESS
    # ========================================================

    def require_command_manager(
        self,
    ) -> Any:
        """
        Return CommandManager or raise a clear configuration error.
        """

        return self._require(
            self.command_manager,
            "command_manager",
        )

    # --------------------------------------------------------

    def require_selection_manager(
        self,
    ) -> Any:
        """
        Return SelectionManager or raise a clear configuration
        error.
        """

        return self._require(
            self.selection_manager,
            "selection_manager",
        )

    # --------------------------------------------------------

    def require_snap_system(
        self,
    ) -> Any:
        """
        Return SnapSystem or raise a clear configuration error.
        """

        return self._require(
            self.snap_system,
            "snap_system",
        )

    # --------------------------------------------------------

    def require_renderer_registry(
        self,
    ) -> Any:
        """
        Return RendererRegistry or raise a clear configuration
        error.
        """

        return self._require(
            self.renderer_registry,
            "renderer_registry",
        )

    # --------------------------------------------------------

    def require_canvas_controller(
        self,
    ) -> Any:
        """
        Return CanvasController or raise a clear configuration
        error.
        """

        return self._require(
            self.canvas_controller,
            "canvas_controller",
        )

    # --------------------------------------------------------

    def require_interaction_controller(
        self,
    ) -> Any:
        """
        Return InteractionController or raise a clear
        configuration error.
        """

        return self._require(
            self.interaction_controller,
            "interaction_controller",
        )

    # --------------------------------------------------------

    def require_navigation_controller(
        self,
    ) -> Any:
        """
        Return NavigationController or raise a clear
        configuration error.
        """

        return self._require(
            self.navigation_controller,
            "navigation_controller",
        )

    # ========================================================
    # PRESENCE CHECKS
    # ========================================================

    @property
    def has_command_manager(
        self,
    ) -> bool:
        """
        Return whether CommandManager is configured.
        """

        return self.command_manager is not None

    # --------------------------------------------------------

    @property
    def has_selection_manager(
        self,
    ) -> bool:
        """
        Return whether SelectionManager is configured.
        """

        return self.selection_manager is not None

    # --------------------------------------------------------

    @property
    def has_snap_system(
        self,
    ) -> bool:
        """
        Return whether SnapSystem is configured.
        """

        return self.snap_system is not None

    # --------------------------------------------------------

    @property
    def has_renderer_registry(
        self,
    ) -> bool:
        """
        Return whether RendererRegistry is configured.
        """

        return self.renderer_registry is not None

    # --------------------------------------------------------

    @property
    def has_canvas_controller(
        self,
    ) -> bool:
        """
        Return whether CanvasController is configured.
        """

        return self.canvas_controller is not None

    # --------------------------------------------------------

    @property
    def has_interaction_controller(
        self,
    ) -> bool:
        """
        Return whether InteractionController is configured.
        """

        return self.interaction_controller is not None

    # --------------------------------------------------------

    @property
    def has_navigation_controller(
        self,
    ) -> bool:
        """
        Return whether NavigationController is configured.
        """

        return self.navigation_controller is not None

    # ========================================================
    # DEPENDENCY VALIDATION
    # ========================================================

    def validate_for_select_tool(
        self,
    ) -> None:
        """
        Validate dependencies required by SelectTool.
        """

        self._require(
            self.selection_manager,
            "selection_manager",
        )

    # --------------------------------------------------------

    def validate_for_bus_tool(
        self,
    ) -> None:
        """
        Validate dependencies required by BusTool.
        """

        self._require(
            self.command_manager,
            "command_manager",
        )

    # --------------------------------------------------------

    def validate_for_line_tool(
        self,
    ) -> None:
        """
        Validate dependencies required by LineTool.
        """

        self._require(
            self.command_manager,
            "command_manager",
        )

        self._require(
            self.snap_system,
            "snap_system",
        )

    # --------------------------------------------------------

    def validate_for_tool(
        self,
        tool_id: str,
    ) -> None:
        """
        Validate the dependency contract for one of the frozen
        concrete tools.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        if tool_id == "select":
            self.validate_for_select_tool()
            return

        if tool_id == "bus":
            self.validate_for_bus_tool()
            return

        if tool_id == "line":
            self.validate_for_line_tool()
            return

        raise ValueError(
            f"Unknown GridForge tool id: {tool_id!r}."
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, bool]:
        """
        Return dependency-presence diagnostics.

        Object references themselves are deliberately excluded
        from the diagnostic state.
        """

        return {
            "has_controller": self.controller is not None,
            "has_command_manager": self.has_command_manager,
            "has_selection_manager": self.has_selection_manager,
            "has_snap_system": self.has_snap_system,
            "has_renderer_registry": self.has_renderer_registry,
            "has_canvas_controller": self.has_canvas_controller,
            "has_interaction_controller": (
                self.has_interaction_controller
            ),
            "has_navigation_controller": (
                self.has_navigation_controller
            ),
        }

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    @staticmethod
    def _require(
        value: Any,
        dependency_name: str,
    ) -> Any:
        """
        Return a dependency or raise a descriptive error.
        """

        if value is None:
            raise RuntimeError(
                f"ToolContext dependency "
                f"{dependency_name!r} is not configured."
            )

        return value


__all__ = [
    "ToolContext",
]
