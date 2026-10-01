# ============================================================
# GridForge V2 — GF-MASTER-0040 Static Closure
# Author: Subhendu Mishra
# ============================================================

## Authority

- Implementation repository: `pandaraseswari03-collab/GridForge`
- Branch: `main`
- Audit/register authority: `SubhenduMishra29/GridForge`
- Verification mode: static source inspection and source correction only.
- Runtime, pytest, CI, and `python main.py` execution were not performed.

## 1. Finding

GF-MASTER-0040 covered the SLD projection/rendering boundary, generic equipment realization, scene authority, connection independence, and historical factory/rendering failures.

The current source already contained the canonical Canvas scene, SLDCanvasProjection, SemanticPresentationRealization, SLDGraphicsItemFactory, and SLDCanvasRenderSystem. Static reconciliation identified two remaining structural weaknesses in that path:

1. `SLDGraphicsItemFactory` queried the Application read facade during graphics realization, allowing the renderer/factory to bypass the already-projected SLD node state.
2. `SLDCanvasRenderSystem` retained a degraded fallback under the same render signature and therefore could skip a later retry even when a subsequent projection reconciliation made the presentation resolvable.
3. `SLDController` could silently construct a second `SLDProjectionManager` when not explicitly injected, weakening the single projection-authority invariant.

## 2. Corrections

### A — Graphics factory is downstream-only

Changed `ui/canvas/sld_graphics_item_factory.py`:

- removed retained Application access from the factory;
- retained only the canonical EquipmentRegistry, SymbolRegistry, and EquipmentFactory dependencies;
- changed node read-side enrichment to derive solely from the projected `SLDCanvasNode`;
- preserved stable equipment identity, element type, labels, attributes, and terminal-role presentation data from the SLD node;
- retained the optional legacy constructor argument only for source compatibility and deliberately ignores it.

Result:

`Application/Core -> read/projection boundary -> SLD node -> graphics factory`

No renderer-side Application read query remains.

### B — Degraded node realization is retryable

Changed `ui/canvas/sld_canvas_render_system.py`:

- added explicit `_degraded_node_ids` state;
- a degraded node is no longer accepted by the render-signature fast path;
- every later canonical synchronization retries presentation realization for degraded nodes;
- successful realization clears the degraded marker;
- removal/clear lifecycle also clears degraded markers.

This preserves the existing controlled diagnostic fallback while preventing a temporary presentation failure from becoming a permanent visual state.

### C — One projection manager

Changed `ui/sld/sld_controller.py`:

- removed implicit construction of `SLDProjectionManager`;
- the controller now requires the canonical manager to be injected by composition;
- `main.py` already composes one manager and passes that same instance to `SLDReadSynchronizer` and `SLDController`.

No second projection authority is therefore created by the controller fallback path.

## 3. Final static projection/realization chain

```
Core electrical truth
  -> Application read model / semantic event
  -> SLDReadAdapter
  -> SLDProjection / canonical SLDProjectionManager
  -> Application-authoritative SLDDocument / SLDModel
  -> SLDCanvasProjection
  -> immutable SLDCanvasSnapshot
  -> SemanticPresentationRealization
  -> canonical EquipmentRegistry + SymbolRegistry/SymbolFactory
  -> SLDGraphicsItemFactory
  -> canonical SLDCanvasRenderSystem
  -> one GridScene/QGraphicsScene
  -> EquipmentItem / BusItem / SLDConnectionItem
```

The reverse mutation boundary remains Application-command based; the renderer and graphics items do not mutate Core.

## 4. Equipment coverage

Static catalogue and symbol catalogue reconciliation covers:

- Bus
- Transformer
- Switch
- Breaker
- Disconnector
- Fuse
- Line
- Cable
- Load
- Generator
- Motor
- Current Transformer (CT)
- Potential Transformer (PT)
- Capacitive Voltage Transformer (CVT)
- Relay

The broader built-in catalogue also contains Synchronous Machine, Shunt, Capacitor, Reactor, Solar, Battery, and Grid. All use the same semantic-definition-symbol realization path, with Bus retaining its existing specialized presentation item.

