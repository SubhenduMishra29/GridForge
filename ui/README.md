# ⚡ GridForge UI

## Engineering Visualization, Interaction & Application Interface

The **GridForge UI** is the application-facing graphical subsystem of GridForge V2.

It provides the visual and interactive environment through which engineers can:

* Build and inspect electrical networks
* Navigate hierarchical engineering canvases
* Place and edit electrical equipment
* Create topology-aware connections
* Inspect engineering properties
* Visualize analysis results
* Interact with protection and simulation state
* Operate engineering tools
* Extend the interface through plugins

The UI is deliberately designed as a **client of GridForge Core**.

> **The UI visualizes and requests changes to engineering state. It does not own engineering truth.**

---

# 1. UI Architectural Principle

The GridForge UI follows one fundamental rule:

> **GUI state is presentation state; engineering state belongs to the GridForge Core.**

The relationship is:

```text
                         USER
                           │
                           ▼
                    GridForge UI
                           │
                           ▼
                 Application / Controller
                           │
                           ▼
                    GridForge Core
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
          Model         Network        Analysis
                           │
                           ▼
                         Solver
```

The reverse dependency is prohibited:

```text
Core
  X
  │
  ▼
GUI
```

Core modules must never require UI classes, Qt widgets, graphics items, rendering objects, or mouse/keyboard events.

---

# 2. Responsibilities

The UI subsystem is responsible for:

* Visualization
* User interaction
* Canvas management
* Engineering navigation
* Tool activation
* Selection
* Snapping
* Coordinate transformation
* Rendering
* Property presentation
* UI state
* Plugin-driven UI composition
* Interaction with application controllers

The UI subsystem is **not responsible for**:

* Owning physical equipment
* Owning electrical topology
* Performing power-flow calculations
* Performing short-circuit calculations
* Executing protection algorithms
* Maintaining authoritative measurement state
* Implementing numerical solvers
* Persisting engineering objects directly
* Becoming a second electrical network model

---

# 3. UI Architecture

The UI is organized into cooperating layers.

```text
┌────────────────────────────────────────────────────────────┐
│                     GridForge Application                  │
│                                                            │
│  Main Window • Menus • Toolbars • Panels • Status          │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    UI Composition Layer                    │
│                                                            │
│  Plugins • Registry • Plugin Manager • Plugin Context      │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    Interaction Layer                       │
│                                                            │
│  Tools • Interaction Manager • Snap • Navigation            │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                      Canvas Layer                           │
│                                                            │
│  Graphics View • Scene • Grid • Coordinates • Rendering      │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                       Core Client                          │
│                                                            │
│             Model • Network • Analysis • State             │
└────────────────────────────────────────────────────────────┘
```

The exact implementation may evolve, but the ownership boundaries remain fixed.

---

# 4. Repository Structure

The UI module follows the following conceptual structure:

```text
ui/
│
├── __init__.py
│
├── main_window.py
│
├── core/
│   ├── qt.py
│   ├── coordinate_system.py
│   ├── plugin_registry.py
│   ├── renderer_registry.py
│   ├── renderer_loader.py
│   ├── snap_system.py
│   └── ...
│
├── canvas/
│   ├── graphics_view.py
│   ├── grid_system.py
│   ├── coordinate_system.py
│   ├── render_system.py
│   ├── preview_layer.py
│   ├── interaction_manager.py
│   ├── navigation_controller.py
│   └── ...
│
├── controllers/
│   └── ...
│
├── interaction/
│   └── ...
│
├── items/
│   ├── base_item.py
│   ├── bus_item.py
│   ├── line_item.py
│   └── ...
│
├── renderers/
│   ├── bus_renderer.py
│   ├── line_renderer.py
│   └── ...
│
├── tools/
│   ├── select_tool.py
│   ├── bus_tool.py
│   └── line_tool.py
│
├── toolbars/
│   └── ...
│
├── plugins/
│   ├── __init__.py
│   ├── canvas_plugin.py
│   ├── panels_plugin.py
│   ├── toolbar_plugin.py
│   ├── status_plugin.py
│   ├── plugin_loader.py
│   ├── plugin_registry.py
│   ├── plugin_manager.py
│   ├── plugin_context.py
│   ├── plugin_contract.py
│   ├── plugin_state.py
│   └── plugin_events.py
│
└── ...
```

