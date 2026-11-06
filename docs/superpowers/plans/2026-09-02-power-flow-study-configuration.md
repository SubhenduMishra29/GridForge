# Power Flow Study Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce an immutable `PowerFlowStudyConfiguration` that owns explicit study-side PQ/PV/SLACK intent and is shared by normal and contingency Power Flow preparation.

**Architecture:** The configuration is a study definition, not Core equipment or Network state. `PowerFlowPreparation` consumes a Network plus configuration and produces `PreparedPowerFlow`; `ContingencyAnalysis` reuses the same configuration for each isolated case and never infers or replaces classifications.

**Tech Stack:** Python, frozen/slots dataclasses, existing GridForge Core analysis and solver contracts.

**Spec:** Approved architecture in conversation; related preparation/contingency design at `docs/superpowers/specs/2026-09-02-power-flow-contingency-preparation-design.md`.

## Global Constraints

- Do not add tests for now.
- Do not add PQ/PV/SLACK classification to `Bus`, equipment, `Network`, `BusState`, or solver-owned configuration.
- Do not infer or silently replace a missing/invalid Slack.
- Contingency cases must use isolated Network state and the same study configuration.
- Solver must continue receiving prepared numerical contracts, not live Core objects.
- Preserve the frozen GridForge V2 dependency direction.

---

### Task 1: Add the study configuration contract

**Files:**
- Create: `core/analysis/power_flow_configuration.py`
- Modify: `core/analysis/__init__.py`

**Interfaces:**
- Produces `PowerFlowStudyConfiguration`.
- Configuration exposes immutable `bus_types` keyed by bus ID using existing `PowerFlowBusType`.
- Constructor validates non-empty configuration, supported classifications, unique IDs, and exactly one configured Slack.

- [ ] Define a frozen/slots configuration type using the existing `PowerFlowBusType` rather than creating a second classification enum.
- [ ] Normalize accepted classification values consistently with existing `PowerFlowInput` behavior.
- [ ] Store a defensive immutable mapping.
- [ ] Export the configuration from `core.analysis`.
- [ ] Re-fetch the files and inspect the resulting API.

### Task 2: Move Power Flow preparation to the configuration boundary

**Files:**
- Modify: `core/analysis/power_flow_preparation.py`

**Interfaces:**
- `PowerFlowPreparation.prepare(network, power_flow_configuration)` produces `PreparedPowerFlow`.
- Preparation reads explicit `bus_types` from the configuration and transfers them into `PowerFlowInput`.

- [ ] Replace the current raw `bus_types` preparation input with `PowerFlowStudyConfiguration`.
- [ ] Preserve exact case-network bus IDs as the validation domain.
- [ ] Reject missing, extra, or invalid configured bus IDs explicitly.
- [ ] Reject a case where the configured Slack/PV/PQ assignment cannot be applied; never auto-select another Slack.
- [ ] Preserve existing Network-derived P/Q, voltage, and YBus preparation semantics unless correlation reveals a concrete incompatibility.
- [ ] Re-fetch and inspect the complete modified file.

### Task 3: Correlate and update contingency orchestration

**Files:**
- Modify: `core/analysis/contingency.py`

**Interfaces:**
- `ContingencyAnalysis(network, power_flow_configuration)`.
- Each isolated contingency case calls `PowerFlowPreparation.prepare(case_network, power_flow_configuration)` and passes the returned prepared data to `PowerFlowAnalysis`.

- [ ] Replace the stale `PowerFlowAnalysis(case_network, ...)` call.
- [ ] Inject the approved configuration at construction time.
- [ ] Reuse the exact same configuration object for every contingency case.
- [ ] Preserve isolated case Network behavior.
- [ ] Ensure contingency logic remains scenario generation/orchestration and does not own classification.
- [ ] Re-fetch and inspect the modified file.

### Task 4: Update analysis exports/documentation and correlate callers

**Files:**
- Modify: `core/analysis/__init__.py` if required.
- Inspect: current repository callers/imports of `ContingencyAnalysis`, `PowerFlowPreparation`, and Power Flow configuration.

- [ ] Search for constructor call sites and imports.
- [ ] Update only callers that are demonstrably incompatible with the new API.
- [ ] Do not invent defaults for missing study configuration.
- [ ] Update focused architecture documentation if the current wording still describes raw `bus_types` or Network-owned classification.

### Task 5: Final verification and freeze decision

**Files:**
- No additional files unless verification finds a concrete inconsistency.

- [ ] FETCH every changed file from the repository after all writes.
- [ ] CHECK signatures, imports, immutability, classification ownership, contingency reuse, and absence of silent Slack reassignment.
- [ ] Confirm no tests were added or required.
- [ ] Review the final diff/commit state.
- [ ] Freeze only after the repository state matches this plan.
