"""
GridForge V2
============

File:
    ui/main_window.py

Purpose
-------
Main application window and UI composition root.

Architectural role
------------------
MainWindow is the authoritative UI composition root and Qt workspace
host for GridForge V2.

MainWindow owns:
    - the Qt root window;
    - the root composition widget;
    - the authoritative Controller reference;
    - the canonical UI ToolManager;
    - the PluginContext;
    - the PluginManager;
    - the Qt dock-area/layout infrastructure.

MainWindow does NOT own:
    - electrical/network state;
    - simulation state;
    - analysis;
    - plugin implementation;
    - canvas implementation;
    - individual tools;
    - renderer implementation;
    - Workspace/Layout policy;
    - individual editor arrangement.

Composition
-----------
main.py
    |
    +-- Grid
    |
    +-- Controller
    |
    +-- MainWindow
            |
            +-- ToolManager
            |
            +-- PluginContext
            |
            +-- PluginManager
            |
            +-- Qt Workspace Host
                    |
                    +-- Workspace/Layout
                    |
                    +-- Editor Areas
                    |
                    +-- Docking / Tab / Floating / Split presentation

Workspace rule
--------------
The Workspace/Layout layer decides how editors are arranged.

Individual panels and plugins do NOT decide the global workspace layout.

MainWindow provides the Qt infrastructure required to realize that
layout.

Logical docking rule
--------------------
PanelArea is the canonical GridForge logical docking abstraction.

Qt.DockWidgetArea exists only at the Qt presentation boundary.

PanelSpec.area must not independently define the canonical logical
area.

Dependency rule
----------------
Application-owned services are explicitly composed.

MainWindow does not silently construct an application-owned Controller.

Plugins receive application-owned dependencies through PluginContext.

Canvas, renderer and panel components must not silently create
application-owned services.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QMainWindow,
    QWidget,
)

from ui.core.controller import Controller
from ui.core.qt import (
    # Keep compatibility with the project's existing Qt abstraction.
    QApplication as _QtApplication,
    QMainWindow as _QtMainWindow,
    QWidget as _QtWidget,
)
from ui.core.tool_manager import ToolManager

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager


# ============================================================
# MAIN WINDOW
# ============================================================


class MainWindow(QMainWindow):
    """
    GridForge V2 main application window.

    MainWindow is the authoritative UI composition root and Qt
    workspace host.

    Application-owned dependencies are supplied explicitly.

    Workspace/Layout policy remains above individual panels and
    determines editor arrangement.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *,
        controller: Controller,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        # ----------------------------------------------------
        # Window identity
        # ----------------------------------------------------

        self.setObjectName(
            "GridForgeMainWindow"
        )

        self.setWindowTitle(
            "GridForge"
        )

        # ----------------------------------------------------
        # Authoritative UI Controller
        #
        # The Controller is application-owned and MUST be
        # supplied explicitly by the composition root.
        #
        # MainWindow never creates a Controller.
        # ----------------------------------------------------

        if controller is None:
            raise ValueError(
                "MainWindow requires an explicit Controller."
            )

        self.controller = controller

        # ----------------------------------------------------
        # Root composition widget
        # ----------------------------------------------------

        self._root_widget = QWidget(
            self
        )

        self._root_widget.setObjectName(
            "GridForgeRootWidget"
        )

        self.setCentralWidget(
            self._root_widget
        )

        # ----------------------------------------------------
        # Canonical ToolManager
        #
        # ToolManager is application-owned and created once
        # at the composition boundary.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=self.controller
        )

        # ----------------------------------------------------
        # Plugin dependency context
        #
        # PluginContext carries references.
        # It does not create or own application services.
        # ----------------------------------------------------

        self.plugin_context = PluginContext(
            main_window=self,
            parent=self,
            application=QApplication.instance(),
            root_widget=self._root_widget,
            controller=self.controller,
            tool_manager=self.tool_manager,
        )

        # ----------------------------------------------------
        # Plugin manager
        # ----------------------------------------------------

        self.plugin_manager = PluginManager()

        # ----------------------------------------------------
        # Canonical plugin definitions
        # ----------------------------------------------------

        self.plugin_manager.define_defaults()

        # ----------------------------------------------------
        # Explicit dependency propagation
        # ----------------------------------------------------

        self.plugin_manager.set_contexts(
            {
                plugin_id: self.plugin_context
                for plugin_id
                in self.plugin_manager.plugin_ids
            }
        )

        self._plugins_initialized = False

    # ========================================================
    # ROOT / CONTEXT PROPERTIES
    # ========================================================

    @property
    def root_widget(
        self,
    ) -> QWidget:
        """
        Return the MainWindow-owned root composition widget.
        """

        return self._root_widget

    # --------------------------------------------------------

    @property
    def context(
        self,
    ) -> PluginContext:
        """
        Return the canonical plugin dependency context.
        """

        return self.plugin_context

    # --------------------------------------------------------

    @property
    def tools(
        self,
    ) -> ToolManager:
        """
        Return the canonical application ToolManager.
        """

        return self.tool_manager

    # ========================================================
    # QT DOCKING / WORKSPACE HOST
    # ========================================================

    def add_dock_widget(
        self,
        area: Qt.DockWidgetArea,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Add a dock widget to the MainWindow.

        This method exposes Qt docking infrastructure.

        It does NOT decide workspace policy.

        Workspace/Layout decides which area is appropriate.
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

    def tabify_dock_widgets(
        self,
        first: QDockWidget,
        second: QDockWidget,
    ) -> None:
        """
        Tabify two dock widgets.

        Tab grouping is a Workspace/Layout decision.
        MainWindow only provides the Qt operation.
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
                "Cannot tabify a dock widget with itself."
            )

        self.tabifyDockWidget(
            first,
            second,
        )

    # --------------------------------------------------------

    def remove_dock_widget(
        self,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Remove a dock widget from the MainWindow.

        Lifecycle ownership remains with the component that created
        the dock widget unless explicitly defined otherwise.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        self.removeDockWidget(
            dock_widget,
        )

    # ========================================================
    # PLUGIN INITIALIZATION
    # ========================================================

    def initialize_plugins(
        self,
    ) -> None:
        """
        Initialize the canonical plugin composition.

        Initialization is performed only once.
        """

        if self._plugins_initialized:
            return

        self.plugin_manager.initialize_all()

        self._plugins_initialized = True

    # ========================================================
    # PLUGIN SHUTDOWN
    # ========================================================

    def shutdown_plugins(
        self,
    ) -> None:
        """
        Shut down all initialized plugins.

        PluginManager owns plugin lifecycle orchestration.
        MainWindow only invokes the lifecycle boundary.
        """

        if not self._plugins_initialized:
            return

        self.plugin_manager.shutdown_all()

        self._plugins_initialized = False

    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(
        self,
        event: Any,
    ) -> None:
        """
        Shut down plugins before the window closes.
        """

        self.shutdown_plugins()

        event.accept()


# ============================================================
# FACTORY
# ============================================================


def create_main_window(
    *,
    controller: Controller,
    parent: Optional[QWidget] = None,
) -> MainWindow:
    """
    Create and fully initialize the GridForge main window.

    Composition order:

        1. MainWindow
        2. root widget
        3. ToolManager
        4. PluginContext
        5. PluginManager
        6. default plugin definitions
        7. plugin contexts
        8. plugin initialization

    Controller creation belongs to the application composition root
    (main.py), not this factory.
    """

    if controller is None:
        raise ValueError(
            "create_main_window requires an explicit Controller."
        )

    window = MainWindow(
        controller=controller,
        parent=parent,
    )

    window.initialize_plugins()

    return window


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MainWindow",
    "create_main_window",
]
