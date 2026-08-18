# ============================================================
# File: ui/core/tool_registry.py
# GridForge V2 — Tool Registry
# ============================================================
"""
Central registry for GridForge UI tools.

Architecture
------------

    ToolRegistry
         │
         ├── tool_id → tool factory
         │
         ▼
    ToolManager
         │
         ▼
    Tool instance
         │
         ▼
    InteractionManager

Responsibilities
----------------
ToolRegistry:

    - stores tool registrations;
    - maps stable tool IDs to tool factories;
    - validates registrations;
    - provides tool lookup;
    - creates tool instances on request;
    - exposes registered tool IDs;
    - prevents accidental duplicate registrations;
    - provides diagnostic state.

ToolRegistry does NOT:

    - own the active tool;
    - manage tool activation/deactivation;
    - manage tool lifecycle;
    - select the application tool;
    - subscribe to Controller events;
    - route mouse/keyboard input;
    - implement tool behavior;
    - create Core model objects;
    - modify the Core model;
    - perform rendering;
    - perform snapping;
    - perform selection.

Tool Ownership
--------------
ToolRegistry owns only the registration/factory definitions.

ToolManager owns concrete tool instances and their lifecycle.

Therefore:

    ToolRegistry
        = registration + factory lookup

    ToolManager
        = instance ownership + lifecycle

Concrete Tools
--------------
GridForge V2 currently has exactly three concrete tools:

    SelectTool
    BusTool
    LineTool

ToolRegistry deliberately does NOT import these concrete
classes.

Concrete tool registration is performed explicitly by the UI
composition/bootstrap layer.

This avoids hidden imports and prevents the registry from
becoming an implicit plugin loader.

Registration Contract
----------------------
A tool registration consists of:

    tool_id
    factory

The factory must be callable.

The factory is expected to accept the keyword arguments supplied
by ToolManager when creating the tool.

The registry does not impose a concrete constructor signature
because tool construction dependencies belong to ToolManager and
the concrete tool implementation.

Qt Architecture
---------------
This registry contains no Qt dependency.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


ToolFactory = Callable[..., Any]


class ToolRegistry:
    """
    Registry of available GridForge UI tools.

    The registry is intentionally independent of concrete tool
    classes.

    Example registration:

        registry.register(
            "select",
            SelectTool,
        )

    Example creation:

        tool = registry.create(
            "select",
            interaction_manager=interaction_manager,
        )

    ToolManager remains responsible for deciding when a tool
    instance should be created and how that instance is used.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty tool registry.
        """

        self._factories: dict[
            str,
            ToolFactory,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        tool_id: str,
        factory: ToolFactory,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a tool factory.

        Parameters
        ----------
        tool_id:
            Stable application-level identifier for the tool.

        factory:
            Callable used to construct the concrete tool.

        replace:
            When False, duplicate registration raises
            ValueError.

            When True, an existing registration is replaced.

        Notes
        -----
        The registry does not import the concrete tool class.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        if (
            normalized_id in self._factories
            and not replace
        ):
            raise ValueError(
                f"Tool {normalized_id!r} "
                "is already registered."
            )

        self._factories[
            normalized_id
        ] = factory

    # --------------------------------------------------------

    def unregister(
        self,
        tool_id: str,
    ) -> ToolFactory:
        """
        Remove and return a registered tool factory.

        Raises
        ------
        KeyError
            If the tool is not registered.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        try:
            return self._factories.pop(
                normalized_id
            )
        except KeyError:
            raise KeyError(
                f"Tool {normalized_id!r} "
                "is not registered."
            ) from None

    # --------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all registered tool factories.

        This does not affect existing tool instances owned by
        ToolManager.
        """

        self._factories.clear()

    # ========================================================
    # REGISTRATION QUERIES
    # ========================================================

    def contains(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when tool_id is registered.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        return (
            normalized_id
            in self._factories
        )

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Semantic alias for contains().
        """

        return self.contains(
            tool_id
        )

    # --------------------------------------------------------

    def get_factory(
        self,
        tool_id: str,
    ) -> ToolFactory:
        """
        Return the factory registered for tool_id.

        The factory itself is not executed.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        try:
            return self._factories[
                normalized_id
            ]
        except KeyError:
            raise KeyError(
                f"Tool {normalized_id!r} "
                "is not registered."
            ) from None

    # --------------------------------------------------------

    def get_optional_factory(
        self,
        tool_id: str,
    ) -> Optional[ToolFactory]:
        """
        Return a registered factory or None when absent.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        return self._factories.get(
            normalized_id
        )

    # ========================================================
    # TOOL CREATION
    # ========================================================

    def create(
        self,
        tool_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Create a tool instance using its registered factory.

        Parameters
        ----------
        tool_id:
            Registered tool identifier.

        **kwargs:
            Constructor dependencies supplied to the concrete
            tool factory.

        Returns
        -------
        object
            Newly created tool instance.

        Notes
        -----
        ToolRegistry creates the instance on behalf of
        ToolManager, but does not retain ownership of it.

        Lifecycle remains exclusively owned by ToolManager.
        """

        factory = self.get_factory(
            tool_id
        )

        return factory(
            **kwargs
        )

    # ========================================================
    # TOOL IDS
    # ========================================================

    def tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered tool IDs.

        Registration order is preserved.
        """

        return tuple(
            self._factories.keys()
        )

    # --------------------------------------------------------

    def get_tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Semantic alias for tool_ids().
        """

        return self.tool_ids()

    # --------------------------------------------------------

    def count(self) -> int:
        """
        Return the number of registered tools.
        """

        return len(
            self._factories
        )

    # ========================================================
    # REQUIRED TOOL VALIDATION
    # ========================================================

    def require(
        self,
        tool_id: str,
    ) -> ToolFactory:
        """
        Require a tool registration.

        This is equivalent to get_factory() and is intended for
        bootstrap validation.
        """

        return self.get_factory(
            tool_id
        )

    # --------------------------------------------------------

    def require_tools(
        self,
        tool_ids: tuple[str, ...] | list[str],
    ) -> None:
        """
        Verify that all supplied tool IDs are registered.

        Raises
        ------
        KeyError
            If any required tool is missing.
        """

        if tool_ids is None:
            raise ValueError(
                "tool_ids must not be None."
            )

        for tool_id in tool_ids:
            self.require(
                tool_id
            )

    # ========================================================
    # FACTORY REPLACEMENT
    # ========================================================

    def replace(
        self,
        tool_id: str,
        factory: ToolFactory,
    ) -> None:
        """
        Replace an existing tool registration.

        Replacement is explicit.

        A missing registration is treated as an error rather
        than silently creating a new registration.
        """

        normalized_id = self._validate_tool_id(
            tool_id
        )

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        if normalized_id not in self._factories:
            raise KeyError(
                f"Tool {normalized_id!r} "
                "is not registered."
            )

        self._factories[
            normalized_id
        ] = factory

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def get_factories(
        self,
    ) -> dict[str, ToolFactory]:
        """
        Return a shallow copy of the registered factories.

        The registry's internal dictionary is never exposed
        directly.
        """

        return dict(
            self._factories
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_tool_id(
        tool_id: str,
    ) -> str:
        """
        Validate and normalize a tool identifier.

        Tool IDs are stable identifiers, not display labels.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        normalized_id = tool_id.strip()

        if not normalized_id:
            raise ValueError(
                "tool_id must not be empty."
            )

        return normalized_id

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of registry state.
        """

        return {
            "tool_count": self.count(),
            "tool_ids": self.tool_ids(),
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "ToolRegistry("
            f"tools={self.tool_ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ToolFactory",
    "ToolRegistry",
]
