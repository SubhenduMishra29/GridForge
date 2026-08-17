"""
GridForge V2
============

File:
    ui/plugins/plugin_context.py

Purpose
-------
Defines the shared application/UI context supplied to GridForge
composition plugins.

Architectural role
------------------
PluginContext is a dependency-carrier object used by composition
plugins.

It:

    - carries references to already-created application/UI services;
    - provides controlled context derivation;
    - provides dependency validation;
    - provides access to genuinely optional services.

It does NOT:

    - create services;
    - create widgets;
    - own application state;
    - own project/network state;
    - perform electrical calculations;
    - mutate Core;
    - construct controllers;
    - contain UI composition logic.

Architectural rules
-------------------
- PluginContext carries references; it does not own application state.
- Plugins must not use this context to bypass established controllers
  or service boundaries.
- Core/domain objects remain authoritative outside the UI.
- PluginContext contains no Qt widget construction logic.
- MainWindow and plugin composition remain separate concerns.
- All Qt access goes through ui.core.qt.
- PySide6 is the sole Qt backend and is hidden behind ui.core.qt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.core.qt import QWidget


# ============================================================
# PLUGIN CONTEXT
# ============================================================


@dataclass(slots=True)
class PluginContext:
    """
    Shared dependency context for GridForge UI plugins.

    PluginContext is intentionally a lightweight dependency carrier.

    It does not create or own:

        - application services
        - controllers
        - widgets
        - tools
        - renderers
        - domain objects
        - Core state

    Plugins may receive narrower, plugin-specific context objects
    when stronger dependency isolation is required.
    """

    # --------------------------------------------------------
    # Application / Window
    # --------------------------------------------------------

    main_window: Optional[QWidget] = None

    parent: Optional[QWidget] = None

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
    # SERVICE ACCESS
    # ========================================================

    def service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a named optional service.

        Explicit context fields should be preferred for architectural
        dependencies. The generic services mapping is reserved for
        genuinely optional application services.
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
        Return a named service.

        Raises
        ------
        KeyError
            If the requested service is unavailable.
        """

        self._validate_name(
            name,
            "name",
        )

        value = self.services.get(
            name
        )

        if value is None:
            raise KeyError(
                (
                    f"Required service "
                    f"{name!r} is not available."
                )
            )

        return value

    # ========================================================
    # CONTEXT DERIVATION
    # ========================================================

    def derive(
        self,
        **overrides: Any,
    ) -> PluginContext:
        """
        Create a derived context with selected values overridden.

        The original context is not modified.

        Only declared PluginContext fields may be overridden.
        """

        field_names = (
            "main_window",
            "parent",
            "application",
            "project",
            "project_controller",
            "controller",
            "command_manager",
            "event_bus",
            "tool_manager",
            "tool_registry",
            "tool_dispatcher",
            "interaction_manager",
            "renderer_registry",
            "render_system",
            "snap_system",
            "navigation_controller",
            "coordinate_system",
            "grid_system",
            "plugin_manager",
            "plugin_registry",
            "plugin_loader",
            "selection_controller",
            "action_manager",
            "status_manager",
            "settings",
            "services",
            "metadata",
        )

        values = {
            name: getattr(
                self,
                name,
            )
            for name in field_names
        }

        unknown = set(
            overrides
        ).difference(
            values
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

        values.update(
            overrides
        )

        return PluginContext(
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

        Validation only checks dependency availability.

        It never creates, resolves, or substitutes missing services.
        """

        for field_name in required:
            if not isinstance(
                field_name,
                str,
            ) or not field_name.strip():
                raise ValueError(
                    (
                        "required dependency names "
                        "must be non-empty strings."
                    )
                )

            if not hasattr(
                self,
                field_name,
            ):
                raise KeyError(
                    (
                        f"Unknown PluginContext "
                        f"field: {field_name!r}"
                    )
                )

            value = getattr(
                self,
                field_name,
            )

            if value is None:
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

    def has_service(
        self,
        name: str,
    ) -> bool:
        """Return whether a named optional service exists."""

        self._validate_name(
            name,
            "name",
        )

        return (
            self.services.get(
                name
            ) is not None
        )

    def has_core_controller(self) -> bool:
        """Return whether an application/core controller is available."""

        return (
            self.project_controller is not None
            or self.controller is not None
        )

    def has_tool_system(self) -> bool:
        """Return whether the UI tool system is available."""

        return (
            self.tool_manager is not None
            or self.tool_registry is not None
        )

    def has_renderer_system(self) -> bool:
        """Return whether the renderer system is available."""

        return (
            self.renderer_registry is not None
            or self.render_system is not None
        )

    def has_canvas_system(self) -> bool:
        """Return whether primary canvas dependencies exist."""

        return (
            self.interaction_manager is not None
            or self.navigation_controller is not None
            or self.coordinate_system is not None
        )

    # ========================================================
    # IMMUTABLE-STYLE UPDATE HELPERS
    # ========================================================

    def with_main_window(
        self,
        main_window: QWidget,
    ) -> PluginContext:
        """Return a derived context with a different main window."""

        if not isinstance(
            main_window,
            QWidget,
        ):
            raise TypeError(
                "main_window must be a QWidget."
            )

        return self.derive(
            main_window=main_window
        )

    def with_parent(
        self,
        parent: QWidget,
    ) -> PluginContext:
        """Return a derived context with a different Qt parent."""

        if not isinstance(
            parent,
            QWidget,
        ):
            raise TypeError(
                "parent must be a QWidget."
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

        services[
            name
        ] = service

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

        metadata[
            key
        ] = value

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


# ============================================================
# FACTORY
# ============================================================


def create_plugin_context(
    **kwargs: Any,
) -> PluginContext:
    """
    Create a PluginContext.

    Construction is dependency injection only.

    No missing services are created or resolved.
    """

    return PluginContext(
        **kwargs
    )


__all__ = [
    "PluginContext",
    "create_plugin_context",
]