No equipment-specific bypass was added to the generic renderer.

## 5. Connection independence

Static inspection of `SLDCanvasRenderSystem.synchronize()` confirms:

- nodes are reconciled before connections;
- desired node and connection IDs are reconciled independently;
- connection failures produce `RenderDiagnostic` / unsupported-connection state;
- failed connection realization does not call node removal;
- wire activation is not part of renderer node deletion;
- scene removal is limited to realized IDs absent from the current immutable snapshot.

Batch 28 movement/snap lifecycle and Batch 39 endpoint/topology authority remain presentation companions around Core/Application authority.

## 6. Symbol and equipment authority

One canonical:

- `EquipmentRegistry`
- `SymbolRegistry`
- `SymbolFactory`
- `EquipmentDefinition`
- `SymbolDefinition`
- `SemanticPresentationRealization`
- `SLDGraphicsItemFactory`
- `SLDCanvasRenderSystem`

is composed by `PresentationBootstrap`.

The factory and renderer do not create a second registry or semantic mapping.

## 7. Scene authority

Static composition confirms the same prepared scene is supplied to:

```
CanvasComposition.scene
GraphicsView.scene()
SnapSystem
SLDCanvasRenderSystem
PreviewLayer
```

`SLDSurface` is only a compatibility adapter around the canonical `SLDCanvasSurface`; it does not create a second scene, projection, renderer, or document.

## 8. Persistence and lifecycle

`SLDDocument` / `SLDModel` persist serializable presentation state only. Qt scene/item objects, renderer instances, SnapSystem runtime state, and preview objects are not persisted.

Project close clears projection state and canonical renderer state through the existing lifecycle/event path. Project load/new/open reuse the same Application-authoritative SLD document and canonical canvas realization path.

## 9. Duplicate/obsolete infrastructure

Static tree inspection found one production implementation for each of:

- `SLDReadAdapter`
- `SLDProjection`
- `SLDProjectionManager`
- `SLDReadSynchronizer`
- `SLDCanvasProjection`
- `SLDCanvasRenderSystem`
- `SemanticPresentationRealization`
- `SLDGraphicsItemFactory`
- `EquipmentRegistry`
- `SymbolRegistry`

`SLDSurface` is explicitly retained as a compatibility adapter and delegates to the canonical `SLDCanvasSurface`.

The only remaining constructor path that could manufacture a second projection manager was removed from `SLDController`.

Preview graphics remain a legitimate transient layer on the same canonical scene and are not a second canvas authority.

## 10. Files changed

- `ui/canvas/sld_graphics_item_factory.py`
- `ui/bootstrap/presentation_bootstrap.py`
- `ui/canvas/sld_canvas_render_system.py`
- `ui/sld/sld_controller.py`
- `audit/GF_MASTER_0040_SLD_PROJECTION_CANVAS_REALIZATION_STATIC_CLOSURE_2026-10-01.md`
- `audit/MASTER_AUDIT_REGISTER.md`
- `audit/MASTER_AUDIT_REGISTER.csv`

## 11. Batch regression check

### Batch 28

Preserved:

- canonical SnapSystem;
- EndpointIdentityAdapter / EndpointReference path;
- equipment movement refresh;
- generic symbol realization;
- independent connection realization;
- no connection-failure deletion of equipment nodes;
- one canonical canvas scene.

### Batch 39

Preserved:

- Core Network/topology authority;
- Application connection orchestration;
- SLD connection as presentation companion;
- terminal endpoint identity;
- no UI/renderer topology authority.

## 12. Static acceptance

The requested GF-MASTER-0040 structural conditions are statically satisfied by the current source after the corrections above.

No runtime claim is made.

## 13. Register status

**GF-MASTER-0040 — STATICALLY VERIFIED — CLOSED**

Runtime verification remains a separate engineering activity and was not performed in this correction pass.

## 14. Implementation commit

`b7a4e20989af7736760bab1da05318e417b66fdc`
