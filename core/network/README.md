# GridForge V2 — Network Layer

The `core/network` package is the **assembled electrical-network layer** of GridForge V2.

It sits between the canonical electrical model layer and the engineering analysis / numerical layers.

```text
UI / SLD
   │
   ▼
Application
   │ commands / orchestration
   ▼
core.model
   │ canonical electrical objects
   ▼
core.network
   ├── Network
   ├── NetworkRegistry
   ├── BusIndex
   ├── NetworkState
   └── TopologyManager
   │
   ▼
core.numerical
   ├── YBus
   └── YBusBuilder
   │
   ▼
core.analysis
   │
   ▼
core.solver
```

## 1. Architectural Role

The Network Layer assembles references to canonical electrical model objects into an operational network representation.

Its responsibilities are:

- network membership;
- topology lifecycle and derived connectivity;
- deterministic bus indexing;
- network structural state and invalidation;
- network-level reconfiguration and structural checks.

The Network Layer does **not** own electrical equipment definitions, study orchestration, numerical solution algorithms, or UI/SLD state.

## 2. Canonical Model Ownership

`core.model` is the authoritative source of truth for electrical entities.

The Network Layer stores and organizes references to those canonical objects. It must not create duplicate network-specific electrical objects.

```text
core.model
    │
    └── canonical electrical objects
            │
            ▼
core.network
    └── assembled membership / topology
```

## 3. Network Ownership

`core.network` owns:

- canonical network membership;
- deterministic `BusIndex` lifecycle;
- derived topology;
- network structural revision/invalidation state;
- network-level structural operations.

It does **not** own:

- GUI state;
- SLD graphics or layout;
- canvas state;
- application commands or transactions;
- engineering-study orchestration;
- numerical solver algorithms;
- electrical equipment definitions;
- numerical Y-bus artifacts.

## 4. Package Structure

```text
core/network/
├── __init__.py
├── README.md
├── network.py
├── registry.py
├── indexing.py
├── state.py
├── endpoint.py
└── topology.py
```

Y-bus is deliberately outside this package:

```text
core/numerical/
├── __init__.py
├── state.py
└── ybus.py
```

## 5. `network.py`

`network.py` contains the `Network` façade.

The façade coordinates:

```text
Network
   ├── NetworkRegistry
   ├── BusIndex
   ├── NetworkState
   └── TopologyManager
```

It provides the stable entry point for callers working with an assembled electrical network.

The Network façade does not own or construct numerical Y-bus artifacts.

## 6. `registry.py`

`NetworkRegistry` owns network membership.

It maintains references to canonical model objects and prevents duplicate identifiers within its registered collections.

```text
Registry = membership
```

The registry does not own topology, numerical Y-bus data, solver calculations, UI state, or study orchestration.

## 7. `indexing.py`

`BusIndex` owns the derived deterministic mapping between canonical bus identifiers and numerical matrix positions.

Example:

```text
BUS-001 → 0
BUS-002 → 1
BUS-003 → 2
```

`BusIndex` is derived state. It must be rebuilt when bus membership/order changes.

The authoritative bus objects remain in `core.model` / Network membership; the index is only the numerical position mapping.

## 8. `state.py`

`NetworkState` owns Network structural lifecycle information.

It currently owns:

- `topology_revision`;
- `topology_dirty`.

It deliberately does **not** own:

- canonical model objects;
- network membership;
- topology graphs;
- terminal relationships;
- `BusIndex` mappings;
- `YBus` objects;
- Y-bus validity/revision state;
- solver state;
- study state.

Numerical artifacts record the Network revision from which they were derived and determine freshness by comparing that revision with `NetworkState.topology_revision`.

## 9. `endpoint.py`

`endpoint.py` is an internal read-only utility for resolving the Bus associated with a canonical Terminal relationship.

The authoritative relationship is:

```text
Equipment → Terminal → Endpoint → Bus
```

Compatibility properties such as `from_bus`, `to_bus`, or `bus` must not replace the terminal-based physical relationship as the authoritative connectivity representation.

`endpoint.py` is not a primary package-level API.

## 10. `topology.py`

`TopologyManager` derives electrical connectivity from the canonical Network model objects and their service/conduction state.

It provides operations such as:

- `build()`;
- `find_islands()`;
- `is_connected()`;
- connectivity queries.

Topology is derived state:

```text
Canonical model + Network membership
              │
              ▼
      TopologyManager
              │
              ▼
      Derived topology graph
```

`TopologyManager` does not own Bus, Line, Transformer, or other equipment objects and does not perform numerical solving.

## 11. Topology and SLD Are Different

The SLD is a visual engineering representation, not the electrical topology database.

```text
core.model
   ├──────────────► core.network topology
   │
   └──────────────► SLD representation
```

A graphical SLD connection does not become electrical truth merely because a graphical line was drawn.

Application orchestration converts authoring intent into engineering commands. Core validates and applies the resulting domain changes.

