# GridForge V2 — Connection Subsystem

## File Location


ui/connections/


## Purpose

The `ui.connections` subsystem owns the logical Single Line Diagram (SLD)
connection workflow at the UI boundary.

It provides the abstractions required for:

* logical connection state;
* terminal resolution;
* structural connection validation;
* interactive connection preview;
* renderer-neutral connection routing;
* synchronization with the authoritative GridForge Core topology.

The subsystem must not become a second electrical-network database.

---

# Architectural Principle

A line drawn on the canvas is not automatically a valid electrical
connection.

The intended workflow is:

```text
User Interaction
       │
       ▼
Terminal Resolution
       │
       ▼
Connection Candidate
       │
       ▼
Structural Validation
       │
       ├──────── invalid ────────► Reject / Preview Feedback
       │
       ▼
Connection Creation
       │
       ▼
Logical SLD Connection
       │
       ▼
Topology Synchronization Boundary
       │
       ▼
GridForge Core
```

The UI connection subsystem owns the logical connection abstractions and
interaction-level state.

GridForge Core remains authoritative for electrical-network topology and
electrical validity.

---

# Components

## `connection.py`

Defines the logical `Connection` object.

### Responsibilities

* stable connection identity;
* source terminal identity;
* target terminal identity;
* connection type;
* connection properties;
* enabled state;
* serialization/deserialization;
* terminal relationship queries.

### Does not

* draw graphics;
* create `LineItem`;
* calculate impedance;
* calculate admittance;
* mutate Core;
* own Qt objects.

---

## `terminal_resolver.py`

Defines `TerminalResolver`.

### Responsibilities

* register logical terminals;
* unregister terminals;
* resolve terminal IDs;
* require existing terminals;
* determine whether a terminal exists;
* enumerate terminals;
* enumerate terminals belonging to equipment;
* resolve the owning equipment ID of a terminal.

### Does not

* perform graphical hit testing;
* create connections;
* validate electrical topology;
* create graphics items.

Terminal identity is maintained independently of graphics objects.

---

## `connection_validator.py`

Defines:

```text
ConnectionValidator
ValidationResult
TerminalResolverProtocol
```

The validator performs UI-level structural validation.

### Responsibilities

* validate source terminal identifiers;
* validate target terminal identifiers;
* verify terminal existence;
* reject self-connections;
* reject same-equipment connections;
* reject duplicate connections;
* reject malformed existing connection entries;
* return explicit immutable `ValidationResult` objects.

### Does not

* perform load-flow analysis;
* perform short-circuit analysis;
* calculate impedance;
* calculate admittance;
* perform protection analysis;
* solve electrical topology;
* modify Core state.

Core remains authoritative for electrical validation.

---

## `connection_preview.py`

Defines `ConnectionPreview`.

It stores temporary state during interactive connection creation.

### Responsibilities

* source terminal;
* target terminal;
* cursor position;
* validation state;
* validation reason;
* active/inactive state;
* commit eligibility;
* reset/cancel lifecycle.

### Does not

* create persistent `Connection` objects;
* mutate Core;
* render graphics;
* own a `QGraphicsScene`.

Preview state is temporary and must not become persistent logical connection state.

---

## `connection_router.py`

Defines:

```text
ConnectionRouter
ConnectionPath
Point
```

The router calculates renderer-neutral connection geometry.

### Responsibilities

* validate routing coordinates;
* normalize coordinates;
* calculate direct connection paths;
* provide start/end points;
* provide intermediate routing points;
* provide an extension point for future routing algorithms.

The current implementation provides direct two-point routing.

Future routing strategies may include:

* orthogonal routing;
* grid-aware routing;
* obstacle-aware routing;
* terminal-direction routing;
* bus-aware routing.

### Does not

* create `QGraphicsPathItem`;
* render graphics;
* access `QGraphicsScene`;
* validate electrical topology;
* modify logical `Connection` state.

---

## `topology_adapter.py`

Defines the `TopologyAdapter` protocol.

This is the explicit synchronization boundary between the UI connection
subsystem and GridForge Core.

The protocol defines operations for:

```text
add_connection(connection)
remove_connection(connection)
```

The protocol deliberately does not import or depend on a concrete Core
network implementation.

This prevents the UI layer from inventing or duplicating the Core topology
API.

