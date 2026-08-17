GridForge Canvas Module
Engineering Canvas Architecture for GridForge V2

The GridForge Canvas Module provides the interactive 2D engineering workspace used to visualize, navigate, and edit the electrical system.

The canvas is not a drawing application.

It is the visual interaction layer over the authoritative GridForge engineering model.

Its primary responsibilities are:

Engineering visualization
Interactive network editing
Coordinate transformation
Grid management
Snapping
Navigation
Interaction coordination
Rendering orchestration
Visual feedback
Multi-canvas context management

The canvas does not own electrical truth.

The Canvas visualizes and interacts with the engineering model; the Core owns the engineering model.

1. Purpose

The Canvas Module provides the visual workspace through which engineers interact with GridForge.

Conceptually:

                    GridForge Core
                         │
                         │ authoritative state
                         ▼
                  Canvas / UI Layer
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Rendering   Interaction  Navigation
             │           │           │
             └───────────┼───────────┘
                         ▼
                    User Interface

The canvas must therefore remain a client of the Core, rather than becoming another engineering state owner.

2. Architectural Position

The Canvas Module belongs to the UI layer.

┌─────────────────────────────────────────────┐
│                 GridForge UI                │
│                                             │
│  Main Window / Plugins / Panels / Toolbar   │
│                     │                       │
│                     ▼                       │
│               Canvas Module                 │
│                                             │
│   View • Scene • Interaction • Rendering    │
│   Grid • Snap • Coordinates • Navigation    │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
              Application / Core
                      │
                      ▼
             Engineering Model

The dependency direction is intentionally one-way:

GUI
 ↓
Application / Controller
 ↓
Core

The Core must not depend on the Canvas Module.

3. Core Principle

The fundamental Canvas rule is:

Graphical state is derived from engineering state; graphical objects are not authoritative engineering objects.

For example:

core.model.Bus
       │
       ▼
BusItem
       │
       ▼
BusRenderer
       │
       ▼
Graphics Scene

The BusItem represents the visual state of the bus.

It does not become the owner of:

Bus electrical parameters
Bus identity
Network connectivity
Voltage information
Power-flow state
Short-circuit state

Those remain owned by the appropriate Core subsystem.

4. Repository Structure

The Canvas subsystem is organized as a collection of specialized services.

A representative structure is:

ui/
│
├── canvas/
│   ├── __init__.py
│   ├── graphics_view.py
│   ├── grid_scene.py
│   ├── grid_system.py
│   ├── coordinate_system.py
│   ├── render_system.py
│   ├── preview_layer.py
│   ├── interaction_manager.py
│   └── navigation_controller.py
│
├── core/
│   ├── snap_system.py
│   └── ...
│
├── items/
│   ├── base_item.py
│   ├── bus_item.py
│   └── line_item.py
│
└── renderers/
    ├── bus_renderer.py
    └── line_renderer.py

The exact implementation may evolve, but the separation of responsibilities should remain intact.

5. Canvas Responsibilities

The Canvas Module is responsible for:

Visualization
Displaying electrical equipment
Displaying network connections
Displaying engineering overlays
Displaying simulation information
Interaction
Mouse interaction
Selection
Dragging
Tool interaction
Connection creation
Preview interaction
Spatial Services
Coordinate transformation
Grid calculation
Snapping
Scene positioning
Navigation
Pan
Zoom
View transformation
Hierarchical navigation
Rendering
Renderer coordination
Visual updates
Preview rendering
Scene synchronization
6. What the Canvas Does Not Own

The Canvas must not become the authoritative owner of:

Physical equipment
Electrical topology
Y-bus
Power-flow results
Protection state
Simulation state
Engineering identities
Numerical indices
Solver state

For example:

BusItem
    │
    ├── visual position
    ├── visual selection
    └── rendering state


core.model.Bus
    │
    ├── engineering identity
    ├── electrical properties
    └── engineering configuration

These are intentionally different responsibilities.

7. Qt Framework

