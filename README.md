# GridForge V2

## Power-System Digital Twin, Engineering, Simulation and Automation Platform

**Author:** Subhendu Mishra

GridForge is a Python-based power-system engineering platform for creating, editing, validating, studying, simulating, documenting and operating digital representations of electrical power systems.

GridForge is designed as a **one-stop engineering environment for power-system engineers**, while maintaining strict separation between:

* authoritative electrical engineering truth;
* application orchestration;
* user interaction;
* graphical presentation;
* studies and solvers;
* protection;
* control and automation;
* dynamics;
* persistence;
* plugins;
* engineering documentation.

GridForge V2 is not an SLD-only application. The SLD is one engineering projection of the underlying digital twin.

---

# 1. Architectural Authority

The GridForge V2 architecture defined in this document is the architectural baseline.

The fundamental rule is:

> **Core owns engineering truth. Application owns orchestration. UI owns interaction and presentation.**

No subsystem may bypass these ownership boundaries merely because direct access is convenient.

The architecture is organized around the following layers:

```text
                    USER / ENGINEER
                           │
                           ▼
                UI / Engineering Workspaces
                           │
                           ▼
                  Controllers / Tools
                           │
                           ▼
                  Immutable Commands
                           │
                           ▼
                 APPLICATION LAYER
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Commands        Transactions      Services
      History         Undo / Redo       Studies
      Lifecycle       Persistence       Events
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    AUTHORITATIVE CORE
                           │
       ┌───────────┬───────┼────────┬───────────┐
       ▼           ▼       ▼        ▼           ▼
     Model      Network  Analysis  Protection  Control
                           │
                           ▼
                         Solvers
                           │
                           ▼
                       Results
                           │
                           ▼
                 APPLICATION EVENTS
                           │
                           ▼
                    READ MODELS
                           │
                           ▼
              UI UPDATE BOUNDARY / BUS
                           │
                           ▼
              UI / Canvas / Projections
```

---

# 2. Core Architectural Principle

GridForge maintains **one authoritative engineering truth**.

The Core is the authority for:

* equipment;
* identities;
* terminals;
* electrical properties;
* topology;
* connections;
* engineering relationships;
* domain validation;
* studies;
* calculations;
* protection decisions;
* simulation state;
* study results.

The UI must never become a second engineering model.

The SLD must never become a second engineering model.

A renderer must never become a second engineering model.

A plugin must never become a second engineering model.

---

# 3. Architectural Ownership

## 3.1 Core

Core is the authoritative engineering/domain layer.

Core contains no Qt or UI dependencies.

Core owns:

```text
Electrical Model
Network Model
Topology
Terminals
Connections
Engineering Identities
Domain Validation
Analysis
Protection
Measurement
Control Domain
Dynamics Domain
Studies
Solvers
Results
```

Core does **not** own:

* Qt;
* QGraphics;
* widgets;
* canvas state;
* UI controllers;
* UI history;
* application lifecycle;
* UI persistence orchestration;
* presentation geometry.

---

# 4. Application Layer

The Application layer is the **sole orchestration boundary between UI and Core**.

UI components must not directly mutate Core.

The Application layer owns:

* command execution;
* command validation;
* command-handler resolution;
* transactions;
* rollback;
* commit;
* command history;
* undo;
* redo;
* project lifecycle;
* persistence orchestration;
* study orchestration;
* application services;
* application events;
* read-model coordination;
* UI update boundaries.

The Application layer may call Core.

Core must not call UI.

UI must not directly mutate Core.

---

# 5. UI / Application / Core Contract

The authoritative mutation path is:

```text
UI interaction
      │
      ▼
Controller / Tool
      │
      ▼
Immutable Command
      │
      ▼
Application.execute()
      │
      ▼
CommandManager
      │
      ├── validation
      ├── handler resolution
      ├── transaction
      ├── history
      └── undo / redo
      │
      ▼
Handler / Application Service
      │
      ▼
Core
      │
      ▼
Semantic Application Event
      │
      ▼
Read Model / Projection
      │
      ▼
UIUpdateBoundary / UIUpdateBus
      │
      ▼
UI
```

