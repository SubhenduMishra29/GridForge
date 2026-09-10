# GridForge V2 Open-Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved GridForge V2 remediation contracts for the currently open/partial engineering and protection integration findings without disturbing closed findings.

**Architecture:** Preserve the existing Core/Network, analysis preparation, numerical solver, protection, application, persistence, and SLD boundaries. Add only the missing canonical contracts and adapters required to connect short-circuit results through explicit measurement binding and protection evaluation to an Application-owned breaker trip mutation; keep numerical solvers detached from live Core objects and keep UI/SLD as projections.

**Tech Stack:** Python, existing GridForge domain/numerical architecture, immutable dataclasses/value objects where existing conventions use them, existing Application command/service patterns, JSON `.gridforge` persistence.

**Spec:** Approved GridForge V2 Design Section 2 — component-by-component remediation contract established in the current conversation.

## Global Constraints

- Audit authority: `SubhenduMishra29/GridForge`; implementation authority: `madhuri196mishra-cpu/GridForge`.
- Implementation starts from current HEAD `f6b4f7cf61c77bafb7dfe1f4c62c18d0409590ac`.
- Do not reopen closed findings unless implementation evidence exposes a regression.
- Core owns electrical truth; Application owns authoritative mutation orchestration; UI/SLD never owns electrical truth.
- Analysis preparation converts engineering data to numerical inputs; numerical builders/solvers do not infer engineering bases or consume live Network objects.
- No second PU system, command system, control system, registry architecture, or mega-manager.
- No silent omission, inferred terminal identity, inferred transformer basis, inferred CT/PT ratio, or dropped SC contribution.
- Short-circuit source semantics explicitly support Grid, Generator, SynchronousMachine, and Motor only where current engineering models provide sufficient semantics; unsupported semantics must be explicit, not silently converted.
- SC calculation status is separate from contribution completeness and must expose `COMPLETE`, `PARTIAL`, `UNAVAILABLE`, or `FAILED` plus diagnostics.
- `values: Mapping[str, Any]` remains compatibility-only when retained; typed SC result/contribution contracts are primary.
- Protection decision objects do not mutate breakers, Network, Topology, or UI.
- Measurement chain is PU → engineering physical quantity → CT/PT/CVT transformation → MeasurementChannel → RelayInput.
- Tests are deferred by user instruction; do not claim executable verification until tests/verification are explicitly authorized and run.

---

### Task 1: Reconcile current repository structure and preserve existing SC-09 remediation

**Files:**
- Inspect: `core/analysis/**`, `core/protection/**`, `core/network/**`, `core/application/**`, `core/model/**`, persistence and SLD modules.
- Modify: none unless a directly blocking import/type mismatch is found during later tasks.

**Interfaces:**
- Consumes: current HEAD `f6b4f7cf61c77bafb7dfe1f4c62c18d0409590ac`.
- Produces: confirmed file map used by all subsequent tasks.

- [ ] Step 1: Reconfirm the implementation branch still starts at the recorded HEAD and compare the audit and implementation trees for the target modules.
- [ ] Step 2: Locate the existing SequenceNetworkSnapshot, SC preparation/result, ProtectionDecision, breaker switching, persistence, and SLD implementations.
- [ ] Step 3: Preserve the existing GF-EDM-054/SC-09 snapshot/result work and identify exact extension points rather than replacing it.
- [ ] Step 4: Record any current naming collision before adding canonical contracts.

---

### Task 2: Establish typed short-circuit source/contribution/result contracts

**Files:**
- Modify: existing SC result/contribution modules identified in Task 1.
- Create: only narrowly scoped typed contract modules if the existing files have no suitable ownership boundary.

**Interfaces:**
- Consumes: existing SC solver output and SequenceNetworkSnapshot.
- Produces: `ShortCircuitResult`, `ShortCircuitSourceContribution`, `ShortCircuitBranchCurrent`, `ShortCircuitEquipmentCurrent` with stable IDs and explicit status/diagnostics.

