# GridForge V2 Network Layer

## Overview

The `core/network/` package provides the authoritative **electrical network representation and network-level numerical infrastructure** for GridForge V2.

The network layer bridges the physical/engineering model layer and the numerical solver layer.

Its primary responsibilities are:

* maintaining electrical topology;
* representing network connectivity;
* resolving buses, terminals, and branches;
* constructing the electrical network representation;
* maintaining the canonical per-unit network representation;
* constructing the system admittance matrix;
* providing network-level data required by analysis and solvers.

The fundamental principle is:

```text
Physical Model
      │
      ▼
  core.model
      │
      ▼
  core.network
      │
      ├── Topology
      ├── Per-Unit Representation
      └── Y-bus
      │
      ▼
 Analysis / Solver
```

The network layer describes **how physical equipment forms an electrical network**.

It does not become the owner of physical equipment, numerical study execution, protection logic, GUI state, or project persistence.

---

# 1. Architectural Position

The GridForge V2 network layer sits between the physical model and the numerical study/solver layers.

```text
                    Physical Digital Twin
                            │
                            ▼
                       core.model
                            │
                            ▼
                       core.network
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
       Topology          Per-Unit            Y-bus
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    Analysis / Solver
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         Power Flow    Short Circuit    Dynamics
```

The network layer is therefore a **derived electrical representation of the authoritative physical model**.

---

# 2. Core Architectural Principle

The fundamental V2 relationship is:

```text
Physical Equipment
       │
       ▼
     Model
       │
       ▼
   Electrical Network
       │
       ▼
 Numerical Representation
       │
       ▼
      Solver
```

The distinction is:

```text
core.model
    = What physical equipment exists

core.network
    = How that equipment forms an electrical network

core.solver
    = How a mathematical problem is solved
```

This separation is essential for maintaining a clean digital-twin architecture.

---

# 3. Package Structure

The current GridForge V2 network foundation is:

```text
core/
└── network/
    ├── __init__.py
    ├── network.py
    ├── topology.py
    ├── per_unit.py
    └── ybus.py
```

These modules establish the core network-layer contracts.

---

# 4. Module Responsibilities

## 4.1 `network.py`

Defines:

```text
Network
```

`Network` is the principal network-level container and orchestration object.

It provides access to the electrical network representation derived from the physical model.

Its responsibilities include:

* network registration;
* network-level entity access;
* topology integration;
* network state management;
* per-unit representation access;
* Y-bus access;
* network-level validation;
* coordination of network construction.

It does not become a power-flow solver.

It does not own protection execution.

It does not own GUI state.

---

# 5. `topology.py`

Defines the network topology infrastructure.

Topology answers:

> Which electrical entities are connected to which other electrical entities?

The fundamental relationship is:

```text
Equipment
    │
    ▼
Terminal
    │
    ▼
Electrical Connection
    │
    ▼
Bus / Network Node
```

Topology is concerned with connectivity, not numerical solution.

---

# 6. Terminal-Based Topology

GridForge V2 uses terminal-based physical connectivity.

The model layer provides physical terminals.

The network layer interprets those terminals to construct the electrical topology.

Conceptually:

```text
Equipment A
    │
 Terminal A
    │
    ▼
Network Topology
    │
    ▼
 Bus / Node
    │
    ▲
    │
 Terminal B
    │
Equipment B
```

This avoids embedding independent topology rules into every solver.

---

# 7. Topology vs Model

The model layer owns physical equipment and terminal relationships.

The network layer derives the electrical network topology from those relationships.

```text
core.model
     │
     ├── Bus
     ├── Terminal
     ├── Line
     ├── Transformer
     ├── Breaker
     └── Other Equipment
     │
     ▼
core.network.topology
     │
     ├── Nodes
     ├── Connectivity
     ├── Branch Relationships
     └── Electrical Adjacency
```

The network topology must not become a second independent physical model.

---

# 8. Topology and Switchgear

Switchgear state can affect electrical topology.

For example:

```text
Closed Breaker
      │
      ▼
Electrical Connection Exists
```

while:

```text
Open Breaker
      │
      ▼
Electrical Connection Interrupted
```

The important ownership boundary is:

