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
- Panel contents communicate through established application
  services/controllers.
- MainWindow remains thin and plugin-driven.
- Qt access occurs exclusively through ui.core.qt.
- No direct PySide6/PyQt imports are permitted here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from ui.core.qt import (
    QDockWidget,
    QMainWindow,
    QObject,
    QVBoxLayout,
    QWidget,
    Qt,
)


# ============================================================
# PANEL SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class PanelSpec:
    """
    Declarative description of one UI panel.

    PanelSpec contains presentation metadata only.

    It does not own application state or panel lifecycle.
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

        if self.area is not None:
            # Qt dock areas are enum values. We deliberately do not
            # hard-code a specific enum type here because the Qt
            # abstraction layer owns the backend representation.
            if not isinstance(
                self.area,
                Qt.DockWidgetArea,
            ):
                raise TypeError(
                    "area must be a Qt.DockWidgetArea value."
                )


# ============================================================
# PANEL CONTEXT
# ============================================================


@dataclass(slots=True)
class PanelsPluginContext:
    """
    Runtime dependencies supplied to PanelsPlugin.

    The context contains references to already-created UI/application
    services. PanelsPlugin does not construct domain services.
    """

    parent: Optional[QWidget] = None

    main_window: Optional[QMainWindow] = None

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

    PanelsPlugin owns the composition of panel widgets and dock
    containers.

    It does not own:

        - project state
        - network topology
        - electrical calculations
        - command history
        - undo/redo state
        - simulation state
        - Core/domain services
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
        super().__init__(
            parent
        )

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
    def context(
        self,
    ) -> PanelsPluginContext:
        """Return the current plugin context."""

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
        """Return the portable panel host widget."""

        return self._panel_host

    @property
    def initialized(
        self,
    ) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def dock_widgets(
        self,
    ) -> tuple[QDockWidget, ...]:
        """Return all managed dock widgets."""

        return tuple(
            self._dock_widgets.values()
        )

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
        Initialize the panel composition.

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

    def shutdown(
        self,
    ) -> None:
        """
        Shut down panel composition.

        Application services are not destroyed here.

        Dock widgets are detached from the MainWindow and scheduled
        for Qt deletion. The panel widgets themselves remain ordinary
        Qt-owned presentation objects.
        """

        if not self._initialized:
            return

        self._disconnect_services()

        self._remove_all_docks()

        self._panels.clear()

        self._panel_specs.clear()

        self._panel_host = None

        self._widget = None

        self._initialized = False

    # ========================================================
    # HOST CREATION
    # ========================================================

    def _create_host(
        self,
    ) -> None:
        """
        Create the portable panel composition host.

        The host is deliberately a simple QWidget. Actual application
        panels are represented by QDockWidgets when a MainWindow is
        available.

        This avoids introducing QTabWidget into the central Qt
        abstraction merely for panel composition.
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

        self._widget = self._panel_host

    # ========================================================
    # PANEL REGISTRATION
    # ========================================================

    def _register_context_panels(
        self,
    ) -> None:
        """Register panels supplied through the plugin context."""

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
        Add a panel to the composition.

        Existing panel IDs are rejected.
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

        self._add_panel_dock(
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

        self._validate_panel_id(
            panel_id
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
            main_window = (
                self._context.main_window
            )

            if main_window is not None:
                self._remove_dock_from_main_window(
                    main_window,
                    dock,
                )

            dock.close()
            dock.deleteLater()

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
    ) -> tuple[QWidget, ...]:
        """Return all registered panel widgets."""

        return tuple(
            self._panels.values()
        )

    def panel_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered panel IDs."""

        return tuple(
            self._panels.keys()
        )

    # ========================================================
    # DOCK CREATION
    # ========================================================

    def _add_panel_dock(
        self,
        spec: PanelSpec,
        widget: QWidget,
    ) -> None:
        """
        Create and register a dock widget for a panel.

        If no MainWindow is available, the widget remains available
        through the plugin's portable root widget but is not attached
        to an application window.
        """

        main_window = (
            self._context.main_window
        )

        if main_window is None:
            return

        dock = QDockWidget(
            spec.title,
            main_window,
        )

        dock.setObjectName(
            f"gridforge_panel_{spec.panel_id}"
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
            else Qt.DockWidgetArea.LeftDockWidgetArea
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

        if spec.tabbed:
            self._tabify_with_previous_panel(
                spec,
                dock,
                main_window,
            )

    def _tabify_with_previous_panel(
        self,
        spec: PanelSpec,
        dock: QDockWidget,
        main_window: QMainWindow,
    ) -> None:
        """
        Tabify a new dock with the most recent compatible panel.

        Tabification is delegated to QMainWindow because dock layout is
        a MainWindow composition concern.
        """

        for panel_id in reversed(
            tuple(
                self._dock_widgets.keys()
            )
        ):
            if panel_id == spec.panel_id:
                continue

            previous_spec = (
                self._panel_specs.get(
                    panel_id
                )
            )

            previous_dock = (
                self._dock_widgets.get(
                    panel_id
                )
            )

            if (
                previous_spec is None
                or previous_dock is None
            ):
                continue

            if (
                previous_spec.area
                == spec.area
            ):
                main_window.tabifyDockWidget(
                    previous_dock,
                    dock,
                )

                return

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

        self._validate_panel_id(
            panel_id
        )

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

        widget.setVisible(
            visible
        )

    def is_panel_visible(
        self,
        panel_id: str,
    ) -> bool:
        """Return panel visibility."""

        self._validate_panel_id(
            panel_id
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
            return dock.isVisible()

        return widget.isVisible()

    # ========================================================
    # TAB / DOCK OPERATIONS
    # ========================================================

    def select_panel(
        self,
        panel_id: str,
    ) -> None:
        """
        Select/show a panel.

        For dock-based panels this makes the dock visible and raises
        it to the foreground. QMainWindow owns the actual dock layout.
        """

        self._validate_panel_id(
            panel_id
        )

        dock = self._dock_widgets.get(
            panel_id
        )

        if dock is not None:
            dock.show()
            dock.raise_()
            return

        widget = self._panels.get(
            panel_id
        )

        if widget is None:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        widget.show()
        widget.raise_()

    # ========================================================
    # SERVICE WIRING
    # ========================================================

    def _wire_services(
        self,
    ) -> None:
        """
        Give existing application services an opportunity to attach
        to the panel composition.

        Services remain outside plugin ownership.
        """

        services = (
            self._context.panel_manager,
            self._context.project_controller,
            self._context.selection_controller,
            self._context.tool_manager,
        )

        for service in services:
            self._attach_service(
                service
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

    def _disconnect_services(
        self,
    ) -> None:
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

    # ========================================================
    # CAPABILITIES
    # ========================================================

    def has_panel(
        self,
        panel_id: str,
    ) -> bool:
        """Return whether a panel is registered."""

        return panel_id in self._panels

    def has_dock(
        self,
        panel_id: str,
    ) -> bool:
        """Return whether a panel currently has a dock widget."""

        return panel_id in self._dock_widgets

    # ========================================================
    # CLEANUP
    # ========================================================

    def _remove_all_docks(
        self,
    ) -> None:
        """Detach and schedule deletion of all managed docks."""

        main_window = (
            self._context.main_window
        )

        docks = tuple(
            self._dock_widgets.values()
        )

        self._dock_widgets.clear()

        for dock in docks:
            if main_window is not None:
                self._remove_dock_from_main_window(
                    main_window,
                    dock,
                )

            dock.close()
            dock.deleteLater()

    @staticmethod
    def _remove_dock_from_main_window(
        main_window: QMainWindow,
        dock: QDockWidget,
    ) -> None:
        """
        Remove a dock from the MainWindow.

        QMainWindow does not expose an explicit removeDockWidget
        operation through application ownership semantics beyond this
        call; the dock is subsequently closed and scheduled for Qt
        deletion.
        """

        main_window.removeDockWidget(
            dock
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_panel_id(
        panel_id: str,
    ) -> None:
        """Validate a panel identifier."""

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        if not panel_id.strip():
            raise ValueError(
                "panel_id cannot be empty."
            )

    # ========================================================
    # OPTIONAL SERVICE HELPER
    # ========================================================

    @staticmethod
    def _invoke_optional(
        target: Any,
        method_names: tuple[str, ...],
        *args: Any,
    ) -> bool:
        """
        Invoke the first compatible service method.

        Exceptions raised by an existing method are deliberately not
        swallowed. They represent genuine integration failures.
        """

        for method_name in method_names:
            method = getattr(
                target,
                method_name,
                None,
            )

            if callable(
                method
            ):
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
    """
    Create an uninitialized PanelsPlugin.

    Construction does not initialize the plugin.
    """

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
