from ui.workspace.area import AreaDefinition
from ui.workspace.editor import EditorDefinition
from ui.workspace.region import RegionDefinition
from ui.workspace.workspace_controller import WorkspaceController
from ui.workspace.workspace_definition import WorkspaceDefinition
from ui.workspace.workspace_layout import WorkspaceLayout
from ui.workspace.workspace_manager import WorkspaceManager
from ui.workspace.workspace_realizer import WorkspaceRealizer


class _Host:
    def __init__(self) -> None:
        self.activations = []
        self.deactivated = 0
        self.fail_editor_ids = set()

    def activate(self, editor_id, *, area=None, region_id=None, context=None):
        if editor_id in self.fail_editor_ids:
            raise RuntimeError(f"failed editor: {editor_id}")
        self.activations.append((editor_id, area.area_id, region_id, context))

    def deactivate(self):
        self.deactivated += 1


def _workspace(workspace_id: str) -> WorkspaceDefinition:
    editor = EditorDefinition(
        editor_id=f"{workspace_id}-editor",
        editor_type=workspace_id,
        title=f"{workspace_id.title()} Editor",
        regions=(RegionDefinition("canvas", "canvas"),),
    )
    area = AreaDefinition(f"main-{workspace_id}", editor, metadata={"role": "main"})
    return WorkspaceDefinition(workspace_id, f"{workspace_id.title()} Workspace", (area,))


def test_workspace_switch_keeps_manager_and_realizer_identity_in_sync():
    host = _Host()
    manager = WorkspaceManager(
        {"sld": _workspace("sld"), "control": _workspace("control")},
        default_workspace_id="sld",
    )
    realizer = WorkspaceRealizer(editor_host=host)
    controller = WorkspaceController(manager=manager, realizer=realizer)

    controller.activate("sld")
    controller.activate("control")

    assert controller.active_workspace_id == "control"
    assert controller.state.workspace_id == "control"
    assert controller.realized_workspace_id == "control"


def test_apply_layout_passes_the_active_workspace_identity():
    host = _Host()
    manager = WorkspaceManager({"sld": _workspace("sld")}, default_workspace_id="sld")
    realizer = WorkspaceRealizer(editor_host=host)
    controller = WorkspaceController(manager=manager, realizer=realizer)
    controller.activate("sld")

    candidate = WorkspaceLayout.from_areas(manager.state.layout.areas)
    controller.apply_layout(candidate)

    assert host.activations[-1][3].workspace == "sld"
    assert controller.realized_workspace_id == controller.active_workspace_id == "sld"


def test_failed_switch_restores_previous_realized_workspace():
    host = _Host()
    manager = WorkspaceManager(
        {"sld": _workspace("sld"), "control": _workspace("control")},
        default_workspace_id="sld",
    )
    realizer = WorkspaceRealizer(editor_host=host)
    controller = WorkspaceController(manager=manager, realizer=realizer)
    controller.activate("sld")

    host.fail_editor_ids.add("control-editor")
    try:
        controller.activate("control")
    except RuntimeError:
        pass
    else:
        raise AssertionError("control activation should fail")

    assert controller.active_workspace_id == "sld"
    assert controller.state.workspace_id == "sld"
    assert controller.realized_workspace_id == "sld"


def test_focus_area_context_retains_workspace_and_discipline():
    host = _Host()
    manager = WorkspaceManager({"control": _workspace("control")}, default_workspace_id="control")
    realizer = WorkspaceRealizer(editor_host=host)
    controller = WorkspaceController(manager=manager, realizer=realizer)
    controller.activate("control")

    realizer.focus_area("main-control")

    context = host.activations[-1][3]
    assert context.workspace == "control"
    assert context.area.area_id == "main-control"
    assert context.editor.editor_type == "control"
    assert context.region.region_id == "canvas"
    assert context.engineering.discipline == "control"
