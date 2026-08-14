"""
GridForge V2
============

File:
    ui/main_window.py

Purpose
-------
Thin Qt application shell for GridForge.

MainWindow owns the top-level application window and delegates UI
composition to the plugin system.

Architectural rules
-------------------
- MainWindow is a composition root, not a domain controller.
- Core remains authoritative for project/electrical state.
- Plugins own their UI composition responsibilities.
- MainWindow must not construct concrete tools or renderers.
- MainWindow must not contain electrical calculations.
- MainWindow must not contain topology logic.
- MainWindow must not become a second application controller.
- PySide6 is the only Qt binding.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager


class MainWindow(QMainWindow):
    """
    GridForge top-level application window.

    The window is intentionally thin. Its primary responsibilities are:

    - establish the Qt top-level shell
    - retain the authoritative application controller
    - construct the plugin composition infrastructure
    - initialize UI plugins
    - shut down UI plugins cleanly

    Concrete UI components are supplied by plugins.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        controller: Any,
        *,
        plugin_manager: Optional[PluginManager] = None,
        plugin_context: Optional[PluginContext] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        if controller is None:
            raise ValueError(
                "MainWindow requires a valid controller."
            )

        super().__init__(parent)

        self.controller = controller

        self._closing = False
        self._plugins_initialized = False

        # --------------------------------------------------------
        # Basic window configuration
        # --------------------------------------------------------

        self.setObjectName(
            "GridForgeMainWindow"
        )

        self.setWindowTitle(
            "GridForge"
        )

        self.setAttribute(
            Qt.WA_DeleteOnClose,
            True,
        )

        # --------------------------------------------------------
        # Plugin context
        # --------------------------------------------------------
        #
        # The context is the dependency boundary between the
        # application shell and individual plugins.
        #
        # Do not pass the MainWindow into plugins as an implicit
        # dependency when PluginContext can provide the required
        # service explicitly.
        # --------------------------------------------------------

        self.plugin_context = (
            plugin_context
            if plugin_context is not None
            else self._create_plugin_context()
        )

        # --------------------------------------------------------
        # Plugin manager
        # --------------------------------------------------------
        #
        # PluginManager owns plugin lifecycle and composition.
        #
        # MainWindow does not manually construct:
        #
        #   CanvasPlugin
        #   PanelsPlugin
        #   ToolbarPlugin
        #   StatusPlugin
        #
        # Concrete plugin discovery/loading remains inside the
        # plugin infrastructure.
        # --------------------------------------------------------

        self.plugin_manager = (
            plugin_manager
            if plugin_manager is not None
            else self._create_plugin_manager()
        )

        # --------------------------------------------------------
        # Central widget
        # --------------------------------------------------------
        #
        # Plugins may replace/configure the central widget during
        # initialization. Until then, provide a neutral container.
        # --------------------------------------------------------

        self._root_widget = QWidget(self)

        self._root_widget.setObjectName(
            "GridForgeRootWidget"
        )

        self.setCentralWidget(
            self._root_widget
        )

        # --------------------------------------------------------
        # Window defaults
        # --------------------------------------------------------

        self.resize(
            1400,
            900,
        )

    # ============================================================
    # PLUGIN CONTEXT
    # ============================================================

    def _create_plugin_context(
        self,
    ) -> PluginContext:
        """
        Create the application-level plugin context.

        PluginContext is intentionally created through a small
        adapter method so the MainWindow does not depend on the
        internal construction details of the context.
        """

        return PluginContext(
            controller=self.controller,
            main_window=self,
        )

    # ============================================================
    # PLUGIN MANAGER
    # ============================================================

    def _create_plugin_manager(
        self,
    ) -> PluginManager:
        """
        Create the plugin manager.

        Concrete plugin discovery remains the responsibility of
        PluginManager/PluginLoader.
        """

        return PluginManager(
            context=self.plugin_context,
        )

    # ============================================================
    # STARTUP
    # ============================================================

    def initialize_plugins(
        self,
    ) -> None:
        """
        Load and initialize the UI plugin composition.

        This method is intentionally explicit rather than being
        hidden inside the constructor. It keeps Qt object creation
        and plugin lifecycle ordering deterministic.
        """

        if self._plugins_initialized:
            return

        try:
            self._load_plugins()
            self._initialize_loaded_plugins()

        except Exception as exc:
            self._handle_plugin_startup_failure(
                exc
            )
            raise

        self._plugins_initialized = True

    def _load_plugins(
        self,
    ) -> None:
        """
        Request plugin loading from PluginManager.

        Compatibility with the current PluginManager API is kept
        deliberately narrow. The manager remains the lifecycle
        authority.
        """

        loader = getattr(
            self.plugin_manager,
            "load_plugins",
            None,
        )

        if callable(loader):
            loader()
            return

        loader = getattr(
            self.plugin_manager,
            "load_all",
            None,
        )

        if callable(loader):
            loader()
            return

        # A manager may already receive preloaded plugins through
        # its constructor. In that case there is nothing for the
        # MainWindow to do here.

    def _initialize_loaded_plugins(
        self,
    ) -> None:
        """
        Initialize loaded plugins through PluginManager.
        """

        initializer = getattr(
            self.plugin_manager,
            "initialize_plugins",
            None,
        )

        if callable(initializer):
            initializer()
            return

        initializer = getattr(
            self.plugin_manager,
            "initialize_all",
            None,
        )

        if callable(initializer):
            initializer()
            return

        initializer = getattr(
            self.plugin_manager,
            "initialize",
            None,
        )

        if callable(initializer):
            initializer()

    # ============================================================
    # SHUTDOWN
    # ============================================================

    def shutdown_plugins(
        self,
    ) -> None:
        """
        Shut down all active UI plugins.

        PluginManager owns lifecycle ordering.
        """

        if not self._plugins_initialized:
            return

        shutdown = getattr(
            self.plugin_manager,
            "shutdown_plugins",
            None,
        )

        if callable(shutdown):
            shutdown()
            self._plugins_initialized = False
            return

        shutdown = getattr(
            self.plugin_manager,
            "shutdown_all",
            None,
        )

        if callable(shutdown):
            shutdown()
            self._plugins_initialized = False
            return

        shutdown = getattr(
            self.plugin_manager,
            "shutdown",
            None,
        )

        if callable(shutdown):
            shutdown()

        self._plugins_initialized = False

    # ============================================================
    # WINDOW EVENTS
    # ============================================================

    def closeEvent(
        self,
        event: Any,
    ) -> None:
        """
        Shut down the plugin composition before destroying the
        application window.
        """

        if self._closing:
            event.accept()
            return

        self._closing = True

        try:
            self.shutdown_plugins()

        except Exception as exc:
            self._closing = False

            result = QMessageBox.critical(
                self,
                "GridForge Shutdown Error",
                (
                    "One or more UI plugins failed to shut down "
                    "cleanly.\n\n"
                    f"{exc}"
                ),
                QMessageBox.Abort
                | QMessageBox.Close,
                QMessageBox.Abort,
            )

            if result == QMessageBox.Abort:
                event.ignore()
                return

        event.accept()

    # ============================================================
    # STARTUP ERROR HANDLING
    # ============================================================

    def _handle_plugin_startup_failure(
        self,
        error: BaseException,
    ) -> None:
        """
        Present a concise startup failure to the user.

        The exception is deliberately not swallowed; callers still
        receive the original failure.
        """

        QMessageBox.critical(
            self,
            "GridForge Plugin Startup Error",
            (
                "GridForge UI plugins could not be initialized.\n\n"
                f"{error}"
            ),
        )

    # ============================================================
    # APPLICATION ACCESS
    # ============================================================

    @staticmethod
    def application() -> Optional[QApplication]:
        """
        Return the current QApplication instance, if available.
        """

        instance = QApplication.instance()

        if isinstance(
            instance,
            QApplication,
        ):
            return instance

        return None

    # ============================================================
    # PUBLIC STATE
    # ============================================================

    @property
    def plugins_initialized(
        self,
    ) -> bool:
        """Return whether the plugin composition is initialized."""

        return self._plugins_initialized


def create_main_window(
    controller: Any,
    *,
    plugin_manager: Optional[PluginManager] = None,
    plugin_context: Optional[PluginContext] = None,
) -> MainWindow:
    """
    Construct and initialize the GridForge main window.

    This helper provides the normal application composition entry
    point while keeping MainWindow itself testable.
    """

    window = MainWindow(
        controller,
        plugin_manager=plugin_manager,
        plugin_context=plugin_context,
    )

    window.initialize_plugins()

    return window


__all__ = [
    "MainWindow",
    "create_main_window",
]
