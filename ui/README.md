GridForge V2 — UI Architecture

Status: Frozen Architecture Contract
Scope: ui/ and all UI-facing integration points
Framework: PySide6
Application: GridForge V2

1. Purpose

The GridForge V2 UI is the presentation, interaction, visualization, workspace, and user-intent boundary of the GridForge engineering platform.

It provides:

electrical SLD editing and visualization;
equipment placement and editing;
topology interaction;
engineering property inspection;
study and result presentation;
project navigation;
tools and interaction modes;
dockable engineering panels;
workspace management;
plugin-based UI extension;
command dispatch;
selection and snapping;
rendering and visual feedback.

The UI does not own engineering truth.

The authoritative engineering state remains outside the UI in the Application/Core architecture.

The fundamental principle is:

UI asks. Application orchestrates. Core decides. Core reports. UI projects and displays.

2. Prime Directive
UI-001 — The UI is never an alternate Core

The UI must never become the authoritative owner of:

buses;
terminals;
branches;
equipment;
electrical parameters;
topology;
connectivity;
protection settings;
study definitions;
solver state;
study results;
engineering validation;
project persistence;
engineering calculations.

The authoritative source is:

Application
    ↓
Core
 ├── Model
 ├── Network
 ├── Topology
 ├── Studies
 ├── Results
 └── Engineering Rules

The UI owns only:

Presentation State
Interaction State
Viewport State
Workspace State
Transient UI State
3. Canonical UI ↔ Core Architecture

The complete interaction architecture is:

                         USER
                           │
                  mouse / keyboard
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                         UI                           │
│                                                      │
│ MainWindow                                           │
│ Shell / Workspace                                    │
│ Canvas                                               │
│ Panels                                               │
│ Toolbar                                              │
│ Tools                                                │
│ Selection                                            │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
                       │ User Intent
                       ▼
              ┌──────────────────┐
              │ Command Boundary │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Application   │
              │                  │
              │ Commands         │
              │ Handlers         │
              │ Services         │
              │ Lifecycle        │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │       CORE       │
              │                  │
              │ Model            │
              │ Network          │
              │ Topology         │
              │ Studies          │
              │ Results          │
              └────────┬─────────┘
                       │
                    Events
                       │
                       ▼
              ┌──────────────────┐
              │    Projection    │
              │     / Adapter    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │    View State    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   RenderSystem   │
              │    Renderers     │
              │   GraphicsItems  │
              └────────┬─────────┘
                       │
                       ▼
                     CANVAS

This is the canonical GridForge V2 UI execution model.

4. Golden Write Contract

Every persistent user action follows:

USER
 ↓
Qt Event
 ↓
Widget / Canvas
 ↓
Tool / Controller
 ↓
User Intent
 ↓
Command
 ↓
Command Boundary
 ↓
Application Handler / Service
 ↓
Core
 ↓
Authoritative State Change

The UI must never use:

UI
 ↓
Core object
 ↓
attribute mutation

For example, this is prohibited:

bus.voltage = 132

from a widget.

Correct:

PropertyEditor
 ↓
ChangeParameterCommand
 ↓
Application
 ↓
Core
 ↓
EquipmentChanged
 ↓
Projection
 ↓
PropertyEditor
5. Golden Read Contract

UI state is derived from authoritative state:

Core
 ↓
Application / Projection
 ↓
ViewState
 ↓
UI Component
 ↓
Renderer
 ↓
Screen

UI components must not reconstruct engineering truth by inspecting arbitrary Core internals.

6. Golden Event Contract

Events communicate authoritative state changes.

Core / Application
        ↓
      Event
        ↓
 UI Event Adapter
        ↓
    Projection
        ↓
    View State
        ↓
 UI Components

Examples:

EquipmentCreated
EquipmentChanged
EquipmentRemoved
TopologyChanged
ProjectLoaded
ProjectSaved
StudyStarted
StudyProgressed
StudyCompleted
StudyFailed
StudyCancelled

A UI action succeeding is determined by authoritative application/Core state—not by the fact that the user clicked a button.

7. Commands vs Events

This distinction is mandatory.

Command

A command means:

"I want this operation to happen."

Examples:

CreateBusCommand
CreateLineCommand
DeleteEquipmentCommand
MoveEquipmentCommand
MoveSLDElementCommand
ConnectTerminalsCommand
DisconnectTerminalsCommand
ChangeParameterCommand
RenameEquipmentCommand
RotateEquipmentCommand
RunStudyCommand
SaveProjectCommand
OpenProjectCommand

Direction:

UI → Application
Event

An event means:

"This authoritative state change happened."

Examples:

BusCreated
EquipmentChanged
EquipmentRemoved
TopologyChanged
ProjectLoaded
StudyCompleted

Direction:

Application/Core → UI

Commands and events must never be treated as interchangeable.

8. Five UI State Domains

GridForge V2 explicitly separates five kinds of state.

8.1 Domain State

Owned by Core/Application:

Network
Equipment
Terminals
Topology
Electrical parameters
Protection
Studies
Results
Engineering rules
8.2 Application State

Owned by the Application layer:

Current project
Project lifecycle
Active study
Command execution
Command history
Execution state
Application services
8.3 Presentation State

UI/application presentation state:

SLD position
SLD rotation
Symbol geometry
Label placement
Routing geometry
Visibility
Presentation metadata

Presentation state is persisted when required but does not become electrical truth.

8.4 Interaction State

Owned by UI:

Active tool
Selection
Dragging
Connecting
Placing
Editing
Previewing
Measuring
8.5 Viewport State

Owned by UI:

Zoom
Pan
Camera
Grid visibility
Grid spacing
Viewport size
9. SLD Contract

The SLD is not the electrical model.

It is:

An editable visual projection of the authoritative electrical model plus presentation/layout state.

Therefore:

Electrical Truth
      ↓
     Core

Presentation/Layout
      ↓
 UI/Application Presentation State

Screen
      ↓
    Canvas

The SLD may be saved and restored.

Saving SLD layout does not make the SLD authoritative over electrical topology.

10. UI Object Identity

Every UI representation corresponding to a Core object must use the Core object's stable identity.

Example:

Core:

equipment_id = "BUS-8F3A..."

UI:

BusItem.domain_id = "BUS-8F3A..."

Never use as authoritative identity:

id(core_object)
Python object identity
Qt object identity
list index
scene index
graphics-item index
display name

Python/Qt object identity may be used internally as an optimization, but never as the cross-layer architectural identity.

Stable identity is required for:

event routing;
projection;
persistence;
undo/redo;
reload;
multi-canvas synchronization;
future collaboration;
incremental rendering.
11. UI Object ≠ Domain Object

The following distinction is mandatory:

Core Bus
     │
     ▼
BusViewState
     │
     ▼
BusItem

Therefore:

BusItem ≠ Bus
LineItem ≠ Line
TransformerItem ≠ Transformer
BreakerItem ≠ Breaker

A GraphicsItem may contain:

domain_id
geometry
visual_state
interaction_state

It must not become a shadow engineering model.

12. Projection Layer

The projection layer explicitly translates authoritative application/Core state into UI-readable state.

Conceptually:

Core Object
     ↓
Projection Adapter
     ↓
View State
     ↓
Renderer
     ↓
GraphicsItem

Example:

EquipmentViewState(
    id="TR-001",
    equipment_type="transformer",
    name="TR-01",
    position=world_position,
    rotation=rotation,
    status=status,
)

The renderer consumes ViewState.

It does not interrogate arbitrary Core internals.

13. MainWindow Contract

MainWindow is the UI composition root.

It is intentionally thin.

Responsibilities:

create the top-level Qt window;
establish the application UI lifetime;
receive application/UI context;
receive PluginContext;
initialize shell composition;
connect top-level UI services;
manage menus/toolbars/docks through composition;
provide UI context;
initiate orderly shutdown.

It must not:

network.add_bus(...)
bus.voltage = ...
solver.solve(...)

It must not:

implement engineering calculations;
implement topology;
create concrete tools directly;
create renderer implementations directly;
mutate Core;
become the application brain;
become a second Controller.
14. Controller Contract

The Controller is the UI/Application coordination boundary.

It may coordinate:

commands;
application actions;
project operations;
UI state;
tool requests;
selection state;
application services.

It must not implement:

electrical calculations;
topology algorithms;
rendering;
snapping algorithms;
coordinate transformations;
concrete tool behavior;
Core business rules.

The Controller is a facade/coordination boundary, not another Core.

15. Interaction Architecture

The interaction system owns human input processing.

Canonical flow:

Qt Input
   ↓
InteractionManager
   ↓
Active Tool
   ↓
Intent
   ↓
Command

The Interaction layer may manage:

mouse input;
keyboard input;
gestures;
tool activation;
tool sessions;
interaction modes;
transient previews;
selection interaction;
snapping;
coordinate conversion.

It may not directly mutate Core.

16. Tool Architecture

The tool architecture is extensible.

Controller
     ↓
InteractionManager
     ↓
ToolManager
     ↓
Tool Registry
     ↓
Tool Instance

Responsibilities are separated.

InteractionManager

Owns input routing.

ToolManager

Owns tool lifecycle.

Tool Registry

Owns registration/discovery.

Tool

Owns interaction behavior.

Controller

Requests/coordinates tool activation.

The ToolManager must not become the registry.

The registry must not become the lifecycle manager.

17. Tool Contract

Tools may:

consume mouse events;
consume keyboard events;
create previews;
query projection state;
query selection;
use snapping;
convert coordinates;
create commands;
manipulate viewport state;
manage transient interaction.

Tools may not:

network.add_bus()
equipment.parameter = value
topology.connect(...)
solver.solve(...)

Correct:

mouseRelease
    ↓
BusTool
    ↓
CreateBusCommand
    ↓
Application
18. Preview Contract

Preview objects are explicitly non-authoritative.

Examples:

BusPreview
LinePreview
TransformerPreview
ConnectionPreview
SelectionRectangle
SnapIndicator
MeasurementPreview

Preview state may contain:

cursor position
temporary geometry
orientation
snap candidate
routing preview
visual feedback

A preview must never be inserted into the authoritative network.

Only a committed command creates persistent state.

19. Coordinate System Contract

The UI owns coordinate transformations.

Conceptual spaces:

Screen
   ↓
Scene / Viewport
   ↓
World

Example:

Mouse Position
      ↓
Screen → Scene
      ↓
Scene → World
      ↓
WorldPosition
      ↓
Command

Core must never depend on:

QPointF
QTransform
QGraphicsScene
QGraphicsView
QMouseEvent

The domain receives domain-neutral values.

20. Snap Contract

Snapping is UI interaction logic.

Possible snap types:

Grid
Terminal
Bus
Endpoint
Alignment
Orthogonal
Angle
Equipment Anchor

Snap determines a candidate.

Core determines whether the resulting operation is legal.

Example:

SnapSystem
     ↓
candidate terminal T-001
     ↓
ConnectTerminalsCommand
     ↓
Core validation
     ↓
Topology change

The SnapSystem must never establish authoritative topology.

21. Canvas Contract

The Canvas is:

An editing and visualization surface, not an electrical model.

The Canvas owns:

viewport;
camera;
zoom;
pan;
grid presentation;
visual items;
rendering;
interaction;
previews;
selection presentation.

It does not own:

network topology;
equipment ownership;
terminal connectivity;
engineering validation;
study state;
solver state.
22. CanvasPlugin Contract

CanvasPlugin is a composition plugin.

It may establish:

Canvas
 ├── Scene
 ├── View
 ├── RenderSystem
 ├── InteractionManager
 ├── ToolManager
 └── PreviewLayer

It must not:

own Core;
create a second network;
own topology;
implement engineering calculations;
bypass commands;
become ToolManager;
become InteractionManager;
become RenderSystem;
own project state.
23. Rendering Contract

Rendering is strictly presentation-oriented.

Core/Application State
        ↓
Projection
        ↓
RenderSystem
        ↓
RendererRegistry
        ↓
Renderer
        ↓
GraphicsItem
        ↓
QGraphicsScene

Renderers may:

draw;
update geometry;
choose visual representation;
display status;
display warnings;
display selection;
display result overlays.

Renderers may not:

modify Core;
calculate engineering values;
validate topology;
create equipment;
run studies.
24. Renderer Identity

The RenderSystem maps visual representations through stable domain IDs.

