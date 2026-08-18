# GridForge V2 — UI Core

**Shared UI Infrastructure, Explicit Contracts, One Authoritative Engineering Core**

The `ui/core/` package is the foundational infrastructure layer of the GridForge V2 graphical application.

It provides the services, abstractions, registries, contracts, and coordination mechanisms required by the higher-level UI subsystems—Canvas, Tools, Panels, Plugins, Renderers, Views, and future workspaces—while deliberately remaining separate from the engineering domain.

The central architectural principle is:

> **`ui/core/` provides GUI infrastructure; `core/` owns engineering truth.**

---

## 1. Overview

GridForge is designed as a digital-twin and power-system engineering platform. Its graphical interface must therefore remain a projection and interaction layer over an authoritative engineering model.

The UI architecture follows this direction:

```text
                         USER
                           │
                           ▼
                    GridForge UI
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Canvas            Tools            Panels
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                       ui/core/
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Qt Abstraction      UI Services        Contracts
        │                  │                  │
        │        ┌─────────┼─────────┐        │
        │        ▼         ▼         ▼        │
        │     Commands  Selection  Registries │
        │                                     │
        └────────────────┬────────────────────┘
                         ▼
                   UI Controllers
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

`ui/core/` sits between concrete UI components and the application/controller layer.

It is intentionally **not** an engineering subsystem.

---

# 2. Architectural Mission

The mission of `ui/core/` is to establish a stable foundation on which the GridForge GUI can evolve without allowing GUI concerns to leak into the engineering core.

It provides:

* centralized Qt access;
* application-facing UI services;
* command execution and history;
* selection projection;
* plugin infrastructure;
* renderer infrastructure;
* tool infrastructure;
* snapping infrastructure;
* UI state and event infrastructure;
* controlled service access;
* stable contracts between UI subsystems.

The package should remain:

* lightweight;
* deterministic;
* testable;
* modular;
* explicitly owned;
* Qt-controlled;
* independent of engineering calculations.

---

# 3. Repository Position

The intended repository relationship is:

```text
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
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── qt.py
│   │   ├── command_manager.py
│   │   ├── selection_manager.py
│   │   ├── plugin_registry.py
│   │   ├── plugin_loader.py
│   │   ├── plugin_manager.py
│   │   ├── plugin_context.py
│   │   ├── plugin_contract.py
│   │   ├── plugin_state.py
│   │   ├── plugin_events.py
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
```

The exact file set may evolve.

The architectural role of `ui/core/` must remain stable even as additional services are introduced.

---

# 4. Current UI Core Responsibilities

The current architecture organizes UI infrastructure around several focused services.

| Service                 | Responsibility                             |
| ----------------------- | ------------------------------------------ |
| `qt.py`                 | Central PySide6 boundary                   |
| Controller integration  | Application/UI workflow boundary           |
| `command_manager.py`    | Command execution and undo/redo history    |
| `selection_manager.py`  | Controller-owned selection projection      |
| Plugin infrastructure   | Plugin registration, loading and lifecycle |
| Renderer infrastructure | Renderer registration and discovery        |
| Tool infrastructure     | Tool registration and coordination         |
| Snap infrastructure     | Geometric UI snapping                      |
| UI state infrastructure | Shared presentation state                  |
| Event infrastructure    | UI/application event communication         |

Each service has a deliberately narrow responsibility.

The architecture avoids creating a single monolithic `UIManager`.

---

# 5. Qt Abstraction

## `qt.py`

`ui/core/qt.py` is the controlled Qt boundary for the GridForge UI.

GridForge V2 uses:

**PySide6**

Concrete UI modules must not directly import:

```text
PySide6
PyQt5
PyQt6
PySide2
```

Instead:

```python
from ui.core.qt import QGraphicsScene
```

rather than:

```python
from PySide6.QtWidgets import QGraphicsScene
```

The abstraction establishes one controlled framework boundary:

```text
PySide6
   │
   ▼
ui/core/qt.py
   │
   ├── Canvas
   ├── Tools
   ├── Renderers
   ├── Panels
   └── Plugins
