# GridForge V2 — Phase 7.1 Bus Vertical Slice Design

**Date:** 2026-09-04  
**Target commit:** `119efe4d6b25e8080770b4be1d54b7c4bb1d53c3`  
**Scope:** First Phase 7 integration slice: Bus creation from UI interaction through Application, Core mutation, and read/event projection.

## Goal

Make Bus placement the first fully truthful UI → UI-Core → Application → Core vertical slice while correcting stale architectural seams encountered on that path.

## Frozen Architecture

Mutation:

```text
UI → UI Core → Application Command → Application.execute()
    → Application CommandManager → Handler → Service → Core Network
```

Read/event:

```text
Core mutation → Application event/result → UI-Core adapter
    → UI update bus → SLD/read-model synchronization → canvas projection
```

SLD remains a presentation/document layer. It does not become the electrical model and does not call Core or Network directly.

## Current Evidence

At the target commit, `Application.execute()` is already the public headless mutation facade. It validates a `Command`, delegates to the Application command manager, publishes `NetworkChanged` after successful execution, and exposes immutable read models. The existing `CreateBusCommand` carries `bus_id`, `name`, `nominal_voltage_kv`, `voltage_pu`, `angle_deg`, `frequency_hz`, and `in_service`.

The current `Controller` and UI `CommandManager` still document and implement the obsolete `Controller → Core.command_manager` route. `main.py` constructs the canonical Application but attaches it dynamically as `controller.gridforge_application`. `CanvasComposer` currently composes tools without a command manager. `BusTool` constructs `CreateBusCommand` with obsolete keyword arguments (`voltage`, `angle`).

The Application Bus handler and Bus-specific ModelService already form a valid Application → Core Bus path: the handler forwards the authoritative command payload to the service, the service constructs `Bus`, calls `Network.add_bus()`, records transaction undo, and returns an `ApplicationResult`.

## Design Decisions

### 1. Application is the sole mutation boundary

The UI must never reach `Core.command_manager`, `Network`, or Core model objects. The UI-facing command facade will delegate to an injected canonical `Application` object.

The existing Application command manager remains authoritative for validation, handler resolution, transaction/history semantics, undo, and redo. No second command-history implementation will be introduced.

### 2. Controller becomes UI coordination state, not Core command gateway

The Controller may retain UI-level state such as requested tool and presentation/application selection, but Bus mutation must not depend on Controller access to Core command infrastructure.

The migration will change only the Controller contract required by the Bus path. Unrelated Controller cleanup is deferred.

### 3. One UI-Core command facade instance is injected into tools

`ToolBase` already accepts `command_manager` and routes `execute_command()` through it. The composition root will supply an Application-backed UI command facade to the Bus tool instead of `None`.

The tool remains unaware of Core and should not import or call `Application.execute()` directly.

### 4. BusTool uses the authoritative command contract

BusTool will construct `CreateBusCommand` using its actual signature. The current placement coordinates are interaction state only unless the Application/Core model contract explicitly provides a presentation-position field. The first slice will not invent a domain position field merely to preserve UI coordinates.

If the existing SLD projection contract requires an ID-to-position association, that association remains presentation-owned and will be handled by the existing SLD document/projection boundary rather than added to `CreateBusCommand`.

### 5. Event propagation must be verified end-to-end

A successful `Application.execute()` already publishes `NetworkChanged`. The slice will verify that this event reaches the existing UI update boundary and SLD synchronization path. If the existing UI-Core adapter is incomplete, the minimal adapter correction required by Bus creation will be made in this slice.

No replacement event system will be introduced.

### 6. Tool-manager seam is corrected only as required

The selected runtime ToolManager is `ui.core.tool_manager.ToolManager`, while CanvasComposition currently calls a broader registration API associated with the parallel tool-manager design. The Bus slice will correct the registration/injection seam necessary for the selected runtime path, without reviving the parallel ToolManager architecture.

## Components and Responsibilities

### `ui/core/command_manager.py`

UI-facing facade backed by the canonical Application. It forwards commands and command-state operations without inspecting command internals or accessing Core.

### `ui/core/controller.py`

UI coordination boundary. It must no longer be the authoritative path to Core command execution for Bus creation.

### `main.py` / `ui/canvas/canvas_composition.py`

Composition only. They create and connect the already-defined Application, UI-Core command facade, Controller, ToolManager, SelectionManager, SnapSystem, and BusTool. They do not implement domain behavior.

### `ui/tools/bus_tool.py`

Captures user placement intent, snaps the position, creates the authoritative Application command, and submits it through the injected command facade. It does not mutate Core or render graphics.

### `core/application/commands/model_commands.py`

Existing `CreateBusCommand` contract remains authoritative; no architectural redesign is required.

### `core/application/command_handlers.py`

Existing `CREATE_BUS` handler remains the Application orchestration boundary. Its current payload-to-service mapping will be verified by tests.

### `core/application/services/bus_model_service.py`

Existing Bus creation service remains responsible for constructing the Core Bus, registering it through `Network.add_bus()`, and recording transaction undo.

### UI update / SLD path

The existing Application event → UI update boundary → SLD read synchronization → canvas projection path is preserved and tested. No Core object is introduced into SLD projection.

## Data Flow

```text
Mouse release
    │
    ▼
BusTool
    │  snapped position is transient UI intent
    │
    ▼
CreateBusCommand
    │
    ▼
UI-Core CommandManager
    │
    ▼
Application.execute()
    │
    ▼
Application CommandManager
    │
    ▼
CREATE_BUS handler
    │
    ▼
Bus ModelService
    │
    ▼
Network.add_bus(Bus)
    │
    ├── transaction undo registration
    │
    └── successful ApplicationResult
             │
             ▼
      NetworkChanged
             │
             ▼
       UI-Core update adapter
             │
             ▼
          SLD sync
             │
             ▼
        canvas projection
```

## Error Handling

- Invalid commands remain rejected by the Application command boundary.
- Unregistered command types remain rejected by the Application CommandManager.
- Bus ID conflicts remain handled by the existing service validation.
- Transaction rollback remains owned by the existing Application transaction path.
- Tool execution must fail clearly if its command manager is not configured; composition must therefore guarantee configuration for the Bus tool.
- No UI fallback may directly mutate Network/Core when Application execution fails.

## Testing Strategy

The slice requires tests at four levels:

1. **UI-Core command facade test** — verifies a command is forwarded to Application and that Core is never accessed directly.
2. **BusTool test** — verifies snapped mouse release creates `CreateBusCommand` with the authoritative field names/defaults and submits it through the injected facade.
3. **Application Bus integration test** — verifies `CreateBusCommand` reaches the registered handler, creates a Bus in Network, returns success, and produces the expected Application event.
4. **Composition/event integration test** — verifies the Bus tool receives the Application-backed command facade and the successful mutation reaches the existing SLD/UI update path.

Tests must use test doubles or the existing composition infrastructure; they must not weaken the architectural boundary merely to make assertions easier.

## Explicit Non-Goals

- No activation of the other equipment tools.
- No new equipment commands.
- No redesign of Network topology.
- No generic selection-system migration unless directly required by Bus creation.
- No SLD domain/electrical ownership.
- No resurrection of `Core.command_manager` as a UI integration boundary.
- No unrelated cleanup discovered during implementation.

## Completion Gate

Phase 7.1 is complete only when the Bus vertical slice is executable and testable through the frozen architecture, the stale mutation seams encountered on that path have been corrected, and verification demonstrates that the UI never directly mutates or commands Core.
