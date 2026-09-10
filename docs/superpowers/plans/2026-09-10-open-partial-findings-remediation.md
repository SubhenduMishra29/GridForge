# GridForge V2 Open/Partial Findings Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining OPEN and PARTIALLY CLOSED GridForge V2 findings with minimal root-cause corrections that preserve the frozen architecture and provide executable targeted regression evidence.

**Architecture:** Preserve Core Model + Network as authoritative engineering truth. Each study-specific preparation boundary converts validated engineering state into an immutable, identity-indexed numerical snapshot; solvers consume only detached numerical data. Measurement converts numerical PU quantities to physical primary quantities before CT/PT/CVT conversion, and protection separates detached study analysis from Application-mediated live switching.

**Tech Stack:** Python, dataclasses, NumPy/SciPy numerical representations, existing GridForge Core/Application architecture, pytest targeted tests only.

**Spec:** User-approved remediation requirements in the 2026-09-10 GridForge V2 Open & Partially Closed Findings Remediation request.

## Global Constraints

- Preserve the frozen V2 architecture; no competing architecture or duplicate service/registry/model/result/preparation system.
- Core remains independent of Qt/UI.
- Commands carry intent/value data, not Core model objects.
- Do not move engineering-to-PU conversion into `YBusBuilder`.
- `YBusBuilder` consumes prepared PU-only numerical data and never owns authoritative engineering units.
- Analysis never mutates the authoritative Network.
- Use existing canonical `PerUnitSystem`, resolvers, mutation boundaries, and identity contracts.
- Every new or substantially modified GridForge V2 source file retains `Author: Subhendu Mishra`.
- Do not run the complete test suite; run only targeted tests needed for each remediation group.
- Do not mark a finding CLOSED without implementation, contract, integration, passing targeted regression, and no conflicting implementation.
- Preserve all explicitly closed findings listed by the user.

---

### Task 1: Re-verify current findings and freeze the remediation surface

**Files:**
- Inspect: `AUDIT_REPORT.md`, `Modification_Register.txt`, current Core measurement/application/model/analysis/persistence/protection/simulation files.
- Modify: `AUDIT_REPORT.md` only if a current-status companion/ledger is required; preserve historical content rather than overwriting it.
- Create: `docs/superpowers/plans/2026-09-10-open-partial-findings-remediation.md`

**Interfaces:**
- Consumes: current commit `7f2cf46c144606efc26b5bfc858467306c261008` and the frozen finding list.
- Produces: a verified file/finding matrix used by all subsequent tasks.

- [ ] **Step 1: Identify authoritative implementation files for each finding.**
- [ ] **Step 2: Confirm the existing measurement, transformer, reactive, persistence, study, protection, and dynamic boundaries before changing code.**
- [ ] **Step 3: Record stale audit documentation as historical when it refers to a different repository/baseline.**
- [ ] **Step 4: Do not alter production behavior during this verification step.**

**Verification:** static repository inspection; no full test suite.

---

### Task 2: Establish the single measurement conversion contract and remove duplicate command responsibility

**Files:**
- Modify: `core/measurement/*` authoritative CT/PT/CVT, point, and channel modules.
- Modify: `core/analysis/measurement_generation.py` or its current authoritative measurement-generation module.
- Modify: `core/application/commands/measurement_commands.py`.
- Modify/Delete after consumer migration: `core/application/commands/measurement_transformer_commands.py`.
- Modify: affected application registration/import modules and targeted measurement tests.

**Interfaces:**
- Consumes: existing CT/PT/CVT models, `MeasurementPoint`, `MeasurementChannel`, existing analysis result contracts, and `PowerFlowPreparation` output.
- Produces: one measurement command contract and deterministic current/voltage conversion paths.

- [ ] **Step 1: Write failing tests for CT conversion: PU current → base current → primary current → CT secondary.**
- [ ] **Step 2: Write failing tests for PT and CVT conversion using PU voltage → voltage base → physical primary voltage → secondary voltage.**
- [ ] **Step 3: Write failing tests proving source/channel binding identifies source, source quantity, basis, conversion, secondary quantity, and destination.**
- [ ] **Step 4: Write a failing regression test demonstrating that applying a physical CT/PT ratio directly to a PU quantity is rejected or produces a materially different, correct result through the authoritative path.**
- [ ] **Step 5: Reconcile `measurement_transformer_commands.py` into the authoritative `measurement_commands.py` contract and update all consumers/imports.**
- [ ] **Step 6: Implement only the minimal conversion helpers required by the existing measurement architecture.**
- [ ] **Step 7: Run targeted measurement tests only.**

**Expected invariant:** no measurement conversion path applies CT/PT/CVT ratios directly to PU values.

---

### Task 3: Complete the Transformer engineering impedance contract and preparation conversion

