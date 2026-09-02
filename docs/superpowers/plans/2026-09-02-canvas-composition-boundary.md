# Canvas Composition Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a small application-owned Canvas composition boundary that wires existing Canvas services without changing their responsibilities or creating a second renderer framework.

**Architecture:** The new boundary composes already-existing services and supplies them to the Canvas presentation layer. `CanvasPlugin` remains a lifecycle/composition plugin; `GraphicsView` remains the Qt viewport boundary; `RenderSystem`, `RendererRegistry`, selection, navigation, coordinate, grid, snap, and preview services remain separately owned responsibilities. `BusItem` and `LineItem` are untouched.

**Tech Stack:** Python, PySide/Qt abstraction used by GridForge, existing UI Canvas/Core services, pytest where repository tests are available.

**Spec:** GridForge V2 authoritative architecture and approved Canvas Composition Boundary design in the conversation.

## Global Constraints

- Core owns authoritative electrical truth.
- Application controls meaningful mutation/use-case orchestration.
- UI expresses intent/results and must not directly mutate Core.
- Canvas owns viewport, geometry, interaction, and navigation only.
- QGraphicsItem remains a projection only.
- Existing renderer contracts remain authoritative; do not create a second renderer framework.
- `BusItem` and `LineItem` must not be modified in this phase.
- PluginManager remains plugin lifecycle/composition orchestration, not a Canvas service container.
- PluginContext remains a dependency carrier, not a service constructor.
- MainWindow remains a Qt host/composition boundary, not the Canvas service owner.
- Generated GridForge source/docs identify author `Subhendu Mishra`.

---

### Task 1: Add the Canvas composition boundary

**Files:**
- Create: `ui/canvas/canvas_composition.py`
- Test: repository-appropriate Canvas composition test location, if an existing test structure is present.

**Interfaces:**
- Consumes: `Controller`, `ToolManager`, existing Canvas services and renderer infrastructure.
- Produces: one explicit composition object containing the already-created/wired Canvas services and authoritative `GraphicsView` access.

- [ ] Inspect existing constructor signatures before implementation.
- [ ] Add focused failing tests for ownership/wiring and dependency identity.
- [ ] Implement only the minimal composition object.
- [ ] Verify tests pass.

### Task 2: Rewire CanvasPlugin to consume composition

**Files:**
- Modify: `ui/plugins/canvas_plugin.py`
- Test: existing CanvasPlugin tests or focused new tests.

**Interfaces:**
- Consumes: Canvas composition boundary from Task 1.
- Produces: lifecycle-managed Canvas widget/scene while retaining PluginManager/PluginContext responsibilities.

- [ ] Add failing test proving CanvasPlugin does not construct application-owned Canvas services itself.
- [ ] Replace only the construction seam required to consume the composition.
- [ ] Preserve plugin lifecycle and public accessors.
- [ ] Verify tests pass.

### Task 3: Wire application bootstrap

**Files:**
- Modify: `main.py`
- Modify: `ui/plugins/plugin_context.py` only if the established dependency carrier requires an exact additive field.

**Interfaces:**
- Consumes: Canvas composition boundary.
- Produces: complete application composition with Canvas services explicitly supplied rather than constructed by `GraphicsView`.

- [ ] Add/adjust focused bootstrap composition test.
- [ ] Wire the boundary at application composition level.
- [ ] Keep WorkspaceManager/WorkspaceController downstream of Canvas initialization.
- [ ] Verify application construction path.

### Task 4: Verify scene and service ownership

**Files:**
- Modify only if verification identifies a necessary seam correction.
- Test: focused Canvas ownership/integration tests.

- [ ] Verify the intended scene implementation is used consistently.
- [ ] Verify SelectionManager receives the external scene and remains authoritative through Controller selection.
- [ ] Verify RenderSystem receives RendererRegistry and the same scene.
- [ ] Verify InteractionManager receives ToolManager without owning it.
- [ ] Verify NavigationController remains viewport-only.
- [ ] Verify no Core mutation was introduced.
- [ ] Verify `BusItem` and `LineItem` remain unchanged.

### Task 5: Full verification and review

- [ ] Run focused tests.
- [ ] Run the repository test suite available on the branch.
- [ ] Inspect the final diff for architectural boundary violations.
- [ ] Confirm no unrelated files changed.
- [ ] Confirm `BusItem`/`LineItem` were not modified.
- [ ] Commit the completed implementation with a focused message.
