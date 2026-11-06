# Power Flow Preparation Boundary

## Goal

Introduce one explicit preparation boundary shared by normal and contingency Power Flow studies:

`Network + explicit study classification -> PreparedPowerFlow(input, ybus)`.

## Frozen constraints

- `PowerFlowInput` remains the immutable execution contract.
- PQ/PV/SLACK classification is study-side only.
- No classification is added to Bus, Generator, Network, or numerical BusState.
- `YBus` remains a derived numerical representation.
- Contingencies isolate and mutate only a copied case Network.
- The same `PowerFlowPreparation` is used for normal and contingency cases.
- Numerical solver execution receives no live Network.
- No tests are added or run during this migration.

## Implementation tasks

1. Add `PreparedPowerFlow` and `PowerFlowPreparation` under `core/analysis/power_flow_preparation.py`.
2. Correlate actual terminal/equipment attachment and operating-value APIs before relying on model aggregation.
3. Wire `PowerFlowAnalysis` to consume the prepared boundary while preserving its analysis-versus-solver separation.
4. Migrate `ContingencyAnalysis` to prepare each isolated case through the same preparation component.
5. Audit exports and all internal callers.
6. Re-fetch changed files and perform architectural/import correlation.
7. Freeze only after verification.
