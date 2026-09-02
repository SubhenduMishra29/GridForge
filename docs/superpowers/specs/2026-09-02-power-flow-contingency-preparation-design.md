# Power Flow / Contingency Preparation Boundary Design

## Status

Approved extension of the GridForge V2 short-circuit migration.

## Goal

Introduce an explicit preparation boundary that converts an authoritative Network into immutable Power Flow numerical input plus a separately prepared YBus, then update Contingency Analysis to execute each isolated outage case through that boundary.

## Frozen Architecture

```text
Authoritative Network
        |
        v
PowerFlowPreparation
        |
        +--> PowerFlowInput
        +--> YBus
                 |
                 v
        PowerFlowAnalysis
                 |
                 v
        PowerFlowSolver
```

For contingency studies:

```text
Authoritative Network
        |
        v
ContingencyAnalysis
        |
        +--> deep-copied case Network
                    |
                    v
          PowerFlowPreparation
                    |
                    +--> PowerFlowInput
                    +--> YBus
                             |
                             v
                    PowerFlowAnalysis
```

## Responsibilities

### PowerFlowPreparation

- Reads the authoritative Network only during preparation.
- Validates that the Network has a valid authoritative BusIndex.
- Extracts bus IDs, bus types, specified P/Q, Q limits, and initial voltage state into PowerFlowInput.
- Builds YBus from the same Network snapshot and preserves identical bus ordering.
- Returns only prepared numerical contracts to execution.
- Does not solve the study.
- Does not mutate Network.

### PowerFlowAnalysis

- Remains an analysis-level numerical study facade.
- Accepts PowerFlowInput and prepared YBus.
- Does not retain or inspect a live Network.
- Delegates numerical execution to the Power Flow solver.

### ContingencyAnalysis

- Retains the authoritative Network at analysis scope.
- Never mutates the authoritative Network.
- Deep-copies the Network before applying an outage.
- Prepares PowerFlowInput and YBus from the isolated case Network.
- Passes only prepared numerical contracts into PowerFlowAnalysis.
- Performs post-contingency violation detection at analysis scope.

## Data Boundary

The numerical solver must never receive a live Network, Bus, Line, Transformer, Terminal, or other mutable Core object. A contingency case may use a copied Network during preparation, but that copy must not cross into numerical execution.

The PowerFlowInput contract currently contains:

- bus_ids
- bus_types
- p_spec
- q_spec
- q_min
- q_max
- initial_vm
- initial_va

YBus is a separately prepared immutable numerical representation whose bus_ids must exactly match PowerFlowInput.bus_ids.

## State Isolation

Contingency outages are applied only to an isolated deep copy. The copied case is the source for both PowerFlowInput and YBus so that outage state is represented consistently in the numerical snapshot.

## No New Electrical Authority

This design does not move ownership of electrical equipment, membership, topology, or BusIndex. Network remains authoritative for those concerns. YBus remains a derived numerical representation under core.numerical. Power Flow preparation is an interpretation boundary, not a new model store.

## Known Repository Constraint

The current PowerFlowInput contract is defined, while the repository does not yet expose a confirmed Network-to-PowerFlowInput preparation service. This migration therefore adds that boundary explicitly rather than making ContingencyAnalysis infer or duplicate solver preparation logic.

## Constraints

- No tests are added or run during this migration.
- No UI, Qt, SLD, or Application dependencies are introduced into Core numerical execution.
- Existing contingency result and violation semantics should be preserved unless repository evidence requires a change.
- Do not silently invent missing electrical field mappings. If an authoritative mapping cannot be established from the repository, stop and request clarification.
