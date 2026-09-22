# GridForge V2 — SLD RCA Static Correction Report — 2026-09-22

Repository: `madhuri196mishra-cpu/GridForge`
Branch: `main`
Correction scope: RCA-SLD-AUTH-001 / RCA-003-B35-001 / RCA-004 / RCA-005 / RCA-009

## Verification boundary

This is a **static source re-audit only**. No tests, CI, application startup, GUI execution, or runtime verification was performed.

## 1. Files changed

- `core/application/commands/placement_commands.py`
- `core/application/placement_command_handlers.py` — removed
- `core/application/sld_command_handlers.py`
- `core/application/command_handlers.py`
- `core/application/application.py`
- `ui/events/sld_update_coordinator.py`
- `ui/sld/sld_read_synchronizer.py`

## 2. Canonical reconciliation owner

The existing `ui.sld.sld_read_synchronizer.SLDReadSynchronizer`, invoked by `ui.events.sld_update_coordinator.SLDUpdateCoordinator`, is the canonical semantic-to-document reconciliation seam.

It consumes Application `NetworkReadModel` data, updates `SLDProjectionManager`, reconciles `SLDDocument.model`, removes stale projection-owned nodes/connections, and preserves existing node geometry.

No new SLD architecture was introduced.

## 3. Exact event → reconciliation path

`Application._publish_semantic_events()` now propagates `ApplicationResult.metadata` into model semantic events.

For engineering mutations:

`Application.execute()`
→ `CommandManager.execute()`
→ model handler
→ Core/Application model service
→ `ElementCreated` / `ElementUpdated` / `ElementRemoved`
→ existing UI event boundary
→ `SLDUpdateCoordinator.refresh()`
→ `SLDReadSynchronizer.synchronize_network()`
→ `SLDDocument.model`
→ `SLDCanvasProjection`
→ `SLDCanvasRenderSystem`
→ graphics.

The central Application event route remains unchanged.

## 4. Engineering identity → SLD identity

`ElementReadModel.object_id` is used as both:

- `SLDNode.node_id`
- `SLDNode.equipment_id`

The canvas projection carries `node_id` and `equipment_id` as renderer-neutral values. `SLDGraphicsItemFactory` passes the SLD node identity into presentation graphics; it does not receive Core objects.

No memory-address identity or second engineering identity was introduced.

## 5. Bus creation

`ui.tools.bus_tool.BusTool` still emits `PlaceBusCommand`, satisfying the UI workflow contract.

The compatibility constructor in `core/application/commands/placement_commands.py` now emits the canonical command identity `model.create_bus` via `CREATE_BUS`.

The former compound `BusPlacementCommandHandler` and its `AddSLDNodeCommand` mutation path were removed.

`ModelCommandHandlers.create_bus()` is the sole canonical Bus engineering handler. Presentation coordinates are treated as presentation hints and are not passed to the Core Bus service.

The event metadata carries those hints to the existing SLD reconciler, which applies them only when creating a missing presentation node.

## 6. Transformer creation

`ui.tools.transformer_tool.TransformerTool` emits `CreateTransformerCommand`.

`ModelCommandHandlers.create_transformer()` resolves endpoints through the Application endpoint resolver and delegates to `ModelService.create_transformer()`.

No SLD command is issued by the tool.

The existing semantic event → read-model → SLD reconciliation route handles the resulting presentation.

## 7. Update

The SLD reconciler reads the current `NetworkReadModel` and reconciles the existing node by canonical identity.

It does not use `ElementUpdated.changes` as authoritative engineering state.

Existing node position is preserved during an update.

## 8. Delete

The synchronizer computes active engineering IDs from the authoritative `NetworkReadModel`.

Projection-owned SLD nodes whose equipment IDs are no longer active are removed. Projection-owned SLD connections not represented by the current read model are also removed.

Topology mutation remains outside the SLD reconciler.

## 9. Project load/reopen

`core/application/project_lifecycle.py` remains the persistence/load authority and restores persistent presentation state.

`Application.open_project()` rebinds the SLD service when configured and publishes `ProjectLoaded`.

`SLDUpdateCoordinator` binds the restored `SLDDocument` and runs the same read-model reconciliation path.

Existing presentation geometry is retained when a corresponding projection node already exists.

QGraphics state is not part of the SLD document model.

## 10. Empty project

The reconciliation implementation does not create catalogue/tool entries. With an empty authoritative network, the projection-owned SLD node set remains empty.

Equipment catalogue/tool authority remains outside the SLD reconciler.

## 11. Undo/redo

`CommandManager` retains the existing transaction/history lifecycle.

Bus creation is now one canonical engineering command identity, so ordinary placement does not create a second SLD command/history record.

