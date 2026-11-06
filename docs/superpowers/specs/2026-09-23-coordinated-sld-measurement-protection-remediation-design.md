# GridForge V2 — Coordinated SLD, Measurement, Protection, and LineTool Remediation Design

**Date:** 2026-09-23  
**Repository:** `madhuri196mishra-cpu/GridForge`  
**Branch:** `main`  
**Author/header:** Subhendu Mishra  
**Verification boundary:** Static inspection and static re-audit only. Tests, CI, startup, GUI execution, and runtime smoke verification are prohibited.

## 1. Purpose

Remediate the coordinated residual findings without weakening the frozen architecture or reopening already-corrected adjacent components. All changes follow this RCA chain:

> observed defect → contract violation → call/data flow → ownership boundary → root cause → minimal correction → dependency chain → static re-audit

## 2. Non-negotiable architecture

- Core owns electrical equipment, authoritative Core `Terminal` objects, topology, measurement, protection, studies, and results.
- Application is the sole UI-to-Core mutation boundary.
- UI, SLD, tools, renderers, and plugins remain presentation/interaction layers.
- The canonical semantic endpoint identity is `EndpointReference(equipment_type, equipment_id, terminal_role)`.
- `EquipmentTerminal.terminal_id` is UI/document identity only and must not become a second semantic identity authority.
- Terminal roles are explicit metadata; they are never inferred from geometry, index, or ordering.
- No `ProtectionTerminal` or `MeasurementTerminal` abstraction is introduced.
- No second topology, connection, equipment, or terminal identity authority is introduced.

## 3. Workstream A — Baseline and dependency map

1. Establish the current HEAD and inspect only the modules participating in the five findings.
2. Map imports, constructors, registration, call sites, and identity flow before editing.
3. Mark already-corrected components as protected unless the dependency trace proves a direct contract violation.
4. Record unresolved uncertainty explicitly rather than filling gaps with assumptions.

Expected evidence: module-to-module dependency map and a list of files requiring changes, with unchanged adjacent components identified.

## 4. Workstream B — Bus/Snap/Endpoint identity

### 4.1 Bus presentation snap contract

Add the smallest presentation-level snap-candidate method required by the existing snap system to `BusItem`. The method may expose the bus's graphical anchor/connection point, but it must not create or mutate Core topology or electrical terminals.

### 4.2 Terminal-aware snap candidates

Reconcile `SnapSystem` normalization and `SnapResult` construction so candidates preserve explicit terminal metadata when supplied:

- object identity;
- source item;
- terminal UI/document identifier, where available;
- explicit terminal role/name, where available;
- snap type and position.

The implementation must not derive a terminal role from a point's position, candidate index, geometry, or ordering.

### 4.3 Canonical endpoint identity

Use the existing `EndpointIdentityAdapter` and `EndpointReference` factory contract as the sole conversion boundary:

- bus object snap → `EndpointReference.bus(equipment_id)`;
- explicit equipment terminal snap → `EndpointReference.terminal(equipment_type, equipment_id, terminal_role)`.

Remove or centralize any duplicate CT/PT/CVT alias conversion that creates a competing semantic mapping. Reuse canonical enum/type normalization already present in the repository rather than adding another map.

The adapter must reject incomplete or ambiguous terminal information instead of guessing.

### 4.4 Required static evidence

Trace both paths completely:

- `BusItem → SnapSystem → SnapResult → EndpointIdentityAdapter → EndpointReference.bus()`
- `SymbolDefinition → EquipmentDefinition → EquipmentTerminal → EquipmentItem.snap_points() → SnapResult → EndpointReference.terminal()`

## 5. Workstream C — Measurement provisioning

Introduce only the smallest dedicated provisioning boundary needed to create measurement channels from physical instrument terminals. The boundary must:

- consume explicit `EndpointReference` source-terminal identity;
- resolve the referenced authoritative Core terminal;
- provision CT/PT/CVT secondary channels without creating duplicate terminal abstractions;
- preserve source-terminal identity through the resulting `MeasurementChannel`;
- avoid any dependency from Core measurement generation into UI modules.

CT/PT/CVT secondary terminals remain authoritative Core `Terminal` objects. The provisioning boundary may orchestrate creation/registration, but it must not become a second source of terminal truth.

Static checks must verify constructor signatures, setter/update paths, registration maps, and duplicate-key behavior for CT/PT/CVT channels.

## 6. Workstream D — Protection integration

Preserve the following chain:

> physical instrument → `MeasurementChannel` → `RelayInput` → `ProtectionElement`

`ProtectionMeasurementBinding` must retain explicit source-terminal identity through `EndpointReference`. Binding logic must not infer identity from a channel name, index, geometry, or object ordering.

`ProtectionRuntime` remains a protection-composition/runtime boundary. It must not generate measurement channels or become the measurement provisioning service.

Static evidence must trace:

> physical terminal → `EndpointReference` → measurement provisioning → `MeasurementChannel` → `RelayInput` → `ProtectionElement` → `ProtectionSystem` → `ProtectionDecision`

## 7. Workstream E — LineTool reconciliation

Determine the actual current role from implementation and call sites before changing behavior.

- If `LineTool` creates real Core Line equipment, it must emit an immutable Application command and use `Application.execute()`/`CommandManager`/handler-service flow.
- If it represents unrestricted graphical wiring, it must be explicitly separated from Core electrical Line equipment and must not mutate or impersonate Core topology.
- No second connection or topology authority may be introduced.

Static evidence must trace the concrete tool path:

> Tool → immutable Command → `Application.execute()` → `CommandManager` → handler/service → Core → semantic event → ReadModel → SLD projection

## 8. Workstream F — Master audit register

Update the existing master register only. Do not create a parallel register. Update the applicable entries for:

- `GF-SLD-TERM-020`, `GF-SLD-TERM-021`, `GF-SLD-TERM-023`–`GF-SLD-TERM-028`;
- `GF-SLD-SNAP-022`;
- `RCA-SLD-CONN-002`;
- `GF-MASTER-0067`;
- `GF-PROT-035`–`GF-PROT-040`, `GF-PROT-042`;
- `GF-SLD-WF-TOOL-006`.

Each entry must distinguish:

1. root cause;
2. affected modules;
3. architectural impact;
4. remediation;
5. static verification status;
6. runtime verification status.

Runtime status must remain explicitly `UNVERIFIED / DEFERRED`.

## 9. Workstream G — Static integrity re-audit

After edits, perform a static-only re-audit of all five workstreams. Verify:

- no forbidden UI-to-Core mutation path;
- no duplicate semantic/equipment/terminal identity mapping;
- no terminal-role inference from geometry, index, or ordering;
- no duplicate CT/PT/CVT provisioning map;
- consistent `MeasurementChannel` construction and updates;
- explicit provisioning boundary;
- independent secondary Core terminals;
- `RelayInput` consumes `MeasurementChannel`;
- binding retains `EndpointReference` source identity;
- `ProtectionRuntime` does not generate measurements;
- concrete tools use immutable commands and Application execution;
- LineTool role is explicitly reconciled;
- master register is updated;
- runtime verification remains deferred.

## 10. Verification reporting

Final reporting must use separate labels:

- **STATICALLY VERIFIED:** supported by source inspection, call-graph tracing, contract checks, registration checks, and dependency composition review.
- **RUNTIME VERIFICATION DEFERRED:** tests, CI, startup, GUI execution, and runtime smoke checks were not performed by design.

No finding may be called closed solely because a static edit was made; closure language requires the complete dependency chain to be statically traced.
