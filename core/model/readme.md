# GridForge V2 Model Layer

## Overview

The `core/model/` package defines the authoritative physical and engineering-domain model for GridForge V2.

The model layer represents the entities that constitute the GridForge digital twin:

* buses and terminals;
* branches and electrical connections;
* lines and cables;
* transformers;
* generators;
* loads;
* motors;
* shunts;
* switchgear;
* measurement and protection equipment;
* grid and graph containers;
* model state and related engineering metadata.

The model layer is intentionally separated from numerical solvers, analysis engines, protection execution, dynamics simulation, GUI state, and project persistence.

The fundamental principle is:

```text
Physical / Engineering Model
             │
             ▼
          core/model
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
   Network  Analysis  Solver
```

The model layer describes **what the system is**.

Other subsystems determine **what the system does under a particular study or simulation**.

---

# 1. Architectural Position

The model layer is the physical-domain foundation of GridForge V2.

```text
                    GridForge Digital Twin
                            │
                            ▼
                       core/model
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     Physical Assets   Engineering Data   Topology
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         Network         Analysis        Solver
             │              │              │
             ▼              ▼              ▼
          Y-bus         Study Logic    Numerical Execution
```

The model layer is authoritative for the physical and engineering objects it represents.

It does not become the owner of numerical study state merely because a solver consumes model objects.

---

# 2. Core Model Principle

GridForge V2 deliberately avoids creating a rigid universal inheritance hierarchy such as:

```text
Asset
  └── Equipment
        └── Component
              └── Device
```

Instead, the terms have **semantic engineering meanings**.

They are classifications used to describe different aspects of the digital twin rather than mandatory Python inheritance relationships.

The distinction is:

```text
Asset
    = Persistent uniquely identifiable entity tracked by the Digital Twin

Equipment
    = Engineered physical apparatus

Component
    = Engineering-significant constituent part of equipment

Device
    = Independently identifiable functional apparatus/element
      participating in one or more engineering domains
```

These classifications must not be converted into a giant mandatory class hierarchy.

Specialized engineering implementations may use appropriate inheritance where it provides genuine technical value.

---

# 3. Model Layer Responsibilities

`core/model/` is responsible for representing:

* physical equipment;
* electrical connectivity;
* engineering parameters;
* equipment identity;
* terminals;
* electrical branches;
* injections;
* equipment-specific state;
* physical switchgear;
* measurement equipment;
* protection-related physical equipment;
* grid/container relationships;
* topology-oriented model relationships.

The model layer should provide authoritative domain objects that can be consumed by other GridForge subsystems.

---

# 4. What the Model Layer Does Not Do

The model layer does **not** own:

* Newton-Raphson execution;
* Y-bus numerical assembly;
* power-flow solving;
* short-circuit solving;
* transient-stability solving;
* EMT simulation;
* protection-function execution;
* protection coordination;
* relay decision execution;
* GUI state;
* rendering;
* project-file persistence;
* study orchestration.

These responsibilities belong to dedicated GridForge subsystems.

The separation is intentional.

---

# 5. Package Structure

The finalized model-layer inventory is:

```text
core/
└── model/
    ├── __init__.py
    ├── base.py
    ├── branch.py
    ├── breaker.py
    ├── bus.py
    ├── cable.py
    ├── CT/CVT
    ├── disconnector.py
    ├── fuse.py
    ├── generator.py
    ├── graph.py
    ├── grid.py
    ├── injection.py
    ├── line.py
    ├── load.py
    ├── motor.py
    ├── PT.py
    ├── relay.py
    ├── shunt.py
    ├── state.py
    ├── terminal.py
    └── transformer.py
```

The exact Python module names for CT/CVT and PT implementations remain subject to the repository's canonical naming conventions.

The important architectural point is that these objects belong to the model layer because they represent physical or engineering-domain entities.

---

# 6. `base.py`

`base.py` provides the common model-layer foundation shared by appropriate model entities.

Its purpose is to establish common domain-level behavior without forcing unrelated equipment into an artificial inheritance structure.

