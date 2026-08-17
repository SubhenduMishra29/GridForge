GridForge UI Core Module
UI Infrastructure and Architectural Services

The ui/core/ module provides the foundational infrastructure for the GridForge V2 graphical application.

It contains the reusable UI services and contracts required by the Canvas, tools, renderers, plugins, controllers, panels, and other GUI components.

The module is intentionally positioned below higher-level UI components but above the Qt framework.

ui/core/ provides UI infrastructure; it does not own engineering truth.

1. Purpose

The ui/core/ module establishes the common infrastructure required by the GridForge GUI.

Its responsibilities include:

Qt abstraction
UI service registration
Plugin contracts and infrastructure
Tool registration
Rendering registration
Coordinate and snapping infrastructure
UI-level event routing
Shared UI state
Application-facing UI contracts
Controlled access to Core services

Conceptually:

                     GRIDFORGE GUI
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
      Canvas            Tools             Panels
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                      ui/core/
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
       Qt             Registries         Contracts
     Abstraction        / Loaders          / State
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    Controllers
                          │
                          ▼
                     GridForge Core
2. Architectural Position

The UI Core sits at the foundation of the GUI subsystem.

┌──────────────────────────────────────────────┐
│                UI Components                 │
│                                              │
│ Canvas • Panels • Tools • Plugins • Views    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                  ui/core/                    │
│                                              │
│ Qt • Contracts • Registries • State         │
│ Snap • Rendering • UI Infrastructure         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              UI Controllers                  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                GridForge Core                │
└──────────────────────────────────────────────┘

ui/core/ is therefore GUI infrastructure, not an engineering domain layer.

3. Repository Position

The intended structure is:

GridForge/
│
├── core/
│   └── ...
│
├── ui/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── qt.py
│   │   ├── plugin_registry.py
│   │   ├── plugin_loader.py
│   │   ├── renderer_registry.py
│   │   ├── renderer_loader.py
│   │   ├── snap_system.py
│   │   └── ...
│   │
│   ├── canvas/
│   ├── controllers/
│   ├── items/
│   ├── panels/
│   ├── plugins/
│   ├── renderers/
│   ├── tools/
│   └── ...
│
└── main.py

The exact file set may evolve, but the architectural role of ui/core/ remains stable.

4. Responsibilities

The module provides infrastructure for:

Area	Responsibility
Qt	Centralized Qt/PySide6 abstraction
Plugin infrastructure	Registration and loading contracts
Renderer infrastructure	Renderer registration and discovery
Snap infrastructure	UI-level snapping services
Tool infrastructure	Tool registration/contracts where applicable
UI state	Shared GUI state contracts
Events	UI-level event communication
Service access	Controlled access to application services
Contracts	Stable interfaces between UI subsystems
5. What ui/core/ Does Not Own

The UI Core must not become an alternative engineering core.

It does not own:

Buses
Lines
Transformers
Generators
Electrical topology
Y-bus
Power-flow state
Solver state
Protection decisions
Simulation truth
Persistent project state

For example:

Bus
 │
 ├── Engineering object → core.model
 │
 └── Graphics representation → ui.items.BusItem

ui/core/ provides infrastructure allowing these representations to interact correctly.

6. Qt Abstraction

GridForge V2 uses PySide6.

The UI Core provides a centralized Qt abstraction layer.

Conceptually:

PySide6
   │
   ▼
ui/core/qt.py
   │
   ▼
GridForge UI

This prevents individual UI modules from scattering framework-specific compatibility logic throughout the codebase.

7. Single Qt Framework

GridForge UI code must use one Qt framework consistently.

The approved framework is:

PySide6

The UI Core must prevent accidental introduction of:

PyQt5
PyQt6
PySide2

into the GUI architecture.

Mixed Qt frameworks are prohibited.

8. Qt Abstraction Responsibilities

ui/core/qt.py may centralize commonly used Qt types such as:

QObject
QPointF
QRectF
QLineF
QTransform
QPainter
QGraphicsItem
QGraphicsScene
QGraphicsView
Signals
Slots
Qt enumerations

The exact exported set should remain controlled and intentional.

9. Why the Qt Abstraction Exists

Without a centralized abstraction:

Canvas ──────► PySide6
Tool ────────► PySide6
Renderer ────► PySide6
Panel ───────► PySide6
Plugin ──────► PySide6