GridForge V2 uses PySide6.

The Canvas Module must not introduce mixed Qt frameworks.

The intended dependency is:

PySide6
    │
    ▼
ui/core/qt.py
    │
    ▼
Canvas

The centralized Qt abstraction provides a controlled boundary for Qt-specific imports and compatibility handling.

Canvas code must not import PyQt5 or other incompatible Qt bindings.

8. Graphics View

The Graphics View provides the interactive viewport.

Conceptually:

GraphicsView
      │
      ▼
GraphicsScene
      │
      ├── Equipment Items
      ├── Connection Items
      ├── Grid
      ├── Preview
      └── Overlays

The view is responsible primarily for presentation and viewport interaction.

It must not become the network topology engine.

9. Graphics Scene

The scene provides the visual object container.

It may contain:

Bus items
Line items
Transformer items
Generator items
Load items
Grid visuals
Preview objects
Selection overlays
Engineering annotations

The scene represents the current visual context.

It does not replace the Core network.

10. Scene vs Network

A fundamental distinction is:

Graphics Scene
      ≠
Electrical Network

The scene answers:

What should currently be displayed?

The network answers:

What electrical system actually exists?

For example, removing a LineItem from the scene does not automatically constitute a valid deletion of an electrical line.

The correct operation is:

User Action
    │
    ▼
Tool / Controller
    │
    ▼
Core Network Operation
    │
    ▼
Authoritative State Updated
    │
    ▼
Canvas Refresh
11. Canvas Items

Canvas items provide visual representations of engineering entities.

Examples include:

BaseItem
    │
    ├── BusItem
    ├── LineItem
    ├── TransformerItem
    ├── GeneratorItem
    └── Other Equipment Items

Items may maintain visual state such as:

Position
Selection
Highlighting
Geometry
Display state
Interaction state

They must not become substitutes for Core model objects.

12. Engineering Identity

Canvas items must preserve the distinction between graphical and engineering identity.

For example:

BusItem
   │
   └── references Bus identity

The item itself is not the engineering identity.

The authoritative identity remains in the Core.

Asset ID
   ≠
BusItem object ID

This prevents graphical recreation from accidentally changing engineering identity.

13. Renderer Architecture

Rendering is separated from the Canvas items.

Core Object
     │
     ▼
Canvas Item
     │
     ▼
Renderer
     │
     ▼
Qt Graphics Representation

The renderer is responsible for translating engineering/visual state into graphical representation.

Examples:

BusRenderer
LineRenderer
TransformerRenderer
GeneratorRenderer
ProtectionRenderer
ResultRenderer
14. Render System

The RenderSystem coordinates rendering.

Conceptually:

                 RenderSystem
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 BusRenderer      LineRenderer   Other Renderers
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Canvas Scene

The RenderSystem should remain concerned with visualization.

It should not contain:

Power-flow algorithms
Network topology algorithms
Protection logic
Solver execution
15. Grid System

The Grid System provides spatial reference for engineering editing.

Responsibilities may include:

Grid spacing
Grid visibility
Grid alignment
Grid drawing
Grid coordinate calculation

Conceptually:

Grid Configuration
       │
       ▼
GridSystem
       │
       ▼
Canvas Grid

The grid is a visual editing aid.

It is not an electrical topology mechanism.

16. Coordinate System

The Coordinate System provides controlled transformation between coordinate spaces.

Typical spaces include:

Screen Coordinates
        │
        ▼
View Coordinates
        │
        ▼
Scene Coordinates
        │
        ▼
Engineering Coordinates

Coordinate transformations must remain deterministic.

This is particularly important for:

Equipment placement
Selection
Connection
Snapping
Zooming
Navigation
17. Coordinate Ownership

The Canvas must distinguish between:

Screen coordinates

Coordinates supplied by mouse/UI events.

Scene coordinates

Coordinates used by the Qt graphics scene.

Engineering coordinates

Coordinates representing the engineering layout.