This is the canonical GridForge V2 mutation pipeline.

---

# 6. Command Architecture

User intent is represented by immutable commands.

A command describes an intended state transition.

Examples include:

```text
CreateBus
CreateTransformer
CreateBreaker
CreateLine
ConnectTerminals
UpdateEquipment
DeleteEquipment
PlaceEquipment
MoveEquipmentRepresentation
RunStudy
SaveProject
OpenProject
CloseProject
```

Commands do not directly manipulate widgets.

Commands do not bypass Application.

Commands do not directly expose mutable Core state to UI code.

---

# 7. CommandManager

Application owns the authoritative CommandManager.

The CommandManager is responsible for:

1. receiving a command;
2. validating the command;
3. resolving the appropriate handler;
4. opening a transaction;
5. executing the handler;
6. committing or rolling back;
7. recording history;
8. supporting undo/redo.

The failure invariant is:

```text
State S0
   │
   │ failed command
   ▼
State S0
```

A failed command must not leave a partially mutated system.

Successful execution follows:

```text
S0
 │
 │ execute
 ▼
S1
 │
 │ undo
 ▼
S0
 │
 │ redo
 ▼
S1
```

Undo and redo remain under the same Application-controlled mutation architecture.

---

# 8. Transactions

Application transactions have explicit lifecycle states.

Conceptually:

```text
OPEN
  │
  ▼
COMMITTING
  │
  ▼
COMMITTED
```

Failure paths include rollback states:

```text
OPEN
  │
  ▼
ROLLING_BACK
  │
  ├──────────────► ROLLED_BACK
  │
  └──────────────► ROLLBACK_FAILED
```

A transaction must never silently transition from failure to apparent success.

---

# 9. Application Events

Application emits semantic events rather than exposing arbitrary Core mutations to UI.

Core event/application integration includes events such as:

```text
ElementCreated
ElementUpdated
ElementRemoved
TopologyChanged

ProjectLoaded
ProjectSaved
ProjectClosed

StudyStarted
StudyCompleted

ValidationChanged
```

An execution event must have a corresponding coherent history/undo/redo interpretation.

---

# 10. Read Models and UI Updates

UI should not depend on arbitrary mutable Core objects for normal presentation.

The preferred path is:

```text
Core
 │
 ▼
Application Event
 │
 ▼
Read Model
 │
 ▼
UIUpdateBoundary / UIUpdateBus
 │
 ▼
Projection
 │
 ▼
UI
```

Read models are presentation-oriented representations.

They do not replace Core.

They do not become a second source of engineering truth.

---

# 11. Physical Model

The physical model represents engineering equipment and relationships.

The architecture does **not** use an artificial inheritance hierarchy such as:

```text
Asset
  └── Equipment
       └── Component
            └── Device
```

Instead, equipment is modeled according to its actual engineering semantics.

Equipment owns its persistent terminals.

A terminal represents an electrical endpoint belonging to its equipment.

---

# 12. Terminals

Terminals are first-class engineering objects.

A terminal has a defined local endpoint associated with its owning equipment.

Terminals provide the basis for:

* connectivity;
* topology;
* electrical relationships;
* switching interpretation;
* network construction.

Generic port abstractions must not be introduced merely for software convenience when terminal semantics are sufficient.

---

# 13. Connections and Topology

Connections are derived from authoritative terminal relationships.

TopologyManager is responsible for canonical topology interpretation.

Topology must not be inferred solely from SLD geometry.

The graphical position of an object does not establish electrical connectivity unless the corresponding engineering relationship exists.

---

# 14. Bus Model

A Bus is an engineering object with its own identity and electrical properties.

A Bus is not merely a graphical line.

A Bus is also not to be treated as a generic derived topological node.

Topology may derive network connectivity from buses, terminals and connections, but the Bus remains an authoritative domain object.

---

# 15. Network Architecture

The network layer derives network representations from authoritative Core engineering data.

Conceptually:

```text
Equipment
   │
   ▼
Terminals
   │
   ▼
Connections
   │
   ▼
TopologyManager
   │
   ▼
Network
   │
   ▼
Analysis / Studies
```

The network representation must remain derivable from authoritative engineering state.

---

# 16. Per-Unit System

Per-unit functionality belongs to the domain foundation.

The canonical architecture is:

```text
core/base/per_unit.py
```

The network layer consumes the appropriate domain functionality rather than maintaining an independent competing per-unit architecture.

---

# 17. Analysis Architecture

Analysis represents engineering calculations and study-domain logic.

Analysis is distinct from numerical solver implementation.

The architecture separates:

```text
Study / Engineering Analysis
          │
          ▼
Numerical Solver
          │
          ▼
Results
```

A solver is an implementation mechanism, not the owner of study lifecycle.

---

# 18. Power Flow

Power Flow is an engineering study orchestrated through Application.

The canonical domain boundary for Power Flow belongs under:

```text
core.analysis
```

not as an independent competing application architecture under a legacy solver package.

The workflow is:

```text
Power Flow Request
       │
       ▼
Application
       │
       ▼
Study Preconditions
       │
       ▼
Core Analysis
       │
       ▼
Numerical Solver
       │
       ▼
Power Flow Results
       │
       ▼
Application StudyCompleted
```

---

# 19. Short Circuit

Short-circuit analysis is a domain study.

It consumes authoritative network and equipment data and produces study results without becoming the owner of the underlying engineering model.

---

# 20. Dynamics

Dynamics is a first-class study domain.

Dynamic simulation is separated from static network modeling.

Dynamic solver infrastructure is organized under:

```text
core/solver/dynamics/
```

Dynamic initialization may use an operating point obtained from a solved static study.

The dynamic model must not silently create a competing permanent electrical truth.

---

# 21. Protection Architecture

Protection is based on measured electrical quantities, protection functions and protection decisions.

The conceptual architecture is:

```text
Primary Electrical System
          │
          ▼
       CT / PT / CVT
          │
          ▼
 Measurement Channel
          │
          ▼
 Protection Function
          │
          ▼
 Protection Decision
          │
          ▼
 Control / Trip Scheme
          │
          ▼
 Application-Controlled State Transition
```

Protection decisions remain distinct from physical switching state.

---

# 22. Measurement Architecture

CT, PT and CVT have distinct electrical meanings.

Conceptually:

```text
CT
 └── Line current measurement

PT / CVT
 └── Voltage measurement
```

Measurement points are first-class engineering concepts.

Measurement channels are represented under the measurement domain, including:

```text
core/measurement/measurement_channel.py
```

The measurement architecture provides the interface between primary electrical quantities and protection/control functions.

---

# 23. Protection Decision

Protection logic produces a semantic protection decision.

The protection decision is represented independently from the physical breaker state.

The protection decision structure includes concepts such as:

```text
relay_id
function_code
function_id
decision
```

The decision may subsequently participate in a control or trip scheme.

A protection function must not directly mutate arbitrary Core state outside the Application-controlled mutation architecture.

---

# 24. Switching Devices

Breakers, switches, disconnectors, contactors and related switching devices are modeled according to their engineering semantics.

A switching device may have:

* authoritative terminals;
* switching state;
* operating mechanism;
* auxiliary contacts;
* trip/close mechanisms where applicable.

Switching state affects topology interpretation where the device semantics require it.

---

# 25. Contactor and Motor-Control Architecture

A Contactor is a controlled multi-pole switching device.

Its domain model may include:

```text
Power switching poles
Coil / actuator
Auxiliary contacts
Switching state
```

Motor starters and similar control arrangements may be represented as reusable subsystems.

The SLD should show the appropriate engineering abstraction rather than attempting to render every physical contact detail.

Control logic remains separate from the physical equipment model.

---

# 26. Control and Automation

Control and automation is a first-class GridForge engineering domain.

It may include:

* digital inputs;
* digital outputs;
* analog signals;
* timers;
* interlocks;
* logic;
* ladder representations;
* control sequences;
* actuator commands;
* equipment feedback.

