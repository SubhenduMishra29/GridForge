# Default Panel Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `PanelsPlugin.initialize()` create the three existing canonical SLD-first docks required by the application composition root.

**Architecture:** Reuse the existing declarative definitions and concrete widgets in `ui/panels/default_panels.py`. Keep dock creation in `PanelsPlugin`; keep arrangement in `WorkspaceRealizer`; keep logical activation in `WorkspaceController`.

**Tech Stack:** Python, PySide6 through `ui.core.qt`, pytest-style tests already organized under `tests/ui`.

**Spec:** `docs/superpowers/specs/2026-08-30-default-panel-composition-design.md`

## Global Constraints

- All Qt dependencies used by UI code pass through `ui.core.qt`.
- `PanelsPlugin` owns panel/dock creation and lifecycle.
- `WorkspaceRealizer` owns dock arrangement only.
- `WorkspaceController` owns prepare → realize → commit orchestration.
- No engineering truth or duplicate engineering state is introduced.
- Do not create duplicate `project`, `equipment`, or `properties` panel implementations.

---

### Task 1: Add the regression test

**Files:**
- Create: `tests/ui/plugins/test_panels_plugin.py`
- Read: `ui/plugins/panels_plugin.py`
- Read: `ui/panels/default_panels.py`

**Interfaces:**
- Consumes: `PanelsPlugin`, `PluginContext`, and canonical default panel IDs.
- Produces: a regression test proving initialization creates all required docks and remains idempotent.

- [ ] **Step 1: Write the failing test**
  - Construct `QApplication` if needed.
  - Construct a `QMainWindow` and `PluginContext(main_window=window)`.
  - Initialize `PanelsPlugin`.
  - Assert `panel_ids == ("project", "equipment", "properties")`.
  - Assert each `get_dock(panel_id)` is a `QDockWidget` with object name equal to the panel ID.
  - Initialize again with the same context and assert the same dock objects remain registered.
  - Shutdown and assert the panel IDs and docks are gone.

- [ ] **Step 2: Run the focused test and confirm it fails**
  - Expected failure: `PanelsPlugin.initialize()` leaves `panel_ids` empty.

### Task 2: Register canonical defaults during plugin initialization

**Files:**
- Modify: `ui/plugins/panels_plugin.py`

**Interfaces:**
- Consumes: `compose_default_panel_specs()` from `ui.panels.default_panels`.
- Produces: initialized `PanelsPlugin` exposing `project`, `equipment`, and `properties` docks.

- [ ] **Step 1: Import the existing default-panel composer locally inside `initialize()`**
  - Keep the import local to avoid a module-level cycle because `default_panels.py` imports `PanelSpec` from `ui.plugins.panels_plugin`.

- [ ] **Step 2: Register each canonical spec after the context/host validation succeeds**
  - Iterate over `compose_default_panel_specs()` and call `self.add_panel(spec)`.
  - Do not add workspace placement or visibility policy.

- [ ] **Step 3: Preserve idempotent initialization**
  - Leave the existing early return for an already initialized plugin unchanged.

- [ ] **Step 4: Run the focused regression test**
  - Expected result: all assertions pass.

### Task 3: Verify repository integration

**Files:**
- Read: `main.py`
- Read: `ui/workspace/workspace_controller.py`
- Read: `ui/workspace/workspace_realizer.py`
- Read: `ui/plugins/panels_plugin.py`

- [ ] **Step 1: Verify `main.py` can obtain all three docks after `initialize_all()`**
- [ ] **Step 2: Verify `WorkspaceController` remains unchanged and still performs prepare → realize → commit**
- [ ] **Step 3: Verify `WorkspaceRealizer` still only consumes already-created docks**
- [ ] **Step 4: Fetch the final changed files and inspect the resulting diff/content**
- [ ] **Step 5: Run the available repository test suite or CI workflow if the repository exposes one**
- [ ] **Step 6: Commit only after verification succeeds**
