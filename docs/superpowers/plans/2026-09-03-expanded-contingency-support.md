# Expanded Contingency Support Implementation Plan

## Goal

Extend `ContingencyAnalysis` to support Bus, Generator, Load, and Shunt contingencies in addition to the existing Line and Transformer scope, while preserving the frozen V2 ownership boundaries.

## Confirmed design

- Every contingency operates on a deep copy of the authoritative `Network`.
- The authoritative Network is never mutated.
- Bus outage keeps the Bus registered in the copied Network and marks it out of service.
- A Bus outage also marks every connected Line, Transformer, Generator, Load, and Shunt out of service in the copied Network.
- Direct Line, Transformer, Generator, Load, and Shunt outages disable only the selected element.
- Equipment operational state is mutated directly on the copied equipment model; no `Network.set_element_status()` API is introduced.
- The existing `PowerFlowStudyConfiguration` instance is reused for every case.
- Each isolated case is converted through `PowerFlowPreparation` and then executed by `PowerFlowAnalysis`.
- N-1/N-k combination semantics remain unchanged.
- Supported contingency element types become exactly: `bus`, `line`, `transformer`, `generator`, `load`, `shunt`.
- No Motor, Capacitor, Reactor, Solar, Battery, Breaker, Switch, Disconnector, or Fuse contingency support is added.
- No tests are added in this implementation cycle.

## Repository findings

`Network` exposes authoritative collections for buses, generators, loads, shunts, lines, and transformers. Equipment models own their operational `in_service` state. Bus, Generator, Load, and Shunt use authoritative Terminal endpoint relationships. `PowerFlowPreparation` already excludes out-of-service generators and loads from numerical injections, while `YBusBuilder` skips out-of-service branches/transformers.

## Implementation steps

1. Update `ContingencyAnalysis` documentation and public parameter descriptions to describe the expanded supported element scope.
2. Replace the obsolete `Network.set_element_status()` call with copied-element operational-state mutation.
3. Extend candidate discovery to buses, generators, loads, and shunts while retaining current in-service filtering and explicit-ID validation.
4. Extend element-type normalization to exactly the six approved contingency types.
5. Extend isolated-case lookup to all six supported element collections.
6. Implement Bus outage propagation using authoritative Terminal endpoint relationships. For the selected copied Bus, mark it out of service and mark connected copied Lines, Transformers, Generators, Loads, and Shunts out of service. Do not introduce duplicate bus references or mutate the authoritative Network.
7. Keep direct equipment outages local to the selected copied element.
8. Reuse the existing preparation/execution boundary unchanged.
9. Inspect the resulting diff and fetch all changed files after commit to confirm only intended changes were made.
10. Verify statically without adding/running tests; do not freeze yet.

## Bus connectivity algorithm

For the copied Network, identify the selected Bus object. For each supported connected equipment collection, inspect its authoritative terminal and resolve its endpoint to a Bus using the existing terminal-resolution API. If the resolved Bus ID matches the selected Bus ID, disable that copied equipment. Elements without a resolvable authoritative endpoint are not implicitly disabled.

## Constraints

- Do not change `Network` ownership or add status APIs.
- Do not move outage semantics into the solver or YBus builder.
- Do not alter `PowerFlowPreparation` beyond what is strictly required by an inspected incompatibility.
- Do not alter study-configuration reuse.
- Do not change legacy N-1/N-k behavior or defaults except the explicitly approved candidate-scope expansion.
- Do not reconstruct the entire contingency file from incomplete output; use exact fetched content for any update.
- Follow FETCH → ANALYSE → INSPECT → CORRELATE → CONFIRM → COMMIT → FETCH → CHECK → FREEZE.
