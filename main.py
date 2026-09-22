# ============================================================
# GridForge V2 — Application Composition Root
# ============================================================
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import sys
from collections.abc import Callable

from core.application.bootstrap import create_application
from core.application.events import ProjectLoaded
from core.application.services.sld_service import SLDService
from core.network.network import Network

from ui.canvas.canvas_composition import CanvasComposer
from ui.canvas.sld_canvas_projection import SLDCanvasProjection
from ui.canvas.sld_canvas_render_system import SLDCanvasRenderSystem
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.core.qt import QApplication, QWidget
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.events.update_boundary import UIUpdateBoundary
from ui.lifecycle import UILifecycle
from ui.main_window import MainWindow
from ui.panels.panel_presentation_bridge import PanelPresentationBridge
from ui.plugins.plugin_context import PluginContext
from ui.plugins.plugin_manager import PluginManager
from ui.projection.element_list_projection import ElementListProjection
from ui.projection.project_hierarchy_projection import ProjectHierarchyProjection
from ui.projection.study_projection import StudyProjection
from ui.projection.ui_projection_coordinator import UIProjectionCoordinator
from ui.projection.validation_projection import ValidationProjection
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

Cleanup = Callable[[], None]


def _invoke_cleanup(cleanup: Cleanup, errors: list[BaseException]) -> None:
    try: cleanup()
    except BaseException as exc: errors.append(exc)


def _cleanup_startup_failure(resources: dict[str, object]) -> None:
    errors: list[BaseException] = []; ui_lifecycle = resources.get("ui_lifecycle"); workspace_controller = resources.get("workspace_controller")
    if isinstance(ui_lifecycle, UILifecycle):
        _invoke_cleanup(ui_lifecycle.close, errors)
        if not ui_lifecycle.closed and isinstance(workspace_controller, WorkspaceController): _invoke_cleanup(workspace_controller.close, errors)
    else:
        adapter = resources.get("project_workspace_adapter")
        if isinstance(adapter, ProjectWorkspaceApplicationAdapter): _invoke_cleanup(adapter.close_project, errors)
        if isinstance(workspace_controller, WorkspaceController): _invoke_cleanup(workspace_controller.close, errors)
    ui_update_boundary = resources.get("ui_update_boundary")
    if isinstance(ui_update_boundary, UIUpdateBoundary): _invoke_cleanup(ui_update_boundary.dispose, errors)
    plugin_manager = resources.get("plugin_manager")
    if isinstance(plugin_manager, PluginManager): _invoke_cleanup(plugin_manager.shutdown_all, errors)


def _shutdown_components(*, ui_lifecycle: UILifecycle, workspace_controller: WorkspaceController, ui_update_boundary: UIUpdateBoundary, plugin_manager: PluginManager) -> None:
    errors: list[BaseException] = []; _invoke_cleanup(ui_lifecycle.close, errors)
    if not ui_lifecycle.closed: _invoke_cleanup(workspace_controller.close, errors)
    _invoke_cleanup(ui_update_boundary.dispose, errors); _invoke_cleanup(plugin_manager.shutdown_all, errors)
    if errors: raise errors[0]