Control logic must interact with the engineering model through defined application/domain interfaces.

Control logic must not directly mutate arbitrary Core objects.

---

# 27. Ladder Logic

Ladder logic represents control intent.

A typical control path is:

```text
Inputs
  │
  ▼
Logic
  │
  ├── contacts
  ├── coils
  ├── timers
  └── interlocks
  │
  ▼
Output / Command
  │
  ▼
Controlled Equipment
```

For switching equipment such as breakers and contactors, ladder logic should act through the equipment's defined control mechanism.

For example, a breaker trip command acts through its trip mechanism rather than directly modifying unrelated topology structures.

---

# 28. SLD Architecture

The Single-Line Diagram is a **presentation and interaction projection** of the engineering model.

It is not the authoritative electrical model.

The SLD may contain:

* symbols;
* graphical positions;
* labels;
* routing;
* annotations;
* visual states;
* selection state;
* interaction state.

These are separate from Core engineering truth.

---

# 29. SLD Placement Workflow

The authoritative equipment-placement workflow is:

```text
Equipment Palette
       │
       ▼
Engineer selects equipment
       │
       ▼
Live cursor preview
       │
       │
       │  preview is NOT a Core object
       ▼
Engineer clicks canvas
       │
       ▼
Placement Command
       │
       ▼
Application.execute()
       │
       ├───────────────┐
       ▼               ▼
Core Equipment     SLD Representation
       │               │
       └───────┬───────┘
               ▼
        Application Event
               │
               ▼
        Projection Update
```

This distinction is mandatory.

---

# 30. Bus Placement and Connectivity

Bus placement may provide intelligent snapping and multi-terminal connection assistance.

However:

> **Graphical snapping does not itself constitute authoritative electrical connectivity.**

The resulting engineering relationship must be committed through the Application command path.

---

# 31. SLD Geometry

SLD geometry is presentation state.

Persistent project data must not depend on QGraphics objects or other runtime UI objects.

The project stores semantic/presentation information, not live GUI objects.

---

# 32. Canvas Architecture

GridForge may provide multiple engineering canvases.

Examples include:

```text
SLD / Network
Protection
Control
Dynamics
Studies
Equipment
Operations
Documentation
Validation
```

These canvases share the same Core and Application infrastructure.

They do not directly mutate one another.

They communicate through Application/domain contracts.

---

# 33. Engineering Scope

SLD and engineering workspaces may be organized into scopes such as:

```text
Plant
 └── Substation
      └── Switchboard
           └── Feeder
```

Scope is a structural/organizational concept and must not be confused with electrical topology.

---

# 34. Rendering

Rendering is presentation.

A renderer:

* reads appropriate projection/read-model data;
* produces graphical output;
* reflects state;
* does not own engineering truth;
* does not mutate Core.

Rendering code must not become an alternate domain model.

---

# 35. UI Architecture

The MainWindow is intentionally thin.

UI responsibilities include:

* presentation;
* interaction;
* workspace composition;
* tool activation;
* navigation;
* user feedback;
* visualization.

The UI must not become a domain-service container.

Qt dependencies should remain isolated through the UI infrastructure, including the canonical Qt abstraction boundary.

---

# 36. Qt Boundary

Qt must not enter Core.

Core must remain importable and usable without a running Qt application.

The UI layer may use:

```text
PySide6
Qt Widgets
Qt Graphics
Qt Models
Qt Signals
```

but those dependencies must remain outside Core.

---

# 37. Plugin Architecture

GridForge supports a plugin platform.

Plugins may contribute:

* equipment types;
* engineering studies;
* canvases;
* tools;
* panels;
* renderers;
* reports;
* domain extensions.

Plugins must communicate through defined Core/Application contracts.

Plugins must not bypass Application to perform uncontrolled Core mutation.

A plugin is an extension of GridForge, not an alternative architecture.

---

# 38. Persistence Architecture

The canonical project package is:

```text
project.gridforge
```

The package contains:

```text
manifest.json
project.json
```

`manifest.json` contains package/schema/version metadata.

