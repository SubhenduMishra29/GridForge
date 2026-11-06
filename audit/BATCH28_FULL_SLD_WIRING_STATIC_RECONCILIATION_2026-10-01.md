# GridForge V2 — Batch 28 Full SLD Wiring Static Reconciliation

**Author:** Subhendu Mishra  
**Implementation authority:** `madhuri196mishra-cpu/GridForge:main`  
**Audit/reference authority:** `SubhenduMishra29/GridForge:main`  
**Audited baseline:** `4f8ccbd6421b0ba97944ff36444a6936f1d87b20`  
**Mode:** Static repository inspection and source correction only  
**Runtime / CI:** Not run

## 1. Existing implementation retained

The correction preserves the existing Batch 28 architecture:

- one canonical `ui/core/snap_system.py`;
- immutable `SnapResult` and typed `SnapType`;
- renderer-owned registration of realized `EquipmentItem` and `BusItem`;
- canonical `EndpointIdentityAdapter`;
- `WireTool` as the sole SLD simple-wire interaction tool;
- `CreateSimpleWireConnectionCommand` / `RemoveSimpleWireConnectionCommand`;
- `SimpleWireConnectionService`;
- Application `_coordinate_connection_pre_commit()`;
- persistent `SLDConnection`;
- `SLDConnectionItem`;
- `SLDUpdateCoordinator` and semantic topology/network events.

No parallel SnapSystem, connection command, topology authority, renderer, or SLD connection model was introduced.

## 2. Remaining static defects corrected

### B28-WIRE-001 — movement refresh lifecycle

The canonical SnapSystem candidate registry already reads live anchor geometry at snap time, but equipment movement did not explicitly emit the renderer-owned refresh lifecycle required by Batch 28.

Correction:

- `EquipmentItem` now emits `position_changed` for Qt position changes;
- `EquipmentItem` enables `ItemSendsGeometryChanges`;
- `SnapSystem.register_item()` subscribes to an item's `position_changed` signal when available;
- movement invokes canonical `SnapSystem.refresh_item()`;
- unregister and scene replacement disconnect movement callbacks;
- project/scene cleanup clears both candidates and callback registrations.

No second coordinate database was added.

### B28-WIRE-002 — endpoint realization identity hardening

`SLDEndpointResolver` previously matched equipment endpoints by terminal role and bus endpoints by attachment ID after locating the node by `node_id`.

Correction:

- equipment resolution now verifies realized `object_id == equipment_id`;
- each matched equipment snap candidate must also carry the same equipment object identity;
- bus resolution now verifies realized `object_id == bus_id`;
- each matched bus candidate must carry the same bus identity and attachment identity.

Endpoint geometry remains sourced exclusively from the live realized item's canonical `snap_points()`.

## 3. Complete static wiring chain

```
GraphicsView viewport event
  -> MouseEventAdapter.scene_position
  -> InteractionManager
  -> ToolManager
  -> WireTool
  -> SnapSystem.snap()
  -> SnapResult(SnapType.OBJECT)
  -> EndpointIdentityAdapter
  -> EndpointReference
  -> CreateSimpleWireConnectionCommand
  -> ToolBase.execute_command()
  -> Application.execute()
  -> CommandManager transaction
  -> SimpleWireConnectionService
  -> EndpointCompatibility / terminal resolution
  -> Core Network SimpleWireConnection
  -> Application._coordinate_connection_pre_commit()
  -> SLDService AddSLDConnectionCommand
  -> transaction commit
  -> SimpleWireConnectionCreated
  -> TopologyChanged / NetworkChanged
  -> UIUpdateBoundary / UIProjectionCoordinator
  -> SLDUpdateCoordinator
  -> SLDCanvasProjection
  -> SLDCanvasRenderSystem
  -> SLDEndpointResolver
  -> SLDGraphicsItemFactory
  -> SLDConnectionItem
  -> visible persistent connection
```

WireTool does not call Core or SLDService directly and does not create persistent graphics.

## 4. Snap and endpoint identity

Equipment snap candidates originate from:

`Equipment terminals -> SymbolDefinition.terminal_anchors -> EquipmentItem.snap_points() -> scene coordinates`.

Bus candidates originate from deterministic `BusItem.snap_points()` attachment identities.

The adapter preserves the distinction between:

- equipment identity;
- terminal presentation identity;
- terminal engineering role;
- bus identity;
- bus attachment identity;
- canonical `EndpointReference`.