The exact file set may change during development.

The architectural responsibilities must not.

---

# 5. Qt Framework

GridForge UI uses:

> **PySide6**

PySide6 is the only supported Qt binding for the UI.

The UI must not mix:

```text
PySide6
PyQt5
PyQt6
```

A centralized Qt abstraction is provided through:

```text
ui/core/qt.py
```

The purpose of this layer is to:

* Centralize Qt imports
* Prevent framework mixing
* Provide controlled Qt access
* Simplify future compatibility work
* Keep low-level Qt implementation details localized

Core engineering code must not import this abstraction.

---

# 6. Main Window

`MainWindow` is intentionally kept thin.

It is responsible for application-level hosting and lifecycle coordination, not for implementing the entire UI architecture.

Conceptually:

```text
MainWindow
    │
    ▼
UI Registry / Composition
    │
    ├── CanvasPlugin
    ├── PanelsPlugin
    ├── ToolbarPlugin
    └── StatusPlugin
```

The main window should not become a monolithic controller containing:

* Canvas logic
* Rendering logic
* Tool logic
* Network editing logic
* Plugin discovery
* Property logic
* Simulation logic

Those responsibilities belong to specialized components.

---

# 7. Plugin-Driven UI Composition

GridForge UI uses a plugin-oriented composition architecture.

The composition system is responsible for constructing UI components dynamically.

Conceptually:

```text
MainWindow
    │
    ▼
UI Registry
    │
    ▼
Plugin Manager
    │
    ├── CanvasPlugin
    ├── PanelsPlugin
    ├── ToolbarPlugin
    └── StatusPlugin
```

The plugin system allows UI components to be added without turning `MainWindow` into a central implementation hub.

---

# 8. UI Plugin Responsibilities

### CanvasPlugin

Responsible for composing the primary engineering canvas environment.

Typical responsibilities:

* Graphics view
* Canvas scene
* Grid
* Coordinate system
* Rendering
* Interaction services

### PanelsPlugin

Responsible for application panels such as:

* Property panels
* Engineering information panels
* Study/result panels
* Navigation panels

### ToolbarPlugin

Responsible for engineering tool presentation and toolbar composition.

### StatusPlugin

Responsible for:

* Status information
* Interaction feedback
* Coordinate information
* Tool state
* Application messages

Plugins compose the UI.

They do not become owners of engineering state.

---

# 9. Canvas Architecture

The GridForge canvas is the primary engineering visualization surface.

```text
Canvas
 │
 ├── Graphics View
 ├── Scene
 ├── Grid System
 ├── Coordinate System
 ├── Snap System
 ├── Interaction Manager
 ├── Navigation Controller
 ├── Preview Layer
 └── Render System
```

The canvas provides graphical interaction with the engineering model while delegating engineering decisions to the appropriate core/application services.

---

# 10. Graphics View

The graphics view provides the Qt presentation surface for the engineering canvas.

Responsibilities include:

* Camera/view management
* Zoom
* Pan
* View transformation
* Mouse interaction routing
* Scene presentation
* Rendering integration

The graphics view must not become an electrical network controller.

---

# 11. Grid System

The grid system provides visual and interaction support for engineering placement.

Responsibilities may include:

* Grid visibility
* Grid spacing
* Grid alignment
* Snap reference points
* Visual guides

The grid is a presentation and interaction aid.

It does not determine electrical validity.

---

# 12. Coordinate System

GridForge separates coordinate transformation from engineering topology.

A coordinate system may translate between:

```text
Screen Coordinates
        │
        ▼
View Coordinates
        │
        ▼
Canvas Coordinates
        │
        ▼
Engineering Coordinates
```

