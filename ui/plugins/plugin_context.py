"""
GridForge V2
============

File:
    ui/plugins/plugin_context.py

Purpose
-------
Defines the dependency context supplied to GridForge UI composition
plugins.

Architectural role
------------------
PluginContext is a dependency-carrier object.

It carries references to already-created application and UI services.
It does not create, resolve, own, or mutate those services.

It provides:

    - explicit dependency references;
    - controlled derived contexts;
    - required-dependency validation;
    - access to genuinely optional services.

It does NOT:

    - create services;
    - create widgets;
    - own application state;
    - own project/network state;
    - perform electrical calculations;
    - mutate Core;
    - construct controllers;
    - perform UI composition;
    - discover plugins;
    - manage plugin lifecycle.

Architectural rules
-------------------
- PluginContext carries references; it does not own application state.
- PluginContext is immutable after construction.
- Derived contexts are created explicitly through derive().
- Plugins must not use this context to bypass established controllers
  or service boundaries.
- Core/domain objects remain authoritative outside the UI.
- PluginContext contains no Qt construction logic.
- MainWindow and plugin composition remain separate concerns.
- All Qt access goes through ui.core.qt.
- PySide6 is the sole Qt backend and is hidden behind ui.core.qt.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
    fields,
)
from types import MappingProxyType
from typing import (
    Any,
    Mapping,
)

from ui.core.qt import QWidget


# ============================================================
# PLUGIN CONTEXT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginContext:
    """
    Immutable dependency context for GridForge UI plugins.

    PluginContext is a lightweight dependency carrier.

    It contains references to already-created objects but does not
    create or own those objects.

    Plugins may derive narrower contexts when stronger dependency
    isolation is required.

    The context itself must not become a replacement for established
    application/controller/service boundaries.
    """

    # --------------------------------------------------------
    # Application / Window
    # --------------------------------------------------------

    main_window: QWidget | None = None

    parent: QWidget | None = None

    application: Any = None

    # --------------------------------------------------------
    # Core application services
    # --------------------------------------------------------

    project: Any = None

    project_controller: Any = None

    controller: Any = None

    command_manager: Any = None

    event_bus: Any = None

    # --------------------------------------------------------
    # UI services
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Plugin infrastructure
    # --------------------------------------------------------

    plugin_manager: Any = None

    plugin_registry: Any = None

    plugin_loader: Any = None

    # --------------------------------------------------------
    # Optional application services
    # --------------------------------------------------------

    selection_controller: Any = None

    action_manager: Any = None

    status_manager: Any = None

    settings: Any = None

    services: Mapping[str, Any] = field(
        default_factory=dict
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # POST INITIALIZATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Normalize mapping fields into immutable mapping views.

        The objects referenced by the context remain owned by their
        respective subsystems. Only the context's mapping containers
        are protected from mutation.
        """

        object.__setattr__(
            self,
            "services",
            MappingProxyType(
                dict(self.services)
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )

    # ========================================================
    # SERVICE ACCESS
    # ========================================================

    def service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return an optional service.

        The generic services mapping is intentionally reserved for
        genuinely optional services.

        Explicitly declared PluginContext fields should be preferred
        for architectural dependencies.
        """

        self._validate_name(
            name,
            "name",
        )

        return self.services.get(
            name,
            default,
        )

    def require_service(
        self,
        name: str,
    ) -> Any:
        """
        Return a required optional service.

        Raises
        ------
        KeyError
            If the service is not present.

        RuntimeError
            If the service is explicitly present but has value None.
        """

        self._validate_name(
            name,
            "name",
        )

        if name not in self.services:
            raise KeyError(
                (
                    f"Required service "
                    f"{name!r} is not available."
                )
            )

        value = self.services[name]

        if value is None:
            raise RuntimeError(
                (
                    f"Required service "
                    f"{name!r} is available but "
                    "has value None."
                )
            )

        return value

    def has_service(
        self,
        name: str,
    ) -> bool:
        """Return whether a non-None optional service exists."""

        self._validate_name(
            name,
            "name",
        )

        return (
            name in self.services
            and self.services[name] is not None
        )

    # ========================================================
    # CONTEXT DERIVATION
    # ========================================================

    def derive(
        self,
        **overrides: Any,
    ) -> PluginContext:
        """
        Create a derived context.

        The current context remains unchanged.

        Only actual PluginContext dataclass fields may be overridden.
        """

        field_names = {
            item.name
            for item in fields(
                self
            )
        }

        unknown = set(
            overrides
        ).difference(
            field_names
        )

        if unknown:
            raise TypeError(
                (
                    "Unknown PluginContext fields: "
                    + ", ".join(
                        sorted(unknown)
                    )
                )
            )

        values = {
            name: getattr(
                self,
                name,
            )
            for name in field_names
        }

        values.update(
            overrides
        )

        return type(self)(
            **values
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        *,
        required: tuple[str, ...] = (),
    ) -> None:
        """
        Validate required context dependencies.

        Validation only checks availability.

        It never:

            - creates dependencies;
            - resolves dependencies;
            - substitutes dependencies;
            - modifies the context.
        """

        valid_fields = {
            item.name
            for item in fields(
                self
            )
        }

        for field_name in required:
            self._validate_name(
                field_name,
                "required dependency name",
            )

            if field_name not in valid_fields:
                raise KeyError(
                    (
                        f"Unknown PluginContext "
                        f"field: {field_name!r}"
                    )
                )

            if getattr(
                self,
                field_name,
            ) is None:
                raise RuntimeError(
                    (
                        f"Required plugin context "
                        f"dependency {field_name!r} "
                        "is not available."
                    )
                )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def has_core_controller(self) -> bool:
        """
        Return whether a usable core/application controller reference
        exists.
        """

        return (
            self.project_controller is not None
            or self.controller is not None
        )

    def has_tool_system(self) -> bool:
        """Return whether a UI tool-system dependency exists."""

        return (
            self.tool_manager is not None
            or self.tool_registry is not None
            or self.tool_dispatcher is not None
        )

    def has_renderer_system(self) -> bool:
        """Return whether a renderer-system dependency exists."""

        return (
            self.renderer_registry is not None
            or self.render_system is not None
        )

    def has_canvas_system(self) -> bool:
        """
        Return whether the minimum canvas interaction dependencies
        are available.
        """

        return (
            self.interaction_manager is not None
            or self.navigation_controller is not None
            or self.coordinate_system is not None
            or self.render_system is not None
        )

    # ========================================================
    # IMMUTABLE-STYLE UPDATE HELPERS
    # ========================================================

    def with_main_window(
        self,
        main_window: QWidget,
    ) -> PluginContext:
        """Return a derived context with a different main window."""

        self._validate_qwidget(
            main_window,
            "main_window",
        )

        return self.derive(
            main_window=main_window
        )

    def with_parent(
        self,
        parent: QWidget,
    ) -> PluginContext:
        """Return a derived context with a different Qt parent."""

        self._validate_qwidget(
            parent,
            "parent",
        )

        return self.derive(
            parent=parent
        )

    def with_service(
        self,
        name: str,
        service: Any,
    ) -> PluginContext:
        """
        Return a derived context with one optional service added or
        replaced.
        """

        self._validate_name(
            name,
            "name",
        )

        services = dict(
            self.services
        )

        services[name] = service

        return self.derive(
            services=services
        )

    def with_metadata(
        self,
        key: str,
        value: Any,
    ) -> PluginContext:
        """Return a derived context with one metadata value added."""

        self._validate_name(
            key,
            "key",
        )

        metadata = dict(
            self.metadata
        )

        metadata[key] = value

        return self.derive(
            metadata=metadata
        )

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_name(
        value: Any,
        parameter_name: str,
    ) -> None:
        """Validate a context/service identifier."""

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise ValueError(
                (
                    f"{parameter_name} must be "
                    "a non-empty string."
                )
            )

    @staticmethod
    def _validate_qwidget(
        value: Any,
        parameter_name: str,
    ) -> None:
        """Validate a Qt widget reference."""

        if not isinstance(
            value,
            QWidget,
        ):
            raise TypeError(
                f"{parameter_name} must be a QWidget."
            )


# ============================================================
# FACTORY
# ============================================================


def create_plugin_context(
    **kwargs: Any,
) -> PluginContext:
    """
    Create a PluginContext.

    This is dependency injection only.

    No service, controller, widget, or Core object is created,
    discovered, or resolved here.
    """

    return PluginContext(
        **kwargs
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PluginContext",
    "create_plugin_context",
]
