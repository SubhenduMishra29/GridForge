GridForge Renderers Module
Engineering Visualization Rendering Layer

The ui/renderers/ module provides the concrete rendering implementations used by the GridForge V2 graphical interface.

Its responsibility is to transform authoritative GridForge engineering objects and UI presentation state into visual representations suitable for the Canvas.

Renderers visualize engineering truth; they do not own engineering truth.

1. Purpose

The renderer subsystem is responsible for visualizing GridForge objects such as:

Buses
Lines
Transformers
Generators
Loads
Breakers
Switches
Shunts
Motors
Protection equipment
Other engineering equipment

Conceptually:

                 GridForge Core
                      │
                      ▼
             Authoritative Object
                      │
                      ▼
              Renderer System
                      │
                      ▼
               ui/renderers/
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     BusRenderer  LineRenderer  Equipment
          │           │           │
          └───────────┼───────────┘
                      ▼
                Canvas / Scene

The renderer layer is therefore a presentation layer, not an engineering execution layer.

2. Architectural Position

The renderer subsystem sits between authoritative application state and the graphical Canvas.

┌──────────────────────────────────────────────┐
│                GridForge Core                │
│                                              │
│ Model • Network • Analysis • Protection      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              UI Controllers                  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             Rendering Infrastructure         │
│                 ui/core/                     │
│                                              │
│ Renderer Registry • Loader • Contracts       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              ui/renderers/                   │
│                                              │
│ Bus • Line • Transformer • Equipment         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                Canvas / Scene                │
└──────────────────────────────────────────────┘
3. Repository Position

The renderer subsystem belongs under the UI package:

GridForge/
│
├── core/
│   ├── model/
│   ├── network/
│   ├── analysis/
│   ├── solver/
│   ├── protection/
│   └── ...
│
├── ui/
│   ├── core/
│   │   ├── renderer_registry.py
│   │   └── renderer_loader.py
│   │
│   ├── canvas/
│   ├── controllers/
│   ├── items/
│   ├── plugins/
│   ├── renderers/
│   │   ├── __init__.py
│   │   ├── bus_renderer.py
│   │   ├── line_renderer.py
│   │   └── ...
│   │
│   ├── tools/
│   └── ...
│
└── main.py

The exact renderer set may expand as GridForge gains additional equipment types.

4. Core Responsibility

A renderer converts an engineering/UI representation into a visual representation.

Engineering Object
        │
        ▼
   Renderer
        │
        ▼
Graphics Representation

For example:

core.model.Bus
      │
      ▼
BusRenderer
      │
      ▼
Bus Graphics

And:

core.model.Line
      │
      ▼
LineRenderer
      │
      ▼
Line Graphics
5. Renderer vs Graphics Item

GridForge deliberately separates rendering logic from graphics item state.

Conceptually:

                Engineering Object
                       │
                       ▼
                   Renderer
                       │
                       ▼
                 Graphics Item
                       │
                       ▼
                    Canvas

For example:

core.model.Bus
      │
      ▼
BusRenderer
      │
      ▼
BusItem
      │
      ▼
QGraphicsScene

The renderer determines how the object is visually represented.

The graphics item provides the concrete scene representation and interaction surface.

6. Renderer Ownership

A renderer owns presentation behavior only.

It may own:

Visual geometry
Symbol construction
Drawing configuration
Display attributes
Visual state mapping
Rendering-specific calculations
Visual updates

It must not own:

Equipment identity
Electrical topology
Electrical parameters
Power-flow results as authoritative state
Protection decisions
Simulation state
Persistent project state
7. One Authoritative Engineering Object

The renderer must always derive its representation from authoritative application state.

               core.model
                   │
                   ▼
          Authoritative Object
                   │
                   ▼
               Renderer
                   │
                   ▼
            Visual Object

Never:

Renderer
   │
   └── independent engineering object

This would create competing sources of truth.

8. Bus Renderer

The Bus Renderer is responsible for visualizing an electrical bus.

Conceptually:

core.model.Bus
       │
       ▼
BusRenderer
       │
       ▼
BusItem
       │
       ▼
Canvas

Typical visual responsibilities include:

Bus geometry
Bus orientation
Bus dimensions
Labels
Visual selection state
Status indicators
Connection anchors
Engineering annotation

The Bus Renderer does not decide whether the bus exists electrically.

9. Line Renderer

The Line Renderer visualizes an electrical branch.

core.model.Line
       │
       ▼
LineRenderer
       │
       ▼
LineItem
       │
       ▼
Canvas

