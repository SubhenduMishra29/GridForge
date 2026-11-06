# Short-Circuit Option A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate short-circuit studies to the frozen Option A boundary: `ShortCircuitAnalysis` prepares an immutable `ShortCircuitInput`, `ShortCircuitSolver` performs numerical execution only, and `ShortCircuitResult` is standalone.

**Architecture:** `ShortCircuitAnalysis` is the canonical public study/use-case facade. It owns preparation and coordination but does not perform the numerical fault algorithms. `ShortCircuitSolver` and its calculation components execute only from immutable prepared numerical data; they must not retain or read live `Network`, `Bus`, `SequenceNetwork`, or other mutable Core objects during execution.

**Tech Stack:** Python, existing GridForge Core domain/numerical modules, immutable value/data objects using the repository's existing Python conventions. No Qt/UI dependencies are introduced.

**Spec:** Frozen GridForge V2 Short-Circuit Option A architecture in the repository architecture decisions: `Application / Study orchestration → ShortCircuitAnalysis → ShortCircuitInput → ShortCircuitSolver → ShortCircuitResult`.

## Global Constraints

- `ShortCircuitAnalysis` remains the canonical public study facade.
- `ShortCircuitSolver` is the numerical execution boundary.
- Numerical execution must never obtain live Core objects during execution.
- `SequenceNetwork` remains a preparation/container object; execution consumes an immutable sequence snapshot.
- `YBus` and other numerical representations remain separate from authoritative Network state.
- Applying numerical results back to Core is outside numerical execution.
- `ShortCircuit` is retained during this migration; do not delete it without explicit caller/API confirmation.
- Preserve existing supported fault mathematics and result information unless an interface change is explicitly required by the frozen boundary.
- No tests are to be added or run for this migration unless explicitly requested by the user.
- Do not introduce UI, Qt, Application, persistence, or SLD dependencies into the solver package.

---

## File Map

### Create
- `core/solver/short_circuit/input.py` — immutable `ShortCircuitInput` numerical execution contract.
- `core/solver/short_circuit/result.py` — standalone `ShortCircuitResult` numerical result contract.
- `core/solver/short_circuit/sequence_snapshot.py` — immutable snapshot of all sequence-network data required during execution.

### Modify
- `core/solver/short_circuit/sequence_network.py` — retain preparation/container responsibility and add an explicit snapshot conversion; do not allow the solver to depend on the mutable container.
- `core/solver/short_circuit/impedance_matrix.py` — remove live `Network` ownership; consume prepared numerical data and expose only numerical impedance operations.
- `core/solver/short_circuit/fault_calculator.py` — remove live `Network` ownership; accept prepared prefault voltage/data rather than reading `Bus` objects.
- `core/solver/short_circuit/symmetrical_fault.py` — preserve numerical formulas while changing its dependency from a live-Core-backed impedance object to prepared numerical impedance data.
- `core/solver/short_circuit/unsymmetrical_fault.py` — preserve existing LG/LL/LLG formulas while consuming the immutable sequence snapshot.
- `core/solver/short_circuit/short_circuit_solver.py` — replace `Network`/mutable `SequenceNetwork` constructor dependencies with `ShortCircuitInput`; return `ShortCircuitResult` and remove live-Core convenience paths.
- `core/solver/short_circuit/short_circuit.py` — retain only as a compatibility facade if caller correlation requires it; delegate to the canonical analysis/input/solver path and remove duplicate numerical orchestration.
- `core/solver/short_circuit/__init__.py` — export the frozen input, snapshot, result, and canonical solver contracts; preserve only intentionally supported compatibility exports.
- `core/analysis/short_circuit.py` — make `ShortCircuitAnalysis` the public study facade that prepares the immutable execution input and invokes `ShortCircuitSolver`.
- `core/analysis/contingency.py` — replace the stale direct `PowerFlowAnalysis(copied_network)` integration with the current prepared numerical Power Flow boundary when this migration reaches its dependent flow.
- `core/solver/short_circuit/README.md` or existing short-circuit documentation file — update ownership and dependency documentation to match the frozen boundary if such documentation is present in the current tree.

### Do not modify in this migration
- `core/model/*` authoritative equipment definitions.
- `core/network/*` authoritative membership/topology implementation.
- `core/numerical/ybus.py` ownership boundary.
- UI/SLD/Application modules except where an actual confirmed caller requires a public-facade integration update.