Undo/redo re-enters the normal Application event path; the SLD reconciler then removes/recreates presentation state from the authoritative read model.

This is source-level evidence only.

## 12. Failure behavior

`CommandManager` distinguishes pre-commit rollback from post-commit history failures.

`SLDUpdateCoordinator.refresh()` now records the most recent reconciliation exception in `last_reconciliation_error` and re-raises it instead of silently swallowing presentation failure. The same full-network reconciliation method remains callable on a subsequent event, providing a rebuild/recovery seam without mutating Core.

No rollback of an already committed Core transaction is claimed.

## 13. application.place_bus disposition

The former command identity `application.place_bus` is no longer an active command identity.

`PLACE_BUS` is retained only as a compatibility symbol and aliases canonical `CREATE_BUS`.

The former compound handler was deleted.

The obsolete semantic-event branch for literal `application.place_bus` was deleted.

Static source inspection found no remaining intended active implementation of the old command path.

## 14. ApplicationResult consumer disposition

`core/application/results.py` still defines `ApplicationResult.value` as the canonical Core object returned by services.

This correction does not speculateively destroy that public contract.

No UI `.value` consumer was established as a safe basis for closing the finding from the available static repository search. Therefore the ApplicationResult finding remains **OPEN — CONSUMER AUDIT / CONTRACT GAP**.

The SLD reconciliation path does not consume `ApplicationResult.value`; it consumes Application ReadModels.

## 15. Terminal identity status

**OPEN.**

`ui/tools/endpoint_identity_adapter.py` currently maps Bus presentation objects to bus-level endpoint references. The full generic multi-terminal presentation identity contract has not been statically demonstrated for all required equipment.

No Core `Terminal` inspection was introduced into SnapSystem or the SLD renderer.

## 16. Parallel-path search

The former compound Bus path was removed from:

- `core/application/placement_command_handlers.py`
- `core/application/sld_command_handlers.py`
- `core/application/application.py`

`BusTool` remains the only inspected UI consumer of `PlaceBusCommand`, and that constructor now emits canonical `model.create_bus`.

SLD presentation commands remain valid for explicit presentation/document operations such as node positioning; they are not used by engineering placement tools.

## 17. Master-register disposition

- RCA-SLD-AUTH-001: **OPEN — CORRECTION IMPLEMENTED; STATIC RE-AUDIT COMPLETE FOR THE CORRECTED SEAM**
- RCA-SLD-AUTH-001-B31-001: **CORRECTED — STATIC RE-AUDIT**
- RCA-SLD-AUTH-001-B32-001: **CORRECTED — STATIC RE-AUDIT**
- RCA-003-B35-001: **CORRECTED — LEGACY COMMAND RECONCILED**
- ApplicationResult Core-object exposure: **OPEN — CONSUMER AUDIT / CONTRACT GAP**
- Terminal identity: **OPEN — GENERIC MULTI-TERMINAL CONTRACT NOT YET PROVEN**
- Rendering separation: **STATICALLY PRESENT** in `ui/canvas/sld_canvas_projection.py`, `ui/canvas/sld_canvas_render_system.py`, and `ui/canvas/sld_graphics_item_factory.py`; runtime coverage remains unverified.

## 18. Workflow re-audit

The listed SLD workflows `SLD-WF-006`, `007`, `016`, `020`, `023`, `025`, `103`, `104`, `106`, `107`, `116`, `118`, `121`, `122`, `129`, `132`, `133`, `134`, `135`, `136`, and `137` now share the corrected central semantic-to-document reconciliation seam where they use engineering create/update/delete events.

No workflow is marked runtime-verified. Workflow closure remains subject to the unresolved terminal identity, ApplicationResult consumer, persistence/runtime, and rendering execution evidence where applicable.

## 19. Static rendering path

The current source path is:

`SLDDocument.model`
→ `ui.canvas.sld_canvas_projection.SLDCanvasProjection`
→ `SLDCanvasSnapshot`
→ `ui.canvas.sld_canvas_render_system.SLDCanvasRenderSystem`
→ `ui.canvas.sld_graphics_item_factory.SLDGraphicsItemFactory`
→ `BusItem` / `EquipmentItem` / `LineItem`.

The render system consumes renderer-neutral snapshots and does not mutate Application/Core state.

## 20. Remaining OPEN findings

1. Generic terminal identity for multi-terminal equipment.
2. ApplicationResult Core-object consumer audit.
3. Full persistence/load semantic round-trip execution evidence.
4. Runtime/event/Canvas execution evidence.
5. Existing broader GF-MASTER-0037/0038/0039 verification clusters remain open where their scope exceeds this correction seam.

No tests or CI were run.
