# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import sys

from core.application.bootstrap import create_application
from core.network.network import Network

from ui.canvas.canvas_composition import CanvasComposer
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.core.qt import QApplication
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.events.update_boundary import UIUpdateBoundary
from ui.lifecycle import UILifecycle
from ui.main_window import MainWindow
from ui.panels.panel_presentation_bridge import PanelPresentationBridge
from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager
from ui.sld.sld_controller import SLDController
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_projection_manager import SLDProjectionManager
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle
from ui.workspace.project_workspace_adapter import ProjectWorkspaceApplicationAdapter, ProjectWorkspaceChanged
from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_defaults import SLD_WORKSPACE_ID, default_workspaces
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer


def build_application() -> tuple[
    QApplication,
    MainWindow,
    PluginManager,
    WorkspaceController,
    UIUpdateBoundary,
    UILifecycle,
]:
    """Build the GridForge runtime around one Application project lifecycle."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    network = Network()
    gridforge_application = create_application(network)

    sld_projection_manager = SLDProjectionManager()
    sld_read_synchronizer = SLDReadSynchronizer(sld_projection_manager)

    sld_controller: SLDController
    project_workspace_lifecycle: ProjectWorkspaceLifecycle

    def serialize_sld(document: SLDDocument) -> dict:
        """Use the existing SLDDocument persistence contract."""
        if not isinstance(document, SLDDocument):
            raise TypeError("Persistent presentation must be an SLDDocument")
        return document.to_dict()

    def deserialize_sld(data: dict) -> SLDDocument:
        """Deserialize presentation only; adapter owns UI activation."""
        document = SLDDocument.from_dict(data)
        if not isinstance(document, SLDDocument):
            raise TypeError("Persistent presentation must deserialize to SLDDocument")
        return document

    workspace_manager = WorkspaceManager(
        definitions={
            definition.workspace_id: definition
            for definition in default_workspaces()
        },
        default_workspace_id=SLD_WORKSPACE_ID,
    )

    controller = Controller(application=gridforge_application)
    canvas_composer = CanvasComposer()
    canvas_preparation = canvas_composer.prepare(controller=controller)
    tool_manager = ToolManager(
        controller=controller,
        application=gridforge_application,
        selection_manager=canvas_preparation.selection_manager,
        snap_system=canvas_preparation.snap_system,
    )
    canvas_composition = canvas_composer.compose(
        controller=controller,
        tool_manager=tool_manager,
        preparation=canvas_preparation,
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
            sld_controller.set_node_position(node_id, float(x()), float(y()))

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
    panels_entry = plugin_registry.get_entry("panels")
    if canvas_entry is None:
        raise RuntimeError("CanvasPlugin is not registered.")
    if panels_entry is None:
        raise RuntimeError("PanelsPlugin is not registered.")
    canvas_plugin = canvas_entry.plugin
    panels_plugin = panels_entry.plugin

    set_composition = getattr(canvas_plugin, "set_composition", None)
    if not callable(set_composition):
        raise RuntimeError("CanvasPlugin does not expose set_composition().")
    set_composition(canvas_composition)
    panel_presentation_bridge = PanelPresentationBridge(panels_plugin)

    window = MainWindow(
        controller=controller,
        plugin_registry=plugin_registry,
        central_surface=canvas_composition.widget,
    )
    root_widget = window.central_surface
    if root_widget is None:
        raise RuntimeError("MainWindow did not provide a central surface.")

    workspace_realizer = WorkspaceRealizer(main_window=window)
    workspace_controller = WorkspaceController(
        manager=workspace_manager,
        realizer=workspace_realizer,
    )
    project_workspace_lifecycle = ProjectWorkspaceLifecycle(
        workspace_controller=workspace_controller,
    )
    project_workspace_adapter = ProjectWorkspaceApplicationAdapter(
        application=gridforge_application,
        lifecycle=project_workspace_lifecycle,
    )

    # The SLD document is the single presentation document for the new project.
    # It is supplied to the lifecycle at creation time, avoiding a generic
    # Document followed by replacement with SLDDocument.
    project_id = "gridforge-project"
    sld_document = SLDDocument(
        document_id="sld-document",
        name="GridForge SLD",
        project_id=project_id,
    )
    project_context = project_workspace_adapter.new_project(
        name="GridForge Project",
        project_id=project_id,
        document=sld_document,
    )

    sld_controller = SLDController(
        projection_manager=sld_projection_manager,
        application=gridforge_application,
    )
    sld_controller.register_document(sld_document)
    sld_controller.activate_document(sld_document.document_id)
    sld_read_synchronizer.synchronize_network(
        sld_document,
        gridforge_application.read_network(),
    )

    def handle_project_workspace_changed(change: ProjectWorkspaceChanged) -> None:
        document = change.state.document
        if isinstance(document, SLDDocument):
            sld_controller.replace_document(document)
            sld_controller.activate_document(document.document_id)

    project_workspace_adapter.subscribe(handle_project_workspace_changed)

    gridforge_application.configure_project_presentation(
        presentation=sld_document,
        serializer=serialize_sld,
        deserializer=deserialize_sld,
    )

    sld_canvas_projection = SLDCanvasProjection()
    sld_canvas_snapshot = sld_canvas_projection.project(sld_document.model)

    context = PluginContext(
        main_window=window,
        parent=window,
        application=app,
        gridforge_application=gridforge_application,
        root_widget=root_widget,
        controller=controller,
        sld_document=sld_document,
        sld_canvas_projection=sld_canvas_projection,
        sld_canvas_render_system=sld_canvas_render_system,
        tool_manager=tool_manager,
        metadata={
            "sld_canvas_snapshot": sld_canvas_snapshot,
            "project_id": project_context.project_id,
            "project_workspace_adapter": project_workspace_adapter,
            "panel_presentation_bridge": panel_presentation_bridge,
        },
    )

    contexts = {plugin_id: context for plugin_id in plugin_manager.plugin_ids}
    plugin_manager.set_contexts(contexts)
    plugin_manager.initialize_all()

    for panel_id in ("project", "equipment", "properties"):
        dock = panels_plugin.get_dock(panel_id)
        if dock is None:
            raise RuntimeError(f"PanelsPlugin did not expose required dock {panel_id!r}.")
        workspace_realizer.register_dock(panel_id=panel_id, dock_widget=dock)

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

    ui_lifecycle = UILifecycle(
        workspace_ready=lambda: project_workspace_adapter.state.workspace_id is not None,
        document_ready=lambda: project_workspace_adapter.state.document is not None,
        document_close=project_workspace_adapter.close_project,
        workspace_teardown=workspace_controller.close,
        cleanup=lambda: None,
    )
    ui_lifecycle.start()
    ui_lifecycle.activate_document()

    window.show()
    return (
        app,
        window,
        plugin_manager,
        workspace_controller,
        ui_update_boundary,
        ui_lifecycle,
    )


def main() -> int:
    """Start the GridForge application."""
    (
        app,
        _window,
        plugin_manager,
        _workspace_controller,
        ui_update_boundary,
        ui_lifecycle,
    ) = build_application()
    try:
        return int(app.exec())
    finally:
        ui_lifecycle.close()
        ui_update_boundary.dispose()
        plugin_manager.shutdown_all()


if __name__ == "__main__":
    raise SystemExit(main())