Common concerns may include:

* identity;
* model metadata;
* validation hooks;
* common engineering attributes;
* lifecycle-related model information.

The base layer must remain lightweight.

It must not become a universal container for solver, GUI, persistence, or protection behavior.

---

# 7. `terminal.py`

`Terminal` is a fundamental electrical connection abstraction.

GridForge V2 uses **terminal-based physical connectivity**.

Conceptually:

```text
Equipment
   │
   ├── Terminal A
   │
   └── Terminal B
```

Terminals provide the explicit connection points through which equipment participates in electrical topology.

This is preferred over embedding ad-hoc connection references directly into every equipment class.

The terminal model provides the foundation for consistent physical connectivity across:

* lines;
* cables;
* transformers;
* breakers;
* disconnectors;
* fuses;
* generators;
* loads;
* motors;
* other terminal-bearing equipment.

---

# 8. `branch.py`

`Branch` provides the common two-terminal representation for branch-type electrical equipment.

The architectural concept is:

```text
Terminal A ───── Branch ───── Terminal B
```

Branch is a common representation of a two-terminal electrical connection.

Specialized equipment such as lines, cables, and transformers may provide their engineering-specific parameters while retaining the common branch concept.

`Branch` must not become a numerical solver object.

It describes the physical/electrical model.

Numerical admittance or Jacobian construction belongs to the network and solver layers.

---

# 9. `injection.py`

`Injection` provides the common model abstraction for equipment that injects or consumes electrical power at a network location.

Its important contract is:

```python
get_power() -> (P, Q)
```

Conceptually:

```text
Injection
   │
   ├── Generator
   ├── Load
   └── Other injection-type models
```

The model provides engineering power information.

It does not perform power-flow solution.

For example:

```text
Generator
    │
    └── provides model power characteristics

Load
    │
    └── provides model demand characteristics
```

The solver interprets these model quantities during numerical execution.

---

# 10. `bus.py`

`Bus` represents a network electrical node and associated model/state information.

The Bus is primarily a **node/state holder**.

It provides the physical/network model representation required by GridForge's network and solver layers.

The Bus should not become responsible for:

* constructing the Y-bus;
* solving power flow;
* solving short circuit;
* executing protection;
* performing dynamics integration.

Those responsibilities remain outside `core/model/`.

The public `BusType` is part of the model-layer API.

---

# 11. `line.py`

`Line` represents physical transmission/distribution line equipment.

A line is a specialized branch-type model.

Conceptually:

```text
Terminal A
    │
    ▼
   Line
    │
    ▼
Terminal B
```

The line model owns engineering parameters associated with the physical line.

It does not perform:

* load-flow calculations;
* short-circuit calculations;
* Y-bus assembly;
* numerical solution.

Those operations consume the line model through the network/solver layers.

---

# 12. `cable.py`

`Cable` represents underground or other cable-based electrical equipment.

Like a line, a cable participates in the branch abstraction where appropriate.

The cable model contains engineering parameters required to describe the physical cable.

Numerical interpretation belongs to the network and solver layers.

---

# 13. `transformer.py`

`Transformer` represents physical transformer equipment.

The transformer model is responsible for engineering information such as:

* winding configuration;
* rated quantities;
* impedance-related parameters;
* voltage ratios;
* terminal relationships;
* transformer-specific metadata.

It does not own the numerical transformer admittance implementation used by a solver.

The solver/network layer interprets the transformer model.

---

# 14. `generator.py`

`Generator` represents physical generator equipment and its model-level engineering state.

The generator model provides the physical and engineering information required by:

* network construction;
* power-flow analysis;
* short-circuit analysis;
* dynamics models;
* other applicable studies.

The generator model itself does not become the numerical implementation of:

* governor;
* AVR;
* PSS;
* transient stability;
* EMT.

Those dynamic implementations belong to the appropriate solver/plugin architecture.

This preserves the distinction:

```text
Generator Model
      ≠
Generator Dynamic Simulation
```

---

