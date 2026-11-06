# GridForge V2 — Phase A Architecture Foundation Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining GridForge V2 architecture foundation so Phase B can build the visual/application UI without reopening ownership boundaries.

**Architecture:** Implement the approved Projection, Workspace, SLD/Canvas, interaction, registry, lifecycle, connection, and presentation-boundary contracts incrementally. Preserve existing dummy rendering and keep `BusItem`/`LineItem` projection-only; all meaningful electrical mutation remains behind Application → Core.

**Tech Stack:** Python, Qt/PySide-compatible presentation layer, existing GridForge Core/Application modules, pytest and existing repository regression tests.

**Spec:** `docs/superpowers/specs/2026-09-02-phase-a-architecture-foundation-design.md`

## Global Constraints

- Core Domain owns electrical truth and engineering meaning.
- Application controls meaningful mutation through commands, handlers, services, and use cases.
- Presentation expresses intent and renders results.
- Fundamental mutation flow is `Intent → Command → Application → Core`.
- Result/update flow is `Core → Domain Event / Result → Projection → UI`.
- Canvas owns viewport and interaction mechanics, not electrical truth.
- SLD is a first-class electrical visual projection and engineering editing surface.
- QGraphicsItem-derived objects are projections only.
- Plugins cannot bypass Application/Core boundaries.
- Persistence does not become part of domain ownership.
- Existing `BusItem` and `LineItem` are preserved unless a concrete contract violation requires a minimal boundary adjustment.
- Dummy rendering remains replaceable by authoritative application/core data without redesigning the UI architecture.
- Generated source/documentation files identify **Subhendu Mishra** as author.
- Prefer small, focused files with one responsibility; do not create monolithic architecture modules.

---

### Task 1: Establish repository architecture baseline and regression guard

**Files:**
- Inspect: `core/application/`, `ui/`, `tests/`, `main.py`, `contract.md`
- Create/modify: `tests/architecture/` focused boundary tests

**Interfaces:**
- Consumes: existing Core/Application/UI modules and approved Phase A spec.
- Produces: executable architecture checks and a baseline for subsequent tasks.

- [ ] **Step 1: Identify current boundary violations and existing contracts.**
- [ ] **Step 2: Add failing tests for UI-to-Core direct mutation and projection-only item expectations where the current repository permits those checks.**
- [ ] **Step 3: Run the focused architecture tests and record the failures.**
- [ ] **Step 4: Keep tests narrowly scoped to architectural ownership rather than implementation style.**
- [ ] **Step 5: Commit the baseline tests.**

---

### Task 2: Formalize Projection contracts

**Files:**
- Create/modify: `ui/projection/` focused projection contracts, records, adapters, and update coordination
- Test: `tests/architecture/test_projection.py`
- Preserve: `ui/items/` including existing `BusItem` and `LineItem`

**Interfaces:**
- Produces a stable presentation projection containing identity, display type, labels, geometry, status, connectivity references, and visual flags.
- Projection consumers receive presentation state rather than authoritative Core objects.

- [ ] **Step 1: Write failing tests proving projections carry presentation state without owning electrical mutation.**
- [ ] **Step 2: Run the focused projection tests and verify failure.**
- [ ] **Step 3: Implement the smallest projection contract and deterministic adapter/update path consistent with existing UI patterns.**
- [ ] **Step 4: Adapt existing dummy SLD data to projections without changing electrical behavior.**
- [ ] **Step 5: Run projection tests plus existing UI tests.**
- [ ] **Step 6: Commit the projection boundary.**

---

### Task 3: Separate Project, Document, and Workspace and add WorkspaceManager

**Files:**
- Create/modify: `ui/core/` or the existing application-boundary location discovered during implementation for project/document/workspace contracts
- Create/modify: `ui/workspace/` only if the repository's current structure supports a dedicated lifecycle package
- Test: `tests/architecture/test_workspace.py`

**Interfaces:**
- `Project`: persistent engineering container and project identity/configuration.
- `Document`: open/editable representation belonging to a project.
- `Workspace`: active application/UI context containing open documents, views, panels, selection/session and navigation state.
- `WorkspaceManager`: creates, activates, switches, and closes workspaces/documents.

