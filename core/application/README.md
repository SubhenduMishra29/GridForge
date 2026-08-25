# GridForge V2 — Application Layer

**Author:** Subhendu Mishra
**Status:** **FROZEN**
**Layer:** Headless Application Layer
**Path:** `core/application/`

---

## 1. Purpose

The GridForge V2 Application Layer is the headless orchestration boundary between external consumers and the authoritative GridForge Core.

It converts application intent into controlled Core mutations through commands, handlers, application services, transactions, and history.

The Application Layer does **not** own electrical truth.

The Core remains authoritative for:

* electrical objects;
* equipment;
* terminals;
* topology;
* electrical validity;
* network state;
* domain invariants.

---

## 2. Architectural Position

```text
External Consumer
       |
       v
   Application
       |
       v
 CommandManager
       |
       v
 Command Handler
       |
       v
   ModelService
       |
       v
      Core
```

Endpoint-bearing commands additionally use:

```text
Command
   |
   v
EndpointReference
   |
   v
EndpointResolver
   |
   v
Canonical Core Endpoint
```

The Application Layer therefore provides controlled orchestration without becoming a second domain model.

---

## 3. Public Entry Point

The public Application facade is:

```python
from core.application import Application
```

`Application` is intentionally thin.

Its responsibility is to expose the Application command-execution boundary to external consumers.

The canonical mutation path is:

```text
Application.execute(command)
        |
        v
CommandManager
        |
        v
Handler
        |
        v
ModelService
        |
        v
Core
```

UI code, plugins, scripts, tests, and other external consumers must not bypass this architecture when performing Application-level mutations.

---

## 4. Composition Root

`bootstrap.py` is the Application composition root.

The canonical construction sequence is:

```text
Core Network
      |
      +----------------------+
      |                      |
      v                      v
ApplicationContext      ModelService
                              |
                              v
                 build_model_command_handlers()
                              |
                              v
                       CommandManager
                              |
                              v
                         Application
```

The authoritative Core Network is supplied by the caller.

Bootstrap does not:

* create a replacement Network;
* duplicate Core state;
* resolve endpoints;
* execute commands;
* create transactions;
* manage history;
* contain UI logic.

The composition root exists only to wire the Application layer together.

---

## 5. ApplicationContext

`ApplicationContext` is the narrow dependency boundary between the Application layer and the Core Network.

Its canonical contract is:

```python
@dataclass(frozen=True)
class ApplicationContext:
    network: Any
```

The context:

* references the authoritative Network;
* does not own the Network;
* does not recreate the Network;
* does not become a service locator;
* does not contain UI state;
* does not contain SLD state;
* does not contain plugin state.

The context is immutable with respect to replacement of its Network reference.

---

## 6. Commands

Commands represent immutable application intent.

They do not execute themselves.

The command flow is:

```text
Command
   |
   v
CommandManager
   |
   v
Registered Handler
   |
   v
Application Service
```

Commands must not:

* mutate Core state;
* contain live Core model objects;
* contain Qt objects;
* contain graphics objects;
* perform endpoint resolution;
* execute application services.

### Current model commands

```text
model.create_bus
model.delete_bus

model.create_line
model.delete_line

model.create_transformer
model.delete_transformer
```

The command package exposes both the command-type constants and the corresponding command classes.

---

## 7. EndpointReference

Commands that operate on network connections use `EndpointReference`.

An `EndpointReference` contains identity information rather than a live Core object.

### Bus identity

A Bus reference is:

```text
kind = BUS
object_id = bus_id
```

Therefore:

```text
Bus identity = Bus ID
```

### Terminal identity

A Terminal reference is:

```text
kind = TERMINAL
equipment_type
equipment_id
terminal_role
```

Therefore:

```text
Terminal identity =
    owning equipment type
    +
    owning equipment ID
    +
    terminal role
```

A Terminal does not require a fabricated global Terminal ID for Application-level resolution.

