from core.application import Application
from core.application.project import ProjectContext
from ui.sld.sld_document import SLDDocument
from ui.workspace.project_workspace import ProjectWorkspaceLifecycle
from ui.workspace.project_workspace_adapter import ProjectWorkspaceApplicationAdapter
from ui.workspace.workspace_controller import WorkspaceController


class _ApplicationStub(Application):
    def new_project(self, name="Untitled Project", *, project_id=None):
        return ProjectContext(project_id=project_id or "project-1", name=name, path=None)


class _WorkspaceControllerStub(WorkspaceController):
    def __init__(self):
        self._workspace_id = None

    @property
    def active_workspace_id(self):
        return self._workspace_id

    def activate_default(self):
        self._workspace_id = "sld"

    def deactivate(self):
        self._workspace_id = None


def test_new_project_uses_supplied_document_without_replacement():
    lifecycle = ProjectWorkspaceLifecycle(_WorkspaceControllerStub())
    adapter = ProjectWorkspaceApplicationAdapter(_ApplicationStub.__new__(_ApplicationStub), lifecycle)
    document = SLDDocument(
        document_id="sld-document",
        project_id="project-1",
        name="GridForge SLD",
    )

    adapter.new_project(
        name="GridForge Project",
        project_id="project-1",
        document=document,
    )

    assert lifecycle.document is document
    assert lifecycle.document.project_id == "project-1"
    assert lifecycle.document.document_type == "sld"
