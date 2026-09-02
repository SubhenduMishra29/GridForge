# GridForge V2 — Numerical Layer

**Author:** Subhendu Mishra

## 1. Purpose

`core/numerical` is the numerical representation and numerical-construction layer of GridForge V2.

It converts authoritative electrical information supplied by the Model and Network layers into numerical structures required by studies and solvers.

The Numerical layer owns **numerical representation and numerical construction**.

It does not own electrical-system truth.

---

## 2. Architectural Position

```text
core/model
    │
    │ physical equipment parameters
    ▼
core/network
    │
    │ authoritative membership + topology
    │ prepared BusIndex
    ▼
core/numerical
    │
    ├── numerical state
    ├── numerical matrices
    ├── matrix assembly
    ├── sparse representation
    ├── numerical validation
    └── Y-bus construction
    │
    ▼
core/solver
    │
    └── numerical algorithms
```

The dependency direction is one-way:

```text
Model → Network → Numerical → Solver
```

Numerical must not create a reverse dependency on Solver or UI.

---

## 3. Ownership

The Numerical layer owns:

* numerical state containers;
* numerical matrix representations;
* numerical matrix assembly;
* sparse numerical representations;
* numerical precondition checks;
* Y-bus construction;
* numerical artifacts derived from authoritative Model/Network data.

The Numerical layer does **not** own:

* physical equipment models;
* Network membership;
* terminal identity;
* electrical topology;
* Network lifecycle state;
* study definitions;
* solver algorithms;
* command/history state;
* GUI state;
* SLD state.

---

## 4. Authoritative Sources

Numerical never becomes the source of electrical truth.

The authoritative hierarchy is:

```text
Physical equipment
        │
        ▼
core/model
        │
        ▼
core/network
        │
        ├── NetworkRegistry
        ├── TopologyManager
        ├── NetworkState
        └── BusIndex
        │
        ▼
core/numerical
```

Numerical structures are derived representations.

If a numerical representation disagrees with the authoritative Model or Network state, the numerical representation is stale or invalid.

---

## 5. Bus Index Contract

There is exactly one authoritative bus ordering.

That ordering is owned by:

```text
core.network.indexing.BusIndex
```

and exposed through:

```text
Network.index
```

Numerical must consume the prepared `Network.index`.

Numerical must **not**:

* create a competing authoritative bus ordering;
* silently rebuild `Network.index`;
* assign matrix indices independently;
* infer bus ordering from arbitrary equipment iteration;
* mutate `Network.index` during numerical calculation.

The required lifecycle is:

```text
Network mutation
      │
      ▼
BusIndex invalid
      │
      ▼
explicit Network preparation
      │
      ▼
BusIndex.rebuild(buses)
      │
      ▼
Numerical consumption
```

A numerical builder requiring a BusIndex must reject an invalid or unprepared index.

---

## 6. Topology Contract

Topology belongs to:

```text
core.network.topology.TopologyManager
```

Numerical may consume topology information.

Numerical must not become a topology engine.

In particular, Numerical must not:

* discover electrical connectivity;
* attach terminals;
* determine terminal ownership;
* rebuild the Network topology;
* modify Network connectivity.

Numerical uses already-established electrical relationships to construct numerical representations.

---

## 7. Y-Bus Ownership

Y-bus is a Numerical-layer artifact.

Therefore:

```text
core/numerical/ybus.py
```

owns Y-bus construction.

Network does not own Y-bus.

There must be no:

```text
Network.ybus
core/network/ybus.py
```

ownership contract.

The intended flow is:

```text
Network
   │
   ├── authoritative membership/models
   ├── prepared topology
   └── valid BusIndex
          │
          ▼
YBusBuilder
          │
          ▼
Y-bus numerical artifact
```

`YBusBuilder` must consume authoritative inputs and produce a derived numerical result.

It must not mutate Network state.

---

## 8. Numerical State

Numerical state is distinct from physical Model state and Network state.

```text
Model state
    = physical equipment parameters / engineering state

NetworkState
    = Network topology/lifecycle state

NumericalState
    = numerical operating-point / derived numerical state
```

Examples of numerical state may include:

* bus voltage magnitude;
* bus voltage angle;
* calculated power;
* numerical dynamic state;
* solver-facing numerical values.

Numerical state must not silently become physical model state.

---

## 9. Matrix Ownership

Common numerical matrix behavior belongs inside Numerical.

The purpose is to provide reusable infrastructure for:

* dense matrices;
* sparse matrices;
* matrix contributions;
* matrix assembly;
* numerical validation;
* solver-facing numerical artifacts.

Matrix infrastructure must remain generic.

It must not contain:

* Newton-Raphson solver algorithms;
* Newton iteration control;
* contingency logic;
* dynamic simulation algorithms;
* protection logic;
* study orchestration.

Those belong to their respective layers.

---

## 10. Assembly Contract

Matrix assembly converts validated numerical contributions into numerical matrices.

Conceptually:

```text
Authoritative Network/Model
          │
          ▼
numerical contribution
          │
          ▼
matrix assembly
          │
          ▼
numerical matrix
```

Assembly code must be deterministic.

It must not depend on GUI ordering or incidental Python object identity.

Where bus-indexed assembly is required, the authoritative `Network.index` must determine matrix positions.

---

## 11. Sparse Numerical Representation

Large power-system studies require sparse numerical structures.

Sparse support belongs to Numerical.

Sparse infrastructure should provide representation and numerical utility only.

It must not decide:

* which buses exist;
* which equipment is connected;
* whether a branch is electrically valid;
* which study is being executed.

Those decisions belong upstream.

---

## 12. Numerical Validation

Numerical validation verifies that inputs are suitable for numerical construction.

Examples include:

* required BusIndex is valid;
* required bus IDs exist;
* matrix dimensions are consistent;
* numerical values are finite;
* required terminal mappings exist;
* numerical contributions are dimensionally compatible.

Numerical validation does not replace:

```text
core/model validation
core/network validation
core/study validation
```

Each layer validates its own contract.

---

## 13. Preparation vs Calculation

Numerical preparation and numerical calculation are separate concepts.

### Preparation

Preparation establishes derived numerical prerequisites.

Example:

```text
Network
    │
    ├── topology prepared
    └── BusIndex prepared
```

### Calculation

Calculation constructs or evaluates numerical artifacts.

Example:

```text
prepared Network
       │
       ▼
YBusBuilder
       │
       ▼
YBus
```

Numerical calculation must not silently repair invalid Network state.

Invalid prerequisites must result in an explicit failure.

---

## 14. Immutability of Inputs

Numerical builders should treat Network and Model inputs as authoritative read-only inputs.

For example:

```text
YBusBuilder
    reads:
        Network
        Network.topology
        Network.index
        model parameters

    writes:
        YBus numerical artifact
```

It must not perform:

```text
Network.add_*
Network.remove_*
Network.index.rebuild(...)
Network.topology.build(...)
NetworkState mutation
```

as a side effect of numerical calculation.

---

## 15. Numerical Artifact Validity

A numerical artifact is valid only for the authoritative state from which it was constructed.

Where required, numerical artifacts should retain enough provenance to determine:

```text
which Network topology revision
which BusIndex ordering
which relevant model state
```

was used for construction.

A stale numerical artifact must not be silently reused against incompatible Network state.

---

## 16. Solver Boundary

The Solver layer owns algorithms.

Numerical supplies numerical structures.

```text
Numerical
    │
    ├── matrices
    ├── vectors
    ├── numerical state
    ├── YBus
    └── numerical validation
    │
    ▼
Solver
    │
    ├── power-flow algorithms
    ├── contingency algorithms
    ├── dynamic algorithms
    └── iterative solution procedures
```

Numerical must not contain solver iteration policy.

Solver must not reconstruct Network topology or independently invent bus indexing.

---

## 17. Study Boundary

Studies define what analysis is requested.

Numerical provides the numerical machinery required to execute that analysis.

Therefore:

```text
Study
    = what analysis is requested

Numerical
    = how electrical data is represented numerically

Solver
    = how the numerical problem is solved
```

Numerical must not become a study orchestration layer.

---

## 18. UI Boundary

Numerical has no dependency on:

* PySide6;
* Canvas;
* SLD;
* UI plugins;
* renderers;
* panels;
* toolbar;
* selection state.

The UI communicates through application/domain contracts.

The Numerical layer remains completely independent of presentation.

---

## 19. Proposed Package Structure

The Numerical package is intentionally modular:

```text
core/numerical/
│
├── __init__.py
├── README.md
│
├── state.py
├── ybus.py
│
├── indexing.py
├── matrix.py
├── assembly.py
├── sparse.py
└── validation.py
```

A file should only be introduced when it owns a clearly defined responsibility.

No placeholder modules should be maintained solely to satisfy the directory structure.

---

## 20. Public API Policy

`core/numerical/__init__.py` should expose only stable public Numerical contracts.

Internal implementation details should remain internal.

Consumers should depend on:

```text
stable Numerical API
```

rather than internal module structure wherever practical.

Changing an internal implementation must not unnecessarily force changes throughout Solver, Study, or UI code.

---

## 21. Dependency Rules

Numerical may depend on:

```text
core.base
core.model
core.network
```

where required by the frozen contracts.

Numerical may not depend on:

```text
ui
plugins
core.application
GUI-specific modules
```

Numerical should not depend on Solver.

The intended dependency direction remains:

```text
Model
  ↓
Network
  ↓
Numerical
  ↓
Solver
```

---

## 22. Error Policy

Numerical code must fail explicitly when required prerequisites are invalid.

Examples:

```text
invalid BusIndex
missing bus
unknown bus ID
invalid matrix dimension
non-finite numerical value
incompatible numerical state
stale numerical artifact
```

It must not silently:

* invent missing indices;
* rebuild Network state;
* repair topology;
* substitute arbitrary ordering;
* ignore inconsistent input.

Explicit failure preserves deterministic numerical behavior.

---

## 23. Determinism

Numerical construction must be deterministic.

For identical authoritative inputs:

```text
same Network
same Model parameters
same topology revision
same BusIndex
```

the numerical artifact must be reproducible.

Numerical code must not rely on:

* GUI insertion order;
* memory addresses;
* object identity;
* unordered iteration where ordering affects numerical indexing.

---

## 24. Core Contract

The fundamental Numerical contract is:

> **Numerical consumes authoritative, prepared electrical information and produces deterministic numerical representations and artifacts without changing electrical truth.**

In particular:

```text
Model owns physical equipment truth.
Network owns assembled membership, connectivity, topology, and BusIndex.
Numerical owns numerical representation.
Solver owns algorithms.
Study owns analysis intent.
UI owns presentation.
```

---

## 25. Frozen Boundary

The Numerical layer must preserve the following invariants:

```text
1. Model owns authoritative physical equipment truth.
2. Network owns authoritative membership, topology, and BusIndex.
3. Numerical consumes a valid prepared BusIndex.
4. Numerical owns YBus construction.
5. Numerical does not own Network state.
6. Numerical does not mutate Network.
7. Numerical does not implement solver algorithms.
8. Numerical does not implement study orchestration.
9. Numerical has no UI dependency.
10. Numerical artifacts are derived and may become stale.
11. Numerical construction is deterministic.
12. Invalid numerical prerequisites fail explicitly.
```

These invariants form the architectural boundary for the Numerical module and must be checked before individual Numerical files are implemented or frozen.
