# Project / Document / Workspace Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the missing runtime Project creation and compose the existing Project, Workspace, SLDDocument, DocumentManager, and ViewManager contracts without moving electrical truth out of the Core/Application Network.

**Architecture:** The composition root creates one Project identity and propagates only its `project_id` into the existing project-aware Workspace and SLDDocument contracts. Workspace owns its existing DocumentManager and ViewManager; SLDController continues to own SLD interaction state; Core Network remains independently owned by the Application/Core composition.

**Tech Stack:** Python, existing GridForge V2 workspace/SLD classes, PySide6 application composition.

**Spec:** `docs/superpowers/specs/2026-09-04-project-document-workspace-lifecycle-design.md`

## Global Constraints

- Project is the persistent project identity/context and does not own the Core `Network`.
- Workspace owns workspace-local document and view registries through its existing `DocumentManager` and `ViewManager`.
- `SLDDocument` remains the specialized Document containing persistent SLD presentation state.
- `SLDController` remains the SLD interaction/editing state owner.
- `WorkspaceManager` remains responsible for workspace definitions/state and realization.
- Do not introduce `ProjectManager`, `DocumentAdapter`, `SLDViewManager`, or duplicate lifecycle abstractions.
- Do not change `BusItem` or `LineItem`.
- Do not change SLD geometry ownership or introduce automatic layout.
- Do not create an Infrastructure/Persistence subsystem in this change.
- Keep Core `Network` creation independent from Project creation.
- Tests are deferred by the current project workflow; use source-level/static validation and existing contracts rather than claiming test execution.

---

### Task 1: Compose the Project identity at the application composition boundary

**Files:**
- Modify: `main.py`
- Read: `ui/workspace/project.py`
- Read: `core/application/bootstrap.py`

**Interfaces:**
- Consume the existing `Project(project_id, name, metadata)` descriptor.
- Preserve `create_application(network)` as the Application/Core composition boundary.
- Produce one stable runtime `Project` identity before composing project-scoped UI objects.

- [ ] **Step 1: Add the existing Project import to `main.py`**

Use the already-defined `ui.workspace.project.Project`; do not add a new project type.

```python
from ui.workspace.project import Project
```

- [ ] **Step 2: Create the runtime Project before the SLDDocument**

Immediately after Application/Core composition, create the project identity without embedding the Network:

```python
project = Project(
    project_id="gridforge-project",
    name="GridForge Project",
)
```

The Project must not receive `network` or any Core object.

- [ ] **Step 3: Pass `project.project_id` into the existing SLDDocument**

Change only the composition arguments:

```python
sld_document = SLDDocument(
    document_id="sld-document",
    name="GridForge SLD",
    project_id=project.project_id,
)
```

Do not modify `Document` or `SLDDocument` definitions.

- [ ] **Step 4: Inspect the resulting composition ordering**

Confirm the source order is:

```text
Network
  ↓
Application
  ↓
Project
  ↓
SLDDocument(project_id)
```

and that Project does not contain or construct Network.

- [ ] **Step 5: Commit the Project composition change**

```bash
git add main.py
git commit -m "feat: compose runtime GridForge project"
```

---

### Task 2: Compose the logical Workspace with the same Project identity

**Files:**
- Modify: `main.py`
- Read: `ui/workspace/workspace.py`
- Read: `ui/workspace/workspace_defaults.py`

**Interfaces:**
- Consume `Workspace(workspace_id, name, project_id=...)`.
- Consume existing `get_initial_workspace()` only for logical workspace definition/activation.
- Produce one runtime `Workspace` carrying the same `project_id` as Project.

- [ ] **Step 1: Import the existing logical Workspace**

```python
from ui.workspace.workspace import Workspace
```

- [ ] **Step 2: Create the runtime Workspace using the Project identity**

Compose it near the other logical workspace objects, before registering its documents/views:

```python
workspace_definition = get_initial_workspace()
workspace = Workspace(
    workspace_id=workspace_definition.workspace_id,
    name=workspace_definition.title,
    project_id=project.project_id,
)
```

Do not change `WorkspaceManager`; it remains the workspace definition/state/realization owner.

- [ ] **Step 3: Verify Workspace does not receive Core/Application objects**

The Workspace constructor must receive only its existing logical identity/name/project ID contract. It must not receive Network, Application, Canvas, Qt scene, or SLDController.

- [ ] **Step 4: Commit the Workspace composition change**

```bash
git add main.py
git commit -m "feat: compose project-scoped workspace"
```

---

### Task 3: Register the SLDDocument through Workspace's existing DocumentManager

**Files:**
- Modify: `main.py`
- Read: `ui/workspace/document_manager.py`
- Read: `ui/workspace/workspace.py`

**Interfaces:**
- Consume `Workspace.add_document(document)`.
- Produce Workspace-owned registration of the existing `SLDDocument`.
- Preserve `SLDController.register_document(sld_document)` for SLD-specific state.

- [ ] **Step 1: Register the SLDDocument with Workspace**

After Workspace creation and SLDDocument creation, call:

```python
workspace.add_document(sld_document)
```

- [ ] **Step 2: Keep SLDController registration separate**

Retain:

```python
sld_controller.register_document(sld_document)
```

This is not duplicate ownership: Workspace's DocumentManager tracks workspace documents, while SLDController tracks SLD interaction state.

- [ ] **Step 3: Activate the SLD document in SLDController explicitly**

After registration, establish the initial SLD interaction document using the existing API:

```python
sld_controller.activate_document(sld_document.document_id)
```

Do not make DocumentManager depend on SLDController.

- [ ] **Step 4: Verify the two registries have the same document identity**

The intended state is:

```text
workspace.documents.active_document.document_id
    ==
sld_controller.active_document.document_id
    ==
"sld-document"
```