- [ ] **Step 1: Write failing lifecycle tests for distinct Project/Document/Workspace responsibilities.**
- [ ] **Step 2: Verify tests fail before implementation.**
- [ ] **Step 3: Implement focused contracts and `WorkspaceManager` with deterministic active-state transitions.**
- [ ] **Step 4: Connect the existing shell/bootstrap to the manager without introducing persistence coupling.**
- [ ] **Step 5: Run focused and existing application tests.**
- [ ] **Step 6: Commit workspace lifecycle foundation.**

---

### Task 4: Formalize SLD, Layout, and Canvas boundaries

**Files:**
- Inspect/modify: `ui/canvas/`
- Inspect/modify: existing SLD-related package/files
- Create/modify: focused SLD layout contract where missing
- Test: `tests/architecture/test_sld_canvas_boundary.py`

**Interfaces:**
- Canvas owns viewport, pan/zoom, transforms, and generic scene/view mechanics.
- SLD owns electrical visual projection, SLD layout coordination, and engineering editing intent.
- Layout owns placement/geometry coordination, not Core electrical truth.

- [ ] **Step 1: Write failing tests asserting Canvas cannot be the owner of electrical mutation.**
- [ ] **Step 2: Run the tests and verify failure.**
- [ ] **Step 3: Introduce the smallest explicit SLD/Layout boundary around existing implementation.**
- [ ] **Step 4: Preserve `BusItem` and `LineItem` behavior while keeping them projection objects.**
- [ ] **Step 5: Run SLD/canvas regression tests and application startup tests.**
- [ ] **Step 6: Commit the SLD/Canvas boundary.**

---

### Task 5: Establish the UI event/update boundary

**Files:**
- Inspect/modify: `core/application/event_bus.py`, `core/application/events.py`
- Modify/create: `ui/events/` and `ui/projection/` focused bridge/update modules
- Test: `tests/architecture/test_ui_update_boundary.py`

**Interfaces:**
- Application events/results feed the projection update path.
- UI widgets/items refresh from projection state.
- Direct widget-to-Core mutation and ad-hoc cross-panel synchronization are prohibited.

- [ ] **Step 1: Write failing tests for event/result → projection → UI update flow.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement a narrow UI update boundary using existing application event infrastructure rather than creating a competing event system.**
- [ ] **Step 4: Route the existing dummy rendering refresh through the boundary.**
- [ ] **Step 5: Run focused and full regression tests.**
- [ ] **Step 6: Commit the UI update boundary.**

---

### Task 6: Introduce InteractionSession

**Files:**
- Inspect/modify: `ui/interaction/`
- Inspect/modify: `ui/tools/` and `ui/connections/`
- Test: `tests/architecture/test_interaction_session.py`

**Interfaces:**
- `InteractionSession` owns transient tool/mode, selection, connection/wiring, drag/edit, preview, and cancellation/commit state.
- It must not persist transient state into Core domain objects.

- [ ] **Step 1: Write failing tests for session creation, state transitions, cancellation, and reset.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement the focused session object and inject it into tools/controllers that currently hold transient state.**
- [ ] **Step 4: Remove duplicated transient state only where the session is now authoritative.**
- [ ] **Step 5: Run interaction and UI regression tests.**
- [ ] **Step 6: Commit InteractionSession ownership.**

---

### Task 7: Make registries explicit and lifecycle-aware

**Files:**
- Inspect/modify: `ui/equipment/`, `ui/renderers/`, `ui/tools/`, `ui/controllers/`, `ui/plugins/`
- Create focused registry modules only where a responsibility is currently implicit/global
- Test: `tests/architecture/test_registries.py`

**Interfaces:**
- Separate equipment/component, renderer, tool, controller, and plugin registration responsibilities.
- Each registry provides deterministic lookup plus explicit register/unregister and lifecycle ownership.

- [ ] **Step 1: Write failing tests for duplicate registration, deterministic lookup, unregister, and teardown.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement focused registry contracts using dependency injection instead of hidden globals.**
- [ ] **Step 4: Wire existing bootstrap registration into explicit owners.**
- [ ] **Step 5: Run registry and startup regression tests.**
- [ ] **Step 6: Commit registry ownership.**

