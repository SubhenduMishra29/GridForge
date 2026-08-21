# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     main.py
#
# Purpose:
#     Application composition root.
#
# Ownership:
#     main.py owns application-level composition.
#
# It composes:
#     Controller
#     ToolManager
#     MainWindow
#     PluginContext
#     PluginManager
#     WorkspaceManager
#     WorkspaceRealizer
#     WorkspaceController
#
# Canvas loading remains owned by the plugin system:
#
#     PluginManager
#         -> CanvasPlugin
#         -> ShellPlugin
#         -> MainWindow.central_surface
#
# Workspace activation occurs only after plugin initialization.
# ============================================================

from __future__ import annotations

import sys

from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.core.qt import QApplication

from ui.main_window import MainWindow

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager

from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_defaults import (
    default_workspaces,
    get_initial_workspace,
)
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer


# ============================================================
# APPLICATION COMPOSITION
# ============================================================


def build_application() -> tuple[
    QApplication,
    MainWindow,
    PluginManager,
    WorkspaceController,
]:
    """
    Build the complete GridForge application graph.

    PluginManager remains the sole owner of plugin construction
    and lifecycle ordering.

    WorkspaceController remains application-level orchestration
    and is deliberately not injected into MainWindow or plugins.
    """

    # --------------------------------------------------------
    # Qt application
    # --------------------------------------------------------

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    # --------------------------------------------------------
    # Application controller
    # --------------------------------------------------------

    controller = Controller()

    # --------------------------------------------------------
    # Tool lifecycle owner
    #
    # interaction_manager and preview are currently optional
    # ToolManager dependencies and therefore remain None until
    # their concrete application services are introduced.
    # --------------------------------------------------------

    tool_manager = ToolManager(
        controller=controller,
        interaction_manager=None,
        preview=None,
        tool_registry=None,
    )

    # --------------------------------------------------------
    # Plugin manager
    #
    # PluginManager owns PluginRegistry and PluginLoader.
    # --------------------------------------------------------

    plugin_manager = PluginManager()

    plugin_manager.define_defaults()

    # Load plugins before creating the MainWindow so the actual
    # PluginRegistry can be injected into MainWindow.
    plugin_manager.load_all()

    plugin_registry = plugin_manager.registry

    # --------------------------------------------------------
    # MainWindow
    #
    # MainWindow owns the central surface.
    # It does not own Workspace orchestration.
    # --------------------------------------------------------

    window = MainWindow(
        controller=controller,
        plugin_registry=plugin_registry,
    )

    root_widget = window.central_surface

    if root_widget is None:
        raise RuntimeError(
            "MainWindow did not provide a central surface."
        )

    # --------------------------------------------------------
    # PluginContext
    #
    # This is a dependency carrier only.
    #
    # ShellPlugin receives root_widget and composes the already
    # initialized Canvas/Toolbar/Status widgets into it.
    # --------------------------------------------------------

    context = PluginContext(
        main_window=window,
        parent=window,
        application=app,
        root_widget=root_widget,
        controller=controller,
        tool_manager=tool_manager,
    )

    # PluginManager expects one context for each defined plugin.
    contexts = {
        plugin_id: context
        for plugin_id in plugin_manager.plugin_ids
    }

    plugin_manager.set_contexts(
        contexts
    )

    # --------------------------------------------------------
    # Plugin lifecycle
    #
    # initialize_all() takes no context argument. It consumes
    # the contexts installed above.
    #
    # Dependency ordering guarantees:
    #
    #     Canvas
    #       ↓
    #     Toolbar
    #       ↓
    #     Status
    #       ↓
    #     Shell
    #
    # Before Shell initialization PluginManager automatically
    # performs _prepare_shell_composition(), supplying:
    #
    #     CanvasPlugin.widget
    #     ToolbarPlugin.widget
    #     StatusPlugin.widget
    #
    # to ShellPlugin.
    # --------------------------------------------------------

    plugin_manager.initialize_all()

    # --------------------------------------------------------
    # Workspace layer
    #
    # Workspace definitions are logical data.
    # They do not create Canvas or panels.
    # --------------------------------------------------------

    workspace_manager = WorkspaceManager(
        definitions={
            definition.workspace_id: definition
            for definition in default_workspaces()
        }
    )

    # --------------------------------------------------------
    # Workspace realizer
    #
    # MainWindow is the Qt host.
    # WorkspaceRealizer receives the host reference but does
    # not become part of MainWindow's responsibilities.
    # --------------------------------------------------------

    workspace_realizer = WorkspaceRealizer(
        main_window=window,
    )

    # --------------------------------------------------------
    # Register concrete panel docks exposed by PanelsPlugin.
    #
    # PanelsPlugin owns the dock widgets.
    # WorkspaceRealizer only owns their logical realization.
    # --------------------------------------------------------

    panels_entry = plugin_registry.get_entry(
        "panels"
    )

    if panels_entry is None:
        raise RuntimeError(
            "PanelsPlugin is not registered."
        )

    panels_plugin = panels_entry.plugin

    for panel_id in (
        "project",
        "equipment",
        "properties",
    ):
        dock = panels_plugin.get_dock(
            panel_id
        )

        if dock is None:
            raise RuntimeError(
                (
                    "PanelsPlugin did not expose "
                    f"required dock {panel_id!r}."
                )
            )

        workspace_realizer.register_dock(
            panel_id=panel_id,
            dock_widget=dock,
        )

    # --------------------------------------------------------
    # Workspace controller
    #
    # This is the legitimate application-level Workspace
    # orchestration owner.
    # --------------------------------------------------------

    workspace_controller = WorkspaceController(
        manager=workspace_manager,
        realizer=workspace_realizer,
    )

    # --------------------------------------------------------
    # FIRST WORKSPACE ACTIVATION BOUNDARY
    #
    # Canvas has already been initialized by CanvasPlugin and
    # composed into MainWindow.central_surface by ShellPlugin.
    #
    # Workspace activation therefore configures presentation
    # around an already-existing Canvas rather than loading it.
    # --------------------------------------------------------

    initial_workspace = get_initial_workspace()

    workspace_controller.activate(
        initial_workspace.workspace_id
    )

    # --------------------------------------------------------
    # Present application
    # --------------------------------------------------------

    window.show()

    return (
        app,
        window,
        plugin_manager,
        workspace_controller,
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================


def main() -> int:
    """
    Start the GridForge application.
    """

    (
        app,
        _window,
        plugin_manager,
        _workspace_controller,
    ) = build_application()

    try:
        return int(
            app.exec()
        )
    finally:
        plugin_manager.shutdown_all()


# ============================================================
# SCRIPT ENTRY
# ============================================================


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
