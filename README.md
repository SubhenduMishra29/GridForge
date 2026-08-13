GridForge

## Power-System Digital Twin & Simulation Platform

GridForge is a modular power-system engineering platform designed to
provide an integrated environment for **power-system modeling, analysis,
simulation, protection, visualization, and digital-twin applications**.

The platform is built around a strict separation between:

```text
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

GridForge V2 is being developed as a Python-based, extensible
power-system engineering platform capable of supporting steady-state
studies, fault analysis, contingency analysis, dynamic simulation,
protection studies, and future real-time digital-twin applications.

1. Vision

The objective of GridForge is to provide a unified engineering environment
for modeling, analyzing, simulating, and operating a digital representation
of an electrical power system.

The long-term vision is:

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

The platform is intended to support:

power-system modeling;
electrical network topology;
power-flow studies;
short-circuit studies;
contingency analysis;
dynamic simulation;
protection studies;
relay coordination;
TCC analysis;
future OPF / SCOPF;
future EMT simulation;
future real-time digital-twin execution;
engineering visualization;
extensible domain plugins.
2. GridForge V2 Architecture

GridForge V2 is organized as a layered engineering system.

┌──────────────────────────────────────────────────────────┐
│                     GridForge Application                 │
│                                                          │
│       GUI • Tools • Rendering • Controllers • UX         │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                         GridForge Core                    │
│                                                          │
│ Model • Network • Analysis • Solver • Protection         │
│ Simulation • Validation • Controllers                    │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────┐
│                  Numerical / Backend Layer                │
│                                                          │
│       NumPy • SciPy • Sparse • GPU Backends             │
└──────────────────────────────────────────────────────────┘

The core remains independent of the graphical user interface and project
persistence system.

3. Repository Structure

The high-level GridForge repository is organized approximately as:

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

The exact directory contents may evolve, but the architectural separation
must remain intact.

4. Core Architecture

The core/ package is the authoritative engineering execution layer.

core/
│
├── model/
│       Physical / engineering objects
│
├── network/
│       Electrical network representation
│
├── analysis/
│       Engineering study services
│
├── solver/
│       Numerical computation
│
├── protection/
│       Protection-function execution
│
├── simulation/
│       Runtime and dynamic execution
│
├── validation/
│       Engineering and structural validation
│
└── controller.py
        Core orchestration

The core does not depend on GUI implementation.

5. Physical Model

The model layer represents what physically exists in the digital twin.

Typical engineering entities include:

buses;
generators;
loads;
transmission lines;
cables;
transformers;
breakers;
switches;
shunts;
motors;
measurement equipment;
protection equipment;
terminals;
other domain-specific equipment.

The model is the authoritative owner of physical equipment identity and
engineering configuration.

6. Asset / Equipment / Component / Device Semantics

GridForge uses explicit engineering semantics for:

Asset
Equipment
Component
Device

These are semantic classifications rather than a mandatory universal
inheritance hierarchy.

The intended interpretation is:

Asset
    Persistent identifiable entity

Equipment
    Engineered physical apparatus

Component
    Engineering-significant constituent part

Device
    Independently identifiable functional apparatus

Specialized domain implementations may therefore be introduced without
creating an artificial monolithic class hierarchy.

7. Electrical Network

The network layer converts the physical model into an authoritative
electrical representation.

It manages concepts such as:

electrical topology;
connectivity;
terminals;
buses/nodes;
branches;
deterministic network indexing;
per-unit representation;
Y-bus construction;
network-derived electrical structures.

The relationship is:

Physical Model
      │
      ▼
Electrical Network
      │
      ├── Topology
      ├── Per-Unit
      └── Y-Bus

The network does not become the owner of physical equipment.

8. Analysis Layer

The analysis layer defines engineering studies.

Current analysis domains include:

Power Flow
Line Flow
Transformer Flow
Short Circuit
Contingency

The analysis layer determines what engineering problem is being
investigated.

The numerical solver determines how that problem is solved.

Therefore:

Analysis ≠ Solver
9. Solver Architecture

The solver layer provides numerical execution engines.

Current solver domains include:

core/solver/
│
├── common/
├── contingency/
├── dynamics/
├── power_flow/
└── short_circuit/

The solver architecture is designed for scalable numerical computation.

Potential computational technologies include:

NumPy;
SciPy;
sparse matrix algorithms;
vectorized numerical operations;
batched calculations;
GPU acceleration.

The numerical backend must remain independent of the physical model
architecture.

10. Power Flow

GridForge provides a dedicated power-flow solver architecture for
steady-state network analysis.

The numerical framework is designed to support:

Newton-Raphson;
adaptive line search;
trust-region methods;
Levenberg-Marquardt / hybrid approaches;
continuation power flow;
predictor-corrector methods;
contingency screening;
sparse Jacobian assembly;
CPU and future GPU execution.

Conceptually:

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
11. Short-Circuit Analysis

The short-circuit subsystem provides fault-analysis capabilities.

The architecture is designed to support:

fault definition;
fault location;
fault type;
sequence-network calculations;
fault currents;
bus voltages;
branch currents;
fault-study results.

The short-circuit solver consumes the authoritative network representation
rather than maintaining a separate physical network model.

12. Dynamics

The dynamics subsystem provides time-domain power-system simulation.

It is intended to support dynamic models for:

generators;
governors;
excitation systems;
power-system stabilizers;
other dynamic equipment and models.

The architecture separates:

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

The dynamics subsystem is independent of steady-state power flow and
short-circuit numerical implementations.

13. Protection

GridForge V2 uses a multifunction protection architecture.

A physical relay is not assumed to represent a single protection function.

For example:

Relay R1
│
├── 50  Instantaneous Overcurrent
├── 51  Time Overcurrent
├── 46  Negative Sequence
├── 67  Directional Overcurrent
└── 50BF Breaker Failure

The architecture is:

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

This allows realistic multifunction numerical relay configurations.

14. Measurement Architecture

Protection functions consume authoritative measurement infrastructure.

The intended flow is:

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

Measurement state must have one authoritative owner.

Protection functions must not create independent copies of:

CT state;
PT state;
CVT state;
scaling;
measurement caches.

This ensures multiple protection functions consume consistent electrical
measurements.

15. Protection Decision Boundary

Protection functions produce protection decisions.

They do not directly operate physical breakers.

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

This architecture allows future implementation of:

breaker failure;
autoreclose;
permissive schemes;
blocking;
interlocking;
transfer trip;
trip-circuit supervision;
communication-assisted protection.
16. Simulation Architecture

Simulation provides runtime execution of the digital twin.

A typical simulation cycle is:

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

Transient runtime state is kept separate from persistent engineering
configuration.

17. Validation

GridForge validates engineering state before and during execution.

Validation may cover:

Model
  ↓
Network
  ↓
Study Configuration
  ↓
Numerical Preconditions
  ↓
Runtime Conditions

Validation distinguishes engineering invalidity from numerical failure.

For example:

Invalid topology

is fundamentally different from:

Valid topology
+
Numerical solver did not converge
18. GUI Architecture

GridForge provides a modern 2D engineering interface designed around
power-system visualization and interactive system modeling.

The GUI is intended to provide:

single-line diagram visualization;
bus-centric editing;
interactive equipment placement;
topology-aware connections;
snapping;
engineering tools;
multi-canvas navigation;
property editing;
simulation visualization;
protection visualization;
analysis-result visualization.

The GUI is a client of the core.

It does not own engineering truth.

19. GUI and Core Separation

The fundamental rule is:

GUI
 │
 ▼
Application / Controller
 │
 ▼
Core

Not:

Core
 │
 ▼
GUI

Core objects must never require:

Qt widgets;
graphics scenes;
rendering objects;
GUI controllers;
mouse events;
UI state.

This allows GridForge to run headlessly.

20. Qt Architecture

The GridForge GUI uses PySide6 as its Qt framework.

GUI code should not introduce mixed Qt frameworks.

A centralized Qt abstraction layer is used so that GUI implementation
details remain controlled.

Conceptually:

PySide6
   │
   ▼
gui/core/qt.py
   │
   ▼
GridForge GUI
21. Multi-Canvas Architecture

GridForge is designed around hierarchical engineering visualization.

Conceptually:

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

This permits navigation between:

grid-level views;
substation-level views;
equipment-level views;
detailed engineering contexts.
22. Bus-Centric Network Editing

Electrical connections are governed by engineering topology rather than
arbitrary graphical proximity.

The connection architecture is intended to enforce:

Valid Electrical Connection
        ✓

Invalid Electrical Connection
        ✗

A graphical line is therefore not merely a drawing object.

It represents an electrical relationship in the core network.

23. Rendering Architecture

Rendering is separated from engineering state.

Conceptually:

Core Model
     │
     ▼
Render System
     │
     ├── BusRenderer
     ├── LineRenderer
     ├── TransformerRenderer
     └── Equipment Renderers

Renderers visualize authoritative objects.

They do not become the owners of those objects.

24. Interaction Architecture

The GUI interaction system is designed around specialized services such
as:

InteractionManager;
Tool System;
Snap System;
Grid System;
Navigation Controller;
Coordinate System;
Rendering System;
Canvas Controller.

The purpose is to prevent individual GUI widgets from becoming
monolithic controllers.

25. Plugin Architecture

GridForge is designed for extensibility through plugins.

Potential plugin domains include:

Protection Functions
Dynamic Models
Equipment Models
Analysis Extensions
Solver Backends
Visualization
Engineering Tools

Plugins should consume stable GridForge contracts.

They should not bypass core ownership boundaries.

26. Persistence Architecture

Project persistence is intentionally separated from the core.

The intended architecture is:

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

Core model objects should not contain arbitrary JSON/file I/O or GUI file
dialog logic.

Loaded projects are reconstructed into authoritative core objects.

27. Digital-Twin State Ownership

GridForge follows a strict state-ownership principle.

Domain	Authoritative Owner
Physical equipment	core.model
Electrical topology	core.network
Per-unit representation	Base/network infrastructure
Y-bus	core.network
Numerical computation	core.solver
Study interpretation	core.analysis
Protection function	Protection subsystem
Protection decision	ProtectionDecision
Runtime simulation	core.simulation
Validation	core.validation
GUI state	GUI
Project persistence	Persistence layer

Derived representations must never silently replace authoritative state.

28. Identity Architecture

GridForge separates engineering identity from numerical indexing.

Asset ID
   ≠
Equipment ID
   ≠
Terminal ID
   ≠
Network Node ID
   ≠
Numerical Index

Numerical indices may change as a result of network reconstruction.

Engineering identities must remain stable.

29. Determinism

GridForge prioritizes deterministic engineering behavior.

Identical:

model state;
network topology;
study configuration;
solver settings;

should produce reproducible results within expected numerical tolerances.

Determinism is particularly important for:

regression testing;
contingency analysis;
protection studies;
simulation;
debugging;
engineering verification.
30. Performance

GridForge is designed for large-scale power-system computation.

The architecture is compatible with:

vectorized computation;
sparse matrices;
sparse Jacobians;
batched contingency analysis;
GPU acceleration;
repeated simulations;
large network models.

Performance optimization must not compromise engineering correctness or
state ownership.

31. CPU / GPU Backend Independence

Numerical backends are implementation details.

The architecture permits:

                    Numerical Representation
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                      CPU           GPU
                    Backend       Backend

The physical model and network model remain backend-independent.

This permits future GPU acceleration without redesigning the engineering
model.

32. Headless Operation

GridForge Core is designed to run without the GUI.

For example:

network = Network(...)
result = power_flow.solve(network)

or:

simulation = Simulation(...)
simulation.run()

This makes the platform suitable for:

automated studies;
batch analysis;
regression testing;
server-side execution;
optimization;
future real-time applications.
33. Testing Strategy

GridForge uses layered testing.

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

Tests should verify both:

software correctness;
engineering correctness.
34. Engineering Regression

Representative engineering cases should be maintained for:

power flow;
short circuit;
contingency;
dynamics;
protection;
network topology.

Regression validation should cover both numerical values and expected
engineering behavior.

35. Architectural Rules

The following rules are fundamental to GridForge V2.

Rule 1 — One authoritative owner per state

Do not maintain competing copies of important engineering state.

Rule 2 — Model owns physical equipment

The solver must not become the equipment model.

Rule 3 — Network owns electrical representation

The GUI must not become the topology engine.

Rule 4 — Solver owns numerical execution

The model must not contain solver algorithms.

Rule 5 — Analysis and solver remain separate

A study definition is not the same thing as its numerical algorithm.

Rule 6 — Protection functions produce decisions

Protection functions do not directly operate breakers.

Rule 7 — Measurement has one authoritative owner

Protection functions consume measurement infrastructure.

Rule 8 — Runtime state is separate from persistent state

Simulation state must not silently become engineering configuration.

Rule 9 — GUI is outside the core

Core objects must remain headless-capable.

Rule 10 — Persistence is outside domain objects

Engineering models must not become file-management classes.

Rule 11 — Numerical indices are not engineering identities

Stable engineering identities must survive numerical reconstruction.

Rule 12 — Plugins respect established contracts

Extensions must not bypass architectural ownership.

36. Engineering Execution Flow

A complete GridForge workflow can be represented as:

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
37. Future Engineering Capabilities

The architecture is prepared for expansion into:

Steady-State
AC power flow;
DC power flow;
continuation power flow;
optimal power flow;
security-constrained OPF;
voltage stability analysis.
Fault Analysis
three-phase faults;
single-line-to-ground faults;
line-to-line faults;
double-line-to-ground faults;
sequence networks;
fault contribution analysis.
Contingency
N-1 analysis;
N-k analysis;
fast screening;
ranking;
security assessment.
Dynamics
transient stability;
AVR;
governor;
PSS;
generator models;
motor dynamics;
dynamic load models.
Protection
overcurrent;
directional overcurrent;
distance;
differential;
voltage;
frequency;
breaker failure;
autoreclose;
protection coordination;
TCC.
Advanced Simulation
EMT;
real-time simulation;
hardware-in-the-loop;
communication-assisted protection.
Digital Twin
SCADA integration;
online measurements;
state estimation;
real-time monitoring;
event recording;
predictive analysis.
38. Development Philosophy

GridForge development follows a layer-by-layer engineering freeze
process.

A subsystem is:

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

Once a foundational subsystem is frozen, it should not be redesigned
without identifying a genuinely fundamental architectural requirement.

This protects the project from continuous architectural drift.

39. V2 Architectural Baseline

GridForge V2 establishes the following major architectural boundaries:

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
40. What GridForge Is Not

GridForge is not intended to be:

a GUI-only drawing application;
a collection of independent numerical scripts;
a monolithic solver;
a monolithic equipment class hierarchy;
a relay-only protection simulator;
a database disguised as an engineering model;
a file-format-dependent core;
a GUI-dependent simulation engine.

GridForge is intended to be an integrated engineering platform with a
single coherent digital-twin architecture.

41. Guiding Principle

The central architectural principle of GridForge is:

Represent engineering truth once, derive specialized representations
from it, execute studies through independent numerical services, and
keep visualization and persistence outside the authoritative engineering
core.

This principle governs the relationship between every major GridForge
subsystem.

42. Final Architecture

The complete conceptual architecture is:

                         ┌───────────────────┐
                         │      USER / UI    │
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
43. Project Status

GridForge V2 is being developed as a layered, modular, extensible
power-system digital-twin platform.

The architectural foundation establishes clear boundaries for:

physical modeling;
network representation;
analysis;
numerical solvers;
dynamics;
protection;
simulation;
validation;
GUI;
persistence;
plugins.

The objective is not merely to implement individual engineering
calculations, but to provide a coherent platform in which those
calculations operate on a common authoritative digital representation of
the electrical system.

44. Status

GridForge V2 — Architectural Foundation

Model        → Engineering Authority
Network      → Electrical Authority
Analysis     → Study Authority
Solver       → Numerical Execution
Protection   → Protection Execution
Simulation   → Runtime Execution
Validation   → Engineering Integrity
GUI          → Visualization / Interaction
Persistence  → Project State Management
Plugins      → Extensibility

GridForge V2 is designed as a unified engineering platform rather than
a collection of disconnected power-system tools.