```text
Breaker Model
    │
    └── Physical State

Network Topology
    │
    └── Electrical Interpretation of That State
```

The network layer interprets physical switchgear state when constructing the active electrical network.

It does not own the physical breaker.

---

# 9. Network Nodes and Buses

GridForge V2 uses buses as electrical network nodes.

Conceptually:

```text
Bus
 │
 ├── Terminal / Connection
 ├── Terminal / Connection
 ├── Terminal / Connection
 └── ...
```

The network layer resolves physical connectivity into an electrical node representation.

This representation is consumed by:

* power-flow solvers;
* short-circuit solvers;
* contingency analysis;
* dynamics;
* other electrical studies.

---

# 10. Network Identity

Network-level identifiers must remain deterministic and stable within the applicable network context.

The network layer must preserve the distinction between:

```text
Physical Equipment ID
        ≠
Network Node ID
        ≠
Numerical Matrix Index
```

For example:

```text
Physical Bus:
    BUS-001

Network Node:
    NODE-001

Numerical Index:
    0
```

The numerical index is an implementation detail.

It must not become the authoritative identity of the physical model.

---

# 11. Numerical Indexing

Numerical solvers require compact integer indexing.

The network layer may therefore provide deterministic mappings such as:

```text
Physical Bus ID
      │
      ▼
Network Node
      │
      ▼
Numerical Index
```

These mappings must be:

* deterministic;
* reproducible;
* internally consistent;
* independent of GUI ordering.

The mapping must not overwrite physical identifiers.

---

# 12. `per_unit.py`

Defines the canonical network-level per-unit representation.

GridForge V2 uses a multi-voltage per-unit architecture.

The purpose of the per-unit layer is to provide consistent electrical normalization across:

* buses;
* lines;
* transformers;
* generators;
* loads;
* shunts;
* fault calculations;
* network equations.

The per-unit system prevents individual solvers from implementing incompatible base-conversion logic.

---

# 13. Per-Unit Architecture

The conceptual flow is:

```text
Physical Equipment
       │
       ▼
Engineering Quantities
       │
       ▼
Per-Unit Base System
       │
       ▼
Canonical Per-Unit Values
       │
       ▼
Network / Solver
```

Voltage-base propagation and impedance-base transformations must follow one authoritative per-unit implementation.

---

# 14. Multi-Voltage Networks

GridForge V2 explicitly supports networks containing multiple voltage levels.

For example:

```text
400 kV
   │
   ▼
Transformer
   │
   ▼
132 kV
   │
   ▼
Transformer
   │
   ▼
33 kV
   │
   ▼
11 kV
```

The network layer must preserve correct electrical relationships across these voltage levels.

The per-unit system handles the appropriate base relationships.

Individual equipment models must not invent independent global voltage-base rules.

---

# 15. Per-Unit Ownership

The authoritative per-unit implementation belongs to the network/base numerical architecture.

The network layer should provide the canonical representation consumed by numerical solvers.

The following must be avoided:

```text
Power Flow
    └── own per-unit conversion

Short Circuit
    └── own per-unit conversion

Dynamics
    └── own per-unit conversion
```

Instead:

```text
                Canonical Per-Unit System
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Power Flow    Short Circuit    Dynamics
```

This ensures numerical consistency across studies.

---

# 16. `ybus.py`

Defines the system admittance matrix infrastructure.

The Y-bus represents the electrical network in matrix form.

Conceptually:

```text
Network Topology
       │
       ▼
Branch / Equipment Parameters
       │
       ▼
Per-Unit Representation
       │
       ▼
Y-bus Assembly
       │
       ▼
Sparse Network Matrix
```

The Y-bus is a **network-level mathematical representation**.

It is not part of the physical equipment model.

---

# 17. Y-bus Responsibilities

`ybus.py` is responsible for:

* admittance matrix construction;
* branch contributions;
* transformer contributions;
* shunt contributions;
* appropriate network-element stamping;
* sparse representation;
* deterministic matrix indexing;
* matrix updates/reconstruction as required.

It must not become responsible for:

* Newton-Raphson iteration;
* power-flow convergence;
* protection execution;
* GUI rendering;
* project persistence.

