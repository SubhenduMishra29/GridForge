# GF-AUD-207/208 Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish one authoritative engineering-unit → per-unit Power Flow preparation boundary and an explicit per-unit → engineering result boundary without weakening GridForge V2 ownership rules.

**Architecture:** `core.analysis.PowerFlowPreparation` becomes the authoritative Analysis boundary. It consumes Core engineering quantities, uses the canonical `core.base.per_unit.PerUnitSystem` with an explicit study `base_mva`, and emits an immutable `PreparedPowerFlow` containing PU-only numerical input plus YBus. Solver code receives only the prepared numerical snapshot. A separate Analysis/result conversion boundary converts numerical results back to structured engineering values using the applicable study and bus reference bases.

**Tech Stack:** Python, dataclasses, NumPy/SciPy, pytest, existing GridForge Core/Analysis/Numerical/Solver contracts.

**Spec:** User-provided GF-AUD-207 + GF-AUD-208 remediation specification in the task request.

## Global Constraints

- Preserve GridForge V2 architecture and Command Rule.
- Core/UI/Application remain engineering-facing; Numerical/Solver remain PU-only for Power Flow.
- Reuse `core.base.per_unit.PerUnitSystem`; create no duplicate PU framework.
- `PowerFlowInput.bus_ids` and `index_of(bus_id)` remain authoritative numerical ordering.
- `PreparedPowerFlow` remains `@dataclass(frozen=True, slots=True)` and detached from mutable Core state.
- Do not add duplicated PU state to Core equipment models.
- Do not modify GF-AUD-204/205/206 unless direct compatibility is proven.
- TDD is mandatory: failing focused test before production change.
- Every newly created or substantially modified GridForge V2 file retains/adds `Author: Subhendu Mishra` in the established header style.
- Do not claim completion without executed passing tests.

---

## Current Audit Baseline

The current repository commit is `1263494808d660d1de4473a9d1942baa867fbb89` (`main`). The branch `remediation/gf-aud-207-208` is based on that commit.

Confirmed architectural facts from the current tree:

1. `core/analysis/power_flow_preparation.py` currently prepares `PowerFlowInput` from aggregated `Injection.get_power()` values, so the Analysis path does not yet enforce the required engineering→PU boundary.
2. `core/solver/power_flow/preparation.py` is a second preparation implementation and performs direct base-MVA division, creating competing preparation authority.
3. `core/analysis/power_flow_configuration.py` and `core/solver/power_flow/study_configuration.py` are competing study-configuration types; the solver-side type already validates `base_mva`.
4. `PowerFlowInput` is already immutable/numerical and exposes canonical `bus_ids` plus `index_of(bus_id)`.
5. `PreparedPowerFlow` is already immutable and validates input/YBus bus ordering.
6. `core.base.per_unit.PerUnitSystem` already provides the canonical MW/MVAr/kV/kA/impedance conversions and validates `base_mva`.
7. The low-level solver receives numerical input rather than Core objects, which should be preserved.
8. `PowerFlowResult` remains numerical/PU and needs an explicit engineering-result conversion boundary.
9. YBus construction and branch/transformer stored-unit semantics require an evidence-based audit before any conversion is introduced.
10. Generator `V_setpoint` is documented as PU; `p`, `q`, `q_min`, and `q_max` require repository evidence before their engineering-unit contract is enforced.

---

## Task 1: Establish focused configuration and preparation tests (RED)

**Files:**
- Modify: existing Power Flow analysis tests/configuration tests discovered during repository audit.
- Test: the repository's existing Power Flow preparation/configuration test module(s).

**Interfaces:**
- `PowerFlowStudyConfiguration(..., base_mva=...)` must expose validated `base_mva`.
- `PowerFlowPreparation` must consume the canonical Analysis configuration.

- [ ] **Step 1: Add failing tests for `base_mva` validation**
  - Accept finite positive values.
  - Reject `0.0`, negative values, `NaN`, and infinities.

- [ ] **Step 2: Add a failing normalization integration test**
  - Build a minimal network whose aggregated injection is `50 MW + j20 MVAr`.
  - Configure `base_mva=100`.
  - Assert prepared numerical P/Q are `0.5` and `0.2` PU, not `50` and `20`.

- [ ] **Step 3: Add failing Q-limit tests**
  - With `q_min=-10 MVAr`, `q_max=30 MVAr`, `base_mva=100`, assert `-0.1 PU` and `0.3 PU` reach the numerical input.

- [ ] **Step 4: Add failing bus-specific voltage-base tests**
  - Use buses with distinct nominal voltages (for example 11 kV and 33 kV).
  - Assert engineering↔PU voltage conversion uses each bus's own nominal voltage rather than a global voltage base.

- [ ] **Step 5: Add failing numerical-purity and ordering tests**
  - Assert `PowerFlowInput` contains normalized numerical values.
  - Assert `PowerFlowInput.bus_ids == YBus.bus_ids`.
  - Assert `index_of(bus_id)` remains the lookup authority.

