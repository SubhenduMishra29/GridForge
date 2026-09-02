# Power Flow / Contingency Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit Network-to-PowerFlowInput/YBus preparation boundary and migrate ContingencyAnalysis to use isolated prepared numerical cases without passing live Core objects into Power Flow execution.

**Architecture:** Authoritative Network is read only during preparation. Each preparation produces an immutable PowerFlowInput and a separately prepared YBus with identical bus ordering; ContingencyAnalysis prepares those artifacts from an isolated deep-copied case Network and passes only those artifacts to PowerFlowAnalysis.

**Tech Stack:** Python, dataclasses, NumPy/SciPy numerical contracts, existing GridForge Core Network/BusIndex/YBus infrastructure.

**Spec:** `docs/superpowers/specs/2026-09-02-power-flow-contingency-preparation-design.md`

## Global Constraints

- No tests are added or run during this migration.
- Network remains authoritative for electrical membership, topology, and BusIndex.
- YBus remains a derived numerical representation under `core.numerical`.
- Numerical execution must never receive a live Network or other mutable Core object.
- Contingency outages must never mutate the authoritative Network.
- Do not invent missing electrical field mappings; stop and request clarification if repository evidence is insufficient.
- Preserve existing contingency result and violation semantics unless an architectural correction requires otherwise.

---

### Task 1: Repository correlation and Power Flow field mapping

**Files:**
- Inspect: `core/model/`
- Inspect: `core/network/`
- Inspect: `core/solver/power_flow/input.py`
- Inspect: `core/solver/power_flow/nr_solver.py`
- Inspect: `core/numerical/ybus.py`
- Inspect: `core/analysis/power_flow.py`
- Inspect: `core/analysis/contingency.py`

**Interfaces:**
- Consumes: existing Network, Bus, and solver contracts.
- Produces: confirmed field mapping for PowerFlowInput preparation and a list of any unresolved mappings.

- [ ] Fetch the current implementations on `feature/short-circuit-option-a`.
- [ ] Correlate every PowerFlowInput field with the authoritative Bus/model field used by the existing repository.
- [ ] Correlate bus ordering with authoritative Network.index.mapping and YBus.bus_ids.
- [ ] Correlate outage state with the fields consumed by YBusBuilder and Power Flow input preparation.
- [ ] If any required field cannot be established without assumption, stop and ask the user before modifying code.

### Task 2: Add the Power Flow preparation service

**Files:**
- Create: `core/analysis/power_flow_preparation.py`
- Inspect/possibly modify: `core/analysis/__init__.py`

**Interfaces:**
- Consumes: authoritative `Network`.
- Produces: `(PowerFlowInput, YBus)` prepared from the same Network state.
- Proposed public interface: `PowerFlowPreparation(network).prepare() -> tuple[PowerFlowInput, YBus]`.

- [ ] Implement read-only Network validation and require a valid authoritative BusIndex.
- [ ] Extract bus IDs in authoritative numerical order.
- [ ] Extract bus type, P/Q specification, Q limits, and initial voltage state using only confirmed model fields.
- [ ] Construct `PowerFlowInput` with immutable tuples.
- [ ] Construct `YBus` through the existing `YBusBuilder(network)`.
- [ ] Validate `PowerFlowInput.bus_ids == YBus.bus_ids` before returning.
- [ ] Ensure the preparation service does not mutate Network state.
- [ ] Export the service only if repository package conventions require it.
- [ ] Review the resulting file for live-Core references crossing the returned numerical boundary.

### Task 3: Refactor PowerFlowAnalysis integration

**Files:**
- Modify: `core/analysis/power_flow.py`
- Inspect: `core/solver/power_flow/`
- Correlate: all repository callers of `PowerFlowAnalysis`

**Interfaces:**
- Consumes: prepared `PowerFlowInput` and `YBus`.
- Produces: `PowerFlowResult` through the existing solver.

