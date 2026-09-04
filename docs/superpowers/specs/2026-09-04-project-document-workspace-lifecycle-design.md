# Project / Document / Workspace Lifecycle Design

## Goal
Restore the missing runtime Project creation and connect the existing Project, Workspace, Document, SLDDocument, and View contracts without changing their ownership boundaries.

## Architectural Contract
GridForge V2 treats Project as the persistent top-level engineering container/context, Document as a project document, Workspace as the active UI context, and View as a logical visual view of a document. The authoritative electrical model remains the Core/Application Network and is not moved into Project, Workspace, Document, or SLD presentation state.

The intended runtime relationship is:

```text
Project
   |
   +--> Workspace(project_id)
          |
          +--> DocumentManager
          |      |
          |      +--> SLDDocument(project_id)
          |
          +--> ViewManager
                 |
                 +--> ViewRecord(document_id="sld-document", view_type="sld")
```

The existing SLD pipeline remains separate:

```text
Application Network
       |
       v
SLDReadSynchronizer
       |
       v
SLDDocument / SLDModel
       |
       v
SLDCanvasProjection
       |
       v
SLDCanvasRenderSystem
```

## Ownership Rules

- `Project` owns only project identity, metadata, and project-level context; it does not own the Core `Network`.
- `Workspace` owns workspace-local document and view registries through its existing `DocumentManager` and `ViewManager`.
- `DocumentManager` remains the workspace-wide document lifecycle owner.
- `SLDDocument` remains the specialized document containing persistent SLD presentation state.
- `SLDController` remains the SLD interaction/editing state owner; it is not replaced by `DocumentManager`.
- `ViewManager` remains responsible only for logical document-to-view association and viewport state.
- `WorkspaceManager` remains responsible for workspace definitions/state and workspace realization; it does not become a Project manager or SLD document registry.
- `MainWindow`, panels, Canvas, `QGraphicsItem`, `BusItem`, and `LineItem` do not become Project or document owners.
- No `ProjectManager`, `DocumentAdapter`, `SLDViewManager`, or duplicate lifecycle abstraction is introduced unless later evidence proves an existing contract cannot express the required behavior.

## Runtime Composition

The composition root must establish one Project identity and propagate its `project_id` to the existing project-aware objects:

1. Create a `Project` at the application composition boundary because no existing Project creation/opening subsystem exists.
2. Create the initial `Workspace` with the same `project_id`.
3. Create the initial `SLDDocument` with the same `project_id`.
4. Register that SLDDocument through `Workspace.add_document()`, thereby using the existing `DocumentManager` instead of maintaining another workspace document registry.
5. Register a logical `ViewRecord` whose `document_id` is the SLD document ID through `Workspace.add_view()`.
6. Keep the existing `SLDController` registration because it owns SLD-specific interaction state; its active document ID must correspond to the SLD document registered in the Workspace.
7. Keep the existing Canvas/SLD projection and RenderSystem composition unchanged except where the new lifecycle objects must be passed through the already-existing composition boundary.
8. Keep Core `Network` creation independent from Project creation. Project identity and Core electrical truth are associated by application composition, not by nesting one inside the other.

## Activation Boundary

Workspace activation, document activation, and SLD interaction activation remain separate concepts:

```text
WorkspaceController
    -> WorkspaceManager / WorkspaceRealizer

Workspace.documents
    -> DocumentManager.active_document

Workspace.views
    -> ViewManager.active_view

SLDController
    -> SLDState.active_document_id
```

The initial composition must establish a consistent initial active SLD document/view without making `ViewManager` depend on `SLDController` or vice versa. Any synchronization beyond initial composition must use an existing lifecycle/event boundary rather than creating a second event architecture.

## Persistence Boundary

This change does not invent an Infrastructure/Persistence subsystem. The repository currently has no established infrastructure persistence owner. `Project`, `Document`, and `SLDDocument` retain their existing serialization contracts for future persistence integration. Runtime creation is therefore limited to composition of the existing in-memory contracts.

## Explicit Non-Goals

- Do not add Core electrical state to Project.
- Do not change `BusItem` or `LineItem`.
- Do not change SLD geometry ownership.
- Do not change Canvas ownership of viewport/interaction.
- Do not add automatic layout or overwrite saved SLD geometry.
- Do not create persistence repositories/loaders in this change.
- Do not replace `SLDController` with `DocumentManager`.
- Do not create duplicate Project/Document/View abstractions.

## Acceptance Criteria

- A runtime `Project` exists before its project-scoped Workspace and SLDDocument are composed.
- Workspace, SLDDocument, and ViewRecord carry the same project/document identity relationships through existing fields.
- The SLDDocument is registered with the Workspace's existing DocumentManager.
- The SLD view is registered with the Workspace's existing ViewManager.
- The SLDController continues to own SLD-specific active-document and interaction state.
- Core `Network` remains independently owned by the Application/Core composition.
- Existing SLD synchronization, Canvas projection, RenderSystem composition, and movement wiring remain architecturally intact.
- No locked `BusItem`/`LineItem` changes are required.
