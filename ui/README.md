# GridForge V2 — UI Architecture

## 1. Purpose

The GridForge V2 UI is an engineering-oriented graphical user interface for
power-system modelling, simulation, analysis, protection, and visualization.

The UI combines:

- ETAP-style electrical engineering workflows;
- Blender-style dockable and configurable workspace organization;
- CAD-style canvas interaction;
- plugin-based UI composition;
- controller-based application coordination;
- renderer-based visual presentation;
- Core-authoritative engineering/domain state.

The UI is not the owner of the electrical model.

The UI is a presentation, interaction, composition, and application-coordination
layer above the authoritative GridForge Core.

The fundamental architectural principle is:

    UI requests actions.
    Controllers coordinate actions.
    Commands modify application state.
    Core remains authoritative.
    Renderers visualize state.
    UI never becomes the source of engineering truth.


---

# 2. Architectural Objectives

GridForge V2 UI must provide:

1. A central electrical canvas.
2. SLD-style electrical drawing.
3. Interactive equipment placement.
4. Constraint-driven electrical connections.
5. Project navigation.
6. Object/property inspection.
7. Equipment configuration.
8. Tool-based interaction.
9. Dockable engineering panels.
10. Command and diagnostic output.
11. Solver and analysis result presentation.
12. File/project management.
13. Undo/redo.
14. Plugin extensibility.
15. Workspace customization.
16. Multiple engineering views.
17. Future multi-canvas/substation navigation.
18. Separation between UI state and Core state.
19. Testable non-visual controllers.
20. Strict ownership boundaries.


---

# 3. Core Architectural Rule

The UI must never become a second implementation of the Core.

The authoritative relationship is:

    User
      |
      v
    UI
      |
      v
    Controller / Command
      |
      v
    Application Services
      |
      v
    GridForge Core
      |
      v
    Engineering State

Rendering works in the opposite direction:

    GridForge Core
          |
          v
    Application / UI State
          |
          v
    Render System
          |
          v
    Renderer
          |
          v
    Graphics Item
          |
          v
    Canvas


The UI may cache presentation information, but it must not become the
authoritative owner of electrical/network state.


---

# 4. Top-Level Application Architecture

The intended application structure is:

    Application
        |
        +-- MainWindow
        |
        +-- Controller
        |
        +-- PluginManager
        |
        +-- Application Services
        |
        +-- GridForge Core
        |
        +-- CLI


The major boundaries are:

    MainWindow
        -> top-level Qt composition

    PluginManager
        -> plugin lifecycle and dependency ordering

    ShellPlugin
        -> final UI composition

    PluginContext
        -> dependency carrier

    Controller
        -> UI/application coordination

    Canvas
        -> graphical engineering workspace

    Tools
        -> user interaction

    RenderSystem
        -> rendering orchestration

    Panels
        -> engineering UI surfaces

    Application Services
        -> project, file, command, solver, analysis, etc.

    Core
        -> authoritative engineering model and computation

    CLI
        -> non-GUI application/Core entry point


---

# 5. MainWindow

File:

    ui/main_window.py

MainWindow is the top-level Qt composition boundary.

It is intentionally thin.

MainWindow responsibilities:

- create the top-level Qt window;
- retain the application Controller;
- create the neutral root widget;
- create or receive PluginContext;
- create or receive PluginManager;
- configure plugin contexts;
- start plugin composition;
- shut down plugin composition;
- provide top-level application access.

MainWindow must NOT:

- create concrete tools;
- create renderers;
- create canvas graphics items;
- implement canvas interaction;
- perform electrical calculations;
- manipulate Core directly;
- construct every dock widget;
- implement plugin lifecycle itself;
- become a second Controller;
- contain application business logic.

The correct flow is:

    main.py
       |
       v
    MainWindow
       |
       v
    PluginManager
       |
       v
    Plugins
       |
       v
    Shell / Workspace
       |
       v
    Visible UI


---

# 6. Plugin Architecture

Directory:

    ui/plugins/

