# ⚡ GridForge V2

### Power-System Digital Twin, Engineering, Simulation & Automation Platform

**Author:** Subhendu Mishra

---

GridForge is a Python-based power-system engineering platform for creating, editing, validating, studying, simulating, documenting, and operating digital representations of electrical power systems.

It is designed as a **one-stop engineering environment for power-system engineers**, while maintaining strict separation between:

- Authoritative electrical engineering truth
- Application orchestration
- User interaction
- Graphical presentation
- Studies and solvers
- Protection
- Control and automation
- Dynamics
- Persistence
- Plugins
- Engineering documentation

> **GridForge V2 is not an SLD-only application.** The Single-Line Diagram is one engineering projection of the underlying digital twin.

---

## 📑 Table of Contents

1. [Architectural Authority](#1-architectural-authority)
2. [Core Architectural Principle](#2-core-architectural-principle)
3. [Architectural Ownership](#3-architectural-ownership)
4. [Application Layer](#4-application-layer)
5. [UI / Application / Core Contract](#5-ui--application--core-contract)
6. [Command Architecture](#6-command-architecture)
7. [Physical Model & Engineering Domains](#7-physical-model--engineering-domains)
8. [SLD Architecture](#8-sld-architecture)
9. [Plugin Architecture](#9-plugin-architecture)
10. [Persistence Architecture](#10-persistence-architecture)
11. [Repository Structure](#11-repository-structure)
12. [Architectural Rules](#12-architectural-rules)
13. [Forbidden Architectural Paths](#13-forbidden-architectural-paths)
14. [Engineering State Ownership](#14-engineering-state-ownership)
15. [Testing Architecture](#15-testing-architecture)
16. [Development Philosophy](#16-development-philosophy)
17. [Guiding Principle](#17-guiding-principle)
18. [What GridForge Is Not](#18-what-gridforge-is-not)

---

## 1. Architectural Authority

The GridForge V2 architecture defined in this document is the **architectural baseline**. No subsystem may bypass ownership boundaries merely because direct access is convenient.

> **Core owns engineering truth. Application owns orchestration. UI owns interaction and presentation.**

```
                    USER / ENGINEER
                           │
                           ▼
                UI / Engineering Workspaces
                           │
                           ▼
                  Controllers / Tools
                           │
                           ▼
                  Immutable Commands
                           │
                           ▼
                 APPLICATION LAYER
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Commands        Transactions      Services
      History         Undo / Redo       Studies
      Lifecycle       Persistence       Events
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    AUTHORITATIVE CORE
                           │
       ┌───────────┬───────┼────────┬───────────┐
       ▼           ▼       ▼        ▼           ▼
     Model      Network  Analysis  Protection  Control
                           │
                           ▼
                         Solvers
                           │
                           ▼
                       Results
                           │
                           ▼
                 APPLICATION EVENTS
                           │
                           ▼
                    READ MODELS
                           │
                           ▼
              UI UPDATE BOUNDARY / BUS
                           │
                           ▼
              UI / Canvas / Projections
```

---

## 2. Core Architectural Principle

GridForge maintains **one authoritative engineering truth**. The Core is the authority for equipment, identities, terminals, electrical properties, topology, connections, engineering relationships, domain validation, studies, calculations, protection decisions, simulation state, and study results.

| ❌ Must never become a second engineering model |
|---|
| The UI |
| The SLD |
| A renderer |
| A plugin |

---

## 3. Architectural Ownership

### Core

The authoritative engineering/domain layer — **no Qt or UI dependencies**.

**Core owns:**
`Electrical Model` · `Network Model` · `Topology` · `Terminals` · `Connections` · `Engineering Identities` · `Domain Validation` · `Analysis` · `Protection` · `Measurement` · `Control Domain` · `Dynamics Domain` · `Studies` · `Solvers` · `Results`

**Core does NOT own:**
Qt, QGraphics, widgets, canvas state, UI controllers, UI history, application lifecycle, UI persistence orchestration, presentation geometry.

---

## 4. Application Layer

The **sole orchestration boundary** between UI and Core.

- UI components must not directly mutate Core.
- The Application layer may call Core.
- Core must not call UI.

**Application owns:** command execution & validation, handler resolution, transactions, rollback/commit, command history, undo/redo, project lifecycle, persistence orchestration, study orchestration, application services & events, read-model coordination, UI update boundaries.

---

## 5. UI / Application / Core Contract

The canonical GridForge V2 mutation pipeline:

```
UI interaction → Controller / Tool → Immutable Command → Application.execute()
      → CommandManager (validation → handler resolution → transaction → history → undo/redo)
      → Handler / Application Service → Core → Semantic Application Event
      → Read Model / Projection → UIUpdateBoundary / UIUpdateBus → UI
```

### CommandManager Responsibilities
1. Receive a command
2. Validate the command
3. Resolve the appropriate handler
4. Open a transaction
5. Execute the handler
6. Commit or roll back
7. Record history
8. Support undo/redo

**Failure invariant:** a failed command must not leave a partially mutated system (`S0 → failed command → S0`).

**Transaction lifecycle:**

```
OPEN → COMMITTING → COMMITTED
OPEN → ROLLING_BACK → ROLLED_BACK | ROLLBACK_FAILED
```

---

## 6. Command Architecture

User intent is represented by **immutable commands** describing an intended state transition — e.g. `CreateBus`, `CreateTransformer`, `CreateBreaker`, `CreateLine`, `ConnectTerminals`, `UpdateEquipment`, `DeleteEquipment`, `PlaceEquipment`, `RunStudy`, `SaveProject`, `OpenProject`, `CloseProject`.

Commands **do not**:
- Directly manipulate widgets
- Bypass Application
- Expose mutable Core state to UI code

### Application Events

`ElementCreated` · `ElementUpdated` · `ElementRemoved` · `TopologyChanged` · `ProjectLoaded` · `ProjectSaved` · `ProjectClosed` · `StudyStarted` · `StudyCompleted` · `ValidationChanged`

---

## 7. Physical Model & Engineering Domains

### Terminals
First-class engineering objects representing electrical endpoints owned by their equipment — basis for connectivity, topology, and switching interpretation.

### Connections & Topology
Derived from authoritative terminal relationships via `TopologyManager`. **Graphical position does not establish electrical connectivity** unless the corresponding engineering relationship exists.

### Bus Model
A Bus is an authoritative engineering object with its own identity — not merely a graphical line, and not a generic derived topological node.

### Analysis / Power Flow / Short Circuit
```
Study / Engineering Analysis → Numerical Solver → Results
```
Power Flow lives under `core.analysis`. Short-circuit analysis consumes authoritative network/equipment data without owning the model.

### Dynamics
First-class study domain, organized under `core/solver/dynamics/`. Dynamic initialization may use an operating point from a solved static study — the dynamic model must never silently replace the persistent electrical truth.

### Protection
```
Primary Electrical System → CT/PT/CVT → Measurement Channel
   → Protection Function → Protection Decision → Trip Scheme
   → Application-Controlled State Transition
```
Protection decisions (`relay_id`, `function_code`, `function_id`, `decision`) remain distinct from physical switching state.

### Control & Automation
Digital I/O, analog signals, timers, interlocks, ladder logic, control sequences — all interacting with the model **only** through defined Application/domain interfaces.

---

## 8. SLD Architecture

The Single-Line Diagram is a **presentation and interaction projection** — not the authoritative electrical model. It may contain symbols, positions, labels, routing, annotations, and interaction state, all separate from Core engineering truth.

### Placement Workflow

```
Equipment Palette → Engineer selects equipment → Live cursor preview (NOT a Core object)
   → Engineer clicks canvas → Placement Command → Application.execute()
   → [Core Equipment + SLD Representation] → Application Event → Projection Update
```

> **Graphical snapping does not itself constitute authoritative electrical connectivity** — it must be committed through the Application command path.

---

## 9. Plugin Architecture

Plugins may contribute equipment types, studies, canvases, tools, panels, renderers, reports, and domain extensions — but must communicate exclusively through defined Core/Application contracts.

A plugin is **an extension of GridForge, not an alternative architecture**.

---

## 10. Persistence Architecture

Canonical project package: **`project.gridforge`**

```
project.gridforge/
├── manifest.json   # package/schema/version metadata
└── project.json    # canonical engineering/presentation data
```

Runtime Qt and QGraphics objects are **never** persisted as project truth.

**Project Lifecycle:** `New → Open → Save → Save As → Close`
Events: `ProjectLoaded` · `ProjectSaved` · `ProjectClosed`

---

## 11. Repository Structure

```
GridForge/
│
├── core/
│   ├── base/
│   ├── model/
│   ├── network/
│   ├── topology/
│   ├── analysis/
│   ├── solver/
│   │   └── dynamics/
│   ├── measurement/
│   ├── protection/
│   ├── control/
│   ├── validation/
│   └── results/
│
├── application/
│   ├── commands/
│   ├── handlers/
│   ├── services/
│   ├── transactions/
│   ├── history/
│   ├── lifecycle/
│   ├── studies/
│   ├── events/
│   ├── read_models/
│   └── persistence/
│
├── ui/
│   ├── core/
│   ├── main_window/
│   ├── sld/
│   ├── control/
│   ├── protection/
│   ├── dynamics/
│   ├── studies/
│   ├── panels/
│   └── projections/
│
├── plugins/
├── tests/
└── docs/
```

---

## 12. Architectural Rules

| # | Rule |
|---|---|
| 1 | **Core is authoritative** — one engineering model |
| 2 | **Application is the UI↔Core boundary** — UI cannot mutate Core directly |
| 3 | **Commands are immutable** |
| 4 | **Transactions are explicit** — controlled commit/rollback |
| 5 | **Undo/redo are Application responsibilities** — never UI-local |
| 6 | **SLD is a projection**, not engineering truth |
| 7 | **Renderer is read-only** with respect to Core |
| 8 | **Plugins use contracts** — no bypassing Application |
| 9 | **Qt stays out of Core** — Core remains headless |
| 10 | **Persistence stores semantics**, not runtime UI objects |
| 11 | **Topology is derived** from engineering relationships, not graphics |
| 12 | **Protection decisions ≠ switching state** |
| 13 | **Studies are Application-orchestrated** workflows |
| 14 | **Read models are not Core** |
| 15 | **Workflows must be auditable end-to-end** |

---

## 13. Forbidden Architectural Paths

```
❌ UI ─────────────────► Core mutation
❌ SLD ────────────────► Core mutation
❌ Renderer ───────────► Core mutation
❌ Plugin ─────────────► uncontrolled Core mutation
❌ Controller ─────────► Core mutation
❌ Core ───────────────► Qt
❌ Core ───────────────► UI
❌ Solver ─────────────► independent engineering truth
❌ SLD geometry ───────► authoritative topology
❌ UI history ─────────► independent undo/redo
```

---

## 14. Engineering State Ownership

| Concern | Owner |
|---|---|
| Equipment identity | Core |
| Equipment properties | Core |
| Terminals | Core |
| Connections | Core |
| Topology | Core |
| Domain validation | Core |
| Numerical domain calculations | Core |
| Study orchestration | Application |
| Command execution | Application |
| Transactions | Application |
| Undo/redo | Application |
| Project lifecycle | Application |
| Persistence orchestration | Application |
| Application events | Application |
| Read models | Application |
| UI interaction | UI |
| Canvas geometry | UI / projection |
| Rendering | UI |
| Selection state | UI |
| User workspace state | UI |
| Plugin contribution | Plugin (via contracts) |

---

## 15. Testing Architecture

**Core Domain:** Model · Network/Topology · Analysis · Solver · Protection · Control · Dynamics

**Application:** Command · Transaction · History · Undo/Redo · Lifecycle · Persistence · Event

**UI / Integration:** Projection · Workflow Integration · Architecture Boundary · Regression

Every major engineering workflow (create/edit/delete equipment, connections, undo/redo, save/open/close, run study, protection trip, control action, dynamic simulation) requires **explicit contract coverage** — testing the complete path, not just isolated classes.

> A passing numerical solver does not prove that the complete engineering workflow works.

---

## 16. Development Philosophy

- **Engineering truth before presentation** — the domain model precedes presentation semantics.
- **Explicit boundaries before convenience** — boundary shortcuts are treated as defects.
- **Workflow before isolated classes** — a capability must work end-to-end.
- **Determinism before convenience** — identity, persistence, and results are reproducible.
- **Validation before freeze** — architecture is checked against implementation before being frozen.

### Workflow Audit Checklist

1. Identify engineer intent
2. Identify UI entry point
3. Identify command
4. Identify Application entry point
5. Identify handler/service
6. Identify Core mutation
7. Identify transaction
8. Identify resulting event
9. Identify read model
10. Identify UI projection
11. Verify persistence
12. Verify undo/redo where applicable
13. Verify failure/rollback behavior
14. Verify no boundary violation

### Architectural Reconciliation

```
FETCH → AUDIT → RECONCILE → CORRECT → CHECK → FREEZE
```

> When old and new architectures conflict, **the current frozen V2 architecture takes precedence.**

---

## 17. Guiding Principle

> **One authoritative engineering truth, one controlled application boundary, multiple specialized engineering workflows and projections.**

```
CORE        = Engineering Truth
APPLICATION = Orchestration + Commands + Transactions + Lifecycle + Studies
UI          = Interaction + Presentation + Projection
WORKFLOWS   = End-to-End Engineering Execution
PLUGINS     = Contract-Bound Extensions
PERSISTENCE = Reproducible Project State
```

The goal is not merely to make the software function — it is to make every engineering action **traceable, deterministic, auditable, reversible where applicable, and architecturally consistent**.

---

## 18. What GridForge Is Not

GridForge is **not**:

- ❌ Merely an SLD drawing application
- ❌ Merely a numerical solver
- ❌ Merely a protection calculator
- ❌ Merely a simulation engine
- ❌ Merely a control-logic editor
- ❌ A collection of disconnected engineering tools
- ❌ A GUI wrapped around an unrelated calculation library
- ❌ A system where graphical state is treated as engineering truth

**GridForge is an integrated engineering platform built around one authoritative digital-twin model.**

---

<p align="center"><sub>GridForge V2 — Architectural Baseline Document</sub></p>
