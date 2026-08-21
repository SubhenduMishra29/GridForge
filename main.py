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
# Architectural ownership
# -----------------------
#
# main.py owns:
#     - QApplication lifecycle;
#     - construction of application-level dependencies;
#     - MainWindow construction;
#     - PluginManager composition;
#     - PluginContext injection;
#     - WorkspaceManager construction;
#     - WorkspaceRealizer construction;
#     - WorkspaceController construction;
#     - initial Workspace activation.
#
# MainWindow does NOT own Workspace orchestration.
# PanelsPlugin does NOT own Workspace orchestration.
#
# ============================================================

"""
GridForge V2 — Application Composition Root.

Startup sequence:

    QApplication
        ↓
    Controller
        ↓
    MainWindow
        ↓
    PluginManager
        ↓
    PluginContext
        ↓
    Canvas / Panels / Toolbar / Status / Shell
        ↓
    WorkspaceManager
        ↓
    WorkspaceRealizer
        ↓
    WorkspaceController
        ↓
    activate("sld")
        ↓
    MainWindow.show()
"""

from __future__ import annotations

import sys

from ui.core.controller import Controller
from ui.core.qt import QApplication

from ui.main_window import MainWindow

from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager

from ui.workspace.workspace_controller import (
    WorkspaceController,
)
from ui.workspace.workspace_defaults import (
    default_workspaces,
    get_initial_workspace,
)
from ui.workspace.workspace_manager import (
    WorkspaceManager,
)
from ui.workspace.workspace_realizer import (
    WorkspaceRealizer,
)

from ui.panels.default_panels import (
    compose_default_panel_specs,
)


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
    Construct the complete GridForge application graph.

    Construction is intentionally separated from ``main()`` so
    tests and integration checks can exercise the composition
    root without entering the Qt event loop.

    Returns
    -------
    tuple
        QApplication,
        MainWindow,
        PluginManager,
        WorkspaceController
    """

    # --------------------------------------------------------
    # Qt application
    # --------------------------------------------------------

    app = QApplication.instance()

    if app is None:
        app = QApplication(
            sys.argv
        )

    # --------------------------------------------------------
    # Application controller
    #
    # Core remains optional here. The current UI composition
    # root does not manufacture domain state merely to create
    # the window.
    # --------------------------------------------------------

    controller = Controller()

    # --------------------------------------------------------
    # Plugin registry is owned by PluginManager.
    #
    # MainWindow only receives the registry reference.
    # --------------------------------------------------------

    plugin_manager = PluginManager()

    plugin_manager.define_defaults()

    plugin_manager.load_all()

    # --------------------------------------------------------
    # Main window
    #
    # No Workspace object is supplied to MainWindow.
    # --------------------------------------------------------

    window = MainWindow(
        controller=controller,
        plugin_registry=plugin_manager.registry,
    )

    # --------------------------------------------------------
    # Plugin context
    #
    # The context carries already-created dependencies.
    # --------------------------------------------------------

    context = PluginContext(
        main_window=window,
        parent=window,
        application=app,
        root_widget=window.central_surface,
        controller=controller,
    )

    plugin_manager.set_contexts(
        {
            plugin_id: context
            for plugin_id
            in plugin_manager.plugin_ids
        }
    )

    # --------------------------------------------------------
    # Initialize the explicit plugin graph.
    #
    # PluginManager resolves dependency order.
    # PanelsPlugin is initialized here but does not create or
    # activate a Workspace.
    # --------------------------------------------------------

    plugin_manager.initialize_all()

    # --------------------------------------------------------
    # Register the canonical initial panel presentation.
    #
    # Panel definitions remain presentation definitions.
    # Workspace placement is handled below by WorkspaceRealizer.
    # --------------------------------------------------------

    panels_entry = (
        plugin_manager.registry.get_entry(
            "panels"
        )
    )

    if panels_entry is None:
        raise RuntimeError(
            "PanelsPlugin was not registered."
        )

    panels_plugin = panels_entry.plugin

    for spec in compose_default_panel_specs():
        panels_plugin.add_panel(
            spec
        )

    # --------------------------------------------------------
    # Workspace manager
    #
    # Definitions are logical data only.
    # --------------------------------------------------------

    workspace_manager = WorkspaceManager(
        definitions={
            workspace.workspace_id: workspace
            for workspace
            in default_workspaces()
        }
    )

    # --------------------------------------------------------
    # Workspace realizer
    #
    # The realizer knows the Qt host but does not define
    # Workspace policy.
    # --------------------------------------------------------

    workspace_realizer = WorkspaceRealizer(
        main_window=window
    )

    # --------------------------------------------------------
    # Inject concrete panel docks into the realizer.
    #
    # PanelsPlugin owns the docks.
    # WorkspaceRealizer only receives references and realizes
    # logical placement.
    # --------------------------------------------------------

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
                    f"PanelsPlugin did not expose "
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
    # This is the application-level orchestration boundary.
    # --------------------------------------------------------

    workspace_controller = WorkspaceController(
        manager=workspace_manager,
        realizer=workspace_realizer,
    )

    # --------------------------------------------------------
    # Initial Workspace activation.
    #
    # This is deliberately the FIRST Workspace activation
    # boundary and lives only at the composition root.
    # --------------------------------------------------------

    initial_workspace = get_initial_workspace()

    workspace_controller.activate(
        initial_workspace.workspace_id
    )

    # --------------------------------------------------------
    # Window presentation
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
        # Application-level lifecycle ownership remains here.
        #
        # WorkspaceController has no shutdown responsibility for
        # plugin lifecycle.
        plugin_manager.shutdown_all()


# ============================================================
# SCRIPT ENTRY
# ============================================================


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
