# ============================================================
# File: ui/tools/tool_manager.py
# GridForge V2 — Tool Manager
# ============================================================
"""Single presentation authority for interactive tool lifecycle.

ToolManager owns tool selection/lifecycle and routes input. It does not own
Core state, CommandManager, history, undo/redo, or electrical validation.
Mutating tools receive the Application facade and submit commands through it.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ui.tools.bus_tool import BusTool
from ui.tools.line_tool import LineTool
from ui.tools.select_tool import SelectTool
from ui.tools.tool_base import ToolBase


class ToolManager:
    """Manage the frozen GridForge V2 concrete presentation tools."""

    SELECT_TOOL_ID = "select"
    BUS_TOOL_ID = "bus"
    LINE_TOOL_ID = "line"
    TOOL_IDS = (SELECT_TOOL_ID, BUS_TOOL_ID, LINE_TOOL_ID)

    def __init__(
        self,
        controller: Any,
        *,
        application: Any,
        selection_manager: Optional[Any] = None,
        snap_system: Optional[Any] = None,
        activate_default: bool = True,
    ) -> None:
        if controller is None:
            raise ValueError("controller must not be None.")
        if application is None:
            raise ValueError("application must not be None.")

        self.controller = controller
        self.application = application
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self._tools: Dict[str, ToolBase] = {}
        self._active_tool_id: Optional[str] = None
        self._disposed = False
        self._register_builtin_tools()
        if activate_default:
            self.activate_tool(self.SELECT_TOOL_ID)

    def _register_builtin_tools(self) -> None:
        self.register_tool(SelectTool(
            self.controller,
            application=self.application,
            selection_manager=self.selection_manager,
            snap_system=self.snap_system,
        ))
        self.register_tool(BusTool(
            self.controller,
            application=self.application,
            selection_manager=self.selection_manager,
            snap_system=self.snap_system,
        ))
        self.register_tool(LineTool(
            self.controller,
            application=self.application,
            selection_manager=self.selection_manager,
            snap_system=self.snap_system,
        ))

    def register_tool(self, tool: ToolBase) -> None:
        self._ensure_not_disposed()
        if not isinstance(tool, ToolBase):
            raise TypeError("tool must be an instance of ToolBase.")
        tool_id = tool.tool_id
        if tool_id not in self.TOOL_IDS:
            raise ValueError(f"Unsupported tool id: {tool_id!r}. Allowed tools: {self.TOOL_IDS!r}.")
        if tool_id in self._tools:
            raise ValueError(f"Tool {tool_id!r} is already registered.")
        self._tools[tool_id] = tool

    def get_tool(self, tool_id: str) -> ToolBase:
        self._ensure_not_disposed()
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise KeyError(f"Unknown tool id: {tool_id!r}.") from exc

    def has_tool(self, tool_id: str) -> bool:
        self._ensure_not_disposed()
        return tool_id in self._tools

    def tools(self) -> Iterable[ToolBase]:
        self._ensure_not_disposed()
        return tuple(self._tools[tool_id] for tool_id in self.TOOL_IDS if tool_id in self._tools)

    def tool_ids(self) -> tuple[str, ...]:
        return tuple(tool.tool_id for tool in self.tools())

    @property
    def active_tool_id(self) -> Optional[str]:
        return self._active_tool_id

    @property
    def active_tool(self) -> Optional[ToolBase]:
        if self._active_tool_id is None:
            return None
        return self._tools[self._active_tool_id]

    def activate_tool(self, tool_id: str) -> ToolBase:
        self._ensure_not_disposed()
        tool = self.get_tool(tool_id)
        if self._active_tool_id == tool_id:
            return tool
        previous = self.active_tool
        if previous is not None:
            previous.deactivate()
        try:
            tool.activate()
        except Exception:
            if previous is not None:
                previous.activate()
            raise
        self._active_tool_id = tool_id
        return tool

    def deactivate_active_tool(self) -> None:
        self._ensure_not_disposed()
        tool = self.active_tool
        if tool is None:
            return
        tool.deactivate()
        self._active_tool_id = None

    def select_tool(self) -> ToolBase:
        return self.activate_tool(self.SELECT_TOOL_ID)

    def bus_tool(self) -> ToolBase:
        return self.activate_tool(self.BUS_TOOL_ID)

    def line_tool(self) -> ToolBase:
        return self.activate_tool(self.LINE_TOOL_ID)

    def mouse_press(self, event: Any) -> bool:
        return bool(self._require_active_tool().mouse_press(event))

    def mouse_move(self, event: Any) -> bool:
        return bool(self._require_active_tool().mouse_move(event))

    def mouse_release(self, event: Any) -> bool:
        return bool(self._require_active_tool().mouse_release(event))

    def mouse_double_click(self, event: Any) -> bool:
        return bool(self._require_active_tool().mouse_double_click(event))

    def key_press(self, event: Any) -> bool:
        return bool(self._require_active_tool().key_press(event))

    def key_release(self, event: Any) -> bool:
        return bool(self._require_active_tool().key_release(event))

    def cancel_active_tool(self) -> bool:
        self._ensure_not_disposed()
        tool = self.active_tool
        return False if tool is None else bool(tool.cancel())

    def reset_active_tool(self) -> None:
        self._ensure_not_disposed()
        tool = self.active_tool
        if tool is not None:
            tool.reset()

    def get_active_tool_state(self) -> Optional[dict[str, Any]]:
        tool = self.active_tool
        return None if tool is None else tool.get_state()

    def get_state(self) -> dict[str, Any]:
        self._ensure_not_disposed()
        return {
            "active_tool_id": self._active_tool_id,
            "registered_tool_ids": self.tool_ids(),
            "tool_count": len(self._tools),
            "disposed": self._disposed,
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        active_tool = self.active_tool
        if active_tool is not None:
            active_tool.deactivate()
        self._active_tool_id = None
        for tool in tuple(self._tools.values()):
            tool.dispose()
        self._tools.clear()
        self._disposed = True

    def _require_active_tool(self) -> ToolBase:
        self._ensure_not_disposed()
        tool = self.active_tool
        if tool is None:
            raise RuntimeError("No active tool is available.")
        return tool

    def _ensure_not_disposed(self) -> None:
        if self._disposed:
            raise RuntimeError("ToolManager has been disposed.")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(active={self._active_tool_id!r}, tools={self.tool_ids()!r}, disposed={self._disposed})"


__all__ = ["ToolManager"]
