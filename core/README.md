# GridForge V2 Core

## Overview

The `core/` package is the **authoritative engineering and simulation
foundation** of GridForge V2.

It contains the domain model, electrical network representation,
numerical solvers, analysis services, protection framework, simulation
infrastructure, validation, and core orchestration required to operate the
GridForge power-system digital twin.

The core is intentionally independent of:

- GUI implementation
- Rendering
- User-interface state
- File dialogs
- Project-file I/O
- Presentation logic
- Platform-specific UI services

The fundamental architectural principle is:

```text
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

The core/ package is therefore the source of engineering truth and
executable domain behavior.

1. Architectural Position

GridForge V2 follows a layered architecture in which the core sits below
application/UI concerns and above low-level numerical implementation
details.

┌─────────────────────────────────────────────────────┐
│                    Application / GUI                │
│                                                     │
│  Canvas • Tools • Controllers • Rendering • UI      │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                         core/                       │
│                                                     │
│  Model • Network • Analysis • Solver • Protection   │
│  Simulation • Validation • Controllers              │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              Numerical / Platform Libraries         │
│                                                     │
│      NumPy • SciPy • Sparse • GPU Backends          │
└─────────────────────────────────────────────────────┘

The core must remain usable without the GUI.

2. Core Architectural Principle

The core is organized around a strict separation of responsibilities:

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

Additional domain execution layers consume authoritative state:

Measurement
      │
      ▼
Protection
      │
      ▼
Protection Decision

The core therefore distinguishes between:

What exists
    → Model

How it is electrically connected
    → Network

What study is being performed
    → Analysis

How the mathematical problem is solved
    → Solver

How protection functions execute
    → Protection

How time-domain behavior is executed
    → Simulation

Whether state is valid
    → Validation
3. Package Structure

The GridForge V2 core is organized as:

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

Each package has a defined architectural responsibility.

4. Core Module Responsibilities
4.1 core/model/

The model layer represents the authoritative physical and engineering
entities of the GridForge digital twin.

It describes what physically exists.

Examples include:

buses
generators
loads
lines
transformers
breakers
switches
shunts
motors
physical protection equipment
other engineering equipment and domain objects

The model layer owns persistent engineering identity and equipment
configuration.

Conceptually:

core.model
    │
    ├── Equipment
    ├── Components
    ├── Devices
    ├── Terminals
    └── Engineering State

The model layer does not become the numerical solver.

5. Asset, Equipment, Component and Device Semantics

GridForge V2 maintains explicit semantic distinctions between:

Asset
Equipment
Component
Device

These are engineering classifications and should not be forced into a
giant inheritance hierarchy.

The distinction is:

Asset
    = Persistent identifiable entity

Equipment
    = Engineered physical apparatus

Component
    = Engineering-significant constituent part

Device
    = Independently identifiable functional apparatus

A specialized implementation may participate in multiple engineering
domains without requiring an artificial universal inheritance tree.

6. Model as Physical Authority

The model layer is the authoritative owner of physical equipment state.

For example:

Breaker
    │
    ├── identity
    ├── terminals
    ├── rating
    └── physical state

The network layer interprets the breaker state electrically.

The protection layer may consume breaker information.

The GUI displays it.

However, the physical model remains the authoritative owner.

7. core/network/

The network layer provides the electrical interpretation of the physical
model.

Its responsibilities include:

topology
electrical connectivity
network nodes
branch relationships
deterministic indexing
per-unit representation
Y-bus construction
network-level derived structures

The fundamental relationship is:

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

The network layer does not own physical equipment.

It does not execute complete numerical studies.

8. core/analysis/

The analysis layer provides study-level engineering services and
result-oriented analysis.

Examples include:

power-flow analysis
line-flow analysis
transformer-flow analysis
short-circuit analysis
contingency analysis

The analysis layer coordinates study requirements and interprets solver
outputs.

Conceptually:

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

Analysis is therefore distinct from the numerical algorithm itself.

9. Analysis vs Solver

A critical architectural distinction is:

Analysis
    ≠
Solver

For example:

Power Flow Analysis
        │
        ▼
Power Flow Solver
        │
        ▼
Numerical Result

The analysis layer determines what the engineering study requires.

The solver determines how the mathematical problem is solved.

10. core/solver/

The solver layer provides the numerical execution engines of
GridForge V2.

It includes study-specific numerical implementations such as:

core/solver/
├── common/
├── contingency/
├── dynamics/
├── power_flow/
└── short_circuit/

The exact internal structure may evolve, but solver responsibilities remain
separate from model and network ownership.

The solver consumes authoritative network/model representations and produces
numerical results.

11. Numerical Solver Principle

The solver architecture follows:

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

The solver must not silently become the owner of:

physical equipment
GUI state
project state
protection configuration
authoritative network identity
12. Common Numerical Infrastructure

Shared numerical infrastructure belongs below study-specific solvers.

Examples include:

mismatch calculations
Jacobian assembly
numerical convergence utilities
sparse matrix utilities
solver diagnostics
common numerical data structures

The purpose is to avoid duplicate implementations across numerical
studies.

For example:

                 Numerical Common Layer
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Power Flow    Short Circuit    Dynamics
13. Power Flow

The GridForge power-flow subsystem provides numerical methods for solving
steady-state electrical network equations.

The architecture supports advanced numerical strategies including:

Newton-Raphson
adaptive line search
trust-region approaches
Levenberg-Marquardt / hybrid methods
continuation / predictor-corrector methods
fast contingency screening
scalable sparse numerical operations

The solver operates on the network representation rather than directly
manipulating GUI or physical equipment objects.

14. Short Circuit

The short-circuit subsystem provides fault-analysis computation.

Its responsibilities include:

fault formulation
network fault representation
fault-current calculation
voltage response
sequence-network handling where applicable
fault-study results

It consumes the authoritative network representation.

It does not own physical network topology.

15. Dynamics

The dynamics subsystem provides time-domain simulation infrastructure for
dynamic power-system behavior.

It supports the execution of dynamic models and numerical integration.

The architecture separates:

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

The dynamics subsystem is distinct from steady-state power flow and
short-circuit computation.

16. core/protection/

The protection subsystem provides the execution framework for protection
functions.

Its architectural structure is:

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

A physical relay is therefore not assumed to equal one protection
function.

A multifunction relay may contain:

Relay R1
│
├── 50
├── 51
├── 46
├── 67
└── 50BF
17. Protection Measurement Boundary

Protection functions consume authoritative measurement infrastructure.

The intended architecture is:

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

Protection functions must not independently create duplicate:

CT state
PT state
measurement caches
scaling logic
instrument transformations

The measurement subsystem remains authoritative.

18. Protection Decision Boundary

Protection functions produce decisions.

They do not directly operate physical equipment.

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

This separation permits future:

interlocking
breaker failure
autoreclose
permissive schemes
transfer trip
trip circuit supervision
communication-assisted protection
19. core/simulation/

The simulation layer provides the execution environment for time-dependent
and event-driven system behavior.

It coordinates:

simulation time
event sequencing
simulation state
subsystem execution
dynamic updates
protection evaluation
equipment/control interactions

The simulation layer must not duplicate the authoritative state of the
model or network.

20. Simulation State vs Physical State

Simulation runtime state must remain distinct from persistent physical
configuration.

Conceptually:

Physical Model
     │
     ▼
Persistent Configuration

Simulation
     │
     ▼
Transient Runtime State

For example:

Generator Model
     │
     ├── physical parameters
     └── configuration

Generator Runtime
     │
     ├── rotor angle
     ├── speed
     └── dynamic states

Runtime state is required for execution but is not automatically the
authoritative project model.

21. core/validation/

The validation layer provides domain and architectural consistency checks.

Validation may operate at several levels:

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

Validation should detect invalid states before they produce misleading
numerical results.

Examples include:

invalid equipment configuration
unresolved terminals
invalid topology
inconsistent network data
invalid study configuration
missing required parameters
incompatible numerical conditions
22. core/controller.py

The core controller provides application-level orchestration between core
services.

It should coordinate workflows without becoming a universal domain object.

For example:

Controller
    │
    ├── Model
    ├── Network
    ├── Analysis
    ├── Solver
    ├── Protection
    └── Simulation

The controller does not replace specialized subsystem managers.

23. Base Layer

The core/base/ layer contains foundational engineering infrastructure
shared by multiple core subsystems.

One important example is the canonical per-unit infrastructure.

The purpose of the base layer is to provide stable low-level contracts
without pulling higher-level domain logic downward.

The dependency direction should remain controlled.

24. Dependency Direction

The intended core dependency direction is broadly:

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

Validation and orchestration may interact with multiple layers without
becoming the owner of their domain state.

The exact dependency graph must remain acyclic and
responsibility-driven.

25. No GUI Dependency

The core must never depend on GUI implementation.

Forbidden architectural direction:

core
  │
  ▼
PySide6 / GUI

The correct direction is:

GUI
 │
 ▼
Application / Controller
 │
 ▼
core

The core must be executable in:

command-line environments
automated tests
batch studies
headless simulations
future services
future real-time execution environments
26. No Persistence Dependency

The core must not own project-file I/O.

The architecture is:

GUI
 │
 ▼
Persistence / Project Layer
 │
 ▼
Core Objects

The persistence layer is responsible for:

serialization
deserialization
project schema
file paths
file formats
reconstruction of core objects

The core remains unaware of GUI file dialogs and application filesystem
workflows.

27. Authoritative State Principle

Every important state category must have a clear owner.

State	Authoritative Owner
Physical equipment	core.model
Physical terminals	core.model
Electrical topology	core.network
Per-unit representation	Canonical network/base infrastructure
Y-bus	core.network
Numerical solution	core.solver
Study interpretation	core.analysis
Protection function state	Protection function / protection subsystem
Protection decision	ProtectionDecision
Simulation runtime	core.simulation
Validation result	Validation subsystem
GUI state	GUI/application layer
Project persistence	Persistence layer

This prevents duplicate or conflicting sources of truth.

28. Derived State Principle

The core contains many derived representations.

Examples include:

topology
Y-bus
numerical indices
Jacobian
mismatch vector
dynamic state
protection runtime state

Derived state must not be confused with authoritative physical state.

Conceptually:

Authoritative State
       │
       ▼
Derived Representation
       │
       ▼
Numerical Execution

When source state changes, dependent derived state must be invalidated or
rebuilt.

29. Identity Principle

GridForge V2 maintains explicit separation between engineering identity
and numerical identity.

Asset ID
    ≠
Equipment ID
    ≠
Terminal ID
    ≠
Network Node ID
    ≠
Numerical Index

Numerical indices are implementation details.

They must never replace stable physical identities.

30. State Ownership Principle

The core follows a strict rule:

A subsystem may derive representations of another subsystem's state, but
it must not silently become the authoritative owner of that state.

For example:

Breaker Model
     │
     ▼
Network Interpretation

does not mean:

Network
     └── owns breaker state

Likewise:

MeasurementChannel
     │
     ▼
RelayInput

does not mean:

RelayInput
     └── owns measurement state
31. Study Isolation

A study should not corrupt the authoritative digital twin.

For example, contingency analysis may require:

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

The original model/network must remain intact unless the user explicitly
commits a physical state change through the appropriate application
workflow.

32. Determinism

GridForge V2 core services should favor deterministic behavior.

Given identical:

model state
network state
study configuration
solver settings

the system should produce reproducible:

topology
numerical indexing
network matrices
solver setup
study results within expected numerical tolerances

Determinism is particularly important for:

testing
regression validation
contingency analysis
protection event studies
debugging
reproducible engineering studies
33. Error Handling

Core subsystems should fail explicitly when authoritative data is invalid
or required prerequisites are missing.

Silent fallback is discouraged where it can produce physically misleading
results.

Errors should distinguish between:

Invalid Model
Invalid Network
Invalid Study
Numerical Failure
Runtime Failure
Configuration Error

A numerical non-convergence should not be confused with an invalid
physical model.

34. Numerical Failure vs Engineering Failure

GridForge V2 distinguishes:

Engineering invalidity
        ≠
Numerical non-convergence

For example:

Invalid topology

is fundamentally different from:

Valid topology
but Newton-Raphson did not converge

The core architecture preserves this distinction so that diagnostics
remain meaningful.

35. Core Execution Flow

A typical GridForge study follows:

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

For dynamic/protection studies, runtime execution extends this flow:

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
36. Core Does Not Define the GUI

The core provides engineering services.

The GUI is responsible for:

visual representation
interaction
tools
canvas management
rendering
selection
user workflows

The GUI may request operations from the core, but core objects must never
require the GUI to function.

37. Core Does Not Define Project Persistence

Project persistence belongs to a dedicated serialization/project layer.

The expected architecture is:

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

Loading reconstructs valid core objects.

Saving serializes authoritative project state.

The core itself should not contain arbitrary file-writing responsibilities.

38. Plugin Architecture

GridForge V2 is designed to permit domain-specific extensions without
compromising the core architecture.

Potential plugin domains include:

protection functions
generator dynamic models
AVR models
governor models
PSS models
specialized equipment
analysis extensions
solver backends

Plugins should consume established core contracts rather than modifying
fundamental ownership boundaries.

39. Protection Function Plugins

Concrete protection functions should implement the established protection
contracts.

For example:

from core.protection import RelayBase


class Overcurrent51(RelayBase):
    ...

The plugin owns its function-specific mathematics and runtime behavior.

It does not own:

physical relay identity
measurement infrastructure
breaker operation
GUI state
40. Dynamic Model Plugins

Dynamic models may similarly extend established simulation contracts.

Conceptually:

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

The plugin architecture prevents the solver from becoming a repository
of every possible physical model.

41. Testing Philosophy

Core subsystems should be testable independently.

Testing should occur at multiple levels:

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

The core should be testable without launching the GUI.

42. Numerical Regression

Numerical subsystems should maintain regression coverage for
representative engineering cases.

Important checks include:

convergence
expected voltages
expected power flows
expected fault currents
expected dynamic trajectories
topology behavior
protection decisions

Regression tests are especially important when optimizing sparse or
GPU-enabled implementations.

43. Performance Architecture

GridForge V2 is designed for scalable power-system computation.

The core therefore supports architecture compatible with:

vectorized NumPy operations
sparse matrices
sparse Jacobians
batched contingency studies
GPU acceleration
large-scale network analysis
repeated simulation
event-driven execution

Performance optimization must never violate ownership or determinism
requirements.

44. CPU and GPU Separation

The core architecture allows numerical backends to evolve independently
of engineering models.

Conceptually:

Engineering Representation
          │
          ▼
Numerical Representation
          │
      ┌───┴───┐
      ▼       ▼
     CPU     GPU
   Backend  Backend

The physical model must not become CUDA-specific.

The network model must not require a specific numerical backend.

45. Core API Stability

Public core interfaces should be treated as architectural contracts.

A stable public API should be exposed through:

from core import ...

or the relevant subsystem:

from core.model import ...
from core.network import ...
from core.protection import ...

Internal implementation details should remain private unless deliberately
promoted to public API.

46. Architectural Invariants

The following invariants must be preserved throughout GridForge V2.

46.1 Model Is the Physical Authority
core.model
    =
Physical / Engineering Authority
46.2 Network Is the Electrical Authority
core.network
    =
Electrical Network Representation
46.3 Solver Is the Numerical Executor
core.solver
    =
Numerical Execution
46.4 Analysis Is the Study Layer
core.analysis
    =
Engineering Study Orchestration / Interpretation
46.5 Protection Functions Produce Decisions
Protection Function
       ↓
ProtectionDecision

They do not directly operate equipment.

46.6 Simulation Owns Runtime Execution

Transient runtime state belongs to the simulation/runtime architecture,
not to the persistent model.

46.7 Derived State Is Not Authoritative

Caches, matrices, indices, and runtime representations must not replace
authoritative state.

46.8 Numerical Indices Are Not Engineering Identities

Physical identities must remain stable independently of numerical
indexing.

46.9 GUI Is Outside Core

No core domain object may depend on GUI implementation.

46.10 Persistence Is Outside Core

Core objects must not perform project-file I/O.

46.11 Plugins Respect Core Contracts

Extensions must build on established interfaces rather than bypassing
ownership boundaries.

46.12 Subsystems Remain Cohesive

A subsystem must not absorb responsibilities belonging to another
subsystem merely for convenience.

47. Dependency Rules

The following dependency rules should be maintained.

Allowed
Model → Network
Network → Solver
Analysis → Solver
Protection → Measurement / Model / Network Context
Simulation → Model / Network / Solver / Protection
Validation → Relevant Core Layers
Controller → Core Services
Discouraged / Forbidden
Core → GUI
Core → GUI Rendering
Core → File Dialog
Model → Solver Implementation
Solver → GUI
Network → Protection Logic
Protection → Direct Breaker Operation
Protection → GUI

The exact implementation may introduce carefully controlled interfaces,
but responsibility ownership must remain unchanged.

48. Core as a Headless Engine

A major architectural requirement is that the GridForge core can operate
without the graphical application.

For example:

network = Network(...)
result = power_flow.solve(network)

or:

simulation = Simulation(...)
simulation.run()

The GUI is therefore an application client of the core, not a prerequisite
for the core.

49. Core and Digital Twin

GridForge V2 is fundamentally a power-system digital-twin platform.

The core represents multiple levels of the twin:

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

This enables the same authoritative system model to support:

steady-state analysis
fault analysis
dynamic simulation
protection studies
contingency analysis
future real-time applications
50. Future Expansion

The core architecture is intentionally prepared for future capabilities
including:

optimal power flow
security-constrained OPF
advanced protection coordination
TCC analysis
transient stability
EMT simulation
real-time digital-twin execution
state estimation
network reduction
dynamic equivalents
hardware-in-the-loop integration
SCADA integration
communication-assisted protection
distributed and GPU-accelerated computation

Future capabilities should be introduced as new domain services or
extensions rather than by weakening existing ownership boundaries.

51. Design Philosophy

GridForge V2 core follows a layered engineering model:

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

Each layer has a distinct responsibility.

The central rule is:

The core represents engineering truth; higher layers request
operations from it, while presentation and persistence remain outside
it.

This prevents the GridForge architecture from becoming tightly coupled
to:

GUI implementation
storage format
numerical backend
individual solver algorithms
individual protection functions
52. Current Foundation Status

The GridForge V2 core foundation consists of:

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

The major foundational layers establish architectural boundaries for:

physical modeling
electrical networking
numerical analysis
power-flow computation
short-circuit computation
dynamics
protection
simulation
validation
orchestration

The core is intended to remain a stable engineering foundation while
concrete study capabilities continue to expand above these contracts.

53. Freeze Rules

Future changes to core/ should follow these rules:

Do not redesign frozen foundational layers without a genuinely
fundamental requirement.
Do not move GUI responsibilities into the core.
Do not move persistence/file I/O into domain objects.
Do not duplicate authoritative state between subsystems.
Do not make solver implementations the owners of physical models.
Do not make network representations the owners of physical equipment.
Do not allow protection functions to directly operate physical
breakers.
Do not mix transient runtime state with persistent engineering
configuration.
Do not replace stable physical identities with numerical indices.
Prefer extension through established contracts and plugins.
Preserve deterministic behavior where the architecture requires it.
Maintain clear dependency direction between core layers.
Preserve headless operation of the core.
Optimize implementation without changing architectural ownership.
54. Final Architectural Summary

The GridForge V2 core is based on the following fundamental separations:

Physical Model
       ≠
Electrical Network
Electrical Network
       ≠
Numerical Solver
Study Analysis
       ≠
Numerical Algorithm
Protection Function
       ≠
Physical Relay
Protection Decision
       ≠
Breaker Operation
Persistent State
       ≠
Runtime State
Engineering Identity
       ≠
Numerical Index
Core
       ≠
GUI
Core
       ≠
Persistence

The complete GridForge V2 architecture can therefore be represented as:

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

The result is a modular, deterministic, extensible, headless-capable
engineering core suitable for a full power-system digital twin.

55. Final Status

core/README.md → FINALIZE / FREEZE

This document is the package-level architectural reference for the
GridForge V2 Core.

The guiding architectural rule is:

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

The GridForge V2 core is the authoritative engineering execution layer
of the platform.