`project.json` contains canonical project engineering/presentation data.

Runtime Qt objects are never persisted as project truth.

QGraphics objects are never persisted as project truth.

---

# 39. Project Lifecycle

Project lifecycle belongs to Application.

Supported lifecycle concepts include:

```text
New
Open
Save
Save As
Close
```

The Application owns the lifecycle orchestration.

Relevant events include:

```text
ProjectLoaded
ProjectSaved
ProjectClosed
```

Persistence implementation must not bypass the lifecycle contract.

---

# 40. Identity and Determinism

Every persistent engineering object must have a stable canonical identity.

Identity is not a graphical label.

Examples of independent concepts include:

```text
Object Identity
Display Name
Equipment Type
Terminal Identity
Project Scope
```

Generated identifiers must be deterministic where required by the domain contract.

Identity generation must not depend on transient GUI state.

---

# 41. Validation

Validation exists at multiple levels.

### Command validation

Determines whether a requested operation is admissible.

### Domain validation

Protects Core engineering invariants.

### Network validation

Checks network/topology consistency.

### Study validation

Checks study-specific prerequisites.

### Project validation

Checks persistence/project integrity.

Validation results should be represented semantically and exposed through Application/read-model mechanisms.

---

# 42. Study Lifecycle

A study is an Application-orchestrated workflow.

Generic pattern:

```text
Study Request
     │
     ▼
Study Configuration
     │
     ▼
Precondition Validation
     │
     ▼
StudyStarted
     │
     ▼
Core Analysis / Solver
     │
     ▼
Results
     │
     ▼
StudyCompleted
```

A failed study must produce an explicit failure state and must not be represented as successful completion.

---

# 43. Engineering Workflow Architecture

GridForge engineering workflows follow a common lifecycle:

```text
Engineer Intent
      │
      ▼
UI Interaction
      │
      ▼
Command
      │
      ▼
Application
      │
      ▼
Validation
      │
      ▼
Transaction
      │
      ▼
Core
      │
      ▼
Semantic Event
      │
      ▼
Read Model
      │
      ▼
Projection
      │
      ▼
Engineer-visible result
```

Different engineering systems implement their domain-specific workflow inside this common architecture.

---

# 44. Workflow-First Architecture

GridForge development and auditing are workflow-first.

A subsystem is not considered architecturally complete merely because its classes exist.

The complete engineering workflow must be traceable from:

```text
User Intent
   ↓
Command
   ↓
Application
   ↓
Domain Operation
   ↓
Core State
   ↓
Event
   ↓
Read Model
   ↓
UI Projection
```

This applies to:

* SLD;
* network editing;
* protection;
* control;
* dynamics;
* studies;
* project lifecycle;
* equipment management;
* documentation;
* operations.

---

# 45. Control Workflow

A control workflow may follow:

```text
Engineer
   │
   ▼
Control Design
   │
   ▼
Signals
   │
   ▼
Logic / Ladder
   │
   ▼
Evaluation
   │
   ▼
Control Output
   │
   ▼
Application / Domain Boundary
   │
   ▼
Equipment Control Mechanism
   │
   ▼
Equipment State
   │
   ▼
Feedback
   │
   └──────────────► Control Logic
```

The workflow must maintain a clear distinction between:

* signal;
* logic;
* command;
* equipment state;
* feedback.

---

# 46. Protection Workflow

A protection workflow may follow:

```text
Primary System
      │
      ▼
CT / PT / CVT
      │
      ▼
Measurement Channel
      │
      ▼
Protection Function
      │
      ▼
Protection Decision
      │
      ▼
Trip / Control Scheme
      │
      ▼
Application-controlled action
      │
      ▼
Switching Equipment
      │
      ▼
Network State
      │
      ▼
Measurement Feedback
```

---

# 47. Dynamics Workflow

A dynamics workflow may follow:

```text
Network Model
      │
      ▼
Solved Operating Point
      │
      ▼
Dynamic Initialization
      │
      ▼
Dynamic Model
      │
      ▼
Simulation
      │
      ▼
Time-Series Results
      │
      ▼
Analysis / Visualization
```

