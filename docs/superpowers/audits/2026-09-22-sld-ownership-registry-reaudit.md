# GridForge V2 — SLD Ownership / Registry Re-audit

Date: 2026-09-22
Repository: `SubhenduMishra29/GridForge`
Implementation branch audited: `main`
Author/header: `Subhendu Mishra`
Verification mode: static source inspection only
Runtime verification: deferred

## Scope

This correction batch follows:

`FETCH → AUDIT → RCA → CORRECT → FETCH → RE-AUDIT`

No tests, pytest, CI, application startup, GUI execution, or runtime verification were performed.

The canonical SLD chain remains:

`Application ReadModel → SLDReadAdapter → SLDProjectionManager → SLDReadSynchronizer → SLDDocument / SLDModel → SLDCanvasProjection → renderer`

No second SLD synchronization path was introduced.

## Findings Corrected

### RCA-SLD-AUTH-001-A — Legacy projection ownership bypass

Classification before correction: CONFIRMED IMPLEMENTATION DEFECT.

Previous behavior allowed legacy recovery to accept either application/network or protection projection source before the later ownership guard.

Correction:
- `SLDReadSynchronizer._require_projection_ownership()` is now the single ownership invariant used by both legacy recovery and normal existing-node reconciliation.
- Legacy migration requires exact equality between persisted `projection_source` and requested `projection_source`.
- NETWORK cannot adopt PROTECTION-owned legacy state.
- PROTECTION cannot adopt NETWORK-owned legacy state.
- A node without projection ownership metadata is not silently converted into projection-owned state.
- `equipment_id` and `node_id` identity rules remain unchanged.

Disposition: REMEDIATED — VERIFICATION DEFERRED.

### RCA-SLD-AUTH-001-B — Projection registry stale-state leak

Classification before correction: CONFIRMED IMPLEMENTATION DEFECT.

### RCA-SLD-AUTH-001-C — Stale cleanup method binding defect

Classification discovered during re-audit: CONFIRMED IMPLEMENTATION DEFECT.

The stale-node helper was declared without the `self` parameter even though it is invoked as an instance method and uses `self._projection_manager`. This made the stale cleanup path structurally inconsistent with its call sites.

Correction:
- `_remove_stale_projection_node()` now has the explicit `self` receiver.
- The existing domain-safe registry cleanup remains inside the method.

Disposition: REMEDIATED — VERIFICATION DEFERRED.


Correction:
- Stale projection cleanup resolves the projection domain from the node's existing projection source before ownership metadata is removed.
- When engineer-owned connections require retaining the node, the matching semantic projection registry entry is removed first.
- The preserved node keeps `node_id`, geometry, and engineer-owned connections.
- Projection ownership metadata and `equipment_id` are then cleared.
- If a registry entry exists under a conflicting domain, cleanup raises an ownership mismatch instead of silently deleting the other domain's projection.
- Network reconciliation now explicitly calls `SLDProjectionManager.reconcile_network(active_ids)`.
- Protection reconciliation continues to call `reconcile_protection(active_ids)`.

Disposition: REMEDIATED — VERIFICATION DEFERRED.

## Ownership State Machine

The implemented invariant is:

`existing projection source == requested projection source`

| Existing state | Requested domain | Static disposition |
|---|---|---|
| New node | NETWORK | Allowed |
| New node | PROTECTION | Allowed |
| NETWORK projection | NETWORK | Allowed |
| PROTECTION projection | PROTECTION | Allowed |
| NETWORK projection | PROTECTION | Rejected |
| PROTECTION projection | NETWORK | Rejected |
| Engineer-owned | NETWORK | Rejected |
| Engineer-owned | PROTECTION | Rejected |
| Legacy compatible NETWORK | NETWORK | Migrated |
| Legacy compatible PROTECTION | PROTECTION | Migrated |
| Legacy NETWORK | PROTECTION | Rejected |
| Legacy PROTECTION | NETWORK | Rejected |

No ownership conversion is performed.

## Single-element synchronization

`SLDReadSynchronizer.synchronize_element_from_application()` is now explicitly network-domain.

A Relay read model is rejected from this path with an instruction to use the protection reconciliation path. The generic `synchronize_element()` path has the same Relay exclusion.

Static evidence therefore supports:
- Relay is protection-owned;
- the single-element network path does not silently project Relay into NETWORK SLD ownership;
- protection Relay projection enters through `synchronize_protection()`.

Disposition: REMEDIATED for the identified Relay domain bypass risk — VERIFICATION DEFERRED.

Further consumer tracing remains required before the broader single-element finding is closed.

## Projection manager / registry

`SLDProjectionManager.project()` validates and preserves explicit `ProjectionDomain` ownership.

`SLDProjectionManager.remove()` accepts an optional domain and therefore cannot intentionally remove a projection from another domain when the domain is supplied.

`ProjectionRegistry.remove()` is also domain-constrained.