Coordinate transformation must not be confused with electrical connectivity.

Two objects being visually close does not imply an electrical connection.

---

# 13. Snap System

The snap system provides precise graphical placement and connection assistance.

Possible snap targets include:

* Grid points
* Bus connection points
* Equipment terminals
* Line endpoints
* Engineering anchors

The snap system determines **where the user is attempting to interact**.

The network layer determines **whether the resulting engineering operation is valid**.

Therefore:

```text
Snap
  ≠
Electrical Validation
```

---

# 14. Navigation Controller

GridForge supports hierarchical engineering navigation.

Typical navigation:

```text
Grid
 │
 ├── Substation
 │      │
 │      ├── Bus
 │      ├── Transformer
 │      └── Feeder
 │
 └── Plant
```

The navigation controller manages the visual context.

It must not create a second electrical topology model.

Navigation state belongs to the UI.

Electrical topology belongs to `core.network`.

---

# 15. Multi-Canvas Architecture

GridForge supports multiple engineering visualization contexts.

Examples include:

* Grid canvas
* Substation canvas
* Plant canvas
* Feeder canvas
* Detailed equipment context

Each canvas represents a visualization context.

A canvas does not become an independent engineering database.

The authoritative model remains shared by the core.

```text
                 GridForge Core
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Grid View   Substation   Plant View
                    View
```

---

# 16. Engineering Items

UI items provide graphical representations of engineering entities.

Examples include:

```text
ui/items/
│
├── base_item.py
├── bus_item.py
├── line_item.py
└── ...
```

An item represents a visual object.

It must not become the authoritative physical object.

Conceptually:

```text
Core Bus
   │
   ▼
BusItem
   │
   ▼
BusRenderer
```

not:

```text
BusItem
   │
   └── becomes the real electrical Bus
```

---

# 17. Base Item

`BaseItem` provides common graphical behavior for UI objects.

Typical concerns include:

* Visual identity
* Selection
* Position
* Transformation
* Interaction hooks
* Rendering integration

Engineering properties should ultimately originate from authoritative core objects.

---

# 18. Bus Item

`BusItem` represents a graphical bus.

It may provide:

* Bus geometry
* Terminal visualization
* Selection
* Movement
* Connection anchors
* Visual state
* Interaction support

The actual electrical bus remains owned by the core model/network architecture.

---

# 19. Line Item

`LineItem` represents a graphical electrical connection.

Its graphical existence does not automatically establish a valid electrical relationship.

The correct sequence is:

```text
User Interaction
      │
      ▼
Line Tool
      │
      ▼
Connection Validation
      │
      ▼
Core Network
      │
      ▼
Electrical Relationship
      │
      ▼
LineItem / Rendering
```

This prevents the UI from becoming a parallel topology engine.

---

# 20. Rendering Architecture

Rendering is separated from graphical item behavior.

```text
Core Object
     │
     ▼
Renderer
     │
     ▼
Graphics Item / Canvas
```

Current renderer concepts include:

* `BusRenderer`
* `LineRenderer`
* Future equipment renderers

A renderer is responsible for visual representation.

It must not:

* Modify authoritative engineering configuration arbitrarily
* Create independent electrical state
* Perform numerical studies
* Replace core objects

---

# 21. Render System

The Render System coordinates rendering across the canvas.

Conceptually:

```text
RenderSystem
     │
     ├── BusRenderer
     ├── LineRenderer
     ├── TransformerRenderer
     ├── GeneratorRenderer
     └── Other Equipment Renderers
```

The Render System consumes state from authoritative sources and produces visual output.

Rendering is therefore a **derived representation**.

---

# 22. Preview Layer

The preview layer provides temporary graphical feedback during interactions.

Examples:

* Line preview
* Connection preview
* Equipment placement preview
* Snap indication
* Selection preview

Preview objects are transient UI state.

They must never be mistaken for committed engineering state.

