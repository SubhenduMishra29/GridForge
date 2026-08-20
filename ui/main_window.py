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
MainWindow is responsible for assembling the UI subsystem.

It owns:

    - the root Qt composition widget;
    - the application controller reference;
    - the canonical UI ToolManager;
    - the PluginContext;
    - the PluginManager.

It does not own:

    - electrical/network state;
    - simulation state;
    - plugin lifecycle implementation;
    - concrete canvas interaction logic;
    - individual tool implementations.

Dependency direction
--------------------
MainWindow
    |
    +-- Controller
    |
    +-- ToolManager
    |
    +-- PluginContext
    |
    +-- PluginManager
             |
             +-- CanvasPlugin
             |       |
             |       +-- GraphicsView
             |              |
             |              +-- InteractionManager
             |                     |
             |                     +-- same ToolManager
             |
             +-- PanelsPlugin
             +-- ToolbarPlugin
             +-- StatusPlugin

The ToolManager is created exactly once at the composition root
and injected into PluginContext.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QApplication,
    QMainWindow,
    QWidget,
)

from ui.core.controller import Controller
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

    It creates the canonical application-owned ToolManager and
    injects it into PluginContext before plugin initialization.
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
        super().__init__(parent)

        # ----------------------------------------------------
        # Basic window configuration
        # ----------------------------------------------------

        self.setObjectName(
            "GridForgeMainWindow"
        )

        self.setWindowTitle(
            "GridForge"
        )

        # ----------------------------------------------------
        # Application controller
        # ----------------------------------------------------

        if controller is None:
            controller = Controller(
                core=core
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
        # IMPORTANT:
        # This is the ONE application-owned ToolManager.
        #
        # It is intentionally created before plugins are
        # initialized.
        #
        # InteractionManager is optional during construction
        # and is attached when GraphicsView is created.
        # ----------------------------------------------------

        self.tool_manager = ToolManager(
            controller=self.controller
        )

        # ----------------------------------------------------
        # Plugin context
        #
        # root_widget and tool_manager are explicit dependencies.
        # ----------------------------------------------------

        self.plugin_context = PluginContext(
            main_window=self,
            parent=self,
            application=QApplication.instance(),
            controller=self.controller,
            root_widget=self._root_widget,
            tool_manager=self.tool_manager,
        )

        # ----------------------------------------------------
        # Plugin manager
        # ----------------------------------------------------

        self.plugin_manager = PluginManager(
            context=self.plugin_context
        )

        self._plugins_initialized = False

    # ========================================================
    # PLUGIN INITIALIZATION
    # ========================================================

    def initialize_plugins(
        self,
    ) -> None:
        """
        Initialize all registered UI plugins.

        Plugin initialization occurs only after the complete
        composition context has been assembled.
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
        Shut down all UI plugins.

        Plugin lifecycle remains owned by PluginManager.
        """

        if not self._plugins_initialized:
            return

        self.plugin_manager.shutdown_all()

        self._plugins_initialized = False

    # ========================================================
    # CONTEXT ACCESS
    # ========================================================

    @property
    def context(
        self,
    ) -> PluginContext:
        """
        Return the immutable plugin dependency context.
        """

        return self.plugin_context

    # ========================================================
    # TOOL MANAGER ACCESS
    # ========================================================

    @property
    def tools(
        self,
    ) -> ToolManager:
        """
        Return the canonical application ToolManager.

        This is an alias for application-level code that needs
        access to the UI tool system.
        """

        return self.tool_manager

    # ========================================================
    # ROOT WIDGET
    # ========================================================

    @property
    def root_widget(
        self,
    ) -> QWidget:
        """
        Return the canonical UI composition root.
        """

        return self._root_widget

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event: Any,
    ) -> None:
        """
        Shut down plugins before closing the window.
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
    Create and initialize the GridForge MainWindow.

    The composition sequence is:

        1. MainWindow
        2. Controller
        3. root widget
        4. ToolManager
        5. PluginContext
        6. PluginManager
        7. plugin initialization

    No duplicate ToolManager is created.
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