**Files:**
- Modify: `core/model/transformer.py`.
- Modify: `core/analysis/power_flow_preparation.py`.
- Inspect/modify: `core/base/per_unit.py` only if an existing canonical conversion primitive is genuinely missing.
- Modify: Transformer command/service/persistence consumers that serialize or construct transformer impedance.
- Modify: targeted transformer and power-flow preparation tests.

**Interfaces:**
- Consumes: `Transformer.r/x/b`, `impedance_basis`, transformer rating/base information, bus voltage bases, and canonical `PerUnitSystem`.
- Produces: `PreparedTransformer` containing deterministic system/study-base PU `r_pu/x_pu/b_pu`, tap, shift, stable ID, and service state.

- [ ] **Step 1: Add failing tests that reject ambiguous Transformer impedance basis.**
- [ ] **Step 2: Add failing tests for an existing PU transformer impedance with explicit base conversion to the study base.**
- [ ] **Step 3: Add failing tests for engineering transformer impedance using an explicitly defined engineering basis and rated MVA/voltage data.**
- [ ] **Step 4: Define and enforce the physical meaning of `r/x/b`; do not invent independent transformer shunt `b` semantics where the model does not support them.**
- [ ] **Step 5: Implement conversion inside `PowerFlowPreparation`, never inside `YBusBuilder`.**
- [ ] **Step 6: Ensure `YBusBuilder` accepts only `PreparedTransformer` numerical quantities and contains no transformer-unit inference.**
- [ ] **Step 7: Run targeted transformer/preparation/YBus tests.**

**Expected invariant:** Transformer engineering values are converted exactly once into system/study PU before numerical stamping.

---

### Task 4: Complete canonical Line/Cable/Transformer/Shunt engineering-to-PU preparation

**Files:**
- Modify: `core/analysis/power_flow_preparation.py`.
- Inspect: `core/model/line.py`, `core/model/cable.py`, `core/model/shunt.py`, `core/model/capacitor.py`, `core/model/reactor.py`.
- Modify: `core/numerical/ybus.py` only if required to consume the already-existing prepared representation; do not add conversion logic.
- Modify: targeted power-flow preparation tests.

**Interfaces:**
- Consumes: engineering Line R/X/B, Cable positive/zero-sequence engineering data, Transformer engineering/PU impedance, and reactive equipment engineering state.
- Produces: `PreparedBranch`, `PreparedTransformer`, and unified `PreparedShunt` records with stable equipment IDs.

- [ ] **Step 1: Add failing tests proving Line engineering R/X/B is converted once.**
- [ ] **Step 2: Add failing tests proving Cable positive-sequence engineering R/X/B is converted once and is not converted again downstream.**
- [ ] **Step 3: Add failing tests proving zero-sequence Cable data remains available for short-circuit preparation without contaminating positive-sequence power-flow data.**
- [ ] **Step 4: Add failing tests proving Capacitor/Reactor/other supported shunt engineering state becomes `PreparedShunt` with correct sign, voltage basis, in-service state, and deterministic bus identity.**
- [ ] **Step 5: Use one numerical `PreparedShunt` representation where the solver sees the same mathematical admittance quantity.**
- [ ] **Step 6: Ensure `YBusBuilder` only stamps the prepared shunt admittance and never reads live Capacitor/Reactor objects.**
- [ ] **Step 7: Run targeted preparation/YBus tests.**

---

### Task 5: Complete `.gridforge` persistence semantic round trip and explicit migration handling

**Files:**
- Modify: existing files under `core/persistence/` that implement Project save/load.
- Inspect/modify: project model/metadata serialization modules and SLD layout persistence modules already present.
- Modify: targeted persistence and migration tests.
- Create/modify: current status documentation if required to replace stale audit claims without deleting history.

**Interfaces:**
- Consumes: canonical `Project`, Network, equipment models, terminals/connections, topology/operating state, engineering electrical parameters, study state, SLD layout, and project metadata.
- Produces: `.gridforge/manifest.json`, `.gridforge/project.json`, and required project data with semantic round-trip equivalence.

- [ ] **Step 1: Add a failing semantic round-trip fixture covering project identity, equipment IDs/names/types, terminals, endpoints, connections, topology state, operating state, electrical engineering parameters, study-relevant state, SLD layout, and metadata.**
- [ ] **Step 2: Add explicit transformer `impedance_basis`/rating persistence coverage.**
- [ ] **Step 3: Add Line/Cable engineering-unit persistence coverage.**
- [ ] **Step 4: Add Bus/source/generator/reactive equipment operating-state persistence coverage.**
- [ ] **Step 5: Verify serialization stores canonical engineering values rather than derived PU values as authoritative engineering state.**
- [ ] **Step 6: Classify legacy values as proven engineering, proven PU, or ambiguous; reject ambiguous legacy electrical values with an explicit migration error instead of guessing.**
- [ ] **Step 7: Implement the smallest serializer/deserializer corrections required by the tests.**
- [ ] **Step 8: Run targeted persistence/migration tests only.**

