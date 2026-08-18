# GridForge UI Core

## UI Infrastructure, Application Services, and Architectural Boundaries

The `ui/core/` package provides the foundational infrastructure and application-facing services used by the GridForge V2 graphical user interface.

It exists to establish **stable boundaries between UI components and the authoritative GridForge Core**.

The central architectural principle is:

> **`ui/core/` provides GUI infrastructure and application-facing services; it does not become a second engineering core.**

Engineering truth remains owned by `core/`.

---

# 1. Purpose

The purpose of `ui/core/` is to provide common services required by higher-level UI components such as:

* Canvas
* Tools
* Panels
* Plugins
* Renderers
* Views
* UI actions
* Future workspaces and application-level UI services

The package provides infrastructure for:

* Qt framework isolation
* Application/UI controller access
* Command execution
* Undo/redo history
* Selection management
* Tool lifecycle management
* UI-facing service coordination
* Stable application-facing boundaries

Conceptually:

```text
                         GridForge UI
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
          Canvas            Tools            Panels
             │                │                │
             └────────────────┼────────────────┘
                              │
                              ▼
                         ui/core/
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
       Qt Layer          UI Services        UI/Application
                           │                  Contracts
          │                │
          └────────────────┼───────────────────┐
                           ▼                   │
                       Controller             │
                           │                   │
                           ▼                   │
                     GridForge Core ◄─────────┘
```

The dependency direction is intentional.

---

# 2. Architectural Position

`ui/core/` sits at the infrastructure boundary of the GUI subsystem.

It is neither:

* an engineering domain layer,
* a rendering layer,
* a concrete tool implementation layer,
* a plugin implementation layer,
* nor a persistence layer.

Its role is to provide the services that allow those higher-level components to operate without creating competing application state.

The broad architecture is:

```text
┌────────────────────────────────────────────────────┐
│                    GridForge UI                    │
│                                                    │
│ Canvas • Tools • Panels • Plugins • Renderers      │
└─────────────────────────┬──────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│                     ui/core/                       │
│                                                    │
│ Qt • Controller • Commands • Selection • Tools     │
│ UI/Application Services and Boundaries             │
└─────────────────────────┬──────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│                  GridForge Core                    │
│                                                    │
│ Model • Network • Analysis • Protection • Solver  │
└────────────────────────────────────────────────────┘
```

The Core remains headless and authoritative.

---

# 3. Current Package Structure

The current `ui/core/` package is intentionally small.

```text
ui/
└── core/
    ├── __init__.py
    ├── README.md
    ├── qt.py
    ├── controller.py
    ├── command_manager.py
    ├── selection_manager.py
    └── tool_manager.py
```

Each module has a deliberately focused responsibility.

---

# 4. Module Responsibilities

## 4.1 `qt.py`

`qt.py` is the central Qt abstraction boundary.

GridForge V2 uses:

```text
PySide6
```

UI modules must not independently introduce alternative Qt frameworks.

The approved dependency direction is:

```text
GridForge UI
     │
     ▼
ui.core.qt
     │
     ▼
PySide6
```

The purpose of this layer is not to hide Qt behavior.

It provides a controlled internal import boundary so that GridForge UI code does not scatter framework imports throughout the architecture.

### Current principles

* PySide6 is the sole Qt implementation.
* No PyQt5.
* No PyQt6.
* No PySide2.
* No wildcard Qt imports.
* Qt types are explicitly exported.
* `qt.py` contains no GridForge application logic.
* `qt.py` must not import Core, Controllers, Tools, Renderers, or Canvas modules.

The Qt layer is therefore infrastructure only.

---

# 5. `controller.py`

The Controller is the application-facing coordination boundary between the UI and GridForge Core.

Conceptually:

```text
UI
 │
 ▼
Controller
 │
 ▼
Core
```

The Controller is responsible for coordinating application operations without transferring engineering authority into the UI.

The Controller may provide UI-facing access to operations such as:

* object creation
* object modification
* object deletion
* selection state
* project/application state
* Core operations
* domain-event propagation
* application-level workflows

The exact engineering behavior remains implemented by the Core.

The Controller must therefore not become a second model.

---

# 6. `command_manager.py`

`CommandManager` provides the central UI-facing command execution boundary.

The command architecture is:

```text
UI / Tool
    │
    ▼
CommandManager
    │
    ▼
Command
    │
    ▼
Controller
    │
    ▼
Core
    │
    ▼
Domain Events
```

Commands represent **intent**.

They do not become an alternative storage mechanism for engineering state.