```

This prevents mixed Qt frameworks and keeps framework dependencies explicit.

### Design rule

`qt.py` contains Qt imports and compatibility infrastructure.

It must not contain GridForge engineering logic.

It must not import:

* Core models;
* Controllers;
* Tools;
* Renderers;
* Canvas implementations;
* Plugins;
* Solvers.

---

# 6. Command Infrastructure

## `command_manager.py`

`CommandManager` is the central UI-facing command execution boundary.

The command flow is:

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

The Core and Controller remain authoritative for validation and mutation.

The `CommandManager` owns only command history:

```text
Undo History
Redo History
```

It does not maintain a second copy of application state.

### Command contract

A command provides:

```python
execute(controller)
undo(controller)
```

### Execution semantics

A successful command:

```text
Command.execute()
       │
       ▼
successful mutation
       │
       ▼
undo history
       │
       ▼
redo history cleared
```

A failed command:

```text
Command.execute()
       │
       ▼
exception
       │
       ▼
not added to history
```

Undo and redo use the normal Controller/Core pathway.

This preserves the fundamental rule:

> **History records intent; it does not become an alternate application state store.**

### History limits

`CommandManager` optionally supports bounded undo history through `max_history`.

The oldest entries are discarded when the configured limit is exceeded.

---

# 7. Selection Infrastructure

## `selection_manager.py`

Selection is UI state.

However, persistent application selection is owned by the Controller.

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

`SelectionManager` therefore acts as an adapter and projection service.

It does not maintain an authoritative duplicate selection collection.

### Responsibilities

It provides:

* selection queries;
* single selection;
* additive selection;
* clearing selection;
* graphics synchronization;
* graphics item lookup;
* selected-item lookup;
* selection diagnostics.

### Authority direction

```text
Controller
    │
    │ selected_ids
    ▼
SelectionManager
    │
    ▼
QGraphicsItem.setSelected()
```

The reverse direction is deliberately not authoritative.

A `QGraphicsItem` being selected does not make that item the owner of application selection.

### Selection identity

Selection is based on stable engineering/application identifiers.

It must not depend on:

* `QGraphicsItem` memory identity;
* scene position;
* numerical network indices.

---

# 8. Plugin Infrastructure

The plugin system provides explicit composition infrastructure for the GridForge UI.

The architecture is:

```text
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
```

Plugin infrastructure is deliberately split into separate responsibilities.

Typical components include:

```text
plugin_contract.py
plugin_registry.py
plugin_loader.py
plugin_manager.py
plugin_context.py
plugin_state.py
plugin_events.py
```

## Explicit loading

The registry must not silently import every concrete plugin.

Instead:

```text
Registry
   │
   │ knows registrations/contracts
   ▼
Loader
   │
   │ explicitly imports
   ▼
Concrete Plugins
```

This provides:

* deterministic startup;
* controlled imports;
* reduced circular-import risk;
* easier testing;
* explicit composition.

## Plugin Context

Plugins receive controlled access to application services through `PluginContext`.

Conceptually:

```text
Plugin
  │
  ▼
PluginContext
  ├── Controller
  ├── UI Services
  ├── Registries
  ├── State
  └── Events
```

Plugins should not bypass the established ownership model by reaching into arbitrary private objects.

---

# 9. Renderer Infrastructure

Renderer infrastructure separates renderer discovery from concrete rendering.

```text
Renderer Contract
       │
       ▼
Renderer Registry
       │
       ▼
Renderer Loader
       │
       ▼
Concrete Renderer
       │
       ├── BusRenderer
       ├── LineRenderer
       └── Future Equipment Renderers
```

Concrete renderers live outside `ui/core/`, normally under:

```text
ui/renderers/
```

The registry and loader provide infrastructure.

The renderer itself provides presentation logic.

### Ownership rule

A renderer visualizes an authoritative Core object.

For example:

```text
core.model.Bus
      │
      ▼
BusRenderer
      │
      ▼
Graphics Representation
```

The renderer must not become the owner of the Bus.

Likewise, `LineRenderer` does not own electrical connectivity.

---

# 10. Snap Infrastructure

The Snap System provides graphical interaction assistance.

Typical responsibilities include:

* grid snapping;
* coordinate quantization;
* point snapping;
* terminal snapping;
* alignment assistance;
* snap candidate selection.

The conceptual pipeline is:

```text
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
      │
      ▼
