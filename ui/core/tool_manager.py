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

from ui.creation.creation_context import CreationContext


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
        preview_layer: Any = None,
        equipment_registry: Any = None,
        creation_context: CreationContext | None = None,
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
        self.preview_layer = preview_layer
        self.equipment_registry = equipment_registry
        self.creation_context = creation_context or CreationContext()
        self._tool_registry: dict[str, ToolFactory] = {}
        self._tool_instances: dict[str, Any] = {}
        self._active_tool_id: str | None = None
        self._active_tool: Any | None = None
        self._interaction_tool: Any | None = None
        self._disposed = False

        bind_controller = getattr(controller, "bind_tool_manager", None)
        if callable(bind_controller):
            bind_controller(self)

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
            preview_layer=self.preview_layer,
        )
        if tool is None:
            raise RuntimeError(f"Tool factory returned None: {tool_id!r}")
        bind_creation = getattr(tool, "bind_creation_context", None)
        if callable(bind_creation):
            bind_creation(self.creation_context)
        return tool

    def _get_or_create_tool(self, tool_id: str) -> Any:
        self._ensure_active()
        if tool_id not in self._tool_instances:
            self._tool_instances[tool_id] = self._create_tool(tool_id)
        return self._tool_instances[tool_id]

    def get_tool(self, tool_id: str) -> Any:
        """Return a lazily-created registered tool without changing the active tool."""
        self._ensure_active()
        self._validate_tool_id(tool_id)
        return self._get_or_create_tool(tool_id)

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

    def activate(
        self,
        tool_id: str | None,
        *,
        cancel_active_creation: bool = False,
    ) -> Any | None:
        """Activate a tool, optionally cancelling an explicit user-requested draft switch."""
        self._ensure_active()
        if tool_id is not None:
            self._validate_tool_id(tool_id)
            if tool_id not in self._tool_registry:
                raise KeyError(f"Unknown tool ID: {tool_id!r}")
            if tool_id == self._active_tool_id:
                if self.creation_context.active:
                    return self._active_tool
                if self.equipment_registry is not None:
                    definition = self._definition_for_tool(tool_id)
                    if definition is not None:
                        self.creation_context.begin(definition)
                return self._active_tool

        previous_id = self._active_tool_id
        previous_tool = self._active_tool
        previous_draft = self.creation_context.snapshot_draft()

        # Only an explicit caller may authorize cancellation of the active
        # transient creation session.  Palette switching uses this path; other
        # callers retain the strict lifecycle guard below.
        if (
            cancel_active_creation
            and previous_tool is not None
            and previous_id != tool_id
            and self.creation_context.active
        ):
            persist = getattr(previous_tool, "persist_transient_draft", None)
            if callable(persist):
                persist()
            self.cancel()

        # An active creation session may not be destroyed implicitly by a
        # tool switch.  The caller must explicitly authorize cancellation.
        if previous_tool is not None and previous_id != tool_id and self.creation_context.active:
            raise RuntimeError(
                "Active equipment creation must be explicitly cancelled before switching tools."
            )

        requested_tool = self._get_or_create_tool(tool_id) if tool_id is not None else None

        if previous_tool is not None:
            persist = getattr(previous_tool, "persist_transient_draft", None)
            if callable(persist) and self.creation_context.active:
                persist()
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
            self.creation_context.restore_draft(previous_draft)
            raise

        self._active_tool_id = tool_id
        self._active_tool = requested_tool
        try:
            if tool_id is not None and self.equipment_registry is not None:
                definition = self._definition_for_tool(tool_id)
                if definition is not None:
                    self.creation_context.begin(definition)
        except Exception:
            if requested_tool is not None:
                requested_tool.deactivate()
            self._active_tool_id = previous_id
            self._active_tool = previous_tool
            if previous_tool is not None:
                previous_tool.activate()
            self.creation_context.restore_draft(previous_draft)
            raise
        self._notify_controller_tool_change(previous_id, tool_id)
        return requested_tool

    def deactivate(self) -> None:
        self._ensure_active()
        self._clear_interaction_tool()
        if self._active_tool is None:
            return
        self._active_tool.deactivate()
        previous_id = self._active_tool_id
        self._active_tool = None
        self._active_tool_id = None
        self.creation_context.cancel()
        self._notify_controller_tool_change(previous_id, None)

    def _notify_controller_tool_change(self, previous_id: str | None, current_id: str | None) -> None:
        callback = getattr(self.controller, "_on_tool_manager_changed", None)
        if callable(callback):
            callback(current_id, previous_id)

    # ========================================================
    # Canonical Canvas Input Dispatch
    # ========================================================

    def mouse_press(self, event: Any) -> bool:
        return self._dispatch_input("mouse_press", event)

    def mouse_move(self, event: Any) -> bool:
        return self._dispatch_input("mouse_move", event)

    def mouse_release(self, event: Any) -> bool:
        return self._dispatch_input("mouse_release", event)

    def mouse_double_click(self, event: Any) -> bool:
        return self._dispatch_input("mouse_double_click", event)

    def key_press(self, event: Any) -> bool:
        return self._dispatch_input("key_press", event)

    def key_release(self, event: Any) -> bool:
        return self._dispatch_input("key_release", event)

    def _dispatch_input(self, method_name: str, event: Any) -> bool:
        self._ensure_active()
        tool = self._interaction_tool or self._active_tool
        if tool is None:
            return False

        # A creation tool may remain selected after draft placement. The
        # placement interaction ends and clears the transient CreationDraft,
        # while the tool remains active so repeated placements are still possible.
        # Re-establish the canonical transient session at the next input
        # boundary instead of allowing the tool to reach require_draft()
        # without an active session.
        self._ensure_creation_session()

        handler = getattr(tool, method_name, None)
        if not callable(handler):
            return False
        result = handler(event)
        handled = bool(result) if result is not None else True
        if self._interaction_tool is not None and method_name in {"mouse_release", "key_press"}:
            if method_name == "key_press" and not getattr(event, "key", None) and isinstance(event, dict) and event.get("key") not in ("Escape", "Key_Escape", 16777216):
                return handled
            if method_name == "mouse_release" and not handled:
                return handled
            self._clear_interaction_tool()
        return handled

    def begin_equipment_insertion(
        self,
        equipment_type: str,
        *,
        creation_parameters: dict[str, Any],
        orientation: float = 0.0,
        equipment_id: str | None = None,
        initial_event: Any | None = None,
    ) -> bool:
        """Temporarily route an equipment drag through ElectricalInsertionTool."""
        self._ensure_active()
        if self._interaction_tool is not None:
            return False
        tool = self.get_tool("electrical-insertion")
        begin = getattr(tool, "begin", None)
        if not callable(begin):
            return False
        begin(
            equipment_type,
            equipment_id=equipment_id,
            creation_parameters=creation_parameters,
            orientation=orientation,
        )
        tool.activate()
        self._interaction_tool = tool
        if initial_event is None:
            return True
        handler = getattr(tool, "mouse_press", None)
        if not callable(handler):
            self._clear_interaction_tool()
            return False
        handled = bool(handler(initial_event))
        if not handled:
            self._clear_interaction_tool()
        return handled

    def _clear_interaction_tool(self) -> None:
        tool = self._interaction_tool
        self._interaction_tool = None
        if tool is not None:
            try:
                tool.deactivate()
            except Exception:
                pass

    def _ensure_creation_session(self) -> None:
        """Ensure an active equipment tool has a canonical CreationDraft."""
        if self.creation_context.active or self._active_tool_id is None:
            return
        if self.equipment_registry is None:
            return
        definition = self._definition_for_tool(self._active_tool_id)
        if definition is not None:
            self.creation_context.begin(definition)

    def place_creation_draft(self) -> bool:
        """Persist the active placement as Application-owned DraftNetwork state."""
        self._ensure_active()
        tool = self._active_tool
        if tool is None:
            raise RuntimeError("No active tool is available for equipment placement.")
        place = getattr(tool, "place_creation_draft", None)
        if not callable(place):
            raise RuntimeError(f"Active tool {self._active_tool_id!r} does not support draft placement.")
        return bool(place())

    def cancel(self) -> bool:
        self._ensure_active()
        if self._active_tool is None:
            return False
        result = bool(self._active_tool.cancel())
        had_draft = self.creation_context.active
        self.creation_context.cancel()
        callback = getattr(self.controller, "_on_creation_cancelled", None)
        if callable(callback) and had_draft:
            callback()
        return result

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
            "interaction_tool_id": getattr(self._interaction_tool, "tool_id", None),
        }

    def dispose(self) -> None:
        if self._disposed:
            return
        self._clear_interaction_tool()
        if self._active_tool is not None:
            previous_id = self._active_tool_id
            self._active_tool.deactivate()
            self._active_tool = None
            self._active_tool_id = None
            self._notify_controller_tool_change(previous_id, None)
        for tool_id, tool in tuple(self._tool_instances.items()):
            self._dispose_tool(tool)
            del self._tool_instances[tool_id]
        self.creation_context.discard()
        self._tool_registry.clear()
        self._disposed = True

    def _definition_for_tool(self, tool_id: str) -> Any | None:
        registry = self.equipment_registry
        require = getattr(registry, "require", None) if registry is not None else None
        if not callable(require):
            return None
        try:
            definition = require(tool_id)
        except KeyError:
            return None
        return definition if getattr(definition, "tool_id", None) == tool_id else None

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
