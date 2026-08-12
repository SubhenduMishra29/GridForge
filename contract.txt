# GridForge SLD & Network Architecture Contract

**Status:** Architectural Working Baseline
**Project:** GridForge
**Layer:** Model / Network / SLD Architecture
**Version:** V2 Audit Contract
**Date:** 12 August 2026

---

## 1. Purpose

This document establishes the architectural contract governing how GridForge represents an electrical power system from:

```text
Physical Equipment
        ↓
Equipment Terminals
        ↓
Electrical Topology
        ↓
Network Representation
        ↓
Study-Specific Numerical Model
        ↓
Analysis / Simulation / Protection
```

The purpose is to prevent the GridForge Model Layer from being designed independently of the SLD and network architecture.

The contract must be established before finalizing the remaining `core/model/` audit.

---

# 2. Fundamental Architectural Principle

GridForge shall maintain a clear distinction between:

1. **Physical equipment**
2. **Physical connection points / terminals**
3. **Global electrical topology**
4. **SLD representation**
5. **Study-specific network representations**
6. **Numerical calculations**

These concepts are related but are not interchangeable.

The authoritative engineering model is **not the GUI canvas**.

The SLD is a representation and interaction mechanism for the underlying engineering model.

This is consistent with commercial power-system platforms. ETAP describes its one-line as an interface for creating and managing the network database, while PowerFactory explicitly distinguishes single-line diagrams used to visualize/define topology from the underlying network model.

---

# 3. GridForge Architectural Layers

The intended architecture is:

```text
                         GRIDFORGE DIGITAL TWIN
                                  │
                                  ▼
                         PHYSICAL MODEL
                                  │
                                  ▼
                            TERMINALS
                                  │
                                  ▼
                         NETWORK TOPOLOGY
                                  │
                                  ▼
                      NETWORK REPRESENTATION
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
             LOAD FLOW      SHORT CIRCUIT      PROTECTION
                 │                │                │
                 ▼                ▼                ▼
             Numerical        Fault Model      Protection
              Model                              Model
```

With the software layers:

```text
core/model/
    Physical electrical equipment

core/network/
    Global electrical topology and network representation

core/solver/
    Numerical computation

core/analysis/
    Public study interfaces

core/protection/
    Protection system and protection studies

core/simulation/
    Dynamic/event/time-domain execution

plugins/
    Specialized extensible equipment and domain models

ui/
    SLD visualization and interaction
```

---

# 4. Physical Model

`core/model/` represents **what physically exists**.

Examples:

```text
Bus
Breaker
Disconnector
Line
Transformer
Load
Generator
Motor
Shunt
CT
PT
VT
CVT
Surge Arrester
Cable
etc.
```

A model object owns its physical parameters and operational state.

It does not own the global network.

---

# 5. Equipment Is Not Topology

A critical GridForge rule is:

> An equipment object represents a physical device; it does not represent the entire electrical topology.

For example:

```text
Breaker
├── from_terminal
└── to_terminal
```

The Breaker represents the physical switching equipment.

It does **not** decide globally what its terminals are connected to.

Likewise:

```text
Transformer
├── HV terminal
└── LV terminal
```

represents the physical transformer.

It does not own the entire network graph.

---

# 6. Terminal Definition

A Terminal is:

> A physical electrical connection point belonging to an equipment object.

Examples:

```text
Load
└── terminal
```

```text
Generator
└── terminal
```

```text
Line
├── from_terminal
└── to_terminal
```

```text
Transformer
├── HV terminal
└── LV terminal
```

```text
Breaker
├── from_terminal
└── to_terminal
```

---

## 6.1 Terminal Is Not Topology

A Terminal must **not become a recursive topology object**.

The following architecture is rejected:

```text
Terminal
    ↓
Terminal
    ↓
Terminal
    ↓
Equipment
```

Likewise, the model layer must not create arbitrary recursive relationships such as:

```text
Load
 → Terminal
 → Breaker Terminal
 → Breaker
 → Load Terminal
 → Load
```

This would mix physical equipment ownership with global topology.

---

## 6.2 Terminal Ownership

A Terminal belongs to exactly one equipment object.

Conceptually:

```text
Equipment
    │
    ├── Terminal
    ├── Terminal
    └── Terminal
```

