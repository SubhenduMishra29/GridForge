# GridForge V2 — Current Architecture and Implementation Boundary

**Baseline:** 2 November 2026  
**Repository:** `SubhenduMishra29/GridForge`  
**Branch:** `main`  
**Baseline commit:** `a9e07287c90667a7aae8bcc060e4e2d0cadf261e`  
**Authority:** This document consolidates the frozen V2 architecture. It supersedes conflicting or older status descriptions, but does not silently change domain contracts or declare unfinished work complete.

## 1. Architecture decision

GridForge maintains one authoritative engineering digital twin with a controlled Application boundary and multiple UI/workflow projections.

- **Core:** authoritative electrical/domain state, physical equipment, terminals, network relationships, topology, engineering validation, protection/control domain semantics, study-domain contracts and immutable results.
- **Application:** controlled mutation, commands, transactions, history, lifecycle, orchestration, persistence coordination, events and read models.
- **UI:** interaction, editors, SLD authoring/projection, canvas geometry, selection, inspectors and result presentation.
- **Plugins:** contract-bound extensions that reuse Core/Application/UI owners without creating parallel authorities.

The universal path remains:

```text
UI / SLD
  → Controller / Tool
  → Immutable Command
  → Application Command / Service
  → Transaction
  → Core
  → Semantic Event / Immutable Result
  → Application Read Model
  → UI Projection
```

Queries follow the corresponding Application read-service path and do not expose mutable Core state.

## 2. Core domain boundaries

### 2.1 Physical model

Physical equipment owns its device-specific parameters, configuration and operational state. Equipment terminals are physical connection points owned by their equipment. Equipment does not own global topology.

### 2.2 Network relationships and topology

The network owns canonical electrical relationships between equipment terminals. Topology is derived from those relationships and the applicable equipment/switching state. A bus is an authoritative electrical object, not a graphical line. A terminal is not itself a recursively connected topology object.

### 2.3 Two connection representations that must not be conflated

**Simple Wire connectivity** is the canonical, persistent terminal-to-terminal relationship used by the conventional network model and SLD workflow. It has an independent relationship identity and explicit endpoints.

**Phase-domain conductor graph** is a separate, explicit physical/study representation used where phase-specific conductors, neutral/earth return paths, conductor impedance and fault-current paths must be represented. It is not a pixel graph, not a route polyline, and not a replacement for the conventional Simple Wire schema.

The graph must retain explicit node/edge identity, phase/conductor role, endpoint references and physical/electrical parameters required by the supported solver. Earth return requires a physical, source-referenced path to the declared earth reference; a neutral/earth metadata flag is not a path. Unsupported or incomplete paths must remain unavailable/fail-closed.

## 3. Application responsibilities

Application is the single authority for:

- immutable command dispatch and handler resolution;
- transaction creation, commit, rollback and supported undo/redo;
- project lifecycle, activation generation and compensation;
- study execution, cancellation, status and result publication;
- controlled changes to network/connectivity and phase-domain graph data;
- persistence coordination, migrations and project-scoped service activation;
- semantic event delivery and read-model assembly.

No subsystem or plugin may create a competing command manager, transaction manager, study scheduler, event bus, project lifecycle authority or general study-result store.

## 4. SLD and UI architecture

The SLD is a first-class engineering authoring surface and a projection of Core/Application state. It is not the electrical model.

- Symbols/items represent equipment; they are not equipment objects.
- Placement previews and draft connections remain authoring state until an explicit Application commit.
- A committed connection requires canonical endpoint identity and an Application-controlled relationship mutation.
- Screen proximity, visual crossing, snapping or route geometry cannot independently establish connectivity.
- SLD geometry/layout and document metadata are presentation state, separately persisted and versioned.
- Runtime QGraphics objects are disposable realizations of immutable/persisted presentation state.
- Undo/redo and reload reconstruct the projection from canonical state rather than treating graphics as authority.

The UI workspace composition uses Window → Workspace → Areas → Editors → Regions → EditorContext → discipline tools. Qt access remains centralized through `ui/core/qt.py`. Core must not import Qt, QGraphics, SLD, plugin or UI types.

**Phase-domain authoring gap:** PR #908 provides programmatic Application editing and persistence for the phase-domain graph. That does not prove a complete SLD/editor workflow for authoring, inspecting, validating and editing those physical conductor nodes/edges. The UI authoring/projection work remains a separate requirement.

## 5. Protection architecture

Protection is separate from Control and is modelled as physical relay devices hosting one or more independent protection-function elements.

Measurement path:

