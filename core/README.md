# GridForge V2 — Core

**Author:** Subhendu Mishra

## 1. Purpose

`core/` is the **headless engineering and domain authority** of GridForge V2.

Core owns the authoritative engineering state, domain semantics, electrical topology, control, protection, analysis, numerical solving, simulation, measurement, and validation contracts.

Core does **not** own presentation.

The Core layer must remain usable without:

- Qt
- PySide6
- UI widgets
- graphics scenes
- canvas objects
- renderers
- dock layouts
- UI plugins
- application-shell presentation state

---

## 2. Architectural Position

GridForge V2 separates application orchestration from domain authority.

```text
                    UI / Plugins
                         │
                         ▼
                core/application/
                         │
                  Commands / Services
                         │
                         ▼
              ┌─────────────────────┐
              │        CORE         │
              │ Domain Authority    │
              └─────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
      Model           Network          Domains
                                         │
                 ┌───────────────────────┼────────────────────┐
                 │                       │                    │
                 ▼                       ▼                    ▼
              Control               Protection           Measurement
                 │                       │                    │
                 └───────────────────────┼────────────────────┘
                                         │
                                         ▼
                                      Analysis
                                         │
                                         ▼
                                       Solver
                                         │
                                         ▼
                                     Simulation
                                         │
                                         ▼
                                     Validation
````

### Core principle

> **Application coordinates Core. Core owns engineering meaning.**

The Application layer may invoke Core capabilities through controlled public APIs, commands, and services.

Core must never depend on Application presentation state.

---

# 3. Core Responsibilities

Core is responsible for the following authoritative capabilities.

| Package        | Responsibility                                                |
| -------------- | ------------------------------------------------------------- |
| `base/`        | Shared foundational contracts and numerical/domain primitives |
| `model/`       | Authoritative physical and engineering model                  |
| `network/`     | Electrical network assembly and topology                      |
| `measurement/` | Measurement-domain state and semantics                        |
| `control/`     | Control-domain state, signals, logic and control execution    |
| `protection/`  | Protection devices, relays, breakers and coordination         |
| `analysis/`    | Engineering studies and analysis orchestration                |
| `solver/`      | Numerical problem solving                                     |
| `simulation/`  | Time/runtime simulation                                       |
| `validation/`  | Domain and engineering validation                             |
| `application/` | Headless application orchestration boundary                   |

---

# 4. Model Authority

`core/model/` is the authoritative representation of engineering objects.

Model answers:

> **What physically exists in the engineering system?**

Model owns:

* stable object identity;
* engineering object properties;
* equipment models;
* model-level validation;
* model collections and registries;
* authoritative physical/domain state.

Model does not own:

* UI representation;
* SLD symbols;
* graphics coordinates;
* rendering;
* canvas interaction;
* application presentation state;
* numerical solver execution.

A visual representation of an engineering object is therefore never the engineering object itself.

---

# 5. Network Authority

`core/network/` represents the assembled electrical network.

Network answers:

> **How are the authoritative electrical objects assembled and electrically connected?**

Network owns:

* network membership;
* electrical topology;
* bus indexing;
* network connectivity;
* network-level electrical representations;
* network-derived state;
* network assembly services.

Network does not replace Model as the source of truth.

The relationship is:

```text
Model
  │
  ▼
Network
```

Model owns the engineering object.

Network assembles those objects into an electrical network.

---

# 6. Control

`core/control/` is a **frozen V2 Core domain**.

Control owns:

* control state;
* control signals;
* control limits;
* controller semantics;
* dynamic control contracts;
* logic components;
* logic execution;
* signal connections;
* execution dependencies;
* control events and results.

The Control module is headless.

It must not depend on:

* Qt;
* UI;
* SLD;
* canvas;
* renderers;
* graphics items;
* UI plugins.

## Frozen Logic Contract

Logic components implement the common Logic Control contract.

The Logic Engine owns:

* component registration;
* signal connections;
* explicit execution dependencies;
* connection-derived dependencies;
* deterministic execution ordering;
* signal propagation;
* state propagation;
* evaluation;
* stabilization;
* events;
* result snapshots.

### Explicit vs derived dependencies

These are distinct concepts.

```text
Explicit dependency:

A ─────────────► B
```

```text
Signal connection:

A.OUT ─────────► B.IN
```

A signal connection may create a **connection-derived execution dependency**:

```text
A.OUT ─────────► B.IN
 │
 └─────────────► A → B