Controller / Validation
```

Snapping is **geometric**.

It is not electrical topology.

Therefore:

> **Geometric proximity does not imply electrical connectivity.**

A snapped line endpoint may still be rejected by the Controller/Core if the resulting electrical operation is invalid.

---

# 11. Tool Infrastructure

GridForge V2 currently maintains a deliberately small concrete tool set:

```text
SelectTool
BusTool
LineTool
```

The tool infrastructure provides shared services and contracts without embedding individual tool behavior into `ui/core/`.

The intended relationship is:

```text
Tool
 │
 ▼
UI Controller
 │
 ▼
Command / Application Operation
 │
 ▼
GridForge Core
```

A tool performs user interaction.

It does not become an engineering authority.

For example, `BusTool` may request creation of a bus, but the authoritative Bus remains a Core model object.

---

# 12. UI State

UI state belongs to the presentation layer.

Examples include:

* active tool;
* current interaction mode;
* selected objects;
* canvas zoom;
* grid visibility;
* navigation context;
* rendering preferences;
* plugin state;
* workspace state.

This must remain separate from engineering state.

| State               | Owner   |
| ------------------- | ------- |
| Bus voltage         | `core/` |
| Bus identity        | `core/` |
| Line impedance      | `core/` |
| Network topology    | `core/` |
| Solver state        | `core/` |
| Protection decision | `core/` |
| Selected object     | UI      |
| Active tool         | UI      |
| Canvas zoom         | UI      |
| Grid visibility     | UI      |
| Interaction mode    | UI      |
| Navigation state    | UI      |

The distinction is fundamental to the digital-twin architecture.

---

# 13. Event Infrastructure

UI events communicate presentation/application transitions.

Examples include:

```text
ToolChanged
SelectionChanged
CanvasChanged
PluginLoaded
RendererRegistered
NavigationChanged
UIStateChanged
```

Events should communicate state transitions rather than become an uncontrolled replacement for explicit application APIs.

Preferred:

```text
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
```

Avoid:

```text
UI Event
   │
   └── directly mutates hidden Core state
```

---

# 14. Dependency Direction

The intended dependency direction is:

```text
                High-Level UI
                     │
                     ▼
                  ui/core
                     │
                     ▼
                Controllers
                     │
                     ▼
                  Core
```

The reverse dependency is prohibited.

In particular:

```text
core/
   ✗
   │
   └────► ui.core
```

The engineering Core remains headless.

No Qt dependency should propagate into `core/`.

---

# 15. Engineering Ownership Boundary

`ui/core/` must never become a second engineering core.

The following do **not** belong in `ui/core/`:

* Bus engineering state;
* Line engineering state;
* Transformer models;
* Generator models;
* electrical topology;
* Y-bus;
* power flow;
* short-circuit calculations;
* Newton-Raphson;
* protection logic;
* relay coordination;
* transient simulation;
* EMT calculations;
* persistent engineering project state.

The correct architecture is:

```text
UI
 │
 ▼
ui/core
 │
 ▼
Controller
 │
 ▼
Core
 │
 ├── Model
 ├── Network
 ├── Analysis
 ├── Solver
 └── Protection
```

---

# 16. Digital-Twin Principle

GridForge's UI follows a digital-twin presentation model.

The Core represents authoritative engineering reality.

The UI represents a human-interaction projection of that reality.

```text
              AUTHORITATIVE ENGINEERING
                         │
                         ▼
                      Core
                         │
                         ▼
                    Controller
                         │
                         ▼
                     ui/core
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Canvas          Panels         Plugins
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                        User
```

The direction is intentional:

> **Engineering truth flows outward toward visualization; visualization does not become engineering truth.**

---

# 17. Multi-Canvas Vision

The UI Core is designed to support hierarchical and multi-canvas navigation.

A future GridForge project may expose a hierarchy such as:

```text
Grid
 │
 ├── Plant
 │    │
 │    ├── Substation
 │    │    ├── Bus
 │    │    ├── Transformer
 │    │    └── Feeder
 │    │
 │    └── Auxiliary Systems
 │
 └── External Network