The system should avoid silently mixing these coordinate systems.

18. Snap System

The Snap System provides topology-aware and geometry-aware positioning assistance.

Potential snap targets include:

Grid points
Bus connection points
Line terminals
Equipment terminals
Existing engineering anchors

Conceptually:

Pointer Position
      │
      ▼
Snap System
      │
      ├── Grid Snap
      ├── Terminal Snap
      ├── Bus Snap
      └── Engineering Anchor
      │
      ▼
Resolved Position

Snapping improves editing precision.

It must not independently create electrical topology.

19. Bus-Centric Editing

GridForge uses bus-centric network editing.

A graphical connection is valid only when it corresponds to a valid electrical relationship.

Therefore:

Graphical Proximity
       ≠
Electrical Connectivity

The Canvas provides the interaction necessary to request a connection.

The Core network determines whether that connection is electrically valid.

20. Connection Workflow

A typical line-creation operation is:

User selects Line Tool
          │
          ▼
Canvas interaction begins
          │
          ▼
First terminal selected
          │
          ▼
Preview Line
          │
          ▼
Second terminal selected
          │
          ▼
Connection request
          │
          ▼
Core Network Validation
          │
       ┌──┴──┐
       ▼     ▼
     Valid Invalid
       │       │
       ▼       ▼
   Commit   Reject
       │
       ▼
Canvas Update

The preview is graphical.

The committed connection is engineering state.

21. Preview Layer

The Preview Layer provides temporary visual feedback during interaction.

Examples include:

Line preview
Bus placement preview
Snap indicator
Connection candidate
Selection preview
Equipment placement preview

Preview objects are transient.

They must not be treated as authoritative engineering objects.

Preview
   ≠
Committed Engineering State
22. Interaction Manager

The Interaction Manager coordinates user interaction.

It may coordinate:

Active tool
Mouse events
Selection
Dragging
Connection workflows
Preview state
Snap requests
Navigation interaction

The Interaction Manager prevents individual graphics items from becoming monolithic controllers.

23. Interaction Flow

The intended flow is:

Qt Event
   │
   ▼
Graphics View
   │
   ▼
Interaction Manager
   │
   ▼
Active Tool
   │
   ├── Snap System
   ├── Coordinate System
   └── Core/Application Controller
             │
             ▼
        Engineering State

This separates event processing from engineering execution.

24. Tool Architecture

The Canvas works with the GridForge Tool System.

The current concrete tool baseline is:

SelectTool
BusTool
LineTool

The Canvas does not hard-code engineering behavior for each tool.

Instead:

Tool
  │
  ▼
Interaction Contract
  │
  ▼
Canvas Services
  │
  ▼
Core/Application Controller
25. SelectTool

SelectTool provides interaction for selecting engineering objects.

Selection may support:

Single selection
Multi-selection
Selection highlighting
Property inspection
Contextual actions

Selection state is GUI state.

It must not alter engineering state unless an explicit engineering operation is performed.

26. BusTool

BusTool provides interactive bus placement.

A typical workflow:

BusTool
   │
   ▼
Pointer Position
   │
   ▼
Coordinate / Grid Snap
   │
   ▼
Preview Bus
   │
   ▼
Commit Request
   │
   ▼
Core Model / Network
   │
   ▼
New Bus
   │
   ▼
Canvas Representation

The Canvas handles visual interaction.

The Core owns the resulting engineering bus.

27. LineTool

LineTool provides interactive line creation.

Its responsibilities include:

Selecting the first terminal
Tracking the cursor
Displaying the preview
Snapping to valid targets
Selecting the destination
Requesting the engineering connection

The LineTool must not directly construct or mutate the authoritative network representation.

28. Navigation Controller

The Navigation Controller manages movement through the canvas hierarchy.

It may support:

Pan
Zoom
Fit-to-view
Hierarchical navigation
Context changes
Substation navigation
Equipment-level views

Conceptually:

Grid Canvas
    │
    ▼
