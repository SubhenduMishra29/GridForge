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
MainWindow assembles the application-owned UI infrastructure
and supplies explicit dependency contexts to the plugin system.

MainWindow owns:
    - the Qt root window;
    - the root composition widget;
    - the authoritative Controller reference;
    - the canonical UI ToolManager;
    - the PluginContext;
    - the PluginManager.

MainWindow does not own:
    - electrical/network state;
    - simulation state;
    - plugin implementation;
    - canvas implementation;
    - individual tools;
    - renderer implementation.

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
                    +-- canvas
                    +-- panels
                    +-- toolbar
                    +-- status
                    +-- shell

The same PluginContext dependency references are supplied to the
plugin system. Plugins do not construct application-owned services.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.controller import Controller
from ui.core.qt import (
    QApplication,
    QMainWindow,
    QWidget,
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

    MainWindow is the UI composition root.

    It creates application-level UI infrastructure and injects
    those dependencies into the plugin system.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        *,
        controller: Optional[Controller] = None,
        core: Any = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            parent
        )

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
        # Application controller
        #
        # main.py normally supplies this explicitly.
        #
        # The fallback exists for direct construction of
        # MainWindow by UI/application code.
        # ----------------------------------------------------

        if controller is None:
            controller = Controller(
                core=core
            )

        if controller is None:
            raise RuntimeError(
                "MainWindow requires a valid Controller."
            )

        self.controller = controller

        # ----------------------------------------------------
        # Root composition widget
        #
        # MainWindow owns this widget.
        # PluginContext carries the reference.
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
        # This is the single application-owned ToolManager.
        #
        # It is deliberately created before plugin initialization.
        # InteractionManager is allowed to be attached later by
        # the canvas composition layer.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=self.controller
        )

        # ----------------------------------------------------
        # Application/plugin dependency context
        #
        # PluginContext carries references only.
        # It does not create or own these objects.
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
        #
        # PluginManager does NOT accept context=.
        # Contexts are assigned explicitly below.
        # ----------------------------------------------------

        self.plugin_manager = PluginManager()

        # ----------------------------------------------------
        # Canonical plugin definitions
        #
        # This establishes:
        #
        #   canvas
        #   panels
        #   toolbar
        #   status
        #   shell
        #
        # with their declared dependencies.
        # ----------------------------------------------------

        self.plugin_manager.define_defaults()

        # ----------------------------------------------------
        # Assign the same base dependency context to every
        # canonical plugin.
        #
        # Individual plugins may derive a narrower context
        # internally when required.
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
    # PROPERTIES
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
    controller: Optional[Controller] = None,
    core: Any = None,
    parent: Optional[QWidget] = None,
) -> MainWindow:
    """
    Create and fully initialize the GridForge main window.

    Composition order:

        1. MainWindow
        2. Controller
        3. root widget
        4. ToolManager
        5. PluginContext
        6. PluginManager
        7. default plugin definitions
        8. plugin contexts
        9. plugin initialization

    The caller receives an initialized MainWindow.
    """

    window = MainWindow(
        controller=controller,
        core=core,
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
