"""
GridForge V2
============

File:
    ui/plugins/panels_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application-side panel area of the GridForge UI.

Architectural rules
-------------------
- The plugin owns panel composition, not panel/domain state.
- Panels are presentation components.
- The plugin must not perform electrical calculations.
- The plugin must not mutate Core directly.
- The plugin must not own authoritative project/network state.
- Panel contents should communicate through established application
  services/controllers.
- MainWindow remains thin and plugin-driven.
- PySide6 is the only Qt binding used by GridForge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QDockWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.core.qt import QtWidgets


# ============================================================
# PANEL SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class PanelSpec:
    """
    Declarative description of one UI panel.

    PanelSpec contains presentation metadata only. It does not own
    panel widgets or application state.
    """

    panel_id: str

    title: str

    widget: Optional[QWidget] = None

    area: Any = None

    closable: bool = True

    movable: bool = True

    floatable: bool = True

    visible: bool = True

    tabbed: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.panel_id,
            str,
        ) or not self.panel_id.strip():
            raise ValueError(
                "panel_id must be a non-empty string."
            )

        if not isinstance(
            self.title,
            str,
        ):
            raise TypeError(
                "title must be a string."
            )


# ============================================================
# PANEL CONTEXT
# ============================================================


@dataclass(slots=True)
class PanelsPluginContext:
    """
    Runtime dependencies supplied to PanelsPlugin.

    The context contains references to existing UI/application
    services. PanelsPlugin does not construct domain services.
    """

    parent: Optional[QWidget] = None

    main_window: Optional[QWidget] = None

    panel_manager: Any = None

    project_controller: Any = None

    selection_controller: Any = None

    tool_manager: Any = None

    panels: Iterable[PanelSpec] = field(
        default_factory=tuple
    )


# ============================================================
# PANELS PLUGIN
# ============================================================


class PanelsPlugin(QObject):
    """
    Composition plugin for GridForge application panels.

    The plugin provides a panel host and manages panel presentation
    widgets. It does not own authoritative application state.
    """

    plugin_id = "panels"
    plugin_name = "Panels"
    plugin_version = "1.0"

    def __init__(
        self,
        context: Optional[
            PanelsPluginContext
        ] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._context = (
            context
            or PanelsPluginContext()
        )

        self._widget: Optional[
            QWidget
        ] = None

        self._panel_host: Optional[
            QWidget
        ] = None

        self._tab_host: Optional[
            QTabWidget
        ] = None

        self._panels: dict[
            str,
            QWidget,
        ] = {}

        self._dock_widgets: dict[
            str,
            QDockWidget,
        ] = {}

        self._panel_specs: dict[
            str,
            PanelSpec,
        ] = {}

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> PanelsPluginContext:
        """Return the plugin context."""

        return self._context

    @property
    def widget(
        self,
    ) -> Optional[QWidget]:
        """Return the plugin root widget."""

        return self._widget

    @property
    def panel_host(
        self,
    ) -> Optional[QWidget]:
        """Return the panel host widget."""

        return self._panel_host

    @property
    def tab_host(
        self,
    ) -> Optional[QTabWidget]:
        """Return the tab host."""

        return self._tab_host

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Optional[
            PanelsPluginContext
        ] = None,
    ) -> QWidget:
        """
        Initialize the panel plugin.

        Initialization is idempotent.
        """

        if self._initialized:
            assert self._widget is not None
            return self._widget

        if context is not None:
            self._context = context

        self._create_host()

        self._register_context_panels()

        self._wire_services()

        self._initialized = True

        assert self._widget is not None

        return self._widget

    def shutdown(self) -> None:
        """
        Shut down the plugin.

        Panel widgets remain normal Qt-owned presentation objects.
        Application/domain services are not destroyed here.
        """

        self._disconnect_services()

        self._panels.clear()
        self._panel_specs.clear()
        self._dock_widgets.clear()

        self._tab_host = None
        self._panel_host = None
        self._widget = None

        self._initialized = False

    # ========================================================
    # HOST CREATION
    # ========================================================

    def _create_host(self) -> None:
        """
        Create the panel composition host.

        A tab host is used as the portable default. When MainWindow
        integration requires dock widgets, add_panel() can create a
        QDockWidget when a MainWindow is available.
        """

        self._panel_host = QWidget(
            self._context.parent
        )

        layout = QVBoxLayout(
            self._panel_host
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self._tab_host = QTabWidget(
            self._panel_host
        )

        layout.addWidget(
            self._tab_host
        )

        self._widget = self._panel_host

    # ========================================================
    # PANEL REGISTRATION
    # ========================================================

    def _register_context_panels(self) -> None:
        """Register panels supplied by the plugin context."""

        for spec in tuple(
            self._context.panels
        ):
            self.add_panel(
                spec
            )

    def add_panel(
        self,
        spec: PanelSpec,
    ) -> QWidget:
        """
        Add a panel according to its specification.

        Existing panel IDs are rejected to prevent ambiguous panel
        ownership.
        """

        if not isinstance(
            spec,
            PanelSpec,
        ):
            raise TypeError(
                "spec must be PanelSpec."
            )

        if spec.panel_id in self._panel_specs:
            raise ValueError(
                (
                    f"Panel {spec.panel_id!r} "
                    "is already registered."
                )
            )

        widget = spec.widget

        if widget is None:
            widget = QWidget(
                self._panel_host
            )

        self._panel_specs[
            spec.panel_id
        ] = spec

        self._panels[
            spec.panel_id
        ] = widget

        if spec.tabbed:
            self._add_tab_panel(
                spec,
                widget,
            )
        else:
            self._add_standard_panel(
                spec,
                widget,
            )

        return widget

    def remove_panel(
        self,
        panel_id: str,
    ) -> Optional[QWidget]:
        """
        Remove a panel from the composition.

        Returns the panel widget if it existed.
        """

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        widget = self._panels.pop(
            panel_id,
            None,
        )

        self._panel_specs.pop(
            panel_id,
            None,
        )

        dock = self._dock_widgets.pop(
            panel_id,
            None,
        )

        if dock is not None:
            dock.close()
            dock.deleteLater()

        if (
            widget is not None
            and self._tab_host is not None
        ):
            index = self._tab_host.indexOf(
                widget
            )

            if index >= 0:
                self._tab_host.removeTab(
                    index
                )

        return widget

    def panel(
        self,
        panel_id: str,
    ) -> Optional[QWidget]:
        """Return a registered panel widget."""

        return self._panels.get(
            panel_id
        )

    def panels(
        self,
    ) -> tuple[
        QWidget,
        ...
    ]:
        """Return all registered panel widgets."""

        return tuple(
            self._panels.values()
        )

    def panel_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered panel identifiers."""

        return tuple(
            self._panels.keys()
        )

    # ========================================================
    # PANEL PRESENTATION
    # ========================================================

    def _add_tab_panel(
        self,
        spec: PanelSpec,
        widget: QWidget,
    ) -> None:
        """Add a panel to the tab host."""

        if self._tab_host is None:
            raise RuntimeError(
                "Panel host has not been initialized."
            )

        self._tab_host.addTab(
            widget,
            spec.title,
        )

        index = self._tab_host.indexOf(
            widget
        )

        self._tab_host.setTabVisible(
            index,
            spec.visible,
        )

    def _add_standard_panel(
        self,
        spec: PanelSpec,
        widget: QWidget,
    ) -> None:
        """
        Add a standard panel.

        When a QMainWindow is available, use a dock widget. Otherwise
        fall back to the tab host so the plugin remains usable in
        isolation and in tests.
        """

        main_window = (
            self._context.main_window
        )

        if (
            main_window is not None
            and hasattr(
                main_window,
                "addDockWidget",
            )
        ):
            dock = QDockWidget(
                spec.title,
                main_window,
            )

            dock.setWidget(
                widget
            )

            dock.setFeatures(
                self._dock_features(
                    spec
                )
            )

            area = (
                spec.area
                if spec.area is not None
                else QtWidgets.LeftDockWidgetArea
            )

            main_window.addDockWidget(
                area,
                dock,
            )

            dock.setVisible(
                spec.visible
            )

            self._dock_widgets[
                spec.panel_id
            ] = dock

            return

        self._add_tab_panel(
            spec,
            widget,
        )

    @staticmethod
    def _dock_features(
        spec: PanelSpec,
    ) -> QDockWidget.DockWidgetFeatures:
        """Build dock-widget feature flags."""

        features = (
            QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )

        if spec.closable:
            features |= (
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )

        if spec.movable:
            features |= (
                QDockWidget.DockWidgetFeature.DockWidgetMovable
            )

        if spec.floatable:
            features |= (
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )

        return features

    # ========================================================
    # VISIBILITY
    # ========================================================

    def set_panel_visible(
        self,
        panel_id: str,
        visible: bool,
    ) -> None:
        """Set panel visibility."""

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

        widget = self._panels.get(
            panel_id
        )

        if widget is None:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        dock = self._dock_widgets.get(
            panel_id
        )

        if dock is not None:
            dock.setVisible(
                visible
            )
            return

        if (
            self._tab_host is not None
        ):
            index = self._tab_host.indexOf(
                widget
            )

            if index >= 0:
                self._tab_host.setTabVisible(
                    index,
                    visible,
                )

    def is_panel_visible(
        self,
        panel_id: str,
    ) -> bool:
        """Return panel visibility."""

        widget = self._panels.get(
            panel_id
        )

        if widget is None:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        dock = self._dock_widgets.get(
            panel_id
        )

        if dock is not None:
            return dock.isVisible()

        if (
            self._tab_host is not None
        ):
            index = self._tab_host.indexOf(
                widget
            )

            if index >= 0:
                return self._tab_host.isTabVisible(
                    index
                )

        return widget.isVisible()

    # ========================================================
    # WIRING
    # ========================================================

    def _wire_services(self) -> None:
        """
        Give existing application services an opportunity to attach
        to the panel composition.

        Services are optional and remain outside plugin ownership.
        """

        self._attach_service(
            self._context.panel_manager
        )

        self._attach_service(
            self._context.project_controller
        )

        self._attach_service(
            self._context.selection_controller
        )

        self._attach_service(
            self._context.tool_manager
        )

    def _disconnect_services(self) -> None:
        """Detach plugin-owned service references."""

        services = (
            self._context.panel_manager,
            self._context.project_controller,
            self._context.selection_controller,
            self._context.tool_manager,
        )

        for service in services:
            if service is None:
                continue

            self._invoke_optional(
                service,
                (
                    "detach_panels",
                    "detach_panel_host",
                    "clear_panel_host",
                ),
                self._widget,
            )

    def _attach_service(
        self,
        service: Any,
    ) -> None:
        """Attach the panel host to a compatible service."""

        if service is None:
            return

        self._invoke_optional(
            service,
            (
                "set_panel_host",
                "set_panels",
                "attach_panels",
                "attach_panel_host",
            ),
            self._widget,
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    def select_panel(
        self,
        panel_id: str,
    ) -> None:
        """Select a tabbed panel."""

        widget = self._panels.get(
            panel_id
        )

        if widget is None:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        if self._tab_host is None:
            return

        index = self._tab_host.indexOf(
            widget
        )

        if index >= 0:
            self._tab_host.setCurrentIndex(
                index
            )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def has_panel(
        self,
        panel_id: str,
    ) -> bool:
        """Return whether a panel is registered."""

        return panel_id in self._panels

    # ========================================================
    # INTERNAL HELPER
    # ========================================================

    @staticmethod
    def _invoke_optional(
        target: Any,
        method_names: tuple[str, ...],
        *args: Any,
    ) -> bool:
        """
        Invoke the first compatible service method.

        Exceptions raised by an existing method are intentionally not
        swallowed because they represent genuine integration errors.
        """

        for method_name in method_names:
            method = getattr(
                target,
                method_name,
                None,
            )

            if callable(method):
                method(*args)
                return True

        return False


# ============================================================
# FACTORY
# ============================================================


def create_panels_plugin(
    context: Optional[
        PanelsPluginContext
    ] = None,
    parent: Optional[QObject] = None,
) -> PanelsPlugin:
    """Create an uninitialized PanelsPlugin."""

    return PanelsPlugin(
        context=context,
        parent=parent,
    )


__all__ = [
    "PanelSpec",
    "PanelsPluginContext",
    "PanelsPlugin",
    "create_panels_plugin",
]