Typical responsibilities include:

Line geometry
Endpoint visualization
Line style
Directional display
Labels
Selection state
Visual status
Branch annotations

Electrical connectivity remains owned by the Core Network.

10. Transformer Renderer

A Transformer Renderer may visualize:

Transformer symbol
Primary/secondary terminals
Tap indication
Labels
Status
Selection state
Engineering annotations

Conceptually:

Transformer
     │
     ▼
TransformerRenderer
     │
     ▼
TransformerItem

The renderer must not calculate transformer electrical behavior.

11. Equipment Renderers

As GridForge expands, additional renderers may be introduced.

Examples:

GeneratorRenderer
LoadRenderer
BreakerRenderer
SwitchRenderer
ShuntRenderer
MotorRenderer
CTRenderer
PTRenderer
RelayRenderer

The general pattern remains:

Engineering Object
        │
        ▼
Specific Renderer
        │
        ▼
Specific Graphics Representation
12. Renderer Contracts

Concrete renderers should implement a stable rendering contract.

A renderer contract may define:

Supported object type
Rendering lifecycle
Creation
Update
Removal
Geometry update
Visual-state update
Selection-state update
Context information

Conceptually:

RendererContract
      │
      ├── supports()
      ├── create()
      ├── update()
      ├── remove()
      └── refresh()

The exact API is governed by the finalized UI Core contract.

13. Renderer Registry

The renderer registry belongs to the UI Core infrastructure.

ui/core/renderer_registry.py

Its role is to discover which renderer handles a particular visual object.

Conceptually:

Object Type
     │
     ▼
Renderer Registry
     │
     ▼
Renderer

For example:

Bus → BusRenderer
Line → LineRenderer

The registry should not contain the rendering implementation itself.

14. Renderer Loader

Renderer loading is separate from renderer registration.

Renderer Registry
        │
        ▼
Renderer Loader
        │
        ▼
Concrete Renderers

This keeps:

Discovery
    ≠
Implementation

and prevents the registry from becoming an uncontrolled importer of all rendering code.

15. Rendering Pipeline

The preferred rendering flow is:

Core Object
     │
     ▼
Controller
     │
     ▼
Renderer Selection
     │
     ▼
Renderer
     │
     ▼
Graphics Item
     │
     ▼
QGraphicsScene
     │
     ▼
QGraphicsView
     │
     ▼
User

This provides a clean separation between engineering state and presentation.

16. Rendering Is Derived State

Graphics are derived representations.

Authoritative State
       │
       ▼
     Render
       │
       ▼
Derived Visual State

Therefore, if a graphical representation becomes inconsistent:

The authoritative Core state must be trusted over the graphical representation.

The renderer should refresh from the authoritative state rather than attempting to reconstruct engineering truth from the Canvas.

17. No Reverse Engineering from Graphics

The renderer must not be treated as the source of engineering state.

Avoid:

QGraphicsItem
     │
     ▼
"Determine electrical topology"

Instead:

Core Network
     │
     ▼
Electrical topology
     │
     ▼
Renderer
     │
     ▼
Graphics

Graphical geometry is not an electrical network representation.

18. Bus-Centric Visualization

GridForge uses a bus-centric engineering visualization model.

Connections should visually reflect authoritative network relationships.

       Bus A
         │
         │
      Line L1
         │
         │
       Bus B

The renderer visualizes the relationship.

It does not independently decide that:

Bus A ↔ Line L1 ↔ Bus B

exists electrically.

That relationship comes from core.network.

19. Topology and Rendering

The distinction is:

Electrical Topology
        │
        ▼
core.network

versus:

Graphical Topology
        │
        ▼
ui/renderers + ui/canvas

The graphical topology must remain derived from the electrical topology.

20. Rendering and Interaction

Renderers may provide visual objects that support interaction.

For example:

User Click
    │
    ▼
Graphics Item
    │
    ▼
Interaction System
    │
    ▼
Controller
    │
    ▼
Core Operation

The renderer should not directly convert arbitrary mouse events into engineering mutations.

21. Rendering and Tools

Tools operate on the UI interaction layer.

For example:

SelectTool
     │
     ▼
Graphics Item
     │
     ▼
Selected Object

For an engineering modification:

LineTool
     │
     ▼
Canvas Interaction
     │
     ▼
Controller
     │
     ▼
Network Operation
     │
     ▼
Authoritative Core State
     │
     ▼
Renderer Refresh

This creates a controlled round trip.

22. Renderer Refresh

When Core state changes, the renderer should update the visual representation.