# 15. `load.py`

`Load` represents physical/electrical load equipment.

It provides the model-level representation of demand and associated engineering parameters.

Its power behavior is exposed through the appropriate injection contract.

The load model does not execute a numerical power-flow algorithm.

---

# 16. `motor.py`

`Motor` represents motor load equipment.

A motor is an engineering-domain model that may participate in:

* network studies;
* load-flow studies;
* short-circuit studies;
* dynamics studies.

The model describes the motor.

Study-specific numerical behavior remains the responsibility of the appropriate solver or analysis subsystem.

---

# 17. `shunt.py`

`Shunt` represents shunt-connected electrical equipment.

The model contains its physical and engineering parameters.

The network and numerical layers interpret those parameters when constructing the appropriate mathematical representation.

The Shunt model must not directly construct or modify a solver matrix.

---

# 18. Switchgear Models

The model layer contains physical switchgear entities such as:

```text
Breaker
Disconnector
Fuse
```

These represent physical apparatus.

Their physical state and engineering attributes belong to the model layer.

However:

```text
Physical Switchgear
        ≠
Protection Logic
```

and:

```text
Physical Breaker
        ≠
Breaker Control Orchestration
```

For example, protection logic may produce a trip request, but the protection function must not directly manipulate the physical breaker object.

The control/output layer and `BreakerManager` provide the appropriate orchestration boundary.

---

# 19. `breaker.py`

`Breaker` represents the physical circuit-breaker model.

It is responsible for representing the equipment itself, including appropriate physical/topological state.

The breaker model must remain independent of:

* GUI interaction;
* relay algorithms;
* protection coordination;
* solver execution;
* rendering.

Breaker topology and terminal behavior must remain consistent with the terminal-based model architecture.

---

# 20. `disconnector.py`

`Disconnector` represents physical disconnector/switchgear equipment.

It is an equipment model rather than a protection-control algorithm.

Its physical state may influence network topology through the appropriate network/control mechanisms, but the model itself does not execute network solving.

---

# 21. `fuse.py`

`Fuse` represents physical fuse equipment.

The fuse model belongs to the physical equipment layer.

Any future fuse protection characteristic or coordination study should be implemented through appropriate protection/analysis functionality rather than embedding a complete protection-study engine into the model class.

---

# 22. Measurement Equipment

The model layer may contain engineering entities representing:

* CT;
* PT;
* CVT;
* Relay.

These are physical/engineering objects.

They must remain distinct from the measurement infrastructure and protection execution layers.

The conceptual separation is:

```text
Physical CT / PT / CVT
          │
          ▼
Measurement Infrastructure
          │
          ▼
MeasurementChannel
          │
          ▼
Protection Input
          │
          ▼
Protection Function
```

Similarly:

```text
Physical Relay
      │
      ▼
ProtectionElement
      │
      ▼
Protection Function
```

A physical Relay is therefore not itself a `RelayBase` protection function.

---

# 23. `relay.py`

`Relay` represents the physical/engineering relay equipment.

It is intentionally separate from the protection execution architecture.

The distinction is:

```text
core.model.relay.Relay
        =
Physical Relay Equipment
```

while:

```text
core.protection.RelayBase
        =
Executable Protection Function
```

A single physical Relay may host multiple protection elements:

```text
Physical Relay RLY-001
        │
        ├── ProtectionElement → 50
        ├── ProtectionElement → 51
        ├── ProtectionElement → 67
        └── ProtectionElement → 50BF
```

This distinction is fundamental to the GridForge V2 architecture.

---

# 24. CT / PT / CVT Models

CT, PT, and CVT models represent physical measurement equipment.

They do not replace `MeasurementChannel`.

The architectural separation is:

```text
Physical Instrument
        │
        ▼
Measurement Infrastructure
        │
        ▼
MeasurementChannel
        │
        ▼
Protection / Analysis Consumers
```

The physical instrument model and measurement-state infrastructure therefore have distinct responsibilities.

---

# 25. `state.py`

`state.py` provides model-level state representations where appropriate.