```

Disconnecting the signal connection must remove only the derived dependency.

An independently registered explicit dependency must remain.

This distinction is part of the frozen Control contract.

---

# 7. Protection

`core/protection/` owns protection-domain semantics.

Protection is responsible for:

* relays;
* breakers;
* protection settings;
* protection curves;
* trip logic;
* coordination;
* protection-domain state;
* protection analysis contracts.

Protection must remain independent of UI representation.

A relay symbol, breaker symbol, or protection panel is a presentation representation and is not the authoritative protection object.

---

# 8. Measurement

`core/measurement/` owns measurement-domain semantics.

Measurement may provide:

* measurement definitions;
* measurement values;
* measurement state;
* acquisition abstractions;
* engineering-unit semantics;
* measurement validation.

Measurement must remain headless.

---

# 9. Analysis

`core/analysis/` owns engineering-study semantics.

Analysis answers:

> **What engineering study is being performed and what results are being produced?**

Analysis may coordinate:

* study inputs;
* study configuration;
* study execution;
* result interpretation;
* engineering diagnostics.

Analysis does not become the numerical solver.

---

# 10. Solver

`core/solver/` owns numerical computation.

Solver answers:

> **How is the mathematical problem solved?**

Solver owns numerical algorithms and computational procedures required by Core studies.

Solver must not contain:

* UI behavior;
* canvas state;
* SLD rendering;
* application presentation logic.

The architectural relationship is:

```text
Analysis
   │
   ▼
Solver
```

Analysis defines the engineering problem.

Solver performs the numerical computation.

---

# 11. Simulation

`core/simulation/` owns simulation execution semantics.

Simulation may coordinate:

* simulation time;
* execution cycles;
* dynamic state;
* simulation events;
* simulation results;
* runtime study progression.

Simulation must use the established Core domain contracts rather than duplicating domain truth.

---

# 12. Validation

`core/validation/` owns validation and verification semantics.

Validation may operate across Core domains to determine whether:

* models are structurally valid;
* topology is valid;
* connections are valid;
* study inputs are valid;
* control configurations are valid;
* protection configurations are valid;
* solver inputs are valid;
* simulation configurations are valid.

Validation reports problems.

It does not become the owner of the data being validated.

---

# 13. Application Boundary

`core/application/` is the **headless Application orchestration boundary**.

Application owns:

* commands;
* command handlers;
* application services;
* command execution;
* command history;
* reversible operations;
* application events;
* application results;
* controlled dependency context;
* composition/bootstrap infrastructure.

Application does not own:

* domain state;
* physical models;
* electrical topology;
* solver internals;
* UI state;
* Qt;
* canvas state;
* rendering;
* plugin lifecycle.

The Application layer coordinates Core through explicit public contracts.

```text
Application
     │
     ├── Command
     ├── Handler
     └── Service
            │
            ▼
          Core
```

---

# 14. ApplicationContext

`ApplicationContext` is the controlled dependency boundary between Application and Core.

It contains already-constructed Core capabilities.

The Composition Root creates Core first and then constructs the Application context.

```text
Composition Root
       │
       ├── construct Core
       │
       ▼
ApplicationContext
       │
       ▼
Application
```

`ApplicationContext` is not:

* a service locator;
* a global state container;
* a UI context;
* a plugin registry;
* a presentation-state object.

Additional dependencies should be added explicitly only when required by an actual Application contract.

---

# 15. Composition Root

Application bootstrap is responsible for composition.

Conceptually:

```text
Core objects
     │
     ▼
ApplicationContext
     │
     ▼
CommandManager
     │
     ▼
Command handlers / Services
     │
     ▼
Application
```

The Composition Root may construct the runtime graph.

It must not move domain semantics out of Core.

---

# 16. Commands and Mutation

Application commands are the controlled mutation boundary.

The preferred direction is:

```text
UI / Plugin
     │
     ▼
Application Command
     │
     ▼
Command Handler / Service
     │
     ▼
Core Public API
     │
     ▼
Authoritative Core State
```

UI and plugins must not bypass this boundary by directly mutating Core internals.

Core public APIs remain authoritative.

---

# 17. Plugin Boundary

Plugins are extensions of GridForge, not owners of Core state.

The preferred interaction is:

```text
Plugin
  │
  ▼
Application API
  │
  ▼
Commands / Services
  │
  ▼
Core
```

Plugins may provide:

* engineering platforms;
* equipment types;
* analysis services;
* control services;
* canvases;
* tools;
* panels;
* renderers;
* property editors;
* commands;
* reports.

However:

> **Plugins must use controlled public contracts and must not bypass the command/application architecture to directly mutate Core internals.**

Core must not depend on UI plugins.

---

# 18. SLD Boundary

The Single Line Diagram is a **presentation projection** of Core engineering state.

```text
Core Model / Network
        │
        ▼
      SLD UI
        │
        ▼
   Visual symbols