domain_id
    ↓
RenderSystem
    ↓
GraphicsItem

The mapping must remain stable across:

reload;
project reconstruction;
Core event updates;
multiple canvases;
undo/redo;
persistence.

Python object identity is not the authoritative mapping.

25. Graphics Item Contract

A GraphicsItem is a UI projection.

It may contain:

domain_id
geometry
visual state
interaction state

It may emit user-intent signals to the interaction/controller layer.

It must not directly mutate Core.

Bad:

BusItem
   ↓
core.bus.voltage = ...

Correct:

BusItem
   ↓
interaction/controller
   ↓
ChangeParameterCommand
26. Selection Contract

Selection is UI/application state.

Canonical model:

User
 ↓
SelectionManager
 ↓
selected_ids
 ↓
Projection
 ↓
Graphics selection

Graphics selection is a visual projection.

It is not the engineering model.

Selection must not:

mutate Core;
create equipment;
change topology;
modify electrical parameters.
27. Panel Architecture

Panels are specialized UI surfaces.

Examples:

ToolPalette
ProjectExplorer
PropertyEditor
EquipmentConfigurator
ObjectInspector
CommandCenter
DiagnosticsPanel
AnalysisResults
ProtectionEditor
Settings
Navigator

Panels may:

display projected state;
accept user input;
dispatch commands;
display diagnostics;
subscribe to events.

Panels may not directly mutate Core.

28. Property Editor Contract

Reading:

Selection
 ↓
Projection
 ↓
PropertyEditor

Writing:

PropertyEditor
 ↓
ChangeParameterCommand
 ↓
Application
 ↓
Core
 ↓
EquipmentChanged
 ↓
Projection
 ↓
PropertyEditor

Never:

QLineEdit.textChanged
        ↓
Core object mutation
29. Workspace Contract

The workspace must support:

docking;
undocking;
resizing;
collapsing;
hiding;
restoring;
layout persistence;
multiple panel instances where appropriate;
workspace profiles;
future multi-canvas arrangements.

Workspace state is UI/application presentation state.

It must not redefine engineering topology.

30. Multi-Canvas Contract

Multiple canvases may represent:

same network
different network scope
different hierarchy level
different SLD
different study view

unless explicitly defined as separate project/domain contexts.

Correct:

                 Core Network
                /     |      \
               /      |       \
          Canvas A Canvas B Canvas C

Incorrect:

Canvas A → Network A
Canvas B → Network B

when they are intended to represent the same project/network.

31. Canvas Synchronization

Core → UI:

Core Change
    ↓
Event
    ↓
Projection
    ↓
Affected Canvas
    ↓
Renderer

UI → Core:

User Intent
    ↓
Command
    ↓
Application
    ↓
Core Change
    ↓
Event
    ↓
Projection
    ↓
Canvas

This closed loop prevents stale UI state.

32. Persistent Layout Changes

Persistent layout changes must cross an explicit command boundary.

Example:

User drags Bus
       ↓
temporary visual movement
       ↓
release
       ↓
MoveSLDElementCommand
       ↓
Presentation/Layout State
       ↓
Event
       ↓
Projection
       ↓
Canvas

Purely transient changes may remain local to the UI.

Examples:

hover
rubber-band
cursor preview
selection rectangle
temporary snap indicator
33. Equipment Creation

Canonical workflow:

Equipment Palette
       ↓
Tool Selection
       ↓
Equipment Tool
       ↓
Preview
       ↓
Canvas Placement
       ↓
User Commit
       ↓
CreateEquipmentCommand
       ↓
Application Handler
       ↓
Core
       ↓
EquipmentCreated
       ↓
Projection
       ↓
EquipmentViewState
       ↓
Renderer
       ↓
EquipmentItem

The EquipmentItem never creates authoritative equipment.

34. Connection Workflow

Connection interaction is terminal-oriented.

LineTool
   ↓
SnapSystem
   ↓
Candidate Terminal
   ↓
User Commit
   ↓
ConnectTerminalsCommand
   ↓
Application
   ↓
Core
   ↓
Topology Validation

Core determines whether the connection is legal.

The UI determines only the user's intended candidates.

35. Validation Contract

Two validation categories exist.

UI validation