The dynamic state must not silently replace the authoritative persistent electrical model.

---

# 48. Documentation and Engineering Knowledge

Documentation and engineering knowledge provide contextual assistance.

Knowledge does not replace Core engineering truth.

Help may be associated with:

* equipment;
* studies;
* validation messages;
* engineering concepts;
* workflows;
* standards references.

Knowledge must have provenance and lifecycle where applicable.

---

# 49. Headless Operation

GridForge Core and Application functionality should be usable without the graphical UI.

A headless workflow follows:

```text
Application
   │
   ▼
Command / Service
   │
   ▼
Core
   │
   ▼
Study / Result
```

Headless operation must use the same domain and application contracts as the graphical environment.

The headless path must not become a separate competing architecture.

---

# 50. Testing Architecture

Testing should verify both engineering correctness and architectural contracts.

Important categories include:

```text
Core Domain Tests
Network / Topology Tests
Analysis Tests
Solver Tests
Protection Tests
Control Tests
Dynamics Tests

Application Tests
Command Tests
Transaction Tests
History Tests
Undo / Redo Tests
Lifecycle Tests
Persistence Tests
Event Tests

UI / Projection Tests
Workflow Integration Tests
Architecture Boundary Tests
Regression Tests
```

---

# 51. Workflow Contract Testing

Every major engineering workflow should have explicit contract coverage.

For example:

```text
Create Equipment
Create Connection
Edit Equipment
Delete Equipment
Undo
Redo
Save
Open
Close
Run Study
Display Result
Protection Trip
Control Action
Dynamic Simulation
```

Testing should verify the complete path rather than only isolated classes.

---

# 52. Regression Principle

Engineering regression must protect against:

* numerical regressions;
* topology regressions;
* identity regressions;
* persistence regressions;
* command regressions;
* transaction regressions;
* workflow regressions;
* UI/Application boundary regressions;
* architectural boundary regressions.

A passing numerical solver does not prove that the complete engineering workflow works.

---

# 53. Performance Architecture

Performance optimization must preserve architectural boundaries.

Potential optimization mechanisms include:

* caching;
* incremental topology updates;
* sparse numerical methods;
* parallel computation;
* background execution;
* GPU acceleration where justified.

Optimization must not introduce a second source of engineering truth.

---

# 54. CPU / GPU

GridForge may use CPU and GPU resources according to solver and workload requirements.

GPU execution is an implementation strategy.

It does not change:

* Core ownership;
* Application ownership;
* engineering semantics;
* persistence semantics;
* workflow contracts.

---

# 55. Repository Architecture

The repository should reflect architectural ownership.

A representative structure is:

```text
GridForge/
│
├── core/
│   ├── base/
│   ├── model/
│   ├── network/
│   ├── topology/
│   ├── analysis/
│   ├── solver/
│   │   └── dynamics/
│   ├── measurement/
│   ├── protection/
│   ├── control/
│   ├── validation/
│   └── results/
│
├── application/
│   ├── commands/
│   ├── handlers/
│   ├── services/
│   ├── transactions/
│   ├── history/
│   ├── lifecycle/
│   ├── studies/
│   ├── events/
│   ├── read_models/
│   └── persistence/
│
├── ui/
│   ├── core/
│   ├── main_window/
│   ├── sld/
│   ├── control/
│   ├── protection/
│   ├── dynamics/
│   ├── studies/
│   ├── panels/
│   └── projections/
│
├── plugins/
│
├── tests/
│
└── docs/
```

The exact repository layout may evolve, but ownership boundaries must remain intact.

---

# 56. Architectural Rules

The following rules are mandatory.

### Rule 1 — Core is authoritative

There must be one authoritative engineering model.

### Rule 2 — Application is the UI↔Core boundary

UI code must not directly mutate Core.

### Rule 3 — Commands are immutable

User-initiated state changes are represented through immutable commands.

### Rule 4 — Transactions are explicit

Mutations must have controlled commit and rollback behavior.