---

## 8. EndpointResolver

`EndpointResolver` converts an `EndpointReference` into the canonical Core endpoint.

```text
EndpointReference
        |
        v
EndpointResolver
        |
        +---- BUS ------> canonical Bus
        |
        +---- TERMINAL -> canonical Terminal
```

Resolution is read-only.

The resolver does not:

* create endpoints;
* mutate topology;
* modify equipment;
* modify terminals;
* call ModelService;
* access UI;
* access SLD state.

### Terminal resolution invariant

A terminal reference is valid only when:

```text
Referenced equipment exists
        AND
Terminal with requested role exists
        AND
Terminal belongs to that equipment
        AND
Resolution is unambiguous
```

The resolver therefore establishes identity, while Core remains responsible for electrical validity.

---

## 9. Command Handlers

Command handlers translate immutable command payloads into application-service calls.

They are not domain logic.

The canonical model handler registry is constructed through:

```python
build_model_command_handlers(model_service)
```

Handlers:

* receive a command;
* extract immutable command data;
* resolve endpoint references when required;
* call the appropriate Application Service operation;
* return the appropriate Application result.

Handlers do not directly manipulate Core internals.

---

## 10. ModelService

`ModelService` is the Application-layer service responsible for controlled model mutations.

Its canonical dependency is:

```python
ModelService(network)
```

The service sits between command handlers and the Core:

```text
Command Handler
       |
       v
ModelService
       |
       v
Core Public API
```

`ModelService` owns Application-level mutation orchestration and undo registration.

It does not become an alternative Core model.

The Core remains responsible for domain invariants and electrical validity.

---

## 11. CommandManager

`CommandManager` is the central command execution boundary.

Its responsibilities include:

* command lookup;
* command dispatch;
* transaction coordination;
* history integration;
* undo;
* redo;
* command result handling.

The manager does not implement electrical-domain logic.

The manager therefore forms the Application execution boundary:

```text
External Command
       |
       v
CommandManager
       |
       v
Registered Handler
       |
       v
ModelService
       |
       v
Core
```

---

## 12. Transactions

Transactions provide controlled grouping of Application-level mutations.

A transaction is not a replacement for Core domain logic.

The Application transaction boundary coordinates:

```text
Command execution
       |
       v
Mutation
       |
       v
Undo registration
       |
       v
History
```

Transactions must not bypass the command architecture.

---

## 13. History, Undo and Redo

History stores reversible Application operations.

The frozen execution relationship is:

```text
Command
   |
   v
CommandManager
   |
   v
Transaction
   |
   v
History
```

Undo reverses the most recent applicable transaction.

Redo reapplies the corresponding reversible operation according to the established history contract.

History does not own Core state.

It stores the information required to reverse or replay Application-level mutations.

---

## 14. Results

Application operations communicate their outcome through Application result contracts.

Results are not Core domain objects.

They provide a stable boundary for:

* success;
* failure;
* created-object identity;
* operation information;
* external consumers.

The Application facade should not expose internal transaction or handler mechanics to callers.

---

## 15. Core/Application Boundary

The fundamental frozen rule is:

> **Core owns electrical truth. Application owns command orchestration.**

### Core owns

```text
Electrical objects
Equipment
Terminals
Topology
Electrical validity
Domain invariants
Network state
```

### Application owns

```text
Commands
Command dispatch
Handlers
Application services
Endpoint references
Endpoint resolution
Transactions
History
Undo/redo
Composition
```

### UI owns

```text
User interaction
SLD authoring workflows
Canvas state
Visual representation
Selection
Tools
Panels
Rendering
```

The UI must never become the owner of electrical truth.

---

## 16. Mutation Rule

The authoritative mutation path is:

```text
UI / Plugin / Script / External Consumer
                  |
                  v
              Command
                  |
                  v
          CommandManager
                  |
                  v
               Handler
                  |
                  v
            ModelService
                  |
                  v
                Core
```

