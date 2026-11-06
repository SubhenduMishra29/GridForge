# GridForge V2 — Batch 28 Static Correction Report

**Author:** Subhendu Mishra  
**Implementation authority:** `madhuri196mishra-cpu/GridForge:main`  
**Audit/reference authority:** `SubhenduMishra29/GridForge:main`  
**Mode:** Static source inspection and implementation correction only  
**Runtime:** Not run; runtime verification remains deferred.

## Finding

Canonical SLD terminal snapping was present only as a scene-scanning service and was not explicitly bound to the active SLD renderer lifecycle. WireTool also relied on fragile enum-name checks.

## Correction

The existing single `ui/core/snap_system.py` is now the canonical presentation snap service. It owns a presentation candidate registry populated by the active `SLDCanvasRenderSystem`.

- `EquipmentItem.snap_points()` exposes symbol-definition terminal anchors with equipment/terminal identity.
- `BusItem.snap_points()` exposes canonical bus attachment identities (`bus_id` + `attachment_id`) without manufacturing terminals.
- `SLDCanvasRenderSystem` registers realized equipment/bus items with the same `SnapSystem` used by `ToolManager/WireTool`.
- Node removal and renderer clear unregister candidates; scene replacement clears stale registrations.
- Anchor coordinates are read from the live realized item at snap time, so movement does not leave copied/stale snap geometry.
- `WireTool` and `EndpointIdentityAdapter` compare the typed `SnapType.OBJECT` enum directly.
- `main.py` composes one `SnapSystem` into the active SLD renderer; `CanvasComposer` rejects a different snap service.
- No Core mutation, history ownership, graphics-object persistence, or parallel wire command was introduced.

## Static lifecycle trace

```
SLDCanvasSurface
  -> SLDCanvasProjection
  -> SLDCanvasRenderSystem
  -> EquipmentItem / BusItem
  -> SnapSystem.register_item()
  -> SnapSystem.snap()
  -> SnapResult(SnapType.OBJECT, terminal/bus identity)
  -> EndpointIdentityAdapter
  -> EndpointReference
  -> CreateSimpleWireConnectionCommand
  -> ToolBase.execute_command()
  -> Application.execute()
```

Committed connection rendering remains independent from equipment realization: nodes are reconciled first, connection failures are diagnostic-only, and renderer removal is keyed by the desired snapshot IDs.

## Status

**AGENT CORRECTED — RE-AUDIT REQUIRED**

This correction does not claim runtime verification or final static closure. The separately designated audit repository was not modified.