### Rule 5 — Undo/redo are Application responsibilities

History must not be independently implemented by UI components.

### Rule 6 — SLD is a projection

SLD geometry and symbols are not engineering truth.

### Rule 7 — Renderer is read-only with respect to Core

Rendering cannot mutate engineering state.

### Rule 8 — Plugins use contracts

Plugins must not bypass Application and directly mutate Core.

### Rule 9 — Qt stays out of Core

Core must remain headless.

### Rule 10 — Persistence stores semantics

Runtime UI objects are never persisted as engineering truth.

### Rule 11 — Topology is derived from engineering relationships

Graphics alone cannot establish electrical connectivity.

### Rule 12 — Protection decisions are separate from switching state

A protection decision is not itself the physical breaker state.

### Rule 13 — Studies are Application-orchestrated

Study execution is a workflow, not merely a solver call.

### Rule 14 — Read models are not Core

Read models are projections for consumers.

### Rule 15 — Workflows must be auditable end-to-end

Every major engineering capability must have a traceable lifecycle.

---

# 57. Forbidden Architectural Paths

The following patterns are prohibited:

```text
UI ───────────────► Core mutation
```

```text
SLD ──────────────► Core mutation
```

```text
Renderer ──────────► Core mutation
```

```text
Plugin ────────────► uncontrolled Core mutation
```

```text
Controller ────────► Core mutation
```

```text
Core ──────────────► Qt
```

```text
Core ──────────────► UI
```

```text
Solver ────────────► independent engineering truth
```

```text
SLD geometry ──────► authoritative topology
```

```text
UI history ────────► independent undo/redo
```

---

# 58. Engineering State Ownership

| Concern                       | Owner                    |
| ----------------------------- | ------------------------ |
| Equipment identity            | Core                     |
| Equipment properties          | Core                     |
| Terminals                     | Core                     |
| Connections                   | Core                     |
| Topology                      | Core                     |
| Domain validation             | Core                     |
| Numerical domain calculations | Core                     |
| Study orchestration           | Application              |
| Command execution             | Application              |
| Transactions                  | Application              |
| Undo/redo                     | Application              |
| Project lifecycle             | Application              |
| Persistence orchestration     | Application              |
| Application events            | Application              |
| Read models                   | Application              |
| UI interaction                | UI                       |
| Canvas geometry               | UI / projection          |
| Rendering                     | UI                       |
| Selection state               | UI                       |
| User workspace state          | UI                       |
| Plugin contribution           | Plugin through contracts |

---

# 59. Architectural Reconciliation Process

Architecture changes must follow:

```text
FETCH
  ↓
AUDIT
  ↓
RECONCILE
  ↓
CORRECT
  ↓
CHECK
  ↓
FREEZE
```

Existing implementation must be inspected before introducing architectural changes.

When old and new architectures conflict:

> **The current frozen V2 architecture takes precedence.**

Parallel competing architectures must not be maintained.

---

# 60. Workflow Audit Process

Workflow is the primary integration audit unit.

For each workflow:

```text
1. Identify engineer intent
2. Identify UI entry point
3. Identify command
4. Identify Application entry point
5. Identify handler/service
6. Identify Core mutation
7. Identify transaction
8. Identify resulting event
9. Identify read model
10. Identify UI projection
11. Verify persistence
12. Verify undo/redo where applicable
13. Verify failure/rollback behavior
14. Verify no boundary violation
```

A workflow is not closed merely because individual components exist.

---

# 61. Definition of Architectural Completion

A feature is architecturally complete only when:

* its domain model is authoritative;
* its Application boundary is defined;
* its commands are defined where required;
* its mutation path is controlled;
* its transactions are correct;
* its events are defined;
* its read model/projection is defined where required;
* persistence is defined where required;
* undo/redo behavior is defined where applicable;
* failure behavior is defined;
* UI/Core boundaries are respected;
* workflow integration is verified.

---

# 62. Project Lifecycle

The GridForge project lifecycle is:

```text
New Project
    │
    ▼
Build Model
    │
    ▼
Validate
    │
    ▼
Save
    │
    ▼
Open / Continue
    │
    ▼
Modify
    │
    ▼
Validate
    │
    ▼
Run Studies
    │
    ▼
Review Results
    │
    ▼
Iterate
    │
    ▼
Document
    │
    ▼
Operate / Simulate
    │
    ▼
Save / Close
```

All lifecycle transitions are Application-controlled.

---

# 63. Engineering Digital Twin

The GridForge digital twin represents multiple engineering aspects of the same system.

These include:

```text
Physical Equipment
Electrical Network
Topology
Measurements
Protection
Control
Dynamic State
Studies
Results
Documentation
Operations
```

The different views must remain consistent through shared authoritative Core state and Application orchestration.

---

# 64. Separation of Representations

GridForge may maintain several representations of the same engineering system:

```text
Core Domain Model
Network Representation
Analysis Representation
Protection Representation
Control Representation
Dynamic Representation
Read Model
SLD Projection
Reports
```

These representations are not independent sources of truth.

They are derived or coordinated representations of the authoritative domain.

---

# 65. Final Architecture

The complete architecture is:

```text
                         ENGINEER
                            │
                            ▼
                    GRIDFORGE UI
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
      SLD                Control             Studies
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                  Controllers / Tools
                            │
                            ▼
                    Immutable Commands
                            │
                            ▼
                 ┌──────────────────────┐
                 │     APPLICATION      │
                 │                      │
                 │ CommandManager       │
                 │ Handlers             │
                 │ Services             │
                 │ Transactions         │
                 │ History              │
                 │ Undo / Redo          │
                 │ Project Lifecycle    │
                 │ Study Orchestration  │
                 │ Persistence          │
                 │ Events               │
                 │ Read Models          │
                 └──────────┬───────────┘
                            │
                            ▼
                    AUTHORITATIVE CORE
                            │
       ┌────────────┬───────┼────────┬────────────┐
       │            │       │        │            │
       ▼            ▼       ▼        ▼            ▼
     Model       Network  Analysis Protection  Control
                            │
                            ▼
                         Solvers
                            │
                            ▼
                         Results
                            │
                            ▼
                    Application Events
                            │
                            ▼
                       Read Models
                            │
                            ▼
                UI Update Boundary / Bus
                            │
                            ▼
                    UI Projections
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
            SLD          Control UI      Study UI
```

---

# 66. What GridForge Is Not

GridForge is not:

* merely an SLD drawing application;
* merely a numerical solver;
* merely a protection calculator;
* merely a simulation engine;
* merely a control-logic editor;
* a collection of disconnected engineering tools;
* a GUI wrapped around an unrelated calculation library;
* a system where graphical state is treated as engineering truth.

GridForge is an integrated engineering platform built around one authoritative digital-twin model.

---

# 67. Development Philosophy

GridForge development follows these principles:

### Engineering truth before presentation

The domain model is established before presentation behavior is allowed to define semantics.

### Explicit boundaries before convenience

Shortcuts across architectural boundaries are treated as defects.

### Workflow before isolated classes

A capability must work end-to-end.

### Determinism before convenience

Identity, persistence and engineering results should be reproducible where the domain requires it.

### Validation before freeze

Architectural decisions are checked against implementation and workflow behavior before being frozen.

---

# 68. Current V2 Guiding Principle

The entire GridForge architecture can be summarized as:

> **One authoritative engineering truth, one controlled application boundary, multiple specialized engineering workflows and projections.**

Or, more precisely:

```text
CORE
    = Engineering Truth

APPLICATION
    = Orchestration + Commands + Transactions + Lifecycle + Studies

UI
    = Interaction + Presentation + Projection

WORKFLOWS
    = End-to-End Engineering Execution

PLUGINS
    = Contract-Bound Extensions

PERSISTENCE
    = Reproducible Project State
```

GridForge V2 therefore remains a unified engineering platform while preserving strict separation of concerns.

The goal is not merely to make the software function.

The goal is to make every engineering action **traceable, deterministic, auditable, reversible where applicable, and architecturally consistent**.
