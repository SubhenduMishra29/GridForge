# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================

from __future__ import annotations

import sys

from core.application.bootstrap import create_application
from core.network.network import Network

from ui.canvas.canvas_composition import CanvasComposer
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.core.command_manager import CommandManager as UICommandManager
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.core.qt import QApplication
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.events.update_boundary import UIUpdateBoundary
from ui.main_window import MainWindow
from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager
from ui.sld.sld_controller import SLDController
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.project import Project
from ui.workspace.workspace import Workspace
from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_defaults import default_workspaces, get_initial_workspace
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer


def build_application() -> tuple[
    QApplication,
    MainWindow,
    PluginManager,
    WorkspaceController,
    UIUpdateBoundary,
]:
    """Build the GridForge application graph around one authoritative Network."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    network = Network()
    gridforge_application = create_application(network)
    command_manager = UICommandManager(application=gridforge_application)

    project = Project(
        project_id="gridforge-project",
        name="GridForge Project",
    )

    workspace_definition = get_initial_workspace()
    workspace = Workspace(
        workspace_id=workspace_definition.workspace_id,
        name=workspace_definition.title,
        project_id=project.project_id,
    )

    sld_document = SLDDocument(
        document_id="sld-document",
        name="GridForge SLD",
        project_id=project.project_id,
    )
    workspace.add_document(sld_document)

    sld_projection_manager = SLDProjectionManager()
    sld_read_synchronizer = SLDReadSynchronizer(sld_projection_manager)
    sld_read_synchronizer.synchronize_network(
        sld_document,
        gridforge_application.read_network(),
    )

    sld_controller = SLDController(
        projection_manager=sld_projection_manager,
    )
    sld_controller.register_document(sld_document)
    sld_controller.activate_document(sld_document.document_id)

    from ui.workspace.view_manager import ViewRecord

    sld_view = ViewRecord(
        view_id="sld-view",
        document_id=sld_document.document_id,
        view_type="sld",
    )
    workspace.add_view(sld_view)

    sld_canvas_projection = SLDCanvasProjection()
    sld_canvas_snapshot = sld_canvas_projection.project(sld_document.model)

    controller = Controller()

    tool_manager = ToolManager(
        controller=controller,
        interaction_manager=None,
        preview=None,
        tool_registry=None,
    )

    canvas_composition = CanvasComposer().compose(
        controller=controller,
        tool_manager=tool_manager,
        command_manager=command_manager,
        parent=None,
    )

    def wire_sld_node_movement(node_id: str, item: object) -> None:
        """Route graphical node movement through the SLD document boundary."""
        position_changed = getattr(item, "position_changed", None)
        connect = getattr(position_changed, "connect", None)
        if not callable(connect):
            return

        def persist_position(position: object) -> None:
            x = getattr(position, "x", None)
            y = getattr(position, "y", None)
            if not callable(x) or not callable(y):
                raise TypeError("position must provide x() and y()")
            sld_controller.set_node_position(
                node_id,
                float(x()),
                float(y()),
            )

        connect(persist_position)

    sld_canvas_render_system = SLDCanvasRenderSystem(
        scene=canvas_composition.scene,
        on_node_realized=wire_sld_node_movement,
    )

    plugin_manager = PluginManager()
    plugin_manager.define_defaults()
    plugin_manager.load_all()
    plugin_registry = plugin_manager.registry

    canvas_entry = plugin_registry.get_entry("canvas")
    if canvas_entry is None:
        raise RuntimeError("CanvasPlugin is not registered.")
    canvas_plugin = canvas_entry.plugin
    set_composition = getattr(canvas_plugin, "set_composition", None)
    if not callable(set_composition):
        raise RuntimeError("CanvasPlugin does not expose set_composition().")
    set_composition(canvas_composition)

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
        command_manager=command_manager,
        sld_document=sld_document,
        sld_canvas_projection=sld_canvas_projection,
        sld_canvas_render_system=sld_canvas_render_system,
        tool_manager=tool_manager,
        metadata={
            "sld_canvas_snapshot": sld_canvas_snapshot,
            "project_id": project.project_id,
        },
    )

    contexts = {plugin_id: context for plugin_id in plugin_manager.plugin_ids}
    plugin_manager.set_contexts(contexts)
    plugin_manager.initialize_all()

    synchronize_canvas = getattr(canvas_plugin, "synchronize_sld", None)
    if not callable(synchronize_canvas):
        raise RuntimeError("CanvasPlugin does not expose synchronize_sld().")

    sld_update_coordinator = SLDUpdateCoordinator(
        application=gridforge_application,
        document=sld_document,
        synchronizer=sld_read_synchronizer,
        canvas_refresh=synchronize_canvas,
    )
    ui_update_boundary = UIUpdateBoundary(
        event_bus=gridforge_application.event_bus,
        refresh=sld_update_coordinator.refresh,
    )
    ui_update_boundary.subscribe()

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
    workspace_controller.activate(workspace_definition.workspace_id)

    window.show()
    return app, window, plugin_manager, workspace_controller, ui_update_boundary


def main() -> int:
    """Start the GridForge application."""
    app, _window, plugin_manager, _workspace_controller, ui_update_boundary = build_application()
    try:
        return int(app.exec())
    finally:
        ui_update_boundary.dispose()
        plugin_manager.shutdown_all()


if __name__ == "__main__":
    raise SystemExit(main())
