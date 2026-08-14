# ============================================================
# File: ui/tools/tool_factory.py
# GridForge V2 — Tool Factory
# ============================================================
"""
Explicit factory for the frozen GridForge V2 tool set.

The factory centralizes construction of concrete tools while
keeping ToolRegistry and ToolManager free from concrete
construction logic.

Frozen concrete tool set
------------------------
    SelectTool
    BusTool
    LineTool

Architecture
------------

    UI Composition / Plugin
              │
              ▼
        ToolContext
              │
              ▼
         ToolFactory
          ┌───┼────┐
          ▼   ▼    ▼
       Select Bus  Line
        Tool  Tool  Tool
          │   │    │
          └───┴────┘
                │
                ▼
          ToolRegistry
                │
                ▼
           ToolManager

Responsibilities
----------------
ToolFactory:

    - construct the explicitly supported tools;
    - inject ToolContext;
    - keep concrete imports in one place;
    - provide deterministic creation of the frozen tool set.

ToolFactory does NOT:

    - register tools;
    - activate tools;
    - route events;
    - execute commands;
    - discover plugins;
    - mutate Core.

No Qt dependency is required by this module.
"""

from __future__ import annotations

from typing import Callable

from ui.tools.bus_tool import BusTool
from ui.tools.line_tool import LineTool
from ui.tools.select_tool import SelectTool
from ui.tools.tool_base import ToolBase
from ui.tools.tool_context import ToolContext


class ToolFactory:
    """
    Explicit factory for GridForge V2 concrete tools.

    A ToolFactory is intentionally stateless. All runtime
    dependencies are supplied through ToolContext.
    """

    SELECT_TOOL_ID = "select"
    BUS_TOOL_ID = "bus"
    LINE_TOOL_ID = "line"

    TOOL_IDS = (
        SELECT_TOOL_ID,
        BUS_TOOL_ID,
        LINE_TOOL_ID,
    )

    def __init__(
        self,
        context: ToolContext,
    ) -> None:
        """
        Initialize the factory with the shared ToolContext.
        """

        if not isinstance(
            context,
            ToolContext,
        ):
            raise TypeError(
                "context must be a ToolContext."
            )

        self._context = context

    # ========================================================
    # CONTEXT
    # ========================================================

    @property
    def context(
        self,
    ) -> ToolContext:
        """
        Return the ToolContext used for construction.
        """

        return self._context

    # ========================================================
    # INDIVIDUAL FACTORIES
    # ========================================================

    def create_select_tool(
        self,
    ) -> ToolBase:
        """
        Construct SelectTool.
        """

        return SelectTool(
            context=self._context,
        )

    # --------------------------------------------------------

    def create_bus_tool(
        self,
    ) -> ToolBase:
        """
        Construct BusTool.
        """

        return BusTool(
            context=self._context,
        )

    # --------------------------------------------------------

    def create_line_tool(
        self,
    ) -> ToolBase:
        """
        Construct LineTool.
        """

        return LineTool(
            context=self._context,
        )

    # ========================================================
    # GENERIC FACTORY
    # ========================================================

    def create(
        self,
        tool_id: str,
    ) -> ToolBase:
        """
        Construct one concrete tool by stable ID.

        Raises
        ------
        ValueError
            If the requested tool ID is not part of the frozen
            tool set.
        """

        creators: dict[str, Callable[[], ToolBase]] = {
            self.SELECT_TOOL_ID: self.create_select_tool,
            self.BUS_TOOL_ID: self.create_bus_tool,
            self.LINE_TOOL_ID: self.create_line_tool,
        }

        try:
            creator = creators[
                tool_id
            ]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported GridForge tool id: {tool_id!r}. "
                f"Allowed tools: {self.TOOL_IDS!r}."
            ) from exc

        return creator()

    # ========================================================
    # COMPLETE SET
    # ========================================================

    def create_all(
        self,
    ) -> tuple[ToolBase, ...]:
        """
        Construct the complete frozen tool set.

        The returned ordering is deterministic:

            SelectTool
            BusTool
            LineTool
        """

        return (
            self.create_select_tool(),
            self.create_bus_tool(),
            self.create_line_tool(),
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    @classmethod
    def supported_tool_ids(
        cls,
    ) -> tuple[str, ...]:
        """
        Return the stable IDs supported by this factory.
        """

        return cls.TOOL_IDS


__all__ = [
    "ToolFactory",
]