For example:

```text
Line Preview
    ≠
Committed Electrical Line
```

A connection becomes engineering state only after the appropriate core operation succeeds.

---

# 23. Interaction Architecture

Interaction is separated from rendering.

```text
User Input
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
    ▼
Application / Core Operation
```

The Interaction Manager coordinates interaction without becoming a monolithic engineering controller.

---

# 24. Tool System

GridForge currently defines exactly **three concrete engineering tools**:

```text
SelectTool
BusTool
LineTool
```

This tool set is intentionally frozen at the current architectural baseline.

### SelectTool

Provides:

* Selection
* Deselection
* Object interaction
* Selection state handling

### BusTool

Provides:

* Bus placement interaction
* Bus placement preview
* Bus positioning
* Delegation to appropriate engineering creation services

### LineTool

Provides:

* Line creation interaction
* Start-terminal selection
* End-terminal selection
* Connection preview
* Delegation to topology validation
* Delegation to core network creation

Tools must not implement independent engineering models.

---

# 25. Tool Lifecycle

The conceptual tool lifecycle is:

```text
Inactive
   │
   ▼
Activated
   │
   ▼
Interaction
   │
   ├── Preview
   ├── Snap
   └── Validation
   │
   ▼
Commit / Cancel
   │
   ▼
Inactive
```

A tool owns interaction state only.

Committed engineering state belongs to the core.

---

# 26. Bus-Centric Editing

GridForge editing is centered around electrical buses and terminals.

The UI should guide the user toward valid engineering topology rather than allowing arbitrary graphical wiring.

```text
User
 │
 ▼
Select Tool
 │
 ▼
Select Equipment / Terminal
 │
 ▼
Bus / Terminal Context
 │
 ▼
Topology Validation
 │
 ▼
Core Network Operation
 │
 ▼
Visual Update
```

The graphical interface therefore reflects engineering constraints rather than replacing them.

---

# 27. Interaction Manager

The Interaction Manager coordinates:

* Active tool
* Mouse interaction
* Keyboard interaction
* Selection
* Snap requests
* Canvas interaction
* Preview state
* Navigation interaction

It should not become responsible for:

* Power-flow execution
* Electrical topology ownership
* Protection logic
* Numerical computation
* Project persistence

---

# 28. Selection Architecture

Selection is UI state.

```text
Core Object
      │
      ▼
Visual Representation
      │
      ▼
Selection State
```

Selection may be used to:

* Highlight an object
* Display properties
* Activate tools
* Provide context actions

Selection must not modify engineering truth merely because an object is selected.

---

# 29. Property Editing

Property panels provide controlled access to engineering configuration.

The intended flow is:

```text
User
 │
 ▼
Property Panel
 │
 ▼
Application / Controller
 │
 ▼
Core Model
 │
 ▼
Validation
 │
 ▼
Updated Engineering State
 │
 ▼
UI Refresh
```

Property panels must not silently maintain a competing copy of engineering properties.

Temporary editor state is permitted, but committed values belong to the core.

---

# 30. GUI State vs Engineering State

The UI may own state such as:

* Active tool
* Selected objects
* Current canvas
* Zoom
* Pan position
* Dock visibility
* Panel state
* View settings
* Interaction mode
* Preview state

The UI must not own authoritative state such as:

* Bus electrical parameters
* Equipment identity
* Network topology
* Y-bus
* Solver state
* Protection decisions
* Measurement infrastructure
* Persistent engineering configuration

This distinction is essential.

---

# 31. Controller Boundary

Application controllers provide the bridge between GUI interaction and core engineering operations.

```text
UI
 │
 ▼
Controller
 │
 ▼
Core
```

Controllers may coordinate:

* User commands
* Engineering operations
* Validation
* Result handling
* UI updates

Controllers should not duplicate core domain logic.

If an operation belongs to the engineering model or network, it should ultimately be implemented in the core.

---

# 32. Analysis Result Visualization