- [ ] Correlate current constructor callers before changing its public signature.
- [ ] Keep the numerical execution path limited to `PowerFlowInput + YBus + solver options`.
- [ ] If a compatibility facade is required by confirmed callers, place Network preparation at the analysis/preparation boundary rather than inside the solver.
- [ ] Remove any remaining path that passes a live Network into `PowerFlowAnalysis` execution.
- [ ] Preserve the existing solver result contract.

### Task 4: Migrate ContingencyAnalysis case execution

**Files:**
- Modify: `core/analysis/contingency.py`

**Interfaces:**
- Consumes: authoritative Network and isolated contingency case Network.
- Produces: existing `ContingencyCaseResult` and `ContingencyResult` with `PowerFlowResult` attached.

- [ ] Keep deep-copy isolation before outage mutation.
- [ ] Apply each outage only to the copied Network.
- [ ] Invoke `PowerFlowPreparation(case_network)` after outage state is applied.
- [ ] Pass only the returned `PowerFlowInput` and `YBus` into `PowerFlowAnalysis`.
- [ ] Preserve power-flow options and existing violation thresholds.
- [ ] Preserve case success/convergence/error aggregation semantics.
- [ ] Ensure no authoritative Network reference is passed to numerical execution.
- [ ] Remove stale documentation that says PowerFlowAnalysis accepts the copied Network directly.

### Task 5: Correlate contingency post-processing with prepared numerical results

**Files:**
- Modify if required: `core/analysis/contingency.py`
- Inspect: `core/solver/power_flow/result.py`

**Interfaces:**
- Consumes: standalone `PowerFlowResult` plus isolated case data where analysis-level violation detection needs it.
- Produces: unchanged contingency violations.

- [ ] Verify voltage violation detection reads the result rather than live solver state.
- [ ] Verify thermal violation detection uses the case Network only at analysis/post-processing scope where required.
- [ ] Confirm result objects do not retain live Network/Core references.
- [ ] Avoid moving engineering violation semantics into numerical solver code.

### Task 6: Documentation and package contract reconciliation

**Files:**
- Modify: `core/analysis/contingency.py` module documentation
- Modify if needed: `core/analysis/README.md`
- Modify if needed: `core/solver/power_flow/README.md`
- Modify if needed: `core/numerical/README.md`

**Interfaces:**
- Consumes: final implementation boundaries.
- Produces: documentation matching the frozen architecture.

- [ ] Replace stale diagrams showing `ContingencyAnalysis -> PowerFlowAnalysis(case_network)`.
- [ ] Document `Network -> PowerFlowPreparation -> (PowerFlowInput, YBus)`.
- [ ] Document contingency isolation before preparation.
- [ ] Do not describe YBus as authoritative Network state.

### Task 7: Final correlation and architectural check

**Files:**
- Inspect: all changed files
- Inspect: `core/analysis/contingency.py`
- Inspect: `core/analysis/power_flow.py`
- Inspect: `core/analysis/power_flow_preparation.py`
- Inspect: `core/solver/power_flow/`
- Inspect: `core/numerical/ybus.py`

**Interfaces:**
- Consumes: completed migration.
- Produces: verified repository architecture ready for freeze.

- [ ] Search for stale `PowerFlowAnalysis(case_network` and equivalent live-Network solver calls.
- [ ] Search numerical Power Flow code for `Network`, `self.network`, Bus/Line/Transformer live-object access, and callback paths.
- [ ] Verify YBus and PowerFlowInput bus ordering is identical.
- [ ] Verify contingency outage mutation is confined to copied Network instances.
- [ ] Verify no UI/Qt/SLD/Application dependency enters numerical execution.
- [ ] FETCH the final branch state after all writes.
- [ ] CHECK the final changed files against this plan and the design spec.
- [ ] Do not freeze until the final verification is complete.

## Verification Policy

Per project instruction, no tests are added or run for this migration. Verification is repository-level architectural inspection, caller correlation, final FETCH, and CHECK against the frozen contracts.
