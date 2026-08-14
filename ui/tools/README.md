````markdown
# GridForge V2 — UI Tools

## Purpose

The `ui/tools/` package contains the concrete interaction tools used by
the GridForge canvas.

Tools translate user interaction into application-level requests while
remaining independent of rendering and Core implementation details.

The package is intentionally kept separate from:

- `ToolManager` — tool lifecycle and active-tool management
- `InteractionManager` — Qt event routing, coordinate mapping, snapping,
  and preview infrastructure
- `RenderSystem` — model-to-visual synchronization
- `Controller` — application orchestration and mutation boundary
- `Core` — authoritative electrical model and domain state

---

## Current Architecture

```text
                    Qt Input
                       │
                       ▼
              InteractionManager
                       │
             ┌─────────┴─────────┐
             │                   │
      coordinate mapping     event routing
             │                   │
             └─────────┬─────────┘
                       ▼
                   ToolManager
                       │
                  Active Tool
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   SelectTool       BusTool        LineTool
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                  Controller
                       │
                       ▼
                Command / Core
                       │
                       ▼
                 Domain Events
                       │
                       ▼
                 RenderSystem
                       │
                       ▼
                 Canvas Items
````

The important architectural rule is:

> Tools express interaction intent. They do not own rendering or
> authoritative application state.

---

# Built-in Tools

## SelectTool

### Purpose

Handles selection and movement interaction.

### Responsibilities

* select canvas objects;
* support multi-selection;
* maintain temporary selection state;
* initiate movement interaction;
* request model-level position changes through the application boundary.

### Does Not

* own the scene;
* render objects;
* own Core state;
* perform electrical calculations;
* directly manipulate permanent graphics.

---

## BusTool

### Purpose

Places electrical buses on the canvas.

### Interaction

```text
Mouse Click
    │
    ▼
InteractionManager
    │
    ▼
SnapSystem
    │
    ▼
BusTool
    │
    ▼
Controller
    │
    ▼
Core / Command
    │
    ▼
Domain Event
    │
    ▼
RenderSystem
```

### Responsibilities

* resolve the placement position;
* use centralized snapping;
* prevent invalid duplicate placement;
* request bus creation through Controller;
* maintain only transient interaction state.

---

## LineTool

### Purpose

Creates electrical connections between existing buses.

### Interaction

```text
First Click
    │
    ▼
Resolve Bus
    │
    ▼
Store Start Bus
    │
    ▼
Mouse Move
    │
    ▼
SnapSystem
    │
    ▼
PreviewLayer
    │
    ▼
Second Click
    │
    ▼
Resolve Destination Bus
    │
    ├── Same Bus ──► Reject
    │
    ├── Duplicate ─► Reject
    │
    ▼
Controller
    │
    ▼
Core / Command
    │
    ▼
Domain Event
    │
    ▼
RenderSystem
```

### Responsibilities

* maintain two-click interaction state;
* resolve buses through SnapSystem;
* request temporary preview;
* reject self-connections;
* reject duplicate connections;
* request persistent line creation.

---

# Tool Contract

All concrete tools should follow a common conceptual contract.

```python
class Tool:
    tool_id = "..."

    def activate(self):
        ...

    def deactivate(self):
        ...

    def reset(self):
        ...

    def mouse_press(self, event):
        ...

    def mouse_move(self, event):
        ...

    def mouse_release(self, event):
        ...

    def key_press(self, event):
        ...
```

Not every tool must implement meaningful behavior for every method,
but the ToolManager should be able to interact with tools consistently.

---

# Registration

Tools are registered through the centralized ToolRegistry.

Example:

```python
@register_tool("line")
class LineTool:
    ...
```

The tool package imports the built-in tools:

```python
from ui.tools.select_tool import SelectTool
from ui.tools.bus_tool import BusTool
from ui.tools.line_tool import LineTool
```

Importing the modules causes their registration decorators to execute.

The registry remains responsible for:

* tool identity;
* duplicate protection;
* registration validation;
* tool lookup;
* plugin/tool discovery rules.

The tool package must not implement a second registry.

---

# Tool Lifecycle

Tool instances are not created by the package itself.

The intended lifecycle is:

```text
ToolRegistry
     │
     ▼
