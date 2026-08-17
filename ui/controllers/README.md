GridForge Controller Module
Application and Engineering Orchestration Layer

The GridForge Controller Module provides the orchestration boundary between the user-facing application and the authoritative GridForge Core.

Controllers coordinate application workflows without becoming owners of engineering truth.

The controller layer is responsible for translating application and UI intent into explicit operations against the Core, coordinating results, and exposing application-level workflows to the GUI, plugins, tools, and future non-GUI clients.

Controllers orchestrate. The Core owns engineering truth.

1. Purpose

The Controller Module exists to prevent the GUI from directly coordinating complex engineering operations.

The intended architecture is:

                    USER / API / PLUGIN
                            │
                            ▼
                     Application Layer
                            │
                            ▼
                       Controllers
                            │
                            ▼
                      GridForge Core
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
        Model            Network            Analysis
                                                │
                                                ▼
                                             Solver

Controllers provide the application-level coordination required to turn user intent into valid engineering operations.

2. Architectural Position

The Controller Module sits between the presentation layer and the engineering core.

┌──────────────────────────────────────────────┐
│                GridForge UI                  │
│                                              │
│ Canvas • Tools • Panels • Plugins • Dialogs  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              Controller Layer                │
│                                              │
│ Application / Network / Study / Simulation  │
│ Protection / Project / Result Workflows      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│               GridForge Core                 │
│                                              │
│ Model • Network • Analysis • Solver          │
│ Protection • Simulation • Validation         │
└──────────────────────────────────────────────┘

The controller layer is therefore an application orchestration layer, not a replacement for the Core.

3. Core Principle

The fundamental controller rule is:

Controllers coordinate operations across subsystems; they do not become a second engineering domain model.

A controller may know:

Which service should be called
Which workflow is currently executing
Which operation the user requested
How results should be routed
Which validation stage must occur first

A controller must not become the authoritative owner of:

Equipment
Electrical topology
Y-bus
Solver state
Protection state
Simulation state
4. Repository Structure

The controller architecture is centered around the application/core boundary.

A representative structure is:

GridForge/
│
├── core/
│   ├── controller.py
│   ├── model/
│   ├── network/
│   ├── analysis/
│   ├── solver/
│   ├── protection/
│   ├── simulation/
│   └── validation/
│
├── ui/
│   ├── controllers/
│   │   └── ...
│   ├── canvas/
│   ├── tools/
│   ├── plugins/
│   └── ...
│
└── main.py

The exact controller file structure may evolve, but the architectural distinction between application orchestration and engineering execution must remain intact.

5. Controller Responsibilities

Controllers may coordinate:

Application workflows
Model creation and modification
Network reconstruction
Study execution
Validation
Simulation lifecycle
Protection workflows
Result retrieval
UI refresh requests
Project lifecycle operations
Cross-subsystem transactions

The controller should provide a stable application-facing contract.

6. What Controllers Do Not Own

Controllers must not become owners of:

Physical equipment
Electrical topology
Y-bus
Numerical solver state
Protection decisions
Simulation state
Persistent project serialization
GUI rendering state

For example:

Controller
   │
   ├── requests creation of Bus
   │
   ▼
core.model
   │
   └── owns Bus

The controller does not retain a competing engineering copy.

7. Application Controller

The primary application controller provides high-level orchestration.

Conceptually:

ApplicationController
        │
        ├── Model Operations
        ├── Network Operations
        ├── Study Operations
        ├── Simulation Operations
        ├── Protection Operations
        ├── Validation
        └── Result Coordination

It provides the application with a coherent entry point without merging all engineering responsibilities into one monolithic class.

8. Controller vs Service

GridForge distinguishes between orchestration and domain execution.

Layer	Responsibility
Controller	Coordinates workflow
Model	Owns physical engineering objects
Network	Owns electrical representation
Analysis	Defines engineering study
Solver	Performs numerical computation
Protection	Executes protection functions
Simulation	Executes runtime simulation
Validation	Validates engineering state
Persistence	Serializes/deserializes projects
GUI	Displays and interacts

Therefore:

Controller ≠ Solver
Controller ≠ Model
Controller ≠ Network
Controller ≠ GUI
9. Model Workflow

A model-editing workflow may follow:

User
 │
 ▼
Canvas / Tool
 │
 ▼
Controller
 │
 ▼
Validation
 │
 ▼
Model Operation
 │
 ▼
Authoritative Model State
 │
 ▼
Network Update
 │
 ▼
UI Refresh

The controller coordinates this sequence.

The model remains authoritative.

10. Creating Engineering Equipment