---

# 18. Sparse Y-bus

GridForge V2 is designed for large power-system networks.

The Y-bus architecture therefore favors sparse matrix representations.

Conceptually:

```text
Electrical Network
       │
       ▼
Y-bus Assembly
       │
       ▼
Sparse Matrix
       │
       ▼
Numerical Solver
```

The sparse representation is essential for scalable:

* power-flow studies;
* short-circuit studies;
* contingency analysis;
* dynamic simulations;
* future large-scale studies.

---

# 19. Y-bus and Solver Separation

A critical architectural boundary is:

```text
Y-bus
   ≠
Power-Flow Solver
```

The network layer provides the electrical matrix representation.

The solver consumes it.

```text
core.network.ybus
        │
        ▼
Y-bus
        │
        ▼
core.solver.power_flow
        │
        ▼
Newton / Hybrid / Other Numerical Method
```

The Y-bus module must not contain the complete power-flow iteration algorithm.

---

# 20. Network and Power Flow

The power-flow solver consumes the network representation.

The relationship is:

```text
Physical Model
      │
      ▼
Network
      │
      ├── Topology
      ├── Per-Unit
      └── Y-bus
      │
      ▼
Power-Flow Solver
      │
      ▼
Power-Flow Result
```

The network layer does not determine whether the solver uses:

* Newton-Raphson;
* trust-region methods;
* line search;
* Levenberg-Marquardt;
* continuation;
* other numerical strategies.

Those are solver concerns.

---

# 21. Network and Short Circuit

Short-circuit analysis also consumes the network representation.

```text
Network
   │
   ├── Topology
   ├── Per-Unit
   └── Electrical Parameters
   │
   ▼
Short-Circuit Solver
   │
   ▼
Fault Result
```

The network layer provides the electrical representation.

The short-circuit solver determines the fault solution.

---

# 22. Network and Dynamics

Dynamics studies consume network information together with dynamic equipment models.

```text
Network
   │
   ▼
Electrical Network Equations
   │
   ▼
Dynamics Solver
   │
   ▼
Time-Domain Solution
```

The network layer does not own:

* generator differential equations;
* AVR integration;
* governor integration;
* PSS integration;
* numerical time stepping.

Those belong to the dynamics solver.

---

# 23. Network and Contingency

Contingency studies may require temporary network modifications.

The architectural distinction is:

```text
Authoritative Network
        │
        ▼
Study / Contingency Case
        │
        ▼
Derived Network Condition
        │
        ▼
Solver
```

A contingency must not permanently corrupt the authoritative physical model simply because a study requires an outage.

Temporary study state should be represented through the appropriate study/network mechanism.

---

# 24. Network State

Network state must be distinguished from physical model state.

Examples of network-level state include:

* active topology;
* node mapping;
* branch connectivity;
* numerical indexing;
* Y-bus state;
* network-level derived quantities.

These are derived or network-specific representations.

They do not replace the authoritative physical model.

---

# 25. Network Caching

The network layer may cache derived numerical structures where beneficial.

Examples include:

* node mappings;
* branch mappings;
* Y-bus;
* sparse index structures;
* topology lookup tables.

However:

```text
Cache
   ≠
Authoritative Model State
```

Caches must be invalidated or rebuilt when their source network information changes.

Stale numerical caches must never silently override authoritative physical state.

---

# 26. Topology Changes

When topology-affecting equipment state changes, dependent network representations must be updated.

Conceptually:

```text
Breaker State Change
        │
        ▼
Topology Update
        │
        ▼
Network Representation Update
        │
        ▼
Y-bus / Derived Structures
        │
        ▼
Next Study / Solver Evaluation
```

The network layer is responsible for maintaining consistency among its derived representations.

It does not own the physical switchgear state.

---

# 27. Network Validation

The network layer performs network-level validation.

Examples include:

* invalid terminal connectivity;
* unresolved network nodes;
* invalid branch endpoints;
* inconsistent topology;
* invalid electrical connectivity;
* duplicate network identifiers;
* invalid network indexing;
* incompatible network structures.

Validation of physical equipment-specific parameters remains the responsibility of the model/domain layer.

Numerical preconditions remain the responsibility of the solver.

