"""
GridForge V2
============

File:
    ui/plugins/panels_plugin.py

Purpose
-------
Composition plugin responsible for creating and managing the
application-side panel/dock area of the GridForge UI.

Architectural rules
-------------------
- The plugin owns panel composition, not application state.
- Panels are presentation components.
- The plugin must not perform electrical calculations.
- The plugin must not mutate Core directly.
- The plugin must not own authoritative project/network state.
- The plugin must not construct application services/controllers.
- MainWindow remains thin and plugin-driven.
- The shared PluginContext is the plugin dependency boundary.
- Qt access occurs exclusively through ui.core.qt.
- No direct PySide6/PyQt imports are permitted here.

Ownership
---------
PanelsPlugin owns the dock composition it creates.

MainWindow owns the overall dock-area/layout infrastructure.

Application/domain state remains outside this plugin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ui.core.qt import (
    QDockWidget,
    QMainWindow,
    QObject,
    QWidget,
    Qt,
)

from ui.plugins.plugin_context import PluginContext


# ============================================================
# PANEL SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class PanelSpec:
    """
    Declarative description of one UI panel.

    PanelSpec contains presentation metadata only.

    The supplied widget is a presentation object. It must not be
    treated as an application-state container by PanelsPlugin.
    """

    panel_id: str

    title: str

    widget: Optional[QWidget] = None

    area: Optional[Qt.DockWidgetArea] = None

    closable: bool = True

    movable: bool = True

    floatable: bool = True

    visible: bool = True

    tabbed: bool = False

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.panel_id, str)
            or not self.panel_id.strip()
        ):
            raise ValueError(
                "panel_id must be a non-empty string."
            )

        if not isinstance(self.title, str):
            raise TypeError(
                "title must be a string."
            )

        if self.widget is not None and not isinstance(
            self.widget,
            QWidget,
        ):
            raise TypeError(
                "widget must be QWidget or None."
            )

        if self.area is not None and not isinstance(
            self.area,
            Qt.DockWidgetArea,
        ):
            raise TypeError(
                "area must be a Qt.DockWidgetArea value."
            )


# ============================================================
# PANELS PLUGIN
# ============================================================


class PanelsPlugin(QObject):
    """
    GridForge panel/dock composition plugin.

    Responsibilities
    ----------------
    - create panel dock widgets;
    - register supplied presentation widgets;
    - configure dock presentation;
    - expose registered panels;
    - manage plugin-owned dock composition.

    Non-responsibilities
    --------------------
    - project state;
    - network topology;
    - electrical calculations;
    - commands;
    - undo/redo;
    - simulation state;
    - Core/domain ownership;
    - controller ownership;
    - service discovery;
    - application-state synchronization.

    Application coordination occurs outside this plugin through the
    established PluginContext/controller architecture.
    """

    plugin_id = "panels"
    plugin_name = "Panels"
    plugin_version = "1.0"
    plugin_description = (
        "GridForge application panel and dock composition."
    )

    plugin_dependencies: tuple[str, ...] = ()
    plugin_optional = False

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct the plugin.

        Construction performs no UI composition and accepts no
        application services.
        """

        super().__init__(parent)

        self._context: Optional[PluginContext] = None

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
    def context(self) -> Optional[PluginContext]:
        """Return the active shared plugin context."""

        return self._context

    @property
    def widget(self) -> Optional[QWidget]:
        """
        Return the plugin presentation root.

        Panels are dock-based, therefore there is no independent
        central panel widget. The MainWindow owns the dock layout.
        """

        return None

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def dock_widgets(self) -> tuple[QDockWidget, ...]:
        """Return all managed dock widgets."""

        return tuple(
            self._dock_widgets.values()
        )

    @property
    def panel_ids(self) -> tuple[str, ...]:
        """Return registered panel identifiers."""

        return tuple(
            self._panels.keys()
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: PluginContext,
    ) -> None:
        """
        Initialize panel composition.

        PluginContext is the sole application dependency boundary.

        Initialization is idempotent for the same lifecycle.
        """

        if not isinstance(
            context,
            PluginContext,
        ):
            raise TypeError(
                "PanelsPlugin requires PluginContext."
            )

        if self._initialized:
            if self._context is not context:
                raise RuntimeError(
                    "PanelsPlugin is already initialized "
                    "with a different PluginContext."
                )

            return

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                "PluginContext.main_window must be QMainWindow."
            )

        self._context = context

        self._initialized = True

    def shutdown(self) -> None:
        """
        Shut down panel composition.

        Application services and MainWindow are never destroyed.

        Managed dock widgets are removed from MainWindow and scheduled
        for Qt deletion.
        """

        if not self._initialized:
            return

        self._remove_all_docks()

        self._panels.clear()
        self._panel_specs.clear()

        self._context = None
        self._initialized = False

    # ========================================================
    # PANEL REGISTRATION
    # ========================================================

    def add_panel(
        self,
        spec: PanelSpec,
    ) -> QWidget:
        """
        Register and compose one panel.

        The plugin must already be initialized.
        """

        self._require_initialized()

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
            widget = QWidget()

        self._panel_specs[
            spec.panel_id
        ] = spec

        self._panels[
            spec.panel_id
        ] = widget

        try:
            self._create_panel_dock(
                spec,
                widget,
            )
        except Exception:
            self._panels.pop(
                spec.panel_id,
                None,
            )

            self._panel_specs.pop(
                spec.panel_id,
                None,
            )

            raise

        return widget

    def remove_panel(
        self,
        panel_id: str,
    ) -> Optional[QWidget]:
        """
        Remove a registered panel.

        Returns the panel widget if it existed.
        """

        self._require_initialized()

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
            self._remove_dock(
                dock
            )

        return widget

    def panel(
        self,
        panel_id: str,
    ) -> Optional[QWidget]:
        """Return a registered panel widget."""

        self._validate_panel_id(
            panel_id
        )

        return self._panels.get(
            panel_id
        )

    def panels(self) -> tuple[QWidget, ...]:
        """Return all registered panel widgets."""

        return tuple(
            self._panels.values()
        )

    # ========================================================
    # DOCK CREATION
    # ========================================================

    def _create_panel_dock(
        self,
        spec: PanelSpec,
        widget: QWidget,
    ) -> None:
        """
        Create and attach the dock for a panel.

        MainWindow remains the owner of the dock-area layout.
        """

        context = self._context

        if context is None:
            raise RuntimeError(
                "PanelsPlugin has no PluginContext."
            )

        main_window = context.main_window

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                "PluginContext.main_window must be QMainWindow."
            )

        dock = QDockWidget(
            spec.title,
            main_window,
        )

        dock.setObjectName(
            f"gridforge_panel_{spec.panel_id}"
        )

        dock.setFeatures(
            self._dock_features(
                spec
            )
        )

        dock.setWidget(
            widget
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
            self._tabify_panel(
                spec,
                dock,
                main_window,
            )

    def _tabify_panel(
        self,
        spec: PanelSpec,
        dock: QDockWidget,
        main_window: QMainWindow,
    ) -> None:
        """
        Tabify the panel with the most recently registered panel in
        the same dock area.
        """

        for panel_id in reversed(
            tuple(
                self._dock_widgets.keys()
            )
        ):
            if panel_id == spec.panel_id:
                continue

            previous_spec = self._panel_specs.get(
                panel_id
            )

            previous_dock = self._dock_widgets.get(
                panel_id
            )

            if (
                previous_spec is None
                or previous_dock is None
            ):
                continue

            if previous_spec.area == spec.area:
                main_window.tabifyDockWidget(
                    previous_dock,
                    dock,
                )

                return

    @staticmethod
    def _dock_features(
        spec: PanelSpec,
    ) -> QDockWidget.DockWidgetFeatures:
        """Construct the Qt dock-feature flags."""

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
        """Set panel presentation visibility."""

        self._require_initialized()

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

        if panel_id not in self._panels:
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

        widget = self._panels[
            panel_id
        ]

        widget.setVisible(
            visible
        )

    def is_panel_visible(
        self,
        panel_id: str,
    ) -> bool:
        """Return panel presentation visibility."""

        self._require_initialized()

        self._validate_panel_id(
            panel_id
        )

        if panel_id not in self._panels:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        dock = self._dock_widgets.get(
            panel_id
        )

        if dock is not None:
            return dock.isVisible()

        return self._panels[
            panel_id
        ].isVisible()

    # ========================================================
    # DOCK OPERATIONS
    # ========================================================

    def select_panel(
        self,
        panel_id: str,
    ) -> None:
        """
        Show and raise a panel.

        Dock layout remains owned by MainWindow/Qt.
        """

        self._require_initialized()

        self._validate_panel_id(
            panel_id
        )

        if panel_id not in self._panels:
            raise KeyError(
                f"Unknown panel: {panel_id!r}"
            )

        dock = self._dock_widgets.get(
            panel_id
        )

        if dock is not None:
            dock.show()
            dock.raise_()
            return

        widget = self._panels[
            panel_id
        ]

        widget.show()
        widget.raise_()

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
        """Return whether a panel has a managed dock."""

        return panel_id in self._dock_widgets

    # ========================================================
    # CLEANUP
    # ========================================================

    def _remove_all_docks(self) -> None:
        """Remove all managed docks from MainWindow."""

        docks = tuple(
            self._dock_widgets.values()
        )

        self._dock_widgets.clear()

        for dock in docks:
            self._remove_dock(
                dock
            )

    def _remove_dock(
        self,
        dock: QDockWidget,
    ) -> None:
        """
        Remove one managed dock from MainWindow.

        The MainWindow remains alive and owns the overall window
        composition.
        """

        context = self._context

        if context is not None:
            main_window = context.main_window

            if isinstance(
                main_window,
                QMainWindow,
            ):
                main_window.removeDockWidget(
                    dock
                )

        dock.close()
        dock.deleteLater()

    # ========================================================
    # VALIDATION
    # ========================================================

    def _require_initialized(self) -> None:
        """Require an active plugin lifecycle."""

        if not self._initialized:
            raise RuntimeError(
                "PanelsPlugin has not been initialized."
            )

        if self._context is None:
            raise RuntimeError(
                "PanelsPlugin is initialized without PluginContext."
            )

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


# ============================================================
# FACTORY
# ============================================================


def create_panels_plugin(
    parent: Optional[QObject] = None,
) -> PanelsPlugin:
    """
    Create an uninitialized PanelsPlugin.

    Application context is supplied during initialize().
    """

    return PanelsPlugin(
        parent=parent
    )


__all__ = [
    "PanelSpec",
    "PanelsPlugin",
    "create_panels_plugin",
]