```

The UI Core may provide:

* navigation state;
* canvas context;
* workspace identity;
* view history;
* context switching;
* multi-canvas coordination.

However, the underlying engineering hierarchy remains owned by the Core model/network.

---

# 18. Registries

GridForge deliberately uses focused registries rather than one universal object registry.

Examples include:

```text
PluginRegistry
RendererRegistry
ToolRegistry
PanelRegistry
CommandRegistry
```

Each registry should have a clearly defined responsibility.

A registry may provide:

* registration;
* lookup;
* duplicate detection;
* removal where appropriate;
* deterministic ordering;
* diagnostics.

A registry should not become responsible for unrelated lifecycle management.

Avoid:

```text
UniversalRegistry
    ├── Plugins
    ├── Renderers
    ├── Tools
    ├── Panels
    ├── Controllers
    ├── Models
    └── Solvers
```

Focused infrastructure is easier to reason about, test, and evolve.

---

# 19. Error Handling

UI Core infrastructure should preserve meaningful failure information.

Examples include:

```text
PluginLoadError
RendererLoadError
InvalidPluginContract
InvalidToolRegistration
QtInfrastructureError
UIServiceError
```

Engineering failures should remain distinguishable from UI infrastructure failures.

For example:

```text
InvalidTopology
SolverFailure
ProtectionError
```

must not be reduced to a generic:

```text
UIError
```

without preserving the underlying cause.

---

# 20. Determinism

UI Core infrastructure should behave deterministically.

Given the same:

```text
Plugin Set
Renderer Set
Tool Set
Application Configuration
```

the resulting registration and loading order should be reproducible.

Determinism improves:

* testing;
* debugging;
* startup reproducibility;
* plugin lifecycle management;
* regression analysis;
* application diagnostics.

---

# 21. Performance Principles

`ui/core/` must remain lightweight.

It should avoid:

* repeated expensive discovery;
* unnecessary object duplication;
* duplicated engineering state;
* blocking operations on the Qt event loop;
* engineering calculations;
* heavyweight event handlers;
* unnecessary registry rebuilding.

Long-running engineering operations belong outside the GUI execution path.

Conceptually:

```text
UI Thread
    │
    ▼
Controller
    │
    ▼
Core Execution
    │
    ▼
Worker / Backend
    │
    ▼
Result
    │
    ▼
UI Thread
```

---

# 22. Testing Strategy

The UI Core should be independently testable.

## Qt Tests

Verify:

* PySide6 imports;
* exported symbols;
* absence of mixed Qt frameworks;
* Qt abstraction behavior.

## Command Tests

Verify:

* command validation;
* successful execution;
* failed execution;
* undo;
* redo;
* redo invalidation;
* failed undo preservation;
* failed redo preservation;
* history limits;
* command diagnostics.

## Selection Tests

Verify:

* Controller remains authoritative;
* selection delegation;
* selection queries;
* graphics synchronization;
* item lookup;
* scene-independent operation;
* graphics reset behavior.

## Registry Tests

Verify:

* registration;
* duplicate handling;
* lookup;
* removal;
* deterministic ordering;
* invalid registration handling.

## Loader Tests

Verify:

* explicit loading;
* loading failures;
* dependency handling;
* lifecycle behavior;
* deterministic loading.

## Contract Tests

Verify:

* required interfaces;
* invalid implementations;
* contract compatibility;
* lifecycle requirements.

## Integration Tests

The complete plugin path should eventually be verified as:

```text
Plugin
   ↓
Registry
   ↓
Loader
   ↓
Manager
   ↓
Context
   ↓
UI Composition
```

---

# 23. Architectural Anti-Patterns

## 23.1 Mixed Qt frameworks

Never allow:

```text
PySide6 + PyQt5
```

or other mixed Qt frameworks.

---

## 23.2 Engineering state inside UI Core

Do not create:

```text
ui/core/
    └── authoritative network
```

The authoritative network belongs to `core/network/`.

---

## 23.3 Hidden plugin imports

Avoid:

```text
plugin_registry
      │
      └── imports every concrete plugin
```

Use explicit loading.

---

## 23.4 UI Core as a God Object

Avoid turning `ui/core/` into something that:

```text
manages Canvas
manages Tools
manages Panels
manages Plugins
manages Solvers
manages Network
manages Projects
```

Infrastructure responsibilities must remain separated.

---

## 23.5 Universal registry

Avoid one registry responsible for every UI object.

---

## 23.6 Graphics as authority

Do not allow:

```text
QGraphicsItem
     │
     └── becomes engineering truth