```text
Primary network quantity
 → instrument primary terminals (CT / PT / CVT)
 → physical secondary circuit and secondary terminals
 → MeasurementChannel
 → RelayInput
 → ProtectionElement / RelayBase
```

Decision/action path:

```text
ProtectionDecision
 → explicit protection scheme / output-to-action mapping
 → Application authorization and command
 → breaker/switching service
 → authoritative physical equipment state
 → feedback / postcondition
```

The ProtectionDecision records function evaluation; it does not itself mutate a breaker. Primary instrument association, secondary terminal wiring, measurement channel, quality/freshness, ratio/polarity and source provenance are explicit. Protection cannot infer CT coverage, neutral current, trip targets or physical protection zones from SLD graphics.

A Protection Study is an Application-owned workflow over a project/network snapshot. It coordinates supported fault scenarios, measurement snapshots, function evaluation, coordination evidence, diagnostics, immutable result provenance and UI read models. It reuses canonical study/application infrastructure.

## 6. Numerical studies and derived representations

Study-specific numerical models are built from authoritative equipment/network state and explicit study configuration. They are disposable derived inputs; they do not become a second engineering model.

- Sequence-domain and phase-domain short-circuit representations have explicit applicability and coverage boundaries.
- Transformer preparation must preserve winding identity, terminal domain, connection, tap and impedance-base semantics.
- Phase-domain conductor models require explicit physical conductor paths and supported impedance data.
- Source equivalents must be derived only from supported, explicitly configured equipment models.
- Internal winding/loop currents are not interchangeable with external terminal currents or CT-aperture currents.
- A numerical output is not automatically a valid measurement-channel input; the physical source/path and measurement contract must support it.
- Dynamics and transient models remain separate from persistent static network truth.

Missing data, unsupported equipment, ambiguous topology, invalid bases or incomplete physical return paths are explicit diagnostics/unsupported states. No nameplate-only, visual, metadata-only or generic fallback may fabricate engineering truth.

## 7. Persistence

The canonical project package is `.gridforge` with package metadata in `manifest.json` and canonical project state in `project.json`. Project, network/connectivity, SLD presentation, measurement, protection/control and dynamic sections retain explicit schema/version contracts.

Load order restores and validates equipment and terminals before canonical relationships and derived topology. Project activation is an Application lifecycle operation with project identity and activation-generation provenance. Runtime UI widgets and graphics objects are not persisted as engineering truth.

Study-result history/archive is separate from the canonical project package. Historical records must retain project/study/source-revision and activation provenance and must never be projected as current live network state.

## 8. Plugin boundary

Plugins may contribute domain algorithms, equipment capabilities, study handlers, integrations, editors, tools, panels, renderers and reports. They must:

- call Core/Application through public contracts;
- route user-originated mutations through Application commands/services;
- reuse canonical transactions, StudyService, ApplicationEventBus and result publication;
- preserve project/generation/study/source-revision identity;
- keep UI plugin lifecycle separate from headless study/domain lifecycle;
- advertise CPU/GPU/NPU only for actual implemented computations.

A plugin is an extension of the platform, not an alternate platform.

## 9. Merged implementation boundary at this baseline

PR #908 merged the following foundations:

- detached, Application-authorized CT terminal-current samples for explicitly supported Line/Cable and transformer sequence cases;
- tap-aware transformer sequence preparation and typed terminal-current records;
- CT association/conversion validation against configured equipment endpoint, CT identity, polarity, ratio, terminal-current basis, topology and project provenance;
- explicit residual-source bindings and derived residual-current measurement for ANSI 50N/51N in supported cases;
- transformer winding/neutral declarations and supported zero-sequence transformer cases;
- physical conductor inventories, topology associations, impedance preparation and phase-domain conductor graph/global-admittance/fault-execution foundations;
- reversible Application commands and transaction handling for phase-domain graph node/connection edits;
- connectivity persistence schema and migration for phase-domain graph collections.

PR #909 separately corrected the visual state of uncommitted draft wires; it did not change electrical connectivity.

### Explicitly not established by this merge

- automatic phase-domain source equivalents for every Grid, Generator, Motor or other source family;
- complete phase-domain machine, load, arc-fault and all switching-equipment variants;
- universal physical neutral CT/CBCT coverage;
- a complete SLD authoring/projection workflow for phase-domain graph objects;
- full end-to-end Protection Study, relay execution, breaker trip, persistence round-trip or commissioning verification.

Open/draft PRs are not mainline. At the stated baseline, PRs #912–#918 remain separate workstreams and must be reconciled independently before their implementation is documented as merged.

