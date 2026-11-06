# GridForge V2 — Connection Subsystem

## Purpose

`ui.connections` is the presentation/interaction subsystem for SLD connection
intent. It owns transient interaction state, presentation-terminal lookup,
structural UI validation, preview state, and renderer-neutral routing geometry.

It is **not** an electrical topology authority and it does not synchronize
Core objects directly.

## Authoritative V2 connection path

```text
SLD Tool
    ↓
SnapResult
    ↓
EndpointIdentityAdapter
    ↓
canonical EndpointReference
    ↓
immutable Application Command
    ↓
Application.execute()
    ↓
Application CommandManager
    ↓
Application Service
    ↓
Core Network / Topology
    ↓
semantic event
    ↓
Application ReadModel / SLD projection
    ↓
Canvas
```

The Application layer is the sole UI-to-Core mutation boundary. Core owns
authoritative electrical identity, equipment, persistent terminals, endpoint
resolution, electrical connection state, topology, and electrical validation.

## Public API

The implemented public connection-layer API is:

```python
from ui.connections import (
    Connection,
    ConnectionPreview,
    ConnectionRouter,
    ConnectionValidator,
    TerminalResolver,
)
```

There is no current `TopologyAdapter` or `ConnectionManager` production
component in this package.

## Components

### Connection

`Connection` is a logical UI connection abstraction. It may represent
connection intent and presentation metadata, but it is not the Core electrical
network database.

It must not:

- resolve or mutate Core objects;
- calculate electrical quantities;
- own Qt graphics objects;
- replace the canonical Application commands.

Committed electrical connectivity remains an Application command concern.

### ConnectionPreview

`ConnectionPreview` is the common transient logical state abstraction used
by interactive connection tools.

It contains only non-persistent interaction data:

- source endpoint intent;
- target endpoint intent;
- cursor position;
- validity;
- validation reason;
- commit readiness.

It contains no Qt objects, renderer state, Core objects, or persistent
electrical state.

Concrete tools may retain presentation-only geometry handles needed to render
a preview. They must not maintain a second logical endpoint/preview state.

### ConnectionValidator

`ConnectionValidator` performs UI-level structural checks such as terminal
existence, self-connection rejection, same-equipment rejection, and duplicate
connection detection.

It does not perform electrical analysis and does not mutate Core.

### TerminalResolver

`TerminalResolver` resolves presentation terminal registrations for UI
structural checks. It is not the authoritative Core terminal identity system.

### ConnectionRouter

`ConnectionRouter` calculates renderer-neutral presentation geometry.
The current implementation provides direct two-point paths.

No current production rendering integration is claimed here. If a future
renderer consumes `ConnectionRouter`, the boundary remains:

```text
ConnectionRouter
    ↓
renderer-neutral presentation geometry
    ↓
renderer
```

It must never own Core topology, commands, persistence, or Qt scene objects.

## Tool integration

`WireTool`, `LineTool`, and `CableTool` all follow the canonical endpoint
boundary:

```text
SnapSystem
    ↓
SnapResult
    ↓
EndpointIdentityAdapter
    ↓
EndpointReference
    ↓
immutable command
    ↓
Application.execute()
```

The tools use `ConnectionPreview` for common transient logical state.
Presentation positions remain tool-owned only where required for visual
preview/rendering.

The simple Wire / engineering Line / engineering Cable distinction remains:

- **Wire** — simple wired connectivity without Line/Cable engineering
  semantics.
- **Line** — engineering parameters such as resistance, reactance, rate, and
  shunt susceptance.
- **Cable** — cable parameters such as length, rated values, and positive/zero
  sequence parameters.

These are not collapsed into a generic electrical connection command.

## Identity boundary

Presentation `EquipmentTerminal.terminal_id` is not promoted to Core
identity.

The canonical terminal reference is represented by:

```text
EndpointReference(
    equipment_type,
    equipment_id,
    terminal_role,
)
```

The UI connection subsystem does not create a second endpoint identity model.

## Qt and Core boundaries

The logical connection package remains Qt-independent and does not import
concrete Core network objects.

It does not own:

- `QGraphicsScene`;
- `QGraphicsView`;
- `QGraphicsItem`;
- renderers;
- viewport state;
- electrical topology;
- persistence of preview state.

## Historical migration note

The former `ui.topology.TopologyValidator` subsystem and the retired
`ui.equipment.connection*` architecture are historical migration residue,
not current V2 production APIs. Historical audit evidence may continue to
refer to those names, but current production documentation must not present
them as active components.

The V2 connection subsystem deliberately does **not** introduce a
`TopologyAdapter` to satisfy historical documentation. The existing
EndpointIdentityAdapter → EndpointReference → Application command boundary is
the authoritative synchronization boundary.
