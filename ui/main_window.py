"""
GridForge V2
============

File:
    ui/main_window.py

Purpose
-------
Thin Qt application shell for GridForge V2.

MainWindow is the top-level UI composition boundary.

Architectural rules
-------------------
- MainWindow is a composition root, not a domain controller.
- Core remains authoritative for project/electrical state.
- Controller remains the UI/application coordination boundary.
- PluginContext is the dependency boundary supplied to plugins.
- PluginManager owns plugin lifecycle and dependency ordering.
- MainWindow does not construct concrete plugins directly.
- MainWindow does not construct tools.
- MainWindow does not construct renderers.
- MainWindow does not implement canvas interaction.
- MainWindow does not implement electrical logic.
- MainWindow does not manipulate the Core model directly.
- All Qt imports pass through ui.core.qt.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QApplication,
    QMainWindow,
    Qt,
    QWidget,
)

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import (
    PluginManager,
    create_default_plugin_manager,
)


# ============================================================
# MAIN WINDOW
# ============================================================


class MainWindow(QMainWindow):
    """
    GridForge top-level application window.

    MainWindow is intentionally thin.

    Its responsibilities are limited to:
        1. Establishing the Qt application shell.
        2. Retaining the application Controller.
        3. Creating the PluginContext.
        4. Creating the PluginManager.
        5. Supplying plugin contexts.
        6. Starting plugin composition.
        7. Shutting down plugin composition.

    Concrete UI composition belongs to the plugin system.
    """

    def __init__(
        self,
        controller: Any,
        *,
        plugin_manager: Optional[PluginManager] = None,
        plugin_context: Optional[PluginContext] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Construct the GridForge main window.

        Plugin loading and initialization are intentionally not
        performed inside the constructor.
        """

        if controller is None:
            raise ValueError(
                "MainWindow requires a valid controller."
            )

        super().__init__(parent)

        self.controller = controller

        self._closing = False
        self._plugins_initialized = False

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

        self.resize(
            1400,
            900,
        )

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
        # Plugin context
        # ----------------------------------------------------

        if plugin_context is None:
            self.plugin_context = (
                self._create_plugin_context()
            )
        else:
            if not isinstance(
                plugin_context,
                PluginContext,
            ):
                raise TypeError(
                    "plugin_context must be PluginContext."
                )

            self.plugin_context = (
                plugin_context
            )

        # ----------------------------------------------------
        # Plugin manager
        # ----------------------------------------------------

        if plugin_manager is None:
            self.plugin_manager = (
                create_default_plugin_manager()
            )
        else:
            if not isinstance(
                plugin_manager,
                PluginManager,
            ):
                raise TypeError(
                    "plugin_manager must be PluginManager."
                )

            self.plugin_manager = (
                plugin_manager
            )

        # ----------------------------------------------------
        # Complete application context
        #
        # IMPORTANT:
        # root_widget MUST be supplied here.
        #
        # ShellPlugin uses this widget as the composition
        # container for CanvasPlugin, ToolbarPlugin, StatusPlugin,
        # and other UI components.
        # ----------------------------------------------------

        self.plugin_context = (
            self.plugin_context.derive(
                main_window=self,
                parent=self,
                application=QApplication.instance(),
                controller=self.controller,
                root_widget=self._root_widget,
            )
        )

        self._configure_plugin_contexts()

    # ========================================================
    # PLUGIN CONTEXT
    # ========================================================

    def _create_plugin_context(
        self,
    ) -> PluginContext:
        """
        Create the initial application PluginContext.
        """

        return PluginContext(
            main_window=self,
            parent=self,
            application=QApplication.instance(),
            controller=self.controller,
        )

    # --------------------------------------------------------

    def _configure_plugin_contexts(
        self,
    ) -> None:
        """
        Supply a derived PluginContext to every plugin.

        PluginManager remains responsible for:
            - loading;
            - dependency resolution;
            - initialization ordering;
            - shutdown ordering;
            - lifecycle state.
        """

        for plugin_id in (
            self.plugin_manager.plugin_ids
        ):
            context = (
                self.plugin_context.derive()
            )

            self.plugin_manager.set_context(
                plugin_id,
                context,
            )

    # ========================================================
    # PLUGIN STARTUP
    # ========================================================

    def initialize_plugins(
        self,
    ) -> None:
        """
        Load and initialize the complete UI plugin composition.
        """

        if self._plugins_initialized:
            return

        try:
            self.plugin_manager.load_all()
            self.plugin_manager.initialize_all()

        except Exception:
            try:
                self.plugin_manager.shutdown_all()
            except Exception:
                pass

            self._plugins_initialized = False
            raise

        self._plugins_initialized = True

    # ========================================================
    # PLUGIN SHUTDOWN
    # ========================================================

    def shutdown_plugins(
        self,
    ) -> None:
        """
        Shut down all initialized UI plugins.
        """

        if not self._plugins_initialized:
            return

        self.plugin_manager.shutdown_all()

        self._plugins_initialized = False

    # ========================================================
    # WINDOW LIFECYCLE
    # ========================================================

    def closeEvent(
        self,
        event: Any,
    ) -> None:
        """
        Shut down the plugin composition before closing.
        """

        if self._closing:
            event.accept()
            return

        self._closing = True

        try:
            self.shutdown_plugins()

        except Exception:
            self._closing = False
            event.ignore()
            raise

        event.accept()

    # ========================================================
    # APPLICATION ACCESS
    # ========================================================

    @staticmethod
    def application() -> Optional[QApplication]:
        """
        Return the current QApplication instance.
        """

        instance = QApplication.instance()

        if isinstance(
            instance,
            QApplication,
        ):
            return instance

        return None

    # ========================================================
    # ROOT WIDGET ACCESS
    # ========================================================

    @property
    def root_widget(
        self,
    ) -> QWidget:
        """
        Return the MainWindow root composition widget.
        """

        return self._root_widget

    # ========================================================
    # PUBLIC STATE
    # ========================================================

    @property
    def plugins_initialized(
        self,
    ) -> bool:
        """
        Return whether the complete UI plugin composition
        has successfully initialized.
        """

        return self._plugins_initialized


# ============================================================
# FACTORY
# ============================================================


def create_main_window(
    controller: Any,
    *,
    plugin_manager: Optional[PluginManager] = None,
    plugin_context: Optional[PluginContext] = None,
) -> MainWindow:
    """
    Construct and initialize the GridForge main window.
    """

    window = MainWindow(
        controller=controller,
        plugin_manager=plugin_manager,
        plugin_context=plugin_context,
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