The UI may visualize engineering results from:

* Power flow
* Short circuit
* Contingency analysis
* Dynamics
* Protection
* Other analysis services

The conceptual flow is:

```text
Core Analysis
      │
      ▼
Engineering Result
      │
      ▼
UI Result Adapter / Controller
      │
      ▼
Visualization
```

The UI does not recalculate engineering results merely for visualization.

---

# 33. Protection Visualization

Protection results may be visualized through:

* Relay state
* Pickup indication
* Trip indication
* Protection zones
* TCC curves
* Fault location
* Breaker state
* Protection decision status

The UI displays the protection subsystem's authoritative result.

It does not independently execute protection algorithms.

---

# 34. Simulation Visualization

Simulation results may be visualized through:

* Voltage trends
* Current trends
* Frequency
* Generator state
* Relay state
* Breaker state
* Fault events
* Dynamic response
* Event timelines

The simulation engine remains in `core.simulation`.

The UI is responsible only for presentation and interaction.

---

# 35. Plugin Contracts

Plugins must interact through explicit contracts.

A plugin should have:

* Defined lifecycle
* Defined dependencies
* Defined capabilities
* Defined UI ownership
* Controlled access to application context

Plugins should not rely on undocumented internals.

The plugin architecture exists to enable extensibility without weakening the core architecture.

---

# 36. Plugin Loading

The UI plugin architecture uses explicit loading and composition.

Conceptually:

```text
Plugin Discovery
       │
       ▼
Plugin Loader
       │
       ▼
Plugin Registry
       │
       ▼
Plugin Manager
       │
       ▼
Plugin Context
       │
       ▼
UI Composition
```

The registry should remain a contract/index mechanism rather than becoming an implicit importer of every concrete plugin.

Explicit loading prevents hidden import side effects and makes application composition deterministic.

---

# 37. Plugin State

Plugin-specific runtime state belongs to the plugin/UI layer.

It must not silently become:

* Core engineering state
* Network state
* Solver state
* Persistent project state

If plugin configuration needs persistence, it should pass through the appropriate persistence/application mechanism.

---

# 38. Plugin Events

Plugins may communicate through defined events and application-level signals.

Events should be used to communicate state changes without creating hidden direct dependencies between unrelated plugins.

The preferred pattern is:

```text
Plugin A
   │
   ▼
Defined Event / Contract
   │
   ▼
Plugin B
```

rather than:

```text
Plugin A
   │
   └── directly manipulates Plugin B internals
```

---

# 39. Error Handling

UI errors should distinguish between:

### User interaction errors

Examples:

* Invalid selection
* Invalid tool operation
* Unsupported interaction

### Engineering validation errors

Examples:

* Invalid topology
* Invalid equipment configuration
* Invalid connection

### Numerical errors

Examples:

* Solver failure
* Non-convergence
* Invalid numerical state

### UI infrastructure errors

Examples:

* Renderer failure
* Plugin loading failure
* Missing UI component

These categories should not be collapsed into a generic GUI error.

---

# 40. Performance Principles

The UI should remain responsive even when engineering calculations are expensive.

The GUI must not perform heavy numerical computation directly in event handlers.

Long-running operations should be delegated to appropriate application/core execution mechanisms.

The architecture therefore follows:

```text
UI Event
   │
   ▼
Application / Controller
   │
   ▼
Core / Solver
   │
   ▼
Result
   │
   ▼
UI Update
```

The UI should remain responsible for interaction and visualization rather than numerical computation.

---

# 41. Headless Boundary

The UI is optional from the perspective of GridForge Core.

The following should remain possible:

```text
GridForge Core
      │
      ├── Automated Studies
      ├── Batch Processing
      ├── Testing
      ├── Server Execution
      └── Simulation
```

without importing the UI subsystem.

This is a critical architectural requirement.

---

# 42. Testing Strategy

The UI should be tested at multiple levels.

### Unit Tests

Test:

* Coordinate transformations
* Snap calculations
* Tool state
* Selection behavior
* Navigation state
* Plugin contracts
* Renderer behavior

### Component Tests

Test:

* Canvas
* Interaction Manager
* Tool Manager
* Render System
* Plugin composition
* Property panels

### Integration Tests

Test:

```text
UI Interaction
      │
      ▼
Controller
      │
      ▼
Core
      │
      ▼
Engineering State
      │
      ▼
UI Refresh
```

### Architectural Tests

Verify that:

* Core does not import UI
* Core does not import PySide6
* UI uses only PySide6
* Tools do not become network owners
* Renderers do not become engineering owners
* Plugins respect contracts
* GUI state does not replace core state

---

# 43. UI Architectural Rules

The following rules are mandatory for the GridForge UI architecture.

|  # | Rule                            | Requirement                                                          |
| -: | ------------------------------- | -------------------------------------------------------------------- |
|  1 | **Core independence**           | UI may depend on Core; Core must not depend on UI                    |
|  2 | **One engineering authority**   | Engineering state remains in Core                                    |
|  3 | **No GUI topology engine**      | Network topology belongs to `core.network`                           |
|  4 | **No GUI solver**               | Numerical computation belongs to `core.solver`                       |
|  5 | **Thin MainWindow**             | Application composition must remain plugin-driven                    |
|  6 | **PySide6 only**                | Do not mix Qt bindings                                               |
|  7 | **Items are representations**   | Graphics items are not engineering authorities                       |
|  8 | **Renderers are derived**       | Rendering must not own engineering state                             |
|  9 | **Tools own interaction state** | Tools do not own committed engineering state                         |
| 10 | **Snap is not topology**        | Snap assistance cannot establish electrical validity                 |
| 11 | **Canvas is not network**       | A canvas is a visualization context                                  |
| 12 | **Preview is transient**        | Preview objects are not committed engineering objects                |
| 13 | **Plugins use contracts**       | Plugins must not bypass established architecture                     |
| 14 | **Controllers coordinate**      | Controllers must not duplicate core domain logic                     |
| 15 | **No numerical work in GUI**    | Heavy engineering computation belongs outside GUI event handling     |
| 16 | **UI state remains UI state**   | Selection, navigation and view state do not become engineering state |
| 17 | **Explicit composition**        | Concrete plugins are explicitly loaded                               |
| 18 | **Deterministic composition**   | UI construction should be predictable and reproducible               |

---

# 44. Development Workflow

UI development follows the GridForge engineering freeze process:

```text
Architecture
     │
     ▼
Implementation
     │
     ▼
Audit
     │
     ▼
Correction
     │
     ▼
Fresh Audit
     │
     ▼
Component Tests
     │
     ▼
Integration Tests
     │
     ▼
Application Validation
     │
     ▼
Freeze
```

Production code should be corrected against the established architecture.

Tests should not be modified merely to accommodate an implementation defect.

If a test exposes a genuine architectural or implementation defect, production code should be corrected first.

---

# 45. Current Concrete Tool Baseline

The current GridForge UI tool system deliberately contains exactly three concrete tools:

```text
SelectTool
BusTool
LineTool
```

This is the current baseline.

Additional tools may be introduced later through an explicit architectural decision.

The existing tools should not be expanded implicitly merely to compensate for missing application services.

---

# 46. UI-to-Core Engineering Flow

The canonical network-editing flow is:

```text
                    USER
                      │
                      ▼
                  GUI Event
                      │
                      ▼
               InteractionManager
                      │
                      ▼
                  Active Tool
                      │
              ┌───────┴────────┐
              ▼                ▼
           Snap /           Preview
         Coordinates
              │                │
              └───────┬────────┘
                      ▼
              Application Layer
                      │
                      ▼
                Core Validation
                      │
                      ▼
               Core Engineering
                      │
                      ▼
             Network / Model State
                      │
                      ▼
                UI Synchronization
                      │
                      ▼
                   Render
```