Current infrastructure includes:

    canvas_plugin.py
    panels_plugin.py
    plugin_context.py
    plugin_contract.py
    plugin_events.py
    plugin_loader.py
    plugin_manager.py
    plugin_registry.py
    plugin_state.py
    shell_plugin.py
    status_plugin.py
    toolbar_plugin.py


## 6.1 PluginManager

PluginManager owns:

- plugin discovery/loading;
- dependency resolution;
- initialization ordering;
- shutdown ordering;
- lifecycle state.

PluginManager must remain the lifecycle authority.

MainWindow must not duplicate this responsibility.


## 6.2 PluginContext

PluginContext is an immutable dependency carrier.

It carries references to already-created services.

It does not:

- construct services;
- discover services;
- own services;
- resolve services;
- manage lifecycle;
- construct widgets.

Explicit dependencies are preferred over generic service lookup.


## 6.3 ShellPlugin

ShellPlugin is the final composition boundary.

It must:

- obtain already-initialized UI components;
- establish their layout relationships;
- establish the workspace composition;
- connect existing widgets to the visible root.

It must NOT:

- construct Core services;
- construct tools;
- construct renderers;
- perform calculations;
- own plugin lifecycle;
- duplicate plugin state;
- become a second PluginManager.

The Shell is a composition layer, not an application framework.


---

# 7. Workspace Architecture

The final GridForge workspace is intended to resemble a combination of:

- ETAP engineering workflow;
- Blender dockable workspace;
- CAD-style canvas.

The target layout is:

    +-------------------------------------------------------------+
    | Menu / Toolbar / Application Commands                       |
    +-------------------------------------------------------------+
    |                                                             |
    | Left        |              Central Canvas        | Right    |
    | Dock        |                                  | Dock     |
    |             |                                  |          |
    | Tool        |                                  | Property |
    | Palette     |                                  | Editor   |
    |             |                                  |          |
    | Project     |          Electrical SLD           | Equipment|
    | Explorer    |             Canvas                | Config.  |
    |             |                                  |          |
    +-------------+----------------------------------+----------+
    | Command Center / Diagnostics / Output                     |
    +-------------------------------------------------------------+
    | Status Bar                                                   |
    +-------------------------------------------------------------+


The workspace must support:

- docking;
- undocking;
- resizing;
- collapsing;
- hiding;
- restoring;
- layout persistence;
- multiple panel instances where appropriate;
- future workspace profiles.


---

# 8. Central Canvas

Directory:

    ui/canvas/

Current components:

    coordinate_system.py
    graphics_view.py
    grid_scene.py
    grid_system.py
    interaction_manager.py
    navigation_controller.py
    preview_layer.py
    render_system.py


The canvas is the primary engineering workspace.

It provides:

- electrical drawing;
- object placement;
- object movement;
- connection visualization;
- grid interaction;
- zoom;
- pan;
- selection interaction;
- previews;
- rendering.

The canvas does NOT own the authoritative electrical model.


---

# 9. GraphicsView

File:

    ui/canvas/graphics_view.py

GraphicsView is the Qt viewport.

Responsibilities include:

- receiving mouse input;
- receiving keyboard input;
- receiving wheel events;
- displaying QGraphicsScene;
- forwarding interaction to appropriate controllers;
- displaying the canvas.

GraphicsView should remain thin.

It should not implement:

- electrical topology;
- solver logic;
- equipment configuration;
- rendering rules;
- project management.


---

# 10. GridScene

File:

    ui/canvas/grid_scene.py

GridScene represents the graphical scene.

It owns the Qt scene-level presentation objects.

It may contain:

- graphical items;
- preview objects;
- visual overlays;
- selection presentation.

It does not become the authoritative electrical network.

The Core model remains authoritative.


---

# 11. Coordinate System

File:

    ui/canvas/coordinate_system.py

The coordinate system provides translation between:

- screen coordinates;
- viewport coordinates;
- scene coordinates;
- engineering/grid coordinates.

It should remain independent from electrical calculations.

Future extensions may include:

- engineering units;
- snapping coordinates;
- geographic coordinates;
- substation coordinate systems;
- multi-canvas coordinate transforms;
- world/local coordinate systems.


---

# 12. Grid System