---

# 28. Model / Network / Solver Boundary

The three layers have deliberately different responsibilities:

| Layer          | Responsibility                                 |
| -------------- | ---------------------------------------------- |
| `core.model`   | Physical and engineering entities              |
| `core.network` | Electrical topology and network representation |
| `core.solver`  | Numerical solution                             |

The intended flow is:

```text
Model
  │
  ▼
Network
  │
  ▼
Solver
```

Never collapse these into one layer.

---

# 29. Network and Protection

Protection consumes authoritative electrical information but does not belong inside the network layer.

The relationship is:

```text
core.model
     │
     ▼
core.network
     │
     ▼
Electrical State
     │
     ▼
Measurement Infrastructure
     │
     ▼
core.protection
```

The network layer must not implement:

* relay pickup;
* relay operating time;
* relay trip logic;
* protection coordination;
* protection decisions.

---

# 30. Network and GUI

The network layer is completely independent of the GUI.

It must not depend on:

* PySide6;
* graphics scenes;
* views;
* renderers;
* GUI controllers;
* selection state;
* canvas state.

The intended relationship is:

```text
GUI
 │
 ▼
Controller / Application Layer
 │
 ▼
Network / Model
```

Never:

```text
Network
   │
   ▼
GUI
```

---

# 31. Network and Persistence

The network layer does not own project-file persistence.

It must not contain:

* file dialogs;
* filesystem paths;
* JSON project I/O;
* save/load workflows.

Persistence belongs to the dedicated serialization/project layer.

The persistence layer may serialize the authoritative model and required network configuration/state.

---

# 32. Deterministic Network Construction

Network construction must be deterministic.

Given identical authoritative model state and network configuration, the network layer should produce:

* identical node mappings;
* identical branch mappings;
* identical topology relationships;
* identical matrix indexing;
* equivalent Y-bus representation.

Deterministic ordering is especially important because numerical solvers rely on stable matrix indexing.

---

# 33. Network Identity vs Numerical Identity

GridForge V2 maintains strict identity separation:

```text
Asset ID
   ≠
Equipment ID
   ≠
Terminal ID
   ≠
Network Node ID
   ≠
Numerical Matrix Index
```

Each identifier has a distinct role.

A numerical index may change when a study representation is rebuilt.

The physical identity must not change as a consequence.

---

# 34. Network Construction Flow

A typical network construction process is:

```text
1. Read authoritative model
             │
             ▼
2. Resolve physical terminals
             │
             ▼
3. Resolve electrical nodes
             │
             ▼
4. Determine active topology
             │
             ▼
5. Establish deterministic indices
             │
             ▼
6. Apply canonical per-unit representation
             │
             ▼
7. Assemble Y-bus
             │
             ▼
8. Validate network representation
             │
             ▼
9. Publish network representation
```

This network representation is then consumed by the appropriate analysis and solver subsystems.

---

# 35. Network Update Flow

For topology-affecting changes:

```text
Physical / Control State Change
             │
             ▼
      Network Invalidation
             │
             ▼
       Topology Rebuild
             │
             ▼
       Index Resolution
             │
             ▼
       Y-bus Rebuild
             │
             ▼
      Updated Network State
```

The implementation may optimize this process through incremental updates where safe.

Optimization must not compromise correctness.

---

# 36. Numerical Consistency

The network layer is a major numerical consistency boundary.

The same network should produce consistent representations for:

* power flow;
* short circuit;
* contingency;
* dynamics;
* future electrical studies.

This requires consistent:

* topology;
* voltage bases;
* per-unit conversion;
* equipment interpretation;
* branch orientation;
* transformer representation;
* shunt representation;
* matrix indexing.

---

# 37. Transformer Representation

Transformers require special attention because they connect different voltage levels and may include:

* turns ratios;
* phase shifts;
* impedance;
* tap settings;
* winding configuration.

The model provides transformer engineering information.

The network layer converts that information into the appropriate network representation.

The Y-bus layer performs the corresponding matrix stamping.

The solver then consumes the resulting matrix.

```text
Transformer Model
       │
       ▼
Network Transformer Representation
       │
       ▼
Y-bus Stamp
       │
       ▼
Solver
```

