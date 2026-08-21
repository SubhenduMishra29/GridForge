```python
# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/plugins/panels_plugin.py
#
# Purpose:
#     Panel composition plugin.
#
# Architectural boundary
# ----------------------
#
# PanelsPlugin owns:
#     - panel specifications;
#     - panel widget creation;
#     - QDockWidget creation;
#     - panel capability configuration;
#     - panel registration;
#     - panel lifecycle;
#     - exposure of docks to the application composition layer.
#
# PanelsPlugin does NOT own:
#     - WorkspaceDefinition;
#     - WorkspaceLayout;
#     - PanelArea;
#     - placement;
#     - ordering;
#     - tab groups;
#     - split arrangement;
#     - visibility policy;
#     - workspace activation;
#     - MainWindow layout policy;
#     - authoritative application state;
#     - Core/domain state.
#
# WorkspaceRealizer is responsible for translating a
# WorkspaceLayout into MainWindow host operations.
#
# ============================================================

"""
GridForge V2 — Panels Plugin.
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
    Declarative description of one panel.

    PanelSpec describes identity, presentation, capabilities,
    and metadata only.

    It deliberately contains no Workspace placement or
    visibility information.
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
                "title must not be empty."
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
    GridForge panel composition plugin.

    The plugin creates and manages panel presentation objects.

    It does not decide where or whether those panels are
    displayed.

    Workspace owns arrangement and visibility policy.
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
        """Return the active plugin context."""

        return self._context

    @property
    def widget(self) -> QWidget | None:
        """
        Return the plugin presentation root.

        Panels are independently dockable, therefore the plugin
        has no central presentation widget.
        """

        return None

    @property
    def initialized(self) -> bool:
        """Return whether the plugin has been initialized."""

        return self._initialized

    @property
    def dock_widgets(self) -> tuple[QDockWidget, ...]:
        """
        Return all managed dock widgets.

        Their placement and visibility are deliberately excluded
        from this plugin's responsibilities.
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
        """Return a defensive snapshot of registered specs."""

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
        Initialize panel composition.

        Initialization establishes the shared context only.
        It does not arrange or activate a workspace.
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

        MainWindow itself is never destroyed here.

        Docks are detached through the host abstraction and
        scheduled for Qt deletion.
        """

        if not self._initialized:
            return

        for dock in tuple(
            self._dock_widgets.values()
        ):
            self._remove_dock(
                dock
            )

        self._dock_widgets.clear()
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

        This creates the presentation widget and dock.

        It does NOT:

            - place the dock;
            - show/hide the dock;
            - select a DockWidgetArea;
            - tabify the dock;
            - float the dock;
            - activate a Workspace.

        WorkspaceRealizer owns those decisions.
        """

        self._require_initialized()

        if not isinstance(
            spec,
            PanelSpec,
        ):
            raise TypeError(
                "spec must be a PanelSpec."
            )

        if spec.panel_id in self._panels:
            raise ValueError(
                f"Panel already registered: "
                f"{spec.panel_id!r}"
            )

        widget = spec.widget

        if widget is None:
            widget = QWidget()

        dock = QDockWidget(
            spec.title,
            self._main_window,
        )

        dock.setWidget(
            widget
        )

        dock.setObjectName(
            spec.panel_id
        )

        dock.setFeatures(
            self._dock_features(
                spec
            )
        )

        self._panels[
            spec.panel_id
        ] = widget

        self._dock_widgets[
            spec.panel_id
        ] = dock

        self._panel_specs[
            spec.panel_id
        ] = spec

        return widget

    def remove_panel(
        self,
        panel_id: str,
    ) -> QWidget | None:
        """
        Remove a registered panel.

        The panel is detached from MainWindow and the dock is
        scheduled for deletion.

        Workspace state is not modified here.
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
            self._remove_dock(
                dock
            )

        return widget

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
        """Return the dock for a registered panel."""

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
        """Return the specification for a registered panel."""

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
        """Return a defensive snapshot of panel widgets."""

        return dict(
            self._panels
        )

    def docks(
        self,
    ) -> Mapping[str, QDockWidget]:
        """Return a defensive snapshot of dock widgets."""

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
        """Return the MainWindow supplied through PluginContext."""

        self._require_initialized()

        main_window = self._context.main_window

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
    ):
        """
        Convert panel capabilities into QDockWidget features.
        """

        features = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures

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

    def _remove_dock(
        self,
        dock: QDockWidget,
    ) -> None:
        """
        Detach and schedule deletion of a managed dock.

        This performs lifecycle cleanup only.

        It does not alter Workspace logical state.
        """

        if not isinstance(
            dock,
            QDockWidget,
        ):
            return

        main_window = self._context.main_window

        if isinstance(
            main_window,
            QMainWindow,
        ):
            main_window.removeDockWidget(
                dock
            )

        dock.setParent(
            None
        )

        dock.deleteLater()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PanelSpec",
    "PanelsPlugin",
]
```