## 12. Numerical Boundary and Y-Bus

**Y-bus belongs to `core.numerical`, not `core.network`.**

The Numerical layer owns derived mathematical representations and numerical artifacts produced from authoritative Network/Model data.

```text
core.model
    │
    ▼
core.network
    ├── topology
    └── BusIndex
    │
    ▼
core.numerical
    ├── YBusBuilder
    └── YBus
    │
    ▼
core.analysis
    │
    ▼
core.solver
```

`YBusBuilder` constructs the Y-bus from the assembled Network representation and current deterministic bus indexing.

It performs matrix construction and element stamping. It does not perform Newton-Raphson iterations, power-flow solution, short-circuit solution, protection calculations, or transient simulation.

The Network package therefore must **not** import or export `YBusBuilder` or `YBus` as Network-owned services.

## 13. Derived-State Relationship

The canonical model remains authoritative. Network and Numerical representations are derived/assembled views of that state.

```text
Canonical model mutation
        │
        ▼
Network structural revision changes
        │
        ├── topology becomes stale
        │
        └── numerical artifacts derived from the old revision become stale
```

Derived artifacts may be discarded and rebuilt. Canonical electrical state must never be reconstructed from a Y-bus or topology graph.

## 14. Network Reconfiguration

Topology-affecting changes include operations such as:

- add/remove bus;
- add/remove branch;
- connect/disconnect equipment;
- change topology-affecting service state;
- other structural Network changes.

The Network Layer updates its structural revision/invalidation state. Numerical consumers must ensure their derived artifacts correspond to the current Network revision before use.

## 15. Command and Transaction Boundary

Network modifications are orchestrated by the Application layer.

```text
UI / SLD
   │
   ▼
Intent / Command
   │
   ▼
Application transaction
   │
   ├── create/update canonical model
   ├── validate
   ├── connect/register
   └── commit
          │
          ▼
      Network
```

The Network Layer is not a command dispatcher and does not own application transaction orchestration.

## 16. Validation Boundary

Validation is layered.

```text
Command validation
       ↓
Model/domain validity
       ↓
Network structural validity
       ↓
Engineering validation
       ↓
Study-specific validation
```

Network may enforce structural requirements needed for its own operation, such as duplicate membership, missing identifiers, unregistered references, or invalid indexing state.

Engineering rules remain in the appropriate Core validation/engineering layers.

## 17. Consumption Boundary

Higher-level engineering layers consume Network and Numerical representations.

```text
                 Network
                    │
          ┌─────────┴─────────┐
          │                   │
      topology             BusIndex
          │                   │
          └─────────┬─────────┘
                    ▼
              core.numerical
                    │
                  Y-Bus
                    │
                    ▼
              core.analysis
                    │
                    ▼
               core.solver
```

The solver owns numerical solution algorithms. It does not need to reconstruct the complete electrical Network when the required assembled/numerical representations are already supplied through the intended boundaries.

## 18. Headless Boundary

`core/network` must remain completely headless.

It must not depend on:

- PySide6/PyQt;
- `QGraphicsScene` / `QGraphicsItem`;
- MainWindow or UI panels;
- SLD canvas;
- renderers;
- UI plugins.

The Network Layer must be usable by tests, CLI tools, batch processing, engineering studies, automation, and headless simulation without starting a GUI.

## 19. Solver Boundary

The Network Layer provides assembled network representations. It does not solve studies.

Incorrect:

```text
Network.solve_power_flow()
Network.solve_short_circuit()
Network.run_transient()
```

Correct:

```text
Network / Numerical
        ↓
     Analysis
        ↓
      Solver
        ↓
 Engineering Result
```

## 20. Per-Unit Boundary

The canonical per-unit implementation belongs to:

```text
core.base.per_unit.PerUnitSystem
```

Network may consume per-unit services where required by its structural/numerical boundaries, but it must not create a second canonical per-unit implementation.

## 21. Ownership Summary

| Responsibility | Owner |
|---|---|
| Canonical electrical object definition | `core.model` |
| Network membership | `NetworkRegistry` |
| Bus identifier → numerical index | `BusIndex` |
| Network structural revision | `NetworkState` |
| Connectivity graph | `TopologyManager` |
| Y-bus representation | `core.numerical` |
| Y-bus construction | `YBusBuilder` in `core.numerical` |
| Numerical solution algorithms | `core.solver` |
| Engineering study orchestration | `core.analysis` |
| Commands / transactions | Application |
| SLD rendering / interaction | UI / UI Core |

## 22. Final Boundary

The frozen Network boundary is:

```text
core.model
    = authoritative electrical objects

core.network
    = assembled membership + topology + structural lifecycle + BusIndex

core.numerical
    = derived numerical representations, including Y-bus

core.analysis
    = engineering study orchestration

core.solver
    = numerical solution algorithms
```

No layer may silently become a second owner of another layer's authoritative state.