**Expected invariant:** save/load yields semantic equivalence of engineering state without replacing engineering truth by derived PU state.

---

### Task 6: Freeze Power Flow result/configuration and immutable equipment-indexed snapshot contracts

**Files:**
- Modify: `core/analysis/power_flow_configuration.py` and current Power Flow analysis/result modules only where needed.
- Modify: `core/analysis/power_flow_preparation.py` and `core/analysis/power_flow_result_conversion.py` where identity-safe correlation is incomplete.
- Modify: targeted Power Flow/result tests.

**Interfaces:**
- Consumes: `PreparedPowerFlow`, stable equipment IDs, and explicit `PowerFlowStudyConfiguration`.
- Produces: immutable result structures and identity-safe mappings; no live Core object references.

- [ ] **Step 1: Add failing tests proving result correlation uses stable IDs rather than collection positions wherever an ID exists.**
- [ ] **Step 2: Add failing tests proving the authoritative study configuration explicitly carries the solver-required slack/reference bus, tolerance, iteration limit, base MVA, and preparation-relevant voltage data.**
- [ ] **Step 3: Add failing tests proving prepared branch/transformer/shunt records remain detached after Network mutation.**
- [ ] **Step 4: Implement only missing identity/configuration fields in the existing result/preparation contracts.**
- [ ] **Step 5: Run targeted Power Flow/result tests.**

---

### Task 7: Complete detached Short Circuit preparation and canonical equipment-current results

**Files:**
- Modify: `core/analysis/short_circuit.py`.
- Modify/inspect: `core/solver/short_circuit/*` and existing `SequenceNetworkSnapshot` implementation.
- Modify: supported source/generator/synchronous-machine preparation as required by current short-circuit scope.
- Modify: targeted short-circuit tests.

**Interfaces:**
- Consumes: authoritative engineering source/machine/sequence data and stable equipment identities.
- Produces: detached `SequenceNetworkSnapshot`, `ShortCircuitInput`, solver result, and canonical equipment-current results correlated by stable IDs.

- [ ] **Step 1: Add failing tests proving three-phase faults do not build a numerical network from live mutable Network state at solve time.**
- [ ] **Step 2: Add failing tests proving sequence snapshots are detached from live Core objects.**
- [ ] **Step 3: Add failing tests for supported source/rotating-machine short-circuit contributions using currently represented engineering data.**
- [ ] **Step 4: Add failing tests for stable bus/line/cable/transformer/source-machine result identity.**
- [ ] **Step 5: Implement only the missing preparation/result mappings; do not add unsupported machine models.**
- [ ] **Step 6: Run targeted short-circuit tests.**

---

### Task 8: Close Protection study/execution boundaries without creating a second protection platform

**Files:**
- Modify: existing `core/protection/*` relay, element, input, decision, and execution modules.
- Modify: existing breaker application command/manager path as required for trip mutation.
- Modify: measurement-to-relay input adapters already present.
- Modify: targeted protection tests.

**Interfaces:**
- Study path: `Network → detached protection-study snapshot → relay/protection analysis → ProtectionResult`.
- Execution path: `Measurement/Event → Relay → ProtectionDecision → Application command → Breaker → Core Network → topology`.

- [ ] **Step 1: Add failing tests for minimum engineering relay data required by currently implemented relay functions.**
- [ ] **Step 2: Add failing identity tests freezing `Relay`, `ProtectionElement`, and `RelayBase` semantics without introducing another relay abstraction.**
- [ ] **Step 3: Add a failing integration test proving a protection decision does not mutate a breaker directly and instead emits/dispatches the established Application command.**
- [ ] **Step 4: Add failing tests for the minimum breaker protection-grade fields actually required by implemented trip logic.**
- [ ] **Step 5: If the existing Fuse implementation is active, add only the required time-current representation tests.**
- [ ] **Step 6: Freeze supported function-code/function-ID settings already used by the current protection architecture.**
- [ ] **Step 7: Add tests proving protection study input is detached and cannot persistently alter the live Network.**
- [ ] **Step 8: Add tests for the minimum coordination data consumed by existing protection functions.**
- [ ] **Step 9: Implement the smallest missing adapters/contracts and run targeted protection tests.**

---

### Task 9: Complete the dynamic preparation boundary and sample timestamp ownership

**Files:**
- Modify: existing dynamic preparation/input modules under `core/simulation/` and/or `core/analysis/`.
- Modify: existing dynamic simulation sampling implementation containing `_record_sample()`.
- Modify: targeted dynamic simulation tests.

