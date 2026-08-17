# ⚡ GridForge

## Power-System Digital Twin & Simulation Platform

GridForge is a modular power-system engineering platform for **electrical modeling, network analysis, numerical simulation, protection, visualization, validation, and future digital-twin applications**.

GridForge V2 is designed around a fundamental engineering principle:

> **Represent engineering truth once, derive specialized representations from it, execute studies through independent numerical services, and keep visualization and persistence outside the authoritative engineering core.**

The platform is intended to evolve from an engineering analysis environment into a comprehensive digital representation of electrical power systems capable of supporting steady-state studies, fault analysis, contingency analysis, dynamic simulation, protection studies, and future real-time digital-twin applications.

---

## Table of Contents

1. [Vision](#1-vision)
2. [Core Architectural Principle](#2-core-architectural-principle)
3. [GridForge V2 Architecture](#3-gridforge-v2-architecture)
4. [Repository Structure](#4-repository-structure)
5. [Core Architecture](#5-core-architecture)
6. [Physical Model](#6-physical-model)
7. [Asset, Equipment, Component and Device Semantics](#7-asset-equipment-component-and-device-semantics)
8. [Electrical Network](#8-electrical-network)
9. [Analysis Layer](#9-analysis-layer)
10. [Solver Architecture](#10-solver-architecture)
11. [Power Flow](#11-power-flow)
12. [Short-Circuit Analysis](#12-short-circuit-analysis)
13. [Dynamic Simulation](#13-dynamic-simulation)
14. [Protection Architecture](#14-protection-architecture)
15. [Measurement Architecture](#15-measurement-architecture)
16. [Protection Decision Boundary](#16-protection-decision-boundary)
17. [Simulation Architecture](#17-simulation-architecture)
18. [Validation](#18-validation)
19. [GUI Architecture](#19-gui-architecture)
20. [GUI and Core Separation](#20-gui-and-core-separation)
21. [Qt Architecture](#21-qt-architecture)
22. [Multi-Canvas Architecture](#22-multi-canvas-architecture)
23. [Bus-Centric Network Editing](#23-bus-centric-network-editing)
24. [Rendering Architecture](#24-rendering-architecture)
25. [Interaction Architecture](#25-interaction-architecture)
26. [Plugin Architecture](#26-plugin-architecture)
27. [Persistence Architecture](#27-persistence-architecture)
28. [Digital-Twin State Ownership](#28-digital-twin-state-ownership)
29. [Identity Architecture](#29-identity-architecture)
30. [Determinism](#30-determinism)
31. [Performance](#31-performance)
32. [CPU / GPU Backend Independence](#32-cpu--gpu-backend-independence)
33. [Headless Operation](#33-headless-operation)
34. [Testing Strategy](#34-testing-strategy)
35. [Engineering Regression](#35-engineering-regression)
36. [Architectural Rules](#36-architectural-rules)
37. [Engineering Execution Flow](#37-engineering-execution-flow)
38. [Future Engineering Capabilities](#38-future-engineering-capabilities)
39. [Development Philosophy](#39-development-philosophy)
40. [V2 Architectural Baseline](#40-v2-architectural-baseline)
41. [What GridForge Is Not](#41-what-gridforge-is-not)
42. [Project Status](#42-project-status)
43. [Final Architecture](#43-final-architecture)
44. [Guiding Principle](#44-guiding-principle)

---

# 1. Vision

GridForge is intended to provide a unified engineering environment for representing, analyzing, simulating, and operating a digital representation of an electrical power system.

The long-term vision is:

```text
                         GRIDFORGE
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        Digital Twin    Simulation    Engineering
             │              │           Analysis
             └──────────────┼──────────────┘
                            │
                            ▼
                     Decision Support
```

The platform is designed to support:

* Power-system modeling
* Electrical network topology
* AC and DC power-flow studies
* Short-circuit studies
* Contingency analysis
* Dynamic simulation
* Protection studies
* Relay coordination
* Time-current characteristic analysis
* Future OPF / SCOPF
* Future EMT simulation
* Engineering visualization
* Project persistence
* Extensible engineering plugins
* Future SCADA and real-time digital-twin integration

GridForge is therefore not merely a collection of numerical algorithms or a graphical single-line-diagram editor. It is designed as a **coherent engineering platform built around a common authoritative digital representation of the electrical system**.

---

# 2. Core Architectural Principle

The central architectural principle of GridForge is:

> **One authoritative engineering truth, many specialized services.**

The engineering execution chain is:

```text
Physical Engineering Model
          │
          ▼
Electrical Network
          │
          ▼
Engineering Analysis
          │
          ▼
Numerical Solvers
          │
          ▼
Simulation / Protection
          │
          ▼
Engineering Results
          │
          ▼
Visualization / Reports
```

Each layer has a defined responsibility.

No layer should silently become the owner of another layer's state.

For example:

* The GUI does not own electrical topology.
* The solver does not own physical equipment.
* The network does not replace the physical model.
* Protection functions do not own CT/PT state.
* Protection functions do not directly operate breakers.
* Persistence does not become part of domain objects.
* Numerical indices do not become engineering identities.

This separation is fundamental to the V2 architecture.

---

# 3. GridForge V2 Architecture

GridForge V2 is organized as a layered engineering system.

```text
┌──────────────────────────────────────────────────────────┐
│                 GridForge Application                     │
│                                                          │
│     GUI • Tools • Rendering • Controllers • UX           │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                     GridForge Core                       │
│                                                          │
│ Model • Network • Analysis • Solver • Protection         │
│ Simulation • Validation • Controllers                    │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                 Numerical / Backend Layer                │
│                                                          │
│       NumPy • SciPy • Sparse • GPU Backends              │
└──────────────────────────────────────────────────────────┘
```

The architecture deliberately separates:

* Physical engineering state
* Electrical network representation
* Engineering study definitions
* Numerical execution
* Runtime simulation state
* Protection execution
* Validation
* GUI state
* Persistence state

The core remains independent of GUI implementation and project-file representation.

---

# 4. Repository Structure

The repository is organized around architectural responsibilities rather than individual features.

```text
GridForge/
│
├── core/
│   ├── analysis/
│   ├── base/
│   ├── model/
│   ├── network/
│   ├── protection/
│   ├── simulation/
│   ├── solver/
│   ├── validation/
│   └── controller.py
│
├── ui/
│   ├── canvas/
│   ├── core/
│   ├── controllers/
│   ├── interaction/
│   ├── items/
│   ├── plugins/
│   ├── renderers/
│   ├── tools/
│   └── ...
│
├── plugins/
│   └── ...
│
├── tests/
│   ├── core/
│   ├── network/
│   ├── protection/
│   ├── solver/
│   └── ...
│
├── projects/
│   └── ...
│
├── main.py
└── README.md
```

The exact contents of individual directories may evolve during implementation.

The **architectural boundaries must remain stable**.

---

# 5. Core Architecture

The `core/` package is the authoritative engineering execution layer.

| Module          | Responsibility                                 |
| --------------- | ---------------------------------------------- |
| `model/`        | Physical and engineering objects               |
| `network/`      | Electrical topology and network representation |
| `analysis/`     | Engineering study definitions and services     |
| `solver/`       | Numerical computation                          |
| `protection/`   | Protection-function execution                  |
| `simulation/`   | Runtime and dynamic execution                  |
| `validation/`   | Engineering and structural validation          |
| `controller.py` | Core-level orchestration                       |

The core must not depend on:

* Qt widgets
* Graphics scenes
* Rendering objects
* Mouse events
* GUI controllers
* Project file dialogs
* GUI-specific state

This allows the engineering engine to execute independently of the graphical application.

---

# 6. Physical Model

The model layer represents what physically exists in the digital twin.

Typical engineering entities include:

* Buses
* Generators
* Loads
* Transmission lines
* Cables
* Transformers
* Breakers
* Switches
* Shunts
* Motors
* Measurement equipment
* Protection equipment
* Terminals
* Other domain-specific equipment

The model layer is the authoritative owner of:

* Physical equipment identity
* Engineering configuration
* Equipment relationships
* Persistent engineering properties

Derived numerical representations must not replace the physical model.

---

# 7. Asset, Equipment, Component and Device Semantics

GridForge uses explicit engineering semantics rather than requiring every physical object to inherit from one universal monolithic hierarchy.

| Term          | Meaning                                         |
| ------------- | ----------------------------------------------- |
| **Asset**     | Persistent identifiable engineering entity      |
| **Equipment** | Engineered physical apparatus                   |
| **Component** | Engineering-significant constituent part        |
| **Device**    | Independently identifiable functional apparatus |

This permits specialized engineering domains to evolve independently.

For example, protection, measurement, switching, and dynamic-model objects can have appropriate contracts without forcing every object into an artificial inheritance tree.

---

# 8. Electrical Network

The network layer converts the physical engineering model into an authoritative electrical representation.

It manages:

* Electrical topology
* Connectivity
* Terminals
* Buses / nodes
* Branches
* Network indexing
* Deterministic network construction
* Per-unit representation
* Y-bus construction
* Network-derived electrical structures

The conceptual relationship is:

```text
Physical Model
      │
      ▼
Electrical Network
      │
      ├── Topology
      ├── Network Indexing
      ├── Per-Unit
      └── Y-Bus
```

The network layer **does not become the owner of physical equipment**.

Numerical network indices may be reconstructed whenever topology changes. Engineering identities must remain stable.

---

# 9. Analysis Layer

The analysis layer defines **what engineering problem is being investigated**.

Current study domains include:

* Power Flow
* Line Flow
* Transformer Flow
* Short Circuit
* Contingency

The analysis layer may define:

* Study configuration
* Engineering objectives
* Input requirements
* Preconditions
* Result interpretation
* Study-level validation

The numerical solver defines **how the problem is solved**.

Therefore:

> **Analysis ≠ Solver**

This distinction allows multiple numerical methods to serve the same engineering study.

---

# 10. Solver Architecture

The solver layer provides numerical execution engines.

```text
core/solver/
│
├── common/
├── contingency/
├── dynamics/
├── power_flow/
└── short_circuit/
```

Potential numerical technologies include:

* NumPy
* SciPy
* Sparse matrix algorithms
* Vectorized numerical operations
* Batched calculations
* CPU numerical backends
* GPU numerical backends

The solver consumes appropriate numerical representations derived from the authoritative engineering state.

The solver must not become the owner of physical equipment.

---

# 11. Power Flow

GridForge provides a dedicated power-flow solver architecture for steady-state electrical analysis.

The architecture is intended to support:

* Newton-Raphson
* Adaptive line search
* Armijo-type step control
* Trust-region methods
* Levenberg-Marquardt / hybrid approaches
* Continuation power flow
* Predictor-corrector methods
* Contingency screening
* Sparse Jacobian assembly
* CPU execution
* Future GPU execution

The conceptual execution path is:

```text
Physical Model
      │
      ▼
Network
      │
      ▼
Power Flow Analysis
      │
      ▼
Numerical Representation
      │
      ▼
Power Flow Solver
      │
      ▼
Engineering Result
```

A solver result must clearly distinguish:

* Converged solution
* Non-converged solution
* Invalid input
* Invalid topology
* Numerical failure

---

# 12. Short-Circuit Analysis

The short-circuit subsystem provides fault-analysis capabilities.

The architecture is designed to support:

* Fault definition
* Fault location
* Fault type
* Sequence-network calculations
* Fault currents
* Bus voltages
* Branch currents
* Fault contribution analysis
* Engineering fault-study results

Supported fault categories are intended to include:

* Three-phase faults
* Single-line-to-ground faults
* Line-to-line faults
* Double-line-to-ground faults

The short-circuit solver consumes the authoritative electrical network representation.

It must not maintain a competing physical network model.

---

# 13. Dynamic Simulation

The dynamics subsystem provides time-domain power-system simulation.

Dynamic models may represent:

* Synchronous generators
* Excitation systems
* Governors
* Power-system stabilizers
* Motors
* Dynamic loads
* Other dynamic equipment

The conceptual execution path is:

```text
Dynamic Model
      │
      ▼
Dynamic Equations
      │
      ▼
Numerical Integrator
      │
      ▼
Simulation State
      │
      ▼
Simulation Results
```

Dynamic simulation is architecturally independent from the implementation of steady-state power flow and short-circuit algorithms.

---

# 14. Protection Architecture

GridForge V2 uses a **multifunction protection architecture**.

A physical relay is not assumed to represent a single protection function.

For example:

```text
Relay R1
│
├── 50   Instantaneous Overcurrent
├── 51   Time Overcurrent
├── 46   Negative Sequence
├── 67   Directional Overcurrent
└── 50BF Breaker Failure
```

The conceptual structure is:

```text
Physical Relay
      │
      ├── ProtectionElement
      │       └── RelayBase
      │
      ├── ProtectionElement
      │       └── RelayBase
      │
      └── ProtectionElement
              └── RelayBase
```

This architecture permits realistic multifunction numerical relay configurations.

Protection functions remain specialized execution units rather than forcing all relay behavior into one monolithic class.

---

# 15. Measurement Architecture

Protection functions consume authoritative measurement infrastructure.

The intended signal chain is:

```text
CT / PT / CVT
      │
      ▼
MeasurementChannel
      │
      ▼
RelayInput
      │
      ▼
Protection Function
```

Measurement state must have **one authoritative owner**.

Protection functions must not create independent competing copies of:

* CT state
* PT state
* CVT state
* Scaling
* Measurement caches
* Electrical measurement history

Multiple protection functions should therefore consume consistent measurements from the same measurement infrastructure.

---

# 16. Protection Decision Boundary

Protection functions produce **protection decisions**.

They do not directly operate physical breakers.

```text
Protection Function
       │
       ▼
ProtectionDecision
       │
       ▼
Protection Scheme / Output Logic
       │
       ▼
Trip Command
       │
       ▼
BreakerManager
       │
       ▼
Physical Breaker
```

This boundary allows future implementation of:

* Breaker failure
* Autoreclose
* Permissive schemes
* Blocking
* Interlocking
* Transfer trip
* Trip-circuit supervision
* Communication-assisted protection

The protection decision is therefore a deliberate architectural boundary between **protection logic** and **physical switching**.

---

# 17. Simulation Architecture

Simulation provides runtime execution of the digital twin.

A typical simulation cycle is:

```text
Authoritative System State
          │
          ▼
Simulation Time
          │
          ▼
Dynamic / Network State
          │
          ▼
Measurement
          │
          ▼
Protection / Control
          │
          ▼
System State Update
          │
          ▼
Next Simulation Step
```

Runtime simulation state must remain separate from persistent engineering configuration.

A transient simulation condition must not silently overwrite the permanent engineering model.

---

# 18. Validation

GridForge validates engineering state before and during execution.

Validation may operate across several stages:

```text
Model
  │
  ▼
Network
  │
  ▼
Study Configuration
  │
  ▼
Numerical Preconditions
  │
  ▼
Runtime Conditions
```

Validation must distinguish **engineering invalidity** from **numerical failure**.

For example:

```text
Invalid topology
```

is fundamentally different from:

```text
Valid topology
+
Valid study configuration
+
Numerical solver failed to converge
```

These conditions should not be collapsed into a generic error.

---

# 19. GUI Architecture

GridForge provides a modern 2D engineering interface for power-system visualization and interactive modeling.

The GUI is intended to support:

* Single-line diagrams
* Bus-centric editing
* Interactive equipment placement
* Topology-aware connections
* Snapping
* Engineering tools
* Multi-canvas navigation
* Property editing
* Simulation visualization
* Protection visualization
* Analysis-result visualization

The GUI is a **client of the core**.

It does not own engineering truth.

---

# 20. GUI and Core Separation

The fundamental application direction is:

```text
GUI
 │
 ▼
Application / Controller
 │
 ▼
GridForge Core
```

Not:

```text
Core
 │
 ▼
GUI
```

Core objects must never require:

* Qt widgets
* Graphics scenes
* Rendering objects
* Mouse events
* GUI controllers
* GUI-only state

This separation ensures that the core can operate:

* Headlessly
* In automated tests
* In batch studies
* In server environments
* In future real-time applications

---

# 21. Qt Architecture

GridForge uses **PySide6** as its Qt framework.

GUI implementation must not introduce mixed Qt frameworks.

A centralized Qt abstraction layer provides controlled access to Qt-specific functionality:

```text
PySide6
   │
   ▼
ui/core/qt.py
   │
   ▼
GridForge GUI
```

This prevents individual GUI modules from introducing inconsistent Qt dependencies.

---

# 22. Multi-Canvas Architecture

GridForge is designed around hierarchical engineering visualization.

A typical navigation hierarchy may be:

```text
Grid
 │
 ├── Substation A
 │      ├── Bus
 │      ├── Transformer
 │      └── Feeder
 │
 ├── Substation B
 │
 └── Plant / Network
```

The architecture supports navigation between:

* Grid-level views
* Substation-level views
* Plant-level views
* Equipment-level views
* Detailed engineering contexts

A canvas represents a visualization context, not an independent electrical network.

---

# 23. Bus-Centric Network Editing

Electrical connections are governed by **engineering topology**, not arbitrary graphical proximity.

A graphical connection is meaningful only when it corresponds to a valid electrical relationship.

```text
Graphical Interaction
        │
        ▼
Topology / Connection Validation
        │
        ▼
Authoritative Network
        │
        ▼
Electrical Relationship
```

Therefore:

* A graphical line is not merely a drawing object.
* A bus is not merely a graphical rectangle.
* A connection cannot become electrically valid simply because two graphics overlap.

The network remains authoritative.

---

# 24. Rendering Architecture

Rendering is separated from engineering state.

```text
Core Model / Network
        │
        ▼
Render System
        │
        ├── BusRenderer
        ├── LineRenderer
        ├── TransformerRenderer
        └── Equipment Renderers
```

Renderers visualize authoritative objects.

They do not become owners of those objects.

Rendering state may be derived from engineering state, but it must not silently replace it.

---

# 25. Interaction Architecture

The GUI interaction system is divided into specialized services.

Examples include:

* InteractionManager
* Tool System
* Snap System
* Grid System
* Navigation Controller
* Coordinate System
* Rendering System
* Canvas Controller

The purpose of this separation is to prevent:

* Monolithic widgets
* Hidden state ownership
* Duplicated interaction logic
* Direct GUI manipulation of core engineering state

Tools should request engineering operations through the appropriate application/controller boundary.

---

# 26. Plugin Architecture

GridForge supports extensibility through plugins.

Potential plugin domains include:

* Protection functions
* Dynamic models
* Equipment models
* Analysis extensions
* Solver backends
* Visualization
* Engineering tools
* Application services

Plugins must consume stable GridForge contracts.

They must not bypass established ownership boundaries.

A plugin should not, for example:

* Directly manipulate hidden network state
* Create a competing physical model
* Circumvent validation
* Operate breakers outside the protection/control boundary
* Make GUI objects the authoritative engineering state

---

# 27. Persistence Architecture

Project persistence is intentionally separated from the engineering core.

```text
GUI / Application
        │
        ▼
Persistence / Project Layer
        │
        ├── Serialization
        ├── Deserialization
        ├── Schema Validation
        └── Project File Management
        │
        ▼
GridForge Core
```

Core model objects should not contain arbitrary:

* JSON I/O
* File-system management
* GUI file dialogs
* Project-window logic

Projects are loaded into authoritative core objects.

Persistence represents the engineering state; it does not become the engineering state itself.

---

# 28. Digital-Twin State Ownership

GridForge follows a strict state-ownership principle.

| Domain                  | Authoritative Owner           |
| ----------------------- | ----------------------------- |
| Physical equipment      | `core.model`                  |
| Electrical topology     | `core.network`                |
| Per-unit representation | Base / network infrastructure |
| Y-bus                   | `core.network`                |
| Numerical computation   | `core.solver`                 |
| Study interpretation    | `core.analysis`               |
| Protection function     | Protection subsystem          |
| Protection decision     | `ProtectionDecision`          |
| Runtime simulation      | `core.simulation`             |
| Validation              | `core.validation`             |
| GUI state               | GUI                           |
| Project persistence     | Persistence layer             |

The key rule is:

> **Every important state has one authoritative owner.**

Derived representations may exist, but they must remain derived.

---

# 29. Identity Architecture

GridForge separates engineering identity from numerical indexing.

```text
Asset ID
   ≠
Equipment ID
   ≠
Terminal ID
   ≠
Network Node ID
   ≠
Numerical Index
```

Engineering identities must remain stable.

Numerical indices may change when:

* Topology changes
* Network structures are rebuilt
* Components are added or removed
* Solver representations are reconstructed

A numerical index is therefore an implementation detail, not an engineering identity.

---

# 30. Determinism

GridForge prioritizes deterministic engineering behavior.

Identical:

* Model state
* Network topology
* Study configuration
* Solver settings

should produce reproducible results within expected numerical tolerances.

Determinism is particularly important for:

* Regression testing
* Contingency analysis
* Protection studies
* Simulation
* Debugging
* Engineering verification

Non-deterministic behavior must be deliberate and documented where it is genuinely required.

---

# 31. Performance

GridForge is designed for large-scale power-system computation.

The architecture is compatible with:

* Vectorized computation
* Sparse matrices
* Sparse Jacobians
* Batched contingency analysis
* Repeated simulations
* GPU acceleration
* Large network models

Performance optimization must never compromise:

* Engineering correctness
* Determinism
* State ownership
* Numerical validity
* Architectural boundaries

Correctness remains the first engineering requirement.

---

# 32. CPU / GPU Backend Independence

Numerical hardware backends are implementation details.

```text
                 Numerical Representation
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                   CPU         GPU
                 Backend     Backend
```

The physical model and electrical network remain backend-independent.

This allows future GPU acceleration without requiring a redesign of the engineering model.

A GPU implementation is therefore a computational backend, not a second version of the engineering domain model.

---

# 33. Headless Operation

GridForge Core is designed to operate without the GUI.

For example:

```python
network = Network(...)
result = power_flow.solve(network)
```

and:

```python
simulation = Simulation(...)
simulation.run()
```

Headless execution enables:

* Automated engineering studies
* Batch analysis
* Regression testing
* Server-side execution
* Optimization
* Continuous validation
* Future real-time applications

The GUI is therefore an application client rather than a prerequisite for engineering execution.

---

# 34. Testing Strategy

GridForge uses layered testing.

```text
Unit Tests
     │
     ▼
Subsystem Tests
     │
     ▼
Integration Tests
     │
     ▼
Numerical Regression
     │
     ▼
Engineering Case Validation
```

Testing must verify both:

### Software correctness

* Imports
* APIs
* State transitions
* Contracts
* Error handling
* Deterministic behavior
* Integration boundaries

### Engineering correctness

* Electrical topology
* Power-flow results
* Fault currents
* Protection behavior
* Dynamic response
* Engineering constraints

A test suite that passes software-level assertions while producing incorrect engineering results is not sufficient.

---

# 35. Engineering Regression

Representative engineering cases should be maintained for:

* Power flow
* Short circuit
* Contingency
* Dynamics
* Protection
* Network topology

Regression validation should cover both:

* Numerical values
* Expected engineering behavior

Examples include:

```text
Expected:
Bus voltage within tolerance

Expected:
Fault current within tolerance

Expected:
Relay operates within expected time

Expected:
Breaker remains closed when no trip condition exists

Expected:
Topology rejects invalid connection
```

Engineering regression is a long-term protection against architectural and numerical drift.

---

# 36. Architectural Rules

The following rules are fundamental to GridForge V2.

|  # | Rule                                                      | Description                                                           |
| -: | --------------------------------------------------------- | --------------------------------------------------------------------- |
|  1 | **One authoritative owner per state**                     | Important engineering state must have one authoritative owner         |
|  2 | **Model owns physical equipment**                         | Numerical solvers must not become equipment models                    |
|  3 | **Network owns electrical representation**                | GUI components must not become the topology engine                    |
|  4 | **Solver owns numerical execution**                       | Engineering models must not contain solver algorithms                 |
|  5 | **Analysis and solver remain separate**                   | Study definitions and numerical algorithms are different concerns     |
|  6 | **Protection functions produce decisions**                | Protection functions do not directly operate physical breakers        |
|  7 | **Measurement has one authoritative owner**               | Protection functions consume common measurement infrastructure        |
|  8 | **Runtime state is separate from persistent state**       | Simulation state must not silently become engineering configuration   |
|  9 | **GUI is outside the core**                               | Core objects remain headless-capable                                  |
| 10 | **Persistence is outside domain objects**                 | Domain models do not become file-management classes                   |
| 11 | **Numerical indices are not engineering identities**      | Stable engineering identities survive numerical reconstruction        |
| 12 | **Plugins respect established contracts**                 | Extensions must not bypass architectural ownership                    |
| 13 | **Qt remains isolated to the GUI**                        | Core code must not depend on PySide6                                  |
| 14 | **Derived state remains derived**                         | Cached or rendered representations cannot replace authoritative state |
| 15 | **Engineering invalidity differs from numerical failure** | Validation and solver failure must remain distinguishable             |

These rules define the architectural contract for V2.

---

# 37. Engineering Execution Flow

A complete GridForge workflow can be represented as:

```text
                 PROJECT / USER INPUT
                         │
                         ▼
                  Physical Model
                         │
                         ▼
                     Validation
                         │
                         ▼
                 Network Construction
                         │
                         ▼
                   Study Definition
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        Power Flow   Short Circuit  Dynamics
            │            │            │
            └────────────┼────────────┘
                         ▼
                     Simulation
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Measurement            Protection
              │                     │
              └──────────┬──────────┘
                         ▼
                  Engineering Results
                         │
                         ▼
                 GUI / Reports / Export
```

The important architectural property is that each stage consumes the authoritative state supplied by the appropriate preceding layer.

---

# 38. Future Engineering Capabilities

## Steady-State

Planned or extensible capabilities include:

* AC power flow
* DC power flow
* Continuation power flow
* Optimal power flow
* Security-constrained OPF
* Voltage stability analysis

## Fault Analysis

* Three-phase faults
* Single-line-to-ground faults
* Line-to-line faults
* Double-line-to-ground faults
* Sequence networks
* Fault contribution analysis

## Contingency

* N-1 analysis
* N-k analysis
* Fast contingency screening
* Contingency ranking
* Security assessment

## Dynamics

* Transient stability
* AVR
* Governor
* PSS
* Generator models
* Motor dynamics
* Dynamic load models

## Protection

* Overcurrent
* Directional overcurrent
* Distance
* Differential
* Voltage
* Frequency
* Breaker failure
* Autoreclose
* Protection coordination
* TCC analysis

## Advanced Simulation

* EMT
* Real-time simulation
* Hardware-in-the-loop
* Communication-assisted protection

## Digital Twin

* SCADA integration
* Online measurements
* State estimation
* Real-time monitoring
* Event recording
* Predictive analysis
* Operational decision support

Future capabilities must be introduced without violating the established V2 ownership boundaries.

---

# 39. Development Philosophy

GridForge development follows a controlled engineering freeze process:

```text
Designed
   │
   ▼
Audited
   │
   ▼
Implemented
   │
   ▼
Validated
   │
   ▼
Regressed
   │
   ▼
Finalized
   │
   ▼
Frozen
```

A foundational subsystem should not be redesigned merely because its implementation contains defects.

The preferred process is:

```text
Architectural Contract
        │
        ▼
Implementation Audit
        │
        ▼
Defect Classification
        │
        ▼
Production Correction
        │
        ▼
Fresh Audit
        │
        ▼
Tests
        │
        ▼
Integration Validation
        │
        ▼
Freeze
```

This prevents continuous architectural recursion and protects completed subsystems from unnecessary redesign.

---

# 40. V2 Architectural Baseline

GridForge V2 establishes the following major boundaries:

```text
                         GridForge V2
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
     Model                 Network                Analysis
       │                      │                      │
       │                      ├── Topology           │
       │                      ├── Per-Unit           │
       │                      └── Y-Bus              │
       │                                             │
       └──────────────────────┬──────────────────────┘
                              │
                              ▼
                         Solver Layer
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
           Power Flow    Short Circuit    Dynamics
                │             │             │
                └─────────────┼─────────────┘
                              │
                              ▼
                          Simulation
                              │
                   ┌──────────┴──────────┐
                   ▼                     ▼
              Measurement           Protection
                   │                     │
                   ▼                     ▼
            MeasurementChannel    ProtectionElement
                                         │
                                         ▼
                                ProtectionDecision
                                         │
                                         ▼
                                  Scheme / Output
                                         │
                                         ▼
                                   BreakerManager
                                         │
                                         ▼
                                  Physical Model
```

The V2 architecture therefore maintains a clear distinction between:

* Engineering objects
* Electrical representation
* Study definitions
* Numerical execution
* Runtime state
* Protection decisions
* Physical switching
* Visualization

---

# 41. What GridForge Is Not

GridForge is not intended to become:

* ❌ A GUI-only drawing application
* ❌ A collection of independent numerical scripts
* ❌ A monolithic solver
* ❌ A monolithic equipment class hierarchy
* ❌ A relay-only protection simulator
* ❌ A database disguised as an engineering model
* ❌ A file-format-dependent core
* ❌ A GUI-dependent simulation engine
* ❌ A collection of disconnected analysis tools

GridForge is intended to be:

> **An integrated engineering platform built around a coherent digital representation of an electrical power system.**

---

# 42. Project Status

GridForge V2 is being developed as a:

**Layered · Modular · Extensible · Headless-capable · Power-system Digital-Twin Platform**

The architectural foundation establishes explicit boundaries for:

* Physical modeling
* Electrical network representation
* Engineering analysis
* Numerical solvers
* Dynamic simulation
* Protection
* Measurement
* Validation
* GUI
* Persistence
* Plugins

The objective is not merely to implement individual engineering calculations.

The objective is to provide a coherent platform in which those calculations operate on a **common authoritative digital representation of the electrical system**.

---

# 43. Final Architecture

The complete conceptual architecture is:

```text
                         ┌─────────────────────┐
                         │      USER / UI      │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Application Layer  │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
                 ▼                                     ▼
        Persistence / Projects                    GridForge GUI
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    GRIDFORGE CORE   │
                         └──────────┬──────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
       MODEL                     NETWORK                  ANALYSIS
          │                         │                         │
          │                         ├── Topology              │
          │                         ├── Per-Unit              │
          │                         └── Y-Bus                 │
          │                                                   │
          └─────────────────────────┬─────────────────────────┘
                                    │
                                    ▼
                              SOLVER LAYER
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
               Power Flow      Short Circuit      Dynamics
                   │                │                │
                   └────────────────┼────────────────┘
                                    │
                                    ▼
                                SIMULATION
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                    Measurement           Protection
                         │                     │
                         ▼                     ▼
                  MeasurementChannel    ProtectionElement
                                               │
                                               ▼
                                      ProtectionDecision
                                               │
                                               ▼
                                        Scheme / Control
                                               │
                                               ▼
                                         BreakerManager
                                               │
                                               ▼
                                         Physical Model
```

---

# 44. Guiding Principle

GridForge V2 is governed by one overarching engineering principle:

> ## **One authoritative engineering truth, many specialized services.**

The physical model represents what exists.

The network represents how it is electrically connected.

The analysis layer defines what engineering question is being asked.

The solver determines how that question is numerically solved.

Simulation represents runtime behavior.

Protection evaluates measurements and produces protection decisions.

Validation protects engineering integrity.

The GUI visualizes and interacts with the system.

Persistence stores and reconstructs projects.

Plugins extend stable contracts.

None of these layers should silently take ownership of another layer's authoritative state.

This separation provides the foundation required for a scalable power-system engineering platform capable of evolving from offline studies toward advanced simulation, automation, and real-time digital-twin applications.

---

<p align="center"><em>GridForge — one authoritative engineering truth, many specialized services.</em></p>