---

## Task 1: Lock the numerical contract from existing APIs

**Files:**
- Read: `core/solver/short_circuit/unsymmetrical_fault.py`
- Read: `core/solver/short_circuit/symmetrical_fault.py`
- Read: `core/solver/short_circuit/short_circuit.py`
- Read: `core/solver/short_circuit/short_circuit_solver.py`
- Read: `core/analysis/short_circuit.py`

**Interfaces:**
- Consumes: the existing fault-method signatures and returned result dictionaries already present in the repository.
- Produces: an explicit inventory of required input fields, fault types, prefault data, impedance data, and result fields. Existing result keys must be preserved unless the current implementation demonstrably cannot provide them under the new boundary.

- [ ] **Step 1: Record the existing public fault operations.**
  Preserve the currently implemented three-phase, LG, LL, and LLG operations and their accepted `FaultType` values.

- [ ] **Step 2: Record the existing result dictionaries.**
  Preserve all currently implemented common, sequence-current, ground-current, and phase-current result information. Do not invent fields that are not present in the current implementation.

- [ ] **Step 3: Record the live-Core reads.**
  Identify every read of `Network`, `Bus`, `SequenceNetwork`, or mutable impedance preparation performed by the solver path so each can be replaced by prepared input.

- [ ] **Step 4: Commit the contract decision in the implementation branch.**
  The resulting code must use only the recorded contract; no speculative compatibility fields are added.

---

## Task 2: Add immutable sequence execution snapshot

**Files:**
- Create: `core/solver/short_circuit/sequence_snapshot.py`
- Modify: `core/solver/short_circuit/sequence_network.py`

**Interfaces:**
- Consumes: `SequenceNetwork` sequence element impedances and optional positive/negative/zero matrices.
- Produces: an immutable sequence snapshot containing defensive, immutable copies of the sequence data required by the solver.

- [ ] **Step 1: Define the immutable snapshot.**
  Use an immutable data structure with separate positive, negative, and zero sequence data and immutable matrix storage. Preserve the existing distinction that missing `Z0` remains missing rather than being inferred.

- [ ] **Step 2: Add explicit snapshot creation to `SequenceNetwork`.**
  Add a method such as `snapshot()` that validates the current preparation state and returns the immutable snapshot. The method must copy data so later mutation of `SequenceNetwork` cannot affect an in-flight solve.

- [ ] **Step 3: Preserve legacy `total_impedance()` only as preparation/compatibility behavior.**
  Do not make solver execution depend on it. The snapshot must contain sufficient data for the execution path without reaching back to `SequenceNetwork`.

- [ ] **Step 4: Verify the snapshot boundary by inspection.**
  Confirm that the snapshot has no references to `SequenceNetwork`, `Network`, `Bus`, or other mutable Core objects.

- [ ] **Step 5: Commit.**
  Commit the snapshot boundary separately from solver migration.

---

## Task 3: Define immutable ShortCircuitInput and standalone ShortCircuitResult

**Files:**
- Create: `core/solver/short_circuit/input.py`
- Create: `core/solver/short_circuit/result.py`

**Interfaces:**
- Consumes: immutable sequence snapshot plus prepared numerical fault-study data.
- Produces: `ShortCircuitInput` for solver execution and `ShortCircuitResult` for completed numerical output.

- [ ] **Step 1: Define `ShortCircuitInput` as immutable.**
  It must carry the fault-study data needed by every supported fault calculation, including the immutable sequence snapshot and prepared prefault voltage/impedance data. It must not contain a live `Network`, `Bus`, or mutable `SequenceNetwork`.

- [ ] **Step 2: Define `ShortCircuitResult` as standalone.**
  Store the solver outcome without references to live Core or preparation objects. Preserve the existing fault result information, including fault type and numerical quantities currently returned by the calculation components.

- [ ] **Step 3: Define conversion/access semantics explicitly.**
  The solver receives one `ShortCircuitInput` and returns one `ShortCircuitResult`; result consumers do not need the preparation objects to interpret the numerical result.

- [ ] **Step 4: Commit.**
  Commit only the new immutable contracts and their exports needed at this stage.

---

## Task 4: Remove live Network ownership from impedance and prefault helpers

