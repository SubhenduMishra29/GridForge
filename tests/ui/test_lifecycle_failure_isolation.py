import pytest

from main import _cleanup_startup_failure, _shutdown_components
from ui.events.update_boundary import UIUpdateBoundary
from ui.lifecycle import UILifecycle, UILifecyclePhase
from ui.plugins.plugin_manager import PluginManager
from ui.sld.sld_document import SLDDocument
from ui.workspace.project import Project
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle
from ui.workspace.project_workspace_adapter import ProjectWorkspaceApplicationAdapter
from ui.workspace.workspace_controller import WorkspaceController


def _stub(instance, name, callback):
    setattr(instance, name, callback)


def test_startup_rollback_runs_all_acquired_owners():
    calls = []

    adapter = object.__new__(ProjectWorkspaceApplicationAdapter)
    _stub(adapter, "close_project", lambda: calls.append("project"))

    workspace = object.__new__(WorkspaceController)
    _stub(workspace, "close", lambda: calls.append("workspace"))

    boundary = object.__new__(UIUpdateBoundary)
    _stub(boundary, "dispose", lambda: calls.append("boundary"))

    plugins = object.__new__(PluginManager)
    _stub(plugins, "shutdown_all", lambda: calls.append("plugins"))

    _cleanup_startup_failure({
        "project_workspace_adapter": adapter,
        "workspace_controller": workspace,
        "ui_update_boundary": boundary,
        "plugin_manager": plugins,
    })

    assert calls == ["project", "workspace", "boundary", "plugins"]


def test_shutdown_continues_after_failure_and_raises_first_error():
    calls = []
    first_error = RuntimeError("lifecycle failure")
    second_error = RuntimeError("boundary failure")

    lifecycle = object.__new__(UILifecycle)
    lifecycle._phase = UILifecyclePhase.DOCUMENT_READY
    _stub(lifecycle, "close", lambda: (_ for _ in ()).throw(first_error))

    workspace = object.__new__(WorkspaceController)
    _stub(workspace, "close", lambda: calls.append("workspace"))

    boundary = object.__new__(UIUpdateBoundary)
    _stub(boundary, "dispose", lambda: (_ for _ in ()).throw(second_error))

    plugins = object.__new__(PluginManager)
    _stub(plugins, "shutdown_all", lambda: calls.append("plugins"))

    with pytest.raises(RuntimeError, match="lifecycle failure"):
        _shutdown_components(
            ui_lifecycle=lifecycle,
            workspace_controller=workspace,
            ui_update_boundary=boundary,
            plugin_manager=plugins,
        )

    assert calls == ["workspace", "plugins"]


def test_failed_workspace_activation_clears_partial_document_state():
    workspace = object.__new__(WorkspaceController)
    _stub(workspace, "deactivate", lambda: None)
    _stub(
        workspace,
        "activate_default",
        lambda: (_ for _ in ()).throw(RuntimeError("workspace activation failed")),
    )

    lifecycle = ProjectWorkspaceLifecycle(workspace)
    project = Project(project_id="project-1", name="Project")
    document = SLDDocument("sld-1", project_id="project-1")

    with pytest.raises(RuntimeError, match="workspace activation failed"):
        lifecycle.new_project(project, document=document)

    assert lifecycle.project is None
    assert lifecycle.document is None
    assert lifecycle.active_view is None
    assert lifecycle.documents.count == 0
    assert lifecycle.views.count == 0