NETWORK and PROTECTION remain separate ownership domains. No registry deletion or namespace merge was introduced.

## Terminal identity audit

Static evidence confirms:
- Core/Application `EndpointReference.terminal()` identifies a terminal by `equipment_id + equipment_type + terminal_role`.
- `EndpointResolver` resolves that reference through the canonical Core equipment and its authoritative terminal collection.
- UI `EquipmentTerminal` currently also carries a distinct `terminal_id`.
- UI `TerminalResolver` indexes `EquipmentTerminal` by `terminal_id`.
- `EndpointIdentityAdapter` currently converts supported snapped presentation objects to `EndpointReference`; it does not establish a second Core terminal identity.

Disposition: RCA-SLD-TERM-001 — OPEN — INCOMPLETE INTEGRATION.

Required next audit: establish the explicit relationship between UI `EquipmentTerminal.terminal_id` and Application `EndpointReference(object_id, terminal_role)` without introducing a generic Port abstraction or second Core identity authority.

## ApplicationResult consumer boundary

`ApplicationResult.value` remains present because the current source evidence shows it is part of Application command/result infrastructure.

The complete UI/projection consumer trace is not yet closed.

Disposition: RCA-003 / RCA-009 — OPEN.

No speculative removal or UI exposure of Core objects was performed.

## Project load / reopen / idempotency

Static source evidence confirms `ProjectLifecycleService.open_project()` loads persisted project state and reconstructs presentation through the configured presentation deserializer/factory before activation.

The SLD reconciliation path now:
- uses `equipment_id` lookup before creating nodes;
- preserves existing `node_id`;
- does not overwrite existing geometry during semantic refresh;
- updates an existing projection rather than registering a duplicate;
- reconciles stale NETWORK and PROTECTION projection registry entries by domain.

Disposition: OPEN for complete end-to-end project reopen and persisted-geometry workflow audit; no runtime closure claimed.

## UI dirty shutdown

`Application.close_project()` already accepts an explicit `ProjectTransitionDecision` and rejects an omitted decision for dirty state through `ProjectTransitionRequired`.

`UILifecycle.close()` itself has no decision-provider stage and mechanically closes the document/workspace.

Disposition: RCA-UI-LIFECYCLE-001 — OPEN — CONFIRMED WORKFLOW DEFECT.

No lifecycle architecture change was made in this batch.

## Qt diagnostic

No runtime or overload execution was performed.

The diagnostic:

`qt_isinstance(QPointF(...), QPolygon | Sequence[QPoint] | QRect)`

therefore remains:

RCA-UI-CANVAS-QT-001 — OPEN — SOURCE EVIDENCE PENDING.

Absence of an explicit `qt_isinstance()` call in inspected source is not treated as closure.

## Canonical Bus path / legacy delete_bus

The canonical Bus path remains Application/CommandManager driven.

`core/application/commands/delete_bus.py` remains classified LEGACY / UNVERIFIED pending complete consumer and registration tracing.

It was not deleted.

## Register disposition

### REMEDIATED — VERIFICATION DEFERRED
- RCA-SLD-AUTH-001-A — legacy ownership bypass.
- RCA-SLD-AUTH-001-B — stale projection registry cleanup.
- RCA-SLD-AUTH-001-C — stale cleanup method binding defect.
- Single-element Relay protection-domain rejection.
- Network/protection projection registry reconciliation.
- Existing node identity and geometry preservation remain intact.

### OPEN
- RCA-SLD-AUTH-001 overall — do not close yet.
- RCA-SLD-TERM-001 — terminal identity integration.
- RCA-003 / RCA-009 — ApplicationResult complete consumer boundary.
- Project load/reopen/idempotency complete workflow verification.
- RCA-UI-LIFECYCLE-001 — dirty shutdown decision provider.
- RCA-UI-CANVAS-QT-001 — Qt overload/conversion source tracing.
- `delete_bus.py` — LEGACY / UNVERIFIED.

## Architecture preservation

The correction preserves:
- one authoritative Core engineering state;
- one Application mutation/orchestration boundary;
- ReadModels as the UI-facing semantic boundary;
- SLDDocument/SLDModel as presentation/document state;
- CommandManager as mutation authority;
- TopologyManager as topology authority;
- separate NETWORK and PROTECTION projection ownership;
- stable `equipment_id` engineering identity;
- stable `node_id` presentation identity.

No `SLD → Core` mutation path was introduced.
No generic Port abstraction was introduced.
No parallel SLD synchronization architecture was introduced.
BusItem and LineItem were not modified.

## Closure standard

This batch is source-corrected but not runtime-verified.

Final status: **REMEDIATED — VERIFICATION DEFERRED** for the corrected implementation defects.

RCA-SLD-AUTH-001 remains open pending the broader end-to-end ownership, lifecycle, terminal, consumer, persistence, and runtime verification work.