**Files:**
- Modify: `core/solver/short_circuit/impedance_matrix.py`
- Modify: `core/solver/short_circuit/fault_calculator.py`

**Interfaces:**
- Consumes: prepared numerical matrix/index data and prepared prefault voltage data.
- Produces: numerical impedance and prefault calculations without Core object access.

- [ ] **Step 1: Replace `ImpedanceMatrix(network)` with prepared numerical input.**
  The class must no longer store `self.network` or read `network.Ybus`/`network.buses`. Its construction must receive the already-prepared numerical matrix and bus-index mapping required to calculate Zbus/Thevenin quantities.

- [ ] **Step 2: Preserve Zbus/Thevenin numerical behavior.**
  Matrix inversion and impedance lookup remain in the numerical layer. No topology reconstruction is added here.

- [ ] **Step 3: Replace `FaultCalculator(network)` with prepared prefault data.**
  Remove iteration over `network.buses` and reads of `bus.V`/`bus.theta`. Prefault voltage must be supplied as prepared numerical data through `ShortCircuitInput` or the helper's direct numerical input.

- [ ] **Step 4: Remove Network-dependent diagnostics from numerical helpers.**
  `summary()`/`repr()` and similar methods must not inspect live Core objects. They may report prepared numerical state only.

- [ ] **Step 5: Commit.**
  Commit the helper-boundary migration separately.

---

## Task 5: Migrate the fault calculation engines to immutable data

**Files:**
- Modify: `core/solver/short_circuit/symmetrical_fault.py`
- Modify: `core/solver/short_circuit/unsymmetrical_fault.py`

**Interfaces:**
- Consumes: prepared numerical impedance data and immutable sequence snapshot.
- Produces: the same numerical fault quantities currently produced by the two calculation engines.

- [ ] **Step 1: Refactor `SymmetricalFault`.**
  Keep its three-phase fault formula and output fields, but remove the dependency chain that reaches a live Network through `ImpedanceMatrix`.

- [ ] **Step 2: Refactor `UnsymmetricalFault`.**
  Replace its `SequenceNetwork` dependency with the immutable sequence snapshot. Its LG, LL, and LLG calculations must operate entirely on snapshot values.

- [ ] **Step 3: Preserve existing numerical formulas.**
  Do not change the sequence-component equations or phase-current transformations merely because the ownership boundary changes.

- [ ] **Step 4: Preserve existing result information.**
  Keep the currently implemented common result quantities plus the sequence/ground/phase quantities for the respective fault types.

- [ ] **Step 5: Commit.**
  Commit the fault-engine dependency migration without introducing a new study facade here.

---

## Task 6: Convert ShortCircuitSolver into the numerical execution boundary

**Files:**
- Modify: `core/solver/short_circuit/short_circuit_solver.py`

**Interfaces:**
- Consumes: `ShortCircuitInput` and solver options/configuration that are themselves numerical/immutable.
- Produces: `ShortCircuitResult`.

- [ ] **Step 1: Remove live Core constructor dependencies.**
  `ShortCircuitSolver` must no longer accept or store `Network` or mutable `SequenceNetwork`.

- [ ] **Step 2: Execute only from `ShortCircuitInput`.**
  The solver must obtain bus index, prefault voltage, sequence data, impedance data, and fault configuration from the prepared input.

- [ ] **Step 3: Remove live Bus metadata reads.**
  Do not read `self.network.buses[bus_index]` for validation, prefault voltage, or result metadata. Any required bus identifier must already be part of the immutable numerical input.

- [ ] **Step 4: Remove Core-mutating/convenience behavior.**
  Methods such as live-Network `build_impedance_matrix()`/`get_thevenin_impedance()` must either be moved to preparation code or removed from the solver boundary. The solver itself remains an execution engine.

- [ ] **Step 5: Preserve fault dispatch.**
  Keep three-phase/LG/LL/LLG dispatch semantics, but make every branch consume the same immutable input boundary.

- [ ] **Step 6: Return `ShortCircuitResult`.**
  Normalize the calculation-engine output into the standalone result contract without retaining the input object in the result.

- [ ] **Step 7: Commit.**
  Commit the solver-boundary migration.

---

## Task 7: Make ShortCircuitAnalysis the canonical public study facade

**Files:**
- Modify: `core/analysis/short_circuit.py`