```

Graphics objects are projections.

---

## 23.7 UI-side engineering calculations

Do not perform:

```text
Power Flow
Y-Bus
Short Circuit
Protection
Solver
```

inside `ui/core/`.

---

# 24. Future Vision

`ui/core/` is intentionally designed as a foundation rather than a finished endpoint.

As GridForge evolves, the UI Core can become the infrastructure layer supporting a much larger engineering workspace without changing the fundamental ownership model.

Future capabilities may include the following.

## 24.1 Command and Workflow Infrastructure

The command system can evolve toward:

* composite commands;
* transactional command execution;
* command grouping;
* command coalescing;
* contextual command availability;
* command metadata;
* keyboard shortcut integration;
* command palettes;
* application automation.

The important constraint remains:

> Commands express intent; Core validates and mutates authoritative state.

---

## 24.2 Advanced Workspace Management

Future workspace infrastructure may support:

```text
Project
 │
 ├── Grid Canvas
 ├── Substation Canvas
 ├── Analysis Workspace
 ├── Protection Workspace
 ├── Results Workspace
 └── Custom User Workspace
```

Possible services include:

* workspace registration;
* workspace persistence;
* layout management;
* dock management;
* workspace switching;
* contextual toolbars;
* workspace-specific commands.

---

## 24.3 Multi-Canvas Navigation

Future UI infrastructure may provide:

* hierarchical canvas navigation;
* breadcrumb navigation;
* canvas history;
* cross-canvas selection;
* synchronized views;
* linked viewport navigation;
* contextual navigation commands.

The electrical hierarchy itself will continue to belong to the Core.

---

## 24.4 Rich Plugin Ecosystem

The plugin architecture can eventually support:

```text
Core Plugins
UI Plugins
Analysis Plugins
Visualization Plugins
Import/Export Plugins
Automation Plugins
Workspace Plugins
```

The plugin system should evolve without allowing plugins to bypass Core ownership boundaries.

A mature plugin may contribute:

* panels;
* tools;
* renderers;
* commands;
* menus;
* toolbar actions;
* property editors;
* analysis views;
* result visualizations.

---

## 24.5 Renderer Evolution

Renderer infrastructure can grow toward a comprehensive equipment visualization system:

```text
BusRenderer
LineRenderer
TransformerRenderer
GeneratorRenderer
MotorRenderer
BreakerRenderer
CTRenderer
PTRenderer
RelayRenderer
CableRenderer
SwitchRenderer
```

The renderer layer remains presentation-only.

Engineering behavior stays in Core.

---

## 24.6 Context-Sensitive UI

A future GridForge interface may dynamically adapt to:

```text
Current Canvas
Current Selection
Active Tool
Object Type
Application Mode
Analysis State
User Workspace
```

For example:

```text
Selected Transformer
        │
        ▼
Context Services
        │
        ├── Transformer Properties
        ├── Protection
        ├── Ratings
        ├── Analysis
        └── Commands
```

This should be achieved through explicit service and command contracts rather than hidden cross-layer coupling.

---

## 24.7 Property and Inspector Infrastructure

A future property system could expose Core model data to UI inspectors:

```text
Core Object
     │
     ▼
Property Adapter
     │
     ▼
Inspector Model
     │
     ▼
Property Panel
```

The UI would present and edit authoritative data through controlled application APIs rather than directly modifying Core objects.

---

## 24.8 Analysis Result Presentation

As GridForge's numerical capabilities expand, UI Core infrastructure can support result presentation for:

* load flow;
* contingency analysis;
* short circuit;
* protection;
* relay coordination;
* transient stability;
* optimization;
* scenario comparison.

The architecture should remain:

```text
Core Analysis
      │
      ▼
Authoritative Result
      │
      ▼
Controller
      │
      ▼
UI Result Adapter
      │
      ▼
Visualization
```

The UI displays results; it does not become their owner.

---

## 24.9 Event and State Infrastructure

Future UI state services may support:

* application modes;
* workspace modes;
* navigation state;
* analysis state;
* selection contexts;
* temporary interaction state;
* synchronized views;
* state persistence.

The state model should remain explicit and inspectable.

---

## 24.10 Automation and API Integration

A future automation layer could use the same command infrastructure as the GUI:

```text
GUI
 │
 ├──────────────┐
 ▼              ▼