---

# 38. Branch Orientation

Network branch representation should maintain deterministic endpoint ordering.

For example:

```text
Branch
  ├── from_node
  └── to_node
```

The orientation is a network representation convention.

It must not alter the physical identity or imply that the underlying equipment is physically directional unless the equipment model explicitly has such semantics.

---

# 39. Network-Level Electrical Quantities

The network layer may expose derived electrical quantities required by downstream studies.

Examples include:

* node connectivity;
* branch connectivity;
* network admittance;
* network impedance relationships;
* electrical islands;
* active/inactive branches;
* node mappings.

Study-specific quantities such as final power-flow voltages or fault currents should remain solver/analysis results.

---

# 40. Electrical Islands

Network topology may result in electrically disconnected islands.

The network layer should be capable of identifying relevant connectivity conditions.

Conceptually:

```text
Grid
 │
 ├── Island A
 │
 ├── Island B
 │
 └── Island C
```

Island detection is a network/topology concern.

The numerical solver determines whether and how each island can be solved.

---

# 41. Network Caches and Invalidations

Derived structures must have explicit dependency relationships.

For example:

```text
Physical Topology
      │
      ▼
Node Mapping
      │
      ▼
Branch Mapping
      │
      ▼
Y-bus
```

If topology changes:

```text
Topology Changed
      │
      ├── invalidate node mapping
      ├── invalidate branch mapping
      └── invalidate Y-bus
```

If only a parameter affecting Y-bus changes, the implementation may invalidate only the dependent structures where safe.

The architecture must always favor correctness over premature optimization.

---

# 42. Architectural Invariants

The following invariants must be preserved throughout GridForge V2.

## 42.1 Model Is the Physical Authority

```text
core.model
    =
Physical / Engineering Authority
```

The network layer must not become a second physical equipment database.

---

## 42.2 Network Is the Electrical Representation

```text
core.network
    =
Electrical Network Representation
```

It translates physical model relationships into network-level electrical structures.

---

## 42.3 Solver Is the Numerical Executor

```text
core.solver
    =
Numerical Execution
```

The network layer does not perform complete numerical study algorithms.

---

## 42.4 Topology Is Explicit

Electrical connectivity must be represented explicitly through terminals, nodes, branches, and network relationships.

---

## 42.5 Per-Unit Representation Is Canonical

Individual solvers must not independently redefine the network's per-unit base system.

---

## 42.6 Y-bus Is a Network Representation

```text
Y-bus
   ≠
Power-Flow Solver
```

The matrix is supplied to numerical consumers.

---

## 42.7 Numerical Indices Are Not Physical IDs

Numerical indexing is derived implementation state.

---

## 42.8 Derived Caches Are Not Authoritative

Topology caches, node maps, and Y-bus matrices must never silently override source model state.

---

## 42.9 Topology Changes Must Propagate

Any topology-affecting state change must invalidate or update dependent network representations.

---

## 42.10 GUI Is Outside the Network Core

No network object may depend on GUI state or services.

---

## 42.11 Persistence Is Outside the Network Core

Network objects do not perform project-file I/O.

---

## 42.12 Protection Is Outside the Network Core

Network representation provides electrical information.

Protection execution remains in `core.protection`.

---

# 43. Dependency Direction

The intended dependency direction is:

```text
core.model
     │
     ▼
core.network
     │
     ├── topology
     ├── per_unit
     └── ybus
     │
     ▼
core.analysis / core.solver
     │
     ├── power_flow
     ├── short_circuit
     ├── dynamics
     └── contingency
```

The network layer must remain below the numerical solver layer and above the physical model layer.

---

# 44. Public Network API

The package should expose stable network contracts through:

```python
from core.network import ...
```

The public API should contain canonical network abstractions such as:

* `Network`;
* topology interfaces;
* per-unit interfaces;
* Y-bus interfaces;
* stable network-level data structures.

Implementation-specific internals should not automatically become public API.

---

# 45. Network Reusability

A single authoritative network representation should support multiple study types.

Conceptually:

```text
                  Network
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   Power Flow   Short Circuit   Dynamics
        │            │            │
        ▼            ▼            ▼
      Result       Result       Result
```