**Interfaces:**
- Consumes: authoritative Core/Network state at preparation time and study configuration.
- Produces: prepared `ShortCircuitInput`, invokes `ShortCircuitSolver`, and returns `ShortCircuitResult`.

- [ ] **Step 1: Keep the public facade name.**
  Preserve `ShortCircuitAnalysis` as the canonical analysis-level entry point and retain `ShortCircuitAnalyzer = ShortCircuitAnalysis` as compatibility unless caller correlation proves it can be removed.

- [ ] **Step 2: Move preparation into the analysis boundary.**
  Build the numerical snapshot needed by short-circuit execution before invoking the solver. Preparation may read live Core state; execution may not.

- [ ] **Step 3: Construct `ShortCircuitInput`.**
  The facade must construct the immutable input once all required numerical data is prepared.

- [ ] **Step 4: Invoke the solver using only the prepared input.**
  Do not call a solver API that accepts `Network`, `Bus`, or mutable `SequenceNetwork`.

- [ ] **Step 5: Fix fault-bus validation.**
  Ensure `_validate_fault_bus()` is actually invoked during request validation/preparation, preserving the existing explicit validation intent.

- [ ] **Step 6: Preserve convenience study methods.**
  `run_three_phase_fault`, `run_lg_fault`, `run_ll_fault`, and `run_llg_fault` must delegate to the canonical `run()` path rather than duplicate solver orchestration.

- [ ] **Step 7: Commit.**
  Commit the analysis-facade migration.

---

## Task 8: Collapse or preserve the legacy `ShortCircuit` facade based on confirmed callers

**Files:**
- Modify: `core/solver/short_circuit/short_circuit.py`
- Modify: `core/solver/short_circuit/__init__.py`

**Interfaces:**
- Consumes: confirmed repository callers and the canonical `ShortCircuitAnalysis` contract.
- Produces: either a minimal compatibility adapter or a removed duplicate API, based only on confirmed evidence.

- [ ] **Step 1: Re-run repository-wide caller searches.**
  Search for `ShortCircuit(`, imports of `ShortCircuit`, `ShortCircuitSolver(`, `ShortCircuitAnalysis(`, `ShortCircuitAnalyzer`, and all existing fault convenience methods.

- [ ] **Step 2: If callers exist, convert `ShortCircuit` to compatibility delegation.**
  It must not retain `Network`, construct its own calculation architecture, or maintain a second source of numerical truth. Its supported methods delegate to the canonical analysis facade.

- [ ] **Step 3: If no callers exist, retain the file only if external/public API compatibility is intentionally required.**
  Do not delete the class solely because GitHub search returned no internal callers; deletion requires explicit confirmation that the public compatibility surface is no longer required.

- [ ] **Step 4: Update package exports.**
  Export `ShortCircuitInput`, immutable sequence snapshot, `ShortCircuitResult`, and `ShortCircuitSolver`. Export `ShortCircuit` only if the confirmed compatibility contract requires it.

- [ ] **Step 5: Commit.**
  Commit compatibility cleanup separately from the core numerical migration.

---

## Task 9: Correlate dependent analyses and remove stale integration assumptions

**Files:**
- Modify: `core/analysis/contingency.py`
- Inspect: `core/analysis/line_flow.py`
- Inspect: `core/analysis/transformer_flow.py`

**Interfaces:**
- Consumes: current prepared numerical boundaries for dependent studies.
- Produces: no new solver architecture; only compatibility with the frozen numerical execution rule.

- [ ] **Step 1: Remove stale Power Flow integration in contingency analysis.**
  Replace direct construction of `PowerFlowAnalysis` around copied live Network objects with the repository's already-frozen `PowerFlowInput + YBus` preparation/execution boundary.

- [ ] **Step 2: Preserve contingency isolation.**
  Outage modifications remain isolated to the contingency preparation snapshot/copy; the authoritative live Network must not be mutated by a numerical solve.

- [ ] **Step 3: Audit line-flow and transformer-flow ownership.**
  Confirm whether they are study-level preparation/calculation components or violate the same numerical boundary. Do not migrate them speculatively in this short-circuit task; record any independent required migration as a separate architectural task if needed.

- [ ] **Step 4: Commit only confirmed dependent changes.**
  Do not bundle unrelated analysis migrations.

---