**Interfaces:**
- Consumes: validated engineering state and, where already supported, immutable Power Flow operating-point results.
- Produces: detached dynamic numerical initial state and time-stamped simulation samples consumed by the existing dynamics engine.

- [ ] **Step 1: Add a failing test proving dynamic preparation does not retain live Core equipment references.**
- [ ] **Step 2: Add a failing test proving an existing Power Flow result can be converted to a dynamic initial state without mutation.**
- [ ] **Step 3: Add a failing regression test proving `_record_sample()` records the actual simulation time rather than a hard-coded `0.0`.**
- [ ] **Step 4: Implement only the preparation/sample-time corrections required by those tests.**
- [ ] **Step 5: Explicitly leave AVR/governor/PSS/detailed machine dynamic models deferred unless an already-implemented feature requires them.**
- [ ] **Step 6: Run targeted dynamic tests only.**

---

### Task 10: Re-audit engineering model completeness for Bus/Line/Cable/Transformer/Breaker/Sources/Loads/Motor/Reactive/Measurement data

**Files:**
- Modify only the existing authoritative models/services under `core/model/`, `core/measurement/`, and `core/application/` where currently implemented studies require missing engineering fields.
- Modify targeted model-contract tests.

**Interfaces:**
- Consumes: currently implemented studies and their preparation requirements.
- Produces: explicit engineering contracts without future unsupported functionality.

- [ ] **Step 1: Verify Bus has all engineering study data currently consumed by preparation/analysis.**
- [ ] **Step 2: Verify Line R/X/B engineering units and Cable positive/zero-sequence engineering units are explicit.**
- [ ] **Step 3: Verify Transformer impedance basis/rating/voltage semantics are explicit.**
- [ ] **Step 4: Verify Breaker exposes only protection-grade data required by implemented trip logic.**
- [ ] **Step 5: Verify Grid/Generator/SynchronousMachine/Solar/Battery source contracts cover currently implemented power-flow/short-circuit needs without merging their semantics.**
- [ ] **Step 6: Verify Load classification is explicit where current power-flow support requires it, limited to supported constant-P/Q/current/impedance behavior.**
- [ ] **Step 7: Verify Motor has the minimum engineering data required by studies that currently claim Motor support.**
- [ ] **Step 8: Verify Capacitor/Reactor/Shunt engineering data can reach the unified numerical shunt representation.**
- [ ] **Step 9: Verify CT/PT/CVT/MeasurementPoint/MeasurementChannel semantics are explicit and remain distinct from the electrical Network.**
- [ ] **Step 10: Add/run targeted model-contract tests.**

---

### Task 11: Current-status audit ledger and final targeted verification

**Files:**
- Modify: `AUDIT_REPORT.md` only by preserving historical content and adding a clearly separated current status section, if required.
- Modify: `Modification_Register.txt` only by appending current remediation entries; never rewrite historical entries.
- Create: a current remediation status document if the historical files cannot cleanly represent the new status.

**Interfaces:**
- Consumes: implementation commits and targeted test evidence from Tasks 2–10.
- Produces: finding-by-finding status with CLOSED/PARTIALLY CLOSED/OPEN/OBSOLETE/DEFERRED classification.

- [ ] **Step 1: Re-run only the targeted tests associated with every changed logical boundary.**
- [ ] **Step 2: Confirm previously closed findings remain closed and identify any regression risk.**
- [ ] **Step 3: For every finding record symptom, root cause, contract violation, minimal correction, test, evidence, and remaining gap.**
- [ ] **Step 4: Mark findings CLOSED only where executable targeted evidence satisfies the definition of complete.**
- [ ] **Step 5: Mark dynamic detailed models DEFERRED where explicitly outside current scope.**
- [ ] **Step 6: Report Python version, exact targeted test commands, pass/fail/skip/error counts, and explicitly state that the full suite was not run.**
- [ ] **Step 7: Record the final architecture flows for engineering studies, Application/Core mutation, and protection.**

---

## Verification Commands Policy

Only targeted commands are permitted during this remediation. Examples must be narrowed to the affected tests, such as:

```bash
pytest tests/path/to/test_measurement.py -q
pytest tests/path/to/test_transformer.py -q
pytest tests/path/to/test_power_flow_preparation.py -q
pytest tests/path/to/test_persistence.py -q
pytest tests/path/to/test_short_circuit.py -q
pytest tests/path/to/test_protection.py -q
pytest tests/path/to/test_dynamic.py -q
```

The command `python -m pytest` without a test selection is prohibited for this task.

## Completion Gate

A finding is CLOSED only when implementation, contract, integration, targeted regression, and absence of a conflicting implementation are all demonstrated. The final report must distinguish CLOSED, PARTIALLY CLOSED, STILL OPEN, OBSOLETE, and DEFERRED findings and must not represent targeted verification as full-suite verification.