- [ ] Step 1: Define typed result fields for fault bus/sequence quantities, calculation status, contribution completeness/status, and diagnostics using existing project conventions.
- [ ] Step 2: Define source contribution fields `source_id`, `source_type`, `bus_id`, `Z1`, `Z2`, `Z0`, internal voltage, operating state, and contribution quantities without assuming motor-as-generator semantics.
- [ ] Step 3: Define branch/equipment contribution records using stable equipment IDs and explicit quantities.
- [ ] Step 4: Adapt the existing SC result conversion path so typed fields are populated without removing compatibility accessors.
- [ ] Step 5: Make incomplete source/branch/equipment contributions explicit through status and diagnostics instead of dropping records.
- [ ] Step 6: Keep KCL consistency checking deterministic and expose failure/incompleteness diagnostically rather than hiding it.

---

### Task 3: Complete engineering-to-numerical preparation boundaries

**Files:**
- Inspect/modify: `core/analysis/power_flow_preparation.py`, reactive preparation modules, transformer preparation modules, and related numerical preparation contracts.
- Inspect/modify: existing sequence-network/SC preparation modules.

**Interfaces:**
- Consumes: Core engineering equipment/state/study configuration.
- Produces: detached prepared numerical inputs containing explicit bases, admittances/impedances, states, stable IDs, and no live Core references.

- [ ] Step 1: Verify the existing PowerFlow preparation path has one authoritative study configuration and no duplicate PU conversion.
- [ ] Step 2: Add/complete prepared reactive-element records for shunt/capacitor/reactor equipment with explicit units, sign, state, and study base.
- [ ] Step 3: Ensure transformer impedance basis conversion occurs exactly once in preparation with explicit base MVA/base voltage; reject missing/ambiguous basis instead of inferring it.
- [ ] Step 4: Ensure YBus builders consume prepared numerical data only and do not perform engineering conversion.
- [ ] Step 5: Ensure SC preparation captures explicit source snapshots and rotating-machine semantics, including explicit unsupported handling for motors when the current model cannot provide the required contribution semantics.

---

### Task 4: Implement canonical ProtectionMeasurementBinding

**Files:**
- Create: `core/protection/protection_measurement_binding.py` (or the existing protection-study binding module if Task 1 identifies the canonical owner already).
- Modify: protection package exports and SC/protection study integration points.

**Interfaces:**
- Consumes: `ShortCircuitResult` typed quantities, source equipment/terminal identity, physical CT/PT/CVT model, MeasurementChannel, RelayInput.
- Produces: canonical binding containing `binding_id`, source equipment, source terminal, electrical side, measurement type, phase/sequence quantity, result quantity, instrument, channel, and relay input.

- [ ] Step 1: Define an immutable binding contract with explicit required identities and measurement semantics.
- [ ] Step 2: Require source equipment ID and terminal ID to resolve through authoritative Core topology; do not use collection position or inferred terminal order.
- [ ] Step 3: Require explicit electrical side and phase/sequence quantity where applicable.
- [ ] Step 4: Require explicit instrument identity/ratio and reject missing CT/PT/CVT transformation data.
- [ ] Step 5: Reject ambiguous result-quantity mappings with structured diagnostics.
- [ ] Step 6: Export the canonical binding from the protection package and wire it into the protection-study preparation path.

---

### Task 5: Implement measurement generation and MeasurementChannel

**Files:**
- Create: narrowly scoped measurement-channel/generation modules if canonical types are absent.
- Modify: existing measurement modules and protection-study preparation modules.

**Interfaces:**
- Consumes: `ProtectionMeasurementBinding`, typed SC result quantity, explicit electrical base, CT/PT/CVT instrument definition.
- Produces: physical engineering quantity and `MeasurementChannel` carrying a stable signal identity and value/quality metadata.

- [ ] Step 1: Define `MeasurementChannel` as a logical signal path, distinct from MeasurementPoint and RelayInput.
- [ ] Step 2: Implement current conversion as `Ipu → Ibase → Iprimary → CT ratio → Isecondary`.
- [ ] Step 3: Implement voltage conversion as `Vpu → Vbase → Vprimary → PT/CVT ratio → Vsecondary`.
- [ ] Step 4: Ensure instrument ratios are never applied directly to PU values.
- [ ] Step 5: Propagate source IDs, terminal/side identity, quantity identity, and diagnostics through the channel.
- [ ] Step 6: Reject missing bases or ratios rather than silently generating a value.