File:

    ui/canvas/grid_system.py

GridSystem manages visual/grid interaction such as:

- grid spacing;
- major/minor grid;
- grid visibility;
- alignment;
- grid snapping integration.

GridSystem must not become the electrical topology engine.


---

# 13. NavigationController

File:

    ui/canvas/navigation_controller.py

NavigationController owns:

- zoom;
- pan;
- transform;
- wheel zoom;
- view reset;
- fit-to-content;
- navigation diagnostics.

It does NOT:

- render;
- create graphics items;
- modify Core;
- manage tools;
- manage electrical topology.


---

# 14. InteractionManager

File:

    ui/canvas/interaction_manager.py

InteractionManager coordinates low-level canvas interaction.

It sits between:

    GraphicsView
        |
        v
    InteractionManager
        |
        +-- ToolController
        +-- SelectionController
        +-- NavigationController
        +-- CanvasController


InteractionManager must not become a domain controller.


---

# 15. RenderSystem

File:

    ui/canvas/render_system.py

RenderSystem is responsible for rendering orchestration.

It determines which renderer should represent which visual object.

The relationship is:

    Model / presentation state
            |
            v
       RenderSystem
            |
            v
     RendererRegistry
            |
            v
        Renderer
            |
            v
      Graphics Item


Rendering does not belong to:

- NavigationController;
- ShellPlugin;
- MainWindow;
- PluginContext.


---

# 16. Renderers

Directory:

    ui/renderers/

Current components include:

    renderer_base.py
    renderer_loader.py
    renderer_utils.py
    bus_renderer.py
    line_renderer.py


Renderers are responsible for visual representation.

Examples:

    BusRenderer
    LineRenderer

Future renderers:

    TransformerRenderer
    GeneratorRenderer
    MotorRenderer
    BreakerRenderer
    SwitchRenderer
    LoadRenderer
    CapacitorRenderer
    ReactorRenderer
    RelayRenderer
    CT/PT Renderer
    CableRenderer
    TowerRenderer
    TransmissionLineRenderer
    ProtectionZoneRenderer
    AnnotationRenderer


Renderers must not perform electrical calculations.


---

# 17. Graphics Items

Directory:

    ui/items/

Current:

    base_item.py
    bus_item.py
    line_item.py


Graphics items are presentation objects.

They should represent visual objects and forward meaningful interaction to
controllers.

They should not become independent electrical models.

Future items will be added only when corresponding engineering object
types require a visual representation.


---

# 18. Controller Architecture

Directory:

    ui/controllers/

Current:

    canvas_controller.py
    command_controller.py
    controller_registry.py
    interaction_controller.py
    navigation_controller.py
    selection_controller.py
    tool_controller.py


Controllers coordinate operations between UI components and application
services.

They must not duplicate Core.

Recommended responsibility boundaries:

    CanvasController
        -> canvas-level coordination

    InteractionController
        -> interaction coordination

    NavigationController
        -> navigation coordination

    SelectionController
        -> selection coordination

    ToolController
        -> active tool coordination

    CommandController
        -> application command dispatch

    ControllerRegistry
        -> controller lookup/composition


---

# 19. Application Controller

File:

    ui/core/controller.py

The application Controller is the authoritative UI/application
coordination boundary.

It coordinates:

- commands;
- UI actions;
- application services;
- project operations;
- Core interaction.

The Controller must not become the Core itself.

Its purpose is coordination.


---

# 20. Tools

Directory:

    ui/tools/

The tool subsystem is intentionally extensive.

Current architecture includes:

- ToolBase;
- ToolManager;
- ToolRegistry;
- ToolDispatcher;
- ToolContext;
- ToolFactory;
- ToolLifecycle;
- ToolState;
- ToolMode;
- ToolPolicy;
- ToolCapabilities;
- ToolRequirements;
- ToolValidator;
- ToolSession;
- ToolEnvironment;
- ToolInteraction;
- ToolInput;
- ToolEvents;
- ToolHooks;
- ToolObserver;
- ToolSignals;
- ToolResult;
- ToolProfile;
- ToolShortcuts;
- ToolMetrics;
- ToolTracing;
- ToolLogging;
- ToolDebug;
- ToolDependencies;
- ToolAdapter;
- ToolActions.

