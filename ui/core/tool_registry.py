# ============================================================
# File: ui/core/tool_registry.py
# GridForge V2 — Runtime Tool Registry
# ============================================================
"""
Runtime registry for instantiated GridForge interaction tools.

Architecture
------------

    PluginRegistry
        │
        │ registered tool class / factory
        ▼
    ToolManager
        │
        │ creates tool instance
        ▼
    ToolRegistry
        │
        │ runtime registration
        ▼
    Tool instance


Architectural distinction
-------------------------

ui/core/plugin_registry.py
    Registers plugin definitions/classes/factories.

ui/core/tool_registry.py
    Registers already-created tool instances for a particular
    UI runtime.

ui/core/tool_manager.py
    Owns the lifecycle of the currently active tool instance.

This distinction is intentional.

ToolRegistry does NOT:

    - import individual tools;
    - create tool instances;
    - activate tools;
    - deactivate tools;
    - cancel tools;
    - process input;
    - modify the Core model;
    - perform rendering;
    - perform snapping;
    - own Controller tool selection;
    - own tool lifecycle.

ToolManager remains the lifecycle authority.

Golden rule
-----------
ToolRegistry stores instances supplied to it.

Construction remains outside this class.

Qt rule
-------
This module has no direct Qt dependency.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional


class ToolRegistry:
    """
    Runtime registry of instantiated GridForge tools.

    A ToolRegistry belongs to one UI/application runtime.

    It stores tool instances by stable tool identifier.

    ToolRegistry is deliberately passive. It does not determine
    how tools are constructed and does not control their lifecycle.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Create an empty runtime tool registry.
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
        Register an already-created tool instance.

        Parameters
        ----------
        tool_id:
            Stable identifier associated with the tool.

        tool_instance:
            Already-created tool object.

        Returns
        -------
        object
            The registered instance.

        Raises
        ------
        TypeError
            If tool_id is not a string.

        ValueError
            If tool_id is empty or tool_instance is None.

        KeyError
            If a different instance is already registered under
            the same identifier.

        Notes
        -----
        ToolRegistry never creates the supplied instance.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        tool_id = tool_id.strip()

        if not tool_id:
            raise ValueError(
                "tool_id cannot be empty."
            )

        if tool_instance is None:
            raise ValueError(
                f"Cannot register None as tool '{tool_id}'."
            )

        existing = self._tools.get(
            tool_id
        )

        if (
            existing is not None
            and existing is not tool_instance
        ):
            raise KeyError(
                f"Tool '{tool_id}' is already registered."
            )

        self._tools[
            tool_id
        ] = tool_instance

        return tool_instance

    # ========================================================
    # UNREGISTRATION
    # ========================================================

    def unregister(
        self,
        tool_id: str,
    ) -> bool:
        """
        Remove a registered tool instance.

        Returns
        -------
        bool
            True when an instance was removed.

            False when no instance was registered.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        tool_id = tool_id.strip()

        if not tool_id:
            raise ValueError(
                "tool_id cannot be empty."
            )

        if tool_id not in self._tools:
            return False

        del self._tools[
            tool_id
        ]

        return True

    # ========================================================
    # ACCESS
    # ========================================================

    def get(
        self,
        tool_id: str,
    ) -> Optional[Any]:
        """
        Return the registered tool instance.

        Returns None when the identifier is not registered.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        return self._tools.get(
            tool_id.strip()
        )

    # ========================================================
    # REQUIRED ACCESS
    # ========================================================

    def require(
        self,
        tool_id: str,
    ) -> Any:
        """
        Return a registered tool instance.

        Raises
        ------
        KeyError
            If the requested tool is not registered.
        """

        tool = self.get(
            tool_id
        )

        if tool is None:
            raise KeyError(
                f"Tool '{tool_id}' is not registered."
            )

        return tool

    # ========================================================
    # EXISTENCE
    # ========================================================

    def contains(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when a tool is registered.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        return (
            tool_id.strip()
            in self._tools
        )

    # ========================================================
    # LIST
    # ========================================================

    def list_tools(
        self,
    ) -> List[str]:
        """
        Return registered tool identifiers.

        Registration order is preserved.
        """

        return list(
            self._tools.keys()
        )

    # ========================================================
    # ITERATION
    # ========================================================

    def items(
        self,
    ) -> Iterator[tuple[str, Any]]:
        """
        Iterate over registered:

            (tool_id, tool_instance)

        pairs.
        """

        return iter(
            self._tools.items()
        )

    # --------------------------------------------------------

    def values(
        self,
    ) -> Iterator[Any]:
        """
        Iterate over registered tool instances.
        """

        return iter(
            self._tools.values()
        )

    # --------------------------------------------------------

    def keys(
        self,
    ) -> Iterator[str]:
        """
        Iterate over registered tool identifiers.
        """

        return iter(
            self._tools.keys()
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all registered instances.

        This method only removes registry references.

        It does NOT call:

            deactivate()
            cancel()
            dispose()

        Lifecycle operations belong to ToolManager.
        """

        self._tools.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered tool instances.
        """

        return len(
            self._tools
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic registry state.
        """

        return {
            "count": len(
                self._tools
            ),
            "tool_ids": list(
                self._tools.keys()
            ),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        tools = ", ".join(
            self._tools.keys()
        )

        return (
            "ToolRegistry("
            f"tools=[{tools}]"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolRegistry",
]
