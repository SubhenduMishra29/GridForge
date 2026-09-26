# GridForge V2 — Control Ladder Interaction Remediation Report

**Date:** 2026-09-26  
**Repository:** `madhuri196mishra-cpu/GridForge`  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Mode:** Static source correction and re-audit only

## Disposition

**REMEDIATED — VERIFICATION DEFERRED**

The Control/Ladder UI interaction boundary was corrected without redesigning the frozen Control Core, LogicEngine, ControlEngine, persistence model, or Application command architecture.

No tests, CI, application startup, or GUI/runtime execution were performed.

## Corrected workflow

### Placement

```text
Engineer
  -> Control workspace
  -> selected rung
  -> Control tool
  -> LadderGeometryPolicy
  -> semantic symbol preview
  -> AddControlComponent
  -> Application.execute()
  -> ControlApplicationService
  -> semantic event
  -> ControlUpdateCoordinator
  -> Control read model
  -> ControlCanvas
```

Placement now carries the actual `rung_id` and snapped `position`. The former fixed `rung-001` path was removed.

### Position authority

`ControlComponentReadModel.position` and `LadderRungReadModel.positions` are consumed directly by `ControlCanvas`. Position is no longer reconstructed from component tuple ordering.

### Port interaction

A presentation-only `ControlPortPresentation` identifies:

- component ID;
- port name;
- INPUT/OUTPUT direction;
- signal type;
- scene position.

The canvas renders visible ports on ladder symbols.

### Connection

```text
OUTPUT port
  -> transient preview
  -> INPUT port
  -> structural UI pre-validation
  -> ConnectControlSignals
  -> Application.execute()
```

No connection is persisted during preview. Application/Core remains authoritative for final validation.

### Disconnect

Rendered connections retain their authoritative endpoint tuple as presentation identity. Disconnect selection therefore targets a specific persisted connection rather than reconstructing one from two components or first ports.

### Selection

`selected_rung_id` is UI-only state held by `LadderInteraction`. Rung selection comes from actual canvas interaction or component containment. Rung toolbar actions no longer use `rungs[-1]`.

Component selection updates the Inspector from the Application read model. Rung selection is separately presented as rung state.

### Palette capability

The palette now distinguishes component-specific capability from generic command availability through:

`Application.supports_control_component(component_type)`

The Application Control service remains the factory/capability authority.

### Interlock and Action Binding

- **Logic Interlock** remains a ladder/LogicEngine component.
- **Control Interlock** is a configuration workflow.
- **Action Binding** is a configuration workflow and requires explicit logic-output selection.

No palette entry reaches `AddControlComponent` with `component_type=None`.

### Lifecycle and projection

`ControlUpdateCoordinator` is the authoritative UI projection path for Control semantic events. Project close clears the canvas and transient state without calling `read_control()` against a closed project. Workspace refresh delegates projection to the coordinator.

## Static call-site re-audit

The corrected Control paths were inspected for the required call-site families:

- `LadderInteraction.place`
- `LadderInteraction.preview`
- `ControlCanvas.project`
- `ControlToolPalette`
- `ControlToolRegistry`
- `ControlWorkspace`
- `ConnectControlSignals`
- `DisconnectControlSignals`
- `MoveLadderElement`
- `AddControlComponent`
- `RemoveControlComponent`
- `SetLadderRungEnabled`
- `MoveLadderRung`

The prohibited fallback patterns were not present in the corrected Control workspace/canvas paths:

- `rung_id="rung-001"`
- `model.rungs[-1]`
- `component_ids.index(component_id)`
- `source.outputs[0]`
- `target.inputs[0]`

The remaining Action Binding path was also corrected so that an engineer explicitly selects the source output rather than implicitly using `outputs[0]`.

## Modified source areas

- `ui/control/control_workspace.py`
- `ui/control/control_tool_palette.py`
- `ui/control/control_toolbar.py`
- `ui/control/control_inspector.py`
- `ui/control/ladder/ladder_interaction.py`
- `ui/control/ladder/ladder_geometry.py`
- `ui/canvas/control_canvas.py`
- `ui/items/control_items.py`
- `ui/events/control_update_coordinator.py`
- `core/application/application.py`
- `core/application/services/control_service.py`

All materially modified Python source files retain the required **Author: Subhendu Mishra** header convention.

## Register synchronization

Recorded:

- GF-CTRL-CON-001
- GF-CTRL-CON-002
- GF-CTRL-CON-003
- GF-CTRL-CON-004
- GF-CTRL-CON-010
- GF-CTRL-CON-011
- GF-CTRL-UI-004
- GF-CTRL-UI-008
- GF-CTRL-UI-010
- GF-CTRL-UI-011
- GF-CTRL-UI-013
- GF-CTRL-UI-014
- GF-CTRL-UI-015

All are recorded as **REMEDIATED — VERIFICATION DEFERRED**. Historical audit records were preserved.

## Final status

**STATICALLY VERIFIED**

The source now expresses the requested engineer-operable Control/Ladder workflow while preserving:

**Core authority → Application orchestration → immutable commands → semantic events → read models → UI projection.**

**RUNTIME VERIFICATION — DEFERRED.**