User Input    Automation
 │              │
 └──────┬───────┘
        ▼
     Commands
        │
        ▼
   Controller
        │
        ▼
      Core
```

This would allow GUI actions and automation workflows to share the same authoritative application pathways.

---

# 25. Long-Term Architectural Vision

The long-term goal is not to make `ui/core/` larger.

The goal is to make it **more stable**.

A mature GridForge UI should be able to evolve from:

```text
Simple Canvas
     │
     ▼
Basic Tools
     │
     ▼
Basic Panels
```

toward:

```text
                    GridForge Workspace
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Canvas             Panels            Analysis
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                        ui/core
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
   Commands            Services            Contracts
       │                   │                   │
       ├── Plugins         ├── Selection       │
       ├── Tools           ├── Navigation      │
       ├── Renderers       ├── Workspace       │
       └── Automation      └── UI State        │
                           │
                           ▼
                      Controller
                           │
                           ▼
                    GridForge Core
```

The infrastructure should become more capable while remaining architecturally thin.

---

# 26. Stability Principles

The following principles should remain stable even as the implementation evolves.

### Principle 1 — Core owns engineering truth

No UI component becomes an alternative engineering authority.

### Principle 2 — Controller is the application boundary

UI services request operations through established application pathways.

### Principle 3 — Qt has one boundary

PySide6 access is centralized through `ui.core.qt`.

### Principle 4 — UI state is not engineering state

Selection, tools, navigation, zoom, and interaction state remain separate from engineering truth.

### Principle 5 — Graphics are projections

`QGraphicsItem` objects visualize state; they do not own it.

### Principle 6 — Commands represent intent

Commands do not bypass Core validation.

### Principle 7 — Registries remain focused

Infrastructure should remain modular rather than becoming a universal object manager.

### Principle 8 — Plugin loading is explicit

Concrete plugin imports and lifecycle remain controlled.

### Principle 9 — Core remains headless

No Qt dependency may leak into the engineering Core.

### Principle 10 — Infrastructure should remain replaceable

Concrete UI implementations may evolve without changing engineering architecture.

---

# 27. Development and Freeze Process

UI Core development follows the GridForge subsystem methodology:

```text
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
```

A defect should be corrected at the layer where the architectural responsibility belongs.

Downstream workarounds should not be used to hide an upstream contract violation.

---

# 28. Definition of Done for UI Core

Before a UI Core component is considered stable, it should satisfy:

* [ ] Clear ownership boundary
* [ ] Explicit public contract
* [ ] No engineering state duplication
* [ ] No inappropriate Core dependencies
* [ ] No direct Qt imports outside the Qt boundary
* [ ] Deterministic behavior
* [ ] Meaningful error handling
* [ ] Unit-test coverage
* [ ] Integration-test coverage where applicable
* [ ] No unnecessary global state
* [ ] No hidden lifecycle behavior
* [ ] No circular dependency introduced
* [ ] Documentation updated
* [ ] Architectural audit completed
* [ ] Regression tests passing

---

# 29. Package Philosophy

The `ui/core/` package should remain intentionally boring.

That is a feature.

It should provide the infrastructure that makes the rest of the UI predictable:

```text
Stable Contracts
       +
Focused Services
       +
Explicit Dependencies
       +
Controlled Qt Boundary
       +
Authoritative Controller/Core
       =
Predictable GridForge UI
```

The package should not contain clever shortcuts that make individual features easier at the expense of architectural integrity.

---

# 30. Final Architecture

The final intended relationship is:

```text
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
```

The UI Core is therefore:

* foundational, but not universal;
* shared, but not state-owning;
* powerful, but not authoritative;
* extensible, but contract-driven;
* Qt-aware, but isolated from the engineering Core.

---

# 31. Guiding Principle

The GridForge V2 UI Core follows one central rule:

> **Provide shared GUI infrastructure without becoming a second engineering core.**

Engineering truth belongs to `core/`.

Application workflow belongs to Controllers.

UI infrastructure belongs to `ui/core/`.

Visualization belongs to the UI presentation layers.

This separation is what allows GridForge to evolve from an ETAP-like graphical interface into a broader engineering workspace without compromising the integrity of its digital-twin architecture.

---

**GridForge V2 UI Core**

*Shared infrastructure. Explicit contracts. Deterministic composition. One authoritative engineering core.*