Current concrete tools:

    SelectTool
    BusTool
    LineTool


The architecture permits future tools without changing the fundamental
canvas architecture.

Future tools include:

    TransformerTool
    GeneratorTool
    MotorTool
    LoadTool
    BreakerTool
    SwitchTool
    CableTool
    ProtectionTool
    AnnotationTool
    MeasurementTool
    AreaTool
    BusbarTool
    MultiSelectTool
    ConnectionTool


The number of concrete tools is deliberately controlled.

Infrastructure should not be confused with concrete tool count.


---

# 21. Tool Palette

A dedicated Tool Palette is required.

It is a UI panel, not the ToolManager.

The relationship is:

    Tool Palette
        |
        v
    ToolController
        |
        v
    ToolManager / Dispatcher
        |
        v
    Active Tool


The Tool Palette provides:

- tool selection;
- tool categories;
- icons;
- shortcuts;
- tool descriptions;
- active-tool indication;
- optional search/filter.

The actual tool lifecycle remains in the tool subsystem.


---

# 22. Project Explorer

The Project Explorer is a dockable engineering tree.

Example:

    Project
    |
    +-- Study Cases
    |
    +-- Grid
    |   |
    |   +-- Buses
    |   +-- Lines
    |   +-- Transformers
    |   +-- Generators
    |   +-- Motors
    |   +-- Loads
    |
    +-- Substations
    |
    +-- Protection
    |
    +-- Controllers
    |
    +-- Results
    |
    +-- Reports


The Project Explorer displays application/project structure.

It must not independently own the project model.

It requests information through the appropriate project/application boundary.


---

# 23. Property Editor

The Property Editor is a central engineering UI component.

It displays the properties of the selected object.

Example:

    Selected Object
    -------------------------
    Type
    Name
    ID
    Position

    Electrical
    -------------------------
    Voltage
    Rating
    Frequency
    Parameters

    Protection
    -------------------------
    Relay
    Pickup
    Time Dial
    Curve

    Engineering
    -------------------------
    Manufacturer
    Model
    Description


The Property Editor must not directly mutate Core.

The correct flow is:

    Property Editor
          |
          v
    Controller / Command
          |
          v
    Application Service
          |
          v
    Core


This guarantees:

- validation;
- undo/redo;
- command history;
- consistent state changes.


---

# 24. Equipment Configurator

The Equipment Configurator provides detailed engineering configuration
for equipment.

It may be opened as:

- dock;
- floating window;
- tabbed editor;
- modal engineering editor where appropriate.

Examples:

    Transformer Configurator
    Generator Configurator
    Motor Configurator
    Relay Configurator
    Breaker Configurator
    Cable Configurator


The configurator should use reusable property/editor infrastructure rather
than duplicating Core models.


---

# 25. Panel Architecture

A dedicated panel architecture is required.

Panels should be independently:

- registered;
- created;
- shown;
- hidden;
- docked;
- undocked;
- collapsed;
- restored;
- persisted.

Potential panel identifiers:

    tool_palette
    project_explorer
    property_editor
    equipment_configurator
    command_center
    diagnostics
    analysis_results
    object_inspector
    protection_editor
    settings
    navigator
    layer_manager


The PanelRegistry should remain the central registration boundary.


---

# 26. Dock Manager

A future dedicated DockManager / WorkspaceManager should own:

- panel placement;
- docking areas;
- panel visibility;
- workspace layouts;
- layout restoration;
- layout persistence;
- default workspace;
- engineering workspace profiles.

The ShellPlugin should compose this system rather than manually becoming
the dock manager.


---

# 27. Command Architecture

GridForge needs a unified command architecture.

The relationship should be:

    UI Action
       |
       v
    CommandController
       |
       v
    CommandManager
       |
       +-- execute
       +-- undo
       +-- redo
       +-- history
       |
       v
    Application/Core


Commands should represent meaningful application operations.

