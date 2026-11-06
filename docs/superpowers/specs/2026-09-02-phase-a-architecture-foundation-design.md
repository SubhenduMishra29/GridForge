# GridForge V2 — Phase A Architecture Foundation Completion

**Author:** Subhendu Mishra  
**Date:** 2026-09-02  
**Status:** Approved in chat; written-spec review pending

## 1. Purpose

Complete the remaining GridForge V2 architecture foundation before expanding the visual/application UI or connecting real electrical application models.

The target is to move the architecture foundation from approximately 75–80% readiness to a stable implementation boundary suitable for the next UI phase.

The current SLD/network rendering remains **dummy and non-electrically-authoritative**. Real electrical truth will later come from the Core/Application layers.

## 2. Architectural invariants

1. Core Domain owns electrical truth and engineering meaning.
2. Application controls meaningful mutation through commands, handlers, services, and use cases.
3. Presentation expresses intent and renders results.
4. Fundamental mutation flow is `Intent → Command → Application → Core`.
5. Result/update flow is `Core → Domain Event / Result → Projection → UI`.
6. Canvas owns viewport and interaction mechanics, not electrical truth.
7. SLD is a first-class electrical visual projection and engineering editing surface.
8. QGraphicsItem-derived objects are projections only.
9. Plugins cannot bypass Application/Core boundaries.
10. Persistence does not become part of domain ownership.
11. Existing `BusItem` and `LineItem` are preserved unless a concrete contract violation requires a minimal boundary adjustment.
12. Dummy rendering must remain replaceable by authoritative application/core data without redesigning the UI architecture.

## 3. Scope

### P0 — Foundation boundaries

- Formal Projection layer
- WorkspaceManager
- Explicit Project / Document / Workspace distinction
- Formal SLD boundary
- SLD Layout boundary separated from Canvas
- UI event/update boundary

### P1 — Interaction and lifecycle boundaries

- InteractionSession and interaction-state ownership
- Deliberate registry architecture
- UI lifecycle ownership
- Connection responsibility boundary
- Renderer / Tool / Controller responsibility boundaries

### Out of scope for Phase A

- Real electrical solver integration
- Real project persistence implementation beyond interfaces required by boundaries
- Full visual redesign
- Advanced simulation features
- Replacing existing BusItem/LineItem implementations merely for style

## 4. Projection architecture

Introduce an explicit presentation projection boundary between application/core results and UI rendering.

Conceptual flow:

```text
Core / Application Result
          ↓
      Projection
          ↓
   SLD / Panels / Tables
          ↓
        Canvas
```

A projection must contain presentation-oriented state such as stable identity, display type, labels, geometry, status, connectivity references, and visual flags. It must not become a second electrical model.

Projection updates should be deterministic and replaceable. UI widgets/items consume projections rather than reaching into Core objects for authoritative state.

## 5. Workspace architecture

Introduce `WorkspaceManager` as the owner of application workspace lifecycle.

Definitions:

- **Project:** persistent engineering container and project-level identity/configuration.
- **Document:** an open/editable representation belonging to a project, such as an SLD document or study document.
- **Workspace:** the active UI/application context containing open documents, active views, panels, selection/session state, and navigation state.

The three concepts must not be collapsed into one object.

`WorkspaceManager` owns creation, activation, closing, and switching of workspaces/documents at the application/UI boundary.

## 6. SLD and Canvas boundary

SLD owns the meaning of the electrical visual projection and the editing intent surface.

Canvas owns:

- viewport
- pan/zoom
- scene/view interaction mechanics
- coordinate transforms
- generic selection mechanics where appropriate

SLD owns:

- electrical projection presentation
- layout coordination
- engineering editing intent
- SLD-specific selection/context semantics
- mapping projections to visual items

Canvas must not mutate Core electrical state.

## 7. UI event/update boundary

UI updates must be driven through an explicit application/projection update path.

Preferred flow:

```text
Command
  ↓
Application Handler
  ↓
Core mutation
  ↓
Validation
  ↓
Domain Event / Result
  ↓
Projection update
  ↓
UI refresh
```

Direct widget-to-core mutation and ad-hoc cross-panel synchronization are prohibited.

## 8. InteractionSession

InteractionSession owns transient user interaction state, including where applicable:

- current tool/mode
- active selection
- connection/wiring session
- drag/edit session
- temporary preview state
- cancellation/commit state

Transient interaction state must not leak into persistent Core domain objects.

## 9. Registry architecture

Registries are explicit infrastructure/application mechanisms rather than hidden global state.

Separate responsibilities should exist for:

- equipment/component registration
- renderer registration
- tool registration
- controller registration
- plugin registration where applicable

Each registry has one owner, defined lifecycle, deterministic lookup semantics, and explicit registration/unregistration behavior.

## 10. UI lifecycle

The lifecycle must have explicit ownership for:

1. application bootstrap
2. shell creation
3. workspace creation
4. document/view activation
5. document closing
6. workspace teardown
7. renderer/tool/controller cleanup

Objects should not depend on accidental Python/Qt destruction order for correctness.

## 11. Connection responsibility

The UI may request a connection but must not directly establish authoritative electrical topology.

```text
User gesture
    ↓
Connection tool/session
    ↓
Connection intent / command
    ↓
Application handler
    ↓
Core topology mutation + validation
    ↓
Result/event
    ↓
Projection refresh
```

For the current dummy rendering phase, the same interaction boundary may produce a visual placeholder result without pretending it is authoritative electrical topology.

## 12. Renderer / Tool / Controller boundaries

- **Renderer:** translates projection state into visual representation.
- **Tool:** captures user interaction and expresses intent.
- **Controller:** coordinates presentation/application interactions; it is not a hidden domain service.
- **SLD:** owns SLD-specific presentation/editing semantics.
- **Canvas:** owns viewport/interaction mechanics.
- **Core:** owns engineering truth.

No renderer, tool, or controller may become an alternate domain model.

## 13. Acceptance criteria

Phase A is complete when:

- Projection is a named architectural boundary rather than an implicit pattern.
- WorkspaceManager owns workspace/document lifecycle.
- Project, Document, and Workspace have distinct responsibilities.
- SLD and Canvas responsibilities are explicit in code.
- UI updates have a defined event/result-to-projection path.
- InteractionSession owns transient interaction state.
- Registries have deliberate ownership and lifecycle.
- UI lifecycle is explicit.
- Connection requests follow the Application boundary.
- Renderer/Tool/Controller boundaries are testable.
- `BusItem` and `LineItem` remain projections and do not become electrical authorities.
- Existing dummy rendering can continue to work.
- Architecture tests prevent direct UI-to-Core mutation paths where practical.
- Existing tests/regression checks continue to pass.

## 14. Completion sequence

Implementation should proceed in this order:

1. Projection contracts and adapters
2. WorkspaceManager and Project/Document/Workspace contracts
3. SLD/Layout/Canvas boundary
4. UI event/update boundary
5. InteractionSession
6. Registry ownership
7. UI lifecycle
8. Connection responsibility boundary
9. Renderer/Tool/Controller boundary cleanup
10. Architecture regression tests
11. Final repository audit against the GridForge V2 Working Rule Set

## 15. Definition of done

Phase A is not considered complete merely because the application starts. It is complete only when the architectural boundaries are represented in the repository, exercised by tests where practical, and documented well enough that Phase B can build the visual/application UI without reopening these fundamental ownership decisions.