For example, creating a bus:

BusTool
   │
   ▼
Controller
   │
   ▼
Validation
   │
   ▼
core.model.Bus
   │
   ▼
Network Update
   │
   ▼
Canvas Update

The controller should not directly instantiate graphical objects as the primary engineering operation.

The engineering object is created first in the authoritative domain.

11. Editing Engineering Equipment

An equipment-edit operation should follow:

Property Panel
      │
      ▼
Controller
      │
      ▼
Validate Change
      │
      ▼
Core Model
      │
      ▼
Network Reconstruction / Update
      │
      ▼
Affected Analysis State
      │
      ▼
UI Refresh

This prevents property panels from directly mutating hidden internal state.

12. Network Workflow

Controllers may coordinate network reconstruction.

Model Change
    │
    ▼
Controller
    │
    ▼
Network Validation
    │
    ▼
Network Reconstruction
    │
    ├── Topology
    ├── Indexing
    ├── Per-Unit
    └── Y-Bus
    │
    ▼
Updated Network

The controller coordinates the operation.

The Network subsystem remains the authoritative owner of electrical representation.

13. Analysis Workflow

A study execution may follow:

Study Request
      │
      ▼
Controller
      │
      ▼
Engineering Validation
      │
      ▼
Analysis Service
      │
      ▼
Solver
      │
      ▼
Analysis Result
      │
      ▼
Controller
      │
      ├── UI
      ├── Reports
      └── Result Consumers

The controller does not implement Newton-Raphson, fault equations, or dynamic integration.

14. Power-Flow Workflow

A power-flow request should conceptually follow:

User
 │
 ▼
Study Configuration
 │
 ▼
Controller
 │
 ▼
Validation
 │
 ▼
Power Flow Analysis
 │
 ▼
Power Flow Solver
 │
 ▼
Power Flow Result
 │
 ▼
Controller
 │
 ├── Result Panel
 ├── Canvas Visualization
 └── Report

This maintains the separation:

Study Definition
       ≠
Numerical Algorithm
15. Short-Circuit Workflow

The controller may coordinate:

Fault Definition
      │
      ▼
Controller
      │
      ▼
Validation
      │
      ▼
Short-Circuit Analysis
      │
      ▼
Short-Circuit Solver
      │
      ▼
Fault Result
      │
      ▼
Visualization / Report

The controller does not own the fault network or numerical implementation.

16. Dynamics Workflow

Dynamic simulation may be coordinated as:

Dynamic Study
      │
      ▼
Controller
      │
      ▼
Validation
      │
      ▼
Simulation Initialization
      │
      ▼
Dynamic Solver
      │
      ▼
Runtime State
      │
      ▼
Simulation Results
      │
      ▼
Visualization

The controller owns the workflow lifecycle, not the dynamic state itself.

17. Protection Workflow

Protection operations follow the established decision boundary.

Measurement
     │
     ▼
Protection Function
     │
     ▼
ProtectionDecision
     │
     ▼
Controller / Scheme
     │
     ▼
BreakerManager
     │
     ▼
Physical Breaker

The controller must not bypass:

ProtectionDecision

by directly commanding a breaker simply because a UI action or protection function requested a trip.

18. Protection Study Coordination

A protection-study controller may coordinate:

Protection Configuration
          │
          ▼
Validation
          │
          ▼
Measurement Configuration
          │
          ▼
Protection Functions
          │
          ▼
Protection Decisions
          │
          ▼
Coordination Analysis
          │
          ▼
Results

The controller orchestrates the workflow.

Protection execution remains within the protection subsystem.

19. Simulation Lifecycle

The controller may manage the lifecycle:

Created
   │
   ▼
Configured
   │
   ▼
Validated
   │
   ▼
Initialized
   │
   ▼
Running
   │
   ├── Pause
   ├── Stop
   └── Fault / Event
   │
   ▼
Completed

The simulation subsystem remains the owner of runtime simulation state.

20. Controller State

Controller state should be limited to workflow state, where required.

Examples:

Current operation
Current study request
Operation status
Pending user operation
Workflow context
Error/result routing

Controllers should not cache authoritative engineering state unnecessarily.

Avoid:

Controller
   ├── copied buses
   ├── copied lines
   ├── copied Y-bus
   └── copied protection state

Prefer:

Controller
   │
   └── references authoritative services
21. Validation Boundary

Controllers are responsible for invoking the appropriate validation before committing application operations.

Request
   │
   ▼
Controller
   │
   ▼
Validation
   │
   ├── Invalid
   │     └── Reject
   │
   └── Valid
         │
         ▼
      Execute

