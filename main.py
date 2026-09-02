# ============================================================
# GridForge V2 — Application Composition Root
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import sys

from core.application.bootstrap import create_application
from core.network.network import Network

from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.core.qt import QApplication
from ui.main_window import MainWindow
from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_defaults import default_workspaces, get_initial_workspace
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer


def build_application() -> tuple[QApplication, MainWindow, PluginManager, WorkspaceController]:
    """Build the GridForge application graph around one authoritative Network."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # --------------------------------------------------------
    # Authoritative Core/Application boundary
    # --------------------------------------------------------
    # One Core Network is created here. Presentation never creates
    # an alternative electrical model.
    network = Network()
    gridforge_application = create_application(network)

    # --------------------------------------------------------
    # SLD read-side presentation boundary
    # --------------------------------------------------------
    # The SLD document is presentation-owned. It is populated only
    # from immutable Application read data; it never stores Core objects.
    sld_document = SLDDocument(
        document_id="sld-document",
        name="GridForge SLD",
    )
    sld_projection_manager = SLDProjectionManager()
    sld_read_synchronizer = SLDReadSynchronizer(sld_projection_manager)
    sld_read_synchronizer.synchronize_network(
        sld_document,
        gridforge_application.read_network(),
    )

    controller = Controller()
    tool_manager = ToolManager(
        controller=controller,
        interaction_manager=None,
        preview=None,
        tool_registry=None,
    )

    plugin_manager = PluginManager()
    plugin_manager.define_defaults()
    plugin_manager.load_all()
    plugin_registry = plugin_manager.registry

    window = MainWindow(
        controller=controller,
        plugin_registry=plugin_registry,
    )
    root_widget = window.central_surface
    if root_widget is None:
        raise RuntimeError("MainWindow did not provide a central surface.")

    context = PluginContext(
        main_window=window,
        parent=window,
        application=app,
        gridforge_application=gridforge_application,
        root_widget=root_widget,
        controller=controller,
        sld_document=sld_document,
        tool_manager=tool_manager,
    )

    contexts = {plugin_id: context for plugin_id in plugin_manager.plugin_ids}
    plugin_manager.set_contexts(contexts)
    plugin_manager.initialize_all()

    workspace_manager = WorkspaceManager(
        definitions={
            definition.workspace_id: definition
            for definition in default_workspaces()
        }
    )
    workspace_realizer = WorkspaceRealizer(main_window=window)

    panels_entry = plugin_registry.get_entry("panels")
    if panels_entry is None:
        raise RuntimeError("PanelsPlugin is not registered.")

    panels_plugin = panels_entry.plugin
    for panel_id in ("project", "equipment", "properties"):
        dock = panels_plugin.get_dock(panel_id)
        if dock is None:
            raise RuntimeError(f"PanelsPlugin did not expose required dock {panel_id!r}.")
        workspace_realizer.register_dock(
            panel_id=panel_id,
            dock_widget=dock,
        )

    workspace_controller = WorkspaceController(
        manager=workspace_manager,
        realizer=workspace_realizer,
    )
    workspace_controller.activate(get_initial_workspace().workspace_id)

    window.show()
    return app, window, plugin_manager, workspace_controller


def main() -> int:
    """Start the GridForge application."""
    app, _window, plugin_manager, _workspace_controller = build_application()
    try:
        return int(app.exec())
    finally:
        plugin_manager.shutdown_all()


if __name__ == "__main__":
    raise SystemExit(main())