Substation Canvas
    │
    ▼
Equipment Context

Navigation changes the visual context.

It does not create a second engineering model.

29. Multi-Canvas Architecture

GridForge is designed for hierarchical visualization.

                         Grid
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     Substation A    Substation B      Plant
          │
     ┌────┼────┐
     ▼    ▼    ▼
   Bus  Tx   Feeder

Each canvas may represent a different engineering context.

The contexts remain views over the same authoritative digital twin.

30. Canvas Context

A canvas context may identify:

Current engineering scope
Visible objects
Current navigation level
Display configuration
Selection
View transform

The context is UI state.

It must not become a duplicate network model.

31. Canvas State

Canvas state may include:

Zoom level
Pan position
Selection
Active tool
Grid visibility
Snap configuration
Display preferences
Current navigation context
Temporary preview state

This state belongs to the UI.

Engineering state belongs to the Core.

32. State Ownership

The Canvas follows the GridForge state ownership model.

State	Owner
Physical equipment	core.model
Electrical topology	core.network
Network indexing	core.network
Solver state	core.solver
Protection state	Protection subsystem
Simulation runtime	core.simulation
Canvas position	Canvas/UI
Zoom	Canvas/UI
Selection	Canvas/UI
Preview	Canvas/UI
Grid display	Canvas/UI
Active tool	Tool/UI system

This distinction must be preserved.

33. Canvas and Core Communication

The Canvas should communicate with Core through application/controller contracts.

Preferred:

Canvas
  │
  ▼
Interaction / Application Controller
  │
  ▼
Core

Avoid:

Canvas Item
  │
  ▼
Direct Internal Network Mutation

The latter creates hidden coupling and makes the application difficult to validate.

34. Rendering vs Engineering Execution

Rendering should never perform engineering calculations.

For example:

BusRenderer

must not calculate:

Y-bus
Power flow
Fault current
Protection pickup
Dynamic response

Similarly:

LineRenderer

must not determine whether an electrical connection is valid.

Those responsibilities belong elsewhere.

35. Engineering Result Visualization

The Canvas may visualize results produced by Core analyses.

For example:

Power Flow
    │
    ▼
Analysis Result
    │
    ▼
Canvas Result Renderer
    │
    ▼
Voltage / Loading Visualization

Similarly:

Short Circuit
    │
    ▼
Fault Result
    │
    ▼
Fault Renderer
    │
    ▼
Canvas

The Canvas visualizes results.

It does not become their authoritative owner.

36. Protection Visualization

Protection results may be visualized on the Canvas.

Example:

ProtectionDecision
       │
       ▼
Protection Visualization
       │
       ▼
Relay / Breaker Display

The Canvas must not directly execute the protection decision.

The protection subsystem remains authoritative.

37. Simulation Visualization

Simulation state can be displayed through Canvas overlays.

Examples:

Voltage changes
Current changes
Breaker status
Fault location
Dynamic trajectories
Protection activity

The data flow remains:

Simulation
    │
    ▼
Simulation Result / Runtime State
    │
    ▼
Canvas Visualization

not:

Canvas
    │
    ▼
Simulation Engine
38. Performance Architecture

The Canvas should remain responsive while the Core performs engineering operations.

Long-running operations should not be embedded inside:

Mouse event handlers
Graphics painting
Renderers
Scene updates

Potential heavy operations include:

Power flow
Short circuit
Contingency studies
Dynamic simulation
Large topology reconstruction

These belong to appropriate application/core execution paths.

39. CPU / GPU Independence

The Canvas must remain independent of numerical backend implementation.

It should not assume:

NumPy arrays
SciPy sparse matrices
CUDA
CuPy
GPU memory
Solver-specific data structures

The visualization receives engineering results through defined interfaces.

CPU Solver ─┐
            ├──> Engineering Result ──> Canvas
GPU Solver ─┘
40. Headless Boundary

The Canvas is inherently graphical.

The GridForge Core is not.

Therefore:

Canvas
   │
   └── requires Qt

while:

Core
   │
   └── does not require Canvas

This enables:

Headless testing
Batch studies
Server execution
Numerical regression
Automated engineering workflows
41. Error Handling

Canvas errors should be separated from engineering errors.

Examples:

GUI Error
Unable to render item
Engineering Error
Invalid electrical connection
Numerical Error
Power-flow solver failed to converge

These represent fundamentally different failure domains.

The Canvas should display the result appropriately rather than conflating them.

42. Validation Boundary

When an engineering action originates from the Canvas:

User Action
    │
    ▼
Canvas
    │
    ▼
Application Controller
    │
    ▼
Core Validation
    │
    ▼
Engineering Operation

The Canvas may perform UI-level validation for usability.

It must not replace authoritative engineering validation.

43. Persistence

Canvas-specific state may be persisted where appropriate.

Examples:

View position
Zoom
Canvas context
Display preferences
Layout
Visibility configuration

Engineering state remains persisted through the project/persistence architecture.

The Canvas must not independently serialize the complete engineering model.

44. Plugin Integration

The Canvas is composed through the GridForge UI plugin architecture.

The primary composition component is:

CanvasPlugin

It may assemble:

CanvasPlugin
    │
    ├── GraphicsView
    ├── GridScene
    ├── GridSystem
    ├── CoordinateSystem
    ├── SnapSystem
    ├── InteractionManager
    ├── NavigationController
    ├── RenderSystem
    └── PreviewLayer

The plugin provides composition.

The individual services retain their specialized responsibilities.

45. Dependency Direction

The intended dependency direction is:

CanvasPlugin
     │
     ▼
Canvas Services
     │
     ▼
Application Contracts
     │
     ▼
GridForge Core

Not:

Core
 │
 └──> CanvasPlugin

and not:

BusItem
 │
 └──> Internal Solver
46. Architectural Rules

The Canvas Module follows these rules.

#	Rule	Requirement
1	Core owns engineering truth	Canvas never becomes the engineering authority
2	Canvas owns visual state	Position, selection, preview and viewport state belong to UI
3	Scene ≠ Network	Graphics scene is not the electrical network
4	Item ≠ Model	Graphics items represent Core objects
5	Renderer ≠ Solver	Rendering never performs numerical computation
6	Graphical proximity ≠ topology	Electrical connectivity requires Core validation
7	Preview is transient	Preview objects never become authoritative state
8	Tools use contracts	Tools do not bypass application/core boundaries
9	Qt remains isolated	Core code must not depend on Qt
10	PySide6 only	Do not introduce PyQt5 or mixed Qt bindings
11	Coordinates are explicit	Screen, scene and engineering coordinates must remain distinct
12	Navigation is visual	Navigation does not create duplicate engineering models
13	One engineering identity	Canvas items reference stable Core identities
14	Results are consumed	Canvas visualizes analysis results but does not own them
15	Heavy computation stays outside UI	Numerical studies must not execute inside rendering/event code
16	Headless Core remains possible	Canvas dependencies must not leak into Core
17	Plugin composition remains explicit	Canvas components are composed through established plugin contracts
47. Testing Strategy

The Canvas should be tested at several levels.

Unit Tests

Test individual services:

CoordinateSystem
GridSystem
SnapSystem
NavigationController
Item Tests

Test:

BaseItem
BusItem
LineItem

including:

Construction
Geometry
Selection
Identity association
Visual state
Renderer Tests

Verify that renderers correctly translate state into graphical representations.

Interaction Tests

Test:

Selection
Tool activation
Bus placement
Line creation
Snapping
Preview behavior
Navigation
Integration Tests

Verify:

User Interaction
      │
      ▼
Canvas
      │
      ▼
Application Controller
      │
      ▼
Core
      │
      ▼
Updated Engineering State
      │
      ▼
Canvas Refresh
GUI Regression

Representative engineering diagrams should verify:

Correct rendering
Correct connections
Correct snapping
Correct navigation
Correct selection
Correct visual result presentation
48. Canvas Development Workflow

Canvas development follows the GridForge engineering freeze process:

Architecture
     ↓
Contract Definition
     ↓
Implementation
     ↓
Audit
     ↓
Correction
     ↓
Fresh Audit
     ↓
Unit Testing
     ↓
Integration Testing
     ↓
GUI Validation
     ↓
Finalization
     ↓
Freeze

A GUI defect should not automatically be solved by changing Core architecture.

Likewise, a genuine Core defect should not be hidden by a Canvas workaround.

49. Common Architectural Anti-Patterns

The following patterns are prohibited.

GUI-Owned Network
BusItem
   └── owns electrical Bus

Incorrect.

Scene-Owned Topology
GraphicsScene
   └── determines electrical connectivity

Incorrect.

Renderer-Owned Engineering Logic
Renderer
   └── calculates power flow

Incorrect.

Tool-Owned Network
LineTool
   └── directly edits internal Y-bus

Incorrect.

Hidden Qt Dependency
core.network
    └── imports PySide6

Incorrect.

Duplicate State
Core Bus
   +
Canvas Bus State
   +
Renderer Bus State

as competing engineering state.

Incorrect.

50. Correct Architectural Pattern

The preferred pattern is:

                     User
                      │
                      ▼
                 Canvas / Tool
                      │
                      ▼
             Interaction Manager
                      │
                      ▼
            Application Controller
                      │
                      ▼
                 GridForge Core
                      │
              ┌───────┴───────┐
              ▼               ▼
            Model           Network
              │               │
              └───────┬───────┘
                      ▼
                Engineering State
                      │
                      ▼
                 Canvas Update
                      │
                      ▼
                   Renderer
                      │
                      ▼
                  Graphics

This preserves the authoritative ownership boundary.

51. Canvas Module Status

The Canvas architecture establishes the following major components:

Component	Responsibility
GraphicsView	Interactive viewport
GridScene	Visual scene management
GridSystem	Engineering grid
CoordinateSystem	Coordinate transformation
SnapSystem	Spatial/engineering snapping
InteractionManager	User interaction orchestration
NavigationController	Canvas navigation
RenderSystem	Rendering orchestration
PreviewLayer	Temporary interaction visuals
BaseItem	Common graphical item behavior
BusItem	Bus visualization
LineItem	Line visualization
BusRenderer	Bus rendering
LineRenderer	Line rendering

Additional equipment and result renderers may be introduced through the established architecture.

52. Final Canvas Architecture

The complete conceptual architecture is:

                         USER
                           │
                           ▼
                    Graphics View
                           │
                           ▼
                  Interaction Manager
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Active Tool   Snap System   Navigation
              │            │            │
              └────────────┼────────────┘
                           ▼
                  Application Controller
                           │
                           ▼
                    GridForge Core
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
            Model       Network       Results
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Canvas State
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Scene          Items       RenderSystem
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                      Graphics View
53. Guiding Principle

The GridForge Canvas follows one central principle:

The Canvas is a visual and interaction representation of the engineering system, never the engineering system itself.

The Core owns engineering truth.

The Network owns electrical representation.

The Analysis layer defines engineering studies.

The Solver performs numerical computation.

The Simulation subsystem owns runtime execution.

The Protection subsystem owns protection execution.

The Canvas provides the engineering workspace through which users see and interact with those authoritative systems.

Therefore:

             ENGINEERING TRUTH
                    │
                    ▼
              GRIDFORGE CORE
                    │
                    ▼
            APPLICATION LAYER
                    │
                    ▼
               CANVAS UI
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Rendering  Interaction Navigation
          │         │         │
          └─────────┼─────────┘
                    ▼
                   USER

One authoritative engineering model. One visual canvas. Many specialized visual and interaction services.

<p align="center"><em>GridForge Canvas — visualize the electrical system, interact with it precisely, and never compromise engineering truth.</em></p>