Validation distinguishes:

Invalid Engineering State

from:

Valid Engineering State
        +
Numerical Failure

The controller should preserve this distinction when reporting results.

22. Error Propagation

Controllers should not hide subsystem-specific failures.

For example:

Validation Error
Invalid topology
Analysis Error
Invalid study configuration
Numerical Error
Power-flow solver failed to converge
Runtime Error
Simulation terminated unexpectedly

The controller may translate these into application-level status objects or notifications, but the underlying failure semantics must remain identifiable.

23. GUI Boundary

The GUI should interact with controllers through explicit contracts.

Preferred:

Canvas
   │
   ▼
UI Controller / Application Controller
   │
   ▼
Core

Avoid:

Canvas
   │
   ▼
core.network.internal_structure

or:

PropertyPanel
   │
   ▼
solver.private_state

Controllers provide the controlled boundary.

24. Controller and Canvas

The Canvas handles visual interaction.

The controller handles engineering operation orchestration.

For example:

LineTool
   │
   ▼
InteractionManager
   │
   ▼
Controller
   │
   ▼
Network Validation
   │
   ▼
Create Electrical Connection
   │
   ▼
Canvas Refresh

This prevents the Canvas from becoming a topology engine.

25. Controller and Plugins

Plugins may consume controller contracts.

Plugin
   │
   ▼
Controller Contract
   │
   ▼
Core Service

Plugins should not bypass the application boundary merely because they require access to a Core operation.

This maintains architectural consistency.

26. Controller and Persistence

Project loading and saving are persistence responsibilities.

A project workflow may be:

User
 │
 ▼
Controller
 │
 ▼
Persistence Service
 │
 ├── Deserialize
 ├── Schema Validation
 └── Project Reconstruction
 │
 ▼
Core Model
 │
 ▼
Network Construction
 │
 ▼
Application State

The controller coordinates the workflow.

It does not become a serialization engine.

27. Headless Operation

Controllers should be designed so that application workflows can eventually be executed without the GUI.

For example:

controller = GridForgeController(core)


result = controller.run_power_flow(study)

The controller should not require:

QWidget
QGraphicsScene
Mouse events
Dialogs
Rendering objects

This supports:

Batch studies
Automated analysis
Regression testing
Server execution
CLI applications
Future real-time systems
28. Qt Independence

Core/application controllers should remain independent of Qt whenever possible.

The preferred boundary is:

Qt UI
   │
   ▼
UI Controller
   │
   ▼
Application Controller
   │
   ▼
Core

The Core controller must not require:

from PySide6.QtWidgets import ...

Qt belongs to the GUI layer.

29. CPU / GPU Independence

Controllers should not depend on the numerical backend.

They should be able to request:

Power Flow

without needing to know whether the operation uses:

CPU
GPU
Sparse CPU
GPU sparse backend
Future accelerator

The backend remains an implementation detail of numerical execution.

30. Result Routing

Controllers may route engineering results to application consumers.

For example:

PowerFlowResult
      │
      ▼
Controller
      │
      ├── Canvas
      ├── Result Panel
      ├── Report
      └── Regression System

The controller must not modify the result merely to satisfy a particular UI representation.

31. Transactional Operations

Where appropriate, multi-stage engineering changes should behave as controlled operations.

Conceptually:

Begin Operation
      │
      ▼
Validate
      │
      ▼
Modify Model
      │
      ▼
Rebuild Network
      │
      ▼
Validate Result
      │
   ┌──┴──┐
   ▼     ▼
Commit  Reject

This becomes particularly important for:

Equipment deletion
Topology changes
Network reconstruction
Project loading
Protection configuration changes

The exact transaction mechanism depends on the underlying Core architecture.

32. Dependency Management

Controllers should depend on stable interfaces rather than private implementation details.

Prefer:

Controller
   │
   ├── Model Service
   ├── Network Service
   ├── Analysis Service
   ├── Validation Service
   └── Simulation Service

Avoid:

Controller
   └── accesses private fields of every subsystem

This reduces coupling and improves maintainability.

33. Determinism

Controller workflows should be deterministic.

Given identical:

Model state
Network state
Study configuration
Solver configuration
Workflow inputs

the same controller operation should produce equivalent outcomes.

Controller determinism is important for:

Testing
Regression
Reproducibility
Debugging
Automated studies
34. Performance

Controllers should remain lightweight.

They should coordinate expensive operations rather than implement them.

For example:

Controller
   │
   └── invokes Solver

not:

Controller
   └── contains numerical iteration loops

