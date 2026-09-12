# ============================================================
# File: ui/core/tool_manager.py
# GridForge V2 — Tool Manager
# Author: Subhendu Mishra
# ============================================================
"""Authoritative runtime lifecycle manager for UI interaction tools.

ToolManager owns concrete tool instances, lifecycle, and input dispatch.
The registry provides factories; every factory receives the single canonical
dependency contract: controller, application, selection_manager, and
snap_system.
"""

from __future__ import annotations

from typing import Any, Callable


ToolFactory = Callable[..., Any]


class ToolManager:
    """Own registered UI tools, activation lifecycle, and input dispatch."""

    def __init__(
        self,
        *,
        controller: Any,
        application: Any,
        selection_manager: Any,
        snap_system: Any,
        tool_registry: Any = None,
    ) -> None:
        if controller is None:
            raise ValueError("controller must not be None.")
        if application is None:
            raise ValueError("application must not be None.")
        if selection_manager is None:
            raise ValueError("selection_manager must not be None.")
        if snap_system is None:
            raise ValueError("snap_system must not be None.")

        self.controller = controller
        self.application = application
        self.selection_manager = selection_manager
        self.snap_system = snap_system
        self._tool_registry: dict[str, ToolFactory] = {}
        self._tool_instances: dict[str, Any] = {}
        self._active_tool_id: str | None = None
        self._active_tool: Any | None = None
        self._disposed = False

        if tool_registry is not None:
            self._load_registry(tool_registry)

    def register_tool(self, tool_id: str, factory: ToolFactory) -> None:
        self._ensure_active()
        self._validate_tool_id(tool_id)
        if not callable(factory):
            raise TypeError("factory must be callable.")
        if tool_id in self._tool_registry:
            raise ValueError(f"Tool already registered: {tool_id!r}")
        self._tool_registry[tool_id] = factory

    def register_tools(self, tools: dict[str, ToolFactory]) -> None:
        self._ensure_active()
        if not isinstance(tools, dict):
            raise TypeError("tools must be a dictionary.")
        for tool_id, factory in tools.items():
            self._validate_tool_id(tool_id)
            if not callable(factory):
                raise TypeError("factory must be callable.")
            if tool_id in self._tool_registry:
                raise ValueError(f"Tool already registered: {tool_id!r}")
        self._tool_registry.update(tools)

    def unregister_tool(self, tool_id: str) -> None:
        self._ensure_active()
        self._validate_tool_id(tool_id)
        if tool_id == self._active_tool_id:
            raise RuntimeError("Cannot unregister the active tool.")
        instance = self._tool_instances.pop(tool_id, None)
        if instance is not None:
            self._dispose_tool(instance)
        self._tool_registry.pop(tool_id, None)

    def has_tool(self, tool_id: str) -> bool:
        return not self._disposed and isinstance(tool_id, str) and tool_id in self._tool_registry

    def get_tool_ids(self) -> tuple[str, ...]:
        self._ensure_active()
        return tuple(self._tool_registry)

    def _load_registry(self, registry: Any) -> None:
        if isinstance(registry, dict):
            self.register_tools(registry)
            return
        get_tools = getattr(registry, "get_tools", None)
        if callable(get_tools):
            tools = get_tools()
            if tools is None:
                return
            self.register_tools(tools)
            return
        items = getattr(registry, "items", None)
        if callable(items):
            self.register_tools(dict(items()))
            return
        raise TypeError("tool_registry must provide a mapping, get_tools(), or items().")

    def _create_tool(self, tool_id: str) -> Any:
        self._ensure_active()
        factory = self._tool_registry.get(tool_id)
        if factory is None:
            raise KeyError(f"Unknown tool ID: {tool_id!r}")
        tool = factory(
            controller=self.controller,
            application=self.application,
            selection_manager=self.selection_manager,
            snap_system=self.snap_system,
        )
        if tool is None:
            raise RuntimeError(f"Tool factory returned None: {tool_id!r}")
        return tool

    def _get_or_create_tool(self, tool_id: str) -> Any:
        self._ensure_active()
        if tool_id not in self._tool_instances:
            self._tool_instances[tool_id] = self._create_tool(tool_id)
        return self._tool_instances[tool_id]

    def get_current_tool(self) -> Any | None:
        self._ensure_active()
        return self._active_tool

    def get_current_tool_id(self) -> str | None:
        self._ensure_active()
        return self._active_tool_id

    @property
    def active_tool(self) -> Any | None:
        return self.get_current_tool()

    @property
    def active_tool_id(self) -> str | None:
        return self.get_current_tool_id()

    def activate(self, tool_id: str | None) -> Any | None:
        self._ensure_active()
        if tool_id is not None:
            self._validate_tool_id(tool_id)
            if tool_id not in self._tool_registry:
                raise KeyError(f"Unknown tool ID: {tool_id!r}")
            if tool_id == self._active_tool_id:
                return self._active_tool

        previous_id = self._active_tool_id
        previous_tool = self._active_tool
        requested_tool = self._get_or_create_tool(tool_id) if tool_id is not None else None

        if previous_tool is not None:
            previous_tool.deactivate()

        try:
            if requested_tool is not None:
                requested_tool.activate()
        except Exception:
            if previous_tool is not None:
                try:
                    previous_tool.activate()
                except Exception:
                    self._active_tool_id = None
                    self._active_tool = None
                    raise
            self._active_tool_id = previous_id
            self._active_tool = previous_tool
            raise

        self._active_tool_id = tool_id
        self._active_tool = requested_tool
        return requested_tool

    def deactivate(self) -> None:
        self._ensure_active()
        if self._active_tool is None:
            return
        self._active_tool.deactivate()
        self._active_tool = None
        self._active_tool_id = None

    # ========================================================
    # Canonical Canvas Input Dispatch
    # ========================================================

    def mouse_press(self, event: Any) -> bool:
        return self._dispatch_input("mouse_press", event)

    def mouse_move(self, event: Any) -> bool:
        return self._dispatch_input("mouse_move", event)

    def mouse_release(self, event: Any) -> bool:
        return self._dispatch_input("mouse_release", event)

    def key_press(self, event: Any) -> bool:
        return self._dispatch_input("key_press", event)

    def key_release(self, event: Any) -> bool:
        return self._dispatch_input("key_release", event)

    def _dispatch_input(self, method_name: str, event: Any) -> bool:
        self._ensure_active()
        tool = self._active_tool
        if tool is None:
            return False
        handler = getattr(tool, method_name, None)
        if not callable(handler):
            return False
        result = handler(event)
        return bool(result) if result is not None else True

    def cancel(self) -> bool:
        self._ensure_active()
        if self._active_tool is None:
            return False
        return bool(self._active_tool.cancel())

    def reset(self) -> None:
        self._ensure_active()
        if self._active_tool is not None:
            self._active_tool.reset()

    def get_state(self) -> dict[str, Any]:
        return {
            "disposed": self._disposed,
            "tool_ids": self.get_tool_ids() if not self._disposed else (),
            "active_tool_id": self._active_tool_id,
            "active": self._active_tool is not None,
            "instance_count": len(self._tool_instances),
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        if self._active_tool is not None:
            self._active_tool.deactivate()
            self._active_tool = None
            self._active_tool_id = None
        for tool_id, tool in tuple(self._tool_instances.items()):
            self._dispose_tool(tool)
            del self._tool_instances[tool_id]
        self._tool_registry.clear()
        self._disposed = True

    @staticmethod
    def _dispose_tool(tool: Any) -> None:
        dispose = getattr(tool, "dispose", None)
        if callable(dispose):
            dispose()

    @staticmethod
    def _validate_tool_id(tool_id: str) -> None:
        if not isinstance(tool_id, str):
            raise TypeError("tool_id must be a string.")
        if not tool_id.strip():
            raise ValueError("tool_id must not be empty.")

    def _ensure_active(self) -> None:
        if self._disposed:
            raise RuntimeError("ToolManager has been disposed.")


__all__ = ["ToolFactory", "ToolManager"]
