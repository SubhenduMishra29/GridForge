# GridForge V2 — Connection Subsystem


## File Location


```text
ui/connections/
Purpose

The ui.connections subsystem owns the logical Single Line Diagram (SLD)
connection workflow.

It establishes the UI boundary between:

equipment terminals;
connection candidates;
structural connection validation;
logical connection state;
connection routing;
interactive connection preview;
future synchronization with the authoritative GridForge Core topology.

The subsystem provides the connection abstraction required by the current
SLD workflow without becoming a second electrical-network database.

Architectural Principle

A line drawn on the canvas is not automatically a valid electrical
connection.

The connection workflow is:

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

The UI connection subsystem owns the interaction-level connection lifecycle.

The Core remains authoritative for electrical-network topology and electrical
validity.

Components
connection.py

Defines the logical Connection object.

Responsibilities:

stable connection identity;
source terminal identity;
target terminal identity;
connection type;
connection properties;
enabled state;
serialization/deserialization;
terminal relationship queries.

It does not:

draw graphics;
create LineItem;
calculate impedance;
mutate Core;
own Qt objects.
connection_manager.py

Defines ConnectionManager.

Responsibilities:

create logical connections;
remove logical connections;
retrieve connections;
query connections;
maintain the UI connection collection;
coordinate structural validation;
optionally synchronize committed changes through TopologyAdapter.

ConnectionManager is the lifecycle/orchestration boundary of the UI
connection subsystem.

It must not become a duplicate electrical-network database.

terminal_resolver.py

Defines TerminalResolver.

Responsibilities:

register logical terminals;
unregister terminals;
resolve terminal IDs;
require existing terminals;
determine whether a terminal exists;
enumerate terminals;
enumerate terminals belonging to equipment.

It provides the bridge between spatial UI interaction and stable logical
terminal identity.

It does not:

perform graphical hit testing;
create connections;
validate topology;
create graphics items.
connection_validator.py

Defines ConnectionValidator.

Responsibilities:

validate source terminal existence;
validate target terminal existence;
reject self-connections;
reject duplicate connections;
validate basic UI-level terminal compatibility;
return explicit ValidationResult objects.

The validator is deliberately a structural UI validator.

It does not perform:

load-flow analysis;
short-circuit analysis;
impedance calculations;
protection analysis;
electrical-network topology solving.

Those responsibilities remain in Core.

connection_preview.py

Defines ConnectionPreview.

It stores temporary state during interactive connection creation.

Responsibilities:

source terminal;
target terminal;
cursor position;
validation state;
validation reason;
active/inactive state;
commit eligibility;
reset/cancel lifecycle.

It does not:

create connections;
mutate Core;
render graphics;
own a QGraphicsScene.
connection_router.py

Defines ConnectionRouter.

Responsibilities:

calculate renderer-neutral connection geometry;
generate direct connection paths;
provide routing points;
provide an extension point for future routing algorithms.

The initial implementation supports direct two-point routing.

Future implementations may support:

orthogonal routing;
grid-aware routing;
obstacle-aware routing;
terminal-direction routing;
bus-aware routing.

The router does not:

create QGraphicsPathItem;
render connection graphics;
validate electrical topology.
topology_adapter.py

Defines the TopologyAdapter protocol.

It establishes the explicit synchronization boundary between the UI connection
system and Core.

The adapter defines operations such as:

add_connection(connection)
remove_connection(connection)

The protocol deliberately does not import or depend on the concrete Core
implementation.

This prevents the UI architecture from inventing a Core network API before
the authoritative Core contract is selected.

Dependency Direction

The intended dependency direction is:

                 SLD / Tool Interaction
                         │
                         ▼
                ConnectionManager
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

The connection subsystem must not introduce reverse dependencies from Core
into UI connection objects.

Rendering Boundary

Connection geometry and rendering are deliberately separated.

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

The connection subsystem therefore does not draw anything.

In particular, connection classes must not:

import QGraphicsScene;
create QGraphicsItem;
create QGraphicsPathItem;
manipulate viewport transforms;
perform painting;
access renderer implementations.
Core Boundary

Core remains authoritative for electrical-network state.

The UI connection layer may maintain logical UI connection state such as:

Connection
    ├── connection_id
    ├── source_terminal_id
    ├── target_terminal_id
    ├── connection_type
    ├── properties
    └── enabled

However, this must not become an independent electrical-network model.

The synchronization direction is:

UI Connection
      │
      ▼
TopologyAdapter
      │
      ▼
Core Network API

The connection subsystem must never:

UI Connection
      │
      ├── calculate impedance
      ├── calculate admittance
      ├── solve topology
      ├── calculate power flow
      ├── calculate short circuit
      └── modify Core objects directly
Structural Validation

The UI validator may enforce structural constraints including:

terminal existence;
source/target identity;
self-connection rejection;
duplicate connection rejection;
basic terminal compatibility;
terminal role compatibility;
connection multiplicity;
required connection direction.

These checks are intended to provide immediate UI feedback.

They do not replace Core electrical validation.

The authoritative sequence remains:

UI Structural Validation
          │
          ▼
Logical Connection
          │
          ▼
Core Validation / Topology
          │
          ▼
Electrical Analysis
Connection Lifecycle

A normal connection lifecycle is:

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
 │ commit
 ▼
CONNECTION CREATED
 │
 ▼
CORE SYNCHRONIZATION
 │
 ▼
CONNECTED

Cancellation follows:

PREVIEW
    │
    │ cancel
    ▼
IDLE

Invalid candidates do not create logical connections.

PREVIEW
    │
    ▼
INVALID
    │
    ├── feedback
    │
    └── no Connection created
Connection Manager Boundary

ConnectionManager is responsible for logical connection lifecycle.

It may:

create
remove
query
enumerate
validate
synchronize

It must not:

render
route graphics
perform electrical calculations
own the canvas
own the scene
own LineItem
own Core

The manager owns only the UI-level logical connection collection.

Terminal Identity

Connections use stable logical terminal identifiers.

They must not store:

QGraphicsItem
QGraphicsObject
QPointF
GraphicsView
GraphicsScene

as their identity.

The logical relationship is:

Connection
    │
    ├── source_terminal_id
    │
    └── target_terminal_id

Terminal resolution is performed separately through TerminalResolver.

This allows graphics objects to be recreated without invalidating the logical
connection model.

Equipment Boundary

Equipment owns its terminal definitions.

Conceptually:

Equipment
    │
    ├── Terminal A
    ├── Terminal B
    └── Terminal C

The connection subsystem references those terminals by stable identifiers.

It does not take ownership of equipment.

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
Qt Boundary

The connection subsystem is intentionally mostly Qt-independent.

Connection-domain objects should not directly depend on Qt unless a future
specific requirement establishes a clear presentation boundary.

In particular:

Connection must remain Qt-independent;
ConnectionPreview must remain Qt-independent;
ConnectionRouter must remain Qt-independent;
ConnectionValidator must remain Qt-independent;
TerminalResolver must remain Qt-independent;
TopologyAdapter must remain Qt-independent.

This keeps the logical connection layer testable without constructing a
graphics scene.

Testing Strategy

The subsystem should be tested independently from the Qt canvas.

Expected test structure:

tests/ui/connections/
├── test_connection.py
├── test_connection_manager.py
├── test_connection_preview.py
├── test_connection_router.py
├── test_connection_validator.py
├── test_terminal_resolver.py
└── test_topology_adapter.py

Tests should verify:

Connection
valid construction;
invalid identifiers;
self-connection rejection;
terminal relationship queries;
serialization;
deserialization.
ConnectionManager
creation;
duplicate detection;
removal;
lookup;
enumeration;
terminal-based queries;
validation delegation;
topology-adapter synchronization.
TerminalResolver
registration;
duplicate registration rejection;
lookup;
required lookup;
unregister;
equipment-terminal queries;
clearing.
ConnectionValidator
missing source;
missing target;
self connection;
unknown terminal;
same-equipment connection;
duplicate connection;
valid connection.
ConnectionPreview
begin;
target update;
cursor update;
validity;
commit eligibility;
cancel;
reset.
ConnectionRouter
direct routing;
coordinate conversion to floats;
start/end points;
renderer-neutral output.
TopologyAdapter
protocol conformance;
add/remove synchronization through a fake adapter;
no direct Core dependency.
Architectural Invariants

The following rules are mandatory for GridForge V2.

1. Core Is Authoritative

The UI connection layer must never become the authoritative electrical network.

2. Logical and Visual Connections Are Separate

A logical Connection is not a LineItem.

Connection != LineItem
3. Stable IDs Are Used

Connections reference terminals using stable logical identifiers.

4. Rendering Is External

The connection subsystem does not paint or create graphics objects.

5. Routing Is External to the Model

ConnectionRouter calculates geometry without modifying the logical
connection.

6. Preview Is Temporary

ConnectionPreview must never become persistent connection state.

7. Validation Is Structural

UI validation provides immediate structural feedback but does not replace
Core electrical validation.

8. Core Synchronization Is Explicit

Core synchronization occurs only through TopologyAdapter.

The UI must not silently mutate Core objects.

9. No Core Implementation Dependency

The connection subsystem must not import concrete Core network classes merely
to make the UI compile.

10. No Canvas Ownership

The connection subsystem does not own:

QGraphicsScene;
QGraphicsView;
LineItem;
renderers;
viewport state.
Public API

The package exposes the following public objects:

from ui.connections import (
    Connection,
    ConnectionManager,
    ConnectionPreview,
    ConnectionRouter,
    ConnectionValidator,
    TerminalResolver,
    TopologyAdapter,
)

These constitute the public connection-layer API.

Internal implementation details should remain private.
