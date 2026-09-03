# Power Flow Preparation Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the canonical reusable study-configuration and preparation boundary so current Core/Network state is converted into immutable numerical power-flow contracts before numerical execution.

**Architecture:** `PowerFlowStudyConfiguration` owns study-specific choices, including explicit bus operating classification/slack selection, and is reusable across cases. `PowerFlowPreparation` reads an authoritative `Network`, applies the configuration without mutating the Network, prepares `PowerFlowInput` and YBus in a consistent bus order, and returns those numerical contracts to `PowerFlowAnalysis`. Contingency cases will later reuse the same configuration while preparing each isolated Network copy independently.

**Tech Stack:** Python, existing GridForge Core model/network APIs, existing YBus builder, immutable dataclasses, NumPy-backed numerical contracts.

**Spec:** Frozen GridForge V2 power-flow architecture and the approved decision that study-specific bus classification belongs in `PowerFlowStudyConfiguration` (option B).

## Global Constraints

- Network remains authoritative for electrical membership, terminal connections, and topology.
- PowerFlowInput remains authoritative for PQ/PV/SLACK numerical classification during a solve.
- PowerFlowAnalysis remains numerical execution coordination and must not rebuild Core state.
- NewtonRaphsonSolver remains numerical-only.
- The same PowerFlowStudyConfiguration is reusable across contingency cases.
- Each contingency case prepares an isolated Network copy.
- Current ContingencyAnalysis scope remains LINE + TRANSFORMER.
- Do not expand legacy generator/bus contingency support.
- Do not silently change legacy contingency defaults.
- No tests are added or run in this migration checkpoint.
- Do not perform unrelated legacy rewrites.

---

## File Map

- `core/solver/power_flow/study_configuration.py` — immutable study-level configuration, including explicit bus classification/slack selection and study defaults; no live Network references.
- `core/solver/power_flow/preparation.py` — conversion boundary from authoritative Network + configuration to `PowerFlowInput` + prepared YBus.
- `core/solver/power_flow/__init__.py` — expose the canonical preparation/configuration contracts if existing package conventions require it.
- `core/analysis/contingency.py` — later migration target; replace stale direct `PowerFlowAnalysis(copied_network)` usage with preparation using the reusable configuration.
- `docs/superpowers/plans/2026-09-03-power-flow-preparation-boundary.md` — this implementation plan.

## Tasks

### Task 1 — Lock existing Network/YBus conventions

- [ ] Re-read the current Network bus/index/topology APIs and YBus builder contract.
- [ ] Confirm how generators and loads are associated with buses through authoritative Network/terminal state.
- [ ] Confirm existing solver option/default conventions without changing them.
- [ ] Record only confirmed APIs in implementation notes; do not invent adapters for missing behavior.

### Task 2 — Implement PowerFlowStudyConfiguration

- [ ] Define a frozen configuration object with no live Core references.
- [ ] Represent explicit bus operating classifications and exactly one configured slack bus.
- [ ] Preserve the distinction between study configuration and numerical `PowerFlowInput`.
- [ ] Validate identifiers, classification values, and configuration consistency at construction.
- [ ] Keep configuration reusable so contingency cases can share one instance.

### Task 3 — Implement PowerFlowPreparation

- [ ] Accept an authoritative `Network` and a `PowerFlowStudyConfiguration`.
- [ ] Read buses/equipment from the Network without mutating authoritative state.
- [ ] Derive numerical P/Q specifications from the existing model injection conventions.
- [ ] Derive initial voltage magnitude/angle from authoritative Bus state.
- [ ] Build the bus-ordered YBus through the existing authoritative Network/index/YBus path.
- [ ] Construct immutable `PowerFlowInput` using the configured PQ/PV/SLACK classification.
- [ ] Verify YBus ordering and dimensions against the resulting PowerFlowInput.
- [ ] Return a preparation result containing the numerical input and prepared YBus.

### Task 4 — Integrate package exports

- [ ] Inspect current power-flow package exports.
- [ ] Export the new canonical contracts only where consistent with package conventions.
- [ ] Avoid compatibility aliases that preserve the obsolete live-Network PowerFlowAnalysis boundary.

### Task 5 — Migrate ContingencyAnalysis

- [ ] Preserve the existing public `ContingencyAnalysis` contract and LINE/TRANSFORMER scope.
- [ ] Preserve isolated deep-copy case Networks and never mutate the authoritative Network.
- [ ] Reuse one `PowerFlowStudyConfiguration` for all cases.
- [ ] Prepare each isolated case Network independently.
- [ ] Invoke `PowerFlowAnalysis` only with prepared `PowerFlowInput` + YBus.
- [ ] Preserve existing contingency result and violation semantics unless required by the new boundary.

### Task 6 — Verification and checkpoint

- [ ] Fetch all changed files from GitHub after each write and inspect their committed contents.
- [ ] Check imports, signatures, ownership boundaries, and stale `PowerFlowAnalysis(copied_network)` call sites.
- [ ] Do not run tests, per the current migration constraint.
- [ ] Commit the preparation boundary and contingency integration only after inspection confirms the intended architecture.
- [ ] Do not declare the broader migration frozen; this checkpoint establishes the missing canonical preparation boundary.