ToolManager
     │
     ├── create tool instance
     │
     ├── activate()
     │
     ├── route events
     │
     ├── deactivate()
     │
     └── dispose/reset
```

Only one active primary canvas tool should normally receive interaction
events at a time.

Temporary state must be cleared when a tool is deactivated.

---

# Interaction Ownership

The tools must not duplicate infrastructure already provided by
`InteractionManager`.

## InteractionManager owns

* Qt mouse event routing;
* keyboard event routing;
* scene-coordinate conversion;
* current cursor position;
* PreviewLayer;
* centralized SnapSystem access;
* interaction context.

## Tools own

* tool-specific interaction state;
* tool-specific interpretation of user input;
* requesting application mutations;
* tool-specific validation that belongs to the interaction layer.

This prevents different tools from implementing inconsistent snapping,
coordinate conversion, and event-routing rules.

---

# Rendering Boundary

Tools never create permanent graphics.

For example, `LineTool` may request:

```text
PreviewLayer.show_line(...)
```

for temporary interaction feedback.

It must never create:

```python
LineItem(...)
```

or directly insert graphics into the scene.

Permanent rendering follows:

```text
Tool
  ↓
Controller
  ↓
Core mutation
  ↓
Domain Event
  ↓
RenderSystem
  ↓
Graphics Item
```

This preserves the rule:

> Core state is authoritative; the canvas is a representation.

---

# Mutation Boundary

Tools should not bypass the application mutation boundary.

Preferred:

```python
controller.create_bus(...)
controller.create_line(...)
```

rather than:

```python
controller.model.add_bus(...)
controller.model.graph.add_line(...)
```

The Controller/Command architecture is responsible for determining the
final mutation path.

This is important because future mutations may require:

* command creation;
* validation;
* undo/redo;
* event generation;
* revision tracking;
* transaction handling;
* collaboration;
* logging.

Tools should therefore express intent rather than implement mutation
mechanics.

---

# Current Tool Set

| Tool         | Status      | Purpose                |
| ------------ | ----------- | ---------------------- |
| `SelectTool` | V2 baseline | Selection and movement |
| `BusTool`    | V2 baseline | Bus placement          |
| `LineTool`   | V2 baseline | Bus-to-bus connection  |

---

# Future Tool Roadmap

The following tools are candidates for future GridForge releases.

## Phase 1 — Core Canvas Editing

### TransformerTool

Create and configure transformer topology.

Expected interaction:

```text
Select connection points
        ↓
Place transformer
        ↓
Controller
        ↓
Core
```

Transformer-specific electrical parameters must remain Core-owned.

---

### GeneratorTool

Place generators and connect them to the network.

Future responsibilities may include:

* generator placement;
* connection validation;
* generator type selection;
* initial parameter entry.

Electrical behavior remains in Core.

---

### LoadTool

Place electrical loads.

Potential future capabilities:

* constant-P load;
* constant-Q load;
* ZIP load;
* motor load;
* load templates.

The tool should only collect interaction intent.

---

### BreakerTool

Create and manipulate circuit breakers.

Future integration:

```text
BreakerTool
     │
     ▼
Controller
     │
     ▼
Breaker Model
     │
     ▼
