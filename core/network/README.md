core/network/README.md
# ============================================================
# File: core/network/README.md
# GridForge V2 — Network Layer
# Author: Subhendu Mishra
# ============================================================

# GridForge V2 — Network Layer

The `core/network` package is the **assembled electrical-network
layer** of GridForge V2.

It sits between the canonical electrical model layer and the
engineering analysis / numerical solver layers.

```text
                        CORE MODEL
                    canonical entities
                           │
                           │
                           ▼
                  ┌──────────────────┐
                  │  core.network    │
                  │                  │
                  │     Network      │
                  │       │          │
                  │  ┌────┼────┐     │
                  │  ▼    ▼    ▼     │
                  │ Registry Index   │
                  │       │ State    │
                  │       │          │
                  │   ┌───┴────┐     │
                  │   ▼        ▼     │
                  │Topology   Y-Bus  │
                  └────┬────────┬────┘
                       │        │
                       ▼        ▼
                 core.analysis
                       │
                       ▼
                  core.solver
1. Architectural Role

The Network Layer assembles canonical electrical model objects into
an operational electrical network representation.

It provides the infrastructure required by engineering studies.

The Network Layer is not the electrical model layer.

It is also not the application layer, SLD layer, analysis layer,
or solver layer.

Its central responsibility is:

Maintain an assembled network and expose authoritative derived
representations of that network.

2. Layer Boundaries

GridForge V2 separates responsibilities as follows.

┌─────────────────────────────────────────────────────────────┐
│ UI / SLD                                                    │
│ Engineering authoring and visualization                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ commands / DTOs
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ APPLICATION                                                 │
│ Commands / transactions / orchestration                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ create / connect / register
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ MODEL                                                       │
│ Canonical electrical entities                               │
│ Bus, Line, Transformer, Generator, Load, Shunt, etc.       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ references
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ NETWORK                                                     │
│ Assembled network / topology / indexing / Y-bus / state     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ ANALYSIS                                                    │
│ Study orchestration                                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ SOLVER                                                      │
│ Numerical algorithms                                        │
└─────────────────────────────────────────────────────────────┘
3. Canonical Model Ownership

core.model is the single source of truth for electrical entities.

The Network Layer stores references to those objects.

It does not create duplicate network-specific versions of model
objects.

Examples include:

Bus
Line
Transformer
Generator
Load
Shunt
Breaker
Disconnector
Fuse
CT
PT
CVT
Relay
Motor
Cable

The exact model inventory may expand through the GridForge plugin
architecture, but the ownership rule does not change.

core.model
    │
    └── owns electrical object definition

core.network
    │
    └── assembles references to those objects
4. Network Ownership

The Network Layer owns the assembled-network representation.

It owns:

canonical network membership;
deterministic bus indexing;
topology service;
Y-bus construction service;
network-derived state;
network-level reconfiguration;
network-level status invalidation;
network-level study state required by the network boundary.

It does not own:

GUI state;
SLD graphics;
canvas state;
engineering-study orchestration;
numerical solver algorithms;
electrical equipment definitions;
plugin UI state.
5. Package Structure

The current Network package is deliberately decomposed.

core/network/
│
├── __init__.py
├── README.md
│
├── network.py
├── registry.py
├── indexing.py
├── state.py
├── endpoint.py
├── topology.py
└── ybus.py

Each file has one principal responsibility.

6. network.py

network.py contains the Network façade.

The façade coordinates the Network Layer services.

It does not implement all network functionality itself.

Conceptually:

Network
   │
   ├── NetworkRegistry
   ├── BusIndex
   ├── NetworkState
   ├── TopologyManager
   └── YBusBuilder

The façade provides the stable entry point for callers that need to
work with an assembled network.

Typical usage:

from core.network import Network

network = Network(base_mva=100.0)
7. registry.py

registry.py contains NetworkRegistry.

The registry owns network membership.

It maintains collections of canonical model objects:

buses
lines
transformers
generators
loads
shunts

The registry is responsible for:

registering objects;
preventing duplicate identifiers within a collection;
removing canonical registered objects;
maintaining collection membership.

The registry does not own:

topology;
Y-bus;
bus indexing;
solver calculations;
engineering validation;
GUI state.

Therefore:

Registry = membership

not:

Registry = network logic
8. indexing.py

indexing.py contains BusIndex.

BusIndex owns the deterministic mapping between canonical bus
identifiers and numerical matrix positions.

Conceptually:

BUS-001 ──► 0
BUS-002 ──► 1
BUS-003 ──► 2
BUS-004 ──► 3

This mapping is required by matrix-based calculations such as Y-bus.

The index is derived state.

It must therefore be invalidated whenever bus membership or bus
ordering changes.

The Network Layer does not allow Y-bus construction to operate on a
stale bus index.

9. state.py

state.py contains NetworkState.

NetworkState owns derived-network validity information.

Examples include:

topology_dirty
ybus_dirty
topology_revision
ybus_revision

The purpose is to make derived-state invalidation explicit.

For example:

network topology changes
        │
        ▼
topology becomes invalid
        │
        ▼
Y-bus becomes invalid

A change that affects only Y-bus data may invalidate Y-bus without
necessarily changing topology.

This distinction prevents unnecessary rebuilding.

10. endpoint.py

endpoint.py contains the internal terminal-resolution utility.

Its purpose is to resolve the bus associated with a canonical terminal
relationship.

Conceptually:

Equipment
    │
    ▼
Terminal
    │
    ▼
Endpoint
    │
    ▼
Bus

This utility exists because GridForge V2 uses terminal-based physical
connectivity.

The terminal is therefore more authoritative than compatibility
properties such as:

from_bus
to_bus
bus

Those properties may remain useful model-level interfaces, but they
are not the authoritative network connection representation.

endpoint.py is an internal network utility.

It is not a primary package-level API.

11. topology.py

topology.py contains TopologyManager.

Topology is a derived representation of canonical model state.

The topology manager determines electrical connectivity from the
current canonical network objects and their service state.

It provides functionality such as:

build()
find_islands()
is_connected()

The topology manager does not own:

Bus objects;
Line objects;
Transformer objects;
SLD objects;
UI connections.

The fundamental relationship is:

Canonical model
       │
       ▼
TopologyManager
       │
       ▼
Derived electrical graph

The graph can then be consumed by engineering analysis.

12. Topology and SLD Are Different

The SLD is not the electrical topology database.

The SLD is a visual engineering representation.

The canonical relationship is:

Model
  │
  ├──────────────► Network topology
  │
  └──────────────► SLD representation

Therefore:

SLD connection

does not become electrical truth merely because a graphical line was
drawn.

The application layer converts engineering authoring operations into
commands.

The Core validates and applies the resulting domain changes.

13. ybus.py

ybus.py contains YBusBuilder.

The Y-bus is a derived numerical representation of the assembled
network.

The builder consumes:

Network
    │
    ├── canonical buses
    ├── canonical branches
    ├── transformers
    ├── shunts
    └── deterministic BusIndex

and constructs:

Ybus

Conceptually:

Canonical network
       │
       ▼
   BusIndex
       │
       ▼
 YBusBuilder
       │
       ▼
    Y-bus

The Y-bus builder performs matrix construction and element stamping.

It does not perform:

Newton-Raphson iterations;
power-flow solution;
short-circuit solution;
protection calculations;
transient simulation.
14. Who Builds the Network?

The Network is not normally constructed by the UI directly.

The intended engineering workflow is:

Engineer
   │
   ▼
SLD / Application authoring
   │
   ▼
Command
   │
   ▼
Transaction
   │
   ├── create canonical model
   ├── validate
   ├── connect
   ├── register
   └── commit
          │
          ▼
       Network

The Network Layer provides the APIs consumed by the Application
Layer.

The Application Layer owns the workflow.

15. Command Boundary

The Core is headless.

Therefore commands do not depend on Qt, graphics scenes, widgets, or
SLD items.

A command represents an engineering operation.

Examples include:

CreateBus
CreateLine
CreateTransformer
CreateGenerator
CreateLoad
CreateShunt

ConnectTerminal
DisconnectTerminal

RegisterElement
RemoveElement

SetElementStatus
ReconnectElement

CreateNetwork
DeleteNetwork

The exact command inventory is maintained by the Application command
architecture.

The Network Layer should not become a command dispatcher.

16. Transaction Boundary

Network modifications should occur through application-level
transactions.

The intended conceptual workflow is:

Command
   │
   ▼
Begin transaction
   │
   ├── create model
   ├── validate
   ├── connect
   ├── register
   ├── update derived state
   │
   ▼
Commit

If a required operation fails:

failure
   │
   ▼
rollback

The important ownership rule is:

Application
    owns transaction orchestration

Model
    owns canonical object state

Network
    owns assembled membership and derived network state
17. Creation Ownership

The following ownership model is mandatory.

Responsibility	Owner
Create canonical electrical object	Model/Application boundary
Define electrical object	core.model
Engineering command	Application
Transaction	Application
Network membership	NetworkRegistry
Bus indexing	BusIndex
Connectivity graph	TopologyManager
Y-bus	YBusBuilder
Derived-state validity	NetworkState
Numerical power-flow solution	Solver
Engineering study orchestration	Analysis
SLD rendering	UI
SLD interaction	UI/Application
Electrical truth	Core Model + Network
GUI truth	UI
18. Validation Boundary

Validation occurs at multiple architectural levels.

The Network Layer must not absorb all validation.

Conceptually:

Command validation
       │
       ▼
Domain/model validity
       │
       ▼
Network structural validity
       │
       ▼
Engineering validation
       │
       ▼
Study-specific validation

The Network Layer can enforce structural requirements necessary for
its own operation.

Examples:

duplicate bus ID
missing object ID
unregistered bus reference
invalid network membership
invalid bus index

Engineering rules remain outside the Network Layer.

19. Network Consumption

The Network is consumed by higher-level engineering layers.

Typical dependency flow:

                    Network
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       topology       Ybus       injections
          │            │            │
          └────────────┼────────────┘
                       ▼
                    Analysis
                       │
                       ▼
                     Solver

For example, a power-flow study may consume:

Network buses
Network injections
Network topology
Network Y-bus

The solver then consumes numerical representations prepared by the
analysis layer.

20. Y-Bus Consumer Boundary

The Y-bus is not a final engineering result.

It is an intermediate network representation.

The intended flow is:

Model
  │
  ▼
Network
  │
  ▼
YBusBuilder
  │
  ▼
Ybus
  │
  ▼
Analysis Study
  │
  ▼
Solver
  │
  ▼
Engineering Result

For example:

Power Flow Analysis
        │
        ├── Network state
        ├── Bus specifications
        ├── Y-bus
        └── solver configuration
                 │
                 ▼
             Power Flow Solver

The solver must not independently reconstruct the complete network
from model objects when the Network Layer already provides the
assembled representation required by the study.

21. Network Reconfiguration

Network reconfiguration occurs when network topology-affecting
information changes.

Examples include:

add bus
remove bus
add line
remove line
add transformer
remove transformer
change service state
connect branch
disconnect branch

The derived-state relationship is:

network mutation
       │
       ▼
topology invalid
       │
       ▼
Y-bus invalid

The Network does not necessarily rebuild everything immediately.

Derived structures may be rebuilt lazily when requested.

22. Service State

Topology-affecting equipment may have an in_service state.

Changing the state of such an element must invalidate the derived
network representation.

Conceptually:

Line.in_service = True
        │
        │ change
        ▼
Line.in_service = False
        │
        ▼
Topology invalid
        │
        ▼
Y-bus invalid

The Network Layer performs the state/invalidation boundary.

Engineering consequences of the state change are handled by the
appropriate analysis/validation layers.

23. Bus Indexing and Y-Bus

Bus indexing is deterministic.

The Y-bus matrix position must always correspond to the Network's
current bus index.

BusIndex
    │
    ├── BUS-001 → 0
    ├── BUS-002 → 1
    ├── BUS-003 → 2
    └── BUS-004 → 3
             │
             ▼
          Y-bus

A stale index must never be used to construct a Y-bus.

Therefore Y-bus construction ensures that the bus index is current
before matrix construction.

24. Network State Is Derived State

The following are derived:

bus index
topology graph
Y-bus
island information

The canonical model objects remain authoritative.

Therefore:

Model
   │
   ├── authoritative state
   │
   ▼
Network
   │
   ├── derived index
   ├── derived topology
   └── derived Y-bus

Derived data may be discarded and rebuilt.

Canonical model state must not be reconstructed from derived data.

25. No GUI Dependency

core/network must remain completely headless.

It must not import:

PySide6
PyQt
QGraphicsScene
QGraphicsItem
MainWindow
SLD canvas
UI plugin
renderer

The Network Layer must be usable from:

CLI
unit tests
batch processing
server processes
automation
engineering studies
headless simulation

without starting a GUI.

26. No Solver Dependency

The Network Layer must not contain numerical study algorithms.

It provides network representations.

It does not solve them.

Incorrect:

Network.solve_power_flow()
Network.solve_short_circuit()
Network.run_transient()

Correct boundary:

Network
   │
   ▼
Analysis
   │
   ▼
Solver
27. Per-Unit Boundary

The canonical per-unit implementation belongs to:

core.base.per_unit.PerUnitSystem

There must not be a duplicate:

core/network/per_unit.py

The Network constructs a system-wide instance:

network.per_unit

using the Network MVA base.

PerUnitSystem may also be imported through:

from core.network import PerUnitSystem

but its implementation remains owned by the Base Layer.

28. Public API

The package-level API is intentionally narrow.

from core.network import (
    Network,
    NetworkRegistry,
    BusIndex,
    NetworkState,
    TopologyManager,
    YBusBuilder,
    PerUnitSystem,
)

The principal entry point is:

Network

Most application code should interact with the Network façade rather
than importing implementation details from individual modules.

29. Example

A minimal assembled network conceptually looks like:

from core.network import Network

network = Network(base_mva=100.0)

network.add_bus(bus_1)
network.add_bus(bus_2)

network.add_line(line_1)

network.rebuild_topology()

Ybus = network.get_ybus()

The objects passed to the Network are canonical model objects.

They are not Network-specific duplicates.

30. Engineering Workflow Example

A typical SLD authoring operation is conceptually:

Engineer selects "Bus"
        │
        ▼
SLD preview
        │
        ▼
Engineer clicks canvas
        │
        ▼
Application creates CreateBus command
        │
        ▼
Transaction
        │
        ├── create canonical Bus
        ├── validate
        ├── register Bus with Network
        └── commit
        │
        ▼
Network
        │
        ├── membership updated
        ├── bus index invalidated
        ├── topology invalidated
        └── Y-bus invalidated
        │
        ▼
SLD receives updated state/projection

The SLD never becomes the owner of the electrical Bus.

31. Terminal-Based Connectivity

GridForge V2 uses terminals as the authoritative physical connection
representation.

Conceptually:

Equipment
    │
    ▼
Terminal
    │
    ▼
Endpoint
    │
    ▼
Bus / Terminal

This allows the Network architecture to support:

Terminal ↔ Bus
Terminal ↔ Terminal

and more advanced equipment topologies without forcing every
connection into a simple from_bus / to_bus representation.

Compatibility properties may exist on model objects, but they do not
replace terminal relationships as the authoritative connection model.

32. Bus-to-Bus SLD Connectivity

A graphical bus-to-bus connection is an engineering authoring
operation.

It is not implemented by directly manipulating the Network graph
from the SLD.

The intended path is:

SLD
 │
 ▼
Application command
 │
 ▼
connection validation
 │
 ▼
canonical model connection
 │
 ▼
Network registration/update
 │
 ▼
Topology rebuild/invalidation
 │
 ▼
Y-bus invalidation

The exact electrical interpretation depends on the canonical model
and connection contract.

The Network Layer enforces the resulting assembled-network
representation; the Application Layer owns the authoring workflow.

33. Removal Semantics

Removing a network element changes Network membership.

For example:

Network.remove_line(line)

means:

remove Line from Network membership

It does not automatically mean:

delete Line model object
disconnect unrelated equipment
delete buses
modify SLD graphics

Those operations belong to their respective ownership boundaries.

34. Bus Removal

Bus removal is deliberately strict.

A Bus cannot be removed if a registered element still references it.

References may arise through:

Line terminals
Transformer terminals
Generator bus
Load bus
Shunt terminal

The Network therefore prevents dangling assembled-network references.

The application layer may first issue the necessary disconnect/remove
commands and then remove the Bus.

35. Important Invariants

The following invariants apply to the Network Layer.

Invariant 1 — Canonical model ownership
core.model owns electrical entities.
Invariant 2 — Network references models
Network does not duplicate model classes.
Invariant 3 — Registry owns membership
Registry owns collection membership.
Invariant 4 — Index owns matrix indexing
BusIndex owns deterministic bus indexing.
Invariant 5 — Topology is derived
TopologyManager derives connectivity.
Invariant 6 — Y-bus is derived
YBusBuilder derives Y-bus.
Invariant 7 — State owns invalidation
NetworkState owns derived-state validity.
Invariant 8 — Core remains headless
No GUI dependency.
Invariant 9 — Network does not solve
No numerical engineering solver algorithms.
Invariant 10 — Application owns commands
Commands do not belong in core/network.
36. Responsibility Matrix
Operation	Primary Owner
Define Bus	core.model
Define Line	core.model
Define Transformer	core.model
Define Generator	core.model
Define Load	core.model
Create command	Application
Execute transaction	Application
Engineering authoring workflow	Application / SLD
Register model in Network	Network / Registry
Remove membership	Network / Registry
Bus index	BusIndex
Terminal-to-bus resolution	endpoint.py
Electrical connectivity	TopologyManager
Island detection	TopologyManager
Y-bus construction	YBusBuilder
Derived-state validity	NetworkState
Power-flow orchestration	Analysis
Power-flow numerical solution	Solver
Short-circuit orchestration	Analysis
Short-circuit numerical solution	Solver
Protection study	Analysis / Protection
SLD rendering	UI
SLD graphical interaction	UI
Electrical truth	Model + Network
Visual truth	SLD/UI
37. What the Network Layer Must Not Become

The following are explicitly outside this package:

CommandManager
Command objects
Undo/redo policy
Qt widgets
SLD graphics
Canvas interaction
Equipment palette
Property editor
Power-flow solver
Newton-Raphson implementation
Jacobian implementation
Short-circuit solver
Protection coordination
Transient integration
Plugin UI implementation

If functionality requires one of these responsibilities, it belongs
elsewhere.

38. Design Goal

The final Network Layer should remain small enough that an engineer
can understand its architecture without reading every electrical
model or numerical solver.

The desired relationship is:

                APPLICATION
                     │
                  Commands
                     │
                     ▼
                   MODEL
                     │
              canonical objects
                     │
                     ▼
                  NETWORK
          ┌──────────┼──────────┐
          │          │          │
       Registry    Topology    Y-Bus
          │          │          │
          └──────────┼──────────┘
                     ▼
                  ANALYSIS
                     │
                     ▼
                   SOLVER

The Network Layer is therefore an assembly and derived-state
boundary, not a general-purpose engineering computation layer.

39. Version
GridForge V2
Network Layer
Architecture baseline: 2.0
Author: Subhendu Mishra
Copyright © 2026
40. Final Architectural Rule

The most important rule of the Network Layer is:

The model is authoritative; the Network assembles it; topology and
Y-bus are derived; Application commands perform engineering
workflows; Analysis orchestrates studies; Solver performs numerical
computation.

No component in core/network should violate that boundary without
an explicit architectural decision.