No Bus endpoint is converted into a manufactured equipment terminal.

## 5. Atomicity and failure isolation

`CommandManager._execute_command()` invokes the handler and Application pre-commit hook while the transaction remains open.

If endpoint validation, Core mutation, SLD companion creation, or any pre-commit coordination step raises, the transaction rollback journal is executed and no history record is created.

The Core Simple Wire service registers the inverse network mutation. `SLDService._add_connection()` registers the inverse SLD connection mutation in the same transaction.

Therefore the static failure contract is:

```
Core Simple Wire: absent
SLD Connection: absent
equipment nodes: unchanged
history: unchanged
preview: retained by WireTool
```

Post-commit render failure is intentionally presentation-only: the persisted SLD connection and Core state remain authoritative and a `RenderDiagnostic` is emitted.

## 6. Rendering and node independence

`SLDCanvasRenderSystem.synchronize()`:

1. computes desired node and connection IDs independently;
2. removes only realized IDs absent from the immutable snapshot;
3. realizes equipment/bus nodes before connections;
4. registers only canonical electrical graphics as snap candidates;
5. resolves connection endpoints through `SLDEndpointResolver`;
6. creates `SLDConnectionItem` only as presentation state;
7. records connection failures as `RenderDiagnostic` without deleting endpoint nodes.

Degraded diagnostic rectangles are not registered as electrical snap candidates.

`SLDConnectionItem` is not a snap candidate.

## 7. Undo / redo

The canonical reversible commands preserve the same `connection_id` and endpoint snapshots.

Undo removes the Core Simple Wire and the Application-coordinated persistent SLD companion through the same transaction boundary while leaving equipment nodes intact.

Redo re-executes the original immutable create command, preserving endpoint identity and connection identity; event-driven reconciliation re-realizes the presentation connection.

## 8. Persistence

`SLDConnection.to_dict()` persists:

- connection identity;
- source/target SLD node identity;
- equipment endpoint identity or bus attachment identity;
- route mode/ownership/points;
- presentation properties.

`SLDDocument.from_dict()` reconstructs the logical SLD model. Qt scene/item objects and SnapSystem state are not persisted.

## 9. Scene and project lifecycle

Static composition confirms:

```
CanvasComposition.scene
== GraphicsView.scene()
== SnapSystem.scene
== SLDCanvasRenderSystem.scene
```

ToolManager receives the same SnapSystem and PreviewLayer created by CanvasComposer.

Project-close refresh clears the SLD projection/document presentation through the existing CanvasPlugin synchronization path; renderer cleanup unregisters snap candidates and SnapSystem clears its callback/candidate state.

## 10. Duplicate/dead infrastructure

Repository tree inspection found:

- one `ui/core/snap_system.py`;
- one `SnapResult` implementation in that canonical module;
- no `CreateWireCommand`, `CreateSLDWireCommand`, or `CanvasWireCommand` duplicate;
- `ui/tools/sld_connection_presentation_adapter.py` remains explicitly retired and rejects execution rather than participating in the active path;
- `core/application/commands/connection_commands.py` contains terminal attach/reconnect commands, not a duplicate Simple Wire command.

## 11. Representative symbol coverage

The existing Batch 28 static equipment catalogue covers the registered SLD symbol families including Transformer, Switch/Breaker/Disconnector, Line/Cable, Load, Generator, Motor, CT, PT/CVT, Relay, and Bus. Their terminal anchors are consumed through the canonical SymbolDefinition/EquipmentItem path rather than a second coordinate registry.

## 12. Static acceptance result

The Batch 28 wiring architecture is **STATICALLY VERIFIED — CLOSED** at the source level.

Runtime GUI verification, manual save/reload, interactive snapping, and CI/test execution remain outside this audit and were not performed.

## 13. Implementation changes in this reconciliation

- `ui/items/equipment_item.py`
  - added position-change signal emission for movement lifecycle;
- `ui/core/snap_system.py`
  - added movement callback registration/disconnection and scene-transition cleanup;
- `ui/sld/sld_endpoint_resolver.py`
  - hardened equipment/bus identity checks during presentation endpoint resolution;
- this audit report records the final static reconciliation.

## 14. Register recommendation

- `GF-MASTER-0114`: **STATICALLY VERIFIED — CLOSED**;
- preserve `GF-MASTER-0113` as **REMEDIATED — RUNTIME VERIFICATION DEFERRED**;
- Batch 28 runtime verification remains deferred and must not be represented as executed.
