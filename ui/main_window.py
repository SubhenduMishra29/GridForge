# ============================================================
# File: ui/main_window.py
# GridForge V2 — Main Window
# ============================================================

"""
GridForge V2
============

Main application window and Qt workspace host.

Architectural Role
------------------

MainWindow is the top-level Qt host for the GridForge UI.

It owns:

    - the QApplication-facing main window;
    - the central editor/SLD host;
    - the Qt docking infrastructure;
    - the application controller;
    - the UI plugin composition boundary;
    - the mechanical Qt operations required by WorkspaceRealizer.

It does NOT own:

    - electrical/model state;
    - workspace policy;
    - panel placement policy;
    - panel registration;
    - workspace definitions;
    - workspace layout state;
    - engineering semantics.

Workspace ownership
-------------------

Workspace/Layout decides:

    WHAT is arranged
    WHERE it belongs
    WHETHER it is visible
    WHETHER it is floating
    WHICH panels are grouped

MainWindow realizes those decisions through Qt.

Dependency direction
--------------------

    WorkspaceManager
          |
          v
    WorkspaceLayout
          |
          v
    WorkspaceRealizer
          |
          v
    MainWindow
          |
          v
         Qt

Panel composition remains separate:

    PanelsPlugin
          |
          v
    Panel/Dock instances
          |
          v
    WorkspaceRealizer

Important
---------

No canvas, panel, plugin, or workspace component may silently
create an application-owned MainWindow or service.

MainWindow receives its dependencies explicitly.
"""

from __future__ import annotations

from typing import Optional

from ui.core.controller import UIController
from ui.core.plugin_registry import PluginRegistry
from ui.core.qt import (
    QDockWidget,
    QMainWindow,
    Qt,
    QWidget,
)

# PluginContext is intentionally imported from the established
# plugin infrastructure rather than recreated here.
from ui.plugins.plugin_context import PluginContext


# ============================================================
# MainWindow
# ============================================================


class MainWindow(QMainWindow):
    """
    Top-level GridForge Qt application window.

    MainWindow is the Qt realization host for the UI.

    It does not decide workspace policy. Workspace/Layout provides
    the decisions; MainWindow performs the corresponding Qt
    operations.
    """

    def __init__(
        self,
        *,
        controller: Optional[UIController] = None,
        plugin_registry: Optional[PluginRegistry] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Construct the main application window.

        Parameters
        ----------
        controller:
            Existing UI controller.

        plugin_registry:
            Existing plugin registry.

        parent:
            Optional Qt parent.

        Notes
        -----
        Dependencies are explicitly supplied. MainWindow does not
        silently construct application-owned services.
        """

        super().__init__(parent)

        self._controller = controller
        self._plugin_registry = plugin_registry

        self._plugin_context: Optional[PluginContext] = None

        self._central_widget: Optional[QWidget] = None

        self._configure_window()
        self._create_central_host()

    # ========================================================
    # Window Configuration
    # ========================================================

    def _configure_window(self) -> None:
        """
        Configure only intrinsic MainWindow properties.

        Workspace arrangement is intentionally not configured here.
        """

        self.setWindowTitle(
            "GridForge V2"
        )

        self.resize(
            1600,
            1000,
        )

        self.setDockNestingEnabled(
            True
        )

    # ========================================================
    # Central Workspace Host
    # ========================================================

    def _create_central_host(self) -> None:
        """
        Create the central editor/SLD host.

        The central host is intentionally generic. SLD/editor
        composition belongs to the workspace/editor subsystem.
        """

        self._central_widget = QWidget(
            self
        )

        self._central_widget.setObjectName(
            "GridForgeCentralWorkspace"
        )

        self.setCentralWidget(
            self._central_widget
        )

    # ========================================================
    # Properties
    # ========================================================

    @property
    def controller(
        self,
    ) -> Optional[UIController]:
        """
        Return the explicitly supplied UI controller.
        """

        return self._controller

    # --------------------------------------------------------

    @property
    def plugin_registry(
        self,
    ) -> Optional[PluginRegistry]:
        """
        Return the explicitly supplied plugin registry.
        """

        return self._plugin_registry

    # --------------------------------------------------------

    @property
    def plugin_context(
        self,
    ) -> Optional[PluginContext]:
        """
        Return the current plugin context.
        """

        return self._plugin_context

    # --------------------------------------------------------

    @property
    def central_workspace(
        self,
    ) -> Optional[QWidget]:
        """
        Return the central editor/SLD host widget.
        """

        return self._central_widget

    # ========================================================
    # Plugin Context
    # ========================================================

    def set_plugin_context(
        self,
        context: PluginContext,
    ) -> None:
        """
        Attach an existing PluginContext.

        MainWindow does not create the context.
        """

        if context is None:
            raise ValueError(
                "context must not be None."
            )

        self._plugin_context = context

    # ========================================================
    # Qt Workspace / Docking Infrastructure
    # ========================================================

    def add_dock_widget(
        self,
        area: Qt.DockWidgetArea,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Add an existing dock widget to the MainWindow.

        Workspace/Layout decides the logical area.
        MainWindow performs the Qt operation.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        self.addDockWidget(
            area,
            dock_widget,
        )

    # --------------------------------------------------------

    def remove_dock_widget(
        self,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Remove an existing dock widget from the MainWindow.

        The dock widget itself is not destroyed here.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        self.removeDockWidget(
            dock_widget
        )

    # --------------------------------------------------------

    def tabify_dock_widgets(
        self,
        first: QDockWidget,
        second: QDockWidget,
    ) -> None:
        """
        Tabify two existing dock widgets.

        Workspace/Layout decides the grouping.
        MainWindow performs the Qt operation.
        """

        if first is None:
            raise ValueError(
                "first dock widget must not be None."
            )

        if second is None:
            raise ValueError(
                "second dock widget must not be None."
            )

        if first is second:
            raise ValueError(
                "first and second dock widgets must be different."
            )

        self.tabifyDockWidget(
            first,
            second,
        )

    # --------------------------------------------------------

    def set_dock_visible(
        self,
        dock_widget: QDockWidget,
        visible: bool,
    ) -> None:
        """
        Set the visibility of an existing dock widget.

        Workspace/Layout owns the visibility decision.
        MainWindow performs only the Qt operation.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        dock_widget.setVisible(
            bool(visible)
        )

    # --------------------------------------------------------

    def set_dock_floating(
        self,
        dock_widget: QDockWidget,
        floating: bool,
    ) -> None:
        """
        Set the floating state of an existing dock widget.

        Workspace/Layout owns the floating decision.
        MainWindow performs only the Qt operation.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        dock_widget.setFloating(
            bool(floating)
        )

    # ========================================================
    # Controller Integration
    # ========================================================

    def dispatch_command(
        self,
        command,
    ):
        """
        Dispatch a UI command through the existing controller.

        MainWindow does not execute application/model logic itself.
        """

        if self._controller is None:
            raise RuntimeError(
                "No UIController is attached to MainWindow."
            )

        return self._controller.dispatch(
            command
        )

    # ========================================================
    # Lifecycle
    # ========================================================

    def closeEvent(
        self,
        event,
    ) -> None:
        """
        Handle MainWindow shutdown.

        Application/service lifecycle remains outside this class
        unless explicitly coordinated by the application layer.
        """

        event.accept()


# ============================================================
# Public API
# ============================================================

__all__ = [
    "MainWindow",
]
