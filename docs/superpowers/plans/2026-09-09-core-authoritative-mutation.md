# Core Authoritative Mutation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish one atomic, explicit Core mutation authority for Bus, Generator, Grid, Branch/Line, Transformer, and Terminal while preserving the frozen Network/Application architecture.

**Architecture:** Core model classes will expose explicit mutation operations that validate the complete proposed state before committing any field. Existing compatibility setters/methods remain only when they can delegate to the same Core authority. Application services and undo paths will call these Core APIs rather than directly assigning authoritative electrical state; Network topology, revisioning, snapshots, YBus, and solver preparation remain out of scope for this phase.

**Tech Stack:** Python 3.x repository code, existing GridForge Core validation conventions, pytest test suite, GitHub repository tooling, static repository searches, compile/import checks.

**Spec:** Approved GridForge V2 remediation master prompt, PHASE 1 — CORE AUTHORITATIVE MUTATION, findings GF-AUD-253 through GF-AUD-283.

## Global Constraints

- Core owns electrical truth.
- Application controls meaningful mutation.
- UI expresses intent/results and must not directly mutate Core objects.
- Network owns global structural/topology mutation; do not move Network responsibilities into Core in this phase.
- Every authoritative mutation must validate the complete proposed state before committing it.
- An invalid mutation must leave the pre-mutation state unchanged.
- Domain failures must use the repository's established domain-error contract rather than arbitrary ValueError/TypeError/AttributeError as the primary Application protocol.
- Terminal remains the local endpoint authority; preserve the canonical `Terminal → endpoint → resolve_terminal_bus() → Bus` resolution path, including adapter endpoints exposing `.bus`.
- Do not redesign numerical algorithms or implement Phase 2 revision/snapshot/topology architecture here.
- Constructors remain valid construction paths and may assign fields while building a new object.
- Internal field assignment is permitted inside the Core mutation implementation; external/Application direct assignment is not.
- Do not claim tests or completion without executing and inspecting the verification results.

---

## File Map

### Core authoritative models

- Modify: `core/model/bus.py` — add the Bus-level atomic mutation authority for name, nominal voltage, voltage state, frequency, and service state; retain terminal ownership and existing electrical semantics.
- Modify: `core/model/generator.py` — add atomic mutation for name, P/Q, voltage setpoint, Q limits, and service state; ensure Q-limit validation is performed against the proposed state before commit.
- Modify: `core/model/grid.py` — add atomic mutation for name, voltage/frequency, P/Q, short-circuit/X-R and sequence/grounding fields, and service state without duplicating endpoint authority.
- Modify: `core/model/branch.py` — add atomic mutation for branch electrical parameters, rating, name, service state, and endpoint replacement; make two-endpoint changes all-or-nothing.
- Modify: `core/model/line.py` — keep engineering aliases (`resistance`, `reactance`, `shunt_susceptance`) mapped to the Branch canonical state and route mutation through the same atomic Branch authority.
- Modify: `core/model/transformer.py` — add transformer-specific atomic mutation for tap and phase shift while using the inherited Branch mutation authority for shared state; preserve radians as canonical phase-shift storage and degrees as a conversion interface.
- Modify: `core/model/terminal.py` — strengthen endpoint replacement/detachment validation, ownership/compatibility checks, stable endpoint identity handling, and rollback-safe replacement without duplicating endpoint state.
- Inspect: `core/model/base.py` — preserve stable immutable object identity and the intentional mutability semantics of human-readable `name` while ensuring model-level mutation is authoritative.

### Error contract

- Inspect: `core/errors/` — locate the repository's existing domain exception hierarchy and use it for invalid caller contracts, invalid domain state, invalid structural relationships, and infrastructure failures; extend only if the current contract has a genuine missing category.

### Application boundary

- Modify: `core/application/services/model_service.py` — replace direct authoritative field assignments in `update_bus()`, `update_grid()`, `update_generator()`, and related update/undo paths with Core mutation calls; preserve the existing canonical Application ModelService and transaction/event behavior.
- Search/modify affected Application command handlers only where they directly assign Core authoritative fields after the ModelService boundary.

### Tests

- Inspect existing test layout first; add focused tests under the repository's established Core/Application test locations rather than creating a parallel test convention.
- Add tests for valid mutation, invalid mutation, atomic failure, endpoint replacement rollback, duplicate endpoint identity, invalid ownership, and Application routing through Core mutation APIs.

---

## Task 1: Establish the Core Domain Error Contract

