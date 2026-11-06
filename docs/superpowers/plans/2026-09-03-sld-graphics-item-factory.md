# SLD Graphics Item Factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a focused SLD graphics-item factory and integrate it into the canonical canvas render system without changing locked item classes.

**Architecture:** `SLDCanvasRenderSystem` remains the synchronization and scene-lifecycle owner. `SLDGraphicsItemFactory` becomes the sole construction boundary for `BusItem` and `LineItem`, consuming only renderer-neutral SLD canvas descriptors and never touching Core or Application state.

**Tech Stack:** Python, Qt abstraction in `ui.core.qt`, pytest.

**Spec:** `docs/superpowers/specs/2026-09-03-sld-graphics-item-factory-design.md`

## Global Constraints

- Author: Subhendu Mishra in generated GridForge V2 source/documentation files.
- `BusItem` and `LineItem` are locked and must not be modified.
- `SLDCanvasProjection` remains renderer-neutral and unchanged.
- `SLDCanvasRenderSystem` remains the canonical renderer.
- Do not create `SLDSceneRenderer` or a generic renderer registry.
- Core electrical truth remains outside the presentation layer.
- Factory owns construction only; renderer owns synchronization, styling, scene ownership, and disposal.

---

### Task 1: Add factory contract and tests

**Files:**
- Create: `ui/canvas/sld_graphics_item_factory.py`
- Create: `tests/test_sld_graphics_item_factory.py`

**Interfaces:**
- Consumes: `SLDCanvasNode`, `SLDCanvasConnection`, `QPointF`.
- Produces: `BusItem` and `LineItem` instances.

- [ ] **Step 1: Write failing tests** for node creation, connection creation, and invalid input types.
- [ ] **Step 2: Run the focused tests** and confirm they fail because the factory does not yet exist.
- [ ] **Step 3: Implement the minimal factory** with `create_node()` and `create_connection()` and explicit type validation.
- [ ] **Step 4: Run the focused tests** and confirm they pass.
- [ ] **Step 5: Commit the factory and tests.**

### Task 2: Integrate factory into canonical renderer

**Files:**
- Modify: `ui/canvas/sld_canvas_render_system.py`
- Test: `tests/test_sld_graphics_item_factory.py` and existing SLD canvas tests if present.

**Interfaces:**
- Consumes: `SLDGraphicsItemFactory` from Task 1.
- Produces: existing scene synchronization behavior with factory-owned item construction.

- [ ] **Step 1: Add a failing integration assertion** that `SLDCanvasRenderSystem` uses the factory boundary.
- [ ] **Step 2: Run the focused test** and confirm the assertion fails against direct construction.
- [ ] **Step 3: Inject/use `SLDGraphicsItemFactory` in the render system** while preserving existing styling, scene ownership, `_items`, clear, and dispose behavior.
- [ ] **Step 4: Verify no changes were made to `BusItem` or `LineItem`.**
- [ ] **Step 5: Run the focused and relevant SLD test suite.**
- [ ] **Step 6: Commit the integration.**

### Task 3: Architecture and regression verification

**Files:**
- No additional production files unless verification identifies a necessary correction.

- [ ] **Step 1: Inspect the final diff** for prohibited Core/Application dependencies or renderer-registry behavior.
- [ ] **Step 2: Run all available tests.**
- [ ] **Step 3: Verify `BusItem` and `LineItem` blobs are unchanged from their pre-task SHAs.**
- [ ] **Step 4: Verify the canonical path remains `SLDCanvasProjection → SLDCanvasRenderSystem → SLDGraphicsItemFactory → BusItem/LineItem → QGraphicsScene`.**
- [ ] **Step 5: Record the final audit result.**