## Responsibilities

`CommandManager` owns:

* command execution
* undo history
* redo history
* command validation
* command diagnostics
* undo/redo availability
* history limits
* command labels

It does not own:

* Core state
* engineering models
* topology
* solver state
* domain events
* electrical calculations

## History model

A successful command enters the undo history.

A failed command does not.

A successful new command invalidates redo history.

Undo and redo operate through the normal command pathway.

```text
execute
   │
   ▼
Controller
   │
   ▼
Core
   │
   ▼
Domain Mutation
   │
   ▼
Domain Event
```

Undo:

```text
Command.undo(controller)
        │
        ▼
    Controller
        │
        ▼
       Core
```

Redo:

```text
Command.execute(controller)
        │
        ▼
    Controller
        │
        ▼
       Core
```

The CommandManager does not reconstruct application state from history.

---

# 7. `selection_manager.py`

`SelectionManager` is the UI selection adapter.

Persistent application selection remains owned by the Controller.

The architecture is:

```text
Controller.selected_ids
          │
          ▼
SelectionManager
          │
          ▼
Graphics Selection
```

The SelectionManager therefore does not maintain an independent authoritative selection collection.

## Responsibilities

It provides:

* selection queries
* single selection
* additive selection
* clearing selection
* selection diagnostics
* graphics selection synchronization
* graphics-item lookup by `object_id`

The graphics scene is only a projection.

```text
Controller.selected_ids
          │
          ▼
SelectionManager
          │
          ▼
QGraphicsItem.setSelected()
```

The reverse direction is not authoritative.

A `QGraphicsItem` must never become the owner of application selection state.

---

# 8. `tool_manager.py`

`ToolManager` provides application-level lifecycle management for UI tools.

The current concrete GridForge V2 tool set is intentionally frozen to:

```text
SelectTool
BusTool
LineTool
```

The ToolManager is responsible for coordinating tool activation and lifecycle.

It does not implement the internal behavior of those tools.

The architecture is:

```text
ToolManager
     │
     ├── SelectTool
     ├── BusTool
     └── LineTool
```

Concrete tool implementations remain in:

```text
ui/tools/
```

This distinction is important.

`ui/core/tool_manager.py` manages tool lifecycle.

`ui/tools/` contains concrete tool implementations and tool-specific infrastructure.

---

# 9. Ownership Boundaries

One of the most important responsibilities of `ui/core/` is preserving ownership boundaries.

## Engineering truth

Owned by:

```text
core/
```

Examples include:

* buses
* lines
* transformers
* generators
* electrical topology
* network state
* Y-bus
* power flow
* short circuit
* protection
* relay coordination
* simulation state
* solver state

## UI state

Owned by the UI/application layer.

Examples include:

* active tool
* selected objects
* interaction state
* canvas state
* view state
* UI preferences
* navigation state

The distinction is:

```text
Engineering State
       │
       ▼
     Core

UI State
       │
       ▼
     UI
```

The two must not be conflated.

---

# 10. UI/Core Boundary

The preferred data flow is:

```text
                User
                 │
                 ▼
              UI Tool
                 │
                 ▼
          Command / Controller
                 │
                 ▼
              Core API
                 │
                 ▼
        Authoritative Mutation
                 │
                 ▼
           Domain Events
                 │
                 ▼
             UI Update
```

The UI may request an operation.

The Core determines whether that operation is valid and what the resulting engineering state becomes.

This prevents the UI from becoming a shadow engineering model.

---

# 11. No Engineering Logic

`ui/core/` must not contain engineering computation.

The following do not belong here:

* Newton-Raphson
* Y-bus assembly
* load-flow calculations
* short-circuit calculations
* protection calculations
* relay coordination
* transient simulation
* EMT calculations
* network topology algorithms
* electrical constraint evaluation
* engineering validation logic

Instead:

```text
ui/core
   │
   ▼
Controller
   │
   ▼
GridForge Core
   │
   ├── Model
   ├── Network
   ├── Analysis
   ├── Protection
   └── Solver
```

The UI infrastructure requests operations.

The Core performs engineering work.

---

# 12. No Engineering State Duplication

`ui/core/` must not create a competing representation of the electrical system.

Incorrect:

```text
core/
    authoritative buses

ui/core/
    another list of buses
```

Correct:

```text
core/
    authoritative engineering objects

ui/
    object IDs
    references
    selection state
    presentation state
```

A graphics object may represent a Core object, but it does not become the owner of that object.

For example:

```text
core.model.Bus
      │
      ▼
BusItem
```

`BusItem` represents the bus visually.

It does not own the engineering bus.

---

# 13. Qt Independence of the Command Layer

Although `ui/core/` is a GUI package, not every service needs direct Qt access.

In particular:

```text
command_manager.py
```

is intentionally Qt-independent.

This allows commands to be used by:

* Canvas tools
* Panels
* Toolbar actions
* Menus
* Keyboard shortcuts
* Future automation
* Future API interfaces
* Headless application workflows

The command architecture therefore remains reusable outside direct Qt event handling.

---

# 14. Plugin and Renderer Ownership

Plugin and renderer infrastructure are deliberately kept outside `ui/core/`.

## Plugins

Plugin infrastructure belongs to:

```text
ui/plugins/
```

including:

* plugin contracts
* plugin registry
* plugin loader
* plugin manager
* plugin context
* plugin state
* plugin events

Concrete plugins remain separate from the infrastructure.

The architecture is:

```text
ui/core services
       │
       ▼
ui/plugins infrastructure
       │
       ▼
Concrete UI Plugins
```

The plugin registry must not silently import every concrete plugin.

Explicit loading remains preferred.

---

# 15. Renderer Ownership

Renderer infrastructure and concrete rendering remain outside `ui/core/`.

Conceptually:

```text
ui/renderers/
    │
    ├── Renderer Registry
    ├── Renderer Loader
    ├── BusRenderer
    ├── LineRenderer
    └── Future Renderers
```

A renderer consumes authoritative engineering objects and produces presentation.

```text
Core Object
     │
     ▼
Renderer
     │
     ▼
Graphics Representation
```

The renderer does not own engineering state.

---

# 16. Tool Ownership

Concrete tools belong under:

```text
ui/tools/
```

The current concrete tool set is:

```text
SelectTool
BusTool
LineTool
```

`ToolManager` provides lifecycle coordination.

This separation allows future tool implementations to evolve without turning `ui/core/` into a repository for tool-specific behavior.

---

# 17. Dependency Direction

The dependency direction must remain acyclic.

The intended conceptual direction is:

```text
                 UI Components
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Canvas        Tools       Panels
          │           │           │
          └───────────┼───────────┘
                      ▼
                   ui/core
                      │
                      ▼
                 Controller
                      │
                      ▼
                GridForge Core
```

The Core must never depend on `ui.core`.

Therefore:

```text
core
  ✗──► ui.core
```

is prohibited.

This preserves the headless nature of GridForge Core.

---

# 18. Selection Architecture

Selection is presentation/application state.

A selected engineering object is identified through a stable object identifier.

For example:

```text
Selected ID
    │
    ▼
Controller.selected_ids
    │
    ▼
SelectionManager
    │
    ▼
Graphics Item
```

Selection identity must not depend on:

* `QGraphicsItem` memory identity
* scene ordering
* numerical network index
* renderer instance identity

This is essential for synchronization and future multi-view support.

---

# 19. Command Architecture

The command layer establishes an important separation:

```text
Intent
  │
  ▼
Command
  │
  ▼
Controller
  │
  ▼
Core
  │
  ▼
Authoritative Mutation
```

A command is not an engineering model.

A command is not a transaction database.

A command is not a Core snapshot.

This distinction permits undo/redo while maintaining a single authoritative engineering state.

---

# 20. Error Handling

UI infrastructure should preserve meaningful errors.

Errors should remain distinguishable by architectural layer.

Examples of UI/application errors:

```text
InvalidCommand
InvalidTool
UIServiceError
PluginLoadError
RendererLoadError
QtInfrastructureError
```

Examples of engineering errors:

```text
InvalidTopology
SolverFailure
ProtectionError
InvalidNetworkOperation
```

`ui/core/` should not indiscriminately convert every failure into a generic UI exception.

Meaningful errors are important for:

* debugging
* testing
* diagnostics
* logging
* automation
* future user-facing error handling

---

# 21. Determinism

UI infrastructure should behave deterministically.

Given identical:

* configuration
* plugin set
* tool set
* renderer set
* application state

the resulting infrastructure behavior should be reproducible.

Determinism is particularly important for:

* tests
* startup
* plugin lifecycle
* debugging
* regression analysis
* automated UI workflows

---

# 22. Performance Principles

`ui/core/` must remain lightweight.

It should avoid:

* unnecessary object duplication
* repeated discovery
* hidden global state
* expensive initialization
* blocking GUI operations
* engineering calculations
* synchronous long-running computation