The Terminal may contain local physical metadata, identification and terminal-specific attributes.

Global connectivity is outside the Terminal's ownership.

---

# 7. Network Topology

`core/network/` owns the **global electrical connectivity graph**.

It answers:

> Which physical connection points are electrically connected under the current network state?

For example:

```text
Bus A
  │
Breaker.from_terminal
  │
Breaker
  │
Breaker.to_terminal
  │
Load.terminal
```

The relationship is owned/interpreted by the network topology layer.

The Load does not need to contain:

```text
Load → Breaker
```

and the Breaker does not need to contain:

```text
Breaker → Load
```

to establish global topology.

---

# 8. SLD Representation

The SLD is a **view and interaction representation of the underlying electrical model/topology**.

The SLD may display:

```text
Bus
 │
Breaker
 │
Transformer
 │
Breaker
 │
Bus
```

but the graphical objects must not become the authoritative electrical state.

The UI must therefore obey the established GridForge rule:

```text
UI
 ↓
Core model/network
 ↓
Authoritative state
```

not:

```text
UI
 ↓
private graphical state
 ↓
simulation
```

Commercial software reinforces this separation. PowerFactory permits network objects to exist independently and subsequently be represented in one or more diagrams; multiple diagrams may represent the same network objects.

Therefore GridForge shall support the future possibility of:

```text
ONE ELECTRICAL MODEL
       │
       ├── Main SLD
       ├── Substation SLD
       ├── Feeder SLD
       ├── Protection view
       ├── Geographic view
       └── Study-specific view
```

without duplicating the underlying electrical equipment.

---

# 9. Bus

Bus requires special treatment.

A Bus is fundamentally an **electrical network node / common electrical connection point**.

It is not simply another two-terminal branch.

Conceptually:

```text
                 BUS
            /      │      \
           /       │       \
        Load    Breaker    Line
```

The Bus participates directly in the electrical network representation.

However, the exact relationship between:

```text
Physical Bus
Network Node
Numerical Bus
```

must be resolved during the detailed Bus audit.

We shall not prematurely redesign `bus.py`.

---

# 10. Branch

`Branch` remains a valid common model abstraction for equipment that behaves as a two-terminal electrical branch.

Examples include:

```text
Branch
├── Line
├── Transformer
└── Future two-terminal branch equipment
```

However:

> `Branch` is not the GridForge SLD topology abstraction.

The SLD may contain many physical elements that are not `Branch` objects:

```text
Breaker
Disconnector
CT
PT
Load
Generator
Motor
etc.
```

Therefore the network architecture must not assume:

```text
Everything = Branch
```

---

# 11. Breaker

Breaker is a **physical switchgear equipment model**.

It is not merely a Boolean attribute of a Bus or Line.

A Breaker has physical terminals:

```text
Breaker
├── from_terminal
└── to_terminal
```

It can therefore appear in:

```text
Bus ── Breaker ── Load
```

or:

```text
Bus ── Breaker ── Bus
```

or:

```text
Bus ── Breaker ── Transformer ── Breaker ── Bus
```

The Breaker owns its physical state.

The network layer interprets that state when determining electrical connectivity.

---

# 12. Breaker State vs Topology State

These must remain conceptually distinct.

### Physical model state

```text
Breaker.closed
Breaker.in_service
```

### Topology

```text
Is terminal A electrically connected to terminal B?
```

### Numerical model

```text
Does this connection appear in the solved network?
```

The three are related but must not be collapsed into one object responsibility.

PowerWorld's full-topology model provides strong evidence for this separation: detailed switching devices are represented in the node-breaker model, while topology processing consolidates the network into a form suitable for conventional numerical studies.

---

# 13. Full-Topology Representation

GridForge shall conceptually support a detailed topology model containing switching equipment.

For example:

```text
Bus A
  │
Disconnector
  │
CT
  │
Breaker
  │
CT
  │
Transformer
  │
Breaker
  │
Bus B
```

This detailed representation is important for:

* switching studies
* protection
* fault isolation
* breaker operation
* substation modeling
* SCADA
* maintenance states
* topology processing
* future real-time/digital-twin functionality

ETAP explicitly advertises detailed bus-breaker connectivity and unlimited switching topologies, while PowerWorld identifies detailed breaker/disconnector models as a full-topology or node-breaker representation.

---