State must be distinguished from:

* numerical solver state;
* protection runtime state;
* GUI state;
* persistence state.

The model state represents authoritative domain state.

Study-specific transient state should remain owned by the corresponding analysis/simulation subsystem.

---

# 26. `graph.py`

`Graph` provides graph/topology-oriented infrastructure for the model layer.

It exists to represent relationships among model entities.

It is not a replacement for the dedicated network subsystem.

The distinction is:

```text
core.model.graph
        │
        └── Model / relationship representation

core.network
        │
        └── Electrical network construction and numerical topology
```

The model graph should therefore remain lightweight and domain-oriented.

---

# 27. `grid.py`

`Grid` provides a higher-level model container for the physical system.

It may organize model entities such as:

* buses;
* branches;
* injections;
* equipment;
* terminals;
* grid-level relationships.

`Grid` is a model/container concept.

It is not itself:

* a power-flow solver;
* a short-circuit solver;
* a dynamics engine;
* a protection engine;
* a GUI document.

---

# 28. Model vs Network

A critical V2 boundary exists between:

```text
core.model
```

and:

```text
core.network
```

The model layer represents the authoritative physical/engineering entities.

The network layer derives the electrical network representation required for network analysis and numerical operations.

Conceptually:

```text
Physical Model
     │
     ▼
  core.model
     │
     ▼
  core.network
     │
     ├── topology
     ├── per-unit representation
     ├── Y-bus
     └── network-level structures
     │
     ▼
 Solvers / Analysis
```

The model layer must not duplicate network numerical infrastructure.

---

# 29. Model vs Solver

The model provides inputs to numerical solvers.

It does not perform the numerical solution.

The intended relationship is:

```text
Model
  │
  ▼
Network / Analysis Representation
  │
  ▼
Solver
  │
  ▼
Numerical Result
```

Examples:

```text
Generator Model
       │
       ▼
Power Flow Solver
```

```text
Line Model
       │
       ▼
Short-Circuit Solver
```

```text
Generator + Dynamic Models
       │
       ▼
Dynamics Solver
```

The model remains reusable across different study types.

---

# 30. Model vs Protection

The physical Relay, CT, PT, and CVT models reside in the engineering/model domain.

Protection execution resides in `core/protection`.

The relationship is:

```text
Physical Model
     │
     ├── Relay
     ├── CT
     ├── PT
     └── CVT
     │
     ▼
Measurement / Protection Infrastructure
     │
     ▼
Protection Functions
```

The model layer must not absorb protection-function algorithms.

---

# 31. Model vs GUI

The model layer is completely independent of the GUI.

Model objects must not depend on:

* PySide6 widgets;
* graphics items;
* views;
* controllers;
* rendering systems;
* GUI selection state;
* GUI modes.

The GUI consumes and manipulates model objects through appropriate application/controller boundaries.

```text
GUI
 │
 ▼
Controller / Application Layer
 │
 ▼
Model
```

Never:

```text
Model
 │
 ▼
GUI
```

---

# 32. Model vs Persistence

The model layer is not responsible for project-file I/O.

Persistence belongs to the dedicated serialization/project layer.

The intended architecture is:

```text
GUI
 │
 ▼
Persistence / Project Layer
 │
 ▼
Model
 │
 ▼
Registered Core Objects
```

The model should not contain:

* JSON file handling;
* file dialogs;
* filesystem paths;
* GUI save/load operations.

Serialization should operate against authoritative model objects.

---

# 33. Terminal-Based Connectivity

Terminal-based connectivity is a fundamental GridForge V2 invariant.

Physical equipment connects through explicit terminals.

```text
Equipment A
    │
 Terminal
    │
    ├──────── Connection ────────┐
    │                            │
 Terminal                    Terminal
    │                            │
Equipment B                  Equipment C
```

This architecture supports consistent representation of:

* simple two-terminal equipment;
* multi-terminal equipment;
* switchgear;
* transformers;
* future specialized equipment.

It also avoids embedding incompatible topology assumptions into individual equipment models.

