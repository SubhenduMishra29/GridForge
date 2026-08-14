"""
GridForge V2
============

File:
    ui/plugins/plugin_context.py

Purpose
-------
Defines the shared application/UI context supplied to GridForge
composition plugins.

Architectural rules
-------------------
- PluginContext carries references; it does not own application state.
- Plugins must not use this context to bypass established controllers
  or service boundaries.
- Core/domain objects remain authoritative outside the UI.
- PluginContext contains no Qt widget construction logic.
- MainWindow and plugin composition remain separate concerns.
- PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from PySide6.QtWidgets import QWidget


# ============================================================
# PLUGIN CONTEXT
# ============================================================


@dataclass(slots=True)
class PluginContext:
    """
    Shared dependency context for GridForge UI plugins.

    The context is intentionally a lightweight dependency carrier.
    It does not create services, widgets, tools, renderers, or domain
    objects.

    Plugins may receive narrower, plugin-specific context objects
    derived from this context when stronger dependency isolation is
    required.
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

    services: Mapping[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    metadata: Mapping[
        str,
        Any,
    ] = field(
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

        Explicit fields should be preferred for architectural
        dependencies. The generic services mapping is intended for
        genuinely optional application services.
        """

        if not isinstance(
            name,
            str,
        ) or not name.strip():
            raise ValueError(
                "name must be a non-empty string."
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
        Return a named service or raise KeyError.
        """

        value = self.service(
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
        """

        values = {
            name: getattr(
                self,
                name,
            )
            for name in (
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
        )

        unknown = set(
            overrides
        ).difference(
            values
        )

        if unknown:
            raise TypeError(
                (
                    "Unknown PluginContext "
                    f"fields: {', '.join(sorted(unknown))}"
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
        Validate that required context fields are available.

        This performs dependency validation only; it does not construct
        missing services.
        """

        for field_name in required:
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

        return self.service(
            name
        ) is not None

    def has_core_controller(self) -> bool:
        """Return whether a project/core controller is available."""

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
        """Return whether the primary canvas dependencies exist."""

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
        """Return a context with a different main window."""

        return self.derive(
            main_window=main_window
        )

    def with_parent(
        self,
        parent: QWidget,
    ) -> PluginContext:
        """Return a context with a different Qt parent."""

        return self.derive(
            parent=parent
        )

    def with_service(
        self,
        name: str,
        service: Any,
    ) -> PluginContext:
        """
        Return a context with one optional service added/replaced.
        """

        if not isinstance(
            name,
            str,
        ) or not name.strip():
            raise ValueError(
                "name must be a non-empty string."
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
        """Return a context with one metadata value added/replaced."""

        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "key must be a non-empty string."
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


# ============================================================
# FACTORY
# ============================================================


def create_plugin_context(
    **kwargs: Any,
) -> PluginContext:
    """
    Create a PluginContext.

    Construction is intentionally dependency-injection only; this
    function does not create any missing services.
    """

    return PluginContext(
        **kwargs
    )


__all__ = [
    "PluginContext",
    "create_plugin_context",
]