Long-running work should execute through appropriate Core services and execution mechanisms rather than blocking GUI event handling.

35. Testing Strategy

The Controller Module should be tested at multiple levels.

Unit Tests

Test:

Request validation
Workflow sequencing
Service invocation
Error propagation
Result routing
Integration Tests

Test complete workflows:

Controller
    ↓
Model
    ↓
Network
    ↓
Analysis
    ↓
Solver
    ↓
Result
GUI Integration

Test:

UI Action
    ↓
UI Controller
    ↓
Application Controller
    ↓
Core
    ↓
Result
    ↓
UI Update
Headless Tests

Controllers should be testable without Qt.

This is essential for automated engineering regression.

36. Controller Anti-Patterns

The following patterns are prohibited.

Monolithic Controller
ApplicationController
    ├── Model implementation
    ├── Network implementation
    ├── Solver implementation
    ├── Protection implementation
    └── Simulation implementation

Incorrect.

The controller coordinates these services rather than replacing them.

Controller-Owned Engineering State
Controller
   └── private copy of Network

Incorrect.

The Network remains authoritative.

Controller-Owned Solver
Controller
   └── Newton-Raphson implementation

Incorrect.

The solver subsystem owns numerical algorithms.

GUI Controller as Domain Model
UIController
   └── owns Bus / Line / Transformer state

Incorrect.

The Core model owns physical equipment.

Direct Breaker Operation
UI
 ↓
Controller
 ↓
Breaker.trip()

without the appropriate protection/scheme semantics.

Incorrect for protection-driven operations.

The protection architecture must preserve:

ProtectionDecision
      ↓
Scheme / Output Logic
      ↓
BreakerManager
37. Correct Controller Pattern

The preferred architecture is:

                         USER
                           │
                           ▼
                      UI / Plugin
                           │
                           ▼
                    UI Controller
                           │
                           ▼
                 Application Controller
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
        Model           Network          Analysis
          │                │                │
          │                │                ▼
          │                │              Solver
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                      Result / State
                           │
                           ▼
                   UI / Canvas / Report

The controller remains the orchestration boundary.

38. Engineering Execution Flow

The complete application workflow is:

                   USER REQUEST
                        │
                        ▼
                 GUI / Plugin / API
                        │
                        ▼
                   Controller
                        │
                        ▼
                   Validation
                        │
                        ▼
              Engineering Operation
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
     Model           Network           Study
       │                │                │
       │                │                ▼
       │                │             Solver
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
                     Result
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
            Canvas    Panels    Reports
39. Architectural Rules

The Controller Module follows these rules.

#	Rule	Requirement
1	Controllers orchestrate	Controllers coordinate workflows
2	Core owns engineering truth	Controllers never become a second domain model
3	Model owns equipment	Controllers request model operations
4	Network owns topology	Controllers do not implement topology internally
5	Analysis owns study semantics	Controllers do not replace analysis services
6	Solver owns numerical execution	Controllers never implement numerical algorithms
7	Protection owns protection execution	Controllers preserve the protection decision boundary
8	Simulation owns runtime state	Controllers coordinate lifecycle rather than owning simulation state
9	Validation remains authoritative	Controllers invoke validation before engineering operations
10	Persistence remains separate	Controllers coordinate project workflows but do not become serializers
11	GUI remains outside Core	Core controllers must remain headless-capable
12	Qt remains outside Core	Application/core controllers should not depend on Qt
13	Results remain authoritative	Controllers route results without creating competing copies
14	Stable contracts	Controllers depend on explicit subsystem interfaces
15	No hidden state duplication	Do not cache authoritative engineering state unnecessarily
16	Deterministic workflows	Identical inputs should produce reproducible application behavior
17	No monolithic orchestration	Split fundamentally different workflows into specialized services/controllers
40. Recommended Controller Boundaries

As GridForge grows, specialized controllers may be introduced where the workflow complexity justifies them.

Potential boundaries include:

ApplicationController
        │
        ├── ModelController
        ├── NetworkController
        ├── StudyController
        ├── SimulationController
        ├── ProtectionController
        ├── ProjectController
        └── ResultController

These should be introduced only where they provide a genuine architectural boundary.

The project should avoid creating controllers merely for the sake of increasing the number of classes.

41. Controller Lifecycle

A controller should generally follow:

Create
  │
  ▼
Bind Services
  │
  ▼
Validate Dependencies
  │
  ▼
Accept Requests
  │
  ▼
Execute Workflow
  │
  ▼
Return Result / Status
  │
  ▼
Remain Available

Controllers should not unexpectedly mutate unrelated application state.