Examples:

empty field
malformed text
invalid dialog input
unsupported UI selection

UI may handle these.

Domain validation

Examples:

terminal already occupied
illegal topology
invalid equipment connection
invalid electrical parameter
invalid study configuration

Domain validation belongs to Core/Application.

The UI displays the result.

36. Error Contract

Raw Core exceptions must not be pushed directly into widgets.

Canonical path:

Core
 ↓
Application Error
 ↓
Command Result
 ↓
UI Notification
 ↓
User

The UI determines presentation:

Toast
Dialog
Status Bar
Diagnostic Panel
Badge
Log
Inline Error

The Core determines validity.

37. Notification Contract

Notification presentation is UI-owned.

Notification types include:

Information
Warning
Error
Progress
Success

Structured application status is transformed into appropriate UI presentation.

38. Undo / Redo

Undo/redo belongs to the command/application architecture.

Correct:

CommandManager
 ├── execute
 ├── undo
 ├── redo
 └── history

Not:

GraphicsScene.undo()

UI actions and non-UI application actions should be capable of sharing the same command transaction model.

39. Long-Running Operations

Expensive operations must not block the UI thread.

Examples:

project loading
large network rendering
study execution
result calculation
large imports
large exports

Canonical flow:

UI
 ↓
Command
 ↓
Application Service
 ↓
Worker / Execution Architecture
 ↓
Core / Study / Solver

UI receives:

Started
Progress
Completed
Failed
Cancelled

Qt widgets must only be updated from the UI thread.

40. Study UI

The UI does not own studies or solvers.

Study request:

StudyPanel
 ↓
RunStudyCommand
 ↓
Application
 ↓
Study/Solver Service
 ↓
Execution

The UI displays:

Study Definition
Study Status
Progress
Warnings
Diagnostics
Results

It never calls solver internals directly.

41. Result Visualization

Results are authoritative application/Core data.

Example:

Load Flow Result
 ├── bus voltage
 ├── voltage angle
 ├── branch loading
 └── losses

The UI may display:

Voltage labels
Loading overlays
Result tables
Charts
Warning badges

Visual color or geometry is never itself the engineering result.

42. Project/File Contract

The UI requests project operations through application services.

Examples:

NewProjectCommand
OpenProjectCommand
SaveProjectCommand
SaveAsProjectCommand
CloseProjectCommand
ImportCommand
ExportCommand

The UI must not implement project serialization.

Project persistence remains outside widgets and graphics items.

43. Qt Boundary

All UI Qt dependencies must pass through:

ui.core.qt

Preferred:

from ui.core.qt import QWidget, QObject

Not:

from PySide6.QtWidgets import QWidget

throughout arbitrary UI modules.

The Qt compatibility/binding boundary is the only permitted direct binding boundary.

Core must never depend on PySide6.

44. Plugin Architecture

Plugins extend controlled UI extension points.

Examples:

Canvas
Panels
Toolbar
Status
Equipment UI
Studies
Renderers
Tools
Commands
Importers
Exporters

Every plugin receives a controlled PluginContext.

Conceptually:

PluginContext(
    application=...,
    command_manager=...,
    selection_manager=...,
    tool_manager=...,
    panel_registry=...,
    renderer_registry=...,
    notification_service=...,
    project_context=...,
    canvas_context=...,
)

The context is a dependency boundary.

Plugins must not receive unrestricted access to Core internals.

45. Plugin Lifecycle

Lifecycle ownership:

PluginManager
    ↓
discover
    ↓
resolve dependencies
    ↓
initialize
    ↓
activate
    ↓
deactivate
    ↓
shutdown

MainWindow and ShellPlugin must not duplicate plugin lifecycle management.

46. Registry Contract

Registries provide controlled extensibility.

Examples:

PluginRegistry
ToolRegistry
PanelRegistry
RendererRegistry
CommandRegistry
ControllerRegistry

Registries provide:

registration;
lookup;
capability discovery;
conflict detection;
controlled lifecycle integration.

They must not become arbitrary global application-state stores.

47. Dependency Direction

The preferred direction is:

Qt
 ↓
UI Platform
 ↓
UI Components
 ↓
Controllers / Interaction
 ↓
Application Boundary
 ↓