With the abstraction:

                  ui/core/qt.py
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
     Canvas          Tools          Renderers

This provides a controlled framework boundary.

10. Plugin Infrastructure

The UI Core provides infrastructure for the GridForge plugin system.

Conceptually:

Plugin Contract
      │
      ▼
Plugin Registry
      │
      ▼
Plugin Loader
      │
      ▼
Plugin Manager
      │
      ▼
UI Composition

The registry, loader, manager, context, contract, state, and event infrastructure remain separate responsibilities.

11. Plugin Registry

The Plugin Registry provides registration/discovery infrastructure.

Its responsibility is to know:

Plugin Identity
Plugin Metadata
Plugin Contract
Plugin Availability

It should not silently instantiate every concrete plugin merely by being imported.

This keeps discovery and composition explicit.

12. Explicit Plugin Loading

The GridForge architecture intentionally uses explicit plugin loading.

Conceptually:

Plugin Registry
      │
      │ knows contracts/registrations
      ▼
Plugin Loader
      │
      │ explicitly imports
      ▼
Concrete Plugins

This prevents circular imports and uncontrolled plugin initialization.

13. Plugin Contract

Plugins should communicate through explicit contracts.

A plugin contract may define:

Identity
Lifecycle
Dependencies
Context
Capabilities
State handling
Event participation
UI contribution

Conceptually:

Plugin
  │
  ├── Contract
  ├── Context
  ├── State
  └── Events

Plugins must not bypass established UI/Core ownership boundaries.

14. Plugin Context

The plugin context provides controlled access to application/UI services.

Conceptually:

Plugin
   │
   ▼
PluginContext
   │
   ├── Controller
   ├── UI Services
   ├── Registries
   ├── Application State
   └── Event System

A plugin should not directly reach into arbitrary private objects.

15. Renderer Infrastructure

The UI Core provides renderer registration and loading infrastructure.

Conceptually:

Renderer Contract
       │
       ▼
Renderer Registry
       │
       ▼
Renderer Loader
       │
       ▼
Concrete Renderers
       │
       ├── BusRenderer
       ├── LineRenderer
       └── Equipment Renderers

Renderers remain presentation components.

16. Renderer Ownership

A renderer visualizes authoritative Core objects.

core.model.Bus
       │
       ▼
BusRenderer
       │
       ▼
Graphics Representation

The renderer must not become the owner of:

Bus engineering state

Likewise:

LineRenderer

must not become the owner of electrical connectivity.

17. Snap System

The Snap System provides GUI-level geometric snapping.

Typical responsibilities include:

Grid snapping
Point snapping
Terminal snapping
Alignment assistance
Coordinate quantization
Snap candidate selection

Conceptually:

Mouse Position
      │
      ▼
Coordinate System
      │
      ▼
Snap System
      │
      ▼
Snapped UI Position
18. Snap vs Electrical Topology

Snapping is a GUI interaction aid.

It does not determine whether an electrical connection is valid.

For example:

Snap System
      │
      ▼
Graphical Candidate
      │
      ▼
Controller / Network Validation
      │
      ▼
Electrical Decision

Therefore:

Geometric proximity is not electrical connectivity.

19. Tool Infrastructure

Tools such as:

SelectTool
BusTool
LineTool

operate through UI infrastructure.

The current GridForge V2 tool set is intentionally limited to these three concrete tools.

Tool System
    │
    ├── SelectTool
    ├── BusTool
    └── LineTool

The UI Core should provide stable infrastructure for these tools without embedding their individual behavior into shared infrastructure.

20. Tool and Core Separation

A tool performs user interaction.

It does not become an engineering authority.

Example:

BusTool
   │
   ▼
UI Controller
   │
   ▼
Core Model
   │
   ▼
Authoritative Bus

Not:

BusTool
   │
   └── owns the Bus
21. UI State

The UI Core may define shared UI state such as:

Current mode
Active tool
Selection state
Interaction state
View state
Navigation state
Plugin state
Rendering preferences

These states belong to the GUI.

They must not be confused with engineering state.

22. Engineering State vs UI State

A fundamental distinction is:

ENGINEERING STATE
        │
        ▼
     GridForge Core

versus:

UI STATE
        │
        ▼
      ui/core/

