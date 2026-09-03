# Expanded Contingency Element Scope Design

## Goal

Extend GridForge contingency analysis from Line/Transformer-only outages to Bus, Generator, Load, and Shunt contingencies while preserving the frozen Network, PowerFlowPreparation, and study-configuration boundaries.

## Confirmed outage semantics

### Isolation

`ContingencyAnalysis` receives the authoritative `Network` but MUST never mutate it. Each contingency case is created from a deep copy before any outage state is changed.

### Bus contingency

A Bus contingency does **not** remove the Bus from the copied Network. The copied Bus is marked out of service.

A Bus outage also marks every electrical element connected to that Bus out of service in the copied Network. This includes Lines, Transformers, Generators, Loads, and Shunts connected through their authoritative Terminal endpoint relationships.

The connected equipment remains registered in the copied Network; only its operational state changes.

### Direct equipment contingencies

Line, Transformer, Generator, Load, and Shunt contingencies mark only the selected equipment out of service in the copied Network.

No new Network-level `set_element_status()` API is introduced. Equipment operational state is owned by the equipment model and is mutated only on the isolated copy.

## Candidate scope

The supported contingency element types become:

- `bus`
- `line`
- `transformer`
- `generator`
- `load`
- `shunt`

Only currently in-service candidates are selected when candidates are discovered automatically. Explicitly requested IDs must resolve to supported, in-service candidates.

Existing N-1/N-k combination behavior remains unchanged. `N-1` means one selected outage; `N-k` means combinations of `k` selected outage elements.

## Architecture

```text
Authoritative Network
        |
        | deep copy
        v
Isolated Case Network
        |
        +-- apply outage state
        |      Bus -> bus + connected equipment out of service
        |      other supported element -> selected element out of service
        |
        v
PowerFlowPreparation
        |
        +-- authoritative case Network membership/topology
        +-- numerical snapshot
        +-- prepared YBus
        |
        v
PowerFlowAnalysis
        |
        v
ContingencyCaseResult
```

`PowerFlowPreparation` remains responsible for converting the isolated case Network into `PowerFlowInput` and prepared YBus. `ContingencyAnalysis` remains responsible for contingency selection, isolated outage mutation, execution orchestration, and result aggregation.

## Connectivity rule for Bus outages

Bus-connected equipment is determined from the equipment's authoritative Terminal endpoint relationship. The implementation must inspect and use the existing model/terminal APIs rather than introduce parallel bus references or folder-based heuristics.

If an equipment element has no authoritative endpoint or is not connected to the selected Bus, it is not disabled by that Bus contingency.

## Numerical behavior

The existing `YBusBuilder` behavior is reused. Out-of-service Lines and Transformers are skipped by YBus construction. Out-of-service injection elements are excluded from the prepared numerical injections according to the existing `PowerFlowPreparation` in-service filtering.

The existing `PowerFlowStudyConfiguration` instance is reused for every contingency case. No per-case study configuration is constructed.

## Error handling

Unsupported `element_types` values are rejected explicitly.

Unknown or already out-of-service explicit contingency IDs are rejected consistently with the existing candidate-selection contract.

An outage ID that is not found in the isolated case Network is an execution error for that case and is reported through the existing `ContingencyCaseResult.error` mechanism.

## Scope constraints

- Do not add Generator/Bus/Load/Shunt support by changing the frozen `Network` aggregate boundary.
- Do not add a `Network.set_element_status()` API.
- Do not move outage semantics into numerical solver code.
- Do not change `PowerFlowStudyConfiguration` reuse semantics.
- Do not remove or rewrite existing N-1/N-k behavior.
- Do not add other contingency element types such as Motor, Capacitor, Reactor, Solar, Battery, Breaker, Switch, Disconnector, or Fuse unless separately approved.
- Do not add tests in this implementation cycle; verification is limited to repository inspection/static checks unless explicitly changed later.
- Do not freeze the architecture until post-implementation FETCH/CHECK confirms the intended changes only.
