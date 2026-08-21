# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/plugins/panels_plugin.py
#
# Purpose:
#     Qt panel composition plugin.
#
# Architectural boundary
# ----------------------
#
# PanelsPlugin owns:
#     - panel presentation specifications;
#     - QWidget creation;
#     - QDockWidget creation;
#     - dock capability configuration;
#     - panel registration;
#     - panel/dock lifecycle;
#     - exposure of existing docks to the
#       application composition layer.
#
# PanelsPlugin does NOT own:
#     - WorkspaceDefinition;
#     - WorkspaceLayout;
#     - WorkspaceState;
#     - WorkspaceManager;
#     - WorkspaceController;
#     - WorkspaceRealizer;
#     - PanelArea;
#     - dock placement;
#     - dock ordering;
#     - tab groups;
#     - split arrangement;
#     - workspace visibility policy;
#     - workspace activation;
#     - Core/domain state.
#
# WorkspaceRealizer is the only component that translates
# logical WorkspaceLayout decisions into MainWindow operations.
#
# ============================================================

"""
GridForge V2 — Panels Plugin.

This module is the Qt presentation/composition boundary for
dockable application panels.

The plugin creates docks but never decides where those docks
belong. Workspace realization is deliberately external.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ui.core.qt import (
    QDockWidget,
    QMainWindow,
    QObject,
    QWidget,
)

from ui.plugins.plugin_context import PluginContext


# ============================================================
# PANEL SPECIFICATION
# ============================================================


@dataclass(frozen=True, slots=True)
class PanelSpec:
    """
    Declarative description of one Qt panel.

    PanelSpec contains presentation and capability information
    only.

    It deliberately contains no Workspace placement.
    """

    panel_id: str
    title: str

    widget: QWidget | None = None

    closable: bool = True
    movable: bool = True
    floatable: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str):
            raise TypeError(
                "panel_id must be a string."
            )

        if not self.panel_id.strip():
            raise ValueError(
                "panel_id must be a non-empty string."
            )

        if not isinstance(self.title, str):
            raise TypeError(
                "title must be a string."
            )

        if not self.title.strip():
            raise ValueError(
                "title must be a non-empty string."
            )

        if self.widget is not None and not isinstance(
            self.widget,
            QWidget,
        ):
            raise TypeError(
                "widget must be QWidget or None."
            )

        if not isinstance(self.closable, bool):
            raise TypeError(
                "closable must be bool."
            )

        if not isinstance(self.movable, bool):
            raise TypeError(
                "movable must be bool."
            )

        if not isinstance(self.floatable, bool):
            raise TypeError(
                "floatable must be bool."
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping."
            )


# ============================================================
# PANELS PLUGIN
# ============================================================


class PanelsPlugin(QObject):
    """
    Qt panel composition plugin.

    PanelsPlugin creates and owns the presentation-side panel
    widgets and their QDockWidgets.

    It never performs Workspace arrangement.
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
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._context: PluginContext | None = None

        self._panels: dict[str, QWidget] = {}

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
    def context(self) -> PluginContext | None:
        """Return the active PluginContext."""

        return self._context

    @property
    def widget(self) -> QWidget | None:
        """
        Return the plugin presentation root.

        Panels are independently dockable, therefore the plugin
        has no single central presentation widget.
        """

        return None

    @property
    def initialized(self) -> bool:
        """Return whether the plugin is initialized."""

        return self._initialized

    @property
    def dock_widgets(self) -> tuple[QDockWidget, ...]:
        """
        Return all currently managed docks.

        This exposes existing docks without making any
        placement decision.
        """

        return tuple(
            self._dock_widgets.values()
        )

    @property
    def panel_ids(self) -> tuple[str, ...]:
        """Return registered panel identifiers."""

        return tuple(
            self._panels.keys()
        )

    @property
    def panel_specs(
        self,
    ) -> Mapping[str, PanelSpec]:
        """
        Return a defensive snapshot of panel specifications.
        """

        return dict(
            self._panel_specs
        )

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: PluginContext,
    ) -> None:
        """
        Initialize the panel composition layer.

        This establishes the host context only.

        No Workspace is created, selected, activated, arranged,
        or realized here.
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
        Shut down panel presentation.

        Docks are detached and scheduled for Qt deletion.

        Workspace logical state is never modified here.
        """

        if not self._initialized:
            return

        for dock in tuple(
            self._dock_widgets.values()
        ):
            self._remove_dock(dock)

        self._dock_widgets.clear()
        self._panels.clear()
        self._panel_specs.clear()

        self._context = None
        self._initialized = False

    # ========================================================
    # PANEL REGISTRATION / COMPOSITION
    # ========================================================

    def add_panel(
        self,
        spec: PanelSpec,
    ) -> QWidget:
        """
        Create and register one panel.

        This creates:
            Panel QWidget
            QDockWidget

        It does NOT:
            - add the dock to a Workspace;
            - select a DockWidgetArea;
            - position the dock;
            - tabify the dock;
            - split the dock;
            - show/hide according to Workspace policy;
            - float according to Workspace policy;
            - activate a Workspace.
        """

        self._require_initialized()

        if not isinstance(
            spec,
            PanelSpec,
        ):
            raise TypeError(
                "spec must be a PanelSpec."
            )

        panel_id = spec.panel_id

        if panel_id in self._panels:
            raise ValueError(
                f"Panel already registered: {panel_id!r}"
            )

        widget = spec.widget

        if widget is None:
            widget = QWidget()

        widget.setObjectName(
            f"GridForgePanel_{panel_id}"
        )

        dock = QDockWidget(
            spec.title,
            self._main_window,
        )

        dock.setObjectName(
            panel_id
        )

        dock.setWidget(
            widget
        )

        dock.setFeatures(
            self._dock_features(spec)
        )

        self._panels[
            panel_id
        ] = widget

        self._dock_widgets[
            panel_id
        ] = dock

        self._panel_specs[
            panel_id
        ] = spec

        return widget

    def remove_panel(
        self,
        panel_id: str,
    ) -> QWidget | None:
        """
        Remove one panel from the presentation layer.

        Workspace state is not changed.
        """

        self._require_initialized()

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

        dock = self._dock_widgets.pop(
            panel_id,
            None,
        )

        self._panel_specs.pop(
            panel_id,
            None,
        )

        if dock is not None:
            self._remove_dock(dock)

        return widget

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_panel(
        self,
        panel_id: str,
    ) -> QWidget | None:
        """Return a registered panel widget."""

        self._require_initialized()

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        return self._panels.get(
            panel_id
        )

    def get_dock(
        self,
        panel_id: str,
    ) -> QDockWidget | None:
        """
        Return an existing dock.

        The caller receives the dock for composition or
        Workspace realization; ownership remains here.
        """

        self._require_initialized()

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        return self._dock_widgets.get(
            panel_id
        )

    def get_panel_spec(
        self,
        panel_id: str,
    ) -> PanelSpec | None:
        """Return a registered panel specification."""

        self._require_initialized()

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        return self._panel_specs.get(
            panel_id
        )

    # ========================================================
    # BULK ACCESS
    # ========================================================

    def panels(
        self,
    ) -> Mapping[str, QWidget]:
        """
        Return a defensive snapshot of panel widgets.
        """

        return dict(
            self._panels
        )

    def docks(
        self,
    ) -> Mapping[str, QDockWidget]:
        """
        Return a defensive snapshot of panel docks.
        """

        return dict(
            self._dock_widgets
        )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _require_initialized(self) -> None:
        """Require successful plugin initialization."""

        if not self._initialized:
            raise RuntimeError(
                "PanelsPlugin is not initialized."
            )

    @property
    def _main_window(self) -> QMainWindow:
        """Return the QMainWindow supplied through PluginContext."""

        self._require_initialized()

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

        return main_window

    @staticmethod
    def _dock_features(
        spec: PanelSpec,
    ) -> QDockWidget.DockWidgetFeature:
        """
        Convert presentation capabilities into Qt dock
        capabilities.
        """

        features = (
            QDockWidget.DockWidgetFeature
            .NoDockWidgetFeatures
        )

        if spec.closable:
            features |= (
                QDockWidget.DockWidgetFeature
                .DockWidgetClosable
            )

        if spec.movable:
            features |= (
                QDockWidget.DockWidgetFeature
                .DockWidgetMovable
            )

        if spec.floatable:
            features |= (
                QDockWidget.DockWidgetFeature
                .DockWidgetFloatable
            )

        return features

    def _remove_dock(
        self,
        dock: QDockWidget,
    ) -> None:
        """
        Detach and schedule deletion of one managed dock.

        This is lifecycle cleanup only.
        """

        if not isinstance(
            dock,
            QDockWidget,
        ):
            return

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

        dock.setParent(None)
        dock.deleteLater()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PanelSpec",
    "PanelsPlugin",
]