---

### Task 6: Implement canonical RelayInput and connect ProtectionFunction evaluation

**Files:**
- Create/modify: canonical RelayInput module following existing protection package ownership.
- Modify: existing `ProtectionDecision`/`ProtectionElement`/relay function modules only at their established integration boundary.

**Interfaces:**
- Consumes: `MeasurementChannel`.
- Produces: typed `RelayInput` and existing immutable `ProtectionDecision`.

- [ ] Step 1: Define RelayInput as the binding from a MeasurementChannel to a protection-function input, with stable identities and quantity semantics.
- [ ] Step 2: Map channel values into the existing protection function interface without introducing a second relay architecture.
- [ ] Step 3: Preserve `ProtectionDecision` immutability and its prohibition on direct breaker/network mutation.
- [ ] Step 4: Propagate measurement quality/diagnostics so a protection function cannot silently evaluate invalid or unavailable inputs.

---

### Task 7: Implement TripBreakerCommand and Application-owned switching mutation

**Files:**
- Create: canonical `TripBreakerCommand` module in the existing Application command ownership area.
- Modify: existing switching application service/command dispatcher and Core breaker mutation path.

**Interfaces:**
- Consumes: `ProtectionDecision`.
- Produces: `TripBreakerCommand` with command identity, breaker identity, originating protection/relay identity, decision identity, reason, and timestamp; Application executes it through existing switching mutation architecture.

- [ ] Step 1: Define TripBreakerCommand as an intent/command value object that cannot mutate Core during construction.
- [ ] Step 2: Validate breaker identity against authoritative Core/application switching rules at execution time.
- [ ] Step 3: Route command execution through the existing Application switching service/mutation facade.
- [ ] Step 4: Ensure Core breaker state and Network/Topology updates happen only inside the established mutation boundary.
- [ ] Step 5: Remove/replace only direct protection-to-breaker mutation paths that violate the boundary; preserve valid existing command paths.
- [ ] Step 6: Return structured success/failure diagnostics rather than silently ignoring invalid breaker identity or state.

---

### Task 8: Integrate control action through the existing control architecture

**Files:**
- Inspect/modify existing control signal, control logic, control decision, and equipment-action modules.
- Modify: existing Application command integration only where needed to use the established switching/mutation path.

**Interfaces:**
- Consumes: control signal/input.
- Produces: control decision/equipment action routed through Application/Core mutation.

- [ ] Step 1: Identify the existing control architecture and confirm its authoritative command path.
- [ ] Step 2: Route breaker/control actions through that architecture without creating a second command system.
- [ ] Step 3: Ensure control logic evaluates detached inputs and does not directly mutate Core.
- [ ] Step 4: Ensure equipment action reaches Core through Application and updates Network/Topology consistently.

---

### Task 9: Complete validation ownership and error/diagnostic contracts

**Files:**
- Modify: existing model/network/topology/study validation modules identified in Task 1.

**Interfaces:**
- Consumes: engineering model, topology, study configuration, binding/instrument definitions, and command inputs.
- Produces: existing validation/diagnostic contract used by Application and analysis/protection preparation.

- [ ] Step 1: Put each rule in its authoritative layer: model invariants in Core model validation, connection/topology rules in Network/Topology, study-input rules in study preparation, mutation authorization in Application.
- [ ] Step 2: Add explicit validation for ambiguous terminals, missing measurement ratios, missing bases, unsupported source semantics, and unresolved binding identities.
- [ ] Step 3: Ensure UI-facing validation remains convenience-only and cannot bypass Core/Application validation.

---

### Task 10: Complete canonical `.gridforge` persistence round trip

**Files:**
- Inspect/modify: existing persistence package, manifest/project serializers/deserializers, model restoration code, SLD layout persistence.

**Interfaces:**
- Consumes: Project/Core semantic state and SLD presentation state.
- Produces: canonical `.gridforge` package with `manifest.json` and `project.json`; loader reconstructs semantic-equivalent Network/Core state.

