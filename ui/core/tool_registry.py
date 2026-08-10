# ============================================================
# File: ui/core/tool_registry.py
# GridForge Tool Registry
# ============================================================
#
# PURPOSE
# -------
# Manages the ACTIVE tool instances used by the GridForge UI.
#
# IMPORTANT ARCHITECTURAL DISTINCTION
# -----------------------------------
#
# ui/core/plugin_registry.py
#     → registers plugin CLASSES
#
# ui/core/tool_registry.py
#     → manages active TOOL INSTANCES
#
# This separation is intentional.
#
#
# ARCHITECTURE
# ------------
#
#     @register_plugin("tool", "line")
#                  │
#                  ▼
#          Plugin Registry
#                  │
#                  │ class
#                  ▼
#          Controller / Tool Manager
#                  │
#                  │ instance
#                  ▼
#             ToolRegistry
#                  │
#          ┌───────┼────────┐
#          ▼       ▼        ▼
#       Select    Bus      Line
#
#
# GOLDEN RULE
# -----------
# ToolRegistry does NOT import individual tools.
#
# It only manages tool instances supplied to it.
#
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ToolRegistry:
    """
    Runtime registry for active GridForge tool instances.

    A ToolRegistry belongs to a particular UI/controller
    runtime and therefore stores INSTANCES, not classes.

    Examples of tools:

        "select"
        "bus"
        "line"
        "transformer"
        "load"

    The registry provides a stable interface for retrieving
    and managing those tools.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Create an empty runtime tool registry.

        Mapping:

            tool_id -> tool instance
        """

        self._tools: Dict[str, Any] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        tool_id: str,
        tool_instance: Any,
    ) -> Any:
        """
        Register a tool instance.

        Parameters
        ----------
        tool_id:
            Unique identifier of the tool.

        tool_instance:
            Already-created tool object.

        Returns
        -------
        object
            The registered tool instance.

        Notes
        -----
        Tool creation is deliberately outside this class.

        This keeps construction separate from runtime storage.

        Example:

            tool_registry.register(
                "line",
                LineTool(controller, interaction_manager)
            )
        """

        # ----------------------------------------------------
        # Validate tool ID
        # ----------------------------------------------------

        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError(
                "tool_id must be a non-empty string"
            )

        tool_id = tool_id.strip()

        # ----------------------------------------------------
        # Validate instance
        # ----------------------------------------------------

        if tool_instance is None:
            raise ValueError(
                f"Cannot register None as tool '{tool_id}'"
            )

        # ----------------------------------------------------
        # Prevent accidental replacement.
        #
        # Replacing an active tool silently can leave the
        # controller holding references to the old instance.
        # ----------------------------------------------------

        existing = self._tools.get(tool_id)

        if existing is not None and existing is not tool_instance:
            raise ValueError(
                f"Tool '{tool_id}' is already registered"
            )

        # ----------------------------------------------------
        # Store instance
        # ----------------------------------------------------

        self._tools[tool_id] = tool_instance

        return tool_instance

    # ========================================================
    # UNREGISTER
    # ========================================================

    def unregister(
        self,
        tool_id: str,
    ) -> bool:
        """
        Remove a tool instance from the registry.

        Returns
        -------
        bool
            True if removed.
            False if the tool was not registered.
        """

        if tool_id not in self._tools:
            return False

        del self._tools[tool_id]

        return True

    # ========================================================
    # ACCESS
    # ========================================================

    def get(
        self,
        tool_id: str,
    ) -> Optional[Any]:
        """
        Retrieve a tool instance by ID.

        Returns None if the tool is not registered.
        """

        return self._tools.get(tool_id)

    # ========================================================
    # REQUIRED ACCESS
    # ========================================================

    def require(
        self,
        tool_id: str,
    ) -> Any:
        """
        Retrieve a tool instance.

        Raises
        ------
        KeyError
            If the requested tool does not exist.

        Use this when absence of the tool represents an
        application configuration error.
        """

        tool = self._tools.get(tool_id)

        if tool is None:
            raise KeyError(
                f"Tool '{tool_id}' is not registered"
            )

        return tool

    # ========================================================
    # EXISTENCE CHECK
    # ========================================================

    def contains(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when a tool is registered.
        """

        return tool_id in self._tools

    # ========================================================
    # LIST TOOLS
    # ========================================================

    def list_tools(self) -> List[str]:
        """
        Return the IDs of all registered tools.

        Example:

            [
                "select",
                "bus",
                "line"
            ]
        """

        return list(self._tools.keys())

    # ========================================================
    # ITERATION
    # ========================================================

    def items(self):
        """
        Iterate over:

            (tool_id, tool_instance)

        pairs.

        This is useful for controller initialization,
        diagnostics, and UI integration.
        """

        return self._tools.items()

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all registered tool instances.

        Primarily intended for:

            - testing
            - application shutdown
            - development reload
        """

        self._tools.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(self) -> int:
        """
        Return the number of registered tools.
        """

        return len(self._tools)

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        tools = ", ".join(self._tools.keys())

        return (
            f"ToolRegistry("
            f"tools=[{tools}]"
            f")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolRegistry",
]