---

# 34. Physical State vs Study State

GridForge V2 distinguishes physical/model state from study-specific runtime state.

```text
Physical Model State
        ≠
Power Flow State
        ≠
Short-Circuit State
        ≠
Dynamics Runtime State
        ≠
Protection Runtime State
```

The model provides authoritative physical information.

Each study subsystem owns its own transient computational state.

This prevents cross-subsystem state contamination.

---

# 35. Model Layer Invariants

The following invariants must be preserved.

### 35.1 Model Objects Represent Domain Entities

Model classes represent physical or engineering-domain concepts.

They must not become general-purpose containers for unrelated subsystem logic.

### 35.2 Terminals Are the Physical Connection Boundary

Equipment connectivity is represented through terminals.

### 35.3 Branch Is the Common Two-Terminal Abstraction

Lines, cables, and other appropriate branch equipment share the common branch concept.

### 35.4 Injection Provides the Common Power Interface

Injection-type models expose:

```python
get_power() -> (P, Q)
```

### 35.5 Bus Is a Node / State Holder

Bus does not become a numerical solver.

### 35.6 Switchgear Is Physical Equipment

Breaker, disconnector, and fuse models represent physical apparatus.

They do not become protection orchestration engines.

### 35.7 Measurement Equipment Is Distinct from Measurement Infrastructure

CT/PT/CVT models do not replace `MeasurementChannel`.

### 35.8 Physical Relay Is Distinct from Protection Function

```text
Relay Model
    ≠
RelayBase
```

### 35.9 No Mandatory Asset Hierarchy

The semantic categories:

```text
Asset
Equipment
Component
Device
```

must not be implemented as a mandatory universal inheritance tree.

### 35.10 Numerical Solving Is Outside the Model Layer

No Y-bus construction, Newton-Raphson execution, short-circuit solution, or dynamics integration belongs in model classes.

### 35.11 Protection Execution Is Outside the Model Layer

Protection algorithms, decisions, coordination, and trip logic belong to the protection/control architecture.

### 35.12 GUI Is Outside the Model Layer

No model object may depend on GUI implementation.

### 35.13 Persistence Is Outside the Model Layer

Model classes must not own project-file serialization or filesystem operations.

---

# 36. Dependency Direction

The intended dependency direction is:

```text
core.model
     │
     ▼
core.network
     │
     ├───────────────┐
     ▼               ▼
core.analysis    core.solver
     │               │
     │        ┌──────┼──────────┐
     │        ▼      ▼          ▼
     │    power_flow short_circuit dynamics
     │
     ▼
Study Results
```

Protection has its own architecture:

```text
core.model
     │
     ▼
Measurement Infrastructure
     │
     ▼
core.protection
```

The model layer remains at the physical/domain foundation.

---

# 37. Extensibility

The model layer is intended to support future specialized engineering domains without destabilizing the foundational architecture.

Potential extensions include:

* specialized generator models;
* advanced transformer models;
* renewable generation equipment;
* inverter-based resources;
* FACTS equipment;
* energy-storage systems;
* advanced switchgear;
* specialized measurement equipment;
* railway electrical equipment;
* industrial plant equipment.

New equipment should be introduced according to its engineering semantics.

A new domain model should not automatically require modification of the entire model hierarchy.

---

# 38. Interaction with Plugins

GridForge V2 permits specialized engineering implementations to be supplied through appropriate plugin mechanisms.

Plugins may provide specialized domain models where required.

However, plugin implementations must respect the core model contracts.

The core model must remain:

* stable;
* domain-oriented;
* solver-independent;
* GUI-independent;
* persistence-independent.

---

# 39. Public Model API

The model package should expose stable, intentionally selected public contracts through:

```python
from core.model import ...
```

Public exports should represent canonical model-layer concepts.

Internal implementation details should not automatically become public API.

`BusType` is part of the public model API.

---

# 40. Design Philosophy

GridForge V2 treats the model layer as the **authoritative engineering description of the digital twin**.