The Qt event loop must remain responsive.

Long-running engineering operations belong outside the UI execution path and should be coordinated through appropriate controller/backend mechanisms.

---

# 23. Threading Boundary

The UI Core does not own numerical execution.

A long-running operation should conceptually follow:

```text
UI Thread
    │
    ▼
Controller
    │
    ▼
Core Operation
    │
    ▼
Worker / Backend
    │
    ▼
Result
    │
    ▼
Controller
    │
    ▼
UI Update
```

The exact execution mechanism may evolve.

The architectural rule does not:

> **Engineering computation must not block the GUI event loop.**

---

# 24. Multi-Canvas Vision

GridForge is designed to support hierarchical multi-canvas workflows.

A future application may expose contexts such as:

```text
Grid
 │
 ├── Plant
 │
 ├── Substation
 │     ├── Bus
 │     ├── Transformer
 │     └── Feeder
 │
 └── Distribution Area
```

`ui/core/` may eventually provide application-level infrastructure for:

* canvas context identification
* navigation state
* active workspace state
* view coordination
* cross-canvas selection
* context-aware commands

However, the electrical hierarchy remains owned by Core.

The UI may represent the hierarchy.

It must not redefine it.

---

# 25. Future Vision

The long-term goal of `ui/core/` is to become a **small, stable application infrastructure layer**, not a large collection of unrelated UI utilities.

Potential future capabilities include:

### Command Infrastructure

* command grouping
* command coalescing
* transactional command sequences
* command metadata
* command auditing
* command enablement
* keyboard shortcut integration

### Selection Infrastructure

* cross-canvas selection
* selection scopes
* terminal selection
* hierarchical selection
* selection filters
* selection synchronization across views

### UI Services

Potential future services may include:

* workspace management
* navigation services
* notification services
* action services
* shortcut services
* view coordination
* application state services

### Multi-Canvas Support

Future infrastructure may support:

```text
Grid Canvas
     │
     ├── Substation Canvas
     │       │
     │       ├── Equipment
     │       └── Feeders
     │
     └── Plant Canvas
```

The infrastructure should permit multiple views over the same authoritative Core state without duplicating engineering truth.

### Automation

The command architecture can eventually support non-GUI clients:

```text
GUI
 │
 ├── Canvas
 ├── Toolbar
 └── Panel
       │
       ▼
 CommandManager
       ▲
       │
Automation / API
```

This is one reason the command layer is intentionally independent of Qt.

---

# 26. Future Architectural Guardrails

Future expansion must not turn `ui/core/` into a God object.

The following pattern is prohibited:

```text
ui/core/
    ├── Canvas Manager
    ├── Tool Manager
    ├── Panel Manager
    ├── Plugin Manager
    ├── Renderer Manager
    ├── Solver Manager
    ├── Network Manager
    ├── Project Manager
    └── Everything Manager
```

Instead, responsibilities should remain separated:

```text
ui/core/
    │
    ├── Application-facing services
    ├── Command infrastructure
    ├── Selection infrastructure
    ├── Tool lifecycle
    └── Qt boundary

ui/tools/
    └── Concrete tools

ui/renderers/
    └── Rendering infrastructure and implementations

ui/plugins/
    └── Plugin infrastructure and implementations

ui/canvas/
    └── Canvas implementation

core/
    └── Engineering truth
```

A new responsibility should only be added to `ui/core/` when it is genuinely shared infrastructure.

---

# 27. What Must Never Move Into `ui/core/`

The following remain outside the package permanently:

```text
Electrical Models
Network Topology
Y-Bus
Power Flow
Short Circuit
Protection
Relay Coordination
Dynamic Simulation
Solver Algorithms
Project Engineering State
Engineering Persistence
```

Likewise, `ui/core/` should not become the home of:

```text
Concrete Renderers
Concrete Tools
Concrete Plugins
Canvas Rendering
Equipment Graphics
Engineering Algorithms
```

The package is intentionally limited.

---

# 28. Testing Strategy

`ui/core/` should be testable independently from the full GUI where practical.

## Qt Boundary Tests

Verify:

* PySide6 imports
* exported symbols
* absence of alternative Qt frameworks
* stable internal API

## Controller Tests

Verify:

* application-facing operations
* Core delegation
* selection ownership
* event propagation
* error preservation

## CommandManager Tests

Verify:

* command validation
* successful execution
* failed execution
* undo
* redo
* failed undo
* failed redo
* redo invalidation
* history limits
* recursive execution protection
* diagnostic state

## SelectionManager Tests