This prevents each study from creating an incompatible interpretation of the same physical network.

---

# 46. Performance Architecture

GridForge V2 is intended for large-scale power-system analysis.

The network layer should therefore support efficient:

* topology lookup;
* node indexing;
* branch lookup;
* sparse Y-bus construction;
* incremental invalidation;
* vectorized numerical preparation;
* repeated study execution.

Performance optimizations must preserve the authoritative ownership model.

---

# 47. Future Expansion

The network architecture is intentionally prepared for future capabilities including:

* multi-island analysis;
* topology reduction;
* network equivalents;
* Kron reduction;
* dynamic network reduction;
* adaptive network partitioning;
* large-scale sparse matrix optimization;
* parallel network assembly;
* GPU-compatible matrix preparation;
* real-time network updates;
* contingency-specific network snapshots.

These capabilities should extend the network representation without moving solver responsibilities into the network layer.

---

# 48. Design Philosophy

GridForge V2 treats `core/network/` as the **electrical interpretation layer of the digital twin**.

The network layer answers:

> Given the authoritative physical model, what electrical network exists, how is it connected, what are its electrical parameters, and what mathematical network representation should downstream studies consume?

It does not answer:

> What equipment physically exists?

That belongs to `core/model`.

It does not answer:

> How should the nonlinear equations be solved?

That belongs to `core/solver`.

It does not answer:

> What protection function should operate?

That belongs to `core/protection`.

It does not answer:

> How should the network be displayed?

That belongs to the GUI/application layer.

The resulting architecture is:

```text
                 Physical Digital Twin
                         │
                         ▼
                    core.model
                         │
                         ▼
                   core.network
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
       Topology       Per-Unit         Y-bus
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Analysis / Solver
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Power Flow    Short Circuit    Dynamics
```

---

# 49. Current Foundation Status

The GridForge V2 Network Layer is a **frozen foundational subsystem**.

The current canonical network foundation is:

```text
core/network/
├── __init__.py
├── network.py
├── topology.py
├── per_unit.py
└── ybus.py
```

The Network Layer V1.0 baseline establishes:

* terminal-aware electrical topology;
* deterministic network representation;
* canonical per-unit infrastructure;
* multi-voltage network support;
* Y-bus construction;
* sparse matrix representation;
* network-to-solver separation;
* explicit physical-model/network boundaries.

The network layer is considered a stable foundation for the higher-level GridForge analysis and solver architecture.

---

# 50. Freeze Status

**`core/network/README.md` → FINALIZE / FREEZE**

This document is the package-level architectural reference for the GridForge V2 Network Layer.

Future network changes should:

1. preserve the model/network/solver separation;
2. preserve terminal-based connectivity;
3. preserve deterministic node and branch indexing;
4. preserve the canonical per-unit architecture;
5. preserve the Y-bus contract;
6. preserve sparse numerical representation;
7. preserve explicit topology invalidation/update behavior;
8. prevent derived network caches from becoming authoritative physical state;
9. keep GUI and persistence outside the network layer;
10. keep protection execution outside the network layer.

The guiding rule is:

```text
Preserve the electrical network architecture.
Improve representation and performance without changing ownership boundaries.
```

---

# 51. Final Architectural Summary

The GridForge V2 Network Layer is based on five fundamental separations:

```text
Physical Model
       ≠
Electrical Network
```

```text
Electrical Network
       ≠
Numerical Solver
```

```text
Physical Identity
       ≠
Numerical Index
```

```text
Network Representation
       ≠
Study Result
```

```text
Network Topology
       ≠
Protection Logic
```

The final architectural flow is:

```text
                     Physical Model
                           │
                           ▼
                    Terminal Relationships
                           │
                           ▼
                      Network Topology
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
          Per-Unit System             Nodes
               │                       │
               └───────────┬───────────┘
                           ▼
                         Y-bus
                           │
                           ▼
                  Numerical Solvers
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Power Flow      Short Circuit      Dynamics
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     Study Results
```

The network layer therefore provides the stable electrical foundation between the physical GridForge digital twin and its numerical analysis engines.

**`core/network/README.md` → FINALIZE / FREEZE**