Examples:

    CreateBusCommand
    CreateLineCommand
    DeleteElementCommand
    MoveElementCommand
    ModifyPropertyCommand
    ConnectElementsCommand
    CreateTransformerCommand
    RunLoadFlowCommand
    RunShortCircuitCommand


The Command Center provides a visible interface to this infrastructure.


---

# 28. Command Center

The Command Center is a future dockable UI.

It provides:

- command history;
- command status;
- errors;
- warnings;
- execution information;
- solver commands;
- application commands;
- optional CLI-like interaction.

It is a UI surface.

It is NOT the CommandManager.


---

# 29. File and Project Architecture

A first-class File/Project subsystem is required.

Responsibilities should include:

    ProjectManager
        |
        +-- New
        +-- Open
        +-- Save
        +-- Save As
        +-- Close
        +-- Recent Projects
        +-- Import
        +-- Export


The project system must support future:

- versioning;
- migration;
- validation;
- autosave;
- recovery;
- templates;
- project metadata;
- multiple study cases.


The UI must not implement serialization directly.


---

# 30. Solver Manager

A first-class SolverManager is required.

The UI must not call individual numerical solvers directly.

Correct architecture:

    UI
      |
      v
    CommandController
      |
      v
    SolverManager
      |
      v
    Analysis / Solver Layer
      |
      v
    Core


Future solver operations include:

    Load Flow
    Short Circuit
    N-1
    Optimal Power Flow
    Protection Coordination
    Transient Stability
    EMT
    Harmonic Analysis
    Motor Starting
    Arc Flash
    Reliability
    Voltage Stability


SolverManager also provides a natural place for:

- execution state;
- cancellation;
- progress;
- result handles;
- solver diagnostics;
- asynchronous execution.


---

# 31. Analysis Results

Analysis results should have dedicated UI surfaces.

Examples:

    Load Flow Results
    Short Circuit Results
    Protection Results
    OPF Results
    Stability Results
    Harmonic Results


Results should not be stored solely in widgets.

They belong to the application/Core result architecture.


---

# 32. Core CLI

GridForge should provide a CLI entry boundary independent of the GUI.

Conceptually:

    CLI
      |
      v
    Application Services
      |
      v
    Core


The CLI may support:

    gridforge new
    gridforge open
    gridforge validate
    gridforge solve
    gridforge loadflow
    gridforge shortcircuit
    gridforge export
    gridforge report


The CLI must share application services with the GUI where appropriate.

The GUI and CLI must not implement separate business logic.


---

# 33. Status and Diagnostics

The status system should communicate:

- current tool;
- cursor position;
- grid state;
- selection;
- solver status;
- project state;
- warnings;
- errors;
- background operations.

Diagnostics should be available independently from the status bar.

A serious engineering application requires persistent diagnostic information.


---

# 34. Styling and Theme

Directory:

    ui/styling/

Current:

    style_manager.py
    theme.py
    stylesheet.qss


Styling must support:

- dark engineering workspace;
- light workspace;
- high contrast;
- equipment color schemes;
- analysis overlays;
- selection visualization;
- status states.

Future support:

- user themes;
- workspace-specific themes;
- accessibility scaling;
- icon packs;
- engineering color standards.


---

# 35. Future Multi-Canvas Architecture

GridForge is intended to support more than one canvas context.

Possible hierarchy:

    Project
      |
      +-- System Canvas
      |
      +-- Substation Canvas
      |
      +-- Switchyard Canvas
      |
      +-- Equipment Canvas
      |
      +-- Protection Canvas
      |
      +-- Geographic Canvas


Navigation between these contexts must remain separate from ordinary
viewport zoom/pan.


---

# 36. Future Engineering Views

Future UI views may include:

    Single Line Diagram
    Physical Layout
    Geographic View
    Control Logic
    Protection View
    TCC View
    Sequence Network
    Cable Schedule
    Equipment Schedule
    Load Flow Results
    Harmonic Results
    Trend View
    Time-Domain Plot
    Oscillography
    Relay Coordination
    Report View


These should become pluggable view/workspace components.


---

# 37. Future Visualization System

The rendering architecture should eventually support:

- electrical state overlays;
- energized/de-energized visualization;
- load-flow arrows;
- voltage coloring;
- current coloring;
- fault current visualization;
- protection zones;
- relay reach;
- TCC visualization;
- animation;
- transient visualization;
- result overlays.

Rendering remains separate from the Core computation.


---

# 38. Selection Architecture

Selection is a cross-cutting UI capability.

The intended flow is:

    GraphicsView
        |
        v
    SelectionController
        |
        v
    SelectionManager
        |
        +-- Project Explorer
        +-- Property Editor
        +-- Equipment Configurator
        +-- Canvas
        +-- Status


Selecting an object on the canvas should automatically allow its properties
to appear in the Property Editor.

Selecting the same object from the Project Explorer should produce the
same authoritative selection state.


---

# 39. Snap Architecture

Snap functionality remains separate.

Current:

    ui/core/snap_system.py

Possible snap types:

    Grid Snap
    Endpoint Snap
    Bus Snap
    Connection Snap
    Alignment Snap
    Orthogonal Snap
    Angle Snap
    Equipment Anchor Snap


Snap logic must remain independent of rendering.


---

# 40. Preview Layer

PreviewLayer provides temporary visualization while tools operate.

Examples:

- line preview;
- connection preview;
- equipment placement preview;
- selection rectangle;
- snap indicator;
- measurement preview.

Preview objects are transient.

They must not be mistaken for committed Core state.


---

# 41. UI State vs Core State

This distinction is mandatory.

### UI state

Examples:

    active tool
    active panel
    panel visibility
    zoom
    pan
    selection presentation
    workspace layout
    theme
    cursor mode


### Core/application state

Examples:

    buses
    lines
    transformers
    generators
    loads
    network topology
    electrical parameters
    protection settings
    study cases
    solver results


UI state may be owned by UI infrastructure.

Engineering state remains authoritative in Core/application services.


---

# 42. Dependency Direction

The preferred dependency direction is:

    UI
      |
      v
    Controllers
      |
      v
    Application Services
      |
      v
    Core


Rendering:

    Core/Application State
          |
          v
       UI State
          |
          v
      RenderSystem
          |
          v
       Renderers
          |
          v
    Graphics Items


The following are architectural violations:

    Renderer -> Core mutation
    GraphicsItem -> Core direct mutation
    ShellPlugin -> Solver
    PropertyEditor -> Core direct mutation
    MainWindow -> electrical calculation
    NavigationController -> Core
    Tool -> direct uncontrolled Core mutation


---

# 43. Plugin Expansion Strategy

Future plugins may include:

    CanvasPlugin
    PanelsPlugin
    ToolbarPlugin
    StatusPlugin
    ShellPlugin

Future:

    ProjectPlugin
    PropertyPlugin
    EquipmentPlugin
    CommandCenterPlugin
    DiagnosticsPlugin
    SolverPlugin
    AnalysisPlugin
    ProtectionPlugin
    ReportPlugin
    FilePlugin
    WorkspacePlugin
    CLI integration


Plugins should be introduced only when they represent a coherent
architectural boundary.

The plugin system must not be used merely to fragment ordinary classes.


---

# 44. Planned UI Plugin Tree

A future target may evolve toward:

    ui/
    |
    +-- canvas/
    |
    +-- controllers/
    |
    +-- core/
    |
    +-- items/
    |
    +-- panels/
    |
    +-- plugins/
    |
    +-- renderers/
    |
    +-- styling/
    |
    +-- tools/
    |
    +-- workspace/
    |
    +-- main_window.py


Potential panel package:

    ui/panels/
    |
    +-- base_panel.py
    +-- dock_manager.py
    +-- tool_palette.py
    +-- project_explorer.py
    +-- property_editor.py
    +-- equipment_configurator.py
    +-- command_center.py
    +-- diagnostics_panel.py
    +-- analysis_results.py


Potential application package:

    application/
    |
    +-- project_manager.py
    +-- file_manager.py
    +-- solver_manager.py
    +-- command_center.py
    +-- analysis_manager.py
    +-- workspace_manager.py
    +-- application_services.py