This flow ensures that a graphical operation becomes engineering state only after the appropriate core operation succeeds.

---

# 47. Example: Creating a Bus

A bus creation operation conceptually follows:

```text
User activates BusTool
        │
        ▼
BusTool enters placement mode
        │
        ▼
Mouse movement
        │
        ▼
Coordinate / Grid / Snap
        │
        ▼
Placement Preview
        │
        ▼
User commits
        │
        ▼
Application Controller
        │
        ▼
Core Model Operation
        │
        ▼
Validation
        │
        ▼
Authoritative Bus Created
        │
        ▼
BusItem / Renderer Updated
```

The preview does not become authoritative merely because it is visible.

---

# 48. Example: Creating a Line

A line creation operation conceptually follows:

```text
User activates LineTool
        │
        ▼
Select Start Terminal
        │
        ▼
Snap / Preview
        │
        ▼
Select End Terminal
        │
        ▼
Topology Validation
        │
        ▼
Core Network Operation
        │
        ▼
Electrical Connection Created
        │
        ▼
LineItem / Renderer Updated
```

An arbitrary graphical line must not be accepted as an electrical connection without topology validation.

---

# 49. Example: Editing Engineering Properties

```text
User selects equipment
        │
        ▼
Property Panel
        │
        ▼
Edit Value
        │
        ▼
Application Controller
        │
        ▼
Core Model
        │
        ▼
Validation
        │
        ▼
Committed Engineering State
        │
        ▼
UI Refresh
```

The property panel is therefore an editor, not a second model.

---

# 50. What the UI Must Never Become

The GridForge UI must never evolve into:

* ❌ A second network model
* ❌ A second equipment database
* ❌ A numerical solver
* ❌ A protection engine
* ❌ A simulation engine
* ❌ A persistence engine embedded in widgets
* ❌ A monolithic `MainWindow`
* ❌ A collection of mutually dependent widgets
* ❌ A mixed PyQt/PySide application
* ❌ An uncontrolled plugin dependency graph

The UI exists to provide **engineering visualization, interaction, orchestration, and presentation**.

---

# 51. Final UI Architecture

The complete UI architecture can be summarized as:

```text
                         USER
                           │
                           ▼
                  ┌────────────────┐
                  │   MainWindow   │
                  └───────┬────────┘
                          │
                          ▼
                 UI Composition Layer
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Canvas        Panels      Toolbar
          Plugin        Plugin       Plugin
             │
             ▼
       Canvas / View
             │
      ┌──────┼───────┬──────────────┐
      ▼      ▼       ▼              ▼
   Grid   Snap   Interaction   Navigation
   System System   Manager      Controller
      │      │       │              │
      └──────┴───────┴──────────────┘
                     │
                     ▼
                  Tools
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      SelectTool   BusTool   LineTool
          │          │          │
          └──────────┼──────────┘
                     │
                     ▼
              Application Layer
                     │
                     ▼
                GridForge Core
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        Model     Network     Analysis
                                │
                                ▼
                              Solver
                     │
                     ▼
                Engineering State
                     │
                     ▼
              Render / Visualize
```

---

# 52. Guiding Principle

The GridForge UI follows one final rule:

> ## **The UI is the window into the engineering system, not the engineering system itself.**

The Core owns engineering truth.

The UI owns visualization and interaction.

The Application/Controller layer coordinates operations between them.

The plugin architecture composes the application without creating architectural coupling.

The canvas provides engineering visualization without becoming an electrical network.

Tools provide interaction without becoming engineering authorities.

Renderers visualize authoritative state without owning it.

This separation allows GridForge to maintain a scalable architecture capable of supporting:

* Large electrical networks
* Advanced engineering studies
* Protection simulation
* Dynamic simulation
* Multi-canvas engineering workflows
* Plugin extensibility
* Automated testing
* Headless execution
* Future digital-twin applications

---

<p align="center"><em>GridForge UI — visualize the system, interact with the engineering model, never replace it.</em></p>