For example:

State	Owner
Bus voltage	Core
Bus identity	Core
Line impedance	Core
Network topology	Core
Selected bus	UI
Active tool	UI
Canvas zoom	UI
Grid visibility	UI
Current interaction mode	UI
23. Event Infrastructure

The UI Core may provide application-level UI events.

Examples:

ToolChanged
SelectionChanged
CanvasChanged
PluginLoaded
RendererRegistered
NavigationChanged
UIStateChanged

Events should communicate UI/application state transitions.

They must not become an uncontrolled replacement for explicit Core APIs.

24. Event Direction

Preferred:

UI Component
     │
     ▼
UI Event
     │
     ▼
Controller
     │
     ▼
Core Operation

Avoid using UI events to directly mutate hidden Core state.

25. Service Registry

Where required, ui/core/ may provide controlled registration/discovery of UI services.

Examples:

Tool Registry
Renderer Registry
Plugin Registry
Command Registry

Registries should remain focused.

Avoid creating one universal registry that becomes responsible for every UI object.

26. Dependency Direction

The intended dependency direction is:

High-Level UI Components
          │
          ▼
       ui/core/
          │
          ▼
     UI Controllers
          │
          ▼
      GridForge Core

The Core must not depend on ui/core/.

Therefore:

core
  ✗──► ui.core

is prohibited.

27. Canvas Relationship

The Canvas subsystem consumes UI Core services.

Canvas
  │
  ├── Coordinate System
  ├── Snap System
  ├── Render System
  ├── Interaction Manager
  └── Navigation Controller
            │
            ▼
         ui/core/

The Canvas is not the owner of the shared UI infrastructure.

28. Rendering Relationship

The rendering subsystem uses:

ui/core/
   │
   ├── Renderer Registry
   ├── Renderer Loader
   └── Qt Abstraction

while the actual rendering logic remains in:

ui/renderers/

This maintains:

Infrastructure
      ≠
Concrete Rendering
29. Plugin Relationship

The plugin subsystem uses the UI Core plugin infrastructure.

ui/core/
   │
   ├── Plugin Contract
   ├── Plugin Registry
   ├── Plugin Loader
   ├── Plugin Context
   ├── Plugin State
   └── Plugin Events
             │
             ▼
       ui/plugins/

The concrete plugins remain outside the infrastructure layer.

30. Controller Relationship

The UI Core should not become the application's main controller.

Instead:

UI Component
      │
      ▼
ui/core Infrastructure
      │
      ▼
UI / Application Controller
      │
      ▼
GridForge Core

The UI Core provides infrastructure; controllers execute workflows.

31. Headless Boundary

ui/core/ itself is GUI infrastructure and therefore may depend on Qt where necessary.

However, this dependency must stop at the UI boundary.

                 GUI
                  │
          ┌───────┴───────┐
          ▼               ▼
       ui/core/         ui/canvas/
          │
          ▼
      Controllers
          │
          ▼
         Core

The Core remains headless.

32. No Engineering Computation

ui/core/ must not perform engineering calculations.

Prohibited responsibilities include:

Power Flow
Short Circuit
Y-Bus Assembly
Newton-Raphson
Protection Logic
Relay Coordination
Dynamic Integration

Instead:

ui/core/
    │
    ▼
Controller
    │
    ▼
Core Analysis / Solver / Protection
33. No Engineering State Duplication

Avoid:

ui/core/
    └── copy of network buses

or:

ui/core/
    └── independent topology

The UI should hold references, identifiers, selections, and presentation state as required, while engineering truth remains in the Core.

34. UI/Core Synchronization

The preferred synchronization model is:

Core State
    │
    ▼
Controller
    │
    ▼
UI Update

rather than:

UI State
    │
    ▼
Core State

The UI may request changes, but the Core determines the resulting authoritative engineering state.

35. Error Handling

UI Core infrastructure should preserve meaningful errors.

For example:

PluginLoadError
RendererLoadError
InvalidToolRegistration
InvalidPluginContract
QtInfrastructureError
UIServiceError

Engineering errors should remain distinguishable:

InvalidTopology
SolverFailure
ProtectionError

The UI Core should not convert every failure into an opaque generic UI exception.

36. Determinism

UI Core registries and loaders should behave deterministically.

Identical:

Plugin Set
Renderer Set
Tool Set
Application Configuration

should produce the same registration and loading behavior.

Determinism is important for:

Reproducibility
Testing
Debugging
Plugin lifecycle
Application startup
37. Performance

The UI Core should remain lightweight.

It should avoid:

Repeated expensive discovery
Unnecessary object duplication
Rebuilding registries unnecessarily
Heavy computation in event handlers
Engineering calculations
Blocking operations on the Qt event loop

Expensive engineering computation belongs in the Core execution layer.

38. Threading Boundary

Long-running engineering operations should not block the GUI event loop.

Conceptually:

UI Thread
    │
    ▼
Controller
    │
    ▼
Core Execution
    │
    ▼
Worker / Appropriate Backend
    │
    ▼
Result
    │
    ▼
UI Thread

ui/core/ may provide infrastructure for safely communicating results back to the UI, but numerical execution remains outside the UI subsystem.

39. Testing Strategy

The UI Core should be tested independently.

Qt Infrastructure Tests

Verify:

Correct Qt imports
Exported symbols
Framework consistency
Compatibility behavior
Registry Tests

Verify:

Registration
Duplicate handling
Lookup
Removal where supported
Deterministic ordering
Loader Tests

Verify:

Explicit loading
Failure handling
Dependency behavior
Lifecycle behavior
Contract Tests

Verify:

Required interfaces
Invalid implementations
Compatibility rules
Integration Tests

Verify:

Plugin
   ↓
Registry
   ↓
Loader
   ↓
Manager
   ↓
UI Composition
40. Architectural Anti-Patterns
Mixed Qt Frameworks

Incorrect:

PySide6
+
PyQt5

All GridForge V2 GUI code should use the approved PySide6 architecture.

Universal Registry

Incorrect:

Everything
   ↓
One Giant Registry

Registries should remain domain-specific.

UI Core as God Object

Incorrect:

ui/core/
    └── manages Canvas
    └── manages Tools
    └── manages Panels
    └── manages Solvers
    └── manages Network

The UI Core provides infrastructure, not universal application orchestration.

Engineering State in UI Core

Incorrect:

ui/core/
    └── authoritative Network

Engineering state belongs to GridForge Core.

Hidden Plugin Imports

Avoid uncontrolled imports where:

plugin_registry
      │
      └── imports every concrete plugin

Explicit plugin loading is preferred.

Rendering Logic in Core

Incorrect:

core.model.Bus
    └── creates QGraphicsItem

Rendering belongs to the UI.

41. Stable Contracts

ui/core/ should expose stable contracts for higher-level UI components.

Examples include:

Tool Contract
Plugin Contract
Renderer Contract
Controller Contract
UI Service Contract

Concrete implementations can evolve without forcing unrelated UI components to depend on implementation details.

42. Extensibility

The UI Core is designed to support future capabilities such as:

Additional tools
Additional renderers
Additional plugins
Command systems
Keyboard shortcut systems
UI themes
Workspace management
Dock/panel registration
Multi-canvas services
Context-sensitive actions

Extensions must preserve the existing ownership boundaries.

43. Multi-Canvas Support

The UI Core supports infrastructure needed by hierarchical Canvas navigation.

Potential contexts include:

Grid
 │
 ├── Substation
 │     ├── Bus
 │     ├── Transformer
 │     └── Feeder
 │
 └── Plant

The UI Core may maintain navigation-related infrastructure, but the underlying electrical hierarchy remains authoritative in the Core model/network.

44. Selection Architecture

Selection is UI state.

For example:

Selected Equipment
Active Item
Selected Terminal
Selection Set

The UI may identify selected engineering objects through stable engineering IDs.

It must not make selection identity equivalent to:

QGraphicsItem memory identity

or:

Numerical network index
45. Coordinate Architecture

UI coordinates are presentation coordinates.

Screen Coordinates
       │
       ▼
View Coordinates
       │
       ▼
Scene Coordinates
       │
       ▼
Engineering Reference Coordinates

Coordinate transformations must remain separate from electrical topology.

A screen position does not inherently represent an electrical node.

46. UI Core and Digital-Twin Principle

The UI Core participates in the digital-twin architecture as a presentation infrastructure layer.

               AUTHORITATIVE CORE
                      │
                      ▼
                 Controller
                      │
                      ▼
                  ui/core/
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Canvas       Panels      Plugins