```

The SLD symbol is not the electrical object.

The canvas is not the electrical truth.

The graphics scene is not the topology authority.

The UI may translate user interaction into commands and domain-neutral values.

Core owns the resulting engineering meaning.

---

# 19. Forbidden Dependencies

The following dependencies are forbidden inside Core:

```text
core ─X─► PySide6
core ─X─► Qt widgets
core ─X─► QGraphicsScene
core ─X─► QGraphicsItem
core ─X─► SLD renderer
core ─X─► canvas
core ─X─► dock widgets
core ─X─► UI controllers
core ─X─► UI plugins
core ─X─► presentation state
```

Core may expose data and contracts that the UI consumes.

Core must not consume presentation implementation.

---

# 20. Legacy Controller

The historical:

```text
core/controller.py
```

is **not part of the new V2 Application architecture**.

The new architecture uses:

```text
core/application/
```

as the Application coordination boundary.

Therefore `core/controller.py` must not be expanded into another application architecture.

Its eventual fate is:

1. audit repository references;
2. migrate legitimate consumers to the new Application boundary if necessary;
3. remove the obsolete controller.

This is a reconciliation task, not a new architectural feature.

---

# 21. Dependency Direction

The intended dependency direction is:

```text
UI / Plugins
      │
      ▼
Application
      │
      ▼
Core
      │
      ├── Model
      ├── Network
      ├── Control
      ├── Protection
      ├── Measurement
      ├── Analysis
      ├── Solver
      ├── Simulation
      └── Validation
```

Core domains may depend on lower-level Core contracts where architecturally justified.

They must not depend upward on Application or UI.

---

# 22. Source of Truth

GridForge V2 follows this rule:

> **Authoritative engineering state exists in Core.**

Examples:

```text
Equipment truth       → Model
Electrical topology   → Network
Control truth         → Control
Protection truth      → Protection
Measurement truth     → Measurement
Study truth           → Analysis
Numerical truth       → Solver
Simulation state      → Simulation
Validation result     → Validation
Application workflow  → Application
Visual representation → UI
```

No UI representation may become a second source of engineering truth.

---

# 23. Error Handling

Core components must use explicit domain/application contracts for errors.

Do not use:

```python
print(...)
```

as a substitute for Core error propagation.

Diagnostics must be structured where the surrounding contract requires them.

Exceptions must identify the violated domain contract clearly.

---

# 24. Determinism

Core operations should be deterministic wherever the engineering semantics permit.

This includes:

* stable object identity;
* deterministic registration;
* deterministic network indexing;
* deterministic logic evaluation order;
* deterministic command behavior;
* reproducible analysis/solver inputs;
* stable validation results.

Non-deterministic behavior must not be introduced merely for UI convenience.

---

# 25. Testing Boundary

Tests should validate Core contracts independently from UI.

Core tests must not require:

* Qt application startup;
* MainWindow;
* graphics scenes;
* canvas initialization;
* UI plugins.

Application tests may test command orchestration using constructed Core capabilities.

UI tests belong outside Core.

---

# 26. Freeze Policy

The Core architecture is progressively frozen by subsystem.

Current status:

```text
Control
  → ARCHITECTURE / CONTRACT FROZEN
```

Other Core domains remain subject to reconciliation until their actual repository implementation is aligned with the V2 architecture.

Once a Core subsystem is frozen:

> **Implementation defects may be corrected against the frozen contract, but the architectural contract must not be silently redesigned.**

Any architectural change requires an explicit new architecture decision.

---

# 27. Core V2 Rules

The following rules are authoritative.

### Rule 1

Core owns engineering meaning.

### Rule 2

Application coordinates Core.

### Rule 3

UI presents and edits through controlled Application/Core contracts.

### Rule 4

Canvas is never authoritative for electrical truth.

### Rule 5

SLD symbols are representations, not electrical objects.

### Rule 6

Plugins extend the platform through public contracts.

### Rule 7

Core never depends on UI.

### Rule 8

Control remains a Core domain and is already frozen.

### Rule 9

Numerical computation belongs to Solver and appropriate domain services, not UI.

### Rule 10

No legacy controller may be allowed to recreate the old application architecture.

---

# 28. Target Core Tree

The intended V2 Core organization is:

```text
core/
├── README.md
│
├── __init__.py
│
├── base/
│
├── model/
│
├── network/
│
├── measurement/
│
├── control/
│
├── protection/
│
├── analysis/
│
├── solver/
│
├── simulation/
│
├── validation/
│
└── application/
    ├── __init__.py
    ├── application.py
    ├── bootstrap.py
    ├── command.py
    ├── command_handlers.py
    ├── command_manager.py
    ├── context.py
    ├── errors.py
    ├── events.py
    ├── history.py
    ├── results.py
    ├── reversible.py
    ├── commands/
    └── services/
```

The exact contents of each domain package remain governed by its own frozen contract and actual repository reconciliation.

---

# 29. Architectural Freeze Statement

**GridForge V2 Core is a headless engineering authority.**

Its public architecture is:

```text
Application
    ↓
Core contracts
    ↓
Engineering domains
```

The Core layer must remain independent of presentation.

The Application layer is the controlled orchestration boundary.

The Control subsystem is frozen and must be treated as a stable Core domain.

Legacy architectural concepts must be removed or reconciled rather than expanded.

**This document defines the intended Core V2 architecture and supersedes legacy Core documentation where the two conflict.**

```
```
