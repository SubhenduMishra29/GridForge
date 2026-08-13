# 🖥️ GridForge — UI

### User Interface Architecture

The `ui/` package provides the application-facing graphical interface for GridForge V2.

The UI is responsible for:

- Visualization
- User interaction
- Engineering editing workflows
- Navigation
- Tool execution
- Rendering
- Property inspection
- Study configuration
- Result visualization
- Simulation monitoring

**The UI is not the authoritative owner of engineering state.**

GridForge follows the fundamental rule:

```
                         GRIDFORGE UI
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
          User Interaction            Visualization
                │                           │
                └─────────────┬─────────────┘
                              │
                              ▼
                     Application / Controller
                              │
                              ▼
                         GridForge Core
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
              Model        Network        Solver
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                         Engineering State
```

> The UI is therefore a client of the GridForge Core, not a replacement for it.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [UI Technology](#2-ui-technology)
3. [UI Package Structure](#3-ui-package-structure)
4. [Application Layer](#4-application-layer)
5. [Main Window](#5-main-window)
6. [Engineering Canvas](#6-engineering-canvas)
7. [Scene and View Separation](#7-scene-and-view-separation)
8. [Graphical Items](#8-graphical-items)
9. [Rendering System](#9-rendering-system)
10. [Rendering Principles](#10-rendering-principles)
11. [Tool System](#11-tool-system)
12. [Tool Registry](#12-tool-registry)
13. [Bus Tool](#13-bus-tool)
14. [Line Tool](#14-line-tool)
15. [Snap System](#15-snap-system)
16. [Coordinate System](#16-coordinate-system)
17. [Navigation System](#17-navigation-system)
18. [Multi-Canvas Architecture](#18-multi-canvas-architecture)
19. [Selection System](#19-selection-system)
20. [Property Inspector](#20-property-inspector)
21. [Project Explorer](#21-project-explorer)
22. [Controllers](#22-controllers)
23. [Command Architecture](#23-command-architecture)
24. [Undo / Redo](#24-undo--redo)
25. [Engineering Modes](#25-engineering-modes)
26. [Design Mode](#26-design-mode)
27. [Control Mode](#27-control-mode)
28. [Analysis Mode](#28-analysis-mode)
29. [Protection Mode](#29-protection-mode)
30. [Simulation Mode](#30-simulation-mode)
31. [Status and Event System](#31-status-and-event-system)
32. [Engineering Overlays](#32-engineering-overlays)
33. [Result Visualization](#33-result-visualization)
34. [Protection Visualization](#34-protection-visualization)
35. [TCC Visualization](#35-tcc-visualization)
36. [Simulation Timeline](#36-simulation-timeline)
37. [Event Timeline](#37-event-timeline)
38. [Theme and Visual Design](#38-theme-and-visual-design)
39. [Dark / Light Engineering Themes](#39-dark--light-engineering-themes)
40. [Accessibility](#40-accessibility)
41. [Keyboard Interaction](#41-keyboard-interaction)
42. [Contextual Tools](#42-contextual-tools)
43. [UI Plugin Architecture](#43-ui-plugin-architecture)
44. [Renderer Registry](#44-renderer-registry)
45. [Tool Registry (Expanded)](#45-tool-registry-expanded)
46. [Application State](#46-application-state)
47. [Core State Synchronization](#47-core-state-synchronization)
48. [No GUI-Only Engineering State](#48-no-gui-only-engineering-state)
49. [Error Handling](#49-error-handling)
50. [Future UI Roadmap](#50-future-ui-roadmap)
51. [Future UI Architecture](#51-future-ui-architecture)
52. [UI Architectural Invariants](#52-ui-architectural-invariants)
53. [Performance Strategy](#53-performance-strategy)
54. [Large-Network Visualization](#54-large-network-visualization)
55. [Reporting](#55-reporting)
56. [Import / Export](#56-import--export)
57. [Automation and Scripting](#57-automation-and-scripting)
58. [Future Digital-Twin Interface](#58-future-digital-twin-interface)
59. [Final UI Architecture](#59-final-ui-architecture)
60. [Summary](#60-summary)
61. [Current Status](#61-current-status)

---

## 1. Design Philosophy

GridForge UI is designed as a professional engineering interface for building, inspecting, analyzing, and simulating electrical systems.

The design principles are:

- Core owns engineering truth.
- UI owns presentation and interaction state.
- Every engineering modification is performed through core services.
- The GUI never performs authoritative engineering calculations.
- The GUI never stores engineering state only in graphics objects.
- Rendering is separate from engineering models.
- Tools are separate from rendering.
- Navigation is separate from editing.
- The UI must remain modular and extensible.
- The application must remain capable of headless core execution.

```
UI State
   │
   ▼
Interaction
   │
   ▼
Controller / Application Service
   │
   ▼
GridForge Core
   │
   ▼
Authoritative Engineering State
```

---

## 2. UI Technology

GridForge V2 uses:

```
Python
   │
   ▼
PySide6
   │
   ▼
Qt Graphics / Widgets
```

The UI must use PySide6 consistently. **Mixed Qt frameworks are not permitted.**

The UI should use a centralized Qt abstraction layer:

```text
ui/
└── core/
    └── qt.py
```

> This prevents Qt-specific implementation details from being scattered throughout the application.

---

## 3. UI Package Structure

```text
ui/
│
├── __init__.py
│
├── core/
│   ├── qt.py
│   ├── application.py
│   ├── theme.py
│   ├── commands.py
│   └── state.py
│
├── canvas/
│   ├── scene.py
│   ├── view.py
│   ├── coordinate_system.py
│   └── navigation.py
│
├── items/
│   ├── bus_item.py
│   ├── line_item.py
│   ├── transformer_item.py
│   ├── generator_item.py
│   ├── load_item.py
│   ├── breaker_item.py
│   └── ...
│
├── rendering/
│   ├── render_system.py
│   ├── bus_renderer.py
│   ├── line_renderer.py
│   └── ...
│
├── tools/
│   ├── tool.py
│   ├── tool_registry.py
│   ├── bus_tool.py
│   ├── line_tool.py
│   ├── transformer_tool.py
│   └── ...
│
├── interaction/
│   ├── interaction_manager.py
│   ├── selection.py
│   ├── snapping.py
│   └── gestures.py
│
├── controllers/
│   ├── project_controller.py
│   ├── network_controller.py
│   ├── analysis_controller.py
│   └── simulation_controller.py
│
├── panels/
│   ├── properties/
│   ├── explorer/
│   ├── analysis/
│   ├── protection/
│   └── simulation/
│
└── dialogs/
    ├── project/
    ├── equipment/
    ├── analysis/
    └── settings/
```

> The exact package layout may evolve during implementation. The architectural responsibilities must remain separated even if files are reorganized.

---

## 4. Application Layer

The application layer is responsible for coordinating the UI application.

```
User
 │
 ▼
Application
 │
 ├── Main Window
 ├── Workspace
 ├── Canvas
 ├── Panels
 ├── Tools
 └── Controllers
```

The application layer should not contain engineering algorithms. Instead:

```
UI Action
   │
   ▼
Controller
   │
   ▼
Core Service
   │
   ▼
Engineering State
```

---

## 5. Main Window

The GridForge main window provides the primary engineering workspace.

```
┌───────────────────────────────────────────────────────────────┐
│ Menu / Application Commands                                    │
├───────────────────────────────────────────────────────────────┤
│ Toolbar / Engineering Tools                                    │
├───────────────┬───────────────────────────────────┬────────────┤
│               │                                    │            │
│ Project /     │                                    │ Property   │
│ Network       │          Engineering Canvas        │ Inspector  │
│ Explorer      │                                    │            │
│               │                                    │            │
│               │                                    │            │
├───────────────┴───────────────────────────────────┴────────────┤
│ Status / Simulation / Validation / Messages                    │
└───────────────────────────────────────────────────────────────┘
```

> The interface should support configurable panels and workspaces.

---

## 6. Engineering Canvas

The canvas is the primary environment for electrical-system visualization and editing. It is responsible for:

- Displaying network objects
- Displaying connections
- Selecting objects
- Moving graphical objects
- Snapping
- Zooming
- Panning
- Navigation
- Previewing tools
- Displaying engineering status

> The canvas does not own the underlying electrical network.

---

## 7. Scene and View Separation

The UI separates:

```
Scene → Graphical Objects
View  → Camera / Zoom / Pan / Presentation
```

```
GridForge Core
      │
      ▼
Render System
      │
      ▼
QGraphicsScene
      │
      ▼
QGraphicsView
```

> The scene represents the current graphical presentation. The view controls how the presentation is observed.

---

## 8. Graphical Items

Graphical items represent the visual representation of core objects.

| Core Object | Graphical Item |
|---|---|
| Bus | `BusItem` |
| Line | `LineItem` |
| Transformer | `TransformerItem` |
| Generator | `GeneratorItem` |
| Load | `LoadItem` |
| Breaker | `BreakerItem` |

A graphical item must not become the authoritative engineering object.

**Correct:**
```
BusItem
   │
   └── references → core.model.Bus
```

**Incorrect:**
```
BusItem
   └── contains the only copy of Bus engineering state
```

---

## 9. Rendering System

Rendering is separated from graphical item lifecycle and engineering state.

```
Core Object
     │
     ▼
Render System
     │
     ├── BusRenderer
     ├── LineRenderer
     ├── TransformerRenderer
     ├── GeneratorRenderer
     └── Equipment Renderers
     │
     ▼
Graphical Item
```

> The rendering system determines how engineering objects are represented visually.

---

## 10. Rendering Principles

Renderers should be:

- Deterministic
- Lightweight
- Reusable
- Independent of engineering calculations
- Independent of project persistence
- Independent of solver implementation

> Rendering should visualize state rather than calculate state. For example, the renderer may display `Bus Voltage = 1.02 pu` but must not become responsible for calculating the bus voltage.

---

## 11. Tool System

GridForge uses a dedicated engineering Tool System. Tools represent user actions such as:

- Create bus / line / transformer / generator / load / breaker
- Connect equipment
- Move equipment
- Delete equipment
- Inspect equipment
- Configure protection
- Configure studies

```
User
 │
 ▼
Tool
 │
 ▼
Controller
 │
 ▼
Core
```

> Tools must not directly manipulate internal solver state.

---

## 12. Tool Registry

Tools should be registered through a centralized registry.

```python
tool_registry.register(BusTool)
tool_registry.register(LineTool)
tool_registry.register(TransformerTool)
```

The registry allows:

- Dynamic tool discovery
- Plugin tools
- Toolbar integration
- Keyboard shortcuts
- Contextual tools
- Future scripting support

---

## 13. Bus Tool

The Bus Tool creates and edits bus objects.

```
Activate Bus Tool
       │
       ▼
Move Cursor
       │
       ▼
Preview Bus
       │
       ▼
Click Canvas
       │
       ▼
Create Core Bus
       │
       ▼
Register in Network
       │
       ▼
Create / Update BusItem
```

> The core object must be created before the graphical representation becomes authoritative.

---

## 14. Line Tool

The Line Tool is topology-aware.

```
Start Line Tool
      │
      ▼
Select Source Terminal
      │
      ▼
Preview Connection
      │
      ▼
Snap to Valid Target
      │
      ▼
Validate Connection
      │
      ▼
Create Core Line
      │
      ▼
Update Rendering
```

> The tool must reject electrically invalid connections. Graphical proximity alone must not determine electrical connectivity.

---

## 15. Snap System

The Snap System provides precise engineering placement and connection. Potential snap targets include:

- Bus connection points
- Terminals
- Line endpoints
- Equipment terminals
- Grid coordinates
- Predefined engineering anchors

```
Cursor
  │
  ▼
Snap Candidates
  │
  ▼
Engineering Validation
  │
  ▼
Valid Snap Target
```

> The Snap System should remain independent from the core topology engine, while using core validation to determine whether a proposed connection is valid.

---

## 16. Coordinate System

The Coordinate System provides a controlled mapping between:

```
Screen Coordinates
        ↕
Canvas Coordinates
        ↕
Engineering Coordinates
```

This allows:

- Zoom-independent positioning
- Accurate snapping
- Consistent object placement
- Pan/zoom transformations
- Future geographic coordinates
- Print/export layouts

---

## 17. Navigation System

The Navigation System manages movement through the engineering workspace. Supported operations include:

- Pan
- Zoom
- Fit-to-view
- Zoom-to-selection
- Zoom-to-equipment
- Hierarchical navigation
- Canvas switching

Future navigation may support:

```
Grid
 │
 ├── Region
 │    └── Substation
 │          └── Switchyard
 │                └── Feeder
 │
 └── Plant
```

---

## 18. Multi-Canvas Architecture

GridForge is designed for multiple engineering canvases.

```
Grid Canvas
   │
   ├── Substation A Canvas
   ├── Substation B Canvas
   └── Plant Canvas
```

A canvas represents a visualization context. The underlying engineering model remains shared:

```
Canvas A ─┐
Canvas B ─┼──> Same Core Model
Canvas C ─┘
```

> Multiple views must never create multiple authoritative network models.

---

## 19. Selection System

The Selection System manages graphical and engineering selection, which may include:

- Single object
- Multiple objects
- Connected equipment
- Network region
- Bus and connected branches
- Protection elements
- Analysis results

> Selection state is UI state. It should not be confused with engineering ownership.

---

## 20. Property Inspector

The Property Inspector provides structured editing of engineering objects.

```
Transformer
────────────────────────
ID              TR-001
Name            Main Transformer
Rating          40 MVA
HV Voltage      132 kV
LV Voltage      33 kV
Impedance       10.5 %
Status          In Service
```

The inspector reads authoritative core state. When the user modifies a property:

```
Property Editor
      │
      ▼
Controller
      │
      ▼
Core Model
      │
      ▼
Validation
      │
      ▼
Updated State
      │
      ▼
UI Refresh
```

> The inspector must not directly mutate arbitrary internal fields.

---

## 21. Project Explorer

The Project Explorer provides hierarchical access to the digital twin.

```
Project
│
├── Network
│   ├── Buses
│   ├── Lines
│   ├── Transformers
│   ├── Generators
│   └── Loads
│
├── Protection
│   ├── Relays
│   ├── Protection Elements
│   └── Schemes
│
├── Studies
│   ├── Power Flow
│   ├── Short Circuit
│   ├── Contingency
│   └── Dynamics
│
└── Results
```

> The explorer is a navigation interface, not an independent database.

---

## 22. Controllers

Controllers translate UI intent into core operations, for example:

- `ProjectController`
- `NetworkController`
- `AnalysisController`
- `ProtectionController`
- `SimulationController`

```
UI Event
   │
   ▼
Controller
   │
   ├── Validate Request
   ├── Call Core Service
   ├── Handle Result
   └── Notify UI
```

> Controllers should not duplicate core engineering logic.

---

## 23. Command Architecture

UI operations should eventually use a command-based architecture: `Create Bus`, `Delete Line`, `Move Equipment`, `Change Transformer Rating`, `Enable Protection Element`, `Run Power Flow`.

Each operation becomes an explicit command, providing a foundation for:

- Undo
- Redo
- Transaction management
- Command history
- Scripting
- Automation
- Audit trails

---

## 24. Undo / Redo

A future GridForge UI should provide comprehensive undo/redo.

```
Create Bus
      ↓
Create Line
      ↓
Move Transformer
      ↓
Delete Load
```

The user should be able to:

```
Undo → Delete Load
Undo → Move Transformer
Undo → Create Line
Redo → Create Line
```

> Undo/redo should operate on core state through controlled commands rather than by simply restoring graphical positions.

---

## 25. Engineering Modes

The UI is intended to support distinct operating modes:

- Design Mode
- Control Mode
- Analysis Mode
- Protection Mode
- Simulation Mode
- Review Mode

> Each mode can provide a different set of tools and visual overlays, preventing the UI from becoming overloaded with unrelated operations.

---

## 26. Design Mode

Design Mode is intended for engineering model creation and modification:

- Create equipment
- Edit equipment
- Connect terminals
- Modify ratings
- Configure network
- Configure topology
- Validate engineering model

---

## 27. Control Mode

Control Mode is intended for operational interaction with the digital twin:

- Breaker open/close
- Switch operation
- Equipment status
- Interlocking
- Control commands
- Operational state visualization

> All control actions must pass through appropriate core/control services.

---

## 28. Analysis Mode

Analysis Mode provides access to engineering studies.

```
Select Study
      │
      ▼
Configure Study
      │
      ▼
Validate
      │
      ▼
Execute Solver
      │
      ▼
Display Results
```

> The UI does not perform the numerical study itself.

---

## 29. Protection Mode

Protection Mode is intended for:

- Relay configuration
- Protection-element inspection
- Pickup visualization
- Trip logic visualization
- TCC studies
- Relay coordination
- Fault-event analysis
- Protection-event playback

A multifunction relay may be displayed as:

```
Relay R1
│
├── 50
├── 51
├── 46
├── 67
└── 50BF
```

> The UI reflects the core protection architecture.

---

## 30. Simulation Mode

Simulation Mode provides runtime visualization, with potential displays including:

- Simulation time
- Bus voltage
- Frequency
- Generator state
- Breaker status
- Relay pickup / operation
- Trip commands
- Fault events
- Dynamic plots

> The UI observes simulation state rather than becoming its owner.

---

## 31. Status and Event System

The UI should provide structured system feedback.

```
INFO
Network validated successfully.

WARNING
Bus B-102 has no voltage reference.

ERROR
Line L-201 cannot connect to selected terminal.

EVENT
Relay R1-51 picked up.

TRIP
Breaker BRK-201 received trip command.
```

> Messages should originate from structured core/application events where possible.

---

## 32. Engineering Overlays

The UI should support visual overlays for engineering information:

- Voltage
- Current
- Power Flow
- Loading
- Fault Current
- Protection Pickup
- Protection Trip
- Breaker Status
- Contingency Status
- Dynamic State

> An overlay should be a visualization of an existing result or state. It should not independently calculate engineering values.

---

## 33. Result Visualization

Results from core analyses may be represented through:

- Canvas overlays
- Tables
- Plots
- Equipment labels
- Color-independent status indicators
- Alarms
- Reports
- Event timelines

```
Power Flow Result
       │
       ├── Bus Voltages
       ├── Branch Flows
       ├── Losses
       └── Convergence Status
```

---

## 34. Protection Visualization

Future protection visualization may include:

```
Relay
 │
 ├── Measurement
 │
 ├── Pickup
 │
 ├── Timer
 │
 ├── Operate
 │
 ├── Trip Request
 │
 └── Breaker Operation
```

> The UI may display the complete protection event chain without coupling the renderer directly to breaker implementation.

---

## 35. TCC Visualization

The UI is intended to eventually support Time-Current Characteristic visualization.

```
Current
  │
  │       Relay A
  │      ╱
  │     ╱
  │    ╱      Relay B
  │   ╱      ╱
  │  ╱      ╱
  │ ╱      ╱
  └────────────────── Time
```

> The TCC calculation belongs to the protection/coordination subsystem. The UI is responsible only for displaying the calculated curves and engineering settings.

---

## 36. Simulation Timeline

A future simulation timeline may provide:

```
0.000 s ─────────────── 1.000 s ─────────────── 2.000 s
   │                         │                       │
   │                         │                       │
 Initial State             Fault                  Clearing
                             │                       │
                             ▼                       ▼
                         Relay Pickup             Breaker Trip
```

Users should be able to:

- Pause
- Resume
- Inspect events
- Step through simulation
- Navigate to event times
- Inspect equipment state

---

## 37. Event Timeline

GridForge should provide an event-oriented visualization:

```
Time       Event
────────────────────────────────────────
0.000 s    Simulation started
0.500 s    Fault applied
0.512 s    Relay R1-50 pickup
0.540 s    Relay R1-51 operate
0.545 s    Trip command issued
0.575 s    Breaker BRK-01 opened
0.700 s    Network stabilized
```

> This becomes particularly valuable for protection and transient studies.

---

## 38. Theme and Visual Design

The UI should provide a consistent engineering visual language. The theme system should control:

- Typography
- Spacing
- Icons
- Panel appearance
- Canvas appearance
- Equipment symbols
- Status indicators
- Selection state
- Alarm state
- Engineering annotations

> The visual system should remain independent of engineering logic.

---

## 39. Dark / Light Engineering Themes

Future UI releases may support:

- Light engineering theme
- Dark engineering theme
- High-contrast theme
- Presentation theme

> Theme changes must affect presentation only. They must never modify engineering state.

---

## 40. Accessibility

Future UI development should consider:

- Keyboard navigation
- Scalable fonts
- High-contrast display
- Accessible controls
- Tooltips
- Meaningful status messages
- Non-color-only engineering indicators
- Screen-reader compatibility where practical

---

## 41. Keyboard Interaction

Engineering workflows should support keyboard shortcuts:

| Shortcut | Action |
|---|---|
| `Ctrl + S` | Save Project |
| `Ctrl + Z` | Undo |
| `Ctrl + Y` | Redo |
| `Delete` | Delete Selection |
| `Esc` | Cancel Tool |
| `F` | Fit View |
| `Space` | Pan / Temporary Navigation |

> Shortcuts should be centrally registered rather than embedded into individual widgets.

---

## 42. Contextual Tools

The UI should provide context-sensitive tools.

**Selected Bus:**
```
Selected Bus
   │
   ├── Add Line
   ├── Add Transformer
   ├── Add Generator
   ├── Add Load
   ├── Inspect
   └── Properties
```

**Selected Relay:**
```
Selected Relay
   │
   ├── View Elements
   ├── Configure
   ├── View Measurements
   ├── Protection Settings
   ├── TCC
   └── Events
```

---

## 43. UI Plugin Architecture

The UI is designed to support plugins, including:

- Tool Plugin
- Renderer Plugin
- Panel Plugin
- Dialog Plugin
- Analysis Visualization Plugin
- Protection Visualization Plugin
- Equipment Symbol Plugin
- Workspace Plugin

> A plugin registry can expose functionality without modifying the main application architecture.

---

## 44. Renderer Registry

Future rendering architecture should allow:

```python
renderer_registry.register(
    equipment_type="TRANSFORMER",
    renderer=TransformerRenderer,
)
```

> This enables specialized equipment visualization without coupling the core model to a particular renderer.

---

## 45. Tool Registry (Expanded)

```python
tool_registry.register(LineTool)
tool_registry.register(BusTool)
tool_registry.register(BreakerTool)
```

> This allows the UI to discover tools dynamically. Plugin tools can therefore become first-class engineering tools.

---

## 46. Application State

UI application state may include:

- Active project
- Active canvas
- Active tool
- Selection
- Zoom
- Pan
- Active mode
- Visible panels
- Active overlays
- Current workspace
- Temporary previews

> This state belongs to the UI/application layer. It must not replace core engineering state.

---

## 47. Core State Synchronization

The UI must remain synchronized with the core.

```
Core State
    │
    ▼
Application State / Events
    │
    ▼
UI Update
```

For a user-initiated modification:

```
User
 │
 ▼
UI Command
 │
 ▼
Controller
 │
 ▼
Core
 │
 ▼
Validation
 │
 ▼
Updated Core State
 │
 ▼
Event / Notification
 │
 ▼
UI Refresh
```

> This prevents stale or divergent graphical state.

---

## 48. No GUI-Only Engineering State

The following must **never** exist only inside UI objects:

- Bus electrical parameters
- Transformer ratings
- Line impedance
- Breaker state
- Generator settings
- Protection settings
- Network topology
- Simulation state
- Analysis results

> The UI may cache derived information for performance, but the cache must not become the authoritative source.

---

## 49. Error Handling

The UI should distinguish:

- User Error
- Engineering Validation Error
- Solver Error
- Simulation Error
- Application Error
- Unexpected Software Error

**Preferred:**
```
Engineering Validation Error:
Line L-102 cannot connect terminals of incompatible voltage levels.
```

**Rather than a generic:**
```
Error
```

---

## 50. Future UI Roadmap

The GridForge UI roadmap is divided into progressive stages.

<details>
<summary><strong>Phase 1 — Core UI Foundation</strong></summary>

- PySide6 architecture
- Centralized Qt abstraction
- Main application
- Main window
- Canvas
- Scene
- View
- Coordinate system
- Basic selection
- Basic navigation
- Core-to-UI synchronization
</details>

<details>
<summary><strong>Phase 2 — Network Editing</strong></summary>

- Bus Tool
- Line Tool
- Transformer tool
- Generator tool
- Load tool
- Breaker tool
- Topology-aware connections
- Snapping
- Terminal handling
- Property editing
- Validation feedback

Target workflow:
```
Create Bus
   ↓
Create Equipment
   ↓
Connect Equipment
   ↓
Validate Network
```
</details>

<details>
<summary><strong>Phase 3 — Engineering Workspace</strong></summary>

- Project Explorer
- Property Inspector
- Engineering toolbars
- Contextual menus
- Equipment dialogs
- Status system
- Command architecture
- Undo/redo
- Project workspace management
</details>

<details>
<summary><strong>Phase 4 — Analysis UI</strong></summary>

- Power-flow configuration
- Short-circuit configuration
- Contingency configuration
- Study execution
- Result tables
- Result overlays
- Engineering plots
- Convergence reporting
- Study history
</details>

<details>
<summary><strong>Phase 5 — Protection UI</strong></summary>

- Relay configuration
- Multifunction relay hierarchy
- Protection-element editor
- Measurement visualization
- Protection status
- Trip-event visualization
- TCC workspace
- Relay coordination workspace
- Fault-event analysis
</details>

<details>
<summary><strong>Phase 6 — Dynamic Simulation UI</strong></summary>

- Simulation configuration
- Simulation control
- Time-step controls
- Event scheduling
- Waveform plots
- Dynamic result visualization
- Event timeline
- Playback
- Pause/resume
- Simulation inspection
</details>

<details>
<summary><strong>Phase 7 — Advanced Visualization</strong></summary>

- Engineering overlays
- Animated network state
- Voltage profiles
- Loading visualization
- Fault propagation visualization
- Protection-event animation
- Dynamic simulation playback
- Configurable dashboards
</details>

<details>
<summary><strong>Phase 8 — Multi-Canvas Digital-Twin Workspace</strong></summary>

```
Grid
 │
 ├── Region
 │
 ├── Substation
 │
 ├── Plant
 │
 └── Feeder
```

Navigation between hierarchical engineering contexts while retaining one authoritative digital twin.
</details>

<details>
<summary><strong>Phase 9 — Plugin Ecosystem</strong></summary>

- UI plugin registry
- Tool registry
- Renderer registry
- Panel registry
- Workspace registry
- Equipment-symbol plugins
- Analysis-visualization plugins
- Protection-visualization plugins

The goal is to allow new engineering capabilities to be integrated without modifying the UI foundation.
</details>

<details>
<summary><strong>Phase 10 — Advanced Engineering Environment</strong></summary>

- Real-time digital-twin visualization
- SCADA visualization
- Online measurement dashboards
- State-estimation visualization
- Event playback
- Automated study dashboards
- Advanced protection analysis
- Real-time simulation monitoring
- Engineering reporting
- Multi-monitor workspaces
- Remote simulation monitoring
</details>

---

## 51. Future UI Architecture

The long-term UI architecture is envisioned as:

```
                         GridForge UI
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
          Workspace         Tools          Panels
              │               │                │
              └───────────────┼────────────────┘
                              │
                              ▼
                     InteractionManager
                              │
                              ▼
                         Controllers
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
           Commands        Services         Events
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                        GridForge Core
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
      Model                Network                Solver
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                         Core Results
                              │
                              ▼
                         Render System
                              │
                              ▼
                       Graphics / Canvas
```

> This architecture permits the UI to grow significantly without turning the application into a monolithic collection of widgets.

---

## 52. UI Architectural Invariants

The following invariants must be preserved.

| # | Invariant | Description |
|---|---|---|
| 1 | **Core owns engineering truth** | The UI is never the authoritative engineering database |
| 2 | **Graphics are representations** | `BusItem`, `LineItem`, and other graphical objects represent core objects |
| 3 | **Rendering does not calculate engineering state** | Renderers visualize results |
| 4 | **Tools do not bypass controllers** | User operations should flow through controlled application services |
| 5 | **GUI does not perform solver calculations** | Numerical calculations belong to the solver layer |
| 6 | **GUI does not own topology** | Topology belongs to the network layer |
| 7 | **GUI does not own persistence** | Project serialization belongs to the persistence layer |
| 8 | **GUI does not own protection logic** | Protection execution belongs to the protection subsystem |
| 9 | **UI state is distinct from engineering state** | Selection, zoom, active tools, and panels are UI state |
| 10 | **Multiple canvases share the same digital twin** | A canvas must never create a second authoritative engineering model |
| 11 | **Plugins use stable contracts** | Plugins must not bypass ownership boundaries |
| 12 | **The core remains headless** | GridForge engineering execution must remain possible without starting the graphical interface |

---

## 53. Performance Strategy

The UI must remain responsive while the core performs expensive calculations. Long-running operations should not block the main UI thread.

```
UI Thread
   │
   ├── Interaction
   ├── Rendering
   └── User Feedback
          │
          ▼
     Task / Worker
          │
          ▼
     GridForge Core
          │
          ▼
        Result
          │
          ▼
      UI Update
```

This is particularly important for:

- Large power-flow studies
- Short-circuit studies
- Contingency analysis
- Dynamic simulation
- Protection coordination
- Large network rendering

---

## 54. Large-Network Visualization

Future GridForge UI versions should support large networks through:

- Level-of-detail rendering
- Object culling
- Viewport-aware rendering
- Incremental updates
- Cached graphical geometry
- Selective overlays
- Asynchronous result processing

> The goal is to prevent the number of graphical objects from becoming a fundamental limitation on network size.

---

## 55. Reporting

Future UI functionality should include engineering report generation. Reports may contain:

- Network summary
- Equipment inventory
- Power-flow results
- Short-circuit results
- Contingency results
- Protection settings
- Coordination results
- Simulation events
- Plots
- Engineering warnings

> Reporting should consume authoritative results from the core and analysis layers.

---

## 56. Import / Export

The UI may eventually provide workflows for:

- Project files
- Engineering data import
- Result export
- Tabular data
- Graphical exports
- Engineering reports

> File handling should remain behind the persistence/project boundary.

---

## 57. Automation and Scripting

A future UI may expose engineering commands to a scripting layer.

```
UI Tool
   │
   ▼
Command
   │
   ├── Interactive Execution
   │
   └── Scripted Execution
          │
          ▼
       GridForge Core
```

> This allows repetitive engineering operations to be automated without duplicating the underlying core functionality.

---

## 58. Future Digital-Twin Interface

The long-term UI may evolve from a design environment into a complete digital-twin workspace.

```
Live Network
     │
     ├── Measurements
     ├── Equipment State
     ├── Alarms
     ├── Protection State
     ├── Simulation State
     ├── Analysis Results
     └── Historical Events
```

> This will allow GridForge to move from static engineering studies toward continuous system observation and decision support.

---

## 59. Final UI Architecture

The intended final relationship is:

```
                         USER
                           │
                           ▼
                    GridForge UI
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Workspace          Tools            Panels
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                 Interaction Manager
                           │
                           ▼
                     Controllers
                           │
                           ▼
                      Commands
                           │
                           ▼
                     GridForge Core
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
    Model                Network              Analysis
      │                    │                    │
      │                    │                    ▼
      │                    │                  Solver
      │                    │                    │
      └────────────────────┼────────────────────┘
                           │
                           ▼
                     Simulation /
                      Protection
                           │
                           ▼
                    Engineering Results
                           │
                           ▼
                     Render System
                           │
                           ▼
                        Canvas
```

---

## 60. Summary

The GridForge V2 UI is designed as a modular engineering application layer rather than as a collection of graphical widgets.

The fundamental separations are:

```
Engineering State   ≠  UI State
Core Model          ≠  Graphical Item
Rendering           ≠  Engineering Calculation
Tool                ≠  Core Service
Canvas              ≠  Network
UI                  ≠  Solver
UI                  ≠  Persistence
```

The resulting architecture provides a foundation for:

- Interactive electrical-network construction
- Topology-aware editing
- Engineering property management
- Power-system study configuration
- Analysis-result visualization
- Multifunction protection visualization
- Dynamic simulation monitoring
- Event-driven engineering workflows
- Multi-canvas digital-twin navigation
- Plugin-based UI expansion
- Automation and scripting
- Future real-time digital-twin applications

---

## 61. Current Status

The GridForge UI architecture is being developed around the following foundational concepts:

```
PySide6
   │
   ▼
Qt Abstraction
   │
   ▼
Application
   │
   ├── Workspace
   ├── Canvas
   ├── Tools
   ├── Interaction
   ├── Rendering
   ├── Controllers
   └── Panels
           │
           ▼
      GridForge Core
```

> The UI foundation should be finalized incrementally, with each subsystem audited, validated, and frozen before dependent functionality is built on top of it.

**The GridForge UI exists to make the engineering core understandable, editable, controllable, and visually observable — never to replace the engineering core itself.**

---

<p align="center"><em>ui/ — a window onto engineering truth, never its owner.</em></p>