## 10. Phase-domain physical equipment coverage — D15F-29–37

The merged-main Modification Register records the following implementation increments. These are explicit supported construction paths, not universal equipment coverage:

- **D15F-29:** Switch, Disconnector and Fuse phase/neutral pole inventories are explicit; their internal paths are gated by authoritative closed/in-service or not-blown operating state. Per-pole discrepancies, fuse arc/melting behaviour, contact resistance and earthing blades are not covered.
- **D15F-30:** Breaker, Switch, Disconnector and Fuse use the common immutable `PhysicalConductorConstruction` / `PhysicalConductorPath` contract. Construction and operating state remain separate authorities.
- **D15F-31:** Transformer winding construction explicitly declares HV/LV connection, terminal roles, phases, neutral/grounding and vector/core metadata. It does not itself create magnetic or galvanic coupling.
- **D15F-32:** The phase-domain solver accepts a reciprocal, passive terminal-domain Transformer multiport and reports signed terminal currents.
- **D15F-33:** `prepare_transformer_phase_domain_multiport()` produces a multiport from a Transformer only when a complete externally supplied admittance matrix, tap/phase-shift provenance and exact winding terminal graph inventory are available.
- **D15F-34:** The SLD-derived graph builder creates explicit Transformer HV/LV phase and declared neutral terminal nodes, attaches them to canonical Bus slots, and automatically supplies the Transformer multiport to short-circuit preparation. HV/LV windings are not joined galvanically.
- **D15F-35:** Grounded-wye neutral paths require distinct explicit neutral-grounding and earth-return impedances, local earth nodes and a global earth reference. Solver reconciliation checks the transformer neutral multiport current against the physical electrode branch current.
- **D15F-36:** Core zero-sequence and delta-circulation coverage claims are bound to the exact ordered terminal-admittance matrix fingerprint, core construction and required manufacturer/test references.
- **D15F-37:** Explicit internal delta-loop states are stamped as coupled MNA current unknowns and solved with network voltages, faults and transformer terminal currents. Results expose per-loop circulating currents; coupling and impedance require manufacturer/test-derived data.

The resulting Transformer multiport remains a derived study representation, not a second persistent Transformer model. The matrix is supplied explicitly; scalar nameplate data or vector-group labels are not used to fabricate missing magnetic coupling. D15F-37 exposes reduced internal loop-current coordinates, not individual physical SLD conductor geometry, thermal behaviour or core limb flux/current states.

D15F-29 records persistence/schema migration and UI configurator integration as outstanding for switching-device construction; D15F-30 records full persistence/configurator support for the common contract as outstanding; Transformer matrix/provenance persistence and Application configurator support were also recorded as outstanding in D15F-33/34. These must not be silently upgraded to complete project round-trip or user-facing configuration without separate evidence.

## 11. Verification and claims policy

The #908 merge record states remote source inspection and integration review only. It explicitly records that tests/CI, Python syntax/import checks, persistence round-trip, numerical fixtures and end-to-end runtime execution were not run.

Therefore documentation must distinguish:

1. **Implemented in source / merged** — code is on the named baseline.
2. **Statically inspected** — source/patch/architecture evidence was reviewed.
3. **Runtime verified** — the actual execution path was exercised.
4. **Numerically validated** — engineering results were compared against appropriate references/fixtures.
5. **Commissioned / production enabled** — required external adapters, operational controls and deployment evidence exist.

These labels are not interchangeable. A class, protocol, schema, unit fixture or isolated helper does not prove an end-to-end engineering workflow.

## 12. Frozen invariants

1. One authoritative Core engineering model.
2. Core remains headless.
3. Application owns controlled mutation and workflow.
4. SLD is authoring/projection, not electrical truth.
5. Graphics and geometry never establish topology.
6. Simple Wire and phase-domain conductor graph remain distinct.
7. Numerical representations are derived study inputs.
8. Protection decisions are separate from physical switching state.
9. Measurement inputs require explicit physical source and channel contracts.
10. Unsupported electrical semantics fail closed.
11. Plugins reuse shared owners and public contracts.
12. Persistence stores semantic project state, not runtime UI objects.
13. Project and study results preserve revision and activation provenance.
14. Runtime/engineering verification is reported separately from static source inspection.

## 13. Change control

Use the repository workflow:

```text
FETCH → AUDIT → RECONCILE → CORRECT → CHECK → FREEZE
```

Architecture changes require an explicit gap and evidence. Do not reopen frozen boundaries merely to accommodate a local implementation convenience. Do not add tests/CI as acceptance gates unless requested; record the exact checks actually performed.
