"""
GridForge V2 — Plugin Dependency Context.
Author: Subhendu Mishra

Immutable dependency carrier for UI composition plugins. It carries references
to already-created application and UI services; it does not create or own them.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Any, Mapping

from ui.core.qt import QWidget


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Immutable dependency context for GridForge UI plugins."""

    main_window: QWidget | None = None
    parent: QWidget | None = None
    application: Any = None
    gridforge_application: Any = None
    root_widget: QWidget | None = None
    controller: Any = None

    project: Any = None
    project_controller: Any = None
    command_manager: Any = None
    event_bus: Any = None

    # Active presentation document supplied by application composition.
    sld_document: Any = None
    # Renderer-neutral projection boundary between SLD and Canvas.
    sld_canvas_projection: Any = None
    # Transient graphics realization of the SLD canvas snapshot.
    sld_canvas_render_system: Any = None

    tool_manager: Any = None
    tool_registry: Any = None
    tool_dispatcher: Any = None
    interaction_manager: Any = None
    renderer_registry: Any = None
    render_system: Any = None
    snap_system: Any = None
    navigation_controller: Any = None
    coordinate_system: Any = None
    grid_system: Any = None

    selection_controller: Any = None
    action_manager: Any = None
    status_manager: Any = None
    settings: Any = None

    services: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.services, Mapping):
            raise TypeError("services must be a mapping.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "services", MappingProxyType(dict(self.services)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def service(self, name: str, default: Any = None) -> Any:
        self._validate_name(name, "name")
        return self.services.get(name, default)

    def require_service(self, name: str) -> Any:
        self._validate_name(name, "name")
        if name not in self.services:
            raise KeyError(f"Required extension service {name!r} is not available.")
        value = self.services[name]
        if value is None:
            raise RuntimeError(f"Required extension service {name!r} is None.")
        return value

    def has_service(self, name: str) -> bool:
        self._validate_name(name, "name")
        return name in self.services and self.services[name] is not None

    def derive(self, **overrides: Any) -> "PluginContext":
        names = tuple(item.name for item in fields(self))
        unknown = set(overrides).difference(names)
        if unknown:
            raise TypeError("Unknown PluginContext fields: " + ", ".join(sorted(unknown)))
        values = {name: getattr(self, name) for name in names}
        values.update(overrides)
        return type(self)(**values)

    def validate(self, *, required: tuple[str, ...] = ()) -> None:
        if not isinstance(required, tuple):
            raise TypeError("required must be a tuple.")
        valid = {item.name for item in fields(self) if item.name not in {"services", "metadata"}}
        for field_name in required:
            self._validate_name(field_name, "required dependency name")
            if field_name not in valid:
                raise KeyError(f"Unknown PluginContext dependency field: {field_name!r}")
            if getattr(self, field_name) is None:
                raise RuntimeError(f"Required plugin context dependency {field_name!r} is unavailable.")

    def has_controller(self) -> bool:
        return self.controller is not None

    def has_root_widget(self) -> bool:
        return self.root_widget is not None

    def has_core_controller(self) -> bool:
        return self.project_controller is not None

    def has_tool_system(self) -> bool:
        return self.tool_manager is not None and self.tool_registry is not None and self.tool_dispatcher is not None

    def has_renderer_system(self) -> bool:
        return self.renderer_registry is not None and self.render_system is not None

    def has_canvas_system(self) -> bool:
        return (
            self.interaction_manager is not None
            and self.navigation_controller is not None
            and self.coordinate_system is not None
            and self.render_system is not None
        )

    def with_main_window(self, main_window: QWidget) -> "PluginContext":
        self._validate_qwidget(main_window, "main_window")
        return self.derive(main_window=main_window)

    def with_parent(self, parent: QWidget) -> "PluginContext":
        self._validate_qwidget(parent, "parent")
        return self.derive(parent=parent)

    def with_root_widget(self, root_widget: QWidget) -> "PluginContext":
        self._validate_qwidget(root_widget, "root_widget")
        return self.derive(root_widget=root_widget)

    def with_controller(self, controller: Any) -> "PluginContext":
        if controller is None:
            raise ValueError("controller cannot be None.")
        return self.derive(controller=controller)

    def with_service(self, name: str, service: Any) -> "PluginContext":
        self._validate_name(name, "name")
        services = dict(self.services)
        services[name] = service
        return self.derive(services=services)

    def with_metadata(self, key: str, value: Any) -> "PluginContext":
        self._validate_name(key, "key")
        metadata = dict(self.metadata)
        metadata[key] = value
        return self.derive(metadata=metadata)

    @staticmethod
    def _validate_name(value: Any, parameter_name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{parameter_name} must be a string.")
        if not value.strip():
            raise ValueError(f"{parameter_name} must be a non-empty string.")

    @staticmethod
    def _validate_qwidget(value: Any, parameter_name: str) -> None:
        if not isinstance(value, QWidget):
            raise TypeError(f"{parameter_name} must be a QWidget.")


def create_plugin_context(**kwargs: Any) -> PluginContext:
    """Create a PluginContext through explicit dependency injection."""
    return PluginContext(**kwargs)


__all__ = ["PluginContext", "create_plugin_context"]