def _build_application_impl(resources: dict[str, object]) -> tuple[QApplication, MainWindow, PluginManager, WorkspaceController, UIUpdateBoundary, UILifecycle]:
    app = QApplication.instance()
    if app is None: app = QApplication(sys.argv)
    network = Network(); gridforge_application = create_application(network)
    sld_projection_manager = SLDProjectionManager(); sld_read_synchronizer = SLDReadSynchronizer(sld_projection_manager, application=gridforge_application)
    sld_controller: SLDController

    def serialize_sld(document: SLDDocument) -> dict:
        if not isinstance(document, SLDDocument): raise TypeError("Persistent presentation must be an SLDDocument")
        return document.to_dict()

    def deserialize_sld(data: dict) -> SLDDocument:
        document = SLDDocument.from_dict(data)
        if not isinstance(document, SLDDocument): raise TypeError("Persistent presentation must deserialize to an SLDDocument")
        return document

    workspace_manager = WorkspaceManager(definitions={definition.workspace_id: definition for definition in default_workspaces()}, default_workspace_id=SLD_WORKSPACE_ID)
    controller = Controller(application=gridforge_application); canvas_composer = CanvasComposer(); canvas_preparation = canvas_composer.prepare(controller=controller)
    tool_manager = ToolManager(controller=controller, application=gridforge_application, selection_manager=canvas_preparation.selection_manager, snap_system=canvas_preparation.snap_system, preview_layer=canvas_preparation.preview_layer)
    canvas_composition = canvas_composer.compose(controller=controller, tool_manager=tool_manager, preparation=canvas_preparation, parent=None)

    def wire_sld_node_movement(node_id: str, item: object) -> None:
        position_changed = getattr(item, "position_changed", None); connect = getattr(position_changed, "connect", None)
        if not callable(connect): return
        def persist_position(position: object) -> None:
            x = getattr(position, "x", None); y = getattr(position, "y", None)
            if not callable(x) or not callable(y): raise TypeError("position must provide x() and y()")
            sld_controller.set_node_position(node_id, float(x()), float(y()))
        connect(persist_position)

    sld_canvas_render_system = SLDCanvasRenderSystem(scene=canvas_composition.scene, on_node_realized=wire_sld_node_movement)
    plugin_manager = PluginManager(); resources["plugin_manager"] = plugin_manager; plugin_manager.define_defaults(); plugin_manager.load_all(); plugin_registry = plugin_manager.registry
    canvas_entry = plugin_registry.get_entry("canvas"); panels_entry = plugin_registry.get_entry("panels")
    if canvas_entry is None: raise RuntimeError("CanvasPlugin is not registered.")
    if panels_entry is None: raise RuntimeError("PanelsPlugin is not registered.")
    canvas_plugin = canvas_entry.plugin; panels_plugin = panels_entry.plugin; set_composition = getattr(canvas_plugin, "set_composition", None)
    if not callable(set_composition): raise RuntimeError("CanvasPlugin does not expose set_composition().")
    set_composition(canvas_composition); panel_presentation_bridge = PanelPresentationBridge(panels_plugin)

    # ShellPlugin owns the visible central widget composition. It requires a
    # distinct root widget so that its QVBoxLayout never becomes a child
    # layout of the GraphicsView that it is intended to contain.
    root_widget = QWidget()
    root_widget.setObjectName("GridForgeShellRoot")
    window = MainWindow(controller=controller, plugin_registry=plugin_registry, central_surface=root_widget)

    workspace_realizer = WorkspaceRealizer(main_window=window); workspace_controller = WorkspaceController(manager=workspace_manager, realizer=workspace_realizer); resources["workspace_controller"] = workspace_controller
    project_workspace_lifecycle = ProjectWorkspaceLifecycle(workspace_controller=workspace_controller); project_workspace_adapter = ProjectWorkspaceApplicationAdapter(application=gridforge_application, lifecycle=project_workspace_lifecycle); resources["project_workspace_adapter"] = project_workspace_adapter

    def create_sld_document(context: object) -> SLDDocument:
        if not hasattr(context, "project_id") or not hasattr(context, "name"): raise TypeError("presentation factory requires a ProjectContext")
        return SLDDocument(document_id=f"{context.project_id}:sld", name=f"{context.name} SLD", project_id=context.project_id)

    lifecycle_service = project_workspace_adapter.application.project_lifecycle
    lifecycle_service.configure_presentation_factory(create_sld_document)
    # The lifecycle service starts with an internal bootstrap context, but the
    # composition root must not materialize a presentation for that transient
    # context and then immediately replace it with a second project activation.
    # Configure the presentation factory first, then perform exactly one explicit
    # initial project activation; that activation creates the authoritative SLD
    # document for the project that the UI actually opens.
    project_id = "gridforge-project"
    project_context = project_workspace_adapter.new_project(
        name="GridForge Project",
        project_id=project_id,
        activate_workspace=False,
    )
    sld_document = gridforge_application.presentation
    if not isinstance(sld_document, SLDDocument):
        raise RuntimeError("Application did not establish an SLDDocument for the active project.")
    gridforge_application.attach_sld_service(SLDService(sld_document))
    gridforge_application.configure_project_presentation(
        presentation=sld_document,
        serializer=serialize_sld,
        deserializer=deserialize_sld,
    )
    if not isinstance(sld_document, SLDDocument): raise RuntimeError("Application did not establish an SLDDocument for the active project.")
    sld_controller = SLDController(projection_manager=sld_projection_manager, application=gridforge_application); sld_controller.register_document(sld_document); sld_controller.reconcile_presentation()

    def handle_project_workspace_changed(change: ProjectWorkspaceChanged) -> None:
        document = change.state.document
        if isinstance(document, SLDDocument): sld_controller.replace_document(document); sld_controller.activate_document(document.document_id); synchronize_canvas()

    project_workspace_adapter.subscribe(handle_project_workspace_changed); sld_canvas_projection = SLDCanvasProjection(); sld_canvas_snapshot = sld_canvas_projection.project(sld_document.model)
    equipment_registry = EquipmentRegistry.create_default()
    context = PluginContext(main_window=window, parent=window, application=gridforge_application, root_widget=root_widget, controller=controller, equipment_registry=equipment_registry, sld_document=sld_document, sld_canvas_projection=sld_canvas_projection, sld_canvas_render_system=sld_canvas_render_system, tool_manager=tool_manager, metadata={"sld_canvas_snapshot": sld_canvas_snapshot, "project_id": project_context.project_id, "project_workspace_adapter": project_workspace_adapter, "panel_presentation_bridge": panel_presentation_bridge})
    contexts = {plugin_id: context for plugin_id in plugin_manager.plugin_ids}; plugin_manager.set_contexts(contexts); plugin_manager.initialize_all()
    properties_panel = panels_plugin.get_panel("properties"); project_panel = panels_plugin.get_panel("project"); element_list_panel = panels_plugin.get_panel("element_list"); messages_panel = panels_plugin.get_panel("messages"); study_cases_panel = panels_plugin.get_panel("study_cases")
    for panel_id, panel in (("properties", properties_panel), ("project", project_panel), ("element_list", element_list_panel), ("messages", messages_panel), ("study_cases", study_cases_panel)):
        if panel is None: raise RuntimeError(f"PanelsPlugin did not create required {panel_id!r} presentation.")
    canvas_composer.bind_selection_projection(composition=canvas_composition, properties_panel=properties_panel); selection_projection = canvas_composition.selection_projection
    if selection_projection is None: raise RuntimeError("CanvasComposer did not create the canonical SelectionProjectionCoordinator.")
    registered_docks: list[str] = []
    try:
        for panel_id in ("project", "equipment", "properties", "element_list", "messages", "study_cases"):
            dock = panels_plugin.get_dock(panel_id)
            if dock is None:
                raise RuntimeError(f"PanelsPlugin did not expose required dock {panel_id!r}.")
            workspace_realizer.register_dock(panel_id=panel_id, dock_widget=dock)
            registered_docks.append(panel_id)
    except BaseException:
        for panel_id in reversed(registered_docks):
            workspace_realizer.unregister_dock(panel_id)
        raise
    workspace_controller.activate_default()
    synchronize_canvas = getattr(canvas_plugin, "synchronize_sld", None)
    if not callable(synchronize_canvas): raise RuntimeError("CanvasPlugin does not expose synchronize_sld().")
    sld_update_coordinator = SLDUpdateCoordinator(application=gridforge_application, synchronizer=sld_read_synchronizer, canvas_refresh=synchronize_canvas)
    element_list_projection = ElementListProjection(application=gridforge_application, panel=element_list_panel); project_hierarchy_projection = ProjectHierarchyProjection(adapter=project_workspace_adapter, panel=project_panel); validation_projection = ValidationProjection(application=gridforge_application, panel=messages_panel); study_projection = StudyProjection(application=gridforge_application, panel=study_cases_panel)
    projection_coordinator = UIProjectionCoordinator(projections=(sld_update_coordinator, selection_projection, element_list_projection, project_hierarchy_projection, validation_projection, study_projection)); resources["ui_projection_coordinator"] = projection_coordinator
    ui_update_boundary = UIUpdateBoundary(event_bus=gridforge_application.event_bus, projection_coordinator=projection_coordinator); resources["ui_update_boundary"] = ui_update_boundary; ui_update_boundary.subscribe()
    sld_update_coordinator.reconcile_current_state()
    element_list_projection.refresh(ProjectLoaded(metadata={"project_id": project_context.project_id, "operation": "initial"})); validation_projection.refresh_from_application(); selection_projection.refresh()
    ui_lifecycle = UILifecycle(workspace_ready=lambda: project_workspace_adapter.state.workspace_id is not None, document_ready=lambda: project_workspace_adapter.state.document is not None, document_close=project_workspace_adapter.close_project, workspace_teardown=workspace_controller.close, cleanup=lambda: None); resources["ui_lifecycle"] = ui_lifecycle; ui_lifecycle.start(); ui_lifecycle.activate_document(); window.show()
    return app, window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle


def build_application() -> tuple[QApplication, MainWindow, PluginManager, WorkspaceController, UIUpdateBoundary, UILifecycle]:
    resources: dict[str, object] = {}
    try: return _build_application_impl(resources)
    except BaseException: _cleanup_startup_failure(resources); raise


def main() -> int:
    app, _window, plugin_manager, workspace_controller, ui_update_boundary, ui_lifecycle = build_application()
    try: return int(app.exec())
    finally: _shutdown_components(ui_lifecycle=ui_lifecycle, workspace_controller=workspace_controller, ui_update_boundary=ui_update_boundary, plugin_manager=plugin_manager)


if __name__ == "__main__": raise SystemExit(main())