**Files:**
- Inspect: `core/errors/`
- Modify only the existing error module(s) if a required category is genuinely absent.
- Test: repository's existing Core error tests, or create the smallest matching test file if none exists.

**Interfaces:**
- Consumes: existing GridForge exception hierarchy and validation conventions.
- Produces: stable Core exceptions for invalid caller contract, invalid domain state, invalid structural relationship, and infrastructure failure, with no unnecessary duplicate hierarchy.

- [ ] **Step 1: Locate and classify existing Core exceptions.**

Run repository searches for `class .*Error`, `DomainError`, `ValidationError`, `Invalid`, `Structural`, and imports from `core.errors`. Record which existing exception maps to each required failure category.

- [ ] **Step 2: Write failing tests for missing semantic categories only.**

Use the existing test conventions. A representative assertion must verify that an invalid Core mutation raises the semantic Core exception rather than relying on the exact text of a generic built-in exception.

- [ ] **Step 3: Add only the missing exception types.**

Keep the hierarchy minimal and make new types derive from the repository's established domain base error when one exists.

- [ ] **Step 4: Run the focused error tests.**

Run the exact test module created/found in Steps 1–3 and verify PASS before moving on.

- [ ] **Step 5: Commit.**

```bash
git add core/errors tests
git commit -m "fix(core): formalize mutation error contract"
```

---

## Task 2: Make Terminal Endpoint Mutation Atomic and Authoritative

**Files:**
- Modify: `core/model/terminal.py`
- Inspect: endpoint implementations and the canonical terminal-to-bus resolver.
- Test: existing terminal tests plus focused new Core terminal tests.

**Interfaces:**
- Consumes: Task 1 Core error contract.
- Produces: `Terminal.replace_endpoint(endpoint)`, `Terminal.detach()`, and `Terminal.attach(endpoint)` sharing one validation/commit path; failed replacement leaves the previous endpoint unchanged.

- [ ] **Step 1: Write failing tests for terminal invariants.**

Cover: valid attachment; invalid endpoint; endpoint without a stable non-empty `id`; invalid owner relationship; incompatible endpoint; replacement from endpoint A to endpoint B; failed replacement preserving A; duplicate endpoint identity rejection where the current contract requires uniqueness; and adapter endpoint objects exposing `.bus` remaining resolvable by the canonical resolver.

- [ ] **Step 2: Run the terminal tests and verify they fail for the missing behavior.**

Run the focused terminal test module with `pytest -q <terminal-test-path>` and inspect the failure rather than assuming the expected failure mode.

- [ ] **Step 3: Implement validation-before-commit.**

Refactor endpoint validation into a private validation phase that performs all ownership/compatibility/identity checks before `_endpoint` changes. Implement `replace_endpoint()` as the explicit replacement authority and make `attach()` delegate to it. Keep `detach()` as the canonical nulling operation.

- [ ] **Step 4: Verify resolver compatibility.**

Run the focused terminal and resolver tests and confirm that `Terminal.endpoint` remains the sole connectivity state and `Terminal → endpoint → resolve_terminal_bus() → Bus` still works for direct Bus endpoints and supported adapters.

- [ ] **Step 5: Commit.**

```bash
git add core/model/terminal.py tests
git commit -m "fix(core): establish terminal mutation authority"
```

---

## Task 3: Establish Atomic Bus Mutation

**Files:**
- Modify: `core/model/bus.py`
- Test: established Bus Core tests.

**Interfaces:**
- Consumes: Task 1 error contract and Task 2 Terminal authority.
- Produces: one explicit Bus mutation API, e.g. `Bus.update(...)`, whose exact keyword signature matches the fields actually present in the current class: `name`, `nominal_voltage_kv`, `voltage_pu`, `angle_deg`, `frequency_hz`, and `in_service`.

- [ ] **Step 1: Write failing tests for complete valid Bus updates.**

Assert that one call changes all requested fields and that terminal state is unchanged. Add invalid cases for non-positive voltage/frequency, negative nominal voltage, non-finite angle, and non-boolean service state.

- [ ] **Step 2: Add atomicity assertions.**

Capture all mutable authoritative fields before each invalid call and assert every field is byte/value-for-value unchanged afterward.

- [ ] **Step 3: Run focused Bus tests and confirm failure.**

Run the established Bus test module with `pytest -q <bus-test-path>`.

- [ ] **Step 4: Implement `Bus.update(...)`.**

