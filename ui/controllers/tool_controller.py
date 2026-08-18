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
         ├── SelectTool
         ├── BusTool
         └── LineTool
              │
              ▼
       InteractionManager
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

The actual tool lifecycle remains owned by ToolManager.

Current GridForge V2 concrete tools remain intentionally
limited to:

    SelectTool
    BusTool
    LineTool

This controller does not discover tools and does not create
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
    - activate the configured default tool;
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
    - active-tool state;
    - tool activation/deactivation;
    - event routing;
    - cancellation;
    - reset;
    - tool lifecycle.

ToolController is only an orchestration adapter.

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

    ToolController deliberately maintains no active-tool state.
    ToolManager remains the sole authority for tool lifecycle.
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
            Existing GridForge ToolManager instance.

        The ToolManager is neither copied nor replaced.
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
        Return the underlying ToolManager.
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

        ToolManager owns the actual activation semantics.
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
    ) -> Any:
        """
        Deactivate the currently active tool.

        After this operation ToolManager has no active tool.
        """

        self._ensure_active()

        return self.tool_manager.deactivate_active_tool()

    # --------------------------------------------------------

    def deactivate_tool(
        self,
    ) -> Any:
        """
        Explicit alias for deactivate().
        """

        return self.deactivate()

    # ========================================================
    # SWITCH
    # ========================================================

    def switch(
        self,
        tool_id: str,
    ) -> Any:
        """
        Switch from the current tool to tool_id.

        ToolManager.activate_tool() already owns the complete
        transition semantics, including deactivation of the
        previous tool and rollback on activation failure.
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
        Return the currently active tool.

        The value is obtained directly from ToolManager.
        """

        self._ensure_active()

        return self.tool_manager.active_tool

    # --------------------------------------------------------

    def get_active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the stable identifier of the active tool.
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
        Return registered tool identifiers in deterministic order.

        Registration ownership remains with ToolManager.
        """

        self._ensure_active()

        return self.tool_manager.tool_ids()

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether ToolManager knows tool_id.
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

        ToolController does not instantiate tools.
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
        Cancel the current tool interaction.

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
    # DEFAULT / SELECT TOOL
    # ========================================================

    def activate_default(
        self,
    ) -> Any:
        """
        Activate the GridForge V2 default tool.

        The frozen ToolManager defines SelectTool as the
        default tool. The controller delegates to the
        ToolManager's explicit SelectTool operation rather
        than duplicating the tool identifier.
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

        ToolManager defines deterministic registration order.

        This method is intended only for composition/bootstrap
        code where registration ordering is explicitly
        meaningful.

        It does not define a preferred GridForge tool.
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
            "active_tool_id": (
                self.get_active_tool_id()
            ),
            "registered_tool_ids": (
                self.get_tool_ids()
            ),
            "manager_state": (
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
        Dispose this UI adapter.

        ToolManager is intentionally NOT disposed here because
        ownership belongs to the application/UI composition
        layer.
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
        Validate a tool identifier without checking registration.

        Registration validation remains the responsibility of
        ToolManager.
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