Verify:

* Controller selection remains authoritative
* single selection
* additive selection
* clearing
* graphics synchronization
* item lookup
* graphics reset
* selection diagnostics

## ToolManager Tests

Verify:

* registration/use of approved tools
* activation
* deactivation
* current-tool state
* lifecycle behavior
* invalid tool handling

## Integration Tests

The long-term integration path is:

```text
UI Component
      │
      ▼
UI Service
      │
      ▼
Controller
      │
      ▼
Core
      │
      ▼
Domain Event
      │
      ▼
UI Projection
```

The tests should verify that this path preserves ownership boundaries.

---

# 29. Development and Freeze Process

Changes to `ui/core/` should follow the GridForge development methodology:

```text
Architecture
     ↓
Contract
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
```

A downstream workaround should not be used to hide an architectural defect.

Defects should be corrected at the layer where ownership is actually wrong.

---

# 30. Architectural Rules

| #  | Rule                         | Requirement                                                     |
| -- | ---------------------------- | --------------------------------------------------------------- |
| 1  | Infrastructure only          | `ui/core/` must not become an engineering subsystem             |
| 2  | Core authority               | Engineering truth belongs to `core/`                            |
| 3  | PySide6 only                 | No mixed Qt frameworks                                          |
| 4  | Qt boundary                  | Common Qt imports pass through `ui.core.qt`                     |
| 5  | No Core dependency on UI     | `core/` must remain headless                                    |
| 6  | No state duplication         | UI must not duplicate engineering truth                         |
| 7  | Controller boundary          | UI operations reach Core through defined application interfaces |
| 8  | Commands represent intent    | Commands must not become state snapshots                        |
| 9  | Selection is UI state        | Persistent engineering state remains in Core                    |
| 10 | Focused services             | Each manager/service has a narrow responsibility                |
| 11 | Concrete tools stay separate | Tool implementations remain in `ui/tools/`                      |
| 12 | Renderers stay separate      | Rendering remains in `ui/renderers/`                            |
| 13 | Plugins stay separate        | Plugin infrastructure remains in `ui/plugins/`                  |
| 14 | Deterministic behavior       | Infrastructure behavior must be reproducible                    |
| 15 | Responsive UI                | Long-running engineering work must not block Qt                 |
| 16 | Explicit dependencies        | Avoid hidden global state and uncontrolled imports              |
| 17 | Stable contracts             | Higher-level components depend on explicit interfaces           |
| 18 | No God object                | `ui/core/` must remain focused                                  |

---

# 31. Digital-Twin Principle

GridForge follows a digital-twin architecture in which engineering truth is authoritative and visualization is a projection.

The relationship is:

```text
                 AUTHORITATIVE ENGINEERING STATE
                              │
                              ▼
                         GridForge Core
                              │
                              ▼
                         Controller
                              │
                              ▼
                           UI Core
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
            Canvas          Panels           Tools
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                         User Interface
```

The direction is deliberate.

Engineering state flows outward toward the UI.

The UI does not become engineering truth.

---

# 32. Current Status

`ui/core/` is currently established as the foundational UI infrastructure layer containing:

```text
Qt Boundary
    │
    ├── qt.py
    │
Application Services
    │
    ├── controller.py
    ├── command_manager.py
    ├── selection_manager.py
    └── tool_manager.py
```

The package is intentionally kept small and focused.

The current architecture is suitable for the next integration phase involving:

* MainWindow composition
* plugin-driven UI construction
* Canvas integration
* tool integration
* selection projection
* command integration
* panel integration
* application-level event flow

Future capabilities should be added only after their ownership and contracts have been established.

---

# 33. Final Architectural Principle

The defining rule of GridForge UI Core is:

> **Shared UI infrastructure belongs in `ui/core/`; engineering truth belongs in `core/`.**

The package exists to provide stable boundaries between:

```text
User
  │
  ▼
GridForge UI
  │
  ▼
UI Services
  │
  ▼
Controller
  │
  ▼
GridForge Core
  │
  ├── Model
  ├── Network
  ├── Analysis
  ├── Protection
  └── Solver
```

A successful `ui/core/` architecture is therefore not one that contains everything the GUI needs.

It is one that **contains only the infrastructure that genuinely belongs at this boundary**, while keeping Canvas, Tools, Plugins, Renderers, and Engineering Core responsibilities in their appropriate layers.

---

<p align="center">
<em>GridForge UI Core — stable UI infrastructure, explicit application boundaries, and one authoritative engineering core.</em>
</p>