Direct mutation of Core state from UI or rendering code is prohibited.

Plugins must use the same Application contracts.

---

## 17. Endpoint Ownership Rule

A Terminal belongs to its owning electrical equipment.

Therefore:

```text
Equipment
    |
    +-- Terminal
    +-- Terminal
    +-- Terminal
```

Terminal identity is derived from:

```text
equipment identity + terminal role
```

The Application layer does not create an independent electrical ownership model for terminals.

This maintains consistency with the Core equipment/terminal architecture.

---

## 18. Bus and Terminal Connection Model

The Application layer treats connection endpoints uniformly through `EndpointReference`.

Therefore a connection command can conceptually carry:

```text
Bus <-> Bus
Bus <-> Terminal
Terminal <-> Bus
Terminal <-> Terminal
```

provided that the Core domain model and the applicable Application service permit that topology.

The Application layer identifies endpoints.

The Core determines whether the resulting electrical topology is valid.

---

## 19. What the Application Layer Must Never Do

The following are explicitly outside the Application Layer's authority:

* electrical calculations;
* power-flow solving;
* short-circuit solving;
* protection calculations;
* electrical topology validity rules;
* SLD rendering;
* Qt operations;
* graphics-scene mutation;
* symbol management;
* canvas ownership;
* direct manipulation of Core internals;
* creation of alternate electrical state.

---

## 20. Dependency Direction

The intended dependency direction is:

```text
UI / Plugins
     |
     v
Application
     |
     v
Core
```

Never:

```text
Core
  |
  v
Application
```

The Core must remain independent of the Application layer.

Likewise, the Core must not import:

* Qt;
* UI modules;
* SLD modules;
* plugin modules;
* Application command modules.

---

## 21. Frozen Package Structure

```text
core/application/
│
├── __init__.py
├── application.py
├── bootstrap.py
├── command.py
├── command_handlers.py
├── command_manager.py
├── context.py
├── endpoint_reference.py
├── endpoint_resolver.py
├── errors.py
├── events.py
├── history.py
├── results.py
├── reversible.py
├── transaction.py
│
├── commands/
│   ├── __init__.py
│   └── model_commands.py
│
└── services/
    └── model_service.py
```

The package initializer:

```python
from .application import Application

__all__ = [
    "Application",
]
```

The commands package separately exposes the command constants and command classes.

---

## 22. Frozen Contracts

The following contracts are frozen together:

```text
Application
ApplicationContext
Bootstrap
Command
CommandManager
Command Handlers
ModelService
EndpointReference
EndpointResolver
Transaction
History
Reversible operation
Application Results
Model Commands
```

These contracts must be changed as an architectural revision, not by isolated local patching.

---

## 23. Change Policy

After this freeze:

### Allowed

* bug fixes that preserve the frozen contract;
* implementation optimizations;
* additional tests;
* documentation improvements;
* additional commands that follow the established command architecture;
* additional handlers/services that follow the established boundaries.

### Requires explicit architecture review

* changing endpoint identity;
* changing Terminal ownership;
* changing CommandManager semantics;
* changing undo/redo semantics;
* bypassing ModelService;
* introducing direct Core mutation from handlers;
* making Application own domain state;
* adding UI dependencies;
* changing the Core/Application dependency direction;
* changing the transaction/history contract.

---

## 24. Final Frozen Principle

The Application Layer is **not the electrical model**.

It is the controlled orchestration layer that turns external intent into valid Core mutations.

The final principle is:

```text
Intent
  |
  v
Command
  |
  v
CommandManager
  |
  v
Handler
  |
  v
ModelService
  |
  v
Core
```

while endpoint identity follows:

```text
EndpointReference
        |
        v
EndpointResolver
        |
        v
Canonical Core Endpoint
```

and the Core remains the sole authority for electrical truth.

**GridForge V2 Application Layer: FROZEN.**
