# GridForge V2 — Post-Re-Audit Correction Addendum — 2026-09-22

Repository: `madhuri196mishra-cpu/GridForge`
Branch: `main`
Author/header: Subhendu Mishra

## Verification boundary

Static source correction only.

No pytest, CI, application startup, GUI execution, integration tests, or runtime verification was performed.

## Corrections implemented

### GF-MASTER-0061 — graphics identity

`ui/canvas/sld_graphics_item_factory.py` now propagates:

- `equipment_id` when an SLD node represents Core equipment;
- an explicit `presentation:<node_id>` graphics identity when `equipment_id is None`.

`node_id` remains the SLD/document identity. `BusItem` and `LineItem` were not modified.

### GF-MASTER-0063 — stale projection cleanup

`ui/sld/sld_read_synchronizer.py` now:

- preserves node identity and geometry when engineer-owned connections require retention;
- removes projection-owned attached connections;
- rejects unknown connection ownership instead of silently classifying it;
- clears projection metadata before converting a retained node to engineer-owned/presentation-only;
- removes the corresponding projection registry entry when applicable.

`core/application/services/sld_service.py` now marks explicitly engineer-created SLD nodes/connections and rejects removal of projection-owned or unknown-owned presentation structure.

### Projection registry lifecycle

`SLDProjectionManager.clear()` was added as an explicit registry lifecycle operation.

`SLDUpdateCoordinator` clears projection state at:

- successful `ProjectClosed`;
- successful `ProjectLoaded`, including new-project and project-replacement activation.

No speculative cleanup was added to arbitrary UI code. Activation rollback remains outside the event path and therefore does not clear the old project's registry before a successful replacement event.

### Terminal identity

`ui/tools/endpoint_identity_adapter.py` now contains an explicit terminal-to-endpoint adaptation seam.

`EquipmentTerminal.terminal_id` remains UI registry identity only. The resulting `EndpointReference` uses:

`equipment_id + terminal_role`

with `EquipmentTerminal.terminal_name` serving as the presentation terminal-role input.

No `Port` abstraction or second Core terminal identity was introduced.

### Dirty shutdown

A composition-owned `ProjectCloseController` was added.

The MainWindow close path is now:

`window close`
→ injected close handler
→ dirty check
→ SAVE / DISCARD / CANCEL decision provider
→ `Application.close_project(decision)`
→ lifecycle/project events.

CANCEL keeps the window open. Missing close-handler configuration fails closed.

The composition root supplies the Qt SAVE/DISCARD/CANCEL decision provider.

## ApplicationResult

`ApplicationResult.value` was retained.

No evidence from the inspected SLD/UI path established a UI consumer that safely receives Core objects through this field. The broader consumer audit remains OPEN and is not closed by this correction.

## Remaining OPEN findings

- `RCA-SLD-AUTH-001` — not closed.
- full ApplicationResult consumer-boundary audit;
- complete generic multi-terminal terminal/connection authority;
- persistence/reopen runtime evidence;
- runtime/event/Canvas execution evidence;
- `RCA-UI-CANVAS-QT-001` remains OPEN;
- dirty-shutdown runtime verification remains deferred.

Correction commits are not closure evidence.

## Compliance

- No tests run.
- No CI run.
- No application startup.
- No GUI execution.
- No integration tests.
- No Core mutation authority moved into UI.
- No second SLD synchronizer introduced.
- No second topology authority introduced.
- No generic Port abstraction introduced.
- `BusItem` and `LineItem` were not modified.
