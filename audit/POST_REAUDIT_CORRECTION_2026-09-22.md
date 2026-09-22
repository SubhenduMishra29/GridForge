# GridForge V2 — Post-Re-Audit Correction Report — 2026-09-22

Repository: madhuri196mishra-cpu/GridForge
Branch: main
Author/header: Subhendu Mishra
Active HEAD: 8eab2c14dde8f488748da8a9fce3732f653c5ece
Merge provenance: PR #163, targeted corrections, from madhuri196mishra-cpu/main

## Operating boundary

FETCH → AUDIT → RCA → CORRECT → FETCH → RE-AUDIT was followed for this batch.

No tests, pytest, CI, application startup, GUI execution, or runtime verification was run.

## Files changed

1. ui/sld/sld_read_synchronizer.py
2. ui/sld/sld_read_adapter.py
3. audit/MASTER_AUDIT_REGISTER.md
4. audit/POST_REAUDIT_CORRECTION_2026-09-22.md

## Exact code changes

### ui/sld/sld_read_synchronizer.py

- Added an ownership guard after equipment_id reconciliation.
- An existing SLD node is no longer silently converted to the requested projection domain when its projection_source belongs to another domain or is absent/engineer-owned.
- Stale projection cleanup now distinguishes engineer-owned attached connections from projection-owned connections.
- If engineer-owned presentation connections are attached to a stale projection node, the node is retained as presentation-only and its persisted geometry/document identity is preserved.
- If no engineer-owned connections are attached, projection-owned connections are removed first and the stale projection node is removed.
- Projection registry cleanup remains aligned with document cleanup.

### ui/sld/sld_read_adapter.py

- Preserved EngineeringParameterReadModel values while adapting Application ReadModels into SLD ReadModels.
- No Core objects are introduced into the SLD adapter.

## ApplicationResult consumer audit

Inspected ApplicationResult usage in the active Application boundary.

Observed ApplicationResult.value usage is internal to the Application command/result contract, including ModelCommandHandlers.create_bus() copying the result value while adding presentation metadata.

No inspected UI SLD synchronizer, projection, canvas, or tool consumes ApplicationResult.value.

Therefore:
- ApplicationResult.value remains as compatibility infrastructure.
- It must not be removed blindly.
- RCA-003 / RCA-009 remain OPEN because the required repository-wide closure is broader than this static batch.

## Canonical Bus creation audit

No Application.place_bus method exists in the active source inspected.

Canonical Bus path:

BusTool
→ PlaceBusCommand
→ model.create_bus
→ Application.execute
→ CommandManager
→ ModelCommandHandlers.create_bus
→ ModelService.create_bus
→ Core
→ semantic events
→ Application ReadModel
→ SLD reconciliation.

The separate core/application/commands/delete_bus.py module remains legacy/unverified. It was not found in the canonical ModelCommandHandlers registration inspected, so it was not deleted speculatively.

## SLD identity audit

The active contract remains:

- equipment_id = canonical engineering identity.
- node_id = document-local SLD identity.

Existing nodes are reconciled by equipment_id. Existing node_id and geometry are retained.

A new ownership guard now prevents an engineer-owned node from being silently converted into a projection-owned node.

## Connection identity audit

Projection connection IDs currently use the engineering branch object_id as the deterministic default. The source contains collision protection: an existing connection with the same ID but without the projection ownership marker is rejected.

Core topology remains outside the SLD connection model.

Engineer-owned connection preservation is now explicitly handled during stale projection-node removal.

RCA-005 remains OPEN because full terminal-aware connection semantics are not proven.

## Terminal identity audit

The Core contract is explicit:

owner + terminal role + endpoint.

EndpointReference.terminal() uses:

equipment_id + terminal_role.

However, the current UI path still contains a separate EquipmentTerminal representation using:

terminal_id + equipment_id + terminal_name.

EndpointIdentityAdapter currently supports BusItem identity and pre-existing EndpointReference values; it does not construct Core terminal references from the UI terminal registry.

Therefore the complete workflow:

Core Terminal
→ Application ReadModel
→ presentation terminal identity
→ SnapSystem
→ EndpointReference
→ Application connection command
→ Core validation
→ TopologyManager

remains OPEN.

No generic Port abstraction was introduced.

## LineTool audit

LineTool is a specialized engineering operation, not a free-form graphical wire.

It constructs CreateLineCommand and requires endpoint references plus engineering line parameters.

The command enters Application.execute() and is resolved through EndpointResolver before LineModelService/Core mutation.

The current limitation is terminal identity coverage, not a separate LineTool Core mutation path.

RCA-SLD-INTERACTION-001 / RCA-005 remain OPEN until terminal-aware presentation endpoints are fully proven.

## Idempotency / project-load audit

The semantic refresh path remains deterministic and read-model based.

The source preserves existing node positions and persisted node IDs during ordinary reconciliation.

ProjectLoaded explicitly reconciles both network and protection read domains.

No historical creation-event replay is required by SLDUpdateCoordinator for ProjectLoaded.

However, static source evidence alone does not prove runtime idempotency, reload behavior, or complete stale-structure cleanup, so these remain verification-deferred/open where applicable.

## UI lifecycle

The shutdown defect remains OPEN.

Current source has:
- Application.close_project(decision=...)
- dirty-state guard
- ProjectTransitionRequired when decision is absent.

But the inspected MainWindow is a mechanical Qt host without a shutdown decision provider, and UILifecycle does not establish the SAVE/DISCARD/CANCEL decision chain.

Required unresolved workflow:

shutdown request
→ dirty-state inspection
→ UI decision provider
→ ProjectTransitionDecision
→ Application.close_project(decision)
→ ProjectClosed
→ UI teardown.

CANCEL must not become an unhandled terminal failure.

## Remaining OPEN findings

- RCA-SLD-AUTH-001 — complete canonical authority closure.
- RCA-003 — complete ApplicationResult consumer boundary.
- RCA-004 — complete ReadModel/event/projection closure.
- RCA-005 — terminal/connection/topology authority.
- RCA-007 — complete tool registry/palette activation.
- RCA-008 — complete SLD canvas interaction workflow.
- RCA-009 — Controller/UI-Core adapter boundary.
- RCA-013 — identity/registry/lifecycle closure.
- RCA-UI-LIFECYCLE-002 — dirty shutdown decision resolution.
- RCA-UI-CANVAS-QT-001 — Qt diagnostic source evidence.
- RCA-SLD-INTERACTION-001 — contextual/terminal interaction.
- RCA-CONTROL-001 — control/ladder command integration.
- RCA-016 — transformer engineering-value full consumer path.
- RCA-017 — equipment catalogue/tool activation full consumer/path audit.
- Generic multi-terminal identity closure.

## Disposition

Remediated — Verification Deferred:
- SLD projection ownership collision during equipment_id reconciliation.
- stale projection cleanup that could erase engineer-owned attached connections.
- loss of engineering parameters during SLD ReadModel adaptation.

Open:
- all findings listed above that require broader end-to-end source proof or runtime evidence.

## Compliance confirmation

- No tests run.
- No pytest run.
- No CI run.
- No runtime verification performed.
- No Core mutation authority moved into SLD/UI.
- No parallel SLD synchronization architecture introduced.
- Existing SLDReadAdapter → SLDProjectionManager → SLDReadSynchronizer path preserved.
- BusItem and LineItem were not changed.
- No generic Port abstraction introduced.