A concrete Core adapter may be introduced only after the authoritative Core
contract is established.

---

## `__init__.py`

Defines the public connection-layer API.

The current public objects are:

```python
from ui.connections import (
    Connection,
    ConnectionPreview,
    ConnectionRouter,
    ConnectionValidator,
    TerminalResolver,
    TopologyAdapter,
)
```

No `ConnectionManager` is currently exported because no production
`connection_manager.py` implementation exists in this subsystem.

---

# Dependency Direction

The intended dependency direction is:

```text
                 SLD / Tool Interaction
                         │
                         ▼
                Connection Workflow
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
 TerminalResolver   ConnectionValidator   Connection
          │              │
          └──────────────┴──────────────┐
                                        │
                                        ▼
                                 TopologyAdapter
                                        │
                                        ▼
                                   GridForge Core
```

The connection subsystem must not introduce reverse dependencies from Core
into UI connection objects.

---

# Rendering Boundary

Connection geometry and rendering are separate responsibilities.

```text
Connection
     │
     ▼
ConnectionRouter
     │
     ▼
LineItem
     │
     ▼
LineRenderer
     │
     ▼
Canvas
```

The connection subsystem therefore does not draw anything.

Connection classes must not:

* import `QGraphicsScene`;
* create `QGraphicsItem`;
* create `QGraphicsPathItem`;
* manipulate viewport transforms;
* perform painting;
* access renderer implementations.

---

# Core Boundary

GridForge Core remains authoritative for electrical-network state.

The UI connection layer may maintain logical UI state such as:

```text
Connection
    ├── connection_id
    ├── source_terminal_id
    ├── target_terminal_id
    ├── connection_type
    ├── properties
    └── enabled
```

This state must not become an independent electrical-network model.

The intended synchronization direction is:

```text
UI Connection
      │
      ▼
TopologyAdapter
      │
      ▼
GridForge Core
```

The UI connection layer must never:

* calculate impedance;
* calculate admittance;
* solve electrical topology;
* perform power-flow calculations;
* perform short-circuit calculations;
* perform protection calculations;
* directly mutate concrete Core network objects.

---

# Structural Validation

The UI validator may enforce immediate structural constraints including:

* terminal existence;
* source/target identity;
* self-connection rejection;
* same-equipment rejection;
* duplicate connection rejection;
* basic connection structure.

These checks provide immediate UI feedback.

They do not replace Core electrical validation.

The authoritative sequence remains:

```text
UI Structural Validation
          │
          ▼
Logical Connection
          │
          ▼
TopologyAdapter
          │
          ▼
Core Validation / Topology
          │
          ▼
Electrical Analysis
```

---

# Connection Lifecycle

The current connection abstractions support the following conceptual lifecycle:

```text
IDLE
 │
 │ user selects source terminal
 ▼
PREVIEW
 │
 │ cursor moves
 │
 ├── terminal resolved
 │
 ├── candidate validated
 │
 └── preview updated
 │
 ▼
VALID CANDIDATE
 │
 │ commit through the higher-level interaction workflow
 ▼
CONNECTION CREATED
 │
 ▼
CORE SYNCHRONIZATION
 │
 ▼
CONNECTED
```

Cancellation:

```text
PREVIEW
    │
    │ cancel
    ▼
IDLE
```

Invalid candidates must not be committed as logical connections.

---

# Terminal Identity

Connections use stable logical terminal identifiers.

A `Connection` must not use graphical objects as logical identity.

It must not store:

```text
QGraphicsItem
QGraphicsObject
QPointF
QGraphicsView
QGraphicsScene
```

as terminal identity.

The logical relationship is:

```text
Connection
    │
    ├── source_terminal_id
    └── target_terminal_id
```

Terminal resolution is performed separately through `TerminalResolver`.

This allows graphics objects to be recreated without invalidating the logical
connection model.

---

# Equipment Boundary

Equipment owns its terminal definitions.

Conceptually:

```text
Equipment
    │
    ├── Terminal A
    ├── Terminal B
    └── Terminal C
```

The connection subsystem references terminals through stable identifiers.

It does not take ownership of equipment.

The relationship is:

```text
Equipment
      │
      ▼
EquipmentTerminal
      │
      ▼
TerminalResolver
      │
      ▼
Connection
```