Core State Changed
       │
       ▼
Controller / Application Event
       │
       ▼
Renderer Update
       │
       ▼
Graphics Item

The renderer should not continuously poll the Core unless specifically required.

Event-driven or explicit refresh mechanisms are preferred.

23. Selection State

Selection is presentation state.

For example:

Bus
 │
 ├── Engineering identity → Core
 └── Selected/unselected → UI

A renderer may visually represent:

Selected
Hovered
Focused
Disabled
Highlighted

without modifying engineering state.

24. Engineering Status Visualization

Renderers may visualize engineering status.

For example:

Normal
Warning
Alarm
Out of Service
Faulted

But the renderer must distinguish:

Engineering Status
        │
        ▼
Core / Analysis / Simulation

from:

Visual Status
        │
        ▼
Renderer

The renderer maps authoritative status to visual presentation.

25. Analysis Result Visualization

Renderers may visualize results from engineering studies.

For example:

Power Flow
    │
    ▼
Line Loading
    │
    ▼
LineRenderer

or:

Short Circuit
      │
      ▼
Fault Current
      │
      ▼
Equipment Renderer

The renderer displays the result.

It does not calculate the result.

26. Protection Visualization

Protection-related renderers may visualize:

Relay status
Trip state
Pickup state
Protection zones
Fault indicators
Breaker state
Protection annotations

The execution remains:

Protection
     │
     ▼
ProtectionDecision
     │
     ▼
BreakerManager

while the renderer performs:

Engineering State
     │
     ▼
Visual Representation
27. Dynamic Simulation Visualization

Dynamic simulation results may be rendered as:

Generator states
Voltage state
Frequency state
Rotor angle
Protection status
Fault status
Time-domain indicators

The architecture remains:

Simulation
    │
    ▼
Runtime State / Results
    │
    ▼
Controller
    │
    ▼
Renderer
    │
    ▼
Canvas

The renderer never becomes the dynamic simulation engine.

28. Geometry Ownership

Graphical geometry belongs to the UI.

Examples:

Bus position
Line visual path
Transformer symbol size
Label position
Graphic rotation
Display offsets

However, geometry must not be confused with engineering topology.

For example:

Bus A is visually near Bus B

does not mean:

Bus A electrically connected to Bus B
29. Coordinate System

Renderers consume coordinates supplied through the UI coordinate infrastructure.

Engineering/UI Position
        │
        ▼
Coordinate System
        │
        ▼
Renderer
        │
        ▼
Graphics Geometry

Coordinate transformation logic should remain centralized where practical rather than duplicated across every renderer.

30. Qt Dependency

The renderer layer is part of the GUI and therefore may use the approved Qt framework.

GridForge V2 uses:

PySide6

The renderer subsystem must not introduce:

PyQt5
PyQt6
PySide2

or mixed Qt object types.

Common Qt abstractions should preferably come through:

ui/core/qt.py
31. Renderer Independence from Core Implementation

Renderers should depend on stable Core contracts rather than internal implementation details.

Preferred:

Renderer
   │
   ▼
Public Core Model API

Avoid:

Renderer
   │
   ▼
Private Core internals

This makes both the UI and Core easier to evolve.

32. Renderer Independence from Persistence

Renderers must not directly read or write project files.

Incorrect:

BusRenderer
    │
    └── save bus to JSON

Correct:

Persistence Layer
       │
       ▼
Core Model
       │
       ▼
Renderer

Persistence remains a separate subsystem.

33. Renderer Independence from Numerical Solvers

Renderers must not directly execute:

Newton-Raphson
Y-bus assembly
Short-circuit calculations
Dynamic integration
Protection algorithms
Contingency calculations

Correct:

Analysis / Solver
       │
       ▼
Result
       │
       ▼
Controller
       │
       ▼
Renderer
34. Performance

The renderer subsystem must remain responsive for large electrical networks.

Important considerations include:

Avoid unnecessary object recreation
Reuse graphics items where practical
Update only changed visual state
Avoid repeated expensive geometry calculations
Avoid blocking the Qt event loop
Use efficient scene updates
Avoid excessive signal emission
Support viewport-based optimization where appropriate

Rendering optimization must not alter engineering semantics.

35. Large Network Rendering

GridForge is intended to support large networks.

A scalable rendering architecture should support:

Large Model
     │
     ▼
Selective Rendering
     │
     ├── Visible Objects
     ├── Active Canvas
     ├── Detail Level
     └── Viewport

Future implementations may introduce:

Level-of-detail rendering
Object visibility filtering
Layer visibility
Cached symbols
Batched updates
Viewport culling

without changing Core ownership.

36. Multi-Canvas Rendering

GridForge supports hierarchical visualization.

Grid Canvas
    │
    ├── Substation A
    │      │
    │      └── Detailed Canvas
    │
    └── Substation B

The renderer subsystem should operate within the active Canvas context.

The same engineering object may have different visual representations depending on the current visualization context.

37. Renderer Context

A renderer may require contextual information such as:

Canvas
Viewport
Coordinate System
Theme
Display Settings
Selection State
Application State

This context should be provided explicitly.

Avoid hidden global state.

38. Theme and Visual Configuration

Visual properties may be controlled by UI configuration.

Examples:

Symbol Size
Line Width
Font
Label Visibility
Selection Appearance
Grid Visibility
Status Indicators

Engineering parameters must remain separate.

For example:

Line impedance ≠ Line visual width

and:

Transformer MVA rating ≠ Transformer symbol size

unless a deliberate visualization rule maps the two.

39. Renderer Testing

Renderer tests should cover:

Contract Tests
supports()
create()
update()
refresh()
remove()
Geometry Tests

Verify:

Correct positions
Correct endpoints
Correct transformations
Correct dimensions
State Tests

Verify:

Selection
Visibility
Highlighting
Status mapping
Integration Tests

Verify:

Core Object
    ↓
Renderer
    ↓
Graphics Item
    ↓
Canvas
40. Headless Testing Considerations

Because renderers use Qt, tests may require an appropriate Qt test environment.

Where possible:

Keep rendering logic separated from pure calculations
Test non-Qt transformations independently
Use isolated graphics tests for Qt behavior
Avoid requiring a visible desktop window unnecessarily

The engineering Core must remain fully headless regardless of renderer requirements.

41. Error Handling

Renderer errors should remain explicit.

Examples:

UnsupportedObjectType
RendererContractError
RendererCreationError
RendererUpdateError
InvalidRenderContext
InvalidGeometry

Errors should not silently corrupt the visual state.

If an authoritative Core object cannot be rendered, the UI should fail visibly and diagnostically rather than creating a misleading representation.

42. Determinism

Rendering behavior should be deterministic for identical:

Object State
Canvas State
Rendering Configuration
Theme
Viewport State

Deterministic rendering is valuable for:

GUI regression testing
Screenshot comparison
Debugging
Reproducibility
Engineering review
43. Architectural Anti-Patterns
Renderer as Engineering Owner

Incorrect:

BusRenderer
    └── owns Bus voltage

Correct:

core.model.Bus
    └── owns engineering state
Renderer as Network Engine

Incorrect:

LineRenderer
    └── determines electrical connectivity

Correct:

core.network
    └── determines connectivity
Renderer as Solver

Incorrect:

Renderer
    └── calculates power flow

Correct:

Solver
    └── calculates power flow
Renderer as Persistence Layer

Incorrect:

Renderer
    └── saves project

Correct:

Persistence
    └── saves project
Renderer as Controller

Avoid allowing renderers to become application-wide workflow managers.

Renderer
   ✗
   └── application orchestration

Rendering and orchestration remain separate.

44. Dependency Direction

The intended dependency direction is:

                         Core
                          │
                          ▼
                    Controllers
                          │
                          ▼
                    UI Rendering
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
         Renderers                   Items
             │                         │
             └────────────┬────────────┘
                          ▼
                         Qt

The reverse dependency is prohibited:

core
  ✗──► ui.renderers
45. Renderer Lifecycle

A typical renderer lifecycle is:

Registered
    │
    ▼
Loaded
    │
    ▼
Created
    │
    ▼
Attached to Canvas
    │
    ▼
Updated
    │
    ▼
Refreshed
    │
    ▼
Removed

The lifecycle should remain explicit and deterministic.

46. Renderer and Item Lifecycle

The renderer and graphics item should have clearly defined responsibilities.

Renderer
   │
   ├── Determines visual representation
   ├── Creates/updates presentation
   └── Applies visual state
             │
             ▼
        Graphics Item
             │
             └── Scene representation

Neither should silently become the owner of Core engineering state.

47. Relationship to ui/items/

The relationship is:

ui/renderers/
      │
      ▼
ui/items/
      │
      ▼
QGraphicsScene

For example:

BusRenderer
     │
     ▼
BusItem

and:

LineRenderer
     │
     ▼
LineItem

The exact responsibility split should remain stable:

Renderer = visual construction/update logic