The direction is intentional:

Engineering truth flows outward toward visualization; visualization does not become engineering truth.

47. Recommended Dependency Graph

The intended UI dependency structure is:

                         ui/
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
          canvas        tools        panels
             │            │            │
             └────────────┼────────────┘
                          ▼
                       ui/core
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Qt Abstraction  Registries   Contracts
                          │
                          ▼
                      Controllers
                          │
                          ▼
                         Core

Concrete dependency directions should remain acyclic.

48. Architectural Rules

The ui/core/ module follows these rules.

#	Rule	Requirement
1	UI infrastructure only	ui/core/ must not become an engineering subsystem
2	Core remains authoritative	Engineering truth belongs to core/
3	PySide6 only	No mixed Qt frameworks
4	Centralized Qt abstraction	Common Qt infrastructure is controlled through the Qt layer
5	Explicit plugin loading	Registry and concrete plugin imports remain controlled
6	Stable contracts	Higher-level UI components depend on explicit interfaces
7	Focused registries	Registries should not become universal object managers
8	No solver logic	Numerical computation remains in core/solver
9	No topology ownership	Electrical topology remains in core/network
10	No physical model ownership	Equipment remains in core/model
11	No persistence ownership	Project serialization remains outside UI Core
12	No hidden state duplication	Do not create competing engineering state
13	UI state is distinct	Selection/tool/navigation state remains presentation state
14	Headless Core preserved	UI dependencies must not propagate into Core
15	Deterministic infrastructure	Registration and loading behavior must be reproducible
16	No monolithic UI manager	Infrastructure responsibilities remain separated
49. Development and Freeze Process

The UI Core should follow the GridForge subsystem development methodology:

Architecture
     ↓
Contracts
     ↓
Implementation
     ↓
Audit
     ↓
Correction
     ↓
Fresh Audit
     ↓
Unit Tests
     ↓
Integration Tests
     ↓
GUI Integration
     ↓
Regression
     ↓
Finalization
     ↓
Freeze

A defect should be corrected at the correct architectural layer rather than hidden through downstream workarounds.

50. Relationship to the Rest of the UI

The UI Core provides infrastructure for:

                    ui/core/
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
     Canvas           Tools            Panels
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                    Plugins
                       │
                       ▼
                  Controllers
                       │
                       ▼
                  GridForge Core

It is therefore foundational but intentionally limited in scope.

51. Final UI Core Architecture
                         GRIDFORGE UI
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          Canvas             Tools            Panels
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                         ui/core/
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     Qt Abstraction       Registries          Contracts
          │                   │                   │
          │             ┌─────┼─────┐             │
          │             ▼     ▼     ▼             │
          │          Plugins Renderers Tools       │
          │                                        │
          └────────────────┬───────────────────────┘
                           ▼
                      UI Controllers
                           │
                           ▼
                    GridForge Core
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      Model             Network            Analysis
                                               │
                                               ▼
                                             Solver
52. Status

The ui/core/ module establishes the foundational infrastructure for GridForge V2's GUI.

Component	Responsibility
Qt Abstraction	Controlled PySide6 boundary
Plugin Registry	Plugin discovery/registration
Plugin Loader	Explicit plugin loading
Plugin Contracts	Stable plugin interfaces
Plugin Context	Controlled plugin service access
Plugin State	UI/plugin lifecycle state
Plugin Events	Plugin/application event communication
Renderer Registry	Renderer discovery
Renderer Loader	Explicit renderer loading
Snap System	Geometric UI snapping
Tool Infrastructure	Tool contracts and registration
UI State	Presentation/application UI state
53. Guiding Principle

The GridForge UI Core follows one central rule:

Provide shared GUI infrastructure without becoming a second engineering core.

The resulting dependency direction is:

                   USER
                     │
                     ▼
               GridForge UI
                     │
                     ▼
                  ui/core
                     │
                     ▼
                Controllers
                     │
                     ▼
               GridForge Core
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Model       Network       Analysis
                                   │
                                   ▼
                                 Solver

UI infrastructure belongs in ui/core/; engineering truth belongs in core/.

<p align="center"><em>GridForge UI Core — shared infrastructure, explicit contracts, one authoritative engineering core.</em></p>
