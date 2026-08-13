# ⚡ GridForge

### Power-System Digital Twin & Simulation Platform

GridForge is a modular power-system engineering platform designed to provide an integrated environment for **power-system modeling, analysis, simulation, protection, visualization, and digital-twin applications**.

The platform is built around a strict separation between:

```
Physical Engineering Model
          ↓
Electrical Network
          ↓
Engineering Analysis
          ↓
Numerical Solvers
          ↓
Simulation / Protection
          ↓
Engineering Results
          ↓
Visualization / Application
```

**GridForge V2** is being developed as a Python-based, extensible power-system engineering platform capable of supporting steady-state studies, fault analysis, contingency analysis, dynamic simulation, protection studies, and future real-time digital-twin applications.

---

## Table of Contents

1. [Vision](#1-vision)
2. [GridForge V2 Architecture](#2-gridforge-v2-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Core Architecture](#4-core-architecture)
5. [Physical Model](#5-physical-model)
6. [Asset / Equipment / Component / Device Semantics](#6-asset--equipment--component--device-semantics)
7. [Electrical Network](#7-electrical-network)
8. [Analysis Layer](#8-analysis-layer)
9. [Solver Architecture](#9-solver-architecture)
10. [Power Flow](#10-power-flow)
11. [Short-Circuit Analysis](#11-short-circuit-analysis)
12. [Dynamics](#12-dynamics)
13. [Protection](#13-protection)
14. [Measurement Architecture](#14-measurement-architecture)
15. [Protection Decision Boundary](#15-protection-decision-boundary)
16. [Simulation Architecture](#16-simulation-architecture)
17. [Validation](#17-validation)
18. [GUI Architecture](#18-gui-architecture)
19. [GUI and Core Separation](#19-gui-and-core-separation)
20. [Qt Architecture](#20-qt-architecture)
21. [Multi-Canvas Architecture](#21-multi-canvas-architecture)
22. [Bus-Centric Network Editing](#22-bus-centric-network-editing)
23. [Rendering Architecture](#23-rendering-architecture)
24. [Interaction Architecture](#24-interaction-architecture)
25. [Plugin Architecture](#25-plugin-architecture)
26. [Persistence Architecture](#26-persistence-architecture)
27. [Digital-Twin State Ownership](#27-digital-twin-state-ownership)
28. [Identity Architecture](#28-identity-architecture)
29. [Determinism](#29-determinism)
30. [Performance](#30-performance)
31. [CPU / GPU Backend Independence](#31-cpu--gpu-backend-independence)
32. [Headless Operation](#32-headless-operation)
33. [Testing Strategy](#33-testing-strategy)
34. [Engineering Regression](#34-engineering-regression)
35. [Architectural Rules](#35-architectural-rules)
36. [Engineering Execution Flow](#36-engineering-execution-flow)
37. [Future Engineering Capabilities](#37-future-engineering-capabilities)
38. [Development Philosophy](#38-development-philosophy)
39. [V2 Architectural Baseline](#39-v2-architectural-baseline)
40. [What GridForge Is Not](#40-what-gridforge-is-not)
41. [Guiding Principle](#41-guiding-principle)
42. [Final Architecture](#42-final-architecture)
43. [Project Status](#43-project-status)
44. [Status](#44-status)

---

## 1. Vision

The objective of GridForge is to provide a unified engineering environment for modeling, analyzing, simulating, and operating a digital representation of an electrical power system.

The long-term vision:

```
                    GRIDFORGE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Digital Twin    Simulation     Engineering
        │              │           Analysis
        └──────────────┼──────────────┘
                       │
                       ▼
                Decision Support
```

The platform is intended to support:

- Power-system modeling
- Electrical network topology
- Power-flow studies
- Short-circuit studies
- Contingency analysis
- Dynamic simulation
- Protection studies
- Relay coordination
- TCC analysis
- Future OPF / SCOPF
- Future EMT simulation
- Future real-time digital-twin execution
- Engineering visualization
- Extensible domain plugins

---

## 2. GridForge V2 Architecture

GridForge V2 is organized as a layered engineering system.

```
┌──────────────────────────────────────────────────────────┐
│                     GridForge Application                 │
│                                                             │
│       GUI • Tools • Rendering • Controllers • UX           │
└─────────────────────────────┬───────────────────────────---┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                         GridForge Core                     │
│                                                             │
│ Model • Network • Analysis • Solver • Protection            │
│ Simulation • Validation • Controllers                       │
└─────────────────────────────┬───────────────────────────---┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                  Numerical / Backend Layer                 │
│                                                             │
│       NumPy • SciPy • Sparse • GPU Backends                │
└──────────────────────────────────────────────────────────┘
```

> The core remains independent of the graphical user interface and project persistence system.

---

## 3. Repository Structure

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
├── gui/
│   ├── core/
│   ├── canvas/
│   ├── controllers/
│   ├── interaction/
│   ├── rendering/
│   ├── tools/
│   └── ...
│
├── plugins/
│   └── ...
│
├── tests/
│   ├── core/
│   ├── solver/
│   ├── protection/
│   ├── network/
│   └── ...
│
├── projects/
│   └── ...
│
├── main.py
└── README.md
```

> The exact directory contents may evolve, but the architectural separation must remain intact.

---

## 4. Core Architecture

The `core/` package is the authoritative engineering execution layer.

| Module | Responsibility |
|---|---|
| `model/` | Physical / engineering objects |
| `network/` | Electrical network representation |
| `analysis/` | Engineering study services |
| `solver/` | Numerical computation |
| `protection/` | Protection-function execution |
| `simulation/` | Runtime and dynamic execution |
| `validation/` | Engineering and structural validation |
| `controller.py` | Core orchestration |

> The core does not depend on GUI implementation.

---

## 5. Physical Model

The model layer represents what physically exists in the digital twin.

Typical engineering entities include:

- Buses
- Generators
- Loads
- Transmission lines
- Cables
- Transformers
- Breakers
- Switches
- Shunts
- Motors
- Measurement equipment
- Protection equipment
- Terminals
- Other domain-specific equipment

> The model is the authoritative owner of physical equipment identity and engineering configuration.

---

## 6. Asset / Equipment / Component / Device Semantics

GridForge uses explicit engineering semantics rather than a mandatory universal inheritance hierarchy:

| Term | Interpretation |
|---|---|
| **Asset** | Persistent identifiable entity |
| **Equipment** | Engineered physical apparatus |
| **Component** | Engineering-significant constituent part |
| **Device** | Independently identifiable functional apparatus |

Specialized domain implementations may therefore be introduced without creating an artificial monolithic class hierarchy.

---

## 7. Electrical Network

The network layer converts the physical model into an authoritative electrical representation. It manages:

- Electrical topology
- Connectivity
- Terminals
- Buses/nodes
- Branches
- Deterministic network indexing
- Per-unit representation
- Y-bus construction
- Network-derived electrical structures

```
Physical Model
      │
      ▼
Electrical Network
      │
      ├── Topology
      ├── Per-Unit
      └── Y-Bus
```

> The network does not become the owner of physical equipment.

---

## 8. Analysis Layer

The analysis layer defines engineering studies. Current analysis domains include:

- Power Flow
- Line Flow
- Transformer Flow
- Short Circuit
- Contingency

The analysis layer determines **what** engineering problem is being investigated. The numerical solver determines **how** that problem is solved.

> **Analysis ≠ Solver**

---

## 9. Solver Architecture

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

Potential computational technologies include:

- NumPy
- SciPy
- Sparse matrix algorithms
- Vectorized numerical operations
- Batched calculations
- GPU acceleration

> The numerical backend must remain independent of the physical model architecture.

---

## 10. Power Flow

GridForge provides a dedicated power-flow solver architecture for steady-state network analysis, designed to support:

- Newton-Raphson
- Adaptive line search
- Trust-region methods
- Levenberg-Marquardt / hybrid approaches
- Continuation power flow
- Predictor-corrector methods
- Contingency screening
- Sparse Jacobian assembly
- CPU and future GPU execution

```
Network
   │
   ▼
Power Flow Analysis
   │
   ▼
Numerical Solver
   │
   ▼
Converged / Failed Result
```

---

## 11. Short-Circuit Analysis

The short-circuit subsystem provides fault-analysis capabilities, designed to support:

- Fault definition
- Fault location
- Fault type
- Sequence-network calculations
- Fault currents
- Bus voltages
- Branch currents
- Fault-study results

> The short-circuit solver consumes the authoritative network representation rather than maintaining a separate physical network model.

---

## 12. Dynamics

The dynamics subsystem provides time-domain power-system simulation, supporting dynamic models for:

- Generators
- Governors
- Excitation systems
- Power-system stabilizers
- Other dynamic equipment and models

```
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
```

> The dynamics subsystem is independent of steady-state power flow and short-circuit numerical implementations.

---

## 13. Protection

GridForge V2 uses a **multifunction protection architecture**. A physical relay is not assumed to represent a single protection function.

**Example:**

```
Relay R1
│
├── 50   Instantaneous Overcurrent
├── 51   Time Overcurrent
├── 46   Negative Sequence
├── 67   Directional Overcurrent
└── 50BF Breaker Failure
```

```
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

> This allows realistic multifunction numerical relay configurations.

---

## 14. Measurement Architecture

Protection functions consume authoritative measurement infrastructure.

```
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

Measurement state must have **one authoritative owner**. Protection functions must **not** create independent copies of:

- CT state
- PT state
- CVT state
- Scaling
- Measurement caches

> This ensures multiple protection functions consume consistent electrical measurements.

---

## 15. Protection Decision Boundary

Protection functions produce protection **decisions**. They do not directly operate physical breakers.

```
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

This architecture allows future implementation of:

- Breaker failure
- Autoreclose
- Permissive schemes
- Blocking
- Interlocking
- Transfer trip
- Trip-circuit supervision
- Communication-assisted protection

---

## 16. Simulation Architecture

Simulation provides runtime execution of the digital twin. A typical simulation cycle:

```
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

> Transient runtime state is kept separate from persistent engineering configuration.

---

## 17. Validation

GridForge validates engineering state before and during execution. Validation may cover:

```
Model
  ↓
Network
  ↓
Study Configuration
  ↓
Numerical Preconditions
  ↓
Runtime Conditions
```

Validation distinguishes **engineering invalidity** from **numerical failure**. For example:

> `Invalid topology`
>
> is fundamentally different from:
>
> `Valid topology + Numerical solver did not converge`

---

## 18. GUI Architecture

GridForge provides a modern 2D engineering interface designed around power-system visualization and interactive system modeling, intended to provide:

- Single-line diagram visualization
- Bus-centric editing
- Interactive equipment placement
- Topology-aware connections
- Snapping
- Engineering tools
- Multi-canvas navigation
- Property editing
- Simulation visualization
- Protection visualization
- Analysis-result visualization

> The GUI is a client of the core. **It does not own engineering truth.**

---

## 19. GUI and Core Separation

The fundamental rule:

```
GUI
 │
 ▼
Application / Controller
 │
 ▼
Core
```

**Not:**

```
Core
 │
 ▼
GUI
```

Core objects must never require:

- Qt widgets
- Graphics scenes
- Rendering objects
- GUI controllers
- Mouse events
- UI state

> This allows GridForge to run headlessly.

---

## 20. Qt Architecture

The GridForge GUI uses **PySide6** as its Qt framework. GUI code should not introduce mixed Qt frameworks. A centralized Qt abstraction layer is used so that GUI implementation details remain controlled.

```
PySide6
   │
   ▼
gui/core/qt.py
   │
   ▼
GridForge GUI
```

---

## 21. Multi-Canvas Architecture

GridForge is designed around hierarchical engineering visualization.

```
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

This permits navigation between:

- Grid-level views
- Substation-level views
- Equipment-level views
- Detailed engineering contexts

---

## 22. Bus-Centric Network Editing

Electrical connections are governed by **engineering topology** rather than arbitrary graphical proximity.

- ✅ Valid Electrical Connection
- ❌ Invalid Electrical Connection

> A graphical line is not merely a drawing object — it represents an electrical relationship in the core network.

---

## 23. Rendering Architecture

Rendering is separated from engineering state.

```
Core Model
     │
     ▼
Render System
     │
     ├── BusRenderer
     ├── LineRenderer
     ├── TransformerRenderer
     └── Equipment Renderers
```

> Renderers visualize authoritative objects. They do not become the owners of those objects.

---

## 24. Interaction Architecture

The GUI interaction system is designed around specialized services such as:

- InteractionManager
- Tool System
- Snap System
- Grid System
- Navigation Controller
- Coordinate System
- Rendering System
- Canvas Controller

> The purpose is to prevent individual GUI widgets from becoming monolithic controllers.

---

## 25. Plugin Architecture

GridForge is designed for extensibility through plugins. Potential plugin domains include:

- Protection Functions
- Dynamic Models
- Equipment Models
- Analysis Extensions
- Solver Backends
- Visualization
- Engineering Tools

> Plugins should consume stable GridForge contracts. They should not bypass core ownership boundaries.

---

## 26. Persistence Architecture

Project persistence is intentionally separated from the core.

```
GUI
 │
 ▼
Project / Persistence Layer
 │
 ├── Serialization
 ├── Deserialization
 ├── Schema Validation
 └── Project File Management
 │
 ▼
GridForge Core
```

> Core model objects should not contain arbitrary JSON/file I/O or GUI file dialog logic. Loaded projects are reconstructed into authoritative core objects.

---

## 27. Digital-Twin State Ownership

GridForge follows a strict state-ownership principle.

| Domain | Authoritative Owner |
|---|---|
| Physical equipment | `core.model` |
| Electrical topology | `core.network` |
| Per-unit representation | Base/network infrastructure |
| Y-bus | `core.network` |
| Numerical computation | `core.solver` |
| Study interpretation | `core.analysis` |
| Protection function | Protection subsystem |
| Protection decision | `ProtectionDecision` |
| Runtime simulation | `core.simulation` |
| Validation | `core.validation` |
| GUI state | GUI |
| Project persistence | Persistence layer |

> Derived representations must never silently replace authoritative state.

---

## 28. Identity Architecture

GridForge separates engineering identity from numerical indexing:

```
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

Numerical indices may change as a result of network reconstruction. **Engineering identities must remain stable.**

---

## 29. Determinism

GridForge prioritizes deterministic engineering behavior. Identical:

- Model state
- Network topology
- Study configuration
- Solver settings

...should produce reproducible results within expected numerical tolerances. Determinism is particularly important for:

- Regression testing
- Contingency analysis
- Protection studies
- Simulation
- Debugging
- Engineering verification

---

## 30. Performance

GridForge is designed for large-scale power-system computation. The architecture is compatible with:

- Vectorized computation
- Sparse matrices
- Sparse Jacobians
- Batched contingency analysis
- GPU acceleration
- Repeated simulations
- Large network models

> Performance optimization must not compromise engineering correctness or state ownership.

---

## 31. CPU / GPU Backend Independence

Numerical backends are implementation details.

```
                    Numerical Representation
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                      CPU           GPU
                    Backend       Backend
```

> The physical model and network model remain backend-independent, permitting future GPU acceleration without redesigning the engineering model.

---

## 32. Headless Operation

GridForge Core is designed to run without the GUI.

```python
network = Network(...)
result = power_flow.solve(network)
```

```python
simulation = Simulation(...)
simulation.run()
```

This makes the platform suitable for:

- Automated studies
- Batch analysis
- Regression testing
- Server-side execution
- Optimization
- Future real-time applications

---

## 33. Testing Strategy

GridForge uses layered testing:

```
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

Tests should verify both:

- Software correctness
- Engineering correctness

---

## 34. Engineering Regression

Representative engineering cases should be maintained for:

- Power flow
- Short circuit
- Contingency
- Dynamics
- Protection
- Network topology

> Regression validation should cover both numerical values and expected engineering behavior.

---

## 35. Architectural Rules

The following rules are fundamental to GridForge V2.

| # | Rule | Description |
|---|---|---|
| 1 | **One authoritative owner per state** | Do not maintain competing copies of important engineering state |
| 2 | **Model owns physical equipment** | The solver must not become the equipment model |
| 3 | **Network owns electrical representation** | The GUI must not become the topology engine |
| 4 | **Solver owns numerical execution** | The model must not contain solver algorithms |
| 5 | **Analysis and solver remain separate** | A study definition is not the same thing as its numerical algorithm |
| 6 | **Protection functions produce decisions** | Protection functions do not directly operate breakers |
| 7 | **Measurement has one authoritative owner** | Protection functions consume measurement infrastructure |
| 8 | **Runtime state is separate from persistent state** | Simulation state must not silently become engineering configuration |
| 9 | **GUI is outside the core** | Core objects must remain headless-capable |
| 10 | **Persistence is outside domain objects** | Engineering models must not become file-management classes |
| 11 | **Numerical indices are not engineering identities** | Stable engineering identities must survive numerical reconstruction |
| 12 | **Plugins respect established contracts** | Extensions must not bypass architectural ownership |

---

## 36. Engineering Execution Flow

A complete GridForge workflow can be represented as:

```
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
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Power Flow  Short-Circuit Dynamics
              │          │          │
              └──────────┼──────────┘
                         ▼
                    Simulation
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
         Measurement            Protection
              │                     │
              └──────────┬──────────┘
                         ▼
                    Engineering
                      Results
                         │
                         ▼
                    GUI / Reports
```

---

## 37. Future Engineering Capabilities

<details>
<summary><strong>Steady-State</strong></summary>

- AC power flow
- DC power flow
- Continuation power flow
- Optimal power flow
- Security-constrained OPF
- Voltage stability analysis
</details>

<details>
<summary><strong>Fault Analysis</strong></summary>

- Three-phase faults
- Single-line-to-ground faults
- Line-to-line faults
- Double-line-to-ground faults
- Sequence networks
- Fault contribution analysis
</details>

<details>
<summary><strong>Contingency</strong></summary>

- N-1 analysis
- N-k analysis
- Fast screening
- Ranking
- Security assessment
</details>

<details>
<summary><strong>Dynamics</strong></summary>

- Transient stability
- AVR
- Governor
- PSS
- Generator models
- Motor dynamics
- Dynamic load models
</details>

<details>
<summary><strong>Protection</strong></summary>

- Overcurrent
- Directional overcurrent
- Distance
- Differential
- Voltage
- Frequency
- Breaker failure
- Autoreclose
- Protection coordination
- TCC
</details>

<details>
<summary><strong>Advanced Simulation</strong></summary>

- EMT
- Real-time simulation
- Hardware-in-the-loop
- Communication-assisted protection
</details>

<details>
<summary><strong>Digital Twin</strong></summary>

- SCADA integration
- Online measurements
- State estimation
- Real-time monitoring
- Event recording
- Predictive analysis
</details>

---

## 38. Development Philosophy

GridForge development follows a layer-by-layer engineering freeze process:

```
Designed
   ↓
Audited
   ↓
Implemented
   ↓
Validated
   ↓
Regressed
   ↓
Finalized
   ↓
Frozen
```

> Once a foundational subsystem is frozen, it should not be redesigned without identifying a genuinely fundamental architectural requirement. This protects the project from continuous architectural drift.

---

## 39. V2 Architectural Baseline

GridForge V2 establishes the following major architectural boundaries:

```
                    GridForge V2
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
     ▼                   ▼                   ▼
   Model              Network             Analysis
     │                   │                   │
     │                   ▼                   ▼
     │                 Y-Bus              Solver
     │                                       │
     │                              ┌────────┼────────┐
     │                              ▼        ▼        ▼
     │                         Power Flow Short  Dynamics
     │                                      Circuit
     │
     ├──────────────────────────────────────────────┐
     │                                              │
     ▼                                              ▼
Measurement                                    Protection
     │                                              │
     ▼                                              ▼
RelayInput                                  ProtectionDecision
                                                    │
                                                    ▼
                                             Scheme / Output
                                                    │
                                                    ▼
                                              BreakerManager
```

---

## 40. What GridForge Is Not

GridForge is **not** intended to be:

- ❌ A GUI-only drawing application
- ❌ A collection of independent numerical scripts
- ❌ A monolithic solver
- ❌ A monolithic equipment class hierarchy
- ❌ A relay-only protection simulator
- ❌ A database disguised as an engineering model
- ❌ A file-format-dependent core
- ❌ A GUI-dependent simulation engine

> GridForge is intended to be an integrated engineering platform with a single coherent digital-twin architecture.

---

## 41. Guiding Principle

> **Represent engineering truth once, derive specialized representations from it, execute studies through independent numerical services, and keep visualization and persistence outside the authoritative engineering core.**

This principle governs the relationship between every major GridForge subsystem.

---

## 42. Final Architecture

The complete conceptual architecture:

```
                         ┌───────────────────┐
                         │      USER / UI     │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Application Layer │
                         └─────────┬─────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
                ▼                                     ▼
       Persistence / Projects                    GridForge GUI
                │                                     │
                └──────────────────┬──────────────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   GRIDFORGE CORE  │
                         └─────────┬─────────┘
                                   │
       ┌───────────────────────────┼──────────────────────────┐
       │                           │                          │
       ▼                           ▼                          ▼
   MODEL                       NETWORK                    ANALYSIS
       │                           │                          │
       │                           ├── Topology               │
       │                           ├── Per-Unit               │
       │                           └── Y-Bus                  │
       │                                                      │
       └───────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
                              SOLVER LAYER
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
             Power Flow      Short Circuit       Dynamics
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   │
                                   ▼
                              SIMULATION
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
                 Measurement               Protection
                      │                         │
                      ▼                         ▼
               MeasurementChannel       ProtectionElement
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

## 43. Project Status

GridForge V2 is being developed as a **layered, modular, extensible power-system digital-twin platform**.

The architectural foundation establishes clear boundaries for:

physical modeling · network representation · analysis · numerical solvers · dynamics · protection · simulation · validation · GUI · persistence · plugins

> The objective is not merely to implement individual engineering calculations, but to provide a coherent platform in which those calculations operate on a common authoritative digital representation of the electrical system.

---

## 44. Status

**GridForge V2 — Architectural Foundation**

| Subsystem | Role |
|---|---|
| Model | Engineering Authority |
| Network | Electrical Authority |
| Analysis | Study Authority |
| Solver | Numerical Execution |
| Protection | Protection Execution |
| Simulation | Runtime Execution |
| Validation | Engineering Integrity |
| GUI | Visualization / Interaction |
| Persistence | Project State Management |
| Plugins | Extensibility |

> GridForge V2 is designed as a **unified engineering platform** rather than a collection of disconnected power-system tools.

---

<p align="center"><em>GridForge — one authoritative engineering truth, many specialized services.</em></p>