- [ ] Step 1: Ensure project identity, stable equipment IDs, names, terminals, connections, topology-relevant state, operating states, and study data are serialized.
- [ ] Step 2: Serialize SLD layout separately from engineering truth.
- [ ] Step 3: Restore all semantic identities and topology relationships from IDs, never collection position.
- [ ] Step 4: Validate semantic equivalence after load rather than treating successful JSON parsing as proof.
- [ ] Step 5: Preserve compatibility fields only where they do not become a second authoritative contract.

---

### Task 11: Complete SLD symbol/projection coverage and controlled creation path

**Files:**
- Modify: existing SLD projection, palette/tool, symbol/item, and layout modules.

**Interfaces:**
- Consumes: Core read model/projection data and user placement intent.
- Produces: SLD items referencing stable equipment IDs; creation commits through Application command to Core then refreshes projection.

- [ ] Step 1: Audit support for Bus, Line, Cable, Transformer, Generator/Grid, Load, Breaker, Switch, and Disconnector.
- [ ] Step 2: Classify each as symbol, connection, annotation, or non-visual projection without inventing electrical entities for purely visual objects.
- [ ] Step 3: Ensure palette placement preview is non-authoritative and creates no Core equipment before commit.
- [ ] Step 4: Route committed creation through the existing Application command path and then create/update the SLD projection.
- [ ] Step 5: Preserve stable equipment IDs in every SLD item and leave existing BusItem/LineItem behavior unchanged unless a direct regression requires correction.

---

### Task 12: Consolidate ModelService without introducing a mega-manager

**Files:**
- Inspect/modify: `core/application/services/model_service.py` and its callers.
- Create: narrowly scoped service modules only where an existing responsibility is already distinct and extraction removes duplication.

**Interfaces:**
- Consumes: existing Application command/service requests.
- Produces: one coherent authoritative mutation service architecture.

- [ ] Step 1: Map every ModelService responsibility and caller before changing it.
- [ ] Step 2: Remove duplicate/parallel mutation services only when the existing authoritative path is clear.
- [ ] Step 3: If decomposition is justified, split by stable responsibility such as bus, branch, transformer, source, load, switching, or measurement without creating generic managers.
- [ ] Step 4: Update callers to one authoritative path and remove dead duplicate entry points.
- [ ] Step 5: Preserve existing closed-finding behavior.

---

### Task 13: Enforce dependency/import boundaries

**Files:**
- Modify: only files implicated by actual boundary violations discovered during Tasks 1–12.

**Interfaces:**
- Consumes: all corrected module graph relationships.
- Produces: Core-independent-of-UI dependency graph; solver-independent-of-live-Network/Application/UI graph; protection-independent-of-direct-Core mutation.

- [ ] Step 1: Search for Qt/PySide6/canvas/renderer/plugin imports inside Core modules and remove only violations introduced or exposed by the remediation.
- [ ] Step 2: Search solver modules for live Network/Application/UI dependencies and replace with prepared/snapshot contracts where required.
- [ ] Step 3: Search protection modules for direct breaker/network mutation and route only those violations through Application commands.
- [ ] Step 4: Search YBusBuilder callers to verify engineering-to-PU conversion is not duplicated in the builder.

---

### Task 14: Integration verification and finding status update

**Files:**
- Modify: remediation/status documentation only after executable verification is authorized and actually performed.

**Interfaces:**
- Consumes: implemented contracts and repository state.
- Produces: evidence-backed finding status.

- [ ] Step 1: Review changed files against the approved Design Section 2 contract matrix.
- [ ] Step 2: Do not mark any finding CLOSED without executable verification.
- [ ] Step 3: Until user authorizes tests/verification, record corrected findings as `REMEDIATED — VERIFICATION DEFERRED` where appropriate.
- [ ] Step 4: Once authorized, run the project’s actual Python/test/startup checks and record Python version, environment, commands, pass/fail/error/skipped results without fabrication.
- [ ] Step 5: Reconfirm current HEAD and produce the final A–G remediation report required by the governing instructions.
