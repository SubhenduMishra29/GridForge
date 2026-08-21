# ============================================================
# File: ui/main_window.py
# GridForge V2 — Main Application Window
# ============================================================

"""
GridForge V2
============

Main application window and UI composition root.

Architectural Role
------------------
MainWindow is the authoritative UI composition root and Qt
workspace host for GridForge V2.

MainWindow owns:

    - QMainWindow lifetime
    - root composition widget
    - authoritative Controller reference
    - canonical ToolManager
    - PluginContext
    - PluginManager
    - Qt docking/layout infrastructure

MainWindow does NOT own:

    - electrical/network state
    - simulation state
    - analysis
    - individual panel implementations
    - individual tools
    - canvas implementation
    - renderers
    - renderer registries/loaders
    - Workspace/Layout policy

Workspace Rule
--------------
The Workspace/Layout layer decides how editors are arranged.

Individual panels and plugins do not decide global workspace layout.

MainWindow provides the Qt infrastructure required to realize
the Workspace/Layout decisions.

Logical Docking Rule
--------------------
PanelArea is the canonical GridForge logical docking abstraction.

Qt.DockWidgetArea exists only at the Qt presentation boundary.

PanelSpec.area must not independently define the canonical
logical docking area.

Dependency Rule
---------------
Application-owned services are explicitly composed.

MainWindow never silently creates an application-owned Controller.

Plugins receive application-owned dependencies through
PluginContext.

Canvas, renderer and panel components must not silently create
application-owned services.

Qt Rule
-------
All Qt imports must come through:

    ui.core.qt

No direct PySide6 imports are permitted in this module.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QApplication,
    QDockWidget,
    QMainWindow,
    Qt,
    QWidget,
)

from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager


# ============================================================
# MainWindow
# ============================================================

class MainWindow(QMainWindow):
    """
    GridForge V2 main application window.

    This class is the UI composition root and Qt workspace host.

    Application-owned dependencies are supplied explicitly by the
    application composition root.
    """

    # ========================================================
    # Construction
    # ========================================================

    def __init__(
        self,
        *,
        controller: Controller,
        parent: QWidget | None = None,
    ) -> None:
        """
        Construct the main GridForge window.

        Parameters
        ----------
        controller:
            Authoritative UI/application Controller.

            This dependency MUST be supplied explicitly.

        parent:
            Optional Qt parent.

        Raises
        ------
        ValueError
            If controller is not supplied.
        """

        if controller is None:
            raise ValueError(
                "MainWindow requires an explicit Controller."
            )

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
        # Authoritative Controller
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # Root composition widget
        # ----------------------------------------------------

        self._root_widget = QWidget(self)

        self._root_widget.setObjectName(
            "GridForgeRootWidget"
        )

        self.setCentralWidget(
            self._root_widget
        )

        # ----------------------------------------------------
        # Canonical ToolManager
        #
        # Created exactly once at the application UI
        # composition boundary.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=self.controller
        )

        # ----------------------------------------------------
        # Plugin dependency context
        #
        # PluginContext carries existing application-owned
        # dependencies. It does not create them.
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
                for plugin_id in self.plugin_manager.plugin_ids
            }
        )

        # ----------------------------------------------------
        # Lifecycle state
        # ----------------------------------------------------

        self._plugins_initialized = False

    # ========================================================
    # Properties
    # ========================================================

    @property
    def root_widget(self) -> QWidget:
        """
        Return the MainWindow-owned root composition widget.
        """

        return self._root_widget

    # --------------------------------------------------------

    @property
    def context(self) -> PluginContext:
        """
        Return the canonical plugin dependency context.
        """

        return self.plugin_context

    # --------------------------------------------------------

    @property
    def tools(self) -> ToolManager:
        """
        Return the canonical ToolManager.
        """

        return self.tool_manager

    # ========================================================
    # Qt Workspace / Docking Infrastructure
    # ========================================================

    def add_dock_widget(
        self,
        area: Qt.DockWidgetArea,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Add a dock widget to the MainWindow.

        This exposes Qt docking infrastructure.

        It does NOT decide workspace policy.

        The Workspace/Layout layer determines the appropriate
        arrangement.
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
        Remove a dock widget from the MainWindow.
        """

        if dock_widget is None:
            raise ValueError(
                "dock_widget must not be None."
            )

        self.removeDockWidget(
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

        MainWindow provides only the Qt operation.
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

    # ========================================================
    # Plugin Lifecycle
    # ========================================================

    def initialize_plugins(self) -> None:
        """
        Initialize all registered plugins.

        Initialization is idempotent.
        """

        if self._plugins_initialized:
            return

        self.plugin_manager.initialize_all()

        self._plugins_initialized = True

    # --------------------------------------------------------

    def shutdown_plugins(self) -> None:
        """
        Shut down all initialized plugins.
        """

        if not self._plugins_initialized:
            return

        self.plugin_manager.shutdown_all()

        self._plugins_initialized = False

    # ========================================================
    # Qt Lifecycle
    # ========================================================

    def closeEvent(
        self,
        event: Any,
    ) -> None:
        """
        Shut down plugins before closing the application window.
        """

        self.shutdown_plugins()

        event.accept()


# ============================================================
# Factory
# ============================================================

def create_main_window(
    *,
    controller: Controller,
    parent: QWidget | None = None,
) -> MainWindow:
    """
    Create and initialize the GridForge MainWindow.

    Application composition order:

        main.py
            ↓
        Controller
            ↓
        MainWindow
            ↓
        ToolManager
            ↓
        PluginContext
            ↓
        PluginManager
            ↓
        Plugin initialization

    Controller creation remains outside MainWindow.
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
# Public API
# ============================================================

__all__ = [
    "MainWindow",
    "create_main_window",
]