Normalize all requested values into local variables, validate the complete proposed state, then perform one internal commit block. Existing setters such as `set_voltage()` and `set_in_service()` must either delegate to the same validation path or remain construction/compatibility helpers without creating a competing Application mutation authority.

- [ ] **Step 5: Run focused Bus tests and verify PASS.**

Run the Bus tests again and inspect failures for regressions in constructor validation, diagnostics, and voltage properties.

- [ ] **Step 6: Commit.**

```bash
git add core/model/bus.py tests
git commit -m "fix(core): make bus mutation atomic"
```

---

## Task 4: Establish Atomic Generator Mutation

**Files:**
- Modify: `core/model/generator.py`
- Test: established Generator Core tests.

**Interfaces:**
- Consumes: Task 1 error contract and Task 2 Terminal authority.
- Produces: `Generator.update(...)` covering name, `p`, `q`, `V_setpoint`, `q_min`, `q_max`, and `in_service`, with Q-limit validation performed against the proposed Q and proposed limits before commit.

- [ ] **Step 1: Write failing tests.**

Test a valid combined P/Q/setpoint/limit/service update. Test invalid Q outside proposed limits, invalid limits where min > max, invalid setpoint, and invalid service state. Assert atomic preservation for each failure.

- [ ] **Step 2: Run focused Generator tests and confirm failure.**

Run `pytest -q <generator-test-path>` and inspect the actual failure.

- [ ] **Step 3: Implement `Generator.update(...)`.**

Resolve unspecified fields to current values, validate every proposed value locally, validate proposed Q against proposed limits, then commit P/Q/setpoint/limits/service/name together. Do not call several public setters sequentially because that would permit partial mutation.

- [ ] **Step 4: Preserve compatibility APIs.**

Keep `set_power()`, `set_active_power()`, `set_reactive_power()`, `set_voltage_setpoint()`, `set_q_limits()`, and service methods working, but make them delegate to the same authoritative validation/commit primitives where practical.

- [ ] **Step 5: Run focused tests and verify PASS.**

Run Generator tests and any existing injection-contract tests.

- [ ] **Step 6: Commit.**

```bash
git add core/model/generator.py tests
git commit -m "fix(core): make generator mutation atomic"
```

---

## Task 5: Establish Atomic Grid Mutation

**Files:**
- Modify: `core/model/grid.py`
- Test: established Grid Core tests.

**Interfaces:**
- Consumes: Task 1 error contract and Task 2 Terminal authority.
- Produces: `Grid.update(...)` covering the actual Grid-owned electrical/engineering fields: name, nominal voltage, frequency, voltage/angle, P/Q, short-circuit data, X/R, sequence impedances, grounding, and service state.

- [ ] **Step 1: Write failing valid/invalid Grid mutation tests.**

Cover combined updates and invalid numeric/boolean/impedance combinations. Include an invalid multi-field update that would fail late and assert no earlier field changed.

- [ ] **Step 2: Run focused Grid tests and confirm failure.**

Run `pytest -q <grid-test-path>`.

- [ ] **Step 3: Implement atomic Grid mutation.**

Validate all proposed values into locals first. Sequence impedance validation must complete before any field is committed. Preserve endpoint ownership exclusively in Terminal and do not add a duplicate Bus field.

- [ ] **Step 4: Run Grid and injection tests.**

Verify power injection semantics and out-of-service zero injection remain unchanged.

- [ ] **Step 5: Commit.**

```bash
git add core/model/grid.py tests
git commit -m "fix(core): make grid mutation atomic"
```

---

## Task 6: Establish Atomic Branch and Line Mutation

**Files:**
- Modify: `core/model/branch.py`
- Modify: `core/model/line.py`
- Test: Branch and Line Core tests.

**Interfaces:**
- Consumes: Task 1 error contract and Task 2 Terminal authority.
- Produces: `Branch.update(...)` for name, r/x/b, rating, service state, and optional endpoint replacements; Line delegates engineering aliases to that same authority.

- [ ] **Step 1: Write failing Branch tests.**

Test combined electrical/service updates, invalid rating, invalid numeric values, and two-endpoint replacement where the second endpoint is invalid. Assert that neither endpoint nor any electrical field changes on failure.

- [ ] **Step 2: Run focused Branch tests and confirm failure.**

Run `pytest -q <branch-test-path>`.

- [ ] **Step 3: Implement Branch proposed-state validation.**