---

# Qt Boundary

The connection subsystem is intentionally Qt-independent.

The following components must remain free of Qt dependencies:

```text
Connection
ConnectionPreview
ConnectionRouter
ConnectionValidator
TerminalResolver
TopologyAdapter
```

This keeps the logical connection layer independently testable without
constructing a graphics scene.

---

# Testing Strategy

Production-code auditing is completed before test-code auditing.

When the test suite is created or audited, it should correspond only to
components that actually exist in the production package.

Expected production-aligned test structure:

```text
tests/ui/connections/
├── test_connection.py
├── test_connection_preview.py
├── test_connection_router.py
├── test_connection_validator.py
├── test_terminal_resolver.py
└── test_topology_adapter.py
```

There is currently no `ConnectionManager` production component, therefore
there must be no mandatory `test_connection_manager.py` until such a
production component is intentionally introduced.

Tests should verify:

### `Connection`

* valid construction;
* invalid identifiers;
* self-connection rejection;
* terminal relationship queries;
* serialization;
* deserialization.

### `TerminalResolver`

* registration;
* duplicate registration rejection;
* lookup;
* required lookup;
* terminal existence;
* equipment lookup;
* equipment-terminal queries;
* unregister;
* clearing.

### `ConnectionValidator`

* invalid source;
* invalid target;
* missing source;
* missing target;
* self connection;
* same-equipment connection;
* duplicate connection;
* malformed existing connection;
* valid connection.

### `ConnectionPreview`

* begin;
* target update;
* cursor update;
* validity;
* commit eligibility;
* cancel;
* reset.

### `ConnectionRouter`

* direct routing;
* coordinate validation;
* coordinate normalization;
* start/end points;
* renderer-neutral output.

### `TopologyAdapter`

* protocol conformance;
* add synchronization through a fake adapter;
* remove synchronization through a fake adapter;
* absence of direct concrete Core dependency.

---

# Architectural Invariants

The following rules are mandatory for GridForge V2.

## 1. Core Is Authoritative

The UI connection layer must never become the authoritative electrical network.

## 2. Logical and Visual Connections Are Separate

A logical `Connection` is not a `LineItem`.

```text
Connection != LineItem
```

## 3. Stable IDs Are Used

Connections reference terminals using stable logical identifiers.

## 4. Rendering Is External

The connection subsystem does not paint or create graphics objects.

## 5. Routing Is Separate From the Model

`ConnectionRouter` calculates geometry without modifying the logical
connection.

## 6. Preview Is Temporary

`ConnectionPreview` must never become persistent connection state.

## 7. Validation Is Structural

UI validation provides immediate structural feedback but does not replace
Core electrical validation.

## 8. Core Synchronization Is Explicit

Core synchronization occurs only through `TopologyAdapter`.

The UI must not silently mutate Core objects.

## 9. No Concrete Core Dependency

The connection subsystem must not import concrete Core network classes merely
to make the UI compile.

## 10. No Canvas Ownership

The connection subsystem does not own:

```text
QGraphicsScene
QGraphicsView
LineItem
renderers
viewport state
```

## 11. No Speculative Components

Documentation must describe implemented production components.

Future components must not be presented as current public APIs.

---

# Current Production API

The current connection-layer public API is:

```python
from ui.connections import (
    Connection,
    ConnectionPreview,
    ConnectionRouter,
    ConnectionValidator,
    TerminalResolver,
    TopologyAdapter,
)
```

These objects constitute the currently implemented public connection-layer
API.

A connection manager/orchestration component may be introduced later if the
application architecture requires one. Until then, lifecycle orchestration
belongs to the existing higher-level interaction/controller workflow.

---

# Production Audit Status

```text
ui/connections/
├── connection.py            PASS
├── connection_preview.py    PASS
├── connection_router.py     PASS
├── connection_validator.py  PASS
├── terminal_resolver.py     PASS
├── topology_adapter.py      PASS
├── __init__.py              PASS
└── README.md                PASS
```

The connection subsystem is intentionally:

```text
Qt-independent
Core-independent
renderer-independent
topology-authority-independent
```

while providing explicit boundaries for:

```text
terminal identity
connection state
structural validation
preview state
routing geometry
Core synchronization
```

```
```
