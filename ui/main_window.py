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

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        *,
        plugin_manager: Optional[
            PluginManager
        ] = None,
        plugin_context: Optional[
            PluginContext
        ] = None,
        parent: Optional[
            QWidget
        ] = None,
    ) -> None:
        """
        Construct the GridForge main window.

        Parameters
        ----------
        controller:
            Application/UI Controller.

        plugin_manager:
            Optional externally supplied PluginManager.

            This is primarily useful for testing or controlled
            composition.

        plugin_context:
            Optional externally supplied PluginContext.

            When omitted, MainWindow creates the application
            plugin context.

        parent:
            Optional Qt parent.

        Notes
        -----
        Plugin loading and initialization are intentionally NOT
        performed inside the constructor.

        Use initialize_plugins() or create_main_window().
        """

        if controller is None:
            raise ValueError(
                "MainWindow requires a valid controller."
            )

        super().__init__(
            parent
        )

        # ----------------------------------------------------
        # AUTHORITATIVE APPLICATION CONTROLLER
        # ----------------------------------------------------
        #
        # MainWindow retains the Controller reference.
        #
        # MainWindow does not duplicate Controller state.
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # LIFECYCLE STATE
        # ----------------------------------------------------

        self._closing = False

        self._plugins_initialized = False

        # ----------------------------------------------------
        # BASIC WINDOW CONFIGURATION
        # ----------------------------------------------------

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
        # ROOT WIDGET
        # ----------------------------------------------------
        #
        # A neutral root widget is created by MainWindow.
        #
        # Plugins are responsible for configuring the actual
        # UI composition around this root.
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
        # PLUGIN CONTEXT
        # ----------------------------------------------------
        #
        # The context carries references into the application
        # composition without allowing plugins to depend on
        # MainWindow internals.
        # ----------------------------------------------------

        if plugin_context is None:

            self.plugin_context = (
                self._create_plugin_context()
            )

        else:

            self.plugin_context = (
                plugin_context
            )

        # ----------------------------------------------------
        # PLUGIN MANAGER
        # ----------------------------------------------------
        #
        # The canonical default factory defines:
        #
        #     canvas
        #     panels
        #     toolbar
        #     status
        #
        # MainWindow does not import or instantiate any of
        # those concrete plugins.
        # ----------------------------------------------------

        if plugin_manager is None:

            self.plugin_manager = (
                create_default_plugin_manager()
            )

        else:

            self.plugin_manager = (
                plugin_manager
            )

        # ----------------------------------------------------
        # COMPLETE PLUGIN CONTEXT
        # ----------------------------------------------------
        #
        # PluginManager, Registry, and Loader are infrastructure
        # dependencies. They are added to the context after the
        # manager exists.
        #
        # derive() does not modify the original context.
        # ----------------------------------------------------

        self.plugin_context = (
            self.plugin_context.derive(
                main_window=self,
                parent=self,
                application=QApplication.instance(),
                controller=self.controller,
                plugin_manager=self.plugin_manager,
                plugin_registry=(
                    self.plugin_manager.registry
                ),
                plugin_loader=(
                    self.plugin_manager.loader
                ),
            )
        )

        # ----------------------------------------------------
        # CONFIGURE PLUGIN CONTEXTS
        # ----------------------------------------------------
        #
        # PluginManager owns lifecycle.
        #
        # MainWindow merely supplies the common application
        # context to each explicitly defined plugin.
        # ----------------------------------------------------

        self._configure_plugin_contexts()

    # ========================================================
    # PLUGIN CONTEXT
    # ========================================================

    def _create_plugin_context(
        self,
    ) -> PluginContext:
        """
        Create the initial application plugin context.

        No services or domain objects are constructed here.

        The Controller is the application's UI coordination
        boundary and is supplied as a reference.
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
        Supply the common PluginContext to every defined plugin.

        PluginManager remains responsible for determining
        lifecycle order.

        MainWindow does not instantiate plugins.
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

        Lifecycle ordering is delegated to PluginManager.

        Expected order for the canonical GridForge composition:

            canvas
                ↓
            panels / toolbar
                ↓
            status

        The actual ordering is determined by the plugin dependency
        graph and not hard-coded here.
        """

        if self._plugins_initialized:
            return

        try:

            # ------------------------------------------------
            # LOAD
            # ------------------------------------------------
            #
            # PluginManager:
            #
            #   - resolves dependencies;
            #   - asks PluginLoader to import concrete plugins;
            #   - constructs plugin instances;
            #   - registers them in PluginRegistry.
            # ------------------------------------------------

            self.plugin_manager.load_all()

            # ------------------------------------------------
            # INITIALIZE
            # ------------------------------------------------
            #
            # PluginManager initializes plugins in dependency
            # order.
            # ------------------------------------------------

            self.plugin_manager.initialize_all()

        except Exception:
            # -----------------------------------------------
            # Startup is transactional from the MainWindow
            # perspective.
            #
            # If initialization fails, attempt to shut down
            # anything that successfully initialized.
            # -----------------------------------------------

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

        PluginManager owns reverse dependency ordering.
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
        Shut down the plugin composition before closing the window.

        Shutdown exceptions are allowed to propagate rather than
        being silently swallowed. The application bootstrap can
        therefore detect lifecycle failures during testing.
        """

        if self._closing:
            event.accept()
            return

        self._closing = True

        try:

            self.shutdown_plugins()

        except Exception:
            # -----------------------------------------------
            # Do not destroy the window when plugin shutdown
            # fails. This gives the caller/application a chance
            # to inspect the failure.
            # -----------------------------------------------

            self._closing = False

            event.ignore()

            raise

        event.accept()

    # ========================================================
    # APPLICATION ACCESS
    # ========================================================

    @staticmethod
    def application() -> Optional[
        QApplication
    ]:
        """
        Return the current QApplication instance.

        Returns
        -------
        QApplication | None
            Current Qt application instance, if available.
        """

        instance = (
            QApplication.instance()
        )

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
        Return the neutral root widget.

        Plugins may use this as the initial UI composition
        container where appropriate.
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
        Return whether the UI plugin composition is initialized.
        """

        return self._plugins_initialized


# ============================================================
# FACTORY
# ============================================================


def create_main_window(
    controller: Any,
    *,
    plugin_manager: Optional[
        PluginManager
    ] = None,
    plugin_context: Optional[
        PluginContext
    ] = None,
) -> MainWindow:
    """
    Construct and initialize the GridForge main window.

    This is the normal application composition entry point.

    The function deliberately separates:

        construction
            from
        plugin initialization

    so MainWindow remains straightforward to unit-test.
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