Normalize both proposed endpoints and all proposed branch fields before committing. Validate both endpoint references first; then commit the endpoint replacements and shared fields only after every check passes. Do not rely on sequential `set_from_endpoint()` / `set_to_endpoint()` calls for atomic multi-field mutation.

- [ ] **Step 4: Write and implement Line alias tests.**

Assert `resistance`, `reactance`, and `shunt_susceptance` always reflect canonical Branch `r`, `x`, and `b`, and invalid line impedance leaves all state unchanged. Keep the zero-series-impedance rule intact.

- [ ] **Step 5: Run Branch, Line, and electrical-model tests.**

Verify inherited validation and π-model behavior remain unchanged.

- [ ] **Step 6: Commit.**

```bash
git add core/model/branch.py core/model/line.py tests
git commit -m "fix(core): make branch mutation authoritative"
```

---

## Task 7: Establish Atomic Transformer Mutation and Unit Semantics

**Files:**
- Modify: `core/model/transformer.py`
- Test: Transformer Core tests.

**Interfaces:**
- Consumes: Task 6 Branch mutation authority.
- Produces: Transformer mutation for inherited Branch fields plus `tap` and canonical `shift` in radians; degree-facing compatibility remains a conversion interface only.

- [ ] **Step 1: Write failing Transformer tests.**

Test valid combined tap/shift and inherited branch updates. Test invalid tap, non-finite shift, invalid inherited branch state, and invalid phase-shift conversion input. Assert complete rollback on every invalid call.

- [ ] **Step 2: Run focused Transformer tests and confirm failure.**

Run `pytest -q <transformer-test-path>`.

- [ ] **Step 3: Implement proposed-state validation and one commit.**

Validate the complete inherited-plus-transformer state before assigning `_tap`, `_shift`, or inherited fields. Preserve `phase_shift_rad` as the canonical stored quantity and `phase_shift_deg` as a conversion view.

- [ ] **Step 4: Run Transformer and Branch tests.**

Confirm inheritance, topology independence, and electrical helper behavior remain unchanged.

- [ ] **Step 5: Commit.**

```bash
git add core/model/transformer.py tests
git commit -m "fix(core): make transformer mutation atomic"
```

---

## Task 8: Reconcile Application ModelService with Core Mutation Authority

**Files:**
- Modify: `core/application/services/model_service.py`
- Modify only directly affected Application command-handler files discovered by repository search.
- Test: established Application ModelService/command-handler tests.

**Interfaces:**
- Consumes: explicit Core `update(...)` APIs from Tasks 3–7.
- Produces: Application updates that invoke one Core mutation operation per authoritative model update and retain existing transaction, rollback, semantic-event, and command-handler boundaries.

- [ ] **Step 1: Write failing Application boundary tests.**

For Bus, Generator, and Grid update flows, replace/mocking the Core update API should show that ModelService calls it. Test that invalid Core mutations surface as the semantic domain error and that Application transaction rollback does not directly assign Core fields.

- [ ] **Step 2: Run focused Application tests and confirm failure.**

Run the relevant ModelService and handler tests with pytest and inspect actual failures.

- [ ] **Step 3: Replace direct Core assignments.**

Remove patterns such as `bus.name = ...`, `bus.nominal_voltage_kv = ...`, `grid.frequency_hz = ...`, and similar authoritative assignments from Application update paths. Build one proposed-state call to the relevant Core `update(...)` method. Preserve existing canonical Application ModelService routing and success-gated events.

- [ ] **Step 4: Repair undo/rollback paths.**

Capture pre-update values in Application transaction state, but restore through the same Core mutation API rather than direct field assignment. Do not introduce a second mutation service.

- [ ] **Step 5: Run Application tests.**

Run the affected ModelService, command-handler, transaction, and event tests and verify PASS.

- [ ] **Step 6: Commit.**

```bash
git add core/application tests
git commit -m "fix(application): route model updates through core authority"
```

---

## Task 9: Repository-Wide Direct-Mutation Audit and Classification

**Files:**
- Search entire repository; modify only confirmed violations.

**Interfaces:**
- Consumes: Core mutation APIs from Tasks 3–7 and Application routing from Task 8.
- Produces: no Application/UI/plugin direct mutation of authoritative Core state, with legitimate Core-internal construction/deserialization assignments explicitly classified.

- [ ] **Step 1: Search all direct assignments.**

Search for at least:

```text
.in_service =
.endpoint =
.nominal_voltage_kv =
.frequency_hz =
.name =
.p =
.q =
.p_mw =
.q_mvar =
.r =
.x =
.b =
.rate_mva =
.tap =
.shift =
```

