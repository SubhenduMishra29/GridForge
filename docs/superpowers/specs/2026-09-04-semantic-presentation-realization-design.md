# Semantic Presentation Realization Design

**Date:** 2026-09-04  
**Status:** Design approved in chat; implementation not yet started

## 1. Purpose

GridForge's live SLD pipeline already preserves the Application semantic `element_type` through `SLDNode` and `SLDCanvasNode`, and the canvas render system already owns transient graphics synchronization and lifecycle. The remaining architectural gap is the boundary that determines which presentation representation is appropriate for an SLD node before concrete graphics construction.

This design introduces only that missing responsibility. It does not redesign the Core/Application model, SLD projection, Canvas projection, graphics items, equipment subsystem, symbol subsystem, or generic renderer infrastructure.

## 2. Authoritative architecture alignment

The design preserves the authoritative flow:

```text
Presentation / Interaction
        ↓
Commands / Application Services
        ↓
Authoritative Core Domain
        ↓
Results / Events / DTOs / Read Models
        ↓
Projection
```

For SLD rendering the relevant presentation flow becomes:

```text
Application Read Model
        ↓
SLDReadSynchronizer
        ↓
SLDNode
        ↓
SLDCanvasProjection
        ↓
SLDCanvasNode
        ↓
Semantic Presentation Realization
        ↓
SLDGraphicsItemFactory
        ↓
QGraphicsItem
```

The Core remains the sole owner of electrical truth. No new semantic truth is created in the presentation layer.

## 3. Responsibilities and ownership

### SLDCanvasRenderSystem

Remains responsible for:

- snapshot synchronization;
- render lifecycle;
- scene ownership;
- endpoint resolution for connections;
- rendering orchestration;
- invoking semantic realization and concrete construction.

It must not become the owner of the semantic mapping table.

### Semantic Presentation Realization

Owns exactly one responsibility:

> Interpret the semantic information already present on `SLDCanvasNode` and determine the valid presentation representation for that node.

It:

- accepts `SLDCanvasNode` as its complete input;
- reads `SLDCanvasNode.properties["element_type"]`;
- selects the appropriate presentation representation;
- validates that the representation exists;
- returns renderer-neutral presentation-selection information;
- fails explicitly for unsupported semantic types.

It must not:

- access Core objects;
- access Application services;
- mutate semantic state;
- perform electrical calculations;
- resolve topology;
- own SLD document state;
- own Canvas scene state;
- create `QGraphicsItem` objects;
- create or require `EquipmentBase` instances;
- create or require `SymbolBase` instances;
- consult `EquipmentRegistry` or `SymbolRegistry` unless a later architectural proof establishes such a dependency;
- revive the legacy generic renderer registry.

### SLDGraphicsItemFactory

Remains a concrete construction boundary.

It receives the renderer-neutral presentation information required for construction and creates the appropriate presentation graphics item. It does not become the semantic resolver.

### BusItem / LineItem

Remain unchanged and presentation-only.

## 4. Input contract

The semantic realization boundary receives exactly:

```text
SLDCanvasNode
```

The semantic selector obtains semantic identity only from:

```text
SLDCanvasNode.properties["element_type"]
```

No additional `graphics_type`, `symbol_type`, or duplicate semantic field is introduced.

## 5. Output contract

The result is the minimum renderer-neutral presentation-selection information necessary for the concrete construction boundary to determine the appropriate construction path.

The result is explicitly **not**:

- the original `element_type` itself;
- `node_id` or `equipment_id`;
- geometry;
- electrical state;
- a Core/Application object;
- an `EquipmentBase`;
- a `SymbolBase`;
- a renderer instance;
- a `QGraphicsItem`;
- a `QGraphicsScene`;
- a new independent identity.

The concrete representation of this selection is intentionally not frozen by this design. Implementation must first determine the smallest suitable existing or new value representation without prematurely introducing a broad vocabulary or descriptor hierarchy.

## 6. Failure contract

Known semantic type:

```text
SLDCanvasNode
    ↓
valid presentation selection
    ↓
SLDGraphicsItemFactory
```

Unsupported or unknown semantic type:

```text
SLDCanvasNode
    ↓
explicit realization failure
```

There is no fallback from an unknown type to `BusItem`.

## 7. Connection realization

This change does not redesign connection realization.

The established path remains:

```text
SLDCanvasConnection
        ↓
SLDGraphicsItemFactory
        ↓
LineItem
```

Any future terminal/port geometry work is a separate audit item and must not be smuggled into this semantic realization change.

## 8. Equipment and Symbol subsystems

This design deliberately does not assert any unproven equivalence between:

```text
ElementReadModel.element_type
EquipmentDefinition.equipment_type
SymbolDefinition.symbol_id
SymbolDefinition.renderer_id
```

Nor does it establish an implicit runtime chain through `EquipmentRegistry`, `EquipmentFactory`, `SymbolRegistry`, `SymbolFactory`, `EquipmentBase`, or `SymbolBase`.

Those subsystems remain available architectural concepts but are not made dependencies merely to fill the current gap.

## 9. Generic renderer infrastructure

The current SLD design explicitly keeps the SLD render path separate from a generic renderer registry. This design therefore does not introduce or reconnect a generic `RendererRegistry` for SLD semantic realization.

`renderer_id` in symbol metadata is not treated as a live realization contract without executable evidence establishing that relationship.

## 10. Compatibility invariants

The implementation must preserve all of the following:

1. Core has no dependency on UI presentation realization.
2. Application remains the mutation boundary.
3. `SLDCanvasProjection` remains a projection boundary.
4. `SLDCanvasRenderSystem` remains canonical for SLD canvas synchronization and lifecycle.
5. `SLDGraphicsItemFactory` remains construction-focused.
6. `BusItem` remains locked and presentation-only.
7. `LineItem` remains locked and presentation-only.
8. No duplicate semantic field is introduced.
9. Unknown semantic types fail explicitly.
10. No electrical truth is moved into presentation code.

## 11. Testing contract

Before implementation is considered complete, tests must establish at minimum:

- a known semantic `element_type` produces the expected presentation selection;
- unsupported `element_type` values fail explicitly;
- the realization boundary does not require Core/Application objects;
- the render system invokes realization before concrete construction;
- the factory remains responsible for concrete item construction;
- BusItem and LineItem remain presentation-only;
- no unknown semantic type silently produces BusItem;
- existing SLD projection and canvas projection contracts remain intact.

Runtime test execution must be reported separately from structural repository verification.

## 12. Non-goals

This change does not:

- redesign the Core electrical model;
- redesign Application commands/services;
- change `CreateBusCommand` or the corrected Bus contract;
- change CanvasComposition;
- change SLDCanvasProjection;
- modify BusItem;
- modify LineItem;
- replace SLDCanvasRenderSystem;
- create a generic renderer registry;
- make EquipmentRegistry or SymbolRegistry authoritative;
- introduce an EquipmentBase or SymbolBase bridge;
- redesign topology or connection routing;
- implement full equipment symbol catalogues.

## 13. Decision

The repository has a genuine unowned semantic-selection responsibility. Existing types do not provide a proven value for that responsibility without crossing an existing boundary. The architecture therefore adds a **minimal semantic presentation realization boundary**, while deliberately leaving the concrete representation of its selection result to the implementation step.

The next implementation phase must follow TDD and must not broaden this contract without a new architecture review.
