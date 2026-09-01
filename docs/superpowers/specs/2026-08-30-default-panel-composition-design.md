# Default Panel Composition Design

## Goal
Ensure the existing `PanelsPlugin` creates and exposes the three canonical SLD-first docks required by `main.py`: `project`, `equipment`, and `properties`.

## Architecture
`ui/panels/default_panels.py` is already the authoritative source for the three concrete presentation widgets and declarative `PanelSpec` definitions. `PanelsPlugin` owns dock/widget creation and lifecycle, while `WorkspaceRealizer` remains responsible only for placement and visibility/layout realization. The fix therefore belongs in `PanelsPlugin.initialize()`: after establishing the `PluginContext`, compose the canonical default panel specs through the existing factory and register them with `add_panel()`.

## Existing verified boundaries
- `main.py` requires `PanelsPlugin.get_dock("project")`, `get_dock("equipment")`, and `get_dock("properties")` after plugin initialization.
- `PanelsPlugin` already owns QWidget/QDockWidget creation and exposes `add_panel()` and `get_dock()`.
- `ui/panels/default_panels.py` already defines `project`, `equipment`, and `properties` and provides `compose_default_panel_specs()`.
- `WorkspaceController` performs prepare → realize → commit; it must not be changed for this integration.
- `WorkspaceRealizer` must not create panels or decide panel identity.

## Change
During first successful `PanelsPlugin.initialize(context)`, call `compose_default_panel_specs()` and register each resulting `PanelSpec` with `add_panel()`. Preserve existing initialization idempotency: repeated initialization with the same context must not recreate docks.

## Testing
Add a focused plugin test that constructs a minimal valid `PluginContext`, initializes `PanelsPlugin`, and asserts that all three canonical panel IDs and docks exist, have the expected object names/titles, and are cleared on shutdown. The test should also verify repeated initialization does not duplicate panels.

## Non-goals
- No new panel widget files.
- No workspace changes.
- No MainWindow changes.
- No Core/model changes.
- No change to dock placement policy.
