# ============================================================
# File: ui/tools/tool_manager.py
# GridForge V2 — Tool Manager
# ============================================================
"""
Tool lifecycle and active-tool management for GridForge V2.

ToolManager is the single UI authority for the concrete tool
set and for which tool is currently active.

Frozen concrete tool set
------------------------
GridForge V2 intentionally contains exactly three concrete tools:

    SelectTool
    BusTool
    LineTool

ToolManager does not discover arbitrary tools dynamically.

Architecture
------------

    MainWindow / UI Composition
              │
              ▼
         ToolManager
          ┌──┼──┐
          ▼  ▼  ▼
       Select Bus Line
          │
          ▼
    InteractionController
          │
          ▼
        Canvas/Core

Responsibilities
----------------
ToolManager:

    - construct the approved concrete tools;
    - register them by stable identifier;
    - activate exactly one tool at a time;
    - deactivate the previous tool;
    - expose the active tool;
    - route input events to the active tool;
    - provide cancellation/reset;
    - manage tool lifecycle.

ToolManager does NOT:

    - mutate Core directly;
    - own command history;
    - perform electrical validation;
    - render graphics;
    - implement selection;
    - perform navigation;
    - discover plugins;
    - create arbitrary third-party tools.

Plugin architecture
-------------------
The UI plugin architecture remains explicit.

ToolManager is deliberately not a plugin discovery mechanism.
The concrete tool imports are explicit and frozen.

Dependency injection
--------------------
Tools receive their application dependencies from ToolManager.
ToolManager itself does not construct Core state.

Qt
--
No direct Qt dependency is used here.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ui.tools.bus_tool import BusTool
from ui.tools.line_tool import LineTool
from ui.tools.select_tool import SelectTool
from ui.tools.tool_base import ToolBase


class ToolManager:
    """
    Manage the GridForge V2 concrete UI tools.

    Exactly one tool is active at any time after initialization.

    The default active tool is SelectTool.
    """

    # ========================================================
    # FROZEN TOOL IDS
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
        controller: Any,
        *,
        command_manager: Optional[Any] = None,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
        renderer_registry: Optional[Any] = None,
        activate_default: bool = True,
    ) -> None:
        """
        Initialize the ToolManager.

        Parameters
        ----------
        controller:
            Authoritative application/controller boundary.

        command_manager:
            CommandManager used by mutating tools.

        selection_manager:
            SelectionManager used by SelectTool.

        snap_system:
            SnapSystem used by LineTool.

        renderer_registry:
            RendererRegistry available to tools that need it.

        activate_default:
            When True, activate SelectTool immediately.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self.controller = controller
        self.command_manager = command_manager
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self.renderer_registry = renderer_registry

        self._tools: Dict[str, ToolBase] = {}
        self._active_tool_id: Optional[str] = None
        self._disposed = False

        self._register_builtin_tools()

        if activate_default:
            self.activate_tool(
                self.SELECT_TOOL_ID
            )

    # ========================================================
    # TOOL REGISTRATION
    # ========================================================

    def _register_builtin_tools(
        self,
    ) -> None:
        """
        Construct and register the frozen concrete tool set.

        The imports are explicit by design.
        """

        self.register_tool(
            SelectTool(
                self.controller,
                command_manager=self.command_manager,
                selection_manager=self.selection_manager,
                snap_system=self.snap_system,
                renderer_registry=self.renderer_registry,
            )
        )

        self.register_tool(
            BusTool(
                self.controller,
                command_manager=self.command_manager,
                selection_manager=self.selection_manager,
                snap_system=self.snap_system,
                renderer_registry=self.renderer_registry,
            )
        )

        self.register_tool(
            LineTool(
                self.controller,
                command_manager=self.command_manager,
                selection_manager=self.selection_manager,
                snap_system=self.snap_system,
                renderer_registry=self.renderer_registry,
            )
        )

    # --------------------------------------------------------

    def register_tool(
        self,
        tool: ToolBase,
    ) -> None:
        """
        Register a tool.

        This method is intentionally strict.

        Only the three frozen concrete tools are accepted.
        Duplicate identifiers are rejected.
        """

        self._ensure_not_disposed()

        if not isinstance(
            tool,
            ToolBase,
        ):
            raise TypeError(
                "tool must be an instance of ToolBase."
            )

        tool_id = tool.tool_id

        if tool_id not in self.TOOL_IDS:
            raise ValueError(
                f"Unsupported tool id: {tool_id!r}. "
                f"Allowed tools: {self.TOOL_IDS!r}."
            )

        if tool_id in self._tools:
            raise ValueError(
                f"Tool {tool_id!r} is already registered."
            )

        self._tools[tool_id] = tool

    # ========================================================
    # TOOL ACCESS
    # ========================================================

    def get_tool(
        self,
        tool_id: str,
    ) -> ToolBase:
        """
        Return a registered tool by identifier.
        """

        self._ensure_not_disposed()

        try:
            return self._tools[
                tool_id
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown tool id: {tool_id!r}."
            ) from exc

    # --------------------------------------------------------

    def has_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return whether a tool is registered.
        """

        self._ensure_not_disposed()

        return tool_id in self._tools

    # --------------------------------------------------------

    def tools(
        self,
    ) -> Iterable[ToolBase]:
        """
        Return registered tools in deterministic order.
        """

        self._ensure_not_disposed()

        return tuple(
            self._tools[
                tool_id
            ]
            for tool_id in self.TOOL_IDS
            if tool_id in self._tools
        )

    # --------------------------------------------------------

    def tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered tool identifiers in deterministic order.
        """

        self._ensure_not_disposed()

        return tuple(
            tool.tool_id
            for tool in self.tools()
        )

    # ========================================================
    # ACTIVE TOOL
    # ========================================================

    @property
    def active_tool_id(
        self,
    ) -> Optional[str]:
        """
        Return the active tool identifier.
        """

        return self._active_tool_id

    # --------------------------------------------------------

    @property
    def active_tool(
        self,
    ) -> Optional[ToolBase]:
        """
        Return the currently active tool.
        """

        if self._active_tool_id is None:
            return None

        return self._tools[
            self._active_tool_id
        ]

    # --------------------------------------------------------

    def activate_tool(
        self,
        tool_id: str,
    ) -> ToolBase:
        """
        Activate a tool.

        If another tool is active, it is deactivated first.

        Activating the already-active tool is idempotent.
        """

        self._ensure_not_disposed()

        tool = self.get_tool(
            tool_id
        )

        if (
            self._active_tool_id
            == tool_id
        ):
            return tool

        previous = self.active_tool

        if previous is not None:
            previous.deactivate()

        try:
            tool.activate()
        except Exception:
            # Restore the previous tool if activation of the new
            # tool fails. This preserves the manager invariant.
            if previous is not None:
                previous.activate()

            raise

        self._active_tool_id = tool_id

        return tool

    # --------------------------------------------------------

    def deactivate_active_tool(
        self,
    ) -> None:
        """
        Deactivate the currently active tool.

        No tool is active after this operation.
        """

        self._ensure_not_disposed()

        tool = self.active_tool

        if tool is None:
            return

        tool.deactivate()

        self._active_tool_id = None

    # ========================================================
    # TOOL SWITCHING
    # ========================================================

    def select_tool(
        self,
    ) -> ToolBase:
        """
        Activate SelectTool.
        """

        return self.activate_tool(
            self.SELECT_TOOL_ID
        )

    # --------------------------------------------------------

    def bus_tool(
        self,
    ) -> ToolBase:
        """
        Activate BusTool.
        """

        return self.activate_tool(
            self.BUS_TOOL_ID
        )

    # --------------------------------------------------------

    def line_tool(
        self,
    ) -> ToolBase:
        """
        Activate LineTool.
        """

        return self.activate_tool(
            self.LINE_TOOL_ID
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

        tool = self._require_active_tool()

        return bool(
            tool.mouse_press(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_move(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse move to the active tool.
        """

        tool = self._require_active_tool()

        return bool(
            tool.mouse_move(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse release to the active tool.
        """

        tool = self._require_active_tool()

        return bool(
            tool.mouse_release(
                event
            )
        )

    # --------------------------------------------------------

    def mouse_double_click(
        self,
        event: Any,
    ) -> bool:
        """
        Route mouse double-click to the active tool.
        """

        tool = self._require_active_tool()

        return bool(
            tool.mouse_double_click(
                event
            )
        )

    # --------------------------------------------------------

    def key_press(
        self,
        event: Any,
    ) -> bool:
        """
        Route keyboard press to the active tool.
        """

        tool = self._require_active_tool()

        return bool(
            tool.key_press(
                event
            )
        )

    # --------------------------------------------------------

    def key_release(
        self,
        event: Any,
    ) -> bool:
        """
        Route keyboard release to the active tool.
        """

        tool = self._require_active_tool()

        return bool(
            tool.key_release(
                event
            )
        )

    # ========================================================
    # CANCELLATION
    # ========================================================

    def cancel_active_tool(
        self,
    ) -> bool:
        """
        Cancel the active tool's transient operation.

        Returns False when no active tool exists or the tool has
        nothing to cancel.
        """

        self._ensure_not_disposed()

        tool = self.active_tool

        if tool is None:
            return False

        return bool(
            tool.cancel()
        )

    # --------------------------------------------------------

    def reset_active_tool(
        self,
    ) -> None:
        """
        Reset transient state of the active tool.
        """

        self._ensure_not_disposed()

        tool = self.active_tool

        if tool is None:
            return

        tool.reset()

    # ========================================================
    # TOOL STATE
    # ========================================================

    def get_active_tool_state(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Return the active tool diagnostic state.
        """

        tool = self.active_tool

        if tool is None:
            return None

        return tool.get_state()

    # --------------------------------------------------------

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a deterministic ToolManager diagnostic snapshot.
        """

        self._ensure_not_disposed()

        return {
            "active_tool_id": self._active_tool_id,
            "registered_tool_ids": self.tool_ids(),
            "tool_count": len(
                self._tools
            ),
            "disposed": self._disposed,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose all tools and release ToolManager ownership.
        """

        if self._disposed:
            return

        active_tool = self.active_tool

        if active_tool is not None:
            active_tool.deactivate()

        self._active_tool_id = None

        for tool in tuple(
            self._tools.values()
        ):
            tool.dispose()

        self._tools.clear()

        self._disposed = True

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _require_active_tool(
        self,
    ) -> ToolBase:
        """
        Return the active tool or raise a lifecycle error.
        """

        self._ensure_not_disposed()

        tool = self.active_tool

        if tool is None:
            raise RuntimeError(
                "No active tool is available."
            )

        return tool

    # --------------------------------------------------------

    def _ensure_not_disposed(
        self,
    ) -> None:
        """
        Ensure the manager has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "ToolManager has been disposed."
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
            f"active={self._active_tool_id!r}, "
            f"tools={self.tool_ids()!r}, "
            f"disposed={self._disposed}"
            ")"
        )


__all__ = [
    "ToolManager",
]