---

### Task 8: Make UI lifecycle explicit

**Files:**
- Inspect/modify: `ui/bootstrap/`, `ui/main_window.py`, `ui/core/`, workspace lifecycle modules
- Test: `tests/architecture/test_ui_lifecycle.py`

**Interfaces:**
- Lifecycle order: application bootstrap → shell → workspace → document/view activation → close → workspace teardown → renderer/tool/controller cleanup.
- Correctness must not depend on accidental Python/Qt destruction order.

- [ ] **Step 1: Write failing lifecycle-order and cleanup tests.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement explicit startup/shutdown ownership and idempotent teardown.**
- [ ] **Step 4: Ensure registry-owned resources are released through lifecycle owners.**
- [ ] **Step 5: Run startup/shutdown and full regression tests.**
- [ ] **Step 6: Commit explicit UI lifecycle.**

---

### Task 9: Enforce connection responsibility boundary

**Files:**
- Inspect/modify: `ui/connections/`, `ui/tools/`, `ui/controllers/`
- Inspect/modify: `core/application/commands/` and existing endpoint/application services
- Test: `tests/architecture/test_connection_boundary.py`

**Interfaces:**
- UI produces connection intent/command.
- Application handles the request.
- Core performs authoritative topology mutation and validation when real electrical models are connected.
- Dummy phase may return a visual placeholder result without claiming authoritative topology.

- [ ] **Step 1: Write failing tests proving the connection tool does not directly mutate Core topology.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement/adapt the connection intent/command bridge to existing Application command infrastructure.**
- [ ] **Step 4: Keep dummy visual connection behavior behind the same intent boundary.**
- [ ] **Step 5: Run connection and full regression tests.**
- [ ] **Step 6: Commit connection ownership.**

---

### Task 10: Clean Renderer, Tool, and Controller boundaries

**Files:**
- Inspect/modify: `ui/renderers/`, `ui/tools/`, `ui/controllers/`, relevant `ui/items/`
- Test: `tests/architecture/test_presentation_boundaries.py`

**Interfaces:**
- Renderer translates projection state to visuals.
- Tool captures interaction and expresses intent.
- Controller coordinates presentation/application interactions.
- None becomes an alternate domain model.

- [ ] **Step 1: Write failing boundary tests for direct Core ownership/mutation from renderer/tool/controller code.**
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Move only violating responsibilities behind existing Projection/Application contracts.**
- [ ] **Step 4: Preserve existing `BusItem` and `LineItem` as visual projections.**
- [ ] **Step 5: Run focused presentation tests and full regression.**
- [ ] **Step 6: Commit presentation-boundary cleanup.**

---

### Task 11: Architecture regression suite and final audit

**Files:**
- Modify: `tests/architecture/`
- Modify: `docs/` architecture documentation only where implementation differs from existing wording
- Inspect: `contract.md`, `README.md`, Modification Register

**Interfaces:**
- All Phase A acceptance criteria become executable checks where practical.

- [ ] **Step 1: Run the complete architecture suite.**
- [ ] **Step 2: Run the complete existing test suite.**
- [ ] **Step 3: Check that `BusItem` and `LineItem` remain projection-only and dummy rendering still works.**
- [ ] **Step 4: Audit dependencies for Core/UI inversion or Application bypasses.**
- [ ] **Step 5: Update architecture documentation and modification register with the completed boundaries.**
- [ ] **Step 6: Commit the Phase A completion state.**

---

## Final Definition of Done

Phase A is complete only when Projection is explicit, WorkspaceManager owns lifecycle, Project/Document/Workspace are distinct, SLD/Layout/Canvas boundaries are represented in code, UI updates follow event/result → projection, InteractionSession owns transient interaction state, registries and UI lifecycle have explicit owners, connection requests cross the Application boundary, Renderer/Tool/Controller responsibilities are testable, existing `BusItem`/`LineItem` remain projections, dummy rendering continues to work, architecture regression tests pass, and the repository has been audited against the GridForge V2 Working Rule Set.