The exact package placement must be decided during the architecture audit
before implementation.


---

# 45. What Already Exists

The current UI architecture already contains substantial infrastructure.

### Canvas

    coordinate_system.py
    graphics_view.py
    grid_scene.py
    grid_system.py
    interaction_manager.py
    navigation_controller.py
    preview_layer.py
    render_system.py


### Controllers

    canvas_controller.py
    command_controller.py
    controller_registry.py
    interaction_controller.py
    navigation_controller.py
    selection_controller.py
    tool_controller.py


### Core UI Infrastructure

    command_manager.py
    controller.py
    panel_registry.py
    qt.py
    renderer_loader.py
    renderer_registry.py
    selection_manager.py
    snap_system.py


### Plugins

    canvas_plugin.py
    panels_plugin.py
    plugin_context.py
    plugin_contract.py
    plugin_events.py
    plugin_loader.py
    plugin_manager.py
    plugin_registry.py
    plugin_state.py
    shell_plugin.py
    status_plugin.py
    toolbar_plugin.py


### Renderers

    bus_renderer.py
    line_renderer.py
    renderer_base.py
    renderer_loader.py
    renderer_utils.py


### Items

    base_item.py
    bus_item.py
    line_item.py


### Tools

The complete tool infrastructure and the initial concrete:

    SelectTool
    BusTool
    LineTool


### Styling

    style_manager.py
    theme.py
    stylesheet.qss


---

# 46. Important Missing Pieces

The following areas require architectural design/integration:

## UI

    Tool Palette
    Project Explorer
    Property Editor
    Equipment Configurator
    Command Center UI
    Diagnostics UI
    Analysis Results UI
    Dock Manager
    Workspace Manager
    Layout persistence


## Application

    File Manager
    Project Manager
    Solver Manager
    Analysis Manager
    Application Service Layer
    Project lifecycle
    Import/Export
    Report generation
    CLI integration


## Engineering UI

    Transformer editor
    Generator editor
    Motor editor
    Breaker editor
    Protection editor
    Relay editor
    Cable editor
    Study Case editor
    Analysis result viewers


These are planned additions.

They must not be implemented as arbitrary widgets without first defining
their ownership and dependency boundaries.


---

# 47. ShellPlugin Integration Rule

The restored ShellPlugin must be reviewed against this architecture.

The final Shell should compose the workspace.

It should NOT destroy the existing architecture by becoming responsible for:

- tool creation;
- renderer creation;
- service creation;
- Core access;
- solver execution;
- project management;
- panel business logic.

The correct model is:

    PluginManager
        |
        +-- CanvasPlugin
        +-- PanelsPlugin
        +-- ToolbarPlugin
        +-- StatusPlugin
        +-- Future plugins
        |
        v
    ShellPlugin
        |
        v
    Workspace Composition


---

# 48. Runtime Composition

The final runtime should conceptually become:

    main.py
       |
       v
    QApplication
       |
       v
    Core / Application Services
       |
       v
    Controller
       |
       v
    MainWindow
       |
       v
    PluginManager
       |
       v
    Plugin Initialization
       |
       v
    Shell / Workspace
       |
       +-----------------------+
       |                       |
       v                       v
    Dock System             Central Canvas
       |                       |
       +--- Tool Palette       +-- GraphicsView
       +--- Project Explorer   +-- GridScene
       +--- Property Editor    +-- Interaction
       +--- Equipment Config   +-- Navigation
       +--- Command Center     +-- Rendering
       +--- Diagnostics
       +--- Results
       |
       v
    Visible GridForge UI


---

# 49. Engineering Workflow

A typical user workflow should become:

    1. Open project
           |
    2. Project Explorer shows project
           |
    3. Select Grid/Substation
           |
    4. Canvas displays the engineering view
           |
    5. Select equipment tool
           |
    6. Place equipment
           |
    7. Configure equipment
           |
    8. Connect equipment
           |
    9. Inspect properties
           |
   10. Validate network
           |
   11. Execute solver
           |
   12. Display results
           |
   13. Review diagnostics
           |
   14. Save project
           |
   15. Generate report


