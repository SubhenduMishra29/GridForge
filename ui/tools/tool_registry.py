# ============================================================
# File: ui/tools/tool_registry.py
# GridForge V2 — Tool Registry
# ============================================================
"""
Explicit tool registry for GridForge V2.

ToolRegistry is responsible for the identity and availability of
UI tools. It deliberately does not perform tool lifecycle
management; that responsibility belongs to ToolManager.

Frozen concrete tool set
------------------------
GridForge V2 currently exposes exactly three concrete tools:

    SelectTool
    BusTool
    LineTool

ToolRegistry does not dynamically discover or import arbitrary
tools. Concrete tool registration is explicit.

Architecture
------------

    ToolRegistry
         │
         ├── select
         ├── bus
         └── line
              │
              ▼
         ToolManager
              │
              ▼
        active ToolBase

Responsibilities
----------------
ToolRegistry:

    - register tool instances;
    - provide tools by stable ID;
    - enforce unique IDs;
    - expose deterministic tool ordering;
    - validate the frozen concrete tool set.

ToolRegistry does NOT:

    - activate/deactivate tools;
    - route input events;
    - create commands;
    - mutate Core;
    - perform rendering;
    - discover plugins;
    - own application state.

The registry is intentionally small and deterministic.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Dict, Optional

from ui.tools.tool_base import ToolBase


class ToolRegistry:
    """
    Registry of the concrete GridForge V2 UI tools.

    Registration is explicit and deterministic.

    The registry accepts only the frozen GridForge tool IDs.
    """

    # ========================================================
    # FROZEN TOOL IDENTIFIERS
    # ========================================================

    SELECT_TOOL_ID = "select"
    BUS_TOOL_ID = "bus"
    LINE_TOOL_ID = "line"

    TOOL_IDS = (
        SELECT_TOOL_ID,
        BUS_TOOL_ID,
        LINE_TOOL_ID,
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        tools: Optional[Iterable[ToolBase]] = None,
    ) -> None:
        """
        Initialize an empty registry and optionally register tools.

        Parameters
        ----------
        tools:
            Optional iterable of already-created ToolBase
            instances.

        Tool construction remains outside the registry.
        """

        self._tools: Dict[str, ToolBase] = {}

        if tools is not None:
            for tool in tools:
                self.register(tool)

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        tool: ToolBase,
    ) -> None:
        """
        Register one tool.

        Raises
        ------
        TypeError
            If the object is not a ToolBase.

        ValueError
            If the tool ID is not part of the frozen tool set or
            is already registered.
        """

        if not isinstance(
            tool,
            ToolBase,
        ):
            raise TypeError(
                "tool must be an instance of ToolBase."
            )

        tool_id = tool.tool_id

        self._validate_tool_id(
            tool_id
        )

        if tool_id in self._tools:
            raise ValueError(
                f"Tool {tool_id!r} is already registered."
            )

        self._tools[tool_id] = tool

    # --------------------------------------------------------

    def unregister(
        self,
        tool_id: str,
    ) -> ToolBase:
        """
        Remove and return a registered tool.

        Tool lifecycle is not modified by this operation.
        Disposal remains the responsibility of the owner,
        normally ToolManager.
        """

        self._validate_tool_id(
            tool_id
        )

        try:
            return self._tools.pop(
                tool_id
            )
        except KeyError as exc:
            raise KeyError(
                f"Tool {tool_id!r} is not registered."
            ) from exc

    # --------------------------------------------------------

    def replace(
        self,
        tool: ToolBase,
    ) -> Optional[ToolBase]:
        """
        Replace an existing registered tool.

        Returns
        -------
        Optional[ToolBase]
            The previous tool, or None when no tool was registered.

        Notes
        -----
        Replacement is useful during explicit composition/testing,
        but it is not a plugin discovery mechanism.
        """

        if not isinstance(
            tool,
            ToolBase,
        ):
            raise TypeError(
                "tool must be an instance of ToolBase."
            )

        tool_id = tool.tool_id

        self._validate_tool_id(
            tool_id
        )

        previous = self._tools.get(
            tool_id
        )

        self._tools[tool_id] = tool

        return previous

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        tool_id: str,
    ) -> ToolBase:
        """
        Return a registered tool.

        Raises
        ------
        KeyError
            If the tool ID is unknown or not registered.
        """

        self._validate_tool_id(
            tool_id
        )

        try:
            return self._tools[
                tool_id
            ]
        except KeyError as exc:
            raise KeyError(
                f"Tool {tool_id!r} is not registered."
            ) from exc

    # --------------------------------------------------------

    def get_optional(
        self,
        tool_id: str,
    ) -> Optional[ToolBase]:
        """
        Return a registered tool or None.

        An invalid tool ID is still rejected.
        """

        self._validate_tool_id(
            tool_id
        )

        return self._tools.get(
            tool_id
        )

    # --------------------------------------------------------

    def has(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether a valid tool ID is registered.
        """

        self._validate_tool_id(
            tool_id
        )

        return tool_id in self._tools

    # ========================================================
    # CONVENIENCE LOOKUPS
    # ========================================================

    @property
    def select_tool(
        self,
    ) -> ToolBase:
        """
        Return SelectTool.
        """

        return self.get(
            self.SELECT_TOOL_ID
        )

    # --------------------------------------------------------

    @property
    def bus_tool(
        self,
    ) -> ToolBase:
        """
        Return BusTool.
        """

        return self.get(
            self.BUS_TOOL_ID
        )

    # --------------------------------------------------------

    @property
    def line_tool(
        self,
    ) -> ToolBase:
        """
        Return LineTool.
        """

        return self.get(
            self.LINE_TOOL_ID
        )

    # ========================================================
    # ITERATION
    # ========================================================

    def ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered tool IDs in frozen deterministic order.
        """

        return tuple(
            tool_id
            for tool_id in self.TOOL_IDS
            if tool_id in self._tools
        )

    # --------------------------------------------------------

    def tools(
        self,
    ) -> tuple[ToolBase, ...]:
        """
        Return registered tools in frozen deterministic order.
        """

        return tuple(
            self._tools[tool_id]
            for tool_id in self.TOOL_IDS
            if tool_id in self._tools
        )

    # --------------------------------------------------------

    def items(
        self,
    ) -> tuple[tuple[str, ToolBase], ...]:
        """
        Return registered ID/tool pairs in deterministic order.
        """

        return tuple(
            (
                tool_id,
                self._tools[tool_id],
            )
            for tool_id in self.TOOL_IDS
            if tool_id in self._tools
        )

    # --------------------------------------------------------

    def __iter__(
        self,
    ) -> Iterator[ToolBase]:
        """
        Iterate over registered tools in deterministic order.
        """

        return iter(
            self.tools()
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered tools.
        """

        return len(
            self._tools
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def is_complete(
        self,
    ) -> bool:
        """
        Return whether all frozen concrete tools are registered.
        """

        return (
            len(self._tools)
            == len(self.TOOL_IDS)
            and all(
                tool_id in self._tools
                for tool_id in self.TOOL_IDS
            )
        )

    # --------------------------------------------------------

    def validate_complete(
        self,
    ) -> None:
        """
        Validate that the complete frozen tool set is registered.

        Raises
        ------
        RuntimeError
            If one or more required tools are missing.
        """

        missing = tuple(
            tool_id
            for tool_id in self.TOOL_IDS
            if tool_id not in self._tools
        )

        if missing:
            raise RuntimeError(
                "ToolRegistry is incomplete. "
                f"Missing tools: {missing!r}."
            )

    # --------------------------------------------------------

    def validate_exact(
        self,
    ) -> None:
        """
        Validate that the registry contains exactly the frozen
        concrete tool set.

        This provides an architectural guard against accidental
        tool proliferation.
        """

        registered = set(
            self._tools
        )
        expected = set(
            self.TOOL_IDS
        )

        if registered != expected:
            missing = tuple(
                tool_id
                for tool_id in self.TOOL_IDS
                if tool_id not in registered
            )

            unexpected = tuple(
                tool_id
                for tool_id in registered
                if tool_id not in expected
            )

            raise RuntimeError(
                "ToolRegistry does not match the frozen "
                "GridForge tool set. "
                f"Missing={missing!r}, "
                f"Unexpected={unexpected!r}."
            )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> tuple[ToolBase, ...]:
        """
        Remove all registered tools.

        Returns
        -------
        tuple[ToolBase, ...]
            Tools removed from the registry.

        Notes
        -----
        Tools are not disposed. Ownership/lifecycle remains
        outside the registry.
        """

        removed = self.tools()

        self._tools.clear()

        return removed

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, object]:
        """
        Return a deterministic diagnostic snapshot.
        """

        return {
            "registered_tool_ids": self.ids(),
            "registered_count": len(
                self._tools
            ),
            "expected_count": len(
                self.TOOL_IDS
            ),
            "complete": self.is_complete(),
            "exact": (
                set(self._tools)
                == set(self.TOOL_IDS)
            ),
        }

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @classmethod
    def _validate_tool_id(
        cls,
        tool_id: str,
    ) -> None:
        """
        Validate a tool identifier against the frozen tool set.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        if tool_id not in cls.TOOL_IDS:
            raise ValueError(
                f"Unsupported tool id: {tool_id!r}. "
                f"Allowed tools: {cls.TOOL_IDS!r}."
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

        return (
            f"{type(self).__name__}("
            f"tools={self.ids()!r}"
            ")"
        )


__all__ = [
    "ToolRegistry",
]
