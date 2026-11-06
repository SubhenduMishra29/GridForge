# SLD Graphics Item Factory Design

**Author:** Subhendu Mishra

## Goal
Introduce a focused SLD graphics-item construction boundary without changing the locked `BusItem` or `LineItem` classes or moving electrical responsibility into presentation code.

## Architecture
`SLDCanvasRenderSystem` remains responsible for snapshot synchronization, lifecycle, scene ownership, and rendering orchestration. `SLDGraphicsItemFactory` owns only the mapping from renderer-neutral SLD presentation descriptors to Qt graphics projection instances. The factory consumes `SLDCanvasNode` / `SLDCanvasConnection` data and returns `BusItem` / `LineItem`; it has no Core, Application, topology, layout, or command responsibilities.

## Invariants
- `BusItem` remains unchanged and locked.
- `LineItem` remains unchanged and locked.
- `SLDCanvasProjection` remains unchanged.
- `SLDCanvasRenderSystem` remains the canonical renderer.
- No `SLDSceneRenderer` is introduced.
- No generic renderer registry is introduced.
- Factory construction must be deterministic and presentation-only.
- Unknown descriptors must fail explicitly rather than silently selecting a fallback item.
- Existing pen/radius presentation configuration remains owned by the render system.

## Proposed interface
- `SLDGraphicsItemFactory.create_node(node: SLDCanvasNode) -> BusItem`
- `SLDGraphicsItemFactory.create_connection(connection: SLDCanvasConnection, source: QPointF, target: QPointF) -> LineItem`

The factory creates the graphics item only. Styling remains in `SLDCanvasRenderSystem` so visual policy is not duplicated.

## Integration
`SLDCanvasRenderSystem.synchronize()` will resolve endpoint positions, ask the factory for each item, apply its existing visual pen configuration, add the item to the scene, and retain ownership for clearing/disposal.

## Testing
Tests will verify node and connection construction, invalid descriptor handling, and renderer integration while leaving the existing item implementations untouched.