No individual widget should implement this entire workflow.


---

# 50. Workspace Persistence

The future WorkspaceManager should save:

    panel visibility
    panel positions
    dock sizes
    active workspace
    active canvas
    toolbar configuration
    theme
    preferred tool layout


Example:

    Default Engineering
    Protection Study
    Load Flow Study
    Substation Design
    Analysis Workspace
    Custom User Workspace


The engineering project itself and the UI workspace configuration should
remain conceptually separate.


---

# 51. Future Collaboration

The architecture should leave room for:

- project locking;
- multi-user collaboration;
- change tracking;
- remote solver execution;
- project synchronization.

These should be application-level features rather than canvas features.


---

# 52. Future Automation

The architecture should support:

- Python automation;
- CLI automation;
- scripting;
- batch studies;
- automated project generation;
- automated solver execution;
- report generation.

Automation must use application/Core services rather than manipulating
widgets.


---

# 53. Testing Strategy

Every architectural layer must remain testable independently.

### Unit tests

    NavigationController
    CoordinateSystem
    GridSystem
    SelectionManager
    SnapSystem
    CommandManager
    ToolManager
    PluginManager
    PluginContext
    RenderSystem


### UI integration tests

    CanvasPlugin
    PanelsPlugin
    ShellPlugin
    MainWindow
    DockManager
    PropertyEditor
    ProjectExplorer


### Application integration tests

    ProjectManager
    FileManager
    SolverManager
    CommandController
    Controller


### Runtime validation

The application must eventually be tested by launching the actual
MainWindow and verifying:

    MainWindow visible
    Canvas visible
    Tool Palette visible
    Project Explorer visible
    Property Editor available
    Status visible
    Command Center available
    Docking works
    Canvas renders
    Tools activate
    Selection propagates
    Properties update
    Save/Open work
    Solver commands execute
    Shutdown is clean


---

# 54. Architectural Freeze Policy

Once a subsystem is audited and accepted, it should not be casually
modified to solve an unrelated integration problem.

For example:

    Canvas architecture
        !=
    Shell architecture

    Renderer architecture
        !=
    Navigation architecture

    Core
        !=
    UI state

    Plugin lifecycle
        !=
    UI composition


Integration should occur through defined boundaries.


---

# 55. Development Order

The preferred implementation sequence is:

    Phase 1
        Audit current architecture.

    Phase 2
        Produce EXISTS / MISSING / MISPLACED matrix.

    Phase 3
        Define application services.

    Phase 4
        Define panel/docking architecture.

    Phase 5
        Define workspace architecture.

    Phase 6
        Reconcile PluginContext.

    Phase 7
        Reconcile PluginManager.

    Phase 8
        Redesign ShellPlugin.

    Phase 9
        Integrate CanvasPlugin.

    Phase 10
        Integrate Tool Palette.

    Phase 11
        Integrate Project Explorer.

    Phase 12
        Integrate Property Editor.

    Phase 13
        Integrate Equipment Configurator.

    Phase 14
        Integrate Command Center and Diagnostics.

    Phase 15
        Integrate File/Project services.

    Phase 16
        Integrate SolverManager.

    Phase 17
        Integrate CLI.

    Phase 18
        Runtime validation.

    Phase 19
        UI integration tests.

    Phase 20
        Architectural freeze.


---

# 56. Final Architectural Principle

GridForge V2 must behave like an engineering platform rather than a
collection of Qt widgets.

The desired architecture is:

    Engineering Core
           ↑
    Application Services
           ↑
       Controllers
           ↑
        Commands
           ↑
          UI
           |
     +-----+-----------------------------+
     |                                   |
     v                                   v
  Engineering Panels                  Canvas
     |                                   |
     |                              RenderSystem
     |                                   |
     +------------- Workspace ------------+
                       |
                 Plugin System
                       |
                   MainWindow


The UI is therefore:

    composable
    dockable
    extensible
    testable
    renderer-driven
    controller-driven
    plugin-driven

while Core remains:

    authoritative
    independent
    computational
    domain-driven

This separation is mandatory for the long-term GridForge V2 architecture.