The model answers:

> What physical and engineering entities exist, how are they identified, what are their engineering properties, and how are they physically connected?

It does not answer:

> How does the numerical solver solve the network?

or:

> How does a protection relay execute?

or:

> How does the GUI render the system?

Those questions belong to other layers.

The resulting architecture is:

```text
                 DIGITAL TWIN
                      │
                      ▼
                Physical Model
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
          Equipment         Topology
              │                │
              └───────┬────────┘
                      │
                      ▼
                 core.model
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     Network       Analysis       Protection
        │             │             │
        ▼             ▼             ▼
     Solvers       Study Logic   Protection
        │                           Logic
        └─────────────┬─────────────┘
                      ▼
                 Study Results
```

---

# 41. Current Foundation Status

The GridForge V2 Model Layer has completed its architectural audit and is treated as a **frozen foundation**.

The finalized model inventory includes:

```text
core/model/
├── __init__.py
├── base.py
├── branch.py
├── breaker.py
├── bus.py
├── cable.py
├── CT/CVT
├── disconnector.py
├── fuse.py
├── generator.py
├── graph.py
├── grid.py
├── injection.py
├── line.py
├── load.py
├── motor.py
├── PT.py
├── relay.py
├── shunt.py
├── state.py
├── terminal.py
└── transformer.py
```

The V2 model-layer audit established the following architectural baseline:

* terminal-based physical connections;
* `Branch` as the common two-terminal representation;
* `Injection` providing `get_power() -> (P, Q)`;
* `Bus` as a node/state holder;
* switchgear represented as physical equipment;
* CT/PT/CVT/Relay represented as engineering entities;
* Grid/Graph retained as model/container and topology infrastructure;
* no mandatory `Asset → Equipment → Component → Device` inheritance tree;
* numerical solving outside the model layer;
* protection execution outside the model layer;
* dynamics execution outside the model layer;
* GUI outside the model layer;
* persistence outside the model layer.

---

# 42. Freeze Status

**`core/model/README.md` → FINALIZE / FREEZE**

This document is the package-level architectural reference for the GridForge V2 Model Layer.

The model layer should be treated as a stable foundation.

Future changes should:

1. preserve the model-layer invariants;
2. preserve terminal-based connectivity;
3. preserve the distinction between physical models and numerical execution;
4. preserve the distinction between physical Relay equipment and protection functions;
5. avoid introducing duplicate ownership of state;
6. avoid unnecessary hierarchy expansion;
7. avoid coupling the model to GUI, persistence, protection execution, or solver internals.

The guiding rule for future model changes is:

```text
Preserve the frozen architecture.
Repair genuine contradictions.
Do not invent structure without a fundamental requirement.
```

---

# 43. Final Architectural Summary

The GridForge V2 model layer is built around the following separation:

```text
Physical Entity
       │
       ▼
    Model Object
       │
       ▼
   Network / Study
       │
       ▼
 Numerical / Protection / Dynamic Execution
```

The essential relationships are:

```text
Terminal
   │
   └── Physical Connectivity

Branch
   │
   └── Common Two-Terminal Equipment

Injection
   │
   └── get_power() → (P, Q)

Bus
   │
   └── Network Node / State Holder

Relay
   │
   └── Physical Protection Equipment

CT / PT / CVT
   │
   └── Physical Measurement Equipment

Breaker / Disconnector / Fuse
   │
   └── Physical Switchgear

Grid / Graph
   │
   └── Model / Relationship Containers
```

The model layer therefore provides the stable physical and engineering foundation upon which the rest of GridForge V2 operates.

```text
                    GridForge V2
                         │
                         ▼
                    core/model
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
      Model           Network          Studies
        │                │                │
        │                ▼                ├── Power Flow
        │             Y-bus               ├── Short Circuit
        │                                 └── Dynamics
        │
        └──────────────────────┐
                               ▼
                         Protection
                               │
                               ▼
                         Control / Output
```

**`core/model/` is the authoritative physical/engineering model layer of GridForge V2.**
