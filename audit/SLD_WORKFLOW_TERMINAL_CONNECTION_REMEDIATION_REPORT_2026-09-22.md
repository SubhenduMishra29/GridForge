# GridForge V2 — Consolidated SLD Workflow / Terminal / Connection Remediation Report

**Date:** 2026-09-22  
**Working repository:** `pandaraseswari03-collab/GridForge`  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Verification mode:** Static source remediation and static re-audit only.

## A. Findings addressed

Addressed in this remediation pass:

- RCA-SLD-AUTH-001
- RCA-UI-DOCUMENT-002
- RCA-UI-DOCUMENT-004
- RCA-UI-DOCUMENT-006
- RCA-UI-DOCUMENT-003 / RCA-UI-DOCUMENT-007
- RCA-UI-BOOTSTRAP-004
- RCA-UI-BOOTSTRAP-005
- RCA-UI-WORKSPACE-001
- RCA-SLD-AUTH-002
- RCA-SLD-PREVIEW-001
- RCA-SLD-CMD-001
- RCA-APP-VALIDATION-001
- RCA-APP-ENDPOINT-001
- RCA-SLD-CONN-001

The following remain deliberately open/source-pending:

- RCA-UI-BOOTSTRAP-003
- RCA-SLD-CONN-002
- RCA-SLD-INTERACTION-002
- RCA-APP-ID-001

## B. Files modified

- `main.py`
- `core/application/application.py`
- `core/application/bootstrap.py`
- `core/application/revision_service.py`
- `core/application/endpoint_resolver.py`
- `core/application/commands/__init__.py`
- `core/application/commands/connection_commands.py`
- `core/application/services/__init__.py`
- `core/application/services/sld_service.py`
- `core/application/services/electrical_connection_service.py`
- `ui/events/sld_update_coordinator.py`
- `ui/sld/sld_controller.py`
- `ui/sld/sld_read_synchronizer.py`
- `ui/plugins/plugin_context.py`
- `ui/canvas/preview_layer.py`
- `ui/tools/bus_tool.py`
- `ui/tools/default_tool_registry.py`
- `ui/workspace/workspace_realizer.py`
- `audit/MASTER_AUDIT_REGISTER.md`
- `audit/MASTER_AUDIT_REGISTER.csv`

All modified/new GridForge source files retain `Author: Subhendu Mishra`.

## C. Architectural changes

### SLD projection authority

`SLDUpdateCoordinator` now reuses `SLDReadSynchronizer.projection_manager`. No second projection manager is created.

Bootstrap projection construction no longer relies on replaying the initial ProjectLoaded event. `reconcile_current_state()` reconciles current authoritative Application read models after the projection coordinator and UI update boundary are ready.

### Presentation document authority

`SLDController` is downstream to `Application.presentation`. It cannot make an unrelated document authoritative.

`SLDService.bind_document()` already enforced the same Application presentation invariant; the controller now follows it explicitly.

On `ProjectClosed`, the SLD controller clears its active document state and registered presentation documents.

`PluginContext.active_presentation_document` provides a lifecycle-safe accessor. The existing `sld_document` field remains compatibility data and is not treated as the active-document authority.

### Authored SLD equipment references

When an engineer-authored `AddSLDNodeCommand` supplies `equipment_id`, `SLDService` validates that ID through Application network/protection read state.

Authored nodes are marked with presentation ownership metadata so projection reconciliation does not mistake them for generated projection nodes. Their node identity and geometry are preserved.

### Bus preview

`PreviewLayer.show_bus()` supplies transient bus-placement preview graphics. `BusTool` owns only transient interaction state and clears the preview on commit/cancel/reset/deactivation.

No Core object is created or mutated by the preview.

### Workspace realization

`WorkspaceRealizer.realize()` now retains the prior realized layout and attempts deterministic compensation if a later Qt realization operation fails. Restoration failure is surfaced rather than silently swallowed.

## D. Canonical electrical connection workflow

The previously unproven Application use case now exists statically as:

```
Application Command
    ↓
CommandManager
    ↓
Transaction
    ↓
ElectricalConnectionCommandHandlers
    ↓
ElectricalConnectionService
    ↓
EndpointReference
    ↓
EndpointResolver / resolve_terminal_reference
    ↓
Core Terminal
    ↓
Terminal.attach() / Terminal.detach()
    ↓
Network.invalidate_topology()
    ↓
Transaction undo journal
    ↓
Application semantic event
    ↓
TopologyChanged + NetworkChanged
    ↓
UIUpdateBoundary / UIProjectionCoordinator
    ↓
SLDUpdateCoordinator
    ↓
SLDReadSynchronizer
    ↓
SLDDocument / Canvas projection
```

Commands added:

- `model.connect_terminal`
- `model.disconnect_terminal`
- `model.reconnect_terminal`

The command handlers are registered in the existing single Application CommandManager at the composition root.

Reconnect mutates the existing Core Terminal association. It does not delete and recreate equipment.

Undo/rollback restores the previous terminal endpoint and invalidates Network topology again.

The Application revision service classifies all three commands as topology mutations.

### Remaining limitation

The Application use case is source-present, but no UI gesture has yet been claimed as a fully proven end-to-end caller of these new commands. Existing line/equipment creation paths remain separate use cases.

## E. Terminal identity

The canonical identity chain is:

```
Core Terminal.role
        ↓
Application EndpointReference(
    equipment_id,
    terminal_role
)
        ↓
Application terminal resolver
        ↓
SLD terminal presentation mapping
        ↓
presentation terminal / symbol anchor
        ↓
UI terminal identifier
```

The new connection use case resolves unconnected Core terminals without weakening the existing `EndpointResolver.resolve()` contract.

The UI `terminal_id` remains presentation-local. It is not used as the authoritative electrical identity.

### Still unresolved

Complete source proof is still missing for:

- Core Terminal → SLD terminal projection realization;
- symbol-anchor mapping for every supported multi-terminal equipment family;
- SnapResult → exact Core Terminal resolution;
- CT/PT/CVT multi-terminal snapping;
- complete terminal catalogue reconciliation.

## F. Register changes

The single master register was updated:

- `audit/MASTER_AUDIT_REGISTER.md`
- `audit/MASTER_AUDIT_REGISTER.csv`

New master entries:

- GF-MASTER-0057 through GF-MASTER-0074

Statuses include only the permitted static-remediation classifications. No runtime/test result was used as closure evidence.

## G. Residual findings

### OPEN — SOURCE EVIDENCE PENDING

- RCA-UI-BOOTSTRAP-003 — redundant startup project activation
- RCA-APP-ID-001 — historical measurement identity vocabulary / compatibility sweep

### OPEN — unresolved

- RCA-SLD-CONN-002 — complete terminal identity/realization/snapping chain
- RCA-SLD-INTERACTION-002 — concrete-tool duplicated interaction state
- Runtime-only behavior, Qt diagnostics, tests, CI, and GUI behavior remain outside static closure

No orphan/deletion policy was invented.

## H. Verification limitation

Static source remediation completed.  
Static self-review completed.  
Static re-audit completed.  
Tests/CI/runtime/GUI were not executed.  
Runtime verification remains deferred.

The remediation batch does not claim executable verification.