Item = graphical scene object and interaction surface

48. Relationship to ui/canvas/

The Canvas owns the scene/view composition.

Renderer
   │
   ▼
Graphics Item
   │
   ▼
Canvas Scene
   │
   ▼
Graphics View

The renderer should not become the owner of the entire Canvas.

49. Relationship to ui/core/

The UI Core provides infrastructure.

ui/core/
   │
   ├── Renderer Contract
   ├── Renderer Registry
   └── Renderer Loader
             │
             ▼
       ui/renderers/
             │
             ├── BusRenderer
             ├── LineRenderer
             └── ...

This separation allows concrete renderers to evolve without redesigning the infrastructure.

50. Architectural Rules
#	Rule	Requirement
1	Render, do not own	Renderers visualize authoritative objects
2	Core is authoritative	Engineering state remains in core/
3	Network remains authoritative	Electrical connectivity remains in core/network
4	No numerical computation	Solvers perform engineering calculations
5	No persistence	Renderers do not save/load projects
6	No GUI orchestration	Application workflows belong to controllers
7	Stable contracts	Renderers use established renderer contracts
8	PySide6 only	No mixed Qt frameworks
9	Derived visual state	Graphics are derived from authoritative state
10	No hidden engineering state	Do not duplicate Core state
11	Explicit context	Rendering context should be controlled
12	Deterministic behavior	Identical state should produce reproducible rendering
13	Efficient updates	Update only what is necessary
14	Canvas independence	Renderers must not become Canvas controllers
15	Item separation	Rendering logic and graphics-item responsibilities remain distinct
51. Development Workflow

The renderer subsystem follows the GridForge development discipline:

Architecture
     ↓
Renderer Contract
     ↓
Concrete Renderer
     ↓
Integration
     ↓
Audit
     ↓
Correction
     ↓
Fresh Audit
     ↓
Renderer Tests
     ↓
Canvas Integration
     ↓
Regression
     ↓
Finalization
     ↓
Freeze

A renderer should be corrected at its architectural layer rather than patched around by Canvas or Controller code.

52. Future Renderer Capabilities

The architecture supports future rendering of:

Network Equipment
Bus
Line
Cable
Transformer
Generator
Load
Motor
Shunt
Breaker
Switch
Protection
Relay
CT
PT
Protection Zone
Trip State
Fault Indicator
TCC Information
Analysis
Voltage
Power Flow
Line Loading
Fault Current
Contingency Status
Voltage Violation
Thermal Violation
Dynamic Simulation
Rotor Angle
Frequency
Voltage
Generator State
Fault Propagation
Protection Response
Digital Twin
Online Measurement
Alarm
SCADA Status
Equipment Health
Real-Time State
Event State

All such capabilities remain visualization services over authoritative engineering state.

53. Final Renderer Architecture
                         GRIDFORGE CORE
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
               Model        Network      Results
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                         Controller
                              │
                              ▼
                       ui/core/renderer
                         infrastructure
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               Registry              Loader
                    │                   │
                    └─────────┬─────────┘
                              ▼
                       ui/renderers/
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     BusRenderer         LineRenderer      EquipmentRenderer
          │                   │                   │
          ▼                   ▼                   ▼
       BusItem             LineItem          EquipmentItem
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                         Canvas Scene
                              │
                              ▼
                         Graphics View
54. Status

The ui/renderers/ module is the concrete visualization layer of GridForge V2.

Layer	Responsibility
core.model	Owns physical engineering objects
core.network	Owns electrical representation
core.analysis	Owns study interpretation
core.solver	Owns numerical execution
ui/core	Owns renderer infrastructure/contracts
ui/renderers	Owns concrete visual rendering
ui/items	Owns graphical scene representations
ui/canvas	Owns Canvas/scene composition
ui/controllers	Owns application/UI workflows
55. Guiding Principle

The renderer architecture follows one fundamental rule:

Engineering objects are authoritative; graphics are derived.

Therefore:

                ENGINEERING TRUTH
                       │
                       ▼
                  GridForge Core
                       │
                       ▼
                   Controller
                       │
                       ▼
                  Renderer
                       │
                       ▼
                 Graphics Item
                       │
                       ▼
                    Canvas
                       │
                       ▼
                      USER

The direction must remain controlled:

Core → Controller → Renderer → Graphics

and never:

Graphics → Engineering Truth

ui/renderers/ exists to make GridForge engineering state visible, not to become the owner of that state.

<p align="center"><em>GridForge Renderers — authoritative engineering truth, deterministic visual representation.</em></p>