Core

Rendering:

Core/Application
      ↓
Projection
      ↓
UI View State
      ↓
RenderSystem
      ↓
Renderer
      ↓
GraphicsItem

Forbidden:

Core → PySide6
Core → QGraphicsItem
Core → MainWindow
Core → Renderer
Core → UI Plugin

Renderer → Core mutation
GraphicsItem → Core mutation
Tool → uncontrolled Core mutation
PropertyEditor → Core mutation
MainWindow → Solver
ShellPlugin → Solver
48. Threading Contract

Qt objects remain on the UI thread.

Background execution:

Worker
  ↓
Application Event
  ↓
UI Thread
  ↓
Widget Update

Never update Qt widgets from solver or worker threads.

49. Lifecycle Contract

UI components must have explicit lifecycle semantics:

create
 ↓
initialize
 ↓
attach
 ↓
activate
 ↓
update
 ↓
deactivate
 ↓
detach
 ↓
dispose

This applies particularly to:

plugins
tools
panels
renderers
canvas
project contexts
workspace components

Critical application state must not be hidden inside uncontrolled global singletons.

50. Human Interaction Edge Cases

Every interactive tool must explicitly define behavior for:

click without selection;
click outside canvas;
double click;
right click;
middle click;
mouse press without release;
release outside canvas;
drag cancellation;
Esc;
Delete;
Backspace;
keyboard focus loss;
tool switching during interaction;
panel focus changes;
selection changes during interaction;
project close during interaction;
project reload during interaction;
command rejection;
Core validation failure;
Core event arriving during interaction;
object deletion during drag;
object deletion during connection;
stale domain ID;
missing projection;
missing renderer;
missing plugin;
missing tool;
invalid snap candidate;
ambiguous snap candidate;
disconnected terminal;
occupied terminal;
cancelled command;
failed command;
undo during transient interaction;
redo during transient interaction;
background study completion during editing;
application shutdown during a tool session.

The required rule is:

Transient interaction may be cancelled safely at any time without creating authoritative Core state.

51. Tool Cancellation Contract

Every stateful tool must support cancellation.

Examples:

Placing
Connecting
Dragging
Editing
Measuring
Routing

Cancellation:

Esc
 ↓
Tool.cancel()
 ↓
Preview discarded
 ↓
Transient interaction cleared
 ↓
No Core mutation

If a command has already been committed, cancellation is no longer a preview operation; undo must use the command architecture.

52. Focus Contract

Keyboard focus must never implicitly mutate engineering state.

Examples:

Canvas focus
Panel focus
Property editor focus
Search focus
Command center focus

Changing focus must not:

change topology;
commit partial engineering edits;
activate arbitrary tools;
create equipment.

Explicit commit/cancel semantics must be defined for editable fields.

53. Stale Projection Contract

A UI projection can become stale.

The UI must not silently assume it remains valid.

If:

domain_id

no longer exists:

Projection
 ↓
missing object
 ↓
remove/invalidated UI representation
 ↓
diagnostic if necessary

The UI must not recreate the Core object itself.

54. Missing Renderer Contract

If a Core object exists but no renderer is registered:

Core object exists
       ↓
Projection exists
       ↓
Renderer unavailable
       ↓
Fallback / diagnostic representation

The absence of a renderer must never imply absence of the engineering object.

55. Plugin Failure Contract

If a plugin fails:

the failure must be isolated;
plugin lifecycle state must be recorded;
the UI must report diagnostics;
unrelated plugins must remain operational where possible;
Core state must remain unaffected;
partial UI registration must be cleaned up.

A failed UI plugin must never corrupt engineering state.

56. Multi-Canvas Synchronization

When the same domain object appears on multiple canvases:

                 Core Object
                 domain_id
                /    |     \
               /     |      \
          Canvas A Canvas B Canvas C

Each canvas owns its own visual projection.

No canvas owns the Core object.

A Core change must update every affected projection.

57. Performance Contract

The UI must remain responsive during:

large SLD rendering;
zooming;
panning;
selection;
project loading;
large project reconstruction;
topology changes;
study execution;
result visualization.

UI thread:

interaction
rendering
widget updates

Worker/execution architecture:

expensive computation
solver execution
large I/O
analysis
58. Testing Contract

UI infrastructure must be testable independently.

Unit-test:

Controller
Command wiring
InteractionManager
ToolManager
Tools
SelectionManager
SnapSystem
CoordinateSystem
Projection
RenderSystem
Renderer
Navigation
Workspace
Plugin lifecycle

Integration-test:

UI Intent
 ↓
Command
 ↓
Application
 ↓
Core
 ↓
Event
 ↓
Projection
 ↓
UI
59. Headless Core Requirement

Core tests must remain runnable without:

QApplication
MainWindow
Canvas
PySide6 widgets

Example:

pytest tests/core

UI tests should be able to substitute mocked Application/Core boundaries.

60. Equipment Extension Contract

Adding a new equipment type should not require repeatedly modifying central UI files.

Conceptually:

Equipment Plugin
 ├── equipment registration
 ├── projection
 ├── renderer
 ├── graphics item
 ├── tool
 ├── commands
 └── UI configuration

The extension must use the established registries and command/projection boundaries.

61. UI Architecture Tree

The canonical UI responsibility structure is:

ui/
│
├── core/
│   ├── controller.py
│   ├── command_manager.py
│   ├── selection_manager.py
│   ├── snap_system.py
│   ├── projection/
│   └── qt.py
│
├── controllers/
│   ├── canvas_controller.py
│   ├── command_controller.py
│   ├── interaction_controller.py
│   ├── navigation_controller.py
│   ├── selection_controller.py
│   └── tool_controller.py
│
├── canvas/
│   ├── coordinate_system.py
│   ├── graphics_view.py
│   ├── grid_scene.py
│   ├── grid_system.py
│   ├── interaction_manager.py
│   ├── preview_layer.py
│   └── render_system.py
│
├── tools/
│   ├── base/
│   ├── manager/
│   ├── registry/
│   └── implementations/
│
├── items/
│
├── renderers/
│
├── panels/
│
├── plugins/
│
├── workspace/
│
├── styling/
│
├── equipment/
│
├── connections/
│
├── topology/
│
├── sld/
│
├── model/
│
├── main_window.py
│
└── README.md

Physical directory organization may evolve, but the architectural responsibilities must remain stable.

62. Canonical Equipment Creation Flow
                    USER
                      │
                      ▼
               Equipment Palette
                      │
                      ▼
                   Tool
                      │
                      ▼
                 Preview
                      │
                 placement
                      │
                      ▼
                  Intent
                      │
                      ▼
             CreateEquipmentCommand
                      │
                      ▼
              Command Boundary
                      │
                      ▼
                Application
                      │
                      ▼
                    Core
                      │
                      ▼
               EquipmentCreated
                      │
                      ▼
                 Projection
                      │
                      ▼
              EquipmentViewState
                      │
                      ▼
                RenderSystem
                      │
                      ▼
                EquipmentItem
                      │
                      ▼
                    SCREEN
63. Canonical Connection Flow
USER
 ↓
LineTool
 ↓
CoordinateSystem
 ↓
SnapSystem
 ↓
Terminal Candidate
 ↓
ConnectTerminalsCommand
 ↓
Application
 ↓
Core
 ↓
Topology Validation
 ↓
TopologyChanged
 ↓
Projection
 ↓
RenderSystem
 ↓
LineItem
64. Canonical Study Flow
USER
 ↓
Study Panel
 ↓
RunStudyCommand
 ↓
Application
 ↓
Study/Solver Service
 ↓
Execution
 ↓
Study Events
 ↓
Results
 ↓
Projection
 ↓
Result UI

The Canvas and panels never execute numerical solver internals.

65. Canonical Error Flow
USER
 ↓
Intent
 ↓
Command
 ↓
Application
 ↓
Core Validation
 ↓
Rejected
 ↓
Structured Error
 ↓
UI Notification
 ↓
User

The UI may offer a correction, but the correction must again become an explicit user intent and command.

66. What This Architecture Prevents
GUI becoming the database

Prevented by authoritative Core state.

BusItem becoming a second Bus

Prevented by projection identity.

Canvas owning topology

Prevented by the command boundary.

Tool directly modifying Core

Prevented by interaction architecture.