Also search setters/properties that mutate the same state indirectly.

- [ ] **Step 2: Classify every hit.**

Allowed categories: constructor initialization, internal Core mutation commit, controlled deserialization/reconstitution where the architecture explicitly permits it, or legitimate non-authoritative projection/cache state. Violations include Application/UI/Controller/Tool/Plugin direct mutation of Core authoritative state.

- [ ] **Step 3: Write failing regression tests for representative violations.**

Where practical, make the affected object expose a test double or spy around its Core `update(...)` method and assert the caller routes through it rather than assignment.

- [ ] **Step 4: Fix confirmed violations only.**

Do not rewrite unrelated numerical or presentation code and do not move Network-owned structural mutation into Core.

- [ ] **Step 5: Re-run architecture searches.**

Confirm remaining assignments are all classified and legitimate.

- [ ] **Step 6: Commit.**

```bash
git add .
git commit -m "fix(core): remove external authoritative field mutation"
```

---

## Task 10: Phase 1 Verification Gate and Re-Audit

**Files:**
- Modify code/tests only if verification exposes a Phase 1 regression.
- No Phase 2 architecture work in this task.

**Interfaces:**
- Consumes: all previous Core/Application changes.
- Produces: evidence that Phase 1 is implemented without claiming success beyond executed checks.

- [ ] **Step 1: Run focused Core mutation tests.**

Run all newly added/affected Bus, Generator, Grid, Terminal, Branch, Line, and Transformer tests.

- [ ] **Step 2: Run affected subsystem tests.**

Run the complete Core model and Application service/command test groups identified from the repository test layout.

- [ ] **Step 3: Run the full test suite.**

Run the repository's standard full-suite command (normally `pytest -q` unless the project declares another command). Record failures verbatim and do not mark the gate passed if failures remain unexplained.

- [ ] **Step 4: Run import and compile checks.**

Run the project's import smoke checks and `python -m compileall` against the affected source tree.

- [ ] **Step 5: Run final architecture searches.**

Repeat the direct-mutation searches from Task 9 and verify UI/Application direction remains `UI → Application → Core/Network`.

- [ ] **Step 6: Re-audit Phase 1 findings.**

Explicitly mark GF-AUD-253 through GF-AUD-283 as fixed, partially fixed, or still open based only on repository evidence. Do not close any finding whose responsibility belongs to Phase 2.

- [ ] **Step 7: Create the phase commit only after verification.**

```bash
git add .
git commit -m "fix(core): establish authoritative mutation boundary"
```

The phase is complete only when the executed verification evidence supports it. Phase 2 must not start before this gate.

---

## Spec Coverage Self-Review

- Core mutation authority for Bus, Generator, Grid, Branch, Line, Transformer, Terminal: Tasks 2–7.
- Atomic validate-before-commit semantics: Tasks 2–7 and their rollback assertions.
- Error contract: Task 1 and Application propagation in Task 8.
- Terminal stable identity, owner, endpoint, compatibility, replacement, detach, duplicate identity, invalid endpoint: Task 2.
- Canonical endpoint-to-Bus resolver compatibility including `.bus` adapters: Task 2.
- Application direct-assignment removal and rollback repair: Task 8.
- Repository-wide direct assignment classification: Task 9.
- Regression tests for valid/invalid/atomic/endpoint/ownership behavior: Tasks 2–9.
- Focused, subsystem, full-suite, import, compile, and architecture verification: Task 10.
- Network revision, topology, BusIndex, NumericalSnapshot, YBus, solver-case architecture: deliberately excluded from Phase 1 and reserved for later phases.

## Placeholder Scan

No task depends on an unspecified new subsystem or a "do later" implementation. `<...-test-path>` in command examples is an execution-time reference to the repository's established test path that must be discovered before the command is run; it is not an implementation placeholder. Exact mutation signatures are defined from the inspected current model fields rather than invented fields.

## Type/Interface Consistency

- Terminal exposes `replace_endpoint()`, with `attach()` delegating to the same validation/commit path.
- Bus, Generator, Grid, Branch, and Transformer expose model-level `update(...)` APIs.
- Line consumes Branch's canonical r/x/b state and exposes engineering aliases.
- Application ModelService consumes the Core update APIs; it does not become a second mutation authority.
- Transformer stores phase shift in radians; degree APIs convert to/from that canonical state.