- [ ] **Step 6: Run only the focused tests and verify the failures are caused by the missing contract**
  - Expected: RED failures for missing `base_mva`/normalization/result-boundary behavior, not import or syntax errors.

---

## Task 2: Canonicalize Power Flow study configuration

**Files:**
- Modify: `core/analysis/power_flow_configuration.py`.
- Modify/remove/quarantine: `core/solver/power_flow/study_configuration.py` only after consumer tracing proves it is the competing legacy authority.
- Modify: imports/exports/consumers discovered by audit.

**Interfaces:**
- Analysis `PowerFlowStudyConfiguration` owns `base_mva: float`.
- Validation requires finite and strictly positive `base_mva`.
- Existing bus-type behavior is preserved.

- [ ] **Step 1: Confirm all constructors/importers of both configuration classes**
  - Search the complete repository before editing.
  - Record every active consumer.

- [ ] **Step 2: Implement `base_mva` validation in the authoritative Analysis configuration**
  - Do not duplicate a new validation abstraction.
  - Preserve existing fields and compatibility where possible.

- [ ] **Step 3: Migrate active consumers to the canonical configuration**
  - Keep the solver numerical API independent from study configuration.

- [ ] **Step 4: Quarantine/remove the competing solver-side configuration only if the audit proves it has no required independent responsibility**
  - Do not delete referenced functionality.

- [ ] **Step 5: Run the Task 1 focused configuration tests**
  - Expected: configuration tests GREEN; normalization tests may remain RED.

---

## Task 3: Canonicalize Power Flow preparation and engineering→PU normalization

**Files:**
- Modify: `core/analysis/power_flow_preparation.py`.
- Modify: relevant numerical input construction code only where required by the established contract.
- Test: focused preparation tests.

**Interfaces:**
- `PowerFlowPreparation` creates/uses `PerUnitSystem(configuration.base_mva)`.
- `PreparedPowerFlow` continues to contain only immutable numerical `PowerFlowInput` and `YBus`.

- [ ] **Step 1: Write/retain the failing end-to-end preparation test before implementation changes**
  - The test must prove an engineering `50 MW + j20 MVAr` injection crosses the boundary as `0.5 + j0.2 PU`.

- [ ] **Step 2: Implement the canonical `PerUnitSystem` at the preparation boundary**
  - No manual `/ base_mva` formulas where the canonical API supports the conversion.

- [ ] **Step 3: Normalize all active Power Flow injection specifications consistently**
  - Generator/Grid/Load/Solar/Battery/Motor/SynchronousMachine semantics must be taken from current constructors/tests/services.
  - Do not assume units without repository evidence.

- [ ] **Step 4: Normalize generator Q limits at the same boundary**
  - Preserve `V_setpoint` as PU if current repository evidence confirms that contract.
  - Convert only engineering Q limits.

- [ ] **Step 5: Preserve initial `Bus.voltage_pu` as numerical PU**
  - Do not unnecessarily reconvert an already-PU Core field.

- [ ] **Step 6: Run focused preparation tests and verify GREEN**

---

## Task 4: Remove competing solver-side Power Flow preparation authority

**Files:**
- Modify/quarantine: `core/solver/power_flow/preparation.py`.
- Modify: all active imports/callers discovered by repository-wide search.
- Test: normal Power Flow execution path and legacy-path regression tests.

**Interfaces:**
- Normal execution is exactly `Network + PowerFlowStudyConfiguration → Analysis PowerFlowPreparation → PreparedPowerFlow → Solver`.
- Solver does not prepare P/Q, classify Core buses independently, or build an alternative prepared input.

- [ ] **Step 1: Trace every reference to solver-side preparation**
- [ ] **Step 2: Add a failing regression test demonstrating the normal solver execution uses the canonical Analysis preparation**
- [ ] **Step 3: Redirect/remove the active legacy execution path without deleting still-required numerical functionality**
- [ ] **Step 4: Remove duplicated engineering conversion from solver preparation**
- [ ] **Step 5: Run Power Flow execution tests**
- [ ] **Step 6: Verify no active second preparation authority remains**

---

## Task 5: Audit and lock branch/transformer/YBus numerical contracts

**Files:**
- Inspect/modify only as evidence requires: `core/model/branch.py`, `core/model/line.py`, `core/model/transformer.py`, `core/model/cable.py`, `core/model/shunt.py`, `core/numerical/ybus.py`, related constructors/services/tests.
- Test: YBus/preparation numerical contract tests.

**Interfaces:**
- `YBusBuilder` consumes already-established numerical quantities in its documented basis.
- It does not create a study base or interpret UI/application state.

- [ ] **Step 1: Trace constructors, defaults, docs, tests, and call sites for Line/Branch/Transformer/Cable/Shunt electrical values**
- [ ] **Step 2: Classify each consumed quantity as already-PU or engineering**
- [ ] **Step 3: If already-PU, make the naming/documentation explicit without changing numerical semantics**
- [ ] **Step 4: If engineering, add conversion only at the established preparation boundary using authoritative bases**
- [ ] **Step 5: Add regression tests proving YBus receives the established numerical basis**
- [ ] **Step 6: Run YBus and Power Flow numerical tests**