MainWindow becoming a God Object

Prevented by composition boundaries.

Plugin bypassing architecture

Prevented by PluginContext and registries.

Study logic entering GUI

Prevented by Application/Solver boundaries.

UI calculating engineering results

Prevented by result projection.

Multiple canvases creating conflicting networks

Prevented by shared Core authority.

Layout changes disappearing

Prevented by explicit Presentation State.

Renderer becoming engineering logic

Prevented by renderer contract.

Selection becoming domain state

Prevented by SelectionManager contract.

Preview becoming engineering state

Prevented by Preview Layer contract.

67. Final Architecture
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │ UI SHELL    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       Panels           Canvas           Toolbar
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                ┌────────────────────┐
                │ INTERACTION LAYER  │
                │                    │
                │ Tools              │
                │ Selection          │
                │ Snap               │
                │ Coordinates        │
                │ Interaction        │
                └─────────┬──────────┘
                          │
                        Intent
                          │
                          ▼
                ┌────────────────────┐
                │ COMMAND BOUNDARY   │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ APPLICATION        │
                │ Commands           │
                │ Handlers           │
                │ Services           │
                │ Lifecycle          │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ CORE               │
                │                    │
                │ Model              │
                │ Network            │
                │ Topology           │
                │ Studies            │
                │ Results            │
                └─────────┬──────────┘
                          │
                        Events
                          │
                          ▼
                ┌────────────────────┐
                │ PROJECTION         │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ UI VIEW STATE      │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ RENDER SYSTEM      │
                │                    │
                │ Registry           │
                │ Renderers          │
                │ Graphics Items     │
                └─────────┬──────────┘
                          │
                          ▼
                        SCREEN
68. Non-Negotiable Rules

The following rules are frozen:

UI never owns engineering truth.

UI never directly mutates Core.

Persistent user actions cross the command boundary.

Core/Application state changes return through events.

UI representations use stable domain IDs.

Graphics items are projections, not domain models.

SLD is not the electrical model.

Presentation state is distinct from engineering state.

Preview state is never authoritative.

Selection is UI/application state.

Snapping identifies candidates; Core validates topology.

Renderers never perform engineering calculations.

Tools never directly mutate Core.

MainWindow is a composition root, not an application brain.

PluginManager owns plugin lifecycle.

ToolManager owns tool lifecycle.

ToolRegistry owns tool registration/discovery.

Projection is an explicit architectural layer.

Qt types never cross into Core.

Core must remain headless.

Long-running operations never block the UI thread.

Undo/redo operates at the command/application level.

Multiple canvases never create duplicate Core networks.
69. The One Rule Above All Others

GridForge V2 UI must never become a second implementation of the Core.

The UI is:

Presentation
+
Interaction
+
Projection
+
Workspace
+
Command Boundary
+
UI Platform

The Application layer is:

Commands
+
Handlers
+
Services
+
Lifecycle
+
Execution Orchestration

The Core is:

Engineering Truth
+
Topology
+
Engineering Rules
+
Studies
+
Results

Therefore:

                 UI
                  │
              asks / displays
                  │
                  ▼
            APPLICATION
                  │
             orchestrates
                  │
                  ▼
                CORE
                  │
               decides
                  │
                  ▼
               EVENTS
                  │
                  ▼
                 UI

This is the frozen GridForge V2 UI ↔ Core contract.

My reconciliation verdict

The current repository README is already strong, but I would replace its current wording with the above rather than simply append to it. The live repository currently describes the UI tree, plugins, controllers, rendering, tools, panels, command architecture, solver integration, snap/preview systems, and UI/Core separation, but several important pieces are still described as future, planned, or to be decided.

The biggest changes I intentionally made are:

Projection is now explicit, not merely implied inside rendering.
Stable domain IDs are mandatory.
ToolManager / ToolRegistry / InteractionManager responsibilities are explicitly separated.
Command boundary is explicit.
SLD presentation state is explicitly separated from engineering truth.
Human-interaction cancellation and failure behavior is part of the contract.
Stale projections, missing renderers, plugin failure, focus, cancellation, and multi-canvas behavior are covered.
The Qt boundary is explicit.
The UI is explicitly forbidden from becoming a second Core.