Protection / Control
```

Breaker operational state must remain outside the tool.

---

## Phase 2 — Electrical Equipment

Potential tools:

* `BusbarTool`
* `CableTool`
* `TransmissionLineTool`
* `ShuntTool`
* `CapacitorTool`
* `ReactorTool`
* `MotorTool`
* `InverterTool`
* `BatteryTool`
* `PVTool`

These should be introduced only when the corresponding Core models
and topology contracts are finalized.

The UI must not invent domain models merely to support a tool.

---

# Phase 3 — Protection and Measurement

Once the underlying domains are mature:

### MeasurementPointTool

Create a semantic measurement location associated with authoritative
network topology.

It must not introduce a parallel wiring topology.

---

### MeasurementChannelTool

Configure measurement channels associated with the measurement
infrastructure.

---

### ProtectionElementTool

Configure protection elements associated with network equipment.

Potential specializations:

* overcurrent;
* directional;
* distance;
* differential;
* earth-fault.

The tool should remain an interaction layer over the Protection domain.

---

### RelayTool

Future relay configuration interaction.

The relay itself belongs to the Protection domain.

---

# Phase 4 — Control and Simulation

Future tools may include:

* `ControlTool`
* `SwitchControlTool`
* `ScenarioTool`
* `SimulationSetupTool`
* `EventTool`
* `FaultTool`

These should integrate with the existing Simulation and Control
architecture rather than implementing simulation behavior inside the UI.

---

# Phase 5 — Advanced Engineering Interaction

Future possibilities include:

* contingency definition tools;
* fault-location tools;
* relay-coordination interaction;
* TCC interaction tools;
* dynamic simulation event placement;
* transient event tools;
* study-case tools;
* OPF constraint tools.

These should only be implemented after the corresponding Core/Analysis/
Simulation contracts are stable.

---

# Tool Design Rules

Every future tool should follow these rules.

## 1. No direct Qt binding imports

Use:

```python
from ui.core.qt import ...
```

Never:

```python
from PyQt5 ...
from PyQt6 ...
from PySide6 ...
```

---

## 2. No rendering responsibility

A tool must never create or permanently manipulate a graphics item.

---

## 3. No Core ownership

A tool may reference the application boundary but must never become the
owner of domain state.

---

## 4. No local snapping algorithms

All spatial snapping must use the centralized SnapSystem.

---

## 5. No duplicated coordinate conversion

Scene/view coordinate conversion belongs to InteractionManager.

---

## 6. No independent event routing

Qt event routing belongs to InteractionManager.

---

## 7. No direct filesystem or persistence logic

Tools should never save or load projects.

---

## 8. No electrical calculations

Electrical calculations belong to Core/Analysis/Solver/Simulation.

---

## 9. Temporary state only

Interaction state such as:

```text
start_bus
dragging
current_position
preview state
```

may live in the tool.

Persistent engineering state must not.

---

## 10. Reset on deactivation

Every stateful tool must leave no unfinished interaction behind when
deactivated.

---

# Testing Strategy

Each tool should eventually have focused tests.

## SelectTool

Test:

* selection;
* deselection;
* multi-selection;
* activation;
* deactivation;
* reset;
* movement intent;
* invalid interaction.

## BusTool

Test:

* valid placement;
* snapped placement;
* duplicate placement prevention;
* Controller mutation request;
* activation/deactivation;
* reset.

## LineTool

Test:

* start-bus selection;
* destination selection;
* self-connection rejection;
* duplicate-line rejection;
* successful line creation;
* preview updates;
* reset;
* Escape cancellation;
* activation/deactivation.

Tests should verify interaction contracts rather than Qt rendering
implementation details.

---

# Future Architectural Improvements

The current tools are intentionally lightweight. Future work should
consider:

1. A formal `Tool` protocol/base contract.
2. Standardized event/context objects.
3. Stronger Controller command integration.
4. Tool capability metadata.
5. Tool enable/disable predicates.
6. Context-sensitive tool availability.
7. Undo/redo integration through CommandManager.
8. Transactional multi-step tools.
9. Tool cancellation semantics.
10. Tool-specific validation feedback.
11. Keyboard shortcut metadata.
12. Cursor/hover metadata.
13. Tool grouping and categories.
14. Plugin-provided tools.
15. Tool discovery and validation diagnostics.

These should be introduced only when the surrounding architecture
requires them.

---

# Architectural Principle

The long-term GridForge interaction pipeline is:

```text
User
 │
 ▼
Qt
 │
 ▼
InteractionManager
 │
 ▼
ToolManager
 │
 ▼
Active Tool
 │
 ▼
Controller / Command
 │
 ▼
Core
 │
 ▼
Domain Event
 │
 ├───────────────┐
 ▼               ▼
RenderSystem   Other Systems
 │
 ▼
Canvas
```

The central rule is:

> **Tools interpret interaction; Core owns truth; RenderSystem owns
> representation.**

This separation allows GridForge to evolve from basic SLD editing into
a full engineering platform without allowing UI interaction code to
become a second domain model.

```
```
