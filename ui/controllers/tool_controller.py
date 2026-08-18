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
    InteractionManager
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

The actual tool lifecycle remains owned by ToolManager and
InteractionManager.

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
ToolManager remains authoritative for tool registration and
tool lifecycle.

InteractionManager remains authoritative for forwarding actual
canvas interaction to the active tool.

Qt Architecture
---------------
This module contains no direct Qt imports.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.tools.tool_manager import ToolManager


class ToolController:
    """
    Thin UI orchestration adapter around ToolManager.

    No tool state is duplicated here.
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
            Existing GridForge ToolManager.

        The ToolManager is not copied or replaced.
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

        Parameters
        ----------
        tool_id:
            Stable ToolManager registration identifier.

        Returns
        -------
        Any
            Result returned by ToolManager.

        Notes
        -----
        ToolController does not validate concrete tool names.
        ToolManager owns the registration contract.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        manager = self.tool_manager

        activate = getattr(
            manager,
            "activate",
            None,
        )

        if callable(activate):
            return activate(
                tool_id
            )

        activate_tool = getattr(
            manager,
            "activate_tool",
            None,
        )

        if callable(activate_tool):
            return activate_tool(
                tool_id
            )

        raise TypeError(
            "ToolManager must provide activate() "
            "or activate_tool()."
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
        """

        self._ensure_active()

        manager = self.tool_manager

        deactivate = getattr(
            manager,
            "deactivate",
            None,
        )

        if callable(deactivate):
            return deactivate()

        deactivate_tool = getattr(
            manager,
            "deactivate_tool",
            None,
        )

        if callable(deactivate_tool):
            return deactivate_tool()

        raise TypeError(
            "ToolManager must provide deactivate() "
            "or deactivate_tool()."
        )

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

        ToolManager owns the exact transition semantics.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        manager = self.tool_manager

        switch = getattr(
            manager,
            "switch",
            None,
        )

        if callable(switch):
            return switch(
                tool_id
            )

        switch_tool = getattr(
            manager,
            "switch_tool",
            None,
        )

        if callable(switch_tool):
            return switch_tool(
                tool_id
            )

        # ----------------------------------------------------
        # Do not maintain transition state here.
        #
        # If ToolManager exposes only activation, activation is
        # the canonical operation.
        # ----------------------------------------------------

        return self.activate(
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
        """

        self._ensure_active()

        manager = self.tool_manager

        getter = getattr(
            manager,
            "get_active_tool",
            None,
        )

        if callable(getter):
            return getter()

        value = getattr(
            manager,
            "active_tool",
            None,
        )

        return value

    # --------------------------------------------------------

    def get_active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the stable identifier of the active tool.

        The value is read from ToolManager rather than inferred
        from the concrete tool class.
        """

        self._ensure_active()

        manager = self.tool_manager

        getter = getattr(
            manager,
            "get_active_tool_id",
            None,
        )

        if callable(getter):
            value = getter()

            if value is None:
                return None

            return str(
                value
            )

        value = getattr(
            manager,
            "active_tool_id",
            None,
        )

        if value is None:
            return None

        return str(
            value
        )

    # ========================================================
    # AVAILABLE TOOLS
    # ========================================================

    def get_tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered tool identifiers.

        Registration ownership remains with ToolManager.
        """

        self._ensure_active()

        manager = self.tool_manager

        getter = getattr(
            manager,
            "get_tool_ids",
            None,
        )

        if callable(getter):
            return tuple(
                str(tool_id)
                for tool_id in getter()
            )

        getter = getattr(
            manager,
            "list_tools",
            None,
        )

        if callable(getter):
            return tuple(
                str(tool_id)
                for tool_id in getter()
            )

        value = getattr(
            manager,
            "tools",
            None,
        )

        if isinstance(
            value,
            dict,
        ):
            return tuple(
                str(tool_id)
                for tool_id in value.keys()
            )

        return ()

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether ToolManager knows tool_id.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        manager = self.tool_manager

        method = getattr(
            manager,
            "has_tool",
            None,
        )

        if callable(method):
            return bool(
                method(
                    tool_id
                )
            )

        return tool_id in self.get_tool_ids()

    # ========================================================
    # TOOL INSTANCE
    # ========================================================

    def get_tool(
        self,
        tool_id: str,
    ) -> Optional[Any]:
        """
        Return a registered tool when ToolManager exposes a
        lookup operation.

        The controller does not instantiate missing tools.
        """

        self._ensure_active()

        self._validate_tool_id(
            tool_id
        )

        manager = self.tool_manager

        getter = getattr(
            manager,
            "get_tool",
            None,
        )

        if callable(getter):
            return getter(
                tool_id
            )

        getter = getattr(
            manager,
            "get",
            None,
        )

        if callable(getter):
            return getter(
                tool_id
            )

        tools = getattr(
            manager,
            "tools",
            None,
        )

        if isinstance(
            tools,
            dict,
        ):
            return tools.get(
                tool_id
            )

        return None

    # ========================================================
    # RESET / CANCEL
    # ========================================================

    def reset(
        self,
    ) -> Any:
        """
        Reset transient state of the current tool.

        ToolManager owns the operation.
        """

        self._ensure_active()

        manager = self.tool_manager

        reset = getattr(
            manager,
            "reset",
            None,
        )

        if callable(reset):
            return reset()

        tool = self.get_active_tool()

        if tool is None:
            return None

        reset_tool = getattr(
            tool,
            "reset",
            None,
        )

        if callable(reset_tool):
            return reset_tool()

        return None

    # --------------------------------------------------------

    def cancel(
        self,
    ) -> bool:
        """
        Cancel the current tool interaction when supported.

        Returns
        -------
        bool
            True when cancellation was handled.
        """

        self._ensure_active()

        manager = self.tool_manager

        cancel = getattr(
            manager,
            "cancel",
            None,
        )

        if callable(cancel):
            result = cancel()

            if result is None:
                return True

            return bool(
                result
            )

        tool = self.get_active_tool()

        if tool is None:
            return False

        cancel_tool = getattr(
            tool,
            "cancel",
            None,
        )

        if not callable(
            cancel_tool
        ):
            return False

        result = cancel_tool()

        if result is None:
            return True

        return bool(
            result
        )

    # ========================================================
    # DEFAULT / SELECT TOOL
    # ========================================================

    def activate_default(
        self,
    ) -> Any:
        """
        Activate ToolManager's configured default tool.

        No tool identifier is guessed by this controller.
        """

        self._ensure_active()

        manager = self.tool_manager

        method = getattr(
            manager,
            "activate_default",
            None,
        )

        if callable(method):
            return method()

        method = getattr(
            manager,
            "get_default_tool_id",
            None,
        )

        if callable(method):
            tool_id = method()

            if tool_id is not None:
                return self.activate(
                    str(tool_id)
                )

        value = getattr(
            manager,
            "default_tool_id",
            None,
        )

        if value is not None:
            return self.activate(
                str(value)
            )

        raise LookupError(
            "ToolManager does not expose a default tool."
        )

    # ========================================================
    # TOOL COLLECTION
    # ========================================================

    def activate_first_registered(
        self,
    ) -> Any:
        """
        Activate the first registered tool.

        This method is intended only for composition/bootstrap
        code where ToolManager ordering is explicitly meaningful.

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
        Return a diagnostic tool-controller snapshot.

        ToolManager remains authoritative.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        manager_state: Any = None

        getter = getattr(
            self.tool_manager,
            "get_state",
            None,
        )

        if callable(getter):
            manager_state = getter()

        return {
            "disposed": False,
            "active_tool_id": (
                self.get_active_tool_id()
            ),
            "registered_tool_ids": (
                self.get_tool_ids()
            ),
            "manager_state": manager_state,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this UI adapter.

        ToolManager is not disposed because it is owned by the
        application/UI composition layer.
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