## Task 10: Documentation and package contract reconciliation

**Files:**
- Modify: `core/solver/short_circuit/__init__.py`
- Modify: existing short-circuit README/documentation file, if present
- Inspect: `core/analysis/__init__.py`
- Inspect: `core/numerical/README.md`

**Interfaces:**
- Consumes: final code ownership boundaries.
- Produces: documentation that states the same dependency direction as the implementation.

- [ ] **Step 1: Document the canonical flow.**
  State `ShortCircuitAnalysis → ShortCircuitInput → ShortCircuitSolver → ShortCircuitResult`.

- [ ] **Step 2: Document the sequence boundary.**
  State `SequenceNetwork → immutable sequence snapshot → ShortCircuitInput`; make clear that the solver does not consume the mutable preparation container.

- [ ] **Step 3: Document the no-live-Core rule.**
  State that numerical execution cannot access live Network/Bus/Core objects.

- [ ] **Step 4: Remove stale Network-owned YBus/solver wording.**
  Keep numerical ownership aligned with `core.numerical` and the already-frozen Power Flow boundary.

- [ ] **Step 5: Commit documentation/package reconciliation.**

---

## Task 11: Final repository correlation and architectural verification

**Files:**
- Inspect: all modified files above
- Inspect: repository-wide imports/usages of short-circuit APIs

**Interfaces:**
- Consumes: completed Option A implementation.
- Produces: verified repository state ready for freeze.

- [ ] **Step 1: Re-fetch every modified file from `main`.**
  Verify the committed contents rather than relying on local assumptions.

- [ ] **Step 2: Search for forbidden solver dependencies.**
  Confirm the short-circuit solver package has no execution-path dependency on `Network`, `Bus`, `SequenceNetwork`, UI, Qt, Application, or SLD objects.

- [ ] **Step 3: Search for duplicate public orchestration.**
  Confirm `ShortCircuitAnalysis` is the only canonical study facade and `ShortCircuit` is only an intentional compatibility adapter if retained.

- [ ] **Step 4: Search for stale constructor usage.**
  Confirm there are no remaining repository callers constructing the migrated `ShortCircuitSolver` with live `Network`/`SequenceNetwork`.

- [ ] **Step 5: Verify immutable execution isolation by code inspection.**
  Confirm mutating `SequenceNetwork` or Core after `ShortCircuitInput` preparation cannot alter the solver's input.

- [ ] **Step 6: Verify no tests were added or required.**
  This migration follows the explicit project constraint of no tests for now; verification is architectural/code/repository inspection only.

- [ ] **Step 7: Freeze only after all checks are clean.**
  Record the final commit SHA and freeze the short-circuit Option A boundary only after the post-change fetch/check cycle.

---

## Migration Order Summary

```text
1. Existing API/result contract inventory
          ↓
2. Immutable SequenceSnapshot
          ↓
3. ShortCircuitInput + ShortCircuitResult
          ↓
4. ImpedanceMatrix / FaultCalculator numerical boundary
          ↓
5. SymmetricalFault / UnsymmetricalFault boundary
          ↓
6. ShortCircuitSolver becomes numerical-only
          ↓
7. ShortCircuitAnalysis becomes preparation + orchestration facade
          ↓
8. ShortCircuit compatibility decision
          ↓
9. Dependent contingency integration
          ↓
10. Documentation / exports
          ↓
11. FETCH → CHECK → FREEZE
```

## Verification Gate

The migration is complete only when all of the following are true:

- `ShortCircuitAnalysis` is the canonical public study facade.
- `ShortCircuitSolver` accepts prepared immutable numerical input rather than live Core objects.
- `ShortCircuitInput` contains no live Core references.
- Sequence execution uses an immutable snapshot rather than mutable `SequenceNetwork`.
- `ShortCircuitResult` contains no live Core/preparation references.
- `ImpedanceMatrix` and `FaultCalculator` no longer read live Network/Bus state during numerical execution.
- Existing three-phase/LG/LL/LLG numerical behavior and result information are preserved.
- `ShortCircuit` is either an explicitly retained compatibility adapter or is removed only after explicit approval.
- No stale repository caller uses the old solver constructor/API.
- Documentation and exports agree with the implementation.
- No tests are added or required under the current project constraint.
- Final post-change FETCH and CHECK are complete before FREEZE.
