# ============================================================
# File: ui/controllers/tool_controller.py
# GridForge V2 — UI Tool Controller
# ============================================================
"""
UI Tool Controller for GridForge V2.

Architecture
------------

    UI / Toolbar
         │
         ▼
    ToolController
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

Purpose
-------
ToolController is the UI orchestration boundary for tool
selection and tool lifecycle requests.

The actual tool lifecycle remains exclusively owned by
ToolManager.

Current GridForge V2 concrete tools remain intentionally
limited to:

    SelectTool
    BusTool
    LineTool

ToolController does not discover tools and does not create
concrete tool implementations.

Responsibilities
----------------
ToolController:

    - activate a registered tool;
    - deactivate the current tool;
    - switch tools;
    - expose the active tool;
    - expose available registered tools;
    - reset/cancel the active interaction;
    - provide tool diagnostics.

ToolController does NOT:

    - implement tool behavior;
    - create tool instances directly;
    - maintain a second active-tool state;
    - perform snapping;
    - perform selection;
    - perform navigation;
    - render graphics;
    - modify Core state directly;
    - discover plugins;
    - bypass ToolManager.

Authority
---------
ToolManager remains authoritative for:

    - concrete tool construction;
    - tool registration;
    - active tool;
    - tool activation/deactivation;
    - tool input routing;
    - cancellation;
    - reset;
    - tool lifecycle.

InteractionManager, where present, remains responsible for
canvas interaction orchestration.

Qt Architecture
---------------
This module contains no direct Qt imports.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.tools.tool_manager import ToolManager


class ToolController:
    """
    Thin UI orchestration adapter around ToolManager.

    No tool state is duplicated here.

    ToolManager is the sole authority for concrete tool
    lifecycle and active-tool state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        tool_manager: ToolManager,
    ) -> None:
        """
        Initialize the ToolController.

        Parameters
        ----------
        tool_manager:
            Existing authoritative ToolManager.

        Notes
        -----
        The ToolManager is externally owned and is not copied,
        replaced, or disposed by this controller.
        """

        if tool_manager is None:
            raise ValueError(
                "tool_manager must not be None."
            )

        if not isinstance(
            tool_manager,
            ToolManager,
        ):
            raise TypeError(
                "tool_manager must be a ToolManager."
            )

        self.tool_manager = tool_manager
        self._disposed = False

    # ========================================================
    # MANAGER ACCESS
    # ========================================================

    def get_tool_manager(
        self,
    ) -> ToolManager:
        """
        Return the authoritative ToolManager.
        """

        self._ensure_active()

        return self.tool_manager

    # ========================================================
    # TOOL ACTIVATION
    # ========================================================

    def activate(
        self,
        tool_id: str,
    ) -> Any:
        """
        Activate a registered tool.

        ToolManager owns validation and lifecycle semantics.
        """

        self._ensure_active()
        self._validate_tool_id(tool_id)

        return self.tool_manager.activate_tool(
            tool_id
        )

    # --------------------------------------------------------

    def activate_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Explicit alias for activate().
        """

        return self.activate(
            tool_id
        )

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate the currently active tool.

        No active tool remains after this operation.
        """

        self._ensure_active()

        self.tool_manager.deactivate_active_tool()

    # --------------------------------------------------------

    def deactivate_tool(
        self,
    ) -> None:
        """
        Explicit alias for deactivate().
        """

        self.deactivate()

    # ========================================================
    # SWITCH
    # ========================================================

    def switch(
        self,
        tool_id: str,
    ) -> Any:
        """
        Switch to the specified registered tool.

        ToolManager owns the transition semantics.
        """

        self._ensure_active()
        self._validate_tool_id(tool_id)

        return self.tool_manager.activate_tool(
            tool_id
        )

    # --------------------------------------------------------

    def switch_tool(
        self,
        tool_id: str,
    ) -> Any:
        """
        Explicit alias for switch().
        """

        return self.switch(
            tool_id
        )

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    def get_active_tool(
        self,
    ) -> Optional[Any]:
        """
        Return the currently active ToolManager tool.

        No active-tool state is maintained by this controller.
        """

        self._ensure_active()

        return self.tool_manager.active_tool

    # --------------------------------------------------------

    def get_active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the authoritative active ToolManager tool ID.
        """

        self._ensure_active()

        return self.tool_manager.active_tool_id

    # ========================================================
    # AVAILABLE TOOLS
    # ========================================================

    def get_tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered ToolManager tool identifiers.

        ToolManager provides deterministic ordering.
        """

        self._ensure_active()

        return tuple(
            self.tool_manager.tool_ids()
        )

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether ToolManager has the specified tool.
        """

        self._ensure_active()
        self._validate_tool_id(tool_id)

        return self.tool_manager.has_tool(
            tool_id
        )

    # ========================================================
    # TOOL INSTANCE
    # ========================================================

    def get_tool(
        self,
        tool_id: str,
    ) -> Optional[Any]:
        """
        Return a registered tool.

        ToolController never creates missing tools.
        """

        self._ensure_active()
        self._validate_tool_id(tool_id)

        if not self.tool_manager.has_tool(
            tool_id
        ):
            return None

        return self.tool_manager.get_tool(
            tool_id
        )

    # ========================================================
    # RESET / CANCEL
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient state of the active tool.

        ToolManager owns the operation.
        """

        self._ensure_active()

        self.tool_manager.reset_active_tool()

    # --------------------------------------------------------

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the active tool interaction.

        Returns
        -------
        bool
            True when the active tool handled cancellation.
        """

        self._ensure_active()

        return bool(
            self.tool_manager.cancel_active_tool()
        )

    # ========================================================
    # DEFAULT TOOL
    # ========================================================

    def activate_default(
        self,
    ) -> Any:
        """
        Activate the canonical GridForge default tool.

        The default tool is defined by ToolManager.

        GridForge V2 currently defines SelectTool as the
        ToolManager default.
        """

        self._ensure_active()

        return self.tool_manager.select_tool()

    # ========================================================
    # TOOL COLLECTION
    # ========================================================

    def activate_first_registered(
        self,
    ) -> Any:
        """
        Activate the first registered tool.

        Registration order is supplied by ToolManager.

        This method does not define a preferred GridForge tool.
        """

        self._ensure_active()

        tool_ids = self.get_tool_ids()

        if not tool_ids:
            raise LookupError(
                "ToolManager has no registered tools."
            )

        return self.activate(
            tool_ids[0]
        )

    # ========================================================
    # EVENT ROUTING
    # ========================================================

    def mouse_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse press to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.mouse_press(
            event
        )

    # --------------------------------------------------------

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse move to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.mouse_move(
            event
        )

    # --------------------------------------------------------

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse release to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.mouse_release(
            event
        )

    # --------------------------------------------------------

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse double-click to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.mouse_double_click(
            event
        )

    # --------------------------------------------------------

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route keyboard press to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.key_press(
            event
        )

    # --------------------------------------------------------

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route keyboard release to the active tool.
        """

        self._ensure_active()

        return self.tool_manager.key_release(
            event
        )

    # ========================================================
    # ACTIVE TOOL STATE
    # ========================================================

    def get_active_tool_state(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Return the diagnostic state of the active tool.
        """

        self._ensure_active()

        return self.tool_manager.get_active_tool_state()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic ToolController snapshot.

        ToolManager remains authoritative for all tool state.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        return {
            "disposed": False,
            "active_tool_id": self.get_active_tool_id(),
            "registered_tool_ids": self.get_tool_ids(),
            "manager_state": self.tool_manager.get_state(),
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this UI adapter.

        ToolManager remains externally owned and is therefore
        NOT disposed here.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_tool_id(
        tool_id: str,
    ) -> None:
        """
        Validate tool ID type and basic syntax.

        Registration validation remains ToolManager's
        responsibility.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        if not tool_id.strip():
            raise ValueError(
                "tool_id must not be empty."
            )

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolController has been disposed."
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
                "ToolController("
                "disposed=True"
                ")"
            )

        return (
            "ToolController("
            f"active_tool="
            f"{self.get_active_tool_id()!r}, "
            f"tools="
            f"{len(self.get_tool_ids())}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolController",
]