This is initial composition synchronization, not a new ongoing event architecture.

- [ ] **Step 5: Commit the document registration change**

```bash
git add main.py
git commit -m "feat: register SLD document in workspace"
```

---

### Task 4: Register the SLD View through Workspace's existing ViewManager

**Files:**
- Modify: `main.py`
- Read: `ui/workspace/view_manager.py`
- Read: `ui/workspace/workspace.py`

**Interfaces:**
- Consume `ViewRecord(view_id, document_id, view_type, viewport)`.
- Consume `Workspace.add_view(view)`.
- Produce a logical SLD view associated with the existing SLDDocument.

- [ ] **Step 1: Import the existing ViewRecord type**

```python
from ui.workspace.view_manager import ViewRecord
```

- [ ] **Step 2: Create the logical SLD ViewRecord**

```python
sld_view = ViewRecord(
    view_id="sld-view",
    document_id=sld_document.document_id,
    view_type="sld",
)
```

Do not construct a QGraphicsView here.

- [ ] **Step 3: Register the view through Workspace**

```python
workspace.add_view(sld_view)
```

This uses the existing ViewManager owned by Workspace.

- [ ] **Step 4: Verify initial active view/document consistency**

The initial state must be:

```text
workspace.project_id == project.project_id
workspace.active_document.document_id == sld_document.document_id
workspace.active_view.document_id == sld_document.document_id
workspace.active_view.view_type == "sld"
```

- [ ] **Step 5: Commit the view composition change**

```bash
git add main.py
git commit -m "feat: compose workspace SLD view"
```

---

### Task 5: Keep workspace realization separate from logical document/view composition

**Files:**
- Modify: `main.py`
- Read: `ui/workspace/workspace_controller.py`
- Read: `ui/workspace/workspace_manager.py`
- Read: `ui/workspace/workspace_realizer.py`

**Interfaces:**
- Existing `WorkspaceController` continues to consume `WorkspaceManager` and `WorkspaceRealizer`.
- Runtime `Workspace` remains a logical document/view container.

- [ ] **Step 1: Preserve the existing WorkspaceManager construction**

Do not move Workspace ownership into WorkspaceManager. Keep the current definition/state composition:

```python
workspace_manager = WorkspaceManager(
    definitions={
        definition.workspace_id: definition
        for definition in default_workspaces()
    }
)
```

- [ ] **Step 2: Preserve WorkspaceController activation**

Keep:

```python
workspace_controller = WorkspaceController(
    manager=workspace_manager,
    realizer=workspace_realizer,
)
workspace_controller.activate(get_initial_workspace().workspace_id)
```

WorkspaceController remains a workspace realization coordinator, not a document/SLD activation manager.

- [ ] **Step 3: Do not introduce a second activation event path**

Initial document/view/SLD consistency is established directly during composition. Do not add signals, buses, adapters, or callbacks solely for this initial state.

- [ ] **Step 4: Commit only if this task required source changes**

If no source change is required, do not create a no-op commit.

---

### Task 6: Static architectural verification

**Files:**
- Inspect: `main.py`
- Inspect: `ui/workspace/project.py`
- Inspect: `ui/workspace/workspace.py`
- Inspect: `ui/workspace/document_manager.py`
- Inspect: `ui/workspace/view_manager.py`
- Inspect: `ui/sld/sld_document.py`
- Inspect: `ui/sld/sld_controller.py`

**Interfaces:**
- Verify the final composition against the design specification and existing contracts.

- [ ] **Step 1: Verify the runtime identity chain**

Confirm:

```text
Project(project_id="gridforge-project")
        ↓
Workspace(project_id="gridforge-project")
        ↓
SLDDocument(project_id="gridforge-project")
        ↓
ViewRecord(document_id="sld-document", view_type="sld")
```

- [ ] **Step 2: Verify the electrical truth boundary**

Confirm Network is still created independently:

```python
network = Network()
gridforge_application = create_application(network)
```

No Project/Workspace/Document class may be passed the Network.

- [ ] **Step 3: Verify the SLD projection pipeline is unchanged**

Confirm the existing path remains:

```text
Application read model
 → SLDReadSynchronizer
 → SLDDocument/SLDModel
 → SLDCanvasProjection
 → SLDCanvasRenderSystem
```

- [ ] **Step 4: Verify movement wiring is unchanged**

Confirm `BusItem.position_changed` still reaches `SLDController.set_node_position()` through the existing RenderSystem realization hook and composition-root callback.

- [ ] **Step 5: Verify locked graphics items are untouched**

Confirm no changes were made to `ui/items/bus_item.py` or `ui/items/line_item.py`.

- [ ] **Step 6: Record test limitation honestly**

Do not report pytest/application execution as successful when the current environment cannot execute the repository. Report static/source validation only unless executable verification becomes available.

---

## Final Acceptance

The implementation is acceptable only when all of the following are true:

1. A runtime Project exists before project-scoped Workspace and SLDDocument composition.
2. Project remains a persistent identity/context object and does not contain Core electrical truth.
3. Workspace carries the Project ID and owns its existing DocumentManager/ViewManager.
4. SLDDocument carries the same Project ID and is registered through Workspace.add_document().
5. The SLD ViewRecord references the SLDDocument and is registered through Workspace.add_view().
6. SLDController remains the SLD-specific interaction/document-state owner.
7. WorkspaceManager/WorkspaceController remain workspace realization infrastructure.
8. Core Network remains independently owned by the Application/Core composition.
9. Existing SLD synchronization, projection, rendering, and movement wiring remain intact.
10. No locked BusItem/LineItem changes are introduced.
11. No duplicate lifecycle/persistence/project manager abstraction is introduced.
