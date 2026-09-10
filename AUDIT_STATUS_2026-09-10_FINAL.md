# GridForge V2 — Final Open / Partial Remediation Status

Author: Subhendu Mishra

Date: 2026-09-10

Audited remediation baseline: `029ffc9e153d980ee03e7ce2671325cd116b256a`

Remediation branch: `remediation/final-open-partial-2026-09-10`

Current remediation HEAD: `342d17f33e0bb54d179d9e19e0048c24d4ae9d8`

## Status rule

A finding is CLOSED only when root cause, contract, integration, executable targeted regression, and conflict-free implementation are all demonstrated. The current environment permits repository inspection and GitHub commits, but the repository checkout/test runner is not available here. A GitHub Actions targeted-test workflow was added, but no workflow run is available for these commits; therefore no test is represented as passed in this register.

## CLOSED

No previously OPEN/PARTIAL finding is newly marked CLOSED because executable targeted evidence is unavailable.

The pre-existing closed findings remain protected and were not intentionally modified:

- GF-AUD-207, 208, 209, 210, 213, 214, 215, 219
- GF-EDM-046, 048, 066

## PARTIALLY CLOSED — implementation/contract corrected, executable proof pending

### Measurement

- GF-AUD-204 — PU -> physical engineering quantity -> instrument ratio -> secondary conversion is explicit for current and voltage paths; short-circuit current conversion uses the prepared numerical base; channel signal type is checked. Targeted conversion/source/channel tests exist but are not executed.
- GF-AUD-205 — duplicate `measurement_transformer_commands.py` authority removed; canonical `measurement_commands.py` remains. Regression tests exist but are not executed.
- GF-EDM-030–037 — reconciled with the existing CT/PT/CVT/MeasurementPoint/MeasurementChannel architecture; no second measurement abstraction introduced. Executable coverage remains pending.

### Transformer / numerical boundary

- GF-AUD-212 — explicit transformer impedance basis and reference metadata; preparation performs conversion; executable proof and persistence coverage pending.
- GF-AUD-217 — raw transformer electrical parameters now have an explicit basis contract; ambiguous basis is rejected.
- GF-AUD-218 — engineering `r/x/b` are defined as ohm/ohm/siemens on the declared reference voltage; no YBus engineering conversion remains.
- GF-AUD-220 — existing `PerUnitSystem` remains the sole PU conversion authority; transformer original-base conversion occurs in preparation.

### Reactive equipment

- GF-EDM-028 — capacitor/reactor engineering data reaches the existing `PreparedShunt` boundary.
- GF-EDM-047 — capacitor/reactor numerical preparation is unified through `PreparedShunt`.
- GF-EDM-067 — reactive equipment is represented as prepared shunt susceptance with preserved identity, service state and sign convention. YBus executable verification is pending.

### Power Flow / cross-cutting preparation

- GF-EDM-049 — `PreparedPowerFlow` is detached and result conversion is ID-based; targeted identity regression remains pending.
- GF-EDM-050 — `PowerFlowStudyConfiguration` now explicitly owns base MVA, slack classification, tolerance, maximum iterations, voltage-base mapping and numerical options.
- GF-EDM-063 — Power Flow and Short Circuit now have explicit preparation boundaries; other implemented study-specific preparation boundaries require final re-verification.
- GF-EDM-064 — engineering-model completeness and preparation completeness are treated as separate concerns; executable study-by-study proof remains pending.
- GF-EDM-065 — prepared Power Flow and Short Circuit boundaries retain stable equipment/bus IDs and detached numerical state; broader equipment-index coverage requires executable verification.

### Short Circuit

- GF-EDM-051 — supported short-circuit execution is retained; source/rotating-machine contribution is limited to the currently implemented sequence-network inputs and is not invented.
- GF-EDM-052 — new `ShortCircuitPreparation` owns the detached preparation boundary and produces `ShortCircuitInput`/`SequenceNetworkSnapshot` data.
- GF-EDM-053 — 3-phase and unbalanced studies consume prepared numerical input rather than building solver data directly in the solver.
- GF-EDM-054 — canonical result identity includes fault type, bus ID and bus index; equipment-level contribution identity remains limited by the currently supported solver contract.

### Persistence

- GF-AUD-206 / GF-AUD-216 — canonical `.gridforge` package boundary added outside Core with `manifest.json` + `project.json`, Project root, stable-ID object references, transformer basis preservation, SLD layout and metadata, semantic load validation, and explicit legacy ambiguity rejection. Full all-equipment semantic round-trip execution remains unverified.

### Protection

- GF-EDM-038–045 — existing Relay / ProtectionElement / RelayBase / MeasurementChannel architecture is preserved; no duplicate relay hierarchy or measurement architecture introduced. Executable end-to-end coverage remains pending.
- GF-EDM-055–057 — existing protection preparation boundary remains detached; study/execution distinction is preserved. Executable proof remains pending.
- GF-EDM-069 — `ProtectionOutputService` now translates an actionable `ProtectionDecision` into the existing `TripBreakerCommand` and `ModelService.trip_breaker()` application mutation path. Integration test is added but not executed.

## OPEN / NOT YET CLOSED

- GF-EDM-001–019 — remaining engineering-data findings are not bulk-closed. They require per-study scope verification against currently implemented consumers; no unsupported future model fields were invented.
- Any individual engineering-data item from GF-EDM-001–019 whose missing field is required by an existing implemented study remains OPEN until that study has a deterministic preparation contract and executable regression.
- Broader short-circuit source/machine contribution remains OPEN where the current GridForge model does not provide the required supported sequence parameters; it is not silently inferred.

## DEFERRED

- GF-EDM-058 — dynamic preparation: current repository contains only `core/simulation/load_flow.py` in the simulation package; no implemented dynamic preparation engine was found in the audited tree.
- GF-EDM-059 — Power Flow -> dynamic initial-state bridge: deferred with the dynamic engine because no current dynamic execution boundary exists.
- GF-EDM-060 — detailed AVR/governor/PSS/transient machine models: explicitly deferred; not implemented merely for audit-count reduction.
- GF-EDM-061 — `_record_sample()` hard-coded sample time: no current `_record_sample()` dynamic implementation was found in the audited tree, so there is no live defect to patch.
- GF-EDM-068 — engineering -> dynamic bridge: deferred with the absent dynamic implementation.

## OBSOLETE / SUPERSEDED

- The duplicate measurement transformer command finding is superseded by the canonical `measurement_commands.py` authority; the removed duplicate is retained only in historical audit traceability, not as a live implementation.
- No historical audit document was deleted or rewritten.

## REGRESSION CHECK

The remediation diff from `029ffc9e153d980ee03e7ce2671325cd116b256a` changes only: targeted-test workflow, Power Flow study configuration, Short Circuit preparation/facade, project persistence, protection output application boundary, and their targeted tests. No intentional change was made to the previously closed Power Flow line/cable preparation, YBus prepared-data boundary, or the listed closed findings.

## TEST VERIFICATION

- Python version: not executable in the current GitHub-backed environment.
- Local repository checkout: unavailable.
- Targeted GitHub Actions workflow: added at `.github/workflows/targeted-remediation.yml`.
- Workflow runs observed for remediation commits: none; therefore no targeted test is claimed as passed.
- Full suite: NOT RUN.

## Evidence discipline

Repository inspection and code-level contract review were performed against the current remediation branch. Absence of executable test evidence is intentionally recorded as PARTIALLY CLOSED rather than converted into a false CLOSED status.