No blind conversion of Line/Transformer values is permitted.

---

## Task 6: Add explicit numerical→engineering Power Flow result conversion

**Files:**
- Create or modify the existing appropriate Analysis result-conversion module identified by repository structure.
- Test: focused result conversion tests.

**Interfaces:**
- Input: numerical `PowerFlowResult` plus authoritative study/base information and bus nominal voltage where required.
- Output: structured engineering quantities, not UI strings or Qt objects.

- [ ] **Step 1: Add failing tests for PU voltage → kV using each bus's nominal voltage**
- [ ] **Step 2: Add failing tests for PU P/Q/S → MW/MVAr/MVA using study `base_mva`**
- [ ] **Step 3: Add failing current conversion test only where the existing numerical result contract supplies enough information to determine the applicable current base**
- [ ] **Step 4: Implement conversions through canonical `PerUnitSystem`**
- [ ] **Step 5: Keep `PowerFlowResult` numerical-only**
- [ ] **Step 6: Run focused result tests and verify GREEN**

---

## Task 7: Preserve line/transformer numerical result contracts

**Files:**
- Inspect/modify only as necessary: `core/analysis/line_flow.py`, `core/analysis/transformer_flow.py`, result conversion module, related tests.

**Interfaces:**
- `LineFlowResult` and `TransformerFlowResult` remain numerical result objects.
- Engineering values are obtained through the result-conversion boundary.

- [ ] **Step 1: Add failing tests for the established numerical result fields remaining PU/numerical**
- [ ] **Step 2: Add engineering conversion tests only for quantities already present in those result objects**
- [ ] **Step 3: Implement the smallest compatible conversion**
- [ ] **Step 4: Run focused line/transformer result tests**

Do not invent missing result quantities.

---

## Task 8: Add full boundary integration test

**Files:**
- Test: appropriate existing Power Flow integration test module, or create a focused integration test with established repository test conventions.

**Interfaces:**
- Proves the complete path:
  `engineering Core input → PowerFlowPreparation → PerUnitSystem → PowerFlowInput/YBus → solver → numerical result → engineering result conversion`.

- [ ] **Step 1: Construct a minimal real repository Network using existing Core models**
- [ ] **Step 2: Supply engineering-unit injection values and explicit `base_mva`**
- [ ] **Step 3: Execute the actual normal Power Flow preparation and solver path**
- [ ] **Step 4: Assert values entering `PowerFlowInput` are PU**
- [ ] **Step 5: Execute the real result conversion boundary**
- [ ] **Step 6: Assert the resulting engineering voltage/power values match the expected physical quantities**
- [ ] **Step 7: Assert `PreparedPowerFlow` remains immutable**
- [ ] **Step 8: Assert canonical bus ordering is shared by input and YBus**
- [ ] **Step 9: Run the integration test and verify GREEN**

This is the acceptance proof and must not be replaced by isolated conversion-unit tests.

---

## Task 9: Regression and architecture audit

**Files:**
- Modify only files required by discovered regressions.

- [ ] **Step 1: Run focused GF-AUD-207/208 tests**
- [ ] **Step 2: Run Core/Analysis/Numerical/Solver Power Flow suites**
- [ ] **Step 3: Run the relevant full repository test suite**
- [ ] **Step 4: Search for remaining direct engineering→PU conversion outside the Analysis/Preparation boundary**
- [ ] **Step 5: Search for remaining active Power Flow preparation paths**
- [ ] **Step 6: Search for UI/Application PU conversion logic**
- [ ] **Step 7: Search for duplicate `PerUnitSystem`/base-MVA helpers**
- [ ] **Step 8: Record unrelated pre-existing failures separately; do not silently change unrelated architecture**

---

## Task 10: Final verification and branch handoff

- [ ] **Step 1: Verify modified/new files contain `Author: Subhendu Mishra` while preserving existing headers**
- [ ] **Step 2: Inspect `git diff` for scope leakage into GF-AUD-204/205/206**
- [ ] **Step 3: Verify no duplicated Core PU state was introduced**
- [ ] **Step 4: Verify the normal solver path consumes only the immutable prepared numerical snapshot**
- [ ] **Step 5: Verify the complete integration test passes**
- [ ] **Step 6: Run final relevant test suites and record exact results**
- [ ] **Step 7: Commit the remediation in logical commits on `remediation/gf-aud-207-208`**

### Completion standard

The remediation is complete only when the repository demonstrates one active Power Flow preparation authority, an explicit validated study `base_mva`, canonical `PerUnitSystem` conversion at the Analysis boundary, PU-only numerical execution, bus-specific voltage bases, normalized Q limits, immutable `PreparedPowerFlow`, and an explicit structured numerical→engineering result boundary, with the full path proven by an integration test.
