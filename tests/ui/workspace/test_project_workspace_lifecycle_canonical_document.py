from core.application.project import ProjectContext
from ui.sld.sld_document import SLDDocument
from ui.workspace.project import Project
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle
from ui.workspace.project_workspace_adapter import ProjectWorkspaceApplicationAdapter
from ui.workspace.workspace_controller import WorkspaceController


def _adapter(application, lifecycle):
    return ProjectWorkspaceApplicationAdapter(application, lifecycle)


def test_new_project_uses_supplied_document_without_replacement(application, workspace_controller):
    lifecycle = ProjectWorkspaceLifecycle(workspace_controller)
    adapter = _adapter(application, lifecycle)
    document = SLDDocument(
        document_id="sld-document",
        project_id="project-1",
        name="GridForge SLD",
    )

    adapter.new_project(name="GridForge Project", project_id="project-1", document=document)

    assert lifecycle.document is document
    assert lifecycle.document.project_id == "project-1"
    assert lifecycle.document.document_type == "sld"
    assert lifecycle.document is not None
    assert not isinstance(lifecycle.document, type(document).__mro__[1]) or lifecycle.document is document