# 14. Numerical Network Representation

The detailed physical topology does not necessarily need to be passed unchanged into every numerical solver.

Instead:

```text
Physical Model
      ↓
Full Topology
      ↓
Topology Processing
      ↓
Study Network Model
      ↓
Solver
```

For example, a detailed substation:

```text
Bus
 │
Disconnector
 │
Breaker
 │
Transformer
 │
Breaker
 │
Bus
```

may be transformed into an appropriate study representation for power flow.

This is a critical GridForge architectural boundary.

---

# 15. Load Flow

The load-flow solver should not need to understand the complete graphical SLD.

The flow should be conceptually:

```text
Physical Model
      ↓
Network Topology
      ↓
Load-Flow Network Representation
      ↓
Y-bus / numerical structures
      ↓
Power Flow Solver
```

The existing GridForge Numerical Reference Layer remains responsible for numerical mathematics.

`core/model/` must not calculate Y-bus or execute Newton-Raphson.

---

# 16. Short Circuit

Short circuit follows a different study-specific interpretation:

```text
Physical Model
      ↓
Network Topology
      ↓
Short-Circuit Network Representation
      ↓
Fault Model
      ↓
Short-Circuit Solver
```

The same physical equipment may therefore contribute different information to different studies.

For example:

```text
Transformer
```

may provide:

* impedance for load flow
* sequence impedance for short circuit
* grounding information for earth faults
* winding configuration for zero-sequence paths
* protection information for relay studies
* dynamic parameters for transient studies

This reinforces the principle:

> The physical model is authoritative; study layers derive the representations they require.

---

# 17. Protection

Protection requires substantially more physical detail than ordinary load flow.

For example:

```text
CT
 │
Relay
 │
Trip signal
 │
Breaker
```

The protection architecture must therefore be able to relate:

```text
Physical equipment
      ↓
Measurement
      ↓
Protection function
      ↓
Trip path
      ↓
Switching equipment
      ↓
Network topology
```

Protection must not be reduced to the load-flow branch model.

---

# 18. Dynamics

Dynamic simulation introduces another representation:

```text
Electrical equipment
       +
Control systems
       +
Signals
       +
Initial operating point
       ↓
Dynamic simulation model
```

This reinforces the existing GridForge decision to keep specialized dynamic/control models extensible through the plugin architecture.

---

# 19. No Premature `Connection` Model

At this stage GridForge shall **not automatically introduce a first-class `Connection` model**.

The architectural question is:

```text
Terminal ↔ Terminal
```

or:

```text
Terminal ↔ Topology
```

and whether topology itself is sufficient.

This must be resolved against the existing `core/network/` implementation before adding another physical model class.

Therefore:

> No `Connection` class shall be introduced merely to solve the current Terminal design problem.

---

# 20. Network Topology Must Be Authoritative for Connectivity

The following principle is mandatory:

```text
core/model
    knows its physical equipment and terminals

core/network
    knows global connectivity
```

Therefore:

```text
Load
```

should not be responsible for determining:

```text
Load → Breaker → Bus
```

and:

```text
Breaker
```

should not independently determine:

```text
Breaker → Load
```

The topology layer determines that relationship.

---

# 21. One Physical Model, Multiple Study Models

GridForge shall support:

```text
                    PHYSICAL MODEL
                          │
                          ▼
                     TOPOLOGY
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
      Load Flow      Short Circuit   Protection
          │               │               │
          ▼               ▼               ▼
      Numerical       Fault Model     Protection
       Network                         Network
```

The study models are derived representations.

They are not independent authoritative copies of the physical system.

---

# 22. SLD Must Not Become a Second Database

The UI must never become the owner of electrical truth.

A graphical item such as:

```text
BusItem
BreakerItem
LineItem
TransformerItem
```

is a visualization/interaction object.

It references the underlying GridForge model/network objects.

Therefore:

```text
SLD Item
   ↓
GridForge Object
   ↓
Network
```

not:

```text
SLD Item
   ↓
private electrical state
```

This preserves the GridForge rule:

> Never compute inside the GUI.
> Never store authoritative electrical state only in the GUI.
> Always synchronize with core.

---

# 23. Implications for the Model Audit

Every `core/model/` class must now be audited against five questions:

### A. What physical thing does it represent?

### B. What terminals does it physically possess?