42. Controller and Digital-Twin State Ownership

The controller participates in the digital-twin architecture without becoming its owner.

                DIGITAL TWIN
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Model        Network      Runtime
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
                 Controller
                     │
              orchestrates access
                     │
                     ▼
                UI / API / Tools

The controller provides controlled access to engineering operations.

43. Controller and Identity

Controllers must preserve engineering identity.

They should never use temporary UI object identity as the engineering identifier.

For example:

Engineering Bus ID
        ≠
Graphics Item ID
        ≠
Numerical Index

When a network is rebuilt:

Numerical Index
    may change


Engineering Identity
    must remain stable

Controllers must preserve this distinction throughout workflows.

44. Controller and Deterministic Network Reconstruction

A controller-triggered topology operation may result in network reconstruction:

Model Change
    │
    ▼
Controller
    │
    ▼
Network Reconstruction
    │
    ├── Deterministic topology
    ├── Deterministic indexing
    ├── Per-unit structures
    └── Y-bus

The controller must not assume that numerical indices remain unchanged after reconstruction.

Engineering identity must be used when referring to persistent equipment.

45. Controller Module and Future Extensions

The architecture is designed to support future application workflows including:

Engineering Studies
Power flow
Short circuit
Contingency
OPF
SCOPF
Voltage stability
Dynamic Simulation
Transient stability
EMT
Real-time simulation
Protection
Relay coordination
TCC
Protection testing
Breaker failure
Autoreclose
Digital Twin
SCADA integration
Online measurements
State estimation
Event processing
Real-time monitoring

The controller architecture should allow these capabilities to be added without turning the GUI into the engineering execution layer.

46. Headless Application Architecture

A major design objective is to allow application workflows to run without a graphical frontend.

For example:

CLI / Automation
       │
       ▼
Application Controller
       │
       ▼
GridForge Core
       │
       ▼
Engineering Result

The same controller contract can therefore support:

GUI
CLI
Batch Processing
Automated Testing
Server
Digital Twin Runtime

where appropriate.

47. Final Controller Architecture

The complete conceptual architecture is:

                         USER / API
                             │
                             ▼
                     GUI / Plugin Layer
                             │
                             ▼
                       UI Controllers
                             │
                             ▼
                   Application Controller
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
      Model              Network              Analysis
        │                    │                    │
        │                    │                    ▼
        │                    │                  Solver
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                        Simulation
                             │
                     ┌───────┴────────┐
                     ▼                ▼
                Measurement       Protection
                                      │
                                      ▼
                              ProtectionDecision
                                      │
                                      ▼
                                BreakerManager
                             │
                             ▼
                     Engineering Results
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
             Canvas        Panels        Reports
48. Development and Freeze Process

Controller development follows the GridForge subsystem freeze methodology:

Architecture
     ↓
Controller Contracts
     ↓
Implementation
     ↓
Architectural Audit
     ↓
Correction
     ↓
Fresh Audit
     ↓
Unit Tests
     ↓
Integration Tests
     ↓
Headless Workflow Tests
     ↓
GUI Integration
     ↓
Regression
     ↓
Finalization
     ↓
Freeze

Controller defects should be corrected at the appropriate architectural layer rather than hidden with GUI-specific workarounds.

49. Controller Module Status

The Controller Module establishes the application orchestration boundary between GridForge presentation systems and the authoritative engineering Core.

Layer	Responsibility
UI	User interaction and presentation
UI Controllers	UI workflow coordination
Application Controller	Application orchestration
Model	Physical engineering authority
Network	Electrical representation authority
Analysis	Study authority
Solver	Numerical execution
Protection	Protection execution
Simulation	Runtime execution
Validation	Engineering integrity
Persistence	Project state management
Canvas	Visualization and interaction
50. Guiding Principle

The GridForge Controller Module follows one central principle:

Controllers coordinate engineering workflows without becoming owners of engineering truth.

The resulting architecture is:

                 USER / API
                     │
                     ▼
               UI / Plugins
                     │
                     ▼
                Controllers
                     │
                     ▼
               GridForge Core
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
    Model         Network         Analysis
      │              │              │
      │              │              ▼
      │              │            Solver
      │              │
      └──────────────┼──────────────┘
                     │
                     ▼
                 Simulation
                     │
                     ▼
                Protection
                     │
                     ▼
             Engineering Results
                     │
                     ▼
               UI / Reports

One authoritative engineering core, controlled application workflows, and no duplicated engineering state.

<p align="center"><em>GridForge Controllers — coordinate the system, preserve the architecture.</em></p>
