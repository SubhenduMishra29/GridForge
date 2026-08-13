# 🧩 GridForge V2 — Core

### Package-Level Architectural Reference for `core/`

The `core/` package is the **authoritative engineering and simulation foundation** of GridForge V2.

It contains the domain model, electrical network representation, numerical solvers, analysis services, protection framework, simulation infrastructure, validation, and core orchestration required to operate the GridForge power-system digital twin.

The core is intentionally independent of:

- GUI implementation
- Rendering
- User-interface state
- File dialogs
- Project-file I/O
- Presentation logic
- Platform-specific UI services

The fundamental architectural principle:

```
                         GridForge Application
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
                 GUI Layer                Persistence Layer
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                              core/
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
      Physical Model          Network                 Analysis
          │                       │                        │
          └───────────────┬───────┴────────────────────────┘
                          │
                          ▼
                       Solvers
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Power Flow   Short Circuit   Dynamics
                          │
                          ▼
                     Protection
```

> The `core/` package is therefore the source of engineering truth and executable domain behavior.

---

## Table of Contents

1. [Architectural Position](#1-architectural-position)
2. [Core Architectural Principle](#2-core-architectural-principle)
3. [Package Structure](#3-package-structure)
4. [Core Module Responsibilities](#4-core-module-responsibilities)
5. [Asset, Equipment, Component and Device Semantics](#5-asset-equipment-component-and-device-semantics)
6. [Model as Physical Authority](#6-model-as-physical-authority)
7. [core/network/](#7-corenetwork)
8. [core/analysis/](#8-coreanalysis)
9. [Analysis vs Solver](#9-analysis-vs-solver)
10. [core/solver/](#10-coresolver)
11. [Numerical Solver Principle](#11-numerical-solver-principle)
12. [Common Numerical Infrastructure](#12-common-numerical-infrastructure)
13. [Power Flow](#13-power-flow)
14. [Short Circuit](#14-short-circuit)
15. [Dynamics](#15-dynamics)
16. [core/protection/](#16-coreprotection)
17. [Protection Measurement Boundary](#17-protection-measurement-boundary)
18. [Protection Decision Boundary](#18-protection-decision-boundary)
19. [core/simulation/](#19-coresimulation)
20. [Simulation State vs Physical State](#20-simulation-state-vs-physical-state)
21. [core/validation/](#21-corevalidation)
22. [core/controller.py](#22-corecontrollerpy)
23. [Base Layer](#23-base-layer)
24. [Dependency Direction](#24-dependency-direction)
25. [No GUI Dependency](#25-no-gui-dependency)
26. [No Persistence Dependency](#26-no-persistence-dependency)
27. [Authoritative State Principle](#27-authoritative-state-principle)
28. [Derived State Principle](#28-derived-state-principle)
29. [Identity Principle](#29-identity-principle)
30. [State Ownership Principle](#30-state-ownership-principle)
31. [Study Isolation](#31-study-isolation)
32. [Determinism](#32-determinism)
33. [Error Handling](#33-error-handling)
34. [Numerical Failure vs Engineering Failure](#34-numerical-failure-vs-engineering-failure)
35. [Core Execution Flow](#35-core-execution-flow)
36. [Core Does Not Define the GUI](#36-core-does-not-define-the-gui)
37. [Core Does Not Define Project Persistence](#37-core-does-not-define-project-persistence)
38. [Plugin Architecture](#38-plugin-architecture)
39. [Protection Function Plugins](#39-protection-function-plugins)
40. [Dynamic Model Plugins](#40-dynamic-model-plugins)
41. [Testing Philosophy](#41-testing-philosophy)
42. [Numerical Regression](#42-numerical-regression)
43. [Performance Architecture](#43-performance-architecture)
44. [CPU and GPU Separation](#44-cpu-and-gpu-separation)
45. [Core API Stability](#45-core-api-stability)
46. [Architectural Invariants](#46-architectural-invariants)
47. [Dependency Rules](#47-dependency-rules)
48. [Core as a Headless Engine](#48-core-as-a-headless-engine)
49. [Core and Digital Twin](#49-core-and-digital-twin)
50. [Future Expansion](#50-future-expansion)
51. [Design Philosophy](#51-design-philosophy)
52. [Current Foundation Status](#52-current-foundation-status)
53. [Freeze Rules](#53-freeze-rules)
54. [Final Architectural Summary](#54-final-architectural-summary)
55. [Final Status](#55-final-status)

---

## 1. Architectural Position

GridForge V2 follows a layered architecture in which the core sits below application/UI concerns and above low-level numerical implementation details.

```
┌─────────────────────────────────────────────────────┐
│                    Application / GUI                 │
│                                                        │
│  Canvas • Tools • Controllers • Rendering • UI         │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                         core/                         │
│                                                        │
│  Model • Network • Analysis • Solver • Protection      │
│  Simulation • Validation • Controllers                 │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              Numerical / Platform Libraries           │
│                                                        │
│      NumPy • SciPy • Sparse • GPU Backends             │
└─────────────────────────────────────────────────────┘
```

> The core must remain usable without the GUI.

---

## 2. Core Architectural Principle

The core is organized around a strict separation of responsibilities:

```
What physically exists
        │
        ▼
Physical / Engineering Model
        │
        ▼
Electrical Network
        │
        ▼
Analysis Representation
        │
        ▼
Numerical Solver
        │
        ▼
Study Result
```

Additional domain execution layers consume authoritative state:

```
Measurement
      │
      ▼
Protection
      │
      ▼
Protection Decision
```

The core therefore distinguishes between:

| Question | Owning Layer |
|---|---|
| What exists | Model |
| How it is electrically connected | Network |
| What study is being performed | Analysis |
| How the mathematical problem is solved | Solver |
| How protection functions execute | Protection |
| How time-domain behavior is executed | Simulation |
| Whether state is valid | Validation |

---

## 3. Package Structure

```text
core/
├── __init__.py
├── analysis/
├── base/
├── controller.py
├── model/
├── network/
├── protection/
├── simulation/
├── solver/
└── validation/
```

> Each package has a defined architectural responsibility.

---

## 4. Core Module Responsibilities

### 4.1 `core/model/`

The model layer represents the authoritative physical and engineering entities of the GridForge digital twin. **It describes what physically exists.**

Examples include:

- Buses
- Generators
- Loads
- Lines
- Transformers
- Breakers
- Switches
- Shunts
- Motors
- Physical protection equipment
- Other engineering equipment and domain objects

The model layer owns persistent engineering identity and equipment configuration.

```
core.model
    │
    ├── Equipment
    ├── Components
    ├── Devices
    ├── Terminals
    └── Engineering State
```

> The model layer does not become the numerical solver.

---

## 5. Asset, Equipment, Component and Device Semantics

GridForge V2 maintains explicit semantic distinctions between **Asset**, **Equipment**, **Component**, and **Device**. These are engineering classifications and should not be forced into a giant inheritance hierarchy.

| Term | Meaning |
|---|---|
| **Asset** | Persistent identifiable entity |
| **Equipment** | Engineered physical apparatus |
| **Component** | Engineering-significant constituent part |
| **Device** | Independently identifiable functional apparatus |

> A specialized implementation may participate in multiple engineering domains without requiring an artificial universal inheritance tree.

---

## 6. Model as Physical Authority

The model layer is the authoritative owner of physical equipment state.

```
Breaker
    │
    ├── identity
    ├── terminals
    ├── rating
    └── physical state
```

The network layer interprets the breaker state electrically. The protection layer may consume breaker information. The GUI displays it.

> However, the physical model remains the authoritative owner.

---

## 7. `core/network/`

The network layer provides the electrical interpretation of the physical model. Its responsibilities include:

- Topology
- Electrical connectivity
- Network nodes
- Branch relationships
- Deterministic indexing
- Per-unit representation
- Y-bus construction
- Network-level derived structures

```
core.model
     │
     ▼
core.network
     │
     ├── topology
     ├── per-unit
     └── ybus
     │
     ▼
core.solver
```

> The network layer does not own physical equipment. It does not execute complete numerical studies.

---

## 8. `core/analysis/`

The analysis layer provides study-level engineering services and result-oriented analysis. Examples include:

- Power-flow analysis
- Line-flow analysis
- Transformer-flow analysis
- Short-circuit analysis
- Contingency analysis

The analysis layer coordinates study requirements and interprets solver outputs.

```
Network
   │
   ▼
Analysis
   │
   ▼
Solver
   │
   ▼
Numerical Result
   │
   ▼
Analysis Interpretation
```

> Analysis is therefore distinct from the numerical algorithm itself.

---

## 9. Analysis vs Solver

A critical architectural distinction:

> **Analysis ≠ Solver**

```
Power Flow Analysis
        │
        ▼
Power Flow Solver
        │
        ▼
Numerical Result
```

The analysis layer determines **what** the engineering study requires. The solver determines **how** the mathematical problem is solved.

---

## 10. `core/solver/`

The solver layer provides the numerical execution engines of GridForge V2.

```text
core/solver/
├── common/
├── contingency/
├── dynamics/
├── power_flow/
└── short_circuit/
```

> The exact internal structure may evolve, but solver responsibilities remain separate from model and network ownership. The solver consumes authoritative network/model representations and produces numerical results.

---

## 11. Numerical Solver Principle

```
Authoritative State
       │
       ▼
Numerical Representation
       │
       ▼
Solver
       │
       ▼
Numerical Result
```

The solver must **not** silently become the owner of:

- Physical equipment
- GUI state
- Project state
- Protection configuration
- Authoritative network identity

---

## 12. Common Numerical Infrastructure

Shared numerical infrastructure belongs below study-specific solvers:

- Mismatch calculations
- Jacobian assembly
- Numerical convergence utilities
- Sparse matrix utilities
- Solver diagnostics
- Common numerical data structures

> The purpose is to avoid duplicate implementations across numerical studies.

```
                 Numerical Common Layer
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Power Flow    Short Circuit    Dynamics
```

---

## 13. Power Flow

The GridForge power-flow subsystem provides numerical methods for solving steady-state electrical network equations, supporting advanced strategies including:

- Newton-Raphson
- Adaptive line search
- Trust-region approaches
- Levenberg-Marquardt / hybrid methods
- Continuation / predictor-corrector methods
- Fast contingency screening
- Scalable sparse numerical operations

> The solver operates on the network representation rather than directly manipulating GUI or physical equipment objects.

---

## 14. Short Circuit

The short-circuit subsystem provides fault-analysis computation, responsible for:

- Fault formulation
- Network fault representation
- Fault-current calculation
- Voltage response
- Sequence-network handling where applicable
- Fault-study results

> It consumes the authoritative network representation. It does not own physical network topology.

---

## 15. Dynamics

The dynamics subsystem provides time-domain simulation infrastructure for dynamic power-system behavior, supporting the execution of dynamic models and numerical integration.

```
Dynamic Model
      │
      ▼
Dynamic Equation
      │
      ▼
Numerical Integrator
      │
      ▼
Simulation State
```

> The dynamics subsystem is distinct from steady-state power flow and short-circuit computation.

---

## 16. `core/protection/`

The protection subsystem provides the execution framework for protection functions.

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

A physical relay is therefore **not** assumed to equal one protection function. A multifunction relay may contain:

```
Relay R1
│
├── 50
├── 51
├── 46
├── 67
└── 50BF
```

---

## 17. Protection Measurement Boundary

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

Protection functions must **not** independently create duplicate:

- CT state
- PT state
- Measurement caches
- Scaling logic
- Instrument transformations

> The measurement subsystem remains authoritative.

---

## 18. Protection Decision Boundary

Protection functions produce **decisions**. They do not directly operate physical equipment.

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

This separation permits future:

- Interlocking
- Breaker failure
- Autoreclose
- Permissive schemes
- Transfer trip
- Trip circuit supervision
- Communication-assisted protection

---

## 19. `core/simulation/`

The simulation layer provides the execution environment for time-dependent and event-driven system behavior. It coordinates:

- Simulation time
- Event sequencing
- Simulation state
- Subsystem execution
- Dynamic updates
- Protection evaluation
- Equipment/control interactions

> The simulation layer must not duplicate the authoritative state of the model or network.

---

## 20. Simulation State vs Physical State

Simulation runtime state must remain distinct from persistent physical configuration.

```
Physical Model
     │
     ▼
Persistent Configuration

Simulation
     │
     ▼
Transient Runtime State
```

**Example:**

```
Generator Model
     │
     ├── physical parameters
     └── configuration

Generator Runtime
     │
     ├── rotor angle
     ├── speed
     └── dynamic states
```

> Runtime state is required for execution but is not automatically the authoritative project model.

---

## 21. `core/validation/`

The validation layer provides domain and architectural consistency checks, operating at several levels:

```
Model Validation
      │
      ▼
Network Validation
      │
      ▼
Study Validation
      │
      ▼
Numerical Preconditions
```

Validation should detect invalid states before they produce misleading numerical results, including:

- Invalid equipment configuration
- Unresolved terminals
- Invalid topology
- Inconsistent network data
- Invalid study configuration
- Missing required parameters
- Incompatible numerical conditions

---

## 22. `core/controller.py`

The core controller provides application-level orchestration between core services. It should coordinate workflows without becoming a universal domain object.

```
Controller
    │
    ├── Model
    ├── Network
    ├── Analysis
    ├── Solver
    ├── Protection
    └── Simulation
```

> The controller does not replace specialized subsystem managers.

---

## 23. Base Layer

The `core/base/` layer contains foundational engineering infrastructure shared by multiple core subsystems. One important example is the canonical per-unit infrastructure.

> The purpose of the base layer is to provide stable low-level contracts without pulling higher-level domain logic downward. The dependency direction should remain controlled.

---

## 24. Dependency Direction

```
                 core.base
                    │
                    ▼
               core.model
                    │
                    ▼
              core.network
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     core.analysis        core.protection
          │                   │
          ▼                   │
      core.solver             │
          │                   │
          └─────────┬─────────┘
                    ▼
              core.simulation
```

> Validation and orchestration may interact with multiple layers without becoming the owner of their domain state. The exact dependency graph must remain acyclic and responsibility-driven.

---

## 25. No GUI Dependency

The core must never depend on GUI implementation.

**Forbidden:**
```
core
  │
  ▼
PySide6 / GUI
```

**Correct:**
```
GUI
 │
 ▼
Application / Controller
 │
 ▼
core
```

The core must be executable in:

- Command-line environments
- Automated tests
- Batch studies
- Headless simulations
- Future services
- Future real-time execution environments

---

## 26. No Persistence Dependency

The core must not own project-file I/O.

```
GUI
 │
 ▼
Persistence / Project Layer
 │
 ▼
Core Objects
```

The persistence layer is responsible for:

- Serialization
- Deserialization
- Project schema
- File paths
- File formats
- Reconstruction of core objects

> The core remains unaware of GUI file dialogs and application filesystem workflows.

---

## 27. Authoritative State Principle

Every important state category must have a clear owner.

| State | Authoritative Owner |
|---|---|
| Physical equipment | `core.model` |
| Physical terminals | `core.model` |
| Electrical topology | `core.network` |
| Per-unit representation | Canonical network/base infrastructure |
| Y-bus | `core.network` |
| Numerical solution | `core.solver` |
| Study interpretation | `core.analysis` |
| Protection function state | Protection function / protection subsystem |
| Protection decision | `ProtectionDecision` |
| Simulation runtime | `core.simulation` |
| Validation result | Validation subsystem |
| GUI state | GUI/application layer |
| Project persistence | Persistence layer |

> This prevents duplicate or conflicting sources of truth.

---

## 28. Derived State Principle

The core contains many derived representations, e.g.:

- Topology
- Y-bus
- Numerical indices
- Jacobian
- Mismatch vector
- Dynamic state
- Protection runtime state

Derived state must not be confused with authoritative physical state.

```
Authoritative State
       │
       ▼
Derived Representation
       │
       ▼
Numerical Execution
```

> When source state changes, dependent derived state must be invalidated or rebuilt.

---

## 29. Identity Principle

GridForge V2 maintains explicit separation between engineering identity and numerical identity.

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

> Numerical indices are implementation details. They must never replace stable physical identities.

---

## 30. State Ownership Principle

> A subsystem may derive representations of another subsystem's state, but it must not silently become the authoritative owner of that state.

**Example:**

```
Breaker Model
     │
     ▼
Network Interpretation
```

does **not** mean:

```
Network
     └── owns breaker state
```

Likewise:

```
MeasurementChannel
     │
     ▼
RelayInput
```

does **not** mean:

```
RelayInput
     └── owns measurement state
```

---

## 31. Study Isolation

A study should not corrupt the authoritative digital twin.

```
Base Network
      │
      ▼
Contingency Case
      │
      ▼
Temporary Network Condition
      │
      ▼
Solver
```

> The original model/network must remain intact unless the user explicitly commits a physical state change through the appropriate application workflow.

---

## 32. Determinism

GridForge V2 core services should favor deterministic behavior. Given identical:

- Model state
- Network state
- Study configuration
- Solver settings

...the system should produce reproducible:

- Topology
- Numerical indexing
- Network matrices
- Solver setup
- Study results within expected numerical tolerances

Determinism is particularly important for:

- Testing
- Regression validation
- Contingency analysis
- Protection event studies
- Debugging
- Reproducible engineering studies

---

## 33. Error Handling

Core subsystems should fail explicitly when authoritative data is invalid or required prerequisites are missing. Silent fallback is discouraged where it can produce physically misleading results.

Errors should distinguish between:

- Invalid Model
- Invalid Network
- Invalid Study
- Numerical Failure
- Runtime Failure
- Configuration Error

> A numerical non-convergence should not be confused with an invalid physical model.

---

## 34. Numerical Failure vs Engineering Failure

> **Engineering invalidity ≠ Numerical non-convergence**

`Invalid topology` is fundamentally different from `Valid topology, but Newton-Raphson did not converge`.

> The core architecture preserves this distinction so that diagnostics remain meaningful.

---

## 35. Core Execution Flow

A typical GridForge study follows:

```
1. Load / construct physical model
             │
             ▼
2. Validate model
             │
             ▼
3. Construct network representation
             │
             ▼
4. Validate network
             │
             ▼
5. Prepare study / analysis
             │
             ▼
6. Construct numerical representation
             │
             ▼
7. Execute solver
             │
             ▼
8. Produce numerical result
             │
             ▼
9. Interpret result
             │
             ▼
10. Publish study result
```

For dynamic/protection studies, runtime execution extends this flow:

```
Simulation State
      │
      ▼
Network / Dynamic State
      │
      ▼
Measurement
      │
      ▼
Protection Evaluation
      │
      ▼
Protection Decision
      │
      ▼
Scheme / Control
      │
      ▼
Physical Model State Update
```

---

## 36. Core Does Not Define the GUI

The core provides engineering services. The GUI is responsible for:

- Visual representation
- Interaction
- Tools
- Canvas management
- Rendering
- Selection
- User workflows

> The GUI may request operations from the core, but core objects must never require the GUI to function.

---

## 37. Core Does Not Define Project Persistence

Project persistence belongs to a dedicated serialization/project layer.

```
User
 │
 ▼
GUI
 │
 ▼
Persistence Layer
 │
 ▼
Core Model / Network / Study State
```

Loading reconstructs valid core objects. Saving serializes authoritative project state.

> The core itself should not contain arbitrary file-writing responsibilities.

---

## 38. Plugin Architecture

GridForge V2 is designed to permit domain-specific extensions without compromising the core architecture. Potential plugin domains include:

- Protection functions
- Generator dynamic models
- AVR models
- Governor models
- PSS models
- Specialized equipment
- Analysis extensions
- Solver backends

> Plugins should consume established core contracts rather than modifying fundamental ownership boundaries.

---

## 39. Protection Function Plugins

Concrete protection functions should implement the established protection contracts:

```python
from core.protection import RelayBase


class Overcurrent51(RelayBase):
    ...
```

The plugin owns its function-specific mathematics and runtime behavior. It does **not** own:

- Physical relay identity
- Measurement infrastructure
- Breaker operation
- GUI state

---

## 40. Dynamic Model Plugins

Dynamic models may similarly extend established simulation contracts.

```
Generator Model
      │
      ▼
Dynamic Model
      │
      ▼
Simulation Engine
      │
      ▼
Numerical Integrator
```

> The plugin architecture prevents the solver from becoming a repository of every possible physical model.

---

## 41. Testing Philosophy

Core subsystems should be testable independently, at multiple levels:

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
Numerical Regression Tests
    │
    ▼
End-to-End Engineering Studies
```

> The core should be testable without launching the GUI.

---

## 42. Numerical Regression

Numerical subsystems should maintain regression coverage for representative engineering cases, including:

- Convergence
- Expected voltages
- Expected power flows
- Expected fault currents
- Expected dynamic trajectories
- Topology behavior
- Protection decisions

> Regression tests are especially important when optimizing sparse or GPU-enabled implementations.

---

## 43. Performance Architecture

GridForge V2 is designed for scalable power-system computation, compatible with:

- Vectorized NumPy operations
- Sparse matrices
- Sparse Jacobians
- Batched contingency studies
- GPU acceleration
- Large-scale network analysis
- Repeated simulation
- Event-driven execution

> Performance optimization must never violate ownership or determinism requirements.

---

## 44. CPU and GPU Separation

The core architecture allows numerical backends to evolve independently of engineering models.

```
Engineering Representation
          │
          ▼
Numerical Representation
          │
      ┌───┴───┐
      ▼       ▼
     CPU     GPU
   Backend  Backend
```

> The physical model must not become CUDA-specific. The network model must not require a specific numerical backend.

---

## 45. Core API Stability

Public core interfaces should be treated as architectural contracts, exposed through:

```python
from core import ...
```

or the relevant subsystem:

```python
from core.model import ...
from core.network import ...
from core.protection import ...
```

> Internal implementation details should remain private unless deliberately promoted to public API.

---

## 46. Architectural Invariants

The following invariants must be preserved throughout GridForge V2.

**46.1 — Model Is the Physical Authority**
```
core.model = Physical / Engineering Authority
```

**46.2 — Network Is the Electrical Authority**
```
core.network = Electrical Network Representation
```

**46.3 — Solver Is the Numerical Executor**
```
core.solver = Numerical Execution
```

**46.4 — Analysis Is the Study Layer**
```
core.analysis = Engineering Study Orchestration / Interpretation
```

**46.5 — Protection Functions Produce Decisions**
```
Protection Function → ProtectionDecision
```
They do not directly operate equipment.

**46.6 — Simulation Owns Runtime Execution**
Transient runtime state belongs to the simulation/runtime architecture, not to the persistent model.

**46.7 — Derived State Is Not Authoritative**
Caches, matrices, indices, and runtime representations must not replace authoritative state.

**46.8 — Numerical Indices Are Not Engineering Identities**
Physical identities must remain stable independently of numerical indexing.

**46.9 — GUI Is Outside Core**
No core domain object may depend on GUI implementation.

**46.10 — Persistence Is Outside Core**
Core objects must not perform project-file I/O.

**46.11 — Plugins Respect Core Contracts**
Extensions must build on established interfaces rather than bypassing ownership boundaries.

**46.12 — Subsystems Remain Cohesive**
A subsystem must not absorb responsibilities belonging to another subsystem merely for convenience.

---

## 47. Dependency Rules

### ✅ Allowed

- Model → Network
- Network → Solver
- Analysis → Solver
- Protection → Measurement / Model / Network Context
- Simulation → Model / Network / Solver / Protection
- Validation → Relevant Core Layers
- Controller → Core Services

### ❌ Discouraged / Forbidden

- Core → GUI
- Core → GUI Rendering
- Core → File Dialog
- Model → Solver Implementation
- Solver → GUI
- Network → Protection Logic
- Protection → Direct Breaker Operation
- Protection → GUI

> The exact implementation may introduce carefully controlled interfaces, but responsibility ownership must remain unchanged.

---

## 48. Core as a Headless Engine

A major architectural requirement is that the GridForge core can operate without the graphical application.

```python
network = Network(...)
result = power_flow.solve(network)
```

```python
simulation = Simulation(...)
simulation.run()
```

> The GUI is therefore an application client of the core, not a prerequisite for the core.

---

## 49. Core and Digital Twin

GridForge V2 is fundamentally a power-system digital-twin platform. The core represents multiple levels of the twin:

```
Physical Reality
      │
      ▼
Engineering Model
      │
      ▼
Electrical Network
      │
      ▼
Numerical State
      │
      ▼
Simulation / Study
      │
      ▼
Engineering Result
```

This enables the same authoritative system model to support:

- Steady-state analysis
- Fault analysis
- Dynamic simulation
- Protection studies
- Contingency analysis
- Future real-time applications

---

## 50. Future Expansion

The core architecture is intentionally prepared for future capabilities including:

- Optimal power flow
- Security-constrained OPF
- Advanced protection coordination
- TCC analysis
- Transient stability
- EMT simulation
- Real-time digital-twin execution
- State estimation
- Network reduction
- Dynamic equivalents
- Hardware-in-the-loop integration
- SCADA integration
- Communication-assisted protection
- Distributed and GPU-accelerated computation

> Future capabilities should be introduced as new domain services or extensions rather than by weakening existing ownership boundaries.

---

## 51. Design Philosophy

GridForge V2 core follows a layered engineering model:

```
Physical Equipment
        ↓
Engineering Model
        ↓
Electrical Network
        ↓
Study / Analysis
        ↓
Numerical Solver
        ↓
Simulation / Protection
        ↓
Engineering Result
```

Each layer has a distinct responsibility. The central rule:

> **The core represents engineering truth; higher layers request operations from it, while presentation and persistence remain outside it.**

This prevents the GridForge architecture from becoming tightly coupled to:

- GUI implementation
- Storage format
- Numerical backend
- Individual solver algorithms
- Individual protection functions

---

## 52. Current Foundation Status

The GridForge V2 core foundation consists of:

```text
core/
├── __init__.py
├── analysis/
├── base/
├── controller.py
├── model/
├── network/
├── protection/
├── simulation/
├── solver/
└── validation/
```

The major foundational layers establish architectural boundaries for:

physical modeling · electrical networking · numerical analysis · power-flow computation · short-circuit computation · dynamics · protection · simulation · validation · orchestration

> The core is intended to remain a stable engineering foundation while concrete study capabilities continue to expand above these contracts.

---

## 53. Freeze Rules

Future changes to `core/` should follow these rules:

1. Do not redesign frozen foundational layers without a genuinely fundamental requirement.
2. Do not move GUI responsibilities into the core.
3. Do not move persistence/file I/O into domain objects.
4. Do not duplicate authoritative state between subsystems.
5. Do not make solver implementations the owners of physical models.
6. Do not make network representations the owners of physical equipment.
7. Do not allow protection functions to directly operate physical breakers.
8. Do not mix transient runtime state with persistent engineering configuration.
9. Do not replace stable physical identities with numerical indices.
10. Prefer extension through established contracts and plugins.
11. Preserve deterministic behavior where the architecture requires it.
12. Maintain clear dependency direction between core layers.
13. Preserve headless operation of the core.
14. Optimize implementation without changing architectural ownership.

---

## 54. Final Architectural Summary

The GridForge V2 core is based on the following fundamental separations:

```
Physical Model        ≠  Electrical Network
Electrical Network    ≠  Numerical Solver
Study Analysis         ≠  Numerical Algorithm
Protection Function    ≠  Physical Relay
Protection Decision    ≠  Breaker Operation
Persistent State        ≠  Runtime State
Engineering Identity    ≠  Numerical Index
Core                    ≠  GUI
Core                    ≠  Persistence
```

The complete GridForge V2 architecture:

```
                         GRIDFORGE APPLICATION
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
          GUI / UI                              Persistence
              │                                       │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
                              ┌───────┐
                              │ core/ │
                              └───┬───┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
      core.model             core.network            core.validation
          │                       │
          │               ┌───────┼────────┐
          │               │       │        │
          │               ▼       ▼        ▼
          │            Topology Per-Unit  Y-bus
          │               │       │        │
          └───────────────┴───────┴────────┘
                                  │
                                  ▼
                           core.analysis
                                  │
                                  ▼
                            core.solver
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                Power Flow   Short Circuit   Dynamics
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                           core.simulation
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
              Measurement                 Protection
                                               │
                                               ▼
                                      Protection Decision
                                               │
                                               ▼
                                       Scheme / Output
                                               │
                                               ▼
                                        Breaker Control
```

> The result is a modular, deterministic, extensible, headless-capable engineering core suitable for a full power-system digital twin.

---

## 55. Final Status

> **`core/README.md` → FINALIZE / FREEZE**

This document is the package-level architectural reference for the GridForge V2 Core.

The guiding architectural rule:

```
                    GRIDFORGE CORE

     Model → Network → Analysis → Solver
       │        │          │         │
       │        │          │         └── Numerical Execution
       │        │          └──────────── Study Interpretation
       │        └────────────────────── Electrical Representation
       └─────────────────────────────── Physical Authority

                    + Simulation
                    + Protection
                    + Validation

                    GUI / Persistence
                         OUTSIDE CORE
```

**The GridForge V2 core is the authoritative engineering execution layer of the platform.**

---

<p align="center"><em>core/ — engineering truth, owned once, derived everywhere else.</em></p>