### C. What physical state does it own?

### D. What information does the network layer need from it?

### E. What information must remain study-specific and outside the model?

For example:

```text
Load
────────────────────────
Physical:
    P demand
    Q demand
    terminal

Network:
    topology connection

Solver:
    numerical injection

Analysis:
    study results
```

---

# 24. Audit Rule for Calculated Quantities

Calculated study results must not become authoritative persistent equipment state unless they are genuinely physical state.

For example, these should generally remain study/result information:

```text
Load flow:
    Pflow
    Qflow
    losses
    loading

Short circuit:
    fault current
    fault contribution

Protection:
    operating time
    CTI
    relay result

Dynamics:
    rotor angle
    transient response
```

The equipment model should store the parameters required to calculate these quantities.

---

# 25. Audit Rule for Frozen Layers

Existing frozen GridForge layers remain frozen unless this architecture audit demonstrates a **genuinely fundamental architectural conflict**.

In particular:

```text
core/model
core/network
core/analysis
core/solver/common
core/base
```

must not be redesigned simply to make individual classes more convenient.

The audit must work from the architecture outward.

---

# 26. Commercial Architecture Evidence

The architecture adopted here is supported by the behavior of established tools:

### ETAP

ETAP describes its one-line as an interface for creating and managing the network database and explicitly provides bus-breaker connectivity, bus-branch representation, and detailed switching topologies.

### DIgSILENT PowerFactory

PowerFactory separates network-model diagrams from dynamic-model diagrams and allows the same network element to appear in multiple diagrams. It also supports detailed single-line representations containing switches and primary/secondary equipment.

### PowerWorld

PowerWorld explicitly distinguishes a detailed full-topology/node-breaker model from the consolidated representation used for conventional numerical studies. Its topology-processing system handles busbars, junctions, terminals and switching devices before consolidation.

These are not being copied as implementation details. They are being used as architectural evidence for the separation of **physical model → topology → study representation**.

---

# 27. Preliminary GridForge Architecture

The current working architecture therefore becomes:

```text
                         GRIDFORGE
                            │
                ┌───────────┴───────────┐
                │                       │
          Physical Model               UI
                │                       │
                │                      SLD
                │                       │
                └───────────┬───────────┘
                            │
                       core/network
                            │
                      Full Topology
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
             Load Flow   Short Circuit Protection
                │           │           │
                ▼           ▼           ▼
             Solver      Solver       Protection
```

The SLD is therefore a **view of the engineering model**, not the engineering model itself.

---

# 28. Decisions Now Established

The following are now the **working architectural rules** for the V2 audit:

1. **SLD is a representation/view of the electrical model.**
2. **Physical equipment belongs to `core/model`.**
3. **Equipment owns its physical terminals.**
4. **Terminal is not a topology graph.**
5. **Terminal must not recursively reference other terminals.**
6. **Global connectivity belongs to `core/network`.**
7. **Breaker is physical switchgear, not merely a branch attribute.**
8. **Breaker state influences topology.**
9. **Physical state, topology state, and numerical state are distinct concepts.**
10. **Branch remains a useful physical/electrical abstraction but is not the SLD graph.**
11. **Bus requires a dedicated audit before changing its current architecture.**
12. **Do not introduce a `Connection` model prematurely.**
13. **The detailed topology may need to be transformed into a study-specific numerical representation.**
14. **Load flow, short circuit, protection and dynamics may require different derived representations of the same physical system.**
15. **The GUI never owns authoritative electrical state.**
16. **Frozen layers are not redesigned without fundamental evidence.**
17. **The model audit will proceed only after each model is checked against this contract.**

---

# 29. Immediate Next Step

We should **not yet generate a revised `terminal.py`**.

The next audit target should be:

```text
core/model/bus.py
```

but not to rewrite it.

We should first inspect its current architecture against this contract and answer:

> **Is GridForge `Bus` simultaneously acting as physical bus equipment, topological node, and numerical bus — and if so, is that intentional and compatible with the existing frozen `core/network/` layer?**

That question is now more important than `Terminal`.

Once `Bus` is resolved, we can correctly settle:

```text
Bus
  ↓
Terminal
  ↓
Breaker
  ↓
Branch
  ↓
Load
  ↓
Network topology
```

without repeatedly redesigning the same interfaces.
