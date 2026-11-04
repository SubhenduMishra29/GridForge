# GridForge V3 — Architecture Research and Change Register

**Opened:** 2026-11-03  
**Authority:** `SubhenduMishra29/GridForge`  
**Baseline:** `main` at `44e9b58eaf3b8a13cbf064b1f81e2b028539cc3c`  
**Status:** Research register; proposed V3 work only.

## 1. Governance

V2 remains the active implementation baseline. This register captures candidate V3 improvements; it does not authorise V2 redesign, mass file moves, API removals or immediate V3 implementation.

Workflow: **FETCH → AUDIT → RESEARCH → RECONCILE → SPECIFY → REVIEW → APPROVE → IMPLEMENT → VERIFY → FREEZE.**

No standards-conformance claim may be made from a title or abstract. Every eventual claim must identify applicable edition, jurisdiction, clauses, implementation evidence, limitations and verification method. Distinguish normative standards, technical reports, guidance, notified regulations and draft proposals.

## 2. Initial standards and regulatory research

| Domain | Primary references to investigate | V3 research question |
|---|---|---|
| Power-system automation | IEC 61850 series, SCL, logical nodes | Model IEDs, logical nodes, data objects, reports, GOOSE, Sampled Values, time quality and engineering exchange. |
| Protection | IEC 60255 series | Model relay functions, instrument interfaces, digital process interfaces, performance evidence, trip paths and feedback. |
| Short-circuit studies | IEC 60909 series | Specify methods, correction factors, source models, assumptions, result metadata and reference cases. |
| Power-system information | IEC 61970 / IEC 61968 CIM | Define canonical object mapping, profiles and import/export boundaries. |
| Equipment identity | IEC 81346 series | Define reference designation, function/product/location aspects and cross-document identity. |
| Diagram symbols | IEC 60617 and applicable national adoptions | Separate symbol identity and geometry from semantic equipment and terminals. |
| PLC/control | IEC 61131-3 | Specify ST, LD, FBD, SFC, task/scan execution, data types and interchange. |
| Alarm management | ISA-18.2 / IEC 62682 | Specify alarm lifecycle, priorities, shelving, suppression, rationalisation and audit. |
| HMI/usability | ISA-101; ISO 9241-210 | Define display hierarchy, human-centred design, navigation and measurable usability. |
| Cybersecurity | IEC 62443 and applicable CEA requirements | Define trust zones, identity, authorisation, plugin trust, secure updates and audit. |
| Functional safety | IEC 61508 and applicable sector standards | Determine applicability and keep safety-related functions distinct from ordinary simulation/control. |
| India compliance | CEA regulations, BIS adoptions, applicable grid codes | Identify notified requirements, amendments, jurisdiction, asset class and applicable edition. |

### Edition observations from the first source pass

- IEC 61131-3:2025 defines the syntax and semantics of ST, LD, FBD and SFC.
- IEC 60255-1:2022 addresses common requirements for measuring relays/protection equipment, including distributed schemes.
- IEC TS 60255-216-1:2025 addresses protection functions using digital communications, including Sampled Values, GOOSE and time synchronisation.
- IEC 60909-0:2026 is a current reference for three-phase AC short-circuit calculations.
- IEC 81346-1:2022 establishes system structuring and reference-designation principles.
- CEA construction standards include 2025 amendments; CEA also lists 2026 draft/regulatory material. Drafts must not be represented as notified requirements.

These are research leads, not detailed requirements or claims of GridForge compliance. Full companion-part, amendment, Indian adoption and clause applicability research remains open.

## 3. Initial architecture findings to investigate

1. Multiple plugin contract families appear to exist (Core plugin SDK, dynamics base, transformer base and domain-specific plugins). Research one consolidated plugin platform, typed capability contracts and a single discovery/registration authority, while retaining capability-specific lifecycle behaviour.
2. Core equipment models overlap with plugin capability models for equipment such as transformers and motors. Define canonical physical equipment identity/configuration separately from optional physics, solver and integration capabilities.
3. The SDK currently resides under `core/plugin_sdk`. Evaluate a neutral platform location; Core must not depend on plugin implementations.
4. Application code is physically under `core/application`. Audit actual import direction and logical ownership before considering a move; filesystem location alone does not prove a violation.
5. Core documentation and package initializers may not agree. Audit namespace-package intent, public exports and import stability before changing package structure.
6. Distinguish `core/numerical` from `core/numerics` by source responsibilities and consumers before considering consolidation.
7. Build a complete Core/Application/plugin/UI import graph and identify cycles, forbidden inward dependencies, duplicate authorities and overly broad package facades.
8. Consolidate plugin platform code under one top-level plugin area with manifests, versioned contracts, capabilities, compatibility declarations, configuration schemas, dependency resolution, lifecycle and diagnostics.

No class deletion, file move, API break or plugin rewrite is approved by these preliminary observations.

## 4. Engineering-model research

V3 must establish canonical semantics and ownership for:

- Equipment identity, nameplate/manufacturer data, engineering settings, operating state and study assumptions.
- Electrical topology versus graphical wiring, conductor routing and diagram layout.
- Terminal identity, connectivity, junctions, multi-terminal buses and physical conductor representation.
- Measurement values, units, scaling, timestamps, quality, freshness, calibration, source identity and provenance.
- Channel lifecycle as distinct states: configured, allocated, connected, communication-healthy, valid, stale, inhibited or faulted. Availability must not collapse to one Boolean.
- Protection measurement, function evaluation, decision, trip command, output activation, actuation and breaker/device feedback as distinct traceable stages.
- Control task/scan execution, function-block state, interlocks, permissives, latching, timers, communication loss and deterministic simulation time.
- Immutable study inputs, preparation snapshots, numerical method, convergence/quality evidence, assumptions, standard edition and reproducible results.
- Physical versus simulated sources/devices and provenance for every value and action.

## 5. Usability research

Investigate one project/domain model with role-oriented workspaces rather than disconnected subsystem databases:

- Electrical design / SLD.
- Protection engineering.
- Control engineering / Control Canvas.
- Instrumentation, I/O and channel management.
- Studies and simulation.
- Commissioning/diagnostics and operations views where in scope.

Evaluate contextual inspection, progressive disclosure, guided equipment configuration, templates with explicit assumptions, signal/channel tracing, cross-reference navigation, actionable validation, engineering diagnostics, search/filter/hierarchy and standards-aware reports. Measure usability using representative engineering tasks, completion time, error rate and recovery—not visual preference alone. Distinguish engineering configuration interfaces from operator HMI requirements.

## 6. Proposed V3 work packages

| ID | Priority | Research package | Deliverable |
|---|---|---|---|
| V3-ARCH-001 | P0 | Repository package/import/dependency audit | Verified dependency graph, ownership map, cycle and forbidden-dependency register |
| V3-ARCH-002 | P0 | Canonical domain ownership | Equipment, terminal, topology, measurement, Control, Protection, Study and Project ownership matrix |
| V3-PLUG-001 | P0 | Consolidated plugin platform | SDK/capability/manifest/discovery/registry/lifecycle design and migration map |
| V3-STD-001 | P0 | Standards and regulatory applicability | Edition/status/jurisdiction/asset/workflow/clause/evidence matrix |
| V3-SIG-001 | P0 | Measurement and channel semantics | Typed signal, channel lifecycle, quality, freshness, provenance and routing contract |
| V3-PROT-001 | P0 | Protection lifecycle and digital interfaces | Relay, merging-unit, SV/GOOSE, trip/output/feedback and evidence model |
| V3-CTRL-001 | P0 | Standards-aligned Control execution | PLC task/scan semantics, typed signals, function blocks and interchange requirements |
| V3-ID-001 | P1 | Equipment identity/reference designation | Cross-domain identity and IEC 81346 mapping |
| V3-NET-001 | P1 | Network and diagram semantic separation | Topology, terminals, conductor paths, junction and SLD projection model |
| V3-STUDY-001 | P1 | Study reproducibility/numerical assurance | Immutable inputs, assumptions, standard editions, solver provenance and quality |
| V3-SIM-001 | P1 | Heterogeneous simulation | Deterministic time, CPU reference, GPU capability, supported NPU inference boundary |
| V3-DATA-001 | P1 | Persistence and interchange | Versioned schema, migration, audit/history, CIM/SCL exchange strategy |
| V3-UX-001 | P1 | Human-centred engineering workspaces | Task-based UX requirements, diagnostics and usability measures |
| V3-SEC-001 | P1 | Cybersecurity/trust boundaries | Threat model, zones/conduits, permissions, plugin trust and audit |
| V3-ALARM-001 | P2 | Alarm/event/SOE lifecycle | Alarm rationalisation, priority, event chronology and historian linkage |
| V3-SAFE-001 | P2 | Functional-safety applicability | Scope decision, hazard boundary and safety lifecycle requirements |

Priorities are provisional and must be reviewed after impact analysis.

## 7. V3 architecture principles to formalise

- One authoritative owner for each engineering fact and state transition.
- No duplicate equipment, topology, measurement, event, scheduler, historian or plugin-registry authorities.
- Core remains independent of Qt, UI, graphics and plugin implementations.
- Plugins extend through public, versioned contracts and Application-controlled mutation; no direct Core mutation.
- Cross-domain signals and commands are typed, attributable, time-qualified and traceable.
- Calculations expose assumptions, standard basis, numerical quality and reproducible inputs/results.
- Control and Protection remain distinct execution/decision authorities with explicit integration contracts.
- Diagram symbols and canvas objects are projections, never domain truth.
- Backward compatibility and project migration are explicit deliverables.
- Standards support is expressed as profiles/capabilities with transparent limitations, not a blanket compliance badge.
- Usability is evaluated against real engineer workflows.
- Every V3 package requires an approved specification and migration plan before implementation.

## 8. Initial primary-source register

- IEC 61131-3:2025 — https://webstore.iec.ch/en/publication/68533
- IEC 60255-1:2022 — https://webstore.iec.ch/en/publication/59762
- IEC TS 60255-216-1:2025 — https://webstore.iec.ch/en/publication/77735
- IEC 60909-0:2026 — https://webstore.iec.ch/en/publication/68454
- IEC 81346-1:2022 — https://webstore.iec.ch/en/publication/64021
- IEC TR 61850-1-1:2026 — https://webstore.iec.ch/en/publication/105222
- IEC TR 61850-90-30:2025 — https://webstore.iec.ch/en/publication/94414
- ISA standards catalogue — https://www.isa.org/standards-and-publications/isa-standards
- ISA-101 — https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards
- ISA/IEC 62443 — https://www.isa.org/standards-and-publications/isa-iec-62443-series-of-standards
- CEA construction standards/amendments — https://www.cea.nic.in/regulations-category/c5e1ec5f-ca2f-4057-8a31-857f91a71701?lang=en
- CEA draft regulations — https://cea.nic.in/regulations/102?lang=en
- CEA updates — https://www.cea.nic.in/whats-new/all-updates?lang=en

The source register must be expanded with companion parts, official Indian adoptions, amendments, grid codes and exact clause-level evidence. Public abstracts are discovery evidence, not substitutes for licensed normative text.

## 8A. Core dependency audit — first evidence batch (2026-11-03)

**Audit scope:** Recursive `main` tree plus direct source inspection of Core package initializers, Network, Measurement, Control, Protection, Analysis, Solver, Numerical, Application and plugin SDK entry points. This is a first dependency sample, not yet an exhaustive proof that no forbidden imports exist elsewhere.

### Verified repository structure

- The recursive tree contains 334 Python files under `core/` across 33 package directories.
- `core/__init__.py` is absent. Most domain packages have package initializers, but `core/measurement` has no `__init__.py`, and `core/validation/__init__.py` is empty.
- Python namespace-package semantics may explain these omissions. The V3 requirement is to document and intentionally choose the package model, not blindly add initializers.
- `core/application/` is a substantial Application layer physically nested under `core/`. In the inspected files, Application imports Core domain contracts; no reverse Core-to-Application import was found in this sample. This supports an outward dependency direction, but does not settle whether the filesystem/package namespace should be separated in V3.
- `core/plugin_sdk/contracts.py` and `host.py` use standard-library contracts and do not import Core domain implementations in the inspected source. The host is an explicit-instance lifecycle host; manifest discovery/catalogue is not present in this host API.
- `core/numerical` and `core/numerics` have distinguishable current responsibilities: `numerical` exposes electrical state/YBus construction, while `numerics` exposes ODE and backend execution abstractions. This is not sufficient evidence to merge them; V3 should define their names and ownership explicitly.

### Confirmed dependency-direction concern

The current source contains a cross-package dependency cycle between Analysis preparation and Solver implementation:

- `core/analysis/short_circuit_preparation.py` imports solver input/snapshot types and `PhaseDomainShortCircuitCase` from `core.solver.short_circuit.phase_domain_solver`.
- `core/solver/short_circuit/phase_domain_solver.py` imports `PhaseDomainAdmittanceSnapshot` and `PhysicalConductorImpedanceSnapshot` from `core.analysis` preparation modules.
- `core/analysis/power_flow_preparation.py` imports `PowerFlowInput` from Solver, while `core/solver/power_flow/preparation.py` imports the Analysis preparation implementation.

This is more than a directory-layout question: the preparation and numerical-execution layers are coupled in both directions. The short-circuit package currently uses lazy package exports to avoid an eager import-time cycle, but that compatibility mechanism does not remove the underlying architectural dependency cycle.

**V3 candidate correction:** define a one-way preparation-to-execution contract. Analysis (or a dedicated study-preparation layer) should construct immutable, solver-neutral/solver-owned numerical input contracts; Solver should consume those contracts and must not import Analysis preparation implementations or Analysis-specific snapshot classes. Where public compatibility facades are needed, isolate them as adapters rather than allowing implementation-level reverse imports. Exact contract placement requires further source and consumer analysis.

### Package-facade and maintainability observations

- `core/analysis/__init__.py` eagerly imports a broad set of Analysis modules, including power flow, short circuit, transient and phase-domain preparation APIs. Broad eager facades increase import coupling and make cycles harder to reason about.
- `core/model/__init__.py`, `core/network/__init__.py` and `core/protection/__init__.py` also expose broad public surfaces. V3 should specify stable public APIs and avoid importing heavy implementation modules merely to access a narrow type.
- `core/solver/short_circuit/__init__.py` uses lazy `__getattr__` resolution for phase-domain exports. This is a deliberate compatibility workaround to preserve exports while avoiding one observed import-time cycle. V3 should prefer clean dependency direction over accumulating lazy-import workarounds.
- The `core/base/__init__.py` self-reference found by the import-line scan is inside its documentation example, not an executable import; it is not a defect.
- The `core/network/__init__.py` occurrence of `from core.network import Network` is likewise inside its usage documentation, not a runtime self-import.

### Initial V3 audit findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F01 | P0 | Analysis preparation and Solver implementation import each other's implementation-level types | Break the bidirectional dependency; formalise immutable preparation/execution contracts |
| V3-ARCH-F02 | P1 | Analysis package facade eagerly imports many preparation and study modules | Define a minimal stable facade; use explicit submodule imports or deliberate lazy exports where justified |
| V3-ARCH-F03 | P1 | Core root and Measurement package initializers are absent; Validation initializer is empty | Decide/document regular-package versus namespace-package policy and public export rules |
| V3-ARCH-F04 | P1 | Application layer is physically nested in `core/application`, although its inspected dependency direction is Application → Core | Decide logical/package ownership based on full import graph and packaging needs; do not move based on path alone |
| V3-ARCH-F05 | P1 | Numerical electrical model/YBus package and numerical runtime/ODE/backend package coexist under similar names | Define separate bounded responsibilities and naming; retain separation unless consumers prove duplication |
| V3-ARCH-F06 | P1 | Plugin SDK host handles explicit instances and lifecycle but does not provide manifest discovery/catalogue | Design the consolidated plugin platform and decide whether discovery belongs in host, loader or platform service |

### Verification limits

- Source-tree and selected-file inspection only; no tests, CI, syntax checks, import experiments or runtime profiling were run.
- The 334-file recursive listing is complete for the returned Git tree (`truncated=false`), but the import review in this section is a selected-source audit, not a complete static import graph.
- No production defect or V2 correction is declared from these V3 research observations.
- Next audit pass must inspect all Core imports and all direct consumers of the preparation/snapshot contracts, then trace plugin/UI boundaries.

## 8B. Core dependency audit — preparation/execution contract trace (2026-11-03)

This pass inspected the complete source bodies of the key Power Flow and Short Circuit preparation/input/solver modules identified in the first audit. The evidence refines the initial cycle finding.

### Power Flow dependency trace

Observed source dependencies:

- `core/analysis/power_flow_preparation.py` builds `PreparedPowerFlow` and imports `PowerFlowInput` / `PowerFlowBusType` from `core.solver.power_flow.input`.
- `core/analysis/power_flow.py` orchestrates preparation and numerical execution, importing `NewtonRaphsonSolver`, `PowerFlowResult` and solver options from Solver.
- `core/solver/power_flow/preparation.py` is a wrapper that imports and delegates to `core.analysis.power_flow_preparation.PowerFlowPreparation`.
- `core/solver/power_flow/input.py` defines a frozen `PowerFlowInput` contract and is solver-owned by package location.

**Interpretation:** the numerical solver can consume a clean input DTO, but preparation implementation currently lives in Analysis while a Solver-namespaced wrapper points back to Analysis. This creates an ambiguous ownership/facade boundary even if the solver kernel itself only consumes its input contract.

**V3 direction:** choose one canonical owner for study preparation. Keep the numerical kernel dependent only on immutable numerical inputs. Either (a) make a distinct Study Preparation layer produce solver-neutral contracts, or (b) make Analysis own orchestration/preparation and remove the misleading Solver preparation wrapper through a compatibility adapter. The correct option must be decided after all public consumers and plugin integrations are mapped.

### Short Circuit dependency trace

Observed source dependencies:

- `core/analysis/short_circuit_preparation.py` imports Solver-owned `FaultType`, `ShortCircuitInput`, sequence snapshot contracts and `PhaseDomainShortCircuitCase`.
- The same Analysis preparation module imports `PhaseDomainShortCircuitCase` directly from `core.solver.short_circuit.phase_domain_solver`.
- `core/solver/short_circuit/phase_domain_solver.py` imports `PhaseDomainAdmittanceSnapshot` from `core.analysis.phase_domain_network_preparation` and `PhysicalConductorImpedanceSnapshot` from `core.analysis.physical_conductor_preparation`.
- `core/solver/short_circuit/input.py` imports `PhaseDomainShortCircuitCase` from the solver's phase-domain solver module.
- `core/analysis/phase_domain_network_preparation.py` builds `PhaseDomainAdmittanceSnapshot` using network conductor topology and a prepared physical-conductor impedance snapshot.
- `core/analysis/physical_conductor_preparation.py` builds `PhysicalConductorImpedanceSnapshot` from Core Network's physical conductor topology snapshot.

**Interpretation:** the case/input data contract and solver implementation are entangled, while solver implementation imports study-preparation snapshot classes from Analysis. This is a genuine bidirectional package dependency, not merely a lazy-export concern. The phase-domain solver's local import of `assemble_phase_domain_admittance` further indicates preparation logic has crossed into the execution module.

**V3 direction:** move stable immutable data contracts (case, prepared admittance and impedance snapshots, source/fault equivalents) into a neutral study-contract package or a carefully bounded Solver input-contract package. The preparation service should create those values; Solver should consume them and return typed solutions. Solver must not import Analysis preparation implementations. Keep network topology snapshots as inputs from the Network domain. Avoid moving engineering preparation algorithms into a numerical kernel.

### Additional package/API evidence

- `core/analysis/__init__.py` re-exports many study and preparation modules as a broad package facade.
- `core/solver/short_circuit/__init__.py` uses lazy attribute loading for phase-domain exports, consistent with a known import-cycle workaround.
- `core/solver/power_flow/preparation.py` presents a Solver package API while delegating its implementation to Analysis. This is a compatibility façade candidate, not evidence that preparation should automatically move to Solver.
- `PowerFlowInput` is a frozen dataclass with validation and typed bus categories; it is a useful existing pattern for explicit numerical input contracts. It should be assessed for completeness/provenance rather than replaced by a new abstraction without need.
- `ShortCircuitInput` is also frozen and validates its phase-domain fault data, but currently imports its phase-domain case from the solver implementation module. That coupling should be reversed by extracting the case contract.
- Network-owned topology snapshots and physical conductor topology are appropriate domain inputs; the unresolved ownership is the study-prepared numerical representation built from them.

### Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F07 | P0 | Analysis Short Circuit preparation imports Solver input/case types; Solver phase-domain implementation imports Analysis prepared snapshots | Extract stable DTOs/contracts; enforce Preparation → Solver one-way dependency |
| V3-ARCH-F08 | P1 | Solver Power Flow preparation wrapper delegates back to Analysis implementation | Decide canonical preparation ownership and treat wrapper as compatibility-only or replace it with an explicit contract |
| V3-ARCH-F09 | P1 | ShortCircuitInput imports PhaseDomainShortCircuitCase from solver implementation module | Move case DTO to a contract module independent of solver algorithm implementation |
| V3-ARCH-F10 | P1 | Phase-domain solver locally imports Analysis admittance assembly | Keep assembly in preparation; solver consumes completed immutable snapshot |
| V3-ARCH-F11 | P1 | PowerFlowInput already provides a frozen typed numerical input contract | Reuse and strengthen existing contract pattern, including assumptions/provenance/version metadata as justified |

### Verification limits

This pass is source inspection of named files, not an exhaustive consumer search or runtime import graph. Direct call sites of the wrappers and public exports remain to be mapped. No tests, CI, syntax/import execution or performance measurements were run.

## 8C. Core domain ownership audit — models, topology, measurement, Control and Protection (2026-11-03)

This pass inspected the model identity/terminal/Bus/Motor contracts, Network topology and snapshots, Measurement channel/provisioning/generation, Control domain contracts, Protection domain contracts, Application lifecycle services, execution bridges and the Application composition root.

### A. Equipment identity, terminals and Network topology

**Observed ownership that is directionally sound:**

- `core/model/base.py` defines the Core electrical-object identity and validation base.
- `core/model/terminal.py` defines an equipment-owned Terminal with a semantic role and endpoint reference. Its documented boundary explicitly excludes global topology, solver indices, calculations and UI state.
- `core/model/bus.py` and `core/model/motor.py` own their equipment parameters/operating state and their terminal(s); the Bus owns one authoritative terminal and Motor similarly owns one authoritative terminal.
- `core/network/network.py` validates Network membership, terminal ownership, endpoint membership and consistency between physical terminal references and resolved Bus identities.
- `core/network/topology.py` builds topology from registered equipment/connectivity and emits detached `TopologySnapshot`; `core/network/topology_snapshot.py` uses frozen dataclasses and immutable mappings.
- `core/network/physical_conductor_topology.py` maps explicit Line/Cable conductor inventories to canonical Network topology without taking over electrical node ownership.

**Interpretation:** the Equipment → Terminal → Network → TopologySnapshot separation is a useful V2 foundation and should be preserved in V3. A topology snapshot is a derived, detached representation; it should not become a second editable source of truth.

**Extension concern:** `core/network/topology.py` imports a concrete list of equipment classes from `core.model` and hard-codes `_TOPOLOGY_TYPES`. The physical-conductor topology builder separately limits its supported branch types to Line and Cable. This is explicit and safe for the present model set, but it means adding a new plugin-provided conductive equipment family may require changes to Core's topology implementation. V3 should assess a typed topology-capability/descriptor contract, with registrations assembled by Application, while retaining Core validation of electrical semantics. Do not solve this by letting Core import plugin implementations.

### B. Endpoint identity and package-facade coupling

- `core/model/endpoint_reference.py` defines immutable endpoint references, but imports its equipment symbols from `core.model` (the package facade) rather than narrowly importing a lower-level contract module.
- `core/model/__init__.py` imports the equipment model collection and later imports `EndpointReference`, so the facade participates in a reverse import path. The exact runtime consequences have not been executed in this audit.
- The package initializer also patches Relay identity properties and registers Relay with `ElectricalObject`, making it a composition point for compatibility behaviour as well as exports.

**V3 direction:** place canonical equipment-type and endpoint-reference contracts in a low-level identity/contracts module that does not import the broad model facade. Keep model package exports declarative; move compatibility adaptation/registration into an explicit composition or compatibility module. Confirm import graph and backward-compatibility requirements before migration.

### C. Measurement ownership and conversion pipeline

**Observed separation:**

- `core/measurement/measurement_channel.py` defines channel signal type, phase, quality, validity, source reference, engineering configuration, timestamps, sample sequence and usability.
- `core/measurement/measurement_provisioning.py` creates logical channels from explicit instrument secondary terminals (CT/PT/CVT); its documented split assigns physical terminal resolution to Application and channel construction/secondary-terminal validation to Core.
- `core/application/services/measurement_channel_service.py` owns the active project's channel registry, activation generation, sample ingress, trusted source verifier, clock-domain validation, monotonic sequence checks and sample update authority. It publishes the accepted sample to an Application-bound trigger after validation.
- `core/control/measurement_input.py` converts a MeasurementChannel into a typed Control input; `core/protection/relay_input.py` exposes a Protection-facing view without owning or copying the channel's authoritative sample state.

**Confirmed boundary concern:**

- `core/measurement/measurement_generation.py` imports Analysis result types (`LineFlowResult`, `TransformerFlowResult`), Solver result types (`PowerFlowResult`, `ShortCircuitResult`) and Network measurement association types.
- It converts numerical results into physical engineering quantities and CT/PT/CVT secondary values before updating logical measurement channels.

**Interpretation:** MeasurementChannel ownership and trusted sample ingress are clearly separated, but the result-to-measurement generation module reaches upward into Analysis and Solver. This couples the Measurement package to study execution/result types and risks turning Measurement into a consumer of every solver's result model.

**V3 direction:** split this pipeline into (1) a result-to-physical-quantity adapter at the Application/Study integration boundary, (2) instrument ratio/polarity/secondary conversion using stable typed physical-quantity contracts, and (3) channel publication through the existing Application-owned MeasurementChannelService. The Measurement domain should own channel semantics, quality, units and instrument conversion rules; it should not import individual solver result classes. Preserve the current single conversion authority and provenance rather than duplicating CT/PT/CVT scaling logic.

### D. Control domain ownership

- `core/control/decision.py` defines immutable `ControlDecision` intent without Core object references.
- `core/control/engine.py` evaluates project Control configuration and logic into immutable evaluation results.
- `core/control/signals.py` documents signal values as transport objects, not owners of electrical/network truth.
- `core/application/services/control_service.py` owns project-scoped Control configuration lifecycle and performs transactional component/connection edits.
- `core/application/control_execution.py` and `core/application/control_dispatch.py` translate/effect Control intent through Application commands. The dispatcher is explicitly the Application bridge to the command system.
- `core/control/configuration.py` persists project-owned Control configuration and reconstructs runtime logic from it.

**Interpretation:** this is broadly aligned with the frozen boundary: Control evaluates and emits intent; Application owns command execution and mutation. V3 should preserve the distinction between persistent engineering configuration, runtime evaluation state, decision intent and command execution.

**Maintainability concern:** `core/control/__init__.py` eagerly exports multiple subdomains and performs a compatibility mutation by assigning `ControlState` onto the imported `base` module. This should be reviewed as an API/compatibility concern, not treated as a demonstrated functional defect.

### E. Protection domain ownership and Control integration

- `core/protection/relay_input.py` consumes MeasurementChannel and explicitly documents that it does not own measurement state or transform values.
- `core/protection/relay_base.py` represents one executable protection function hosted by a physical Relay.
- `core/protection/protection_element.py` composes a protection-function instance and produces ProtectionDecision.
- `core/protection/decision.py` defines the immutable ProtectionDecision contract, distinct from ControlDecision.
- `core/application/services/protection_configuration_service.py` owns project-scoped protection configuration and measurement bindings, while referencing Network, instruments, MeasurementChannel and Protection contracts.
- `core/application/protection_execution.py` explicitly resolves actionable ProtectionDecision values to ControlDecision through an Application-owned resolver, then translates to Application commands and dispatches through the shared Application command boundary. It records dispatch outcomes and does not fabricate physical acknowledgement.

**Interpretation:** the explicit ProtectionDecision → Application resolver → ControlDecision → Application command bridge is a valid integration seam only if it remains an adapter, not a dependency of Protection on Control. The Protection and Control execution authorities remain separate; the shared command system is the mutation boundary.

**V3 direction:** formalise the cross-domain adapter as a typed, auditable action mapping contract. Preserve source ProtectionDecision identity, relay/function identity, target resolution, authorization, command correlation and postcondition/physical-feedback distinctions. Do not make Protection import Control execution internals or silently treat a Control decision as proof that a physical device acknowledged an operation.

### F. Application composition and responsibility

- `core/application/bootstrap.py` is the composition root: it creates the MeasurementChannelService, ProtectionConfigurationService, ControlApplicationService, command handlers, command manager, Network read/validation services and the execution bridges.
- The same composition root wires trusted measurement ingress to the Application protection trigger and uses a shared execution lock around sample publication and breaker authorization.
- This supports Application as the owner of project lifecycle, orchestration, transaction/command composition and cross-domain coordination.

**V3 direction:** preserve a single composition root and shared authoritative services. As the platform grows, split bootstrap into named composition modules/factories by capability (project/model, measurement, control, protection, studies, persistence) while keeping one top-level composition root and avoiding duplicate registries, locks, event buses or command managers.

### Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F12 | P1 | Measurement generation imports Analysis and Solver result classes directly | Separate study-result adaptation from Measurement channel/instrument conversion; use stable typed physical-quantity contracts |
| V3-ARCH-F13 | P1 | Network topology manager hard-codes Core equipment classes and topology type list | Design extensible typed topology capability descriptors/registrations without Core importing plugin implementations |
| V3-ARCH-F14 | P1 | EndpointReference imports equipment identity through broad `core.model` facade; model initializer also owns compatibility patches | Extract low-level identity/type contracts and move compatibility adaptation out of broad package exports |
| V3-ARCH-F15 | P1 | Measurement channel registry, trusted ingress and project activation are Application-owned while channel/sample semantics are Core-owned | Preserve this split and specify producer trust, timestamp domain, quality, sequence, activation-generation and provenance contracts as a first-class measurement lifecycle |
| V3-ARCH-F16 | P1 | Protection-to-Control translation is implemented in Application through a resolver and shared command dispatcher | Formalise a typed cross-domain action adapter with identity/correlation/authorization/feedback separation |
| V3-ARCH-F17 | P2 | Control package initializer performs module mutation and broad eager exports | Define stable public API and isolate compatibility aliases from domain package initialization |
| V3-ARCH-F18 | P2 | Application bootstrap composes many subsystems in one large module | Partition composition by capability while retaining one root and shared singleton authorities |

### Verification limits

This is a targeted source audit, not an exhaustive dependency graph or runtime import test. Topology extension requirements need validation against actual plugin equipment use cases. The full contents/consumers of every model class, all measurement producers, and all Control/Protection function implementations were not inspected. No tests, CI, syntax/import execution or runtime checks were run.

## 9. Status and next sequence

**Completed:** V3 research register opened and initial research tracks captured.  
**In progress:** Complete source/dependency audit; standards applicability and clause research; capability/gap mapping.  
**Not started:** V3 architecture approval, implementation, package migration, plugin consolidation or schema changes.

Next: finish repository dependency audit → complete standards applicability matrix → map current capabilities/gaps → refine and prioritise V3 requirements → submit V3 architecture baseline for review.

No tests, CI, runtime checks or implementation changes were performed as part of opening this register.


## 8D. Plugin platform and extension architecture audit

**Audit scope:** engineering Plugin SDK/host, UI plugin loader/manager/registry/contracts, Motor Dynamics manifest and lifecycle, application composition, equipment/symbol/tool/panel/projection registries, persistence type registry, Network membership registry, and shared numerical backend capability policy.

**Evidence inspected (V2 `main`):**
- `core/plugin_sdk/README.md`, `contracts.py`, `host.py`, `__init__.py`
- `plugins/motor_dynamics/manifest.json`, `plugin.py`, `transient_solver.py`, `npu_inference.py`, `README.md`
- `ui/plugins/plugin_contract.py`, `plugin_loader.py`, `plugin_manager.py`, `plugin_registry.py`, `plugin_context.py`
- `main.py` engineering-host and UI-plugin composition
- `ui/equipment/equipment_registry.py`, `ui/equipment/symbol/symbol_registry.py`, `ui/tools/tool_registry.py`, `ui/panels/panel_registry.py`, `ui/projection/projection_registry.py`
- `core/persistence/type_registry.py`, `core/network/registry.py`, `core/numerics/backend.py`
- Recursive repository tree to enumerate plugin manifests and plugin-related modules.

### A. Current plugin lifecycle topology

Two intentionally separate lifecycle systems are present:

1. **Engineering plugin lifecycle:** `core.plugin_sdk` defines `PluginDescriptor`, `GridForgePlugin`, `EngineeringPluginContext` and `EngineeringPluginHost`. The host validates descriptor identity and supported SDK API version, rejects duplicate IDs, invokes initialization, attempts rollback on initialization failure, retains failed rollback cleanup handles, supports explicit deactivation, and shuts down in reverse ownership order. The host receives already-constructed instances and explicit Application-owned services.
2. **UI composition lifecycle:** `ui.plugins` separates implementation loading/construction (`PluginLoader`), runtime registration/state/lifecycle (`PluginRegistry`) and dependency ordering/transactional composition (`PluginManager`). The loader imports explicitly defined modules/classes/factories. The manager resolves dependency closures, rejects dependency cycles, orders initialization and compensates registrations/initializations on failure.

The composition root in `main.py` creates the EngineeringPluginHost and explicitly activates MotorDynamicsPlugin with the existing Application-owned `motor_dynamics_composition` service. Separately it constructs the UI PluginManager, defines defaults, loads UI plugins and composes Canvas/Panels/Shell. This is evidence of deliberate lifecycle separation, not by itself an architectural defect.

### B. Discovery, manifests and compatibility

The recursive V2 repository tree contains one plugin manifest: `plugins/motor_dynamics/manifest.json`. It declares plugin ID, name, version, API version, entry point, string capabilities, runtime dependencies and CPU/GPU/NPU/inference policy.

The engineering host does not discover or parse this manifest. Its caller constructs `MotorDynamicsPlugin` and passes the instance to `activate()`. The plugin class separately defines a Python `PluginDescriptor` and validates it against the host-supported API versions. Thus the JSON manifest and runtime descriptor are parallel metadata representations; the inspected source does not establish an automated consistency check between them.

The UI PluginLoader uses an explicit in-code `DEFAULT_PLUGIN_IMPLEMENTATIONS` mapping for Canvas, Menu, Panels, Toolbar, Status and Shell. UI PluginManager defines default dependencies in code. The UI contract explicitly assigns discovery/construction to the loader and dependency ordering to the manager; the loader does not scan for plugins or parse a plugin manifest.

**Interpretation:** V2 has explicit and auditable activation, but not a unified discovery/catalogue/install pipeline. The absence of generic discovery is documented as an intentional limit of the engineering SDK, so it should be recorded as a V3 capability requirement rather than reported as an accidental V2 defect.

### C. Typed capabilities and dependency model

Engineering `PluginDescriptor.capabilities` is a `frozenset[str]`; the manifest also uses string capability labels. The descriptor validates non-empty strings and API-version compatibility, but the inspected contract does not provide typed capability payloads, contribution-point schemas, dependency declarations, version ranges, optional dependency semantics, conflict resolution or capability negotiation.

By contrast, UI `PluginDefinition` carries dependency IDs and the UI manager computes a topological initialization order, detects cycles and requires dependencies to be enabled and initialized. These UI dependencies are in-code definitions rather than a shared engineering/UI manifest model.

**V3 direction:** define a versioned manifest schema and typed contribution contracts. Model plugin identity/version separately from SDK contract version; support required/optional dependencies, compatible version ranges, conflicts, declared capabilities, contribution points, required Application services and lifecycle policy. Resolve the complete dependency graph before executing plugin code. Keep UI and engineering activation adapters distinct where their lifecycle/resource needs differ, but use one validated metadata and compatibility model.

### D. Extension contribution and registry topology

The inspected repository has independent registries and type maps for:
- UI equipment definitions (`EquipmentRegistry`) and renderer-neutral SLD symbol definitions (`SymbolRegistry`);
- UI tools, panels and projections;
- persisted Core model type names (`ModelTypeRegistry`);
- Network membership and typed equipment collections (`NetworkRegistry`);
- numerical backend capabilities and selection policy (`core.numerics.backend`).

The UI equipment registry owns presentation/catalogue definitions only and explicitly does not create Core equipment or validate electrical topology. It is populated from a built-in equipment-definition list and reconciles equipment, creation, symbol and optional Core terminal-role contracts. The symbol registry separately owns renderer-neutral symbol definitions.

The persistence type registry seeds a fixed mapping of persisted names to concrete Core classes and a separate fixed mapping from Core model classes to Network adder method names. NetworkRegistry exposes concrete equipment-specific typed collections and add/remove operations. These contracts are consistent with Core retaining electrical/domain authority, but they make a future third-party equipment extension more than a UI registration task.

**Confirmed architectural concern:** there is no single inspected contribution contract connecting a plugin-provided equipment type across domain model construction/identity, terminal semantics, topology capability, persistence serialization/reconstruction, study participation, measurement/protection/control integration and UI symbol/tool/property-editor presentation. The current independent registries are legitimate bounded authorities, but V3 needs an Application-owned composition mechanism to coordinate their registrations and validate completeness without allowing plugins to mutate Core directly.

**V3 direction:** define capability-specific typed contribution points and an Application-owned registration transaction. A contributed equipment type must declare its Core-facing domain contract and explicit support/limitations for topology, persistence, studies and relevant cross-domain services; UI contributions (symbol, palette/tool, property editor, renderer, panel) remain presentation adapters. Registration should validate cross-registry consistency, own reversible registration tokens and reject partial activation. Core should consume stable contracts or registered descriptors assembled by Application, never import plugin implementations.

### E. Analysis, solver and compute extension

The shared `core.numerics.backend` module defines immutable `BackendCapability` facts (backend kind, availability, supported workloads, minimum workload size and precision modes), deterministic selection, rejection reasons and a generic numerical-problem adapter protocol/dispatch path. It deliberately does not probe devices or import accelerator runtimes; adapters provide capability facts. This is a positive reusable foundation for CPU/GPU/NPU workload policy.

Motor Dynamics currently uses the shared `BackendCapability` and `select_backend` policy for its CPU reference and optional Numba-CUDA batch execution. The CUDA adapter only advertises the supported independent-motor workload; unsupported input shape/workload conditions are rejected or routed to CPU. Its separate ONNX inference adapter has a provider list including QNN/Vitis AI/OpenVINO and other execution providers, requires CPU fallback, validates supported tensor shapes/types and records fallback diagnostics. The manifest and README explicitly distinguish NPU-capable inference providers from the recurrent motor-physics solver.

The Motor Dynamics README labels the extension experimental. It documents a bounded balanced squirrel-cage induction motor dq model with fixed-step RK4 and one lumped thermal node, while magnetic saturation, unbalance, switching converters, separate stator/rotor thermal nodes and trusted reference-case validation remain outside current scope. End-to-end study execution, numerical reference validation and accelerator hardware validation remain outstanding. Provider presence/session creation is not treated as proof of graph placement or numerical equivalence.

**V3 direction:** standardize solver/study plugin contracts around immutable numerical problem snapshots, workload and precision declarations, cancellation/progress, deterministic CPU reference behavior, backend capability adapters, result provenance and reproducibility metadata. Separate physics execution from optional AI inference capabilities. GPU/NPU claims must be workload-specific and validated; inference output must not become a Protection decision authority. Preserve Application ownership of study lifecycle, cancellation, events and authoritative result publication.

### F. Lifecycle, trust and isolation

The inspected hosts provide explicit initialization/shutdown and compensation, but the engineering host accepts in-process Python plugin objects and service references. The inspected code does not establish process isolation, sandboxing, signed package verification, permission/capability enforcement or a hostile-plugin security boundary. The manifest describes runtime requirements but is not shown being validated/consumed by the host.

**Interpretation:** lifecycle rollback is not security isolation. In-process plugins execute with the Python process privileges and any capabilities reachable through their injected objects.

**V3 direction:** define a trust model for first-party, approved third-party and untrusted extensions. Add package provenance/signature policy, manifest/schema validation, explicit permission grants, service-scoped capability injection, resource quotas and audit events. Decide which workloads require process isolation or a worker boundary. Do not describe ordinary in-process plugin lifecycle as a sandbox.

### Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F19 | P1 | Engineering host takes explicit instances; only Motor Dynamics manifest found in recursive tree and no manifest discovery/validation path inspected; UI implementations/default dependencies are also explicit in code | Design a shared validated manifest/catalogue/discovery model while retaining separate engineering/UI lifecycle adapters |
| V3-ARCH-F20 | P1 | Equipment, symbol, tool, panel, projection, persistence and Network registration are separate; Core persistence/Network maps remain concrete-type based | Define Application-owned transactional contribution orchestration and cross-registry completeness validation; keep Core independent of plugin implementations |
| V3-ARCH-F21 | P1 | Engineering capability labels are strings and descriptor lacks dependency/version-range/contribution schemas; UI manager has a separate in-code dependency graph | Define typed capability and contribution contracts, dependency/version resolution, conflict policy and API compatibility rules |
| V3-ARCH-F22 | P1 | Engineering host lifecycle is in-process; inspected contract/manifest does not establish package trust, permissions or isolation | Specify plugin trust levels, provenance, scoped permissions, auditability and isolation requirements |
| V3-ARCH-F23 | P1 | Shared numerical backend capability policy exists and Motor Dynamics uses it for CPU/CUDA selection, while ONNX inference is a separate provider path; validation remains incomplete | Standardize study/solver extension contracts and evidence-based CPU/GPU/NPU execution diagnostics; keep inference distinct from physics and Protection authority |
| V3-ARCH-F24 | P2 | Motor Dynamics manifest and Python descriptor both carry plugin identity/version/capability metadata, with no consistency validator observed in inspected activation path | Make one manifest schema authoritative and derive/validate runtime descriptor metadata from it |

### Verification limits

This was a targeted source audit plus a complete recursive tree enumeration, not an exhaustive review of every registry consumer, plugin module, or package distribution path. The tree search found one manifest file; this does not prove that no runtime-generated or external plugin catalog exists outside the inspected repository. The audit did not inspect every contribution registration call or every built-in equipment type's end-to-end persistence/study behavior. No tests, CI, syntax/import execution, runtime plugin activation, numerical reference-case validation or accelerator hardware checks were run. No V2 source was changed.



## 8E. Project persistence, schema evolution and engineering-data interchange audit (2026-11-03)

**Audit scope:** canonical `.gridforge` package contract, project loader/saver, Core model DTO and Network serialization, schema migration pipeline, Study Case persistence, Study Result archive, Application project lifecycle transaction and UI project-workspace adapter. Recursive repository tree was also inspected for dedicated CIM/SCL/interchange modules.

**Evidence inspected (V2 `main`):**
- `core/persistence/project_package.py`, `project_persistence.py`, `migration.py`, `model_dto.py`, `network_serializer.py`, `type_registry.py`, `study_result_archive.py`
- `core/application/project.py`, `project_lifecycle.py`, `project_transition.py`, `project_presentation.py`
- `ui/workspace/project_workspace.py`, `project_workspace_adapter.py`
- Recursive repository tree for persistence, project, import/export, CIM and SCL-related paths.

### A. Canonical package and persistence ownership

The current package is a directory-style `.gridforge` package with `manifest.json` and `project.json`. The manifest currently stores `format = GridForgeProject` and `package_version = 1`. The project payload separately stores `schema = 4`; additional version constants exist for presentation (1), SLD (3), Core serialization (1), transformer configuration (1) and connectivity (4).

The canonical project payload currently includes:
- Project identity/name.
- Core Network equipment state and connectivity.
- A collection of presentation documents and active document identity.
- Dynamic machine model associations.
- Measurement channel definitions.
- Study Case definitions.
- Optional Protection configuration/presentation.
- Optional Control configuration and Control signal mappings.
- Optional draft network state.

The package writer builds a complete temporary candidate directory, writes JSON files with file flush/fsync, replaces the existing package through a sibling backup and attempts recovery after interrupted replacement. The source documentation correctly qualifies directory-entry durability as platform-specific.

**Positive finding:** persistence is not a serialized Qt scene. SLD documents are serialized as canonical presentation data separately from Core Network equipment/connectivity. Project lifecycle is Application-owned; candidate activation uses rollback callbacks and a project activation generation. Normal project opening distinguishes read-only activation audit from an explicitly selected persistent reconciliation transaction.

### B. Schema evolution and migration

The migration pipeline is detached from Application mutation and Qt/UI state. It applies deterministic project-schema steps 1→2→3→4, then presentation-collection/SLD migration and connectivity normalization. It rejects unsupported future schema versions and has an explicit gap failure when a migration step is missing. SLD schema migration has its own version sequence (1→2→3). Connectivity has a separate schema sequence up to version 4.

Legacy electrical migration deliberately rejects ambiguous cable impedance units and transformer impedance basis instead of guessing. Canonical SLD validation rejects unknown fields and validates identity, document type, node/connection structures, symbol presentation and annotation-block references.

**Interpretation:** V2 already has valuable fail-closed migration practices. The version model is nevertheless distributed across package, project, Core serialization, connectivity, SLD, presentation, transformer configuration and Study Case records. Some nested payloads (for example measurement channel definitions in the project envelope) do not expose an independently versioned contract in the inspected save shape. V3 should publish a version ownership matrix and define which nested domains require independent schema evolution.

### C. Core model serialization and reconstruction

Network serialization emits deterministic, sorted equipment DTOs and explicit connectivity collections. Reconstruction uses an explicit `ModelTypeRegistry`, rebuilds equipment membership, resolves object references through the Network identity authority, restores terminal attachments, then reconstructs junctions, simple wires and phase-domain conductor connectivity. Persisted type resolution and Network adder operations are explicit mappings rather than arbitrary class-name lookup.

**Security-relevant confirmed concern:** `core/persistence/model_dto.py::_decode` handles `$enum` and `$dataclass` tags by taking a module-qualified name from persisted data, importing that module with `__import__`, resolving the named attribute and, for dataclasses, invoking its constructor with persisted fields. This is materially different from the explicit allowlist used for top-level Network model types and the Study Result archive's schema-v2 solver result reconstruction. Opening an untrusted project can therefore trigger imports and constructors selected by data in the project file. The source audit does not establish arbitrary code execution in every environment, but it does establish an unsafe polymorphic-deserialization surface with import-time and constructor side effects.

**V3 direction:** replace persisted Python module/class names with stable schema type IDs resolved through an explicit allowlist/codec registry. Do not import or instantiate types named by an untrusted package. Validate exact allowed fields and versioned payload schemas before constructing objects. Treat project packages as untrusted input at the file boundary.

### D. Study Cases versus Study Results

Study Case definitions are persisted in `project.json` with their own schema marker (currently 1), typed configuration kinds for Power Flow, Short Circuit and Transient Stability, source revision fields and non-runtime options. Runtime-only prepared inputs/results are intentionally excluded. Unsupported configuration kinds fail closed.

Study Result execution artifacts use a separate append-only `StudyResultArchive`, stored outside the `.gridforge` package under a caller-supplied archive root, keyed by hashed project identity and activation generation. Archive records include study identity, project identity, activation generation, source revision, status, timestamp, result payload and SHA-256 integrity digest. Archive schema is currently 2. The archive explicitly separates execution history from editable project configuration so saving a project cannot overwrite study history.

The archive's schema-v2 decoder uses allowlisted solver result/event/algebraic record types and rejects field mismatches; unknown enum types are retained as detached scalar values rather than imported. Schema-v1 historical generic dataclass compatibility remains a separate legacy behavior and needs its own security/upgrade disposition.

**V3 direction:** retain the conceptual distinction between project configuration and execution history, but define a portable project bundle/export operation that can include selected result records, checksums, source revision, solver/version provenance and required artifacts. Define retention, relocation, backup/restore and missing-archive behavior. Project portability must not silently imply that external result history is embedded.

### E. Engineering-data interchange

The recursive repository tree search did not identify dedicated IEC CIM (IEC 61970/61968) or IEC 61850 SCL import/export adapter packages or a general-purpose interchange subsystem. The current persistence serializers are GridForge-native formats; they are not evidence of standards-compliant CIM or SCL exchange.

**V3 direction:** treat native project persistence, standards interchange and vendor-specific import/export as separate bounded layers. Research CIM profiles/mappings and IEC 61850 SCL model coverage, version negotiation, namespace/schema validation, round-trip fidelity, unsupported-feature reporting, identity mapping, units/base conversion and provenance. Imports should produce a validated candidate project and explicit reconciliation report before Application-controlled activation; exports should report omitted or lossy semantics rather than silently dropping them.

### F. Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F25 | P1 | Persisted `$enum`/`$dataclass` tags in `model_dto.py` drive dynamic module import, attribute resolution and dataclass construction from package-controlled strings | Replace dynamic type loading with stable allowlisted type IDs/codecs; define untrusted-project threat model and safe migration |
| V3-ARCH-F26 | P1 | Package/project/SLD/connectivity/Core/transformer/Study Case/archive schemas have separate version constants and migration paths; nested domain version ownership is not uniformly explicit | Publish version ownership and compatibility matrix; version every independently evolving persisted contract |
| V3-ARCH-F27 | P1 | Study Result archive is intentionally outside the project package and keyed separately by project/generation | Define portable bundle, archive relocation, backup/restore, result inclusion and provenance policy |
| V3-ARCH-F28 | P1 | Recursive tree inspection found no dedicated CIM/SCL/general interchange adapter package; native serializer is GridForge-specific | Specify separate CIM/SCL/vendor interchange adapters with profile coverage, round-trip/loss reporting and candidate-project validation |
| V3-ARCH-F29 | P2 | `ProjectPersistenceService` coordinates serialization/deserialization for Network, SLD/presentations, Measurement, Protection, Control, dynamic models and Study Cases through one large service | Evaluate V3 decomposition into domain-owned codecs plus one package orchestration/transaction owner; do not split ownership or duplicate project transactions |
| V3-ARCH-F30 | P2 | Project manifest carries package format/version while project schema and nested schema versions live in `project.json` and domain payloads | Define explicit manifest-to-payload compatibility contract, minimum reader version and migration capability declarations |

### Verification limits

This was a targeted source audit and recursive tree search, not a complete review of every serialized field, every legacy fixture, all archive schema-v1 records or all project activation callbacks. The import/constructor finding is based on direct inspection of the persisted DTO decoder; no exploit, malicious package or runtime execution was attempted. The absence of a dedicated CIM/SCL adapter is based on the inspected repository tree and does not rule out external tools or untracked integrations. No tests, CI, syntax/import execution, migration replay, save/load round-trip, runtime project transition, interoperability validation or security testing was run. No V2 source was changed.


## 8F. Standards and Indian regulatory applicability — first official-source batch (2026-11-03)

**Research boundary:** This is an applicability discovery pass, not a clause-level compliance assessment. Official IEC and Indian regulator/catalogue sources were checked. Full normative text, exact clause mapping, BIS adoption status and asset-specific applicability remain to be established before requirements or conformance claims are frozen.

### A. IEC 61850 — substation automation, data models and engineering exchange

- The IEC Webstore's current all-parts series listing is `IEC 61850:2026 SER`, published 2026-09-18. The package listing spans International Standards, Technical Specifications, Technical Reports and a Publicly Available Specification; it is not one monolithic normative document.
- `IEC 61850-6:2009+AMD1:2018+AMD2:2024 CSV`, edition 2.2, is the consolidated current SCL/configuration-description publication found in this source pass. Its scope includes IED capability descriptions, IED parameters, communication system configuration, substation automation system structures and relations, and configuration exchange between engineering tools.
- `IEC TS 61850-6-3:2025` specifies a machine-processable OCL rule format for validation of IEC 61850 XML-based files, including validation during engineering and checking upgrade/downgrade rule conformity. It is a Technical Specification, not a replacement for the normative SCL data model.
- `IEC TR 61850-7-6:2024` is a Technical Report focused on typical information exchange and engineering conventions; it explicitly does not define application implementation requirements.

**V3 implication:** define explicit supported IEC 61850 parts/profiles/use cases. SCL import/export should be a distinct engineering interchange subsystem with schema validation, profile/rule validation, IED capability modelling, communication configuration and loss reporting. Do not claim generic “IEC 61850 compliance” from supporting SCL XML alone.

### B. IEC 60255 — protection equipment and digital process interfaces

- `IEC 60255-1:2022`, edition 2.0, is the current common-requirements publication identified. The IEC scope includes measuring relays/protection equipment and distributed protection schemes; the edition's stated changes include merging units and communications as integral protection components, binary output clarification, environmental conditions, and low-power instrument transformers.
- `IEC TS 60255-216-1:2025`, edition 1.0, is a Technical Specification for protection functions using digital communication as input and output. The official scope specifically covers SV subscription, GOOSE subscription/publication and time-synchronisation subscription, plus functional interoperability and functional requirements/tests.

**V3 implication:** protection requirements must model digital input quality/time, SV stream identity and subscription, GOOSE input/output semantics, merging-unit interfaces, time synchronisation, functional interoperability and test evidence. Keep the relay function, protection decision, output command, physical actuation and breaker feedback as distinct lifecycle stages. This supports the existing Signal/Measurement and Protection domain separation; it does not establish product certification.

### C. IEC 61131-3 — PLC programming-language scope

- `IEC 61131-3:2025`, edition 4.0, is listed by IEC as valid, published 2025-05-22, with a stated stability date of 2027.
- The official scope covers syntax and semantics for Structured Text (ST), Ladder Diagram (LD), Function Block Diagram (FBD), Sequential Function Chart (SFC), configuration elements and features facilitating communication among programmable controllers and other automation components.
- The publication does not by itself define the complete PLC execution runtime, all task scheduling/scan-cycle semantics, controller operating-system behavior or field communication protocol profiles; related IEC 61131 parts and other standards must be evaluated separately.

**V3 implication:** Control Canvas should distinguish IEC 61131-3 language representation/compiler semantics from execution scheduling, task/scan model, runtime state, I/O binding and communications. Build a language/profile support matrix rather than treating a graphical function-block editor as proof of PLC conformance.

### D. India — notified regulations, regulator material and draft separation

- CEA's official regulations page lists the `Central Electricity Authority (Measures relating to Safety and Electric Supply) Regulations, 2023` and a `2026 Amendment Regulations` entry as notified regulations. The 2026 amendment must be incorporated into the applicable consolidated legal baseline after Gazette text and commencement provisions are checked.
- CEA's official Construction Standards page lists the 2022 Technical Standards for Construction of Electrical Plants and Electric Lines regulations, the 2025 amendment and a 2026 amendment entry.
- CEA's official updates page (2026-10-05) records a request for public comments on a **draft list of relevant standards** applicable under the 2023 Safety and Electric Supply Regulations and amendments. That list is consultation material until formally adopted/notified; it must not be represented as an operative notified standards list.
- CEA's official updates page records the `Manual on Transmission Planning Criteria, 2026` (2026-10-14). Its legal character and relationship to notified regulations must be distinguished from regulations; it is planning criteria/guidance unless the governing instrument gives a specific binding effect.
- CERC's official current-regulations register lists the Indian Electricity Grid Code Regulations, 2023 and amendments, including an amendment dated 2026-03-10. It also lists other grid/connectivity regulations and amendments. Applicability depends on the asset, connection, voltage level, licensee/generator role and jurisdiction; central inter-state rules are not automatically universal requirements for every industrial plant.

**V3 implication:** create an India applicability profile with separate legal classes: Acts/rules, notified CEA/CERC regulations, Gazette amendments/commencement, grid codes and procedures, manuals/criteria, BIS adoptions and draft consultations. Model jurisdiction, effective date, asset/workflow applicability, supersession and evidence links. A plant-specific compliance checklist must be generated only after asset and connection scope are known.

### E. Open research questions and evidence gaps

1. Verify the Gazette text, commencement dates and consolidated wording of each CEA 2026 amendment before encoding requirements.
2. Obtain and reconcile the official BIS catalogue/adoption records for each relevant IEC edition; international publication status does not establish Indian adoption or identical national edition.
3. Build an applicability matrix by asset class (industrial captive plant, generating station, transmission, distribution, substation, IED/PLC system), voltage level, owner/operator role and jurisdiction.
4. Obtain licensed normative texts and map precise clauses to GridForge model fields, workflows, validations, reports and evidence. Public abstracts are discovery sources only.
5. Identify relevant companion parts for IEC 61850, IEC 60255, IEC 61131, IEC 61970/61968 CIM, IEC 62443, IEC 62682 and IEC 81346; record document type and edition status individually.

### Official source register — first batch

- IEC 61850 all-parts series, 2026 — https://webstore.iec.ch/en/publication/6028
- IEC 61850-6 consolidated edition 2.2 (2009+AMD1:2018+AMD2:2024) — https://webstore.iec.ch/en/publication/103863
- IEC TS 61850-6-3:2025 — https://webstore.iec.ch/en/publication/79695
- IEC TR 61850-7-6:2024 — https://webstore.iec.ch/en/publication/84757
- IEC 60255-1:2022 — https://webstore.iec.ch/en/publication/59762
- IEC TS 60255-216-1:2025 — https://webstore.iec.ch/en/publication/77735
- IEC 61131-3:2025 — https://webstore.iec.ch/en/publication/68533
- CEA notified safety regulations and amendments — https://cea.nic.in/regulations-subcategory/ad9da247-723a-4a60-9182-fc2753458916?lang=en
- CEA construction standards and amendments — https://www.cea.nic.in/regulations-category/c5e1ec5f-ca2f-4057-8a31-857f91a71701?lang=en
- CEA draft regulations — https://www.cea.nic.in/regulations/draft-regulations?lang=en
- CEA official updates — https://www.cea.nic.in/whats-new/all-updates?lang=en
- CERC current regulations — https://cercind.gov.in/current_reg.html

**Verification limits:** Official catalogue/regulator pages and publication abstracts were inspected; licensed normative standards and all Gazette PDFs were not downloaded or clause-audited. BIS adoption records were not verified in this batch. The date/status statements are a research snapshot and must be refreshed before V3 release. No compliance claim is made.


## 8G. BIS adoption evidence, CEA 2026 Gazette amendments and asset applicability (2026-11-03)

**Research boundary:** This is a second official-source batch. It records verified publication/adoption evidence and regulatory applicability dimensions; it is not a legal opinion or complete BIS catalogue export. The current V3 requirements baseline must distinguish publication date, notification date, commencement date and project/asset applicability.

### A. BIS adoption evidence — confirmed subset

The BIS ETD 34 (Instrument Transformers) official Program of Work identifies the following as published Indian Standards, with identical-under-dual-numbering equivalence to the cited IEC editions:
- IS 16227 (Part 1):2016 — IEC 61869-1:2007, general requirements.
- IS 16227 (Part 2):2016 — IEC 61869-2:2012, current transformers.
- IS 16227 (Part 3):2015 — IEC 61869-3:2011, inductive voltage transformers.
- IS 16227 (Part 4):2015 — IEC 61869-4:2013, combined transformers.
- IS 16227 (Part 5):2015 — IEC 61869-5:2015, capacitor voltage transformers.
- IS 16227 (Part 6):2018 — IEC 61869-6:2016, low-power instrument transformers.
- IS 16227 (Part 9):2018 — IEC 61869-9:2016, digital interface for instrument transformers.
- IS 16227 (Part 100):2018 — IEC 61869-100:2017, CT application in power-system protection.
- IS 16227 (Part 102):2018 and Part 103:2018 are listed as identical-under-dual-numbering adoptions of the corresponding IEC technical reports on ferroresonance and power-quality measurement use of instrument transformers.

The BIS Program of Work is strong official evidence for these published standards. It is not a substitute for checking each standard's current status, amendments, reaffirmation and supersession in the BIS Know Your Standard catalogue before a compliance profile is generated.

A separate BIS draft document (ETD 42, September 2023) lists Indian counterparts for IEC 60255-121:2014, IEC 60255-127:2010, IEC 60255-151:2009 and IEC 60255-181:2019, but that document is explicitly marked **Draft for Comments Only**. These references are useful discovery leads, not proof in this audit that the corresponding Indian Standards are currently published/in force. Current catalogue verification is still required. This pass did not establish current BIS adoption of IEC 61850-6:2024 consolidated edition or IEC 61131-3:2025; do not infer non-adoption from the absence of a search result.

**V3 implication:** make each standards record carry both international document identity and Indian adoption identity, including edition equivalence, modification status, amendments, reaffirmation, withdrawal/supersession and authoritative catalogue evidence. A newer IEC edition must not silently overwrite a different-edition IS adoption.

### B. CEA Safety and Electric Supply Amendment Regulations, 2026 — BESS safety

The Gazette of India Extraordinary, Part III, Section 4, No. 231, dated 30 March 2026 (notification dated 27 March 2026; Gazette ID CG-DL-E-31032026-271455) publishes the CEA (Measures relating to Safety and Electric Supply) Amendment Regulations, 2026. The commencement clause states **1 April 2027**. This is a notified amendment with a future commencement date, not a draft and not yet operative on the 2026-11-03 research snapshot.

The amendment inserts Chapter XA (regulations 122(A) onward) for additional BESS safety. The inspected Gazette text includes:
- chemistry-appropriate PCS design;
- two-independent-fault tolerance with safe operation or safe shutdown;
- fire/explosion protection at cell, module, rack, container and site levels;
- BMS monitoring/recording of voltage and temperature at cell/module/rack, thermal runaway and rack current;
- alarms and charge/discharge stop requirements tied to OEM operating limits;
- automatic PCS operation, synchronisation/disconnection, self-protection and diagnostics.

The complete chapter contains additional requirements; this summary is intentionally not exhaustive. The amendment's precise voltage-scope split and all regulation-level applicability conditions must be taken from the complete Gazette text, not inferred from the headline or BESS definition.

**V3 implication:** BESS cannot be represented merely as a battery object attached to a generic inverter. The engineering model and safety/Control/Protection workflows need explicit cell/module/rack/container/site hierarchy; chemistry; rated power and energy; SoC/SoH; BMS and PCS identities; temperature/voltage/current/thermal-runaway channels; alarm and trip/stop behavior; fire detection/suppression; ventilation; emergency stop; earthing; and safety evidence. Model regulatory requirements with an effective-from date and transition status so design checks can preview future requirements without falsely asserting they are currently mandatory.

### C. CEA Technical Standards for Construction Amendment Regulations, 2026 — renewable and BESS construction

The CEA's official Construction Standards listing identifies a 2026 Amendment Regulations PDF alongside the 2022 principal construction regulations and 2025 amendment. A Gazette transcript for notification CG-DL-E-27062026-273858 (Gazette issue dated 23 June 2026; published 27 June 2026) reports the CEA Technical Standards for Construction of Electrical Plants and Electric Lines Amendment Regulations, 2026, with commencement **1 April 2027**. It introduces a Chapter VI for construction of renewable energy power plants and BESS, split into solar, floating solar, onshore wind, offshore wind and BESS parts. It adds BESS equipment definitions and detailed construction requirements.

The official CEA listing corroborates that the 2026 amendment is notified/listed; the Gazette transcript source used for detailed section discovery is not the eGazette host itself. Before clause-level implementation, retrieve the original Gazette PDF from the official eGazette/CEA document link and verify every provision against it. Do not treat the separate September 2026 proposal for a second amendment (grid-forming inverter and co-located storage proposals) as enacted: CEA's public-comment archive lists that proposal as closed consultation material.

**V3 implication:** BESS and renewable-plant models require design/construction compliance profiles as well as operational safety profiles. Requirements must distinguish the notified 2027 amendment from draft proposals and should be activated according to commissioning date, technology and applicable plant category.

### D. Regulatory applicability matrix — initial classification

| Instrument class | Initial asset/use applicability | V3 treatment |
|---|---|---|
| CEA Safety and Electric Supply Regulations 2023 and amendments | Broad electrical-installation/electrical-plant/electric-line and persons engaged in generation, transmission, distribution, trading, supply or use of electricity, subject to the regulation's specific clauses and exemptions | Base Indian electrical safety rule set; capture installation, owner/operator, voltage, activity, effective date and clause scope |
| CEA Technical Standards for Construction of Electrical Plants and Electric Lines | Construction of covered electrical plants and electric lines; renewable/BESS additions commence 2027 | Asset/construction-stage profile, not blanket application to every industrial process asset |
| CERC Indian Electricity Grid Code and related CERC regulations | Entities, grid interfaces and transactions within CERC's statutory/inter-state jurisdiction and defined scope | Apply only when entity, connection and transaction fall within scope; do not use as universal plant-internal design law |
| State Electricity Regulatory Commission regulations, State Grid Code, distribution supply code and State Electrical Inspector requirements | State jurisdiction and connection/supply conditions; may apply to Rajasthan industrial installations depending on supply voltage, licensee and captive/open-access arrangements | Add state/jurisdiction profile; validate current Rajasthan instruments and local inspectorate requirements before issuing a project compliance assessment |
| BIS Indian Standards and adopted IEC standards | Depends on the regulation, contract, procurement specification, product certification scheme and standard's own scope | Store adoption/status separately from legal applicability; identify mandatory incorporation vs voluntary/contractual engineering reference |
| Draft regulations, consultation papers and proposed standards | No operative requirement solely by virtue of draft publication | Store as proposed/future watch items, never as current compliance failures |

### E. CERC and draft-status watch

The CERC current-regulations register identifies the Indian Electricity Grid Code Regulations, 2023 (Gazette No. 488, 11 July 2023) and the First Amendment Regulations, 2024 (Gazette No. 880, 29 October 2024). On the 2026-11-03 snapshot, CERC's website lists a Second Amendment draft with comment deadline extended to 02 November 2026 and a public hearing scheduled for 04 November 2026. It remains a draft on the snapshot date; the hearing is future-dated relative to this audit. V3's regulatory catalogue therefore needs explicit lifecycle states (draft consultation, notified, published, commenced, amended, superseded, repealed) and event history rather than a simple current-version field.

### F. Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F31 | P1 | BIS ETD 34 identifies published IS 16227 instrument-transformer family and their IEC edition/equivalence relationships | Add Indian adoption-aware standards catalogue and instrument-transformer requirements mapped to CT/VT/CVT/digital interface models |
| V3-ARCH-F32 | P1 | CEA 2026 Safety and Electric Supply amendment introduces BESS safety chapter effective 2027-04-01 | Add BESS safety domain model, monitored signals, interlocks, alarm/trip/stop workflows and future-effective compliance profile |
| V3-ARCH-F33 | P1 | CEA 2026 Construction amendment introduces renewable/BESS construction chapter effective 2027-04-01; September 2026 further amendment remains draft consultation | Separate notified construction requirements from proposed requirements and support effective-dated asset/commissioning applicability |
| V3-ARCH-F34 | P1 | CEA/CERC/BIS requirements have different jurisdiction, asset scope, legal status and effective dates | Create applicability engine using jurisdiction, entity role, asset category, voltage, activity, project dates and instrument lifecycle |
| V3-ARCH-F35 | P2 | BIS draft ETD 42 lists older IS/IEC 60255 adoption leads but is not itself proof of publication/current status; current editions are newer | Require catalogue-level verification and edition-equivalence review before protection standards are marked adopted or mandatory |

### Official source register — second batch

- BIS ETD 34 Instrument Transformers Program of Work (published IS list) — https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/pow_new/Pow/download_pow_pdf_dept_commtt/65/267/
- BIS Know Your Standard catalogue — https://www.bis.gov.in/know-your-standard/?lang=en
- BIS ETD 42 September 2023 draft document (discovery lead only; explicitly draft for comments) — https://www.services.bis.gov.in/tmp/WCETD32523628_21092023_1.pdf
- CEA Safety and Electric Supply Amendment Regulations, 2026, Gazette PDF — https://egazette.gov.in/WriteReadData/2026/271455.pdf
- CEA official Safety and Electric Supply regulations listing — https://cea.nic.in/regulations-subcategory/ad9da247-723a-4a60-9182-fc2753458916?lang=en
- CEA official Construction Standards listing — https://www.cea.nic.in/regulations-category/ffd27059-ea49-469f-a732-74da3cc6b31c?lang=en
- CEA 2026 Construction Amendment Gazette transcript discovery record (verify original Gazette PDF before clause use) — https://gazettetracker.com/g/CG-DL-E-27062026-273858
- CEA September 2026 draft second amendment consultation — https://cea.nic.in/notification/draft-central-electricity-authority-technical-standards-for-construction-of-electric-plants-and-electric-lines-2nd-amendment-regulations-2026-invitation-of-public-comments-till-04-10-2026/?lang=en
- CEA public-comment archive (closed drafts) — https://www.cea.nic.in/whats-new/public-comments-archive?lang=en
- CERC current regulations — https://cercind.gov.in/current_reg.html
- CERC draft regulations — https://cercind.gov.in/Draft_reg.html

**Verification limits:** BIS ETD 34 Program of Work and catalogue discovery were inspected; every IS detail was not independently opened in the Know Your Standard record. The ETD 42 protection adoption references are from a draft document and remain unconfirmed. The CEA Safety amendment was checked against its original eGazette PDF. The 2026 Construction amendment's existence and commencement were cross-checked against the CEA official listing and a Gazette transcript, but the original eGazette PDF was not retrieved in this pass; its detailed clauses remain provisional until verified. Rajasthan state-specific rules, licence/connection arrangements and Electrical Inspector requirements have not yet been audited. No compliance conclusion is made.


## 8H. BIS catalogue verification — Protection, automation, control and OT cybersecurity (2026-11-04)

**Research boundary:** This pass checked publicly indexed BIS Know Your Standard records, official BIS standards publications/compendia and BIS committee/draft documents. It establishes a confirmed subset, not a complete export of every relevant IS record. A search result or a BIS compendium entry is not a substitute for opening the individual current standard record and checking amendments, reaffirmation, withdrawal and supersession. Where an individual current record was not verified, the status is explicitly limited.

### A. Protection relays and protection equipment

**Confirmed current catalogue evidence in the inspected BIS search results:**
- **IS/IEC 60255 (Part 27):2013** — *Measuring Relays and Protection Equipment — Part 27: Product Safety Requirements*. BIS search result identifies the corresponding international document as **IEC 60255-27:2013** and shows “Reviewed In: 2025”. This is an individual part adoption, not adoption of all IEC 60255 parts.
- **IS/IEC 60255 (Part 22/Sec 1):2007** — *Measuring relays and protection equipment — electrical disturbance tests*, corresponding to **IEC 60255-22-1:2007**. The indexed BIS standard-details result lists this exact Indian designation and IEC edition.
- **IS/IEC 61810 (Part 7):2006** — *Electromechanical elementary relays — Part 7: Test and measurement procedures*, corresponding to IEC 61810-7:2006. This is an electromechanical relay test standard, not a substitute for numerical protection relay functional standards.
- **IS/IEC 61812-1:2023 (First Revision)** was found in an ETD 35 January 2025 document, but the document is explicitly **Draft for Comments Only** and states it is to be adopted following committee/division approval. It is not counted as a published Indian Standard in this audit.

**Not confirmed as currently published in this pass:**
- ETD 42's September 2023 draft lists proposed Indian counterparts for IEC 60255-121:2014, IEC 60255-127:2010, IEC 60255-151:2009 and IEC 60255-181:2019. Those remain draft-derived leads until each exact IS number is found in the current BIS catalogue.
- No current catalogue evidence was established here for a complete set of protection function standards covering distance, over/under-voltage, over/under-frequency, thermal overload, differential, directional, earth-fault, motor protection and synchro-check. Do not infer their absence from this limited indexed search.
- Do not map an ANSI/IEEE relay function to a specific Indian Standard solely from the function number. Functional application, performance, testing and product safety are distinct standard scopes.

**V3 implication:** Maintain a part-level protection standards matrix. Each relay function/equipment profile should link to the exact applicable published IS record (if any), corresponding IEC/IEEE source and edition, standard scope (common requirements, functional performance, EMC/disturbance, product safety, communication), adoption equivalence, amendments and review status. Keep “published IS”, “draft IS”, “IEC reference only” and “not yet verified” as separate states.

### B. Automation and programmable controllers

**Confirmed published Indian Standards from BIS official publication:**
- **IS 14254 (Part 1):2006** — *Programmable Controllers: Part 1 — General Information*, corresponding to **IEC 61131-1:2003**.
- **IS 14254 (Part 2):2021** — *Industrial-Process Measurement and Control — Programmable Controllers — Part 2: Equipment Requirements and Tests*, corresponding to **IEC 61131-2:2017**. BIS indexed catalogue result reports “Reviewed In: 2026”.
- The BIS 2023 “Science and Technology” standards publication lists both Part 1 and Part 2 under published programmable-controller standards.
- The same BIS publication lists **IS 17885 (Parts 1–4):2022**, adopting ISO 23247-1:2021 through ISO 23247-4:2021 for manufacturing digital-twin framework. This is useful for manufacturing digital-twin architecture but is not a PLC language or power-system automation protocol standard.

**Not confirmed:**
- **IEC 61131-3:2025** (programming languages) was not found as a published IS adoption in the inspected BIS catalogue evidence. IS 14254 Parts 1 and 2 do not establish adoption of Part 3. IEC 61131-3 must therefore remain an international reference unless a current BIS record is separately verified.
- BIS's 2023 publication lists OPC UA parts 1–10 and 100 under “Areas Identified for Standardization in Future”, not “Standards Published” in that document. Treat this as a historical standardization gap indicator only; it is not proof of the 2026 current status.
- This pass did not establish current published IS adoption of IEC 61850 (including SCL/IEC 61850-6, logical-node/data-model parts or communication service mappings). Keep IEC 61850 as an international reference pending an exact BIS catalogue record. Do not conflate the published instrument-transformer digital-interface adoption **IS 16227 (Part 9):2018 / IEC 61869-9:2016** with IEC 61850.

**V3 implication:** Represent PLC language support, controller hardware/environmental requirements, device interoperability, substation automation and engineering configuration as separate standards domains. A published IS for PLC equipment requirements does not certify the controller's IEC 61131-3 language implementation, IEC 61850 interoperability or a complete PLC runtime.

### C. OT cybersecurity and power-system communications security

**Confirmed BIS publication evidence:**
- The BIS official 2023 Science and Technology standards publication lists:
  - **IS/IEC 62443-1-1:2009** — terminology, concepts and models;
  - **IS/IEC 62443-2-4:2017** — security programme requirements for IACS service providers;
  - **IS/IEC 62443-3-3:2013** — system security requirements and security levels;
  - **IS/IEC 62443-4-1:2018** — secure product development lifecycle requirements;
  - **IS/IEC 62443-4-2:2019** — technical security requirements for IACS components.
- An official BIS ETD 18 synopsis for **IS/IEC 62443-3-3:2013** confirms its focus on IACS system security requirements, foundational requirements and capability security levels. This is direct evidence that the Indian document is not merely a generic IT security checklist.
- The BIS 2025 cybersecurity compendium identifies the **IS/IEC 62351 series** for power-system management and associated information exchange data/communications security, and the **IS/IEC 62443 series** for IACS/OT cybersecurity. However, the compendium's series-level summary does not identify every published part, edition, reaffirmation or amendment.

**Status caution:**
- For **IS/IEC 62351**, this pass confirms BIS recognition/publication of the series at a high level and an individual indexed reference to **IS/IEC/TS 62351 (Part 2):2008** (glossary). It does not establish the current catalogue status of every IEC 62351 part or the equivalence of each Indian edition to current IEC editions.
- The 2025 BIS compendium is a discovery/overview source. Before a part is used as a project compliance requirement, retrieve its individual Know Your Standard record and validate edition, status and amendments.
- Do not treat IEC 62443 certification or a target security level as automatically conferred by GridForge. V3 may support asset inventory, zones/conduits, risk assessment, requirement traceability and evidence management; conformance assessment remains a separate process.

**V3 implication:** Build an OT cybersecurity profile that distinguishes power-system protocol security (IEC 62351 family), industrial control-system security (IEC 62443 family), product development/security requirements, component capability, service-provider obligations and organizational ISMS. Model zones, conduits, trust boundaries, roles, secure engineering lifecycle, access control, audit trails, time synchronization and availability/safety constraints. Do not reduce OT security to generic IT controls.

### D. Alarm management and operator-interface standards

- The search did not establish a current published BIS adoption record for **IEC 62682** (alarm management) or **ISA-18.2** in this pass.
- Do not mark either as an Indian Standard on this evidence. Retain IEC 62682 / ISA-18.2 as international engineering references pending a specific BIS record.
- This is a significant distinction for V3: alarm lifecycle, rationalization, priority, shelving, suppression, flood analysis, operator response and audit history can be supported as engineering capabilities, but a product feature does not establish compliance with a standard.

### E. Consolidated adoption-status matrix

| Domain | Indian adoption evidence established in this pass | International reference / unresolved boundary | Catalogue status for V3 |
|---|---|---|---|
| Protection relay product safety | IS/IEC 60255 (Part 27):2013; IEC 60255-27:2013; BIS result says reviewed 2025 | Does not establish functional coverage of all IEC 60255 parts | Published IS evidence; verify current individual record before compliance use |
| Protection disturbance immunity | IS/IEC 60255 (Part 22/Sec 1):2007; IEC 60255-22-1:2007 | One disturbance-test part only | Published IS evidence; edition-specific |
| Electromechanical relay testing | IS/IEC 61810 (Part 7):2006; IEC 61810-7:2006 | Does not cover all numerical protection relay functions | Published IS evidence; scope-limited |
| Time relays | IS/IEC 61812-1:2023 appears in January 2025 ETD 35 draft | Draft for comments only in inspected source | Draft lead; not counted as published |
| PLC general information | IS 14254 (Part 1):2006; IEC 61131-1:2003 | Older edition; check current record/status | Published IS evidence |
| PLC equipment requirements/tests | IS 14254 (Part 2):2021; IEC 61131-2:2017; catalogue search reports review 2026 | Does not cover IEC 61131-3 programming languages | Published IS evidence; review metadata noted |
| PLC programming languages | No published IS adoption verified | IEC 61131-3:2025 | IEC reference only / adoption unverified |
| Substation automation / SCL | No current IS adoption verified | IEC 61850 family; IEC 61850-6 edition 2.2 (2024 consolidated text) | IEC reference only / adoption unverified |
| OT cybersecurity | IS/IEC 62443-1-1:2009, 2-4:2017, 3-3:2013, 4-1:2018, 4-2:2019 listed in BIS publication | Current IEC revisions may differ; part-level current catalogue check still required | Published IS evidence for listed parts; edition-specific |
| Power-system communication security | IS/IEC 62351 series identified in BIS compendium; IS/IEC/TS 62351 (Part 2):2008 appears in BIS indexed result | Every part/current edition not verified | Series-level evidence; part-level verification pending |
| Alarm management | No current IS adoption verified | IEC 62682 / ISA-18.2 | International reference only / adoption unverified |
| Manufacturing digital twin | IS 17885 (Parts 1–4):2022 / ISO 23247-1 to -4:2021 listed by BIS | Manufacturing scope; not power-system digital twin standard by itself | Published IS evidence; scope-limited |

### F. Refined findings

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-ARCH-F36 | P1 | BIS evidence confirms only selected IEC 60255 parts and older edition-specific protection relay standards; ETD 42 functional standards leads remain draft-derived | Implement part-level protection-standard catalogue; separate functional, common, EMC/disturbance and product-safety coverage; require exact current IS record before compliance claims |
| V3-ARCH-F37 | P1 | IS 14254 Parts 1 and 2 are published, but no IEC 61131-3:2025 IS adoption was established | Separate PLC equipment conformance from language/runtime support; record IEC 61131-3 as international reference until verified |
| V3-ARCH-F38 | P1 | No current BIS adoption record for IEC 61850/SCL was established in this pass; IS 16227 Part 9 is IEC 61869-9, not IEC 61850 | Keep IEC 61850 profile distinct from instrument-transformer digital interface; add SCL import/export/interoperability requirements as reference-driven, not falsely IS-certified |
| V3-ARCH-F39 | P1 | BIS publication lists selected IS/IEC 62443 parts and BIS compendium identifies IS/IEC 62351 series | Add OT cybersecurity and power-system communications security as distinct but integrated profiles with edition-aware evidence and zone/conduit traceability |
| V3-ARCH-F40 | P2 | No current BIS adoption of IEC 62682 / ISA-18.2 was established; OPC UA was historically listed as future standardization subject in BIS 2023 publication | Keep alarm management and OPC UA as international reference/watch items until exact current BIS records are verified |
| V3-ARCH-F41 | P1 | BIS catalogue records expose review/reaffirmation/amendment metadata; series-level compendia do not supply complete lifecycle detail | Standards registry must ingest individual Know Your Standard records and preserve source date, publication, amendment, reaffirmation, withdrawal/supersession and degree of equivalence |

### Official source register — BIS verification batch

- BIS Know Your Standard portal and record capabilities — https://www.bis.gov.in/know-your-standard/?lang=en
- BIS indexed standard details: IS/IEC 60255 (Part 27):2013 and IS/IEC 60255 (Part 22/Sec 1):2007 — https://standards.bis.gov.in/website/standard-details?encryptedId=eyJpdiI6ImpvbGo4cVFET2VSWTgwVnlBU3JkY1E9PSIsInZhbHVlIjoiQytmWjVqR3I5VXJZaTRwY2R0d0Fhdz09IiwibWFjIjoiYzg5NzdhMWE0MWQ5NzBiZDMyYmEzYzRjNjNmMzU0NGU3MDU3YWEzOWJhMDY4N2FkZTUwOWFhNjcyZGRjNTAyZCIsInRhZyI6IiJ9
- BIS indexed standard details: IS/IEC 60255 (Part 27):2013 and related listed standards — https://standards.bis.gov.in/website/standard-details?encryptedId=eyJpdiI6InI1Wkc0Sk1WZWVIL0Fzc3oraTNweXc9PSIsInZhbHVlIjoiWlU3RmlPTEdjUzhlUGx3T0E2WlVVUT09IiwibWFjIjoiNTUzNDg1NjhhODcxZjk2OTE3N2ZlMTI3MzQyNDIxNmEyZjFjYTg2ODUwMTIxNTc0ODdiMjFmYzM1ZTNhMWFkZiIsInRhZyI6IiJ9
- BIS official “Science and Technology” standards publication (IS 14254 Parts 1/2; IS 17885 Parts 1–4; IS/IEC 62443 listed parts) — https://www.bis.gov.in/wp-content/uploads/2023/11/Book-21-Science-and-Technology.pmd_.pdf
- BIS ETD 18 synopsis for IS/IEC 62443-3-3:2013 — https://www.services.bis.gov.in/tmp/SRIE62443_3_3.pdf
- BIS cybersecurity compendium (IS/IEC 62351 and 62443 series overview) — https://www.services.bis.gov.in/tmp/compendium_2025-06-09-10-54-04.pdf
- BIS ETD 35 January 2025 draft IS/IEC 61812-1:2023 (draft for comments only) — https://services.bis.gov.in/tmp/WCETD26826305_20012025_1.pdf
- BIS ETD 42 September 2023 draft for comments (older IEC 60255 functional standard leads) — https://www.services.bis.gov.in/tmp/WCETD32523628_21092023_1.pdf
- BIS current catalogue landing page — https://standards.bis.gov.in/

**Verification limits:** The BIS indexed results and official publication sources were inspected. Individual current standard records were not all opened; exact amendment/reaffirmation/withdrawal status for every listed part remains to be checked before any compliance determination. BIS's 2023 publication and 2025 compendium are official discovery evidence but are not a live, exhaustive catalogue export. No current IS adoption was established for IEC 61850, IEC 61131-3:2025 or IEC 62682 in this pass; this is “not verified”, not proof of non-adoption. No licensed normative text was reviewed and no clause-level compliance assessment was performed. No V2 source, tests, CI or implementation were changed.


## 8I. GridForge UI/UX architecture and engineering-workflow research — first detailed pass (2026-11-04)

**Objective:** Establish a source-backed UI research baseline for GridForge V3. This is not authorization to redesign or modify V2. The audit distinguishes documented architecture, source-observed implementation, runtime/visual behavior not yet verified, and proposed V3 usability requirements.

**Scope inspected:** ui/README.md, ui/main_window.py, ui/bootstrap/presentation_bootstrap.py, ui/workspace, ui/editors/common, SLD/Control/Protection editor and workspace modules, canvas/navigation modules, tool shelf/icon adapter, panels, style tokens/theme/stylesheet/style manager, and the September 2026 UI architecture/audit documents.

### A. Human-centred design and interaction standards baseline

- **ISO 9241-210:2019** — human-centred design throughout the lifecycle of interactive systems. ISO records the 2019 edition as current after review/confirmation in 2025. Use it to structure context-of-use research, user requirements, iterative design solutions and evaluation; it is not a ready-made engineering CAD UI specification.
- **ISO 9241-110:2020** — interaction principles. ISO records the edition as current after review/confirmation in 2025. Apply suitability for the task, self-descriptiveness, conformity with user expectations, suitability for learning, controllability, error tolerance and suitability for individualization.
- **ISO 9241-115:2024** — conceptual design, user-system interaction design, UI design and navigation design. It is relevant to GridForge's multi-editor workspace and cross-discipline navigation.
- **ISO 25065:2019** — Common Industry Format for usability user-requirements specification. Use it to turn vague preferences into traceable user/task/interaction requirements.
- **ISA-101.01-2015 and ISA-TR101.01-2022 / ISA-TR101.02-2019** — process-automation HMI lifecycle, HMI philosophy, usability and performance. Relevant to Control-room/plant-operation views, alarm/status presentation and operational modes, but not indiscriminately to every engineering design editor.
- **ISA-18.2 / ISA-18 series** — alarm lifecycle, prioritization, rationalization and performance monitoring. Relevant to alarm-management surfaces, not a substitute for engineering validation/diagnostic UX.
- **WCAG 2.2** — accessibility reference for perceivable, operable, understandable and robust interaction. Its web-content scope requires careful translation for native Qt desktop controls; use equivalent accessibility outcomes and Qt platform support rather than claim automatic WCAG conformance.
- **NIST human-centred design guidance** summarizes the ISO HCD cycle and interaction principles and supports task/context research and iterative evaluation rather than visual preference alone.

### B. Engineering-software comparative research

- **KiCad 10 documentation** provides useful EDA conventions: project-centred work, multiple integrated editors, customizable toolbars, selection windows, explicit active-tool indication and keyboard-driven interaction. Its schematic and PCB editing semantics are analogies, not direct electrical power-system requirements.
- **Altium Designer documentation (updated 2026-11-02)** describes a design-space/panel/menu/active-bar structure and a consistent placement flow: select placement command, preview/place, edit properties, terminate placement, then inspect/edit selected objects. This provides a benchmark for predictable tool state and contextual property editing.
- **Horizon EDA** describes a unified interactive manipulator with explicit tools and a property editor for low-complexity changes. This supports evaluating whether GridForge's placement, connection, selection and property-editing flows have a coherent interaction vocabulary.
- CAD usability research highlights consistency, visibility, feedback, recoverability, workspace maximization, direct manipulation, familiarity, customizability, assistance, minimalist design and context recognition. Treat these as candidate inspection heuristics, not normative requirements.

**Design principle:** borrow proven interaction conventions, not another product's architecture or domain semantics. GridForge's domain workflows (SLD, protection coordination, Control logic, study setup) must drive interaction design.

### C. Repository architecture and implementation observations

**C1. Main shell and workspace composition**
- ui/main_window.py deliberately remains a mechanical Qt host. It does not own workspace orchestration or Application/Core state.
- ui/workspace/README.md defines WorkspaceManager → WorkspaceDefinition/Layout → Area → Editor → Region → EditorContext → discipline tools.
- ui/editors/common/editor_host.py realizes editor widgets through a shared host; ui/workspace/workspace_realizer.py realizes the logical workspace.
- ui/workspace/workspace_defaults.py defines four workspaces: SLD, Control, Protection and Study.
- The SLD default region definition hides Explorer, Inspector and Diagnostics initially; ui/editors/sld/sld_editor.py provides header toggles for Explorer, Inspector and Messages and a Restore control.
- SLD uses a compact 44/52 px tool-shelf region. The generic editor region definition specifies a wider 180/250 px tool shelf. This may be intentional discipline-specific density, but workspace sizing and panel discoverability need usability evaluation.
- The SLD workspace is not simply missing panels; the question is whether hidden-by-default regions are discoverable and whether new-project first-use gives enough context.

**C2. Editor consistency and canvas interaction**
- SLD editor is composed from explicit regions and uses the canonical canvas surface/GraphicsView path.
- ui/canvas/graphics_view.py is a thin injected viewport; it uses shared NavigationController and InteractionManager contracts.
- ui/control/control_workspace.py contains a dedicated _LadderView(QGraphicsView) and its own mouse event path; it calls fitInView on show and uses ScrollHandDrag.
- ui/protection/protection_workspace.py contains a dedicated ProtectionGraphicsSurface(QGraphicsView) and its own scene/refresh/rendering logic; fit-to-content is implemented in that discipline surface.
- Control and Protection also have ControlEditor and ProtectionEditor region-based compositions. The source indicates shared workspace vocabulary but discipline-specific canvas realizations and event paths.
- This does not prove a defect: Control ladder semantics and Protection coordination diagrams have different needs. It creates a V3 requirement to define shared interaction conventions (selection, focus, pan/zoom, fit, active tool, Escape/cancel, snapping, status, undo/redo, keyboard shortcuts) while permitting discipline-specific tools and rendering.
- Runtime behavior, current application composition and whether any historical surface remains active were not visually verified in this pass. Trace the actual composition path before proposing consolidation.

**C3. Tool shelf and palette**
- ui/editors/common/tool_shelf.py uses ToolDefinition, optional action routing, active-tool provider, contextual editor filtering, keyboard shortcut/description tooltips and a fallback text glyph when icon resolution fails.
- ui/editors/common/tool_icon_adapter.py resolves explicit icon metadata and logs fallback glyphs instead of silently choosing unrelated artwork.
- These are positive foundations for discoverability and truthful affordances.
- Icon fallback text derived from the first two characters of a tool ID is a technical fallback, not a complete visual language. Tool icons, labels, grouping, selected/disabled states, keyboard hints and accessible names need an explicit reviewed catalogue and consistent treatment across all editors.
- Tool activation must visibly identify the active mode and how to exit/cancel it. A disabled or missing action must explain why it is unavailable rather than only appear inactive.

**C4. Properties, configuration and diagnostics**
- ui/panels/properties_panel.py is a logical, non-Qt panel lifecycle/target abstraction; it is not itself the full widget implementation.
- ui/panels/engineering_parameter_editor.py converts projected parameter metadata and user changes into typed engineering configuration intent for Application execution. This is a strong architectural foundation.
- ui/control/control_inspector.py provides Control-specific inspection/configuration behavior.
- ui/panels/messages_panel.py currently renders validation messages and event messages into one QListWidget; it stores the two categories separately but displays them together without a richer structured diagnostic model in this widget.
- ui/panels/study_cases_panel.py places study-case creation fields for Power Flow, Short Circuit and Transient Stability in one panel form. Evaluate progressive disclosure and context-sensitive forms so users see only fields relevant to the selected study type.
- V3 should define a consistent contextual inspector contract: identity/summary, editable properties, read-only calculated values, units/bases, validation state, provenance, grouped sections, inline errors, Apply/Reset/Undo semantics, and links to related objects. Discipline-specific property editors can extend the contract.
- Diagnostics should distinguish validation errors/warnings/information, application events, study execution status, data-quality warnings and Protection/Control operational alarms. Each actionable diagnostic should identify source, severity, timestamp/context, affected object, reason, recommended next action and navigation target. Do not conflate an engineering validation finding with an operational alarm or generic event.

**C5. Visual theme and accessibility**
- ui/styling/style_tokens.py defines semantic dark-window/panel tokens, a white canvas, semantic engineering colors, selection and state colors, and palette-specific icon strokes.
- ui/styling/theme.py defines DEFAULT_THEME as “GridForge Engineering Dark”.
- ui/styling/style_manager.py supports loading/rendering/applying QSS and a theme object; its own design notes describe light/dark variants, high contrast, user themes, density and persisted preferences as future capabilities.
- Source inspection establishes a token/theme foundation, not a verified user-facing theme selector, light theme, high-contrast mode or accessibility conformance.
- V3 should test symbol/line/state contrast on both canvas and dark panels; never use color alone for selected/valid/invalid/alarm states. Provide shape, line style, text/icon and explicit status labels. Include scalable typography, keyboard focus visibility, accessible names, tooltips, keyboard alternatives and user-adjustable density.
- Engineering canvas color must preserve electrical discipline conventions and status semantics. Do not optimize only for a fashionable dark palette.

### D. Initial UX risk and opportunity register

| Candidate finding | Priority | Source evidence / risk | V3 research recommendation |
|---|---|---|---|
| V3-UI-F01 | P1 | Editor shells share Region vocabulary but Control/Protection use separate canvas implementations and event paths from SLD | Define cross-editor interaction contract and compare active composition paths before any unification |
| V3-UI-F02 | P1 | SLD Explorer, Inspector and Diagnostics are hidden by default; discoverability for first-time users not established | Research first-project onboarding, default workspace composition, panel toggles, restore behavior and saved layout preferences |
| V3-UI-F03 | P1 | Canvas navigation/fit/selection behavior differs across SLD, Control and Protection implementations | Define common navigation/selection/active-tool/cancel/status semantics; permit domain-specific gesture extensions |
| V3-UI-F04 | P1 | Logical PropertiesPanel, generic EngineeringParameterEditor and discipline-specific inspectors form multiple concepts | Specify a unified contextual inspection/editing model with typed Application commands, units, provenance and validation |
| V3-UI-F05 | P1 | Messages panel displays validation and events in one list; operational alarms/study status are separate semantic concerns | Design structured diagnostics centre with categories, severity, filters, object navigation and recovery actions |
| V3-UI-F06 | P1 | Dark-only default theme is evident; high-contrast, light theme, density and persisted appearance remain future design notes | Establish accessible visual tokens and appearance profiles; evaluate contrast, color independence, scaling and focus |
| V3-UI-F07 | P1 | Tool shelf has fallback glyph and action routing, but no evidence yet of full icon/label/shortcut/accessibility consistency across every discipline | Create audited tool catalogue and tool-state language; active mode, disabled reason, keyboard hints, accessible labels |
| V3-UI-F08 | P1 | Study Cases panel exposes fields for several study types in one form | Evaluate progressive disclosure, study-specific configuration steps, contextual validation and result-to-source navigation |
| V3-UI-F09 | P1 | No user/task requirements or usability evaluation evidence was identified in the inspected UI architecture docs | Establish role-based personas, context of use, task scenarios, usability requirements and evaluation plan using ISO 9241-210/25065 |
| V3-UI-F10 | P2 | UI architecture and visual style documents define component boundaries but do not establish complete end-to-end task usability | Create traceable workflow maps and scenario acceptance criteria for new project, SLD build/edit, Control logic, Protection configuration, studies, save/reopen and diagnostics recovery |

These are research findings/candidate risks, not confirmed runtime defects. Priorities express the importance of investigating the risk, not severity of a reproduced failure.

### E. V3 UI research method and required evidence

1. **User/task model:** distinguish electrical design engineer, protection engineer, Control/automation engineer, study/analysis engineer, commissioning/operations engineer, reviewer and administrator. A person may hold multiple roles; do not assume one universal persona.
2. **Context of use:** desktop workstation, display resolution/scaling, keyboard/mouse, project size, diagram density, session duration, engineering responsibility, offline/poor-network constraints, and novice/expert experience.
3. **Critical workflows:** create/open project; build SLD; place/edit equipment; connect terminals; inspect and validate; configure CT/PT/relay; map Protection-to-Control actions; build ladder logic; configure/run studies; interpret results; resolve diagnostics; save/reopen/recover.
4. **Scenario-based evaluation:** document goal, preconditions, task steps, expected result, user-visible feedback, failure/recovery path and evidence. Evaluate first-use discoverability and expert efficiency separately.
5. **Quantitative measures:** task completion rate, critical error rate, time-on-task, unnecessary actions, recovery time, navigation depth, tool-mode mistakes, validation rework, and user-rated workload/satisfaction. Set thresholds only after baseline measurement.
6. **Qualitative methods:** contextual inquiry, task observation, think-aloud walkthroughs, expert review, cognitive walkthrough, accessibility inspection and structured user feedback.
7. **Visual/runtime evidence:** screenshots and recordings of the current running application at defined resolution/DPI; inspect light/dark and scaling states; do not infer visual quality from QSS or source alone.
8. **Traceability:** map each UX requirement to workflow, UI surface, interaction contract, evidence, severity, proposed change and verification scenario.
9. **Change control:** V3 recommendations remain research-only until reviewed/approved. No V2 architecture change is implied.

### F. First-pass audit boundaries and next research sequence

**Inspected:** selected workspace/editor/canvas/panel/theme/tool source and architecture docs in the authoritative repository branch. The source tree contains 339 paths under ui/ and related UI documentation at this snapshot.

**Not yet inspected:** all menu/action definitions and actual menu completeness; full MainWindow/application composition; every panel and editor; keyboard shortcut registry and conflicts; accessibility metadata; undo/redo and cancel semantics across tools; context menus; dialogs/wizards; project open/save/close UX; error and exception presentation; study result visualization; large-diagram navigation/performance; persisted workspace layouts; plugin-contributed UI; live application screenshots; user observation or usability metrics.

**Next sequence:**
- 8I-2: trace actual application startup/composition and shell menus/toolbars/actions, identify what users can really access (not merely what classes exist).
- 8I-3: deep SLD workflow audit — new project, palette discovery, preview, placement, connection, selection, property editing, validation, commit, undo/redo, save/reopen.
- 8I-4: Control canvas/ladder usability and Protection workspace interaction audit; compare common interaction contract without forcing identical domain behavior.
- 8I-5: inspector, diagnostics, study configuration/results, navigation, shortcuts, keyboard/accessibility, themes/density and layout persistence.
- 8I-6: consolidate evidence into a V3 UI requirements and design proposal, prioritized by workflow impact and engineering risk.

### G. Official standards and comparative sources

- ISO 9241-210:2019 Human-centred design for interactive systems (confirmed current 2025) — https://www.iso.org/standard/77520.html
- ISO 9241-110:2020 Interaction principles (confirmed current 2025) — https://www.iso.org/standard/75258.html
- ISO 9241-115:2024 Conceptual design, interaction, UI and navigation design — https://committee.iso.org/cms/live/live/en/sites/isoorg/contents/data/standard/08/07/80773.html
- ISO 25065:2019 Usability user requirements specification — https://www.iso.org/standard/72189.html
- ISA-101 series HMI design and lifecycle — https://www.isa.org/standards-and-publications/isa-standards/isa-101-standards
- ISA-18 series alarm management — https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards
- W3C WCAG 2.2 — https://www.w3.org/TR/WCAG22/
- NIST Human-Centred Design overview — https://www.nist.gov/itl/iad/human-centered-technologies/human-factors-human-centered-design
- KiCad 10 user documentation — https://docs.kicad.org/10.0/en/introduction/introduction.html
- Altium Designer design environment documentation (updated 2026-11-02) — https://www.altium.com/documentation/altium-designer/design-environment
- Horizon EDA theory of operation — https://docs.horizon-eda.org/en/v2.5.0/theory-of-operation.html
- ISA TR101.02 HMI Usability and Performance — https://webstore.ansi.org/standards/isa/isatr101022019

**Research limits:** ISO/ISA standards are referenced by scope and public abstracts/official descriptions; normative licensed clauses were not reviewed. Comparative vendor manuals are interaction examples, not standards. Repository inspection was source-level and selective. No running GridForge UI was launched, no screenshot/recording or user test was collected, and no runtime defect is declared reproduced. No tests, CI, V2 source changes or implementation were performed.


## 8I-2. Application startup, main shell, menus, toolbars and workspace navigation audit (2026-11-04)

**Scope:** Trace the actual source composition path from main.py through MainWindow, ShellPlugin, MenuPlugin, ToolbarPlugin, StatusPlugin, WorkspaceManager/Controller/Realizer, action catalogue/router and workspace definitions. This is source tracing, not a live visual audit.

### A. Actual startup and visible shell

- main.py is the executable composition root. It creates QApplication and branding/splash, Core/Application facade and Network, engineering plugin host, SLD projection/read synchronization, WorkspaceManager and PresentationBootstrap, SLD/Control/Protection/Study tool runtimes, canvas surfaces, ControlSurfaceHost, UI PluginManager, MainWindow, action router, project lifecycle adapter, editor context factory, panel composition, projections and shutdown lifecycle.
- The inspected main.py contains approximately 1,419 lines. It performs substantial orchestration: creates dependencies, registers action handlers, evaluates action availability, manages project transitions, handles document lifecycle, synchronizes projections, binds status state, and starts/shuts down the UI.
- This is a composition root by design, not evidence that MainWindow itself violates its mechanical-host boundary. However, the size and mixed orchestration responsibilities make startup flow, action behavior and UI evolution difficult to audit as one unit.
- MainWindow remains a QMainWindow host for central root widget and toolbar/dock mechanics. ShellPlugin composes the application header, canvas surface and status widget into the central root. ToolbarPlugin attaches its QToolBar to QMainWindow's top toolbar area; ShellPlugin explicitly does not insert that toolbar into its central root layout. These are separate QMainWindow and central-shell composition paths.
- ShellPlugin's header currently presents GridForge branding, project name and a text engineering context summary (discipline, study and system state). The inspected header does not itself provide workspace navigation.
- MenuPlugin builds eight menus from declarative MenuSpec values: File, Edit, View, SLD, Study, Reports, Window and Help. It routes each menu action through UIActionRouter, obtains description/status-tip and enabled state from canonical action metadata/router, and refreshes enabled states.
- ToolbarPlugin composes a top-level toolbar and routes actions through the same UIActionRouter. Its default action set is SLD-oriented editing/navigation plus Equipment, Study Cases, SLD, Topology, Map, Reports, Control and Protection entry actions. It has no explicit Study workspace button; Study Cases/Reports are the available study entry affordances.
- StatusPlugin projects authoritative state into status fields and exposes transient status messages. main.py binds it to Controller, Application, selection, GraphicsView, WorkspaceController and project adapter.
- UI plugin lifecycle is explicit and dependency ordered; ShellPlugin composes existing widgets rather than discovering/constructing them. This is a positive separation of composition responsibilities.

### B. Workspace navigation and conceptual model

- Canonical WorkspaceManager definitions are SLD, Control, Protection and Study. The default workspace is SLD. Each definition has one main Area and an Editor composed of Regions.
- WorkspaceController activates a prepared workspace by asking WorkspaceRealizer to realize the layout, then commits the logical state. The Realizer restores the previous realized layout if a transition fails. This provides a deliberate transition boundary.
- Workspace switches in main.py update the active engineering context and clear the shared SLD selection so hidden SLD selection does not leak into another editor. This is a positive context-safety behavior.
- Topology and Map are explicitly described in main.py as compatibility surfaces outside WorkspaceController; _activate_surface activates them through ControlSurfaceHost and updates context separately. The Window menu places these alongside SLD, Control, Protection and Study, even though they are not canonical WorkspaceManager workspaces.
- EngineeringWorkspaceTabs defines a second tab-oriented surface host for SLD, Topology, Map, Reports, Control and Protection. No usage was identified in the inspected main.py composition path. Do not assume this class is part of the visible shell without tracing another composition path.
- The visible workspace navigation is therefore distributed: menu Window, global toolbar actions, discipline editor surfaces, and separate Topology/Map compatibility surfaces. This may be functionally accessible but does not present one simple conceptual model of workspace versus secondary view.
- Study is reachable through Window → Study and toolbar/menu Study Cases or Reports actions; the toolbar does not offer a direct Study workspace control. Reports and Study Cases are separate labels but their action handlers activate the Study workspace. The Study workspace definition declares central_surface="reports". This naming needs a user-task model: opening study setup, reviewing completed reports and entering the Study editor are related but not identical intentions.

### C. Menu/action behavior and discoverability risks

- MenuPlugin uses declarative menu specifications and requires every menu action ID to exist in UIActionRouter before construction. Action descriptions are supplied as tooltips/status tips; enabled state is projected from the canonical router.
- The View menu labels Explorer, Inspector, Messages and Tool Settings generically. Their handlers call _toggle_sld_region, which activates the SLD workspace before toggling the corresponding SLD Region. In _action_enabled, these four actions (and Maximize Editor) are enabled based on project-active state, without checking that the active discipline is SLD. Consequently, when a user is in Control, Protection or Study, these View actions can remain enabled and selecting one transitions the user to SLD. This is a source-confirmed interaction surprise risk, not a reproduced runtime defect.
- The same menu labels do not disclose that they are SLD-specific. The action catalogue descriptions identify SLD Explorer/Inspector/validation, but the visible menu labels remain generic. V3 should either make the context explicit, adapt the menu to the active workspace, or provide discipline-correct equivalent panels.
- View → Equipment Browser and the toolbar Equipment action call a helper that activates SLD and toggles the hidden Explorer Region. The source documents Explorer as hidden in the default SLD layout. This is a valid discoverability path, but the user is taken to SLD rather than opening a contextual equipment browser inside the current discipline.
- Fit/zoom/pan actions are aliases to SLD canvas actions and are gated as SLD-only. This is more explicit in the Fit SLD View menu label and action availability than the generic panel toggles.
- File operations include New/Open/Save/Save As/Close/Exit. Open and Save As use standard file dialogs; project close and application close use unsaved-change decision handling. This is a positive lifecycle affordance. The startup composition also creates an initial project named GridForge Project; no separate landing/start page or recent-project chooser was identified in the inspected startup/menu paths.
- Edit menu and toolbar provide Undo/Redo, Delete, Select All, Copy/Paste/Cut. The code explicitly prevents multi-object Cut until deletion supports an atomic Application batch, and reports cancellation through Messages. This is a good example of safety over misleading affordance, but the disabled/unsupported state and reason should be visible before the user attempts the action.
- The action router supports canonical definitions, aliases, dynamic enabled-state provider, error reporting and dispatch. Menu and toolbar QAction enabled states are refreshed on engineering-context and Controller state changes. This is a strong single-action-authority foundation.
- ToolShortcutRegistry defines semantic actions and contexts (global, SLD, Control, Protection, Study, canvas, inspector and tool shelf), but the inspected startup composition does not show it being installed as the single runtime shortcut dispatcher. Menu QAction shortcuts are specified separately in MenuSpec, while action metadata also carries shortcut strings. Full keyboard shortcut ownership, conflicts, context precedence and runtime coverage remain unverified; do not claim a duplicate-shortcut defect from source samples alone.

### D. Status and feedback

- The shell header reports project and engineering context; StatusPlugin reports authoritative controller/project/viewport state. This can give users both high-level and immediate context.
- Routed action failures are appended to the persistent Messages panel with action ID, exception/error code, message, details and cause where available. Commit Draft errors use critical modal dialogs; study-case errors also use critical dialogs. Different error paths therefore use both persistent and modal feedback.
- V3 should define a consistent feedback policy: inline validation for editable fields; non-modal diagnostic entries for recoverable engineering/action failures; modal confirmation only for destructive/irreversible or project-transition decisions; persistent operation state for long-running studies; and explicit recovery/navigation actions. Avoid duplicating the same failure in a modal and message feed.
- Status should separate project/document dirty state, active workspace/editor, active tool, selection count, cursor coordinates/zoom, snap/grid state, validation severity, simulation/study run state and background task progress. The current StatusPlugin is bound to authoritative state, but the exact field catalogue and usability at runtime require further inspection.

### E. Findings added

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-UI-F11 | P1 | main.py composition root is ~1,419 lines and combines dependency composition, action handlers, enabled-state rules, project lifecycle, projection synchronization and startup/shutdown | Decompose composition into named, declarative presentation-composition modules while retaining one top-level composition root and single shared service/manager/registry instances |
| V3-UI-F12 | P1 | View panel toggles are enabled on project presence but their handlers force SLD activation; labels are generic despite SLD-only behavior | Make action availability and labels discipline-aware; do not unexpectedly switch editor when toggling a panel; define equivalent per-workspace panels or explicit scope |
| V3-UI-F13 | P1 | Window menu mixes canonical SLD/Control/Protection/Study workspaces with Topology/Map compatibility surfaces outside WorkspaceController | Define a clear navigation taxonomy: workspaces, documents, secondary views and tool windows; keep menu grouping and action semantics aligned |
| V3-UI-F14 | P1 | Study Cases and Reports both route to Study workspace; Study is absent as an explicit top-level toolbar workspace entry | Separate study setup, run monitoring and result/report review navigation; make Study workspace entry explicit and consistent across menu/toolbar |
| V3-UI-F15 | P2 | Startup opens a default project directly; no landing/recent-project workflow identified in inspected paths | Research start page with recent projects, new/open actions, recovery and sample/tutorial projects; preserve direct SLD-first entry for fast engineering sessions |
| V3-UI-F16 | P1 | Shortcut semantics exist in ToolShortcutRegistry, action metadata and menu specifications, but one runtime shortcut-dispatch/ownership contract was not established | Audit all active QAction/QShortcut/keymap registrations; define one canonical shortcut catalogue with editor scope, precedence, conflict resolution, remapping and discoverability |
| V3-UI-F17 | P2 | Toolbar is a fixed top-level QToolBar; shell central layout separately hosts header/canvas/status; toolbar defaults contain a large SLD-centric command set | Evaluate toolbar density, contextual action visibility, workspace-specific command groups, customization and compact/expanded modes with real screen/DPI scenarios |
| V3-UI-F18 | P2 | Multi-object Cut is safely blocked but cancellation is surfaced after invocation through Messages | Reflect unavailable operations and their reason before activation; provide consistent disabled-state explanation and recovery guidance |
| V3-UI-F19 | P1 | Action errors, commit failures, study failures and validation messages use different modal/persistent channels | Specify one diagnostic/feedback taxonomy and modality policy with deduplication, source navigation and recovery actions |
| V3-UI-F20 | P2 | No start-page/recent-project flow or explicit user layout persistence was established from this targeted startup/workspace trace | Audit project recents, crash recovery, workspace layout preferences and settings persistence; do not assume absence until full settings path inspected |

All findings above are source-backed usability risks or investigation items. They are not declarations that runtime UI behavior has been reproduced as faulty.

### F. Qt desktop interaction references

- Qt's QMainWindow model explicitly separates menu bar, toolbars, dock widgets, central widget and status bar; QActions can be shared across menus and toolbars so the same command behaves consistently regardless of entry surface. GridForge already uses an action router across menu and toolbar; V3 should preserve one command identity and improve context-specific presentation.
- Qt's main-window framework supports docked/floating helper panels and toolbar/dock layout persistence through saveState/restoreState. This is a platform capability, not proof that GridForge currently persists user layouts. Qt warns restoreState should only consume data produced by the same/compatible application version, not arbitrary untrusted data.
- Qt accessibility guidance emphasizes scalable UI, configurable fonts/font sizes and keyboard navigation; these should be included in the native desktop evaluation plan.

### G. Next research sequence

1. 8I-3: deep SLD engineer workflow from project creation to equipment discovery, preview, placement, connection, selection, contextual properties, validation, commit, undo/redo, save/reopen and recovery.
2. 8I-4: Control canvas/ladder and Protection workspace workflow, with a shared interaction contract but discipline-specific semantics.
3. 8I-5: audit actual shortcut dispatch, menu/action availability, status field catalogue, settings persistence, dialogs, error recovery and accessibility.
4. 8I-6: consolidate UI requirements and prioritized V3 proposal.

### H. Sources and verification limits

- Qt 6.11 Application Main Window — https://doc.qt.io/QT-6/mainwindow.html
- Qt 6.12 QMainWindow API, dock/toolbars and saveState/restoreState — https://doc.qt.io/qt-6/qmainwindow.html
- Qt 6.12 Accessibility — https://doc.qt.io/qt-6/accessible.html
- Qt Menus example — https://doc.qt.io/QT-6/qtwidgets-mainwindows-menus-example.html

**Verification limits:** The authoritative research branch source was inspected selectively: main.py, MainWindow, shell/menu/toolbar/status plugins, action catalogue/definition/router, workspace definitions/controller/manager/realizer, keymap registry and engineering workspace tabs. The current running application was not launched. Menus, toolbar, enabled states, keyboard navigation, focus, screen scaling and actual visible layout were not observed on screen. The action/shortcut audit is incomplete; no claim of runtime shortcut conflict is made. No settings persistence exhaustive search was completed. No tests, CI, V2 source edits or implementation were performed.


## 8I-3. SLD engineer workflow: authoring, configuration, wiring, validation, commit and recovery (2026-11-04)

**Scope:** Source-trace the SLD workflow through SLDEditor, ModelPlacementTool, WireTool, DraftNetwork, DraftSLDProjection, draft presentation realization, EngineeringParameterEditor, commit handler, project persistence and command history. This is a targeted source audit, not a running-application usability test.

### A. Workflow model established by source

- SLDEditor composes document tabs, a compact tool shelf, tool settings, canvas, Explorer, Inspector, Messages and status. Its constructor deliberately hides Explorer, Inspector, Messages/Diagnostics and Tool Settings initially. The region controls can reveal these panels; contextual selection can reveal Inspector unless the user has overridden visibility. The default therefore prioritizes canvas area, but important engineering context is not immediately visible to a first-time engineer.
- ModelPlacementTool is a shared position-first interaction. On initial press it obtains a grid/object snap, stores a placement coordinate in the transient CreationDraft and shows a SymbolPreviewItem. On release it calls place_creation_draft(), which resolves the trusted Application creation contract and submits AddDraftEquipmentCommand. The placement transition is therefore automatic on mouse release; it is not a separate explicit “confirm placement” click.
- The placement tool intentionally permits incomplete engineering parameters at draft placement. Its source comment says engineering validation is authoritative at later commit. This is a sound separation of visual authoring from complete equipment configuration.
- After AddDraftEquipmentCommand succeeds, the tool selects the draft identity, ends the transient CreationContext interaction, clears the preview and reports that the equipment is a draft and that Commit Network is the later boundary. This feedback is useful, but the source alone does not establish whether the visible canvas gives the engineer a persistent and unmistakable draft/uncommitted visual state.
- DraftNetwork is Application-owned and stores DraftEquipment, DraftConnection, presentation coordinates, engineering values, endpoint identities, validation state and trusted creation-contract metadata. DraftSLDProjection reads the Application draft read model and converts draft nodes/connections to immutable canvas projection DTOs. DraftPresentationFactory realizes those draft nodes as SymbolPreviewItem objects using canonical equipment and symbol registries. This is a deliberate projection boundary and avoids constructing Core equipment just to display a draft.
- Draft and committed canvas state have an explicit composite projection contract (committed SLD snapshot plus DraftSLDCanvasSnapshot). The source establishes the data path and realization factory; whether the active renderer refreshes both consistently under every event, selection and workspace transition was not established in this targeted pass.
- WireTool is endpoint-first: first valid object endpoint starts a connection preview; a second valid object endpoint submits the connection command. Grid/empty cursor positions are not promoted to electrical endpoints. If command execution fails, the source endpoint remains selected in the preview and an actionable reason is retained. Draft endpoints create CreateDraftConnectionCommand; committed Core endpoints use the Simple Wire command path.
- DraftConnection stores canonical source and target DraftEndpointReference identities, connection kind, route and validation state. DraftNetwork candidate validation rejects unsupported connection kinds, self-connections, invalid endpoints and incompatible terminal pairs before the draft connection is added. This is useful immediate feedback for impossible endpoint selections, but it means some electrical compatibility checks happen during wire authoring rather than exclusively at the final commit boundary.
- EngineeringParameterEditor accepts only parameters projected as editable and non-derived, enforces paired-field requirements, coerces typed values and creates an EngineeringConfigurationIntent. It routes draft targets through prepare_draft_engineering_update and committed targets through prepare_engineering_update. The UI editor itself does not own equipment-specific command construction or engineering state.
- CommitNetworkHandler validates the canonical creation-contract metadata, connection terminal compatibility, DraftNetwork validation and required connection cardinality before preparing Core equipment and Simple Wire commands. It detects Core identity collisions and prepares all commands before the first Core mutation. Successful commit clears the active draft in the same transaction and returns created-element/connection metadata. This is a strong prepare-before-mutate and transactional boundary.
- The commit handler currently aggregates draft validation errors into a ValueError string ("Draft validation failed: ..."). A structured set of per-object/per-terminal diagnostic records was not established in the inspected commit path. This can make correction navigation harder when several draft items fail together.
- ProjectPersistenceService serializes optional DraftNetwork data into canonical project.json and restores it as part of LoadedProject. Thus draft state has a persistence contract; a complete user-facing save/close/reopen recovery experience and its UI status affordance still require runtime and lifecycle tracing.
- CommandHistory is Application-owned and records successful commands with undo journals. Draft handlers register a pre-command DraftNetwork snapshot as a transaction inverse. This supports transactional undo foundations, but the visible SLD undo/redo experience for a mixed sequence of draft placement, property edits, wire edits, commit and save/reopen was not established by this source pass.

### B. Workflow risks and recommendations

- The engineer-facing workflow should explicitly distinguish three object states: transient preview (follows cursor and can be cancelled), persisted draft (selectable/editable and saved with the project), and committed Core equipment/connectivity (authoritative engineering network). These are different lifecycle states, not just different colors of one symbol.
- The automatic release-to-draft transition is efficient for repeated placement, but it is easy to mistake for a committed network insertion. Provide an explicit, persistent status/visual distinction and a clear next action; consider a user-configurable placement mode (single-place vs repeat-place) rather than adding a mandatory confirmation dialog to every placement.
- The tool should expose a compact equipment configuration step after placement or on selection, with required/optional/derived parameter semantics, units, range constraints, defaults and missing-field indicators. Do not block initial placement merely because a model has incomplete engineering data.
- Draft preview and persisted draft realization both use SymbolPreviewItem. Ensure the draft presentation state is visibly distinct from transient cursor preview and committed equipment, while keeping symbol geometry and terminal hit targets consistent.
- The endpoint-first wire workflow is appropriate for electrical engineering, but the source audit should be complemented by a live check of snap radius, endpoint highlight, route preview, crossing ambiguity, duplicate wire feedback, keyboard cancellation and touch/trackpad behavior. Keep simple wire semantics separate from Line/Cable equipment semantics.
- Retain minimal endpoint identity and safety checks during wire creation, but make the boundary explicit: immediate checks should prevent invalid target selection; comprehensive network, equipment and engineering validation should produce a complete pre-commit diagnostic set. Review whether all current DraftNetwork candidate compatibility checks belong in interaction-time preflight or should be deferred to commit, consistent with the frozen SLD authoring requirements.
- Commit should present a reviewable summary (equipment count, connection count, unresolved requirements, blocking errors and warnings) before mutation, then return diagnostics that identify each affected draft object, parameter or endpoint and offer direct selection/focus. A generic concatenated error string is insufficient for efficient multi-error correction.
- Save/reopen should preserve draft objects, connections, engineering values, presentation geometry, active SLD document and a recoverable dirty/unsaved state. The user must be able to tell whether a draft has been saved and whether commit has completed.
- Undo/redo should be defined as user-visible engineering transactions. Placement, parameter edits, connection add/remove and commit must each have predictable undo scope; undoing commit should restore the draft authoring state and corresponding SLD projection without duplicating or losing equipment.
- Keep the current Core/Application/UI boundary: UI interactions emit intent; Application owns draft and command transactions; Core receives equipment/topology only at explicit commit; renderer receives immutable committed-plus-draft projections.

### C. Findings added

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-UI-F21 | P1 | ModelPlacementTool stores a transient preview on press and automatically submits AddDraftEquipmentCommand on release; there is no separate confirmation interaction in this path | Make preview, draft placement and committed state unmistakable; provide clear post-placement feedback and optional single-place/repeat-place mode without a modal on every placement |
| V3-UI-F22 | P1 | DraftNetwork is projected independently through DraftSLDProjection and DraftPresentationFactory; committed and draft snapshots are represented as a composite canvas snapshot | Define and visually verify a single canvas lifecycle contract for transient preview, persistent draft and committed projections; verify refresh, selection, z-order and event ordering |
| V3-UI-F23 | P1 | EngineeringParameterEditor supports draft and committed identities, editable/derived metadata, typed coercion and paired-field validation, but Inspector is hidden by default and no complete first-placement configuration flow was established | Provide contextual equipment properties on placement/selection, expose required/optional/derived status, units and missing-field state, and retain draft-aware editing |
| V3-UI-F24 | P1 | WireTool requires stable object endpoint snaps and retains source preview on failure; DraftConnection has canonical endpoint identities | Standardize endpoint highlighting, snap feedback, wire route preview, crossing/duplicate handling, cancellation and actionable correction; verify these behaviors live across equipment types |
| V3-UI-F25 | P1 | DraftNetwork.validate_connection_candidate applies endpoint compatibility during draft connection creation; CommitNetworkHandler repeats trusted terminal compatibility and full draft validation at commit | Separate immediate target eligibility from comprehensive commit validation; reconcile early rejection with the approved engineer workflow and avoid duplicate/conflicting diagnostics |
| V3-UI-F26 | P1 | CommitNetworkHandler aggregates snapshot validation and required-connection errors into a single ValueError string; structured commit diagnostics per draft item/parameter/terminal were not established | Return typed, stable diagnostics with severity, object/field/endpoint identity, corrective guidance and direct canvas/Inspector navigation |
| V3-UI-F27 | P1 | ProjectPersistenceService writes DraftNetwork into project.json and restores it into LoadedProject; full UI recovery/dirty-state behavior was not traced | Specify and verify save/reopen/recovery for draft equipment, wiring, parameters, layout, active document and unsaved changes |
| V3-UI-F28 | P1 | Draft commands record transaction inverses and CommandHistory stores undo journals; mixed draft/commit undo behavior was not established end-to-end | Define the SLD undo/redo transaction model, including undoing commit to restore the exact draft and projection state; expose disabled reasons and command descriptions |
| V3-UI-F29 | P2 | SLDEditor hides Explorer, Inspector, Messages and Tool Settings at construction; inspector can be shown contextually on selection | Re-evaluate first-run SLD defaults and provide discoverable, non-obstructive access to equipment catalogue, properties and diagnostics |
| V3-UI-F30 | P2 | WireTool dispatches draft and committed endpoint pairs through different Application command paths while presenting one simple-wire gesture | Preserve one coherent user gesture while making draft/committed endpoint state and resulting transaction semantics transparent; audit mixed-state connections and error recovery |

These findings are source-backed workflow risks and design recommendations. The presence of the underlying architecture is confirmed; visual defects, runtime event-ordering problems, lost selection, projection refresh failures and undo/redo defects have **not** been reproduced in a running application.

### D. Source files inspected

- ui/editors/sld/sld_editor.py
- ui/tools/model_placement_tool.py
- ui/tools/wire_tool.py
- ui/tools/electrical_insertion_tool.py (insertion workflow sampled)
- ui/tools/tool_dispatcher.py
- ui/canvas/interaction_manager.py
- ui/canvas/draft_sld_projection.py
- ui/canvas/draft_presentation_factory.py
- ui/canvas/sld_canvas_projection.py
- ui/sld/sld_controller.py
- ui/sld/sld_document.py
- ui/sld/sld_projection_manager.py
- ui/panels/engineering_parameter_editor.py
- ui/panels/properties_panel.py
- core/application/draft/network.py
- core/application/draft/handlers.py
- core/application/commands/draft_commands.py
- core/application/services/validation_service.py
- core/application/history.py
- core/persistence/project_package.py
- core/persistence/project_persistence.py

### E. Verification limits and next sequence

**Verification limits:** This was a selective source audit on the V3 research branch. No GUI was launched, no screenshot or recording was captured, and no mouse/keyboard workflow was executed. The complete event-to-renderer path, selection hit-testing of draft items, commit dialog/result presentation, mixed draft/Core connection policy, settings persistence and full undo/redo behavior remain to be traced. ProjectPersistenceService's draft serialization/restoration is source-confirmed, but end-user recovery behavior is not. No tests, CI, V2 source edits or implementation were performed.

**Next:** 8I-4 — Control canvas/ladder and Protection workspace workflow audit, covering editor entry, tool discovery, signal/channel availability, selection, property editing, validation, execution/monitoring, diagnostics and cross-domain navigation while preserving separate Control and Protection execution authority.

## 8I-4. Control canvas and Protection workspace workflow audit (2026-11-04)

**Scope:** Trace Control editor composition, ladder canvas interaction, tool palette, selection and Inspector, signal/action/interlock configuration, Control cycle execution, Protection editor/workspace composition, relay/channel presentation, measurement binding, diagnostics, TCC/coordination panels and Application lifecycle/read-model boundaries. Source-level review only; no running UI session.

### A. Control workflow and interaction model

- ControlEditor is a region-composed editor with header, Explorer, Tool Shelf, Tool Settings, canvas, Inspector, overlay, Diagnostics and Status. The inspected ControlWorkspace creates a ControlCanvas, LadderInteraction, ControlToolPalette, ControlToolbar, ControlInspector and ControlStatusBar. It explicitly hides its historical palette and toolbar because ControlEditor is expected to realize the canonical regions. The exact runtime composition/reparenting path and effective visibility of these widgets were not proven in this targeted trace.
- ControlWorkspace's LadderView is a separate QGraphicsView with its own mouse event handlers. Mouse movement updates the LadderInteraction preview; a left press either places/executes the active tool or selects at the cursor. It sets hand-drag mode and fits content when shown. This is a distinct interaction implementation from the shared SLD GraphicsView and the Protection GraphicsSurface.
- LadderInteraction has explicit tool lifecycle, transient preview, selection, signal-routing and cancellation. Component placement snaps to an existing rung and a discrete position; it then executes AddControlComponent through Application. Signal connection is output-port-first then input-port; it checks direction, self-connection and signal type compatibility before executing ConnectControlSignals. Failure leaves the tool active until corrected or cancelled; success cancels the interaction.
- ControlToolRegistry exposes only descriptors whose Application command or component contract is supported. The palette groups tools by category and exposes contacts, coils, timers, latches, logic gates, interlocks, signal connect/disconnect, action binding, move and remove. The descriptors in the inspected candidate list use empty icon strings and the palette renders text buttons, so there is no icon-based visual recognition in this implementation.
- The ControlInspector combines several engineering tasks in one long panel: selected component configuration, timer preset/mode editing, output-to-equipment action binding, interlock setup and engineering signal mapping. It queries the active Network to populate action targets and uses Application commands for persistent changes. It is a strong Application boundary, but the combined information architecture can make it difficult to distinguish logic configuration, physical equipment action mapping, measurement/signal ingress and interlock policy.
- The Inspector exposes Engineering Signal Source, selected Control component input, Control action/interlock destination and project signal bindings. It therefore provides a separate project-level signal mapping workflow in addition to direct component-port wiring. The exact source list, supported channel types and live availability semantics need a focused follow-up; the current source pass does not prove every signal source is visible or fresh.
- ControlApplicationService exposes immutable read models for rungs, components, connections, typed inputs/outputs, state, action bindings, interlocks and dynamic-control associations. Mutations use Application commands and transaction inverses. This is a positive domain boundary and supports a richer future inspector/read model.
- The Control cycle UI calls application.execute_control_cycle() and reports a short completion/failure string through ControlStatusBar. The inspected user-facing path does not expose a cycle timeline, evaluation trace, input-quality snapshot, blocked-action detail, output decision list or linked equipment feedback. ControlEngine itself returns immutable decisions, blocked actions and diagnostics; the current UI status message does not surface that detail.
- The Control canvas and palette are not shown to have a unified interaction contract with the SLD/Protection canvases. The shared CanvasInteractionAdapter is used for status feedback, but Control owns a bespoke view and LadderInteraction state path. This creates a likely source of inconsistent keyboard, pan/zoom, hit-testing, focus, snapping and cancellation behavior; these are evaluation risks, not reproduced failures.
- Control execution authority remains separate: ControlEngine evaluates logic and emits intent; Application owns action execution and Core equipment mutation. Preserve this distinction in any UI execution monitor.

### B. Protection workflow and interaction model

- ProtectionEditor defines header, Explorer, Tool Shelf, Tool Settings, canvas, Inspector and optional Diagnostics/Status regions. Its standard tool shelf exposes Select, Connect Measurement, Inspect, Fit and Diagnostics.
- ProtectionWorkspace composes a ProtectionExplorer with Relays and ANSI Catalogue tabs; an Inspector tab set with Relay Details, TCC, Analysis Coverage and Coordination Study; a ProtectionGraphicsSurface; and a dedicated ProtectionInteractionController. The historical ProtectionToolbar is hidden because the editor's canonical Tool Shelf is expected to expose tool activation. The visible editor composition must be verified at runtime to ensure no explicitly hidden legacy widget is relied upon.
- ProtectionGraphicsSurface builds a read-side flow presentation from Protection read models and project ProtectionFunctionConfiguration: measurement-channel node → relay input → relay → protection function → ProtectionDecision → trip output. This communicates the conceptual evaluation chain and does not mutate Core equipment or act as execution authority.
- The channel nodes currently originate from configuration.input_channel_ids: for each configured relay input, the view looks up the bound channel ID and creates a Measurement Channel node only when a channel ID is present. The inspected refresh path does not enumerate the project's full MeasurementChannelService registry to create a selectable catalogue of unbound channels. ProtectionInteractionController's Connect Measurement tool requires the engineer to select an existing measurement-channel node first and then a relay-input node. Thus the source path does not establish how a user discovers and starts binding a channel that is not already represented on the canvas. This is a source-confirmed discoverability/workflow gap; an alternate channel browser or dialog elsewhere was not found in the inspected Protection path.
- The current Protection node labels show channel ID and relay input name, but the canvas does not establish the full provenance chain from physical CT/PT/CVT source terminal through channel definition, signal type/phase/unit, quality, timestamp and availability. MeasurementChannelService owns those project-scoped channel objects and validates producer identity, project activation, trusted clock, signature attestation, monotonic sequence and sample quality at ingress. The UI should expose a read-only channel detail/provenance inspector so the engineer can confirm what is being bound.
- ProtectionInspector is read-side only. It displays relay identity/type, function label, configured elements, input bindings, settings, implementation status, and available ProtectionDecision fields/reason/operating time. No contextual edit command workflow was established in this inspector; configuration edits are Application-owned and currently appear to require another configuration surface. The distinction between inspect and configure should be explicit.
- The Diagnostics tool currently calls show_diagnostics(), which only emits the feedback text "Protection diagnostics are read-side only." It does not navigate to a diagnostic list, filter diagnostic records, highlight affected nodes or provide correction actions in the inspected path. This is a strong mismatch between tool label and delivered action.
- The Protection workspace has meaningful engineering read-side panels: ANSI function catalogue with implementation status, TCC, analysis coverage and coordination study results. The TCC and coordination panels refresh from Application read models/study results. However, their navigation relationship to selected relay/function, diagnostic findings, and actual edit/coordination workflows needs explicit task-oriented review.
- Protection tool interaction uses one shared SelectionManager and Application commands for binding/unbinding. A connection attempt selects a channel then a relay input; invalid endpoints and command failures are reported through CanvasInteractionAdapter feedback. This is a useful intent/feedback foundation, but there is no source-confirmed live preview path connecting a channel to an unbound input because the source node availability issue above remains.
- ProtectionRuntime composes project Protection configuration against the active Network and MeasurementChannel objects. It invalidates the prior composed system before validation/recomposition so a stale system is not left evaluable after failed recomposition. MeasurementChannelService triggers the Application-owned protection evaluation path only after trusted sample publication. UI should project runtime/configuration freshness and channel quality without attempting to run Protection independently.
- Protection decisions and trip outputs remain separate from Control action intent. The ProtectionOutputService accepts only actionable ProtectionDecision values and delegates trip commands through Application. The UI should present ProtectionDecision provenance, associated channel samples/quality, target breaker and resulting device feedback as linked but distinct stages.

### C. Cross-domain navigation and feedback

- Control and Protection both use the canonical SelectionManager for object selection and both read through Application read models. Their canvas implementations, tool activation and status feedback remain discipline-specific.
- Control has a ladder-specific signal connection path and project engineering signal mapping; Protection has a channel-to-relay-input binding path. These are different relationships and should not be visually or semantically merged into one generic wire concept.
- The Control Inspector can bind a logic output to equipment action and configure interlocks; Protection can produce a decision and request a breaker trip through a distinct Application service. A cross-domain view should show the trace from measurement channel → Protection decision → Protection output/DeviceCommand → equipment feedback and, where explicitly configured, Control interlock/logic participation. It must not merge Control and Protection execution authority or make Control a prerequisite for Protection trips.
- Current Protection Diagnostics is a placeholder feedback action, while Control execution reports only completion/failure. V3 needs a common diagnostic presentation contract with domain-specific typed records, severity, source object/terminal/channel, timestamp, active project generation, explanation, corrective action, and source navigation.
- Status should expose active project/workspace, active tool, selection, execution state, last cycle/evaluation time, channel availability/quality/freshness, blocked/invalid decisions, pending commands, and device feedback. Keep this contextual and avoid overwhelming the canvas with raw telemetry.

### D. Findings added

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-UI-F31 | P1 | Control uses a dedicated LadderView mouse path and LadderInteraction; Protection uses ProtectionGraphicsSurface and its own interaction controller rather than the shared SLD GraphicsView path | Define a shared canvas interaction contract for focus, selection, navigation, preview, cancellation, feedback and accessibility; retain discipline-specific geometry and semantics |
| V3-UI-F32 | P2 | ControlToolDescriptor candidates use empty icon IDs and ControlToolPalette renders text-only buttons | Provide consistent iconography, category hierarchy, concise descriptions and keyboard-accessible tool discovery; preserve text labels |
| V3-UI-F33 | P1 | Control Inspector combines timer configuration, equipment action binding, interlocks and engineering signal mapping in one long panel | Separate contextual property editing from action binding, signal/channel mapping and interlock configuration; use task-specific sections and explicit source/destination semantics |
| V3-UI-F34 | P1 | Control cycle UI reports only completion/failure although ControlEngine results include decisions, blocked actions and diagnostics | Add a read-only cycle monitor with input snapshot, evaluation trace, decisions, blocked actions, interlock reasons, command dispatch and device feedback; keep execution in Application |
| V3-UI-F35 | P1 | Protection canvas creates measurement-channel nodes only for channel IDs already present in configured relay input bindings; Connect Measurement requires selecting a channel node first | Add a project channel browser/picker that lists all eligible channels, including unbound channels, with source provenance, signal type, phase, unit, quality, timestamp and availability; allow direct binding to a selected relay input |
| V3-UI-F36 | P1 | Protection channel node labels show ID only and do not project the physical source terminal or full measurement metadata | Provide a read-only measurement provenance/quality inspector and expose the source chain from physical instrument/terminal through channel to relay input |
| V3-UI-F37 | P1 | Protection Diagnostics action calls a method that only posts "Protection diagnostics are read-side only" feedback | Implement a real diagnostics surface with typed findings, affected relay/function/input/channel, severity, correction guidance and canvas/Inspector navigation; otherwise rename/remove the misleading tool |
| V3-UI-F38 | P1 | ProtectionInspector is read-side only and displays configuration but no contextual editing action; separate configuration workflow was not established in this pass | Make inspect/configure modes explicit and provide controlled Application command-based editing for relay elements, bindings, settings and target mapping |
| V3-UI-F39 | P1 | ProtectionRuntime and MeasurementChannelService enforce project-scoped channel composition and trusted sample ingress, but the workspace does not project runtime freshness/quality/availability into the signal-flow view | Surface stale/unavailable/bad-quality channel states and runtime/configuration mismatch with fail-closed status; never infer a healthy input from a configured channel ID |
| V3-UI-F40 | P1 | ProtectionOutputService routes actionable decisions through Application; ControlEngine separately produces intent and decisions; no consolidated trace view was established | Provide linked but distinct Protection decision, output command, Control interlock/logic context where configured, and device feedback trace; preserve independent Protection trip authority |
| V3-UI-F41 | P2 | Protection workspace combines ANSI catalogue, Relay Details, TCC, Analysis Coverage and Coordination Study tabs without an established end-to-end task/navigation model | Define task journeys for function selection, configuration, coordination, validation, commissioning and post-event review; preserve selection context across related panels |
| V3-UI-F42 | P2 | Control and Protection workspaces rely on distinct canvas/status paths; effective visibility of hidden compatibility-owned palette/toolbar widgets depends on editor composition not verified here | Audit actual composition and first-visible state; remove duplicate hidden widgets after canonical regions are proven, and ensure the intended tool shelf/Inspector/status are visible and reachable |

These findings are source-backed design/usability risks. The unbound-channel discovery issue is established by the inspected Protection refresh and connect-tool code path; no claim is made that no alternate channel picker exists anywhere in the entire repository. No UI rendering, input latency, selection synchronization, or runtime execution defect is declared reproduced.

### E. Source files inspected

- ui/editors/control/control_editor.py
- ui/control/control_workspace.py
- ui/control/control_tool_palette.py
- ui/control/control_inspector.py
- ui/control/control_status_bar.py
- ui/control/ladder/ladder_interaction.py
- ui/control/ladder/ladder_projection.py
- ui/canvas/control_canvas.py
- ui/editors/protection/protection_editor.py
- ui/protection/protection_workspace.py
- ui/protection/protection_tools.py
- ui/protection/protection_engineering_panels.py
- ui/protection/protection_presentation.py
- core/application/services/control_service.py
- core/application/services/measurement_channel_service.py
- core/application/services/protection_configuration_service.py
- core/application/services/protection_output_service.py
- core/control/engine.py
- core/protection/runtime.py

### F. Verification limits and next sequence

**Verification limits:** Selective source inspection on the V3 research branch. No application launch, screenshot, live project, user task execution or runtime event trace was performed. The exact composition/reparenting and visibility of Control/Protection tool widgets remains unverified. The full Control engineering signal source population path and alternate Protection unbound-channel discovery surfaces were not exhaustively searched. Channel quality/freshness projection and cross-domain decision-to-device-feedback visualization were not verified. No tests, CI, V2 source edits or implementation were performed.

**Next:** 8I-5 — cross-cutting UI interaction audit: keyboard shortcut dispatch and focus, status field catalogue, settings/layout persistence, diagnostics and dialogs, keyboard/accessibility, DPI/resizing, recovery and full composition verification. Then 8I-6 will consolidate requirements and prioritize the V3 UI/UX proposal.

## 8I-5. Cross-cutting UI interaction, accessibility, persistence and recovery audit (2026-11-04)

**Scope:** Inspect active keyboard shortcut installation, focus/interaction infrastructure, status bar fields, workspace and viewport state, settings/theme lifecycle, message/diagnostic presentation, dialogs and close recovery, accessibility and high-DPI evidence. This is a selective source audit of the V3 research branch, not a runtime usability/accessibility evaluation.

### A. Keyboard shortcuts, focus and interaction dispatch

- ToolShortcutRegistry is a Qt-independent semantic keymap model with global, SLD, Control, Protection, Study, canvas, inspector and tool-shelf contexts. It validates uniqueness within a context and resolves actions/tool IDs. It does not itself install keyboard handlers or activate tools.
- The inspected active composition root (main.py) contains no ToolShortcutRegistry, ToolShortcut, QShortcut or QKeySequence reference. The menu plugin creates QAction objects and sets shortcuts from MenuActionSpec or canonical ActionDefinition metadata. The toolbar plugin intentionally leaves canonical shortcuts menu-owned unless an individual toolbar spec explicitly supplies one. Thus keyboard behavior is driven by QAction/menu setup in the inspected active path, not by the semantic contextual keymap registry.
- The menu action catalog and menu specs provide overlapping shortcut declarations; the toolbar has an opt-in shortcut field. This arrangement has some deliberate single-owner behavior, but no source-confirmed active context dispatcher was found that resolves the same key differently for SLD, Control, Protection, canvas and Inspector focus.
- ToolManager forwards key_press/key_release to the active tool when its input dispatch method is called. The inspected main composition does not establish a single focus-aware keyboard dispatcher that arbitrates between focused text editors, QAction shortcuts, active canvas tools, and contextual keymap definitions.
- No complete keyboard focus traversal policy, focus restoration after workspace switch, tab order policy, shortcut conflict report, or discoverable shortcut reference surface was established in the inspected paths. QSS defines visible focus styling for several standard widgets and tool-shelf buttons; this is positive but is not equivalent to verified keyboard accessibility.
- Recommendation: maintain one versioned action/shortcut catalogue, explicitly define context precedence (text editor > focused panel > active editor/canvas > global), reserve OS/common editing keys, show shortcuts in menus/tooltips/help, and provide a keyboard-accessible shortcut reference/customization surface. Keep tool activation routed through ToolManager and application actions through UIActionRouter.

### B. Status bar and diagnostics presentation

- StatusPlugin declares six default status fields: tool, selection, coordinates, project, validation and workspace. The plugin can register additional fields and update visibility, but no default field for active signal/channel availability, data quality/freshness, Control cycle state, Protection evaluation freshness, pending device command, or device feedback was established.
- StatusPlugin binds authoritative Controller, Application, SelectionManager, GraphicsView, WorkspaceController and project adapter state. This is a positive read-side composition boundary. Status fields remain presentation-only.
- MessagesPanelWidget is a compact string-list widget. It stores validation strings and event strings separately in memory but renders both into one QListWidget with no visible source grouping, severity, timestamp, object identity, acknowledgement state, filter, or direct navigation metadata in the inspected implementation. Re-render clears and repopulates the list.
- UIActionRouter has a central error callback and avoids repeating an unchanged enabled-provider failure. However, error delivery varies by call site: some routed errors go through Messages, while commit failures use QMessageBox.critical, project close uses a Save/Discard/Cancel warning, and informational fallback actions use QMessageBox.information.
- This is not inherently wrong: blocking dialogs are appropriate for irreversible/high-impact decisions and immediate critical failures, but repeated engineering diagnostics should be persistent, structured, non-modal and navigable. A unified diagnostic record should carry severity, source domain, object/terminal/channel, timestamp, project generation, explanation, corrective guidance and navigation target.
- Recommendation: keep transient status messages for low-impact feedback, use a persistent diagnostic centre for warnings/errors/events, reserve modal dialogs for explicit decisions or exceptional blocking failures, and preserve diagnostic history when the user changes workspace or closes a transient panel.

### C. Workspace, viewport and settings persistence

- WorkspaceManager stores active workspace ID and immutable WorkspaceState in memory. WorkspaceState contains workspace_id and WorkspaceLayout; WorkspaceLayout contains logical Areas. The inspected models do not expose to_dict/from_dict or an explicit settings serialization contract.
- WorkspaceController activates, applies and resets layouts through WorkspaceManager and WorkspaceRealizer. WorkspaceRealizer realizes logical areas/editors/regions and supports rollback if realization fails. This provides a transactional runtime presentation lifecycle, but does not itself prove persistence between application launches.
- ViewportState is a mutable, toolkit-independent value model for center, zoom, rotation, grid and snap visibility. It has to_dict/from_dict methods. This is a useful serialization primitive, but the inspected startup composition does not connect it to QSettings or establish restore/save lifecycle for each project/document/workspace.
- The active main.py and MainWindow paths inspected contain no QSettings, saveGeometry/restoreGeometry, saveState/restoreState or equivalent preference read/write calls. MainWindow has a minimum size and a close handler for project lifecycle, but no window geometry persistence contract was established.
- PluginContext includes a generic settings field, but the inspected context contract alone does not establish a concrete settings provider, schema, versioning, migration, ownership or persistence wiring.
- StyleManager supports setting/resetting a Theme and applying QSS to QApplication. Theme includes font family/size and semantic style tokens. The default is GridForge Engineering Dark. StyleManager.get_state() is diagnostic only; no appearance preference persistence or user-facing theme/density/accessibility profile workflow was established in this source pass.
- Recommendation: define a versioned user-preferences store distinct from project engineering data. Persist window geometry/state, active workspace, per-workspace region visibility/sizes, selected appearance/density/font scale, keyboard preferences and per-document viewport state with stable IDs, migration and safe defaults. Do not put user-machine preferences into canonical project.json unless an explicitly portable project-view setting is intended.

### D. Accessibility, typography and high-DPI considerations

- The stylesheet contains focus-state rules for buttons, line edits, combo boxes, checkboxes, spin boxes and tool shelf controls. Theme tokens include a font family and point-size setting. These are positive foundations.
- The inspected source does not establish systematic accessibleName/accessibilityDescription metadata for custom engineering controls, a screen-reader semantic model for graphics-canvas objects, keyboard alternatives for every pointer-only operation, a high-contrast theme, a density profile, or a user-controlled font scaling setting.
- Theme currently defaults to a dark engineering palette. The presence of semantic valid/warning/invalid colors and focus tokens is useful, but the source audit does not demonstrate contrast ratios, color-independent state encoding, color-vision-deficiency checks, or consistent non-color indicators across all canvases and diagrams.
- The inspected main composition and style modules do not define a project-level high-DPI/raster icon policy or explicit multi-monitor scaling validation. Qt Widgets can use Qt's device-independent high-DPI scaling, but raster icons and custom graphics/canvas dimensions still need asset and coordinate validation at representative scale factors.
- Recommendation: add accessible names/descriptions and logical tab order to custom controls; expose canvas objects through keyboard navigation and semantic object summaries; never encode electrical/protection/control states by color alone; validate contrast, font scaling, 100/125/150/200% DPI, mixed-DPI monitors and display changes. Treat WCAG 2.2 AA as a useful reference for native application accessibility, adapted to Qt Widgets and canvas interactions.

### E. Recovery and safe application transitions

- MainWindow closeEvent fails closed if no composition-owned close handler is installed, preventing a close that could bypass project transition handling. The active composition installs ProjectCloseController and a Save/Discard/Cancel decision provider for unsaved project changes. This is a positive recovery/safety behavior.
- Save/Discard/Cancel handling is explicit for project transitions. The source pass did not establish equivalent persistence for user preferences or restoration of the last workspace/viewport after a crash/restart.
- Several critical operations surface failure through modal dialogs, including Commit Network. The dialog text can include structured ExecutionError code, details and cause, but the user must manually read/copy the text; direct selection of the affected draft item or diagnostic entry was not established.
- No general crash recovery/autosave journal for UI layout, active tool, transient preview, or unsaved project edits was established in the inspected UI paths. Project-level draft persistence was recorded in 8I-3; this section does not reinterpret it as UI session recovery.
- Recommendation: separate engineering-document autosave/recovery from user-preference persistence; never restore a transient active tool or half-finished pointer gesture as if it were committed work. Offer recovery candidates for project drafts and preserve diagnostics/last operation context, with user confirmation and integrity checks.

### F. Findings added

| Finding ID | Priority | Evidence | Proposed V3 action |
|---|---|---|---|
| V3-UI-F43 | P1 | ToolShortcutRegistry models contextual keymaps but is not referenced by the inspected main.py composition; QAction shortcuts are installed through menu definitions/action metadata | Connect a single contextual shortcut dispatcher or formally retire the unused registry; define focus-aware precedence and collision reporting |
| V3-UI-F44 | P1 | ToolManager forwards key events to active tools, but a single focus-aware dispatcher arbitrating text editors, panels, canvas tools and global actions was not established | Define central keyboard routing, focus restoration and keyboard-only workflows for every primary engineering task |
| V3-UI-F45 | P1 | StatusPlugin defaults to tool, selection, coordinates, project, validation and workspace fields | Add contextual channel quality/freshness, Control cycle, Protection evaluation, pending command and device feedback states without flooding the status bar |
| V3-UI-F46 | P1 | MessagesPanelWidget merges validation/event strings in one list without severity, timestamp, source/object metadata, filtering or navigation | Replace the string list with typed, persistent, filterable diagnostics/events and direct object/canvas navigation |
| V3-UI-F47 | P1 | WorkspaceManager/WorkspaceState/WorkspaceLayout retain runtime state but expose no serialization contract in the inspected models; main.py has no QSettings or save/restore state calls | Define versioned user preference persistence for active workspace, region visibility/sizes and window geometry/state |
| V3-UI-F48 | P1 | ViewportState supports to_dict/from_dict but no connection to active project/document settings persistence was established in the inspected composition | Persist and restore per-document/per-workspace viewport state with safe bounds and migration |
| V3-UI-F49 | P1 | StyleManager/Theme support runtime theme configuration and QSS application; default is dark; no user-facing persisted theme/density/font-scale workflow was established | Provide theme, high-contrast, density and font-scale preferences with accessibility validation |
| V3-UI-F50 | P1 | QSS includes focus styling, but systematic accessible names, canvas semantics, keyboard alternatives and screen-reader workflow were not established | Define native Qt accessibility requirements for controls, panels and graphics canvases; verify keyboard-only and assistive-technology operation |
| V3-UI-F51 | P1 | Theme/style tokens exist but no contrast-ratio, color-independent status or color-vision validation evidence was found in the inspected paths | Validate semantic color pairs and require redundant shape/text/pattern indicators for electrical and protection states |
| V3-UI-F52 | P2 | Qt widgets are used with fixed minimum window size and tokenized font size; explicit asset/DPI/mixed-monitor policy was not established | Validate 100–200% scaling, mixed-DPI monitors, raster/vector icon quality, resize behavior and small-screen minimum layouts |
| V3-UI-F53 | P1 | Project transitions have Save/Discard/Cancel handling and MainWindow fails closed without the close handler; UI preference/crash-session recovery was not established | Define crash recovery for project drafts and last valid UI session while excluding transient gestures/tools and preserving project integrity |
| V3-UI-F54 | P2 | Commit errors and some other failures use modal dialogs, while routed errors/messages use other channels; direct diagnostic navigation is not established | Establish a severity/modality policy and route blocking failures to persistent structured diagnostics with direct correction navigation |

These findings describe source-level gaps or unverified capabilities in the inspected active paths. Absence claims are scoped to the inspected composition and modules; they do not prove that no independent or newly added settings/accessibility implementation exists elsewhere in the repository. No keyboard, screen-reader, contrast, DPI, restart/recovery or dialog usability test was performed.

### G. External Qt reference evidence

- Qt QSettings documents portable persistence for application options, window sizes, positions and visibility state, including grouping and synchronization: https://doc.qt.io/qt-6/qsettings.html
- Qt QWidget/QMainWindow geometry and state APIs support saving/restoring window geometry and toolbar/dock layout; restoreState should consume trusted application-produced state with compatible versions: https://doc.qt.io/qt-6/qmainwindow.html and https://doc.qt.io/qt-6/restoring-geometry.html
- Qt Widgets supports high-DPI scaling through device-independent geometry and font scaling; raster assets require appropriate high-resolution resources: https://doc.qt.io/qt-6/scalability.html

These references establish available Qt mechanisms, not evidence that GridForge currently uses them.

### H. Source files inspected and verification limits

**Files inspected:** main.py; ui/main_window.py; ui/core/qt.py; ui/core/action_router.py; ui/core/action_catalog.py; ui/core/action_definition.py; ui/core/controller.py; ui/core/tool_manager.py; ui/tools/tool_shortcuts.py; ui/tools/tool_settings.py; ui/plugins/menu_plugin.py; ui/plugins/toolbar_plugin.py; ui/plugins/status_plugin.py; ui/plugins/shell_plugin.py; ui/plugins/plugin_context.py; ui/panels/messages_panel.py; ui/styling/style_manager.py; ui/styling/theme.py; ui/styling/style_tokens.py; ui/styling/stylesheet.qss; ui/workspace/workspace_state.py; ui/workspace/workspace_layout.py; ui/workspace/workspace_manager.py; ui/workspace/workspace_controller.py; ui/workspace/workspace_realizer.py; ui/workspace/viewport_state.py.

**Verification limits:** Source-only selective review on the V3 research branch. No GUI launch, keyboard interaction, assistive-technology session, contrast measurement, multi-monitor/DPI run, settings restart test, crash simulation or recovery exercise was performed. Search for settings and shortcut installation was scoped to the active main.py and inspected UI modules. No tests, CI, V2 source edits or implementation were performed.

**Next:** 8I-6 — consolidate all 8I UI/UX findings into a prioritized V3 requirements baseline, map user journeys to requirements and acceptance evidence, identify dependencies and sequencing, and distinguish required V3 capabilities from optional enhancements. This is a research/specification consolidation only; do not implement until explicitly approved.

## 8I-6. Consolidated GridForge V3 UI/UX requirements baseline and delivery sequence (2026-11-04)

**Purpose:** Convert the source-backed UI findings V3-UI-F01 through V3-UI-F54 (sections 8I through 8I-5) into a traceable V3 requirements baseline. This is a research/specification consolidation, not implementation authorization and not a change to the frozen V2 architecture.

### A. Consolidated design position

GridForge V3 shall present one coherent engineering application across SLD, Control, Protection and Study, with consistent interaction conventions and distinct domain-specific task models. Consistency means predictable focus, selection, navigation, editing, validation, feedback, undo/redo, cancellation and recovery; it does not mean forcing electrical schematics, ladder logic, protection signal-flow diagrams and numerical study views into one canvas implementation.

The UI is an interaction and projection layer. It must not become an alternative authority for equipment, topology, measurement, Control execution, Protection decisions, studies or project persistence. All engineering mutations continue through UI intent → Controller → Command → Application → Core, with events and read-side projections returning to the UI. V3 usability work must preserve the frozen Core/Application/UI boundary, plugin contracts and separate Control/Protection execution authorities.

**Evidence classification:** the requirements below are derived from selective source inspection. A source gap is not automatically a reproduced runtime defect. Requirements become release acceptance criteria only after their scope, measurable threshold and verification environment are approved.

### B. V3 requirements catalogue

Priority meaning:
- **P1 — baseline:** required to deliver a coherent, safe and usable engineering workflow; must be specified and verified before the corresponding V3 capability is declared production-ready.
- **P2 — important enhancement:** should be planned in the V3 delivery sequence; release inclusion depends on scope and measured user value.
- **P3 — optional/personalization:** valuable where validated by user research, but not a prerequisite for core engineering correctness.

| Requirement ID | Priority | Requirement statement | Source findings |
|---|---|---|---|
| V3-UI-REQ-001 | P1 | Define a shared cross-editor interaction contract for active tool, selection, focus, pan/zoom, fit-to-content, snap, Escape/cancel, status feedback, context menus and undo/redo. Discipline editors may provide explicit extensions. | F01, F03, F31 |
| V3-UI-REQ-002 | P1 | Provide consistent tool discovery and lifecycle: clear labels/icons, active/disabled states, shortcut hints, disabled reasons, preview/placement/commit distinction, cancel/exit affordance and accessible descriptions. | F07, F21, F23, F32 |
| V3-UI-REQ-003 | P1 | Provide a discoverable first-use workspace with SLD as the initial engineering entry point, visible project context, obvious Explorer/Inspector/Diagnostics access and a reliable restore-layout action. | F02, F11–F15, F29 |
| V3-UI-REQ-004 | P1 | Establish a unified contextual Inspector contract separating identity, editable configuration, read-only calculated values, units/bases, provenance, validation, related-object links and Apply/Reset behavior. All edits use Application commands. | F04, F23, F33, F38 |
| V3-UI-REQ-005 | P1 | Define an explicit SLD lifecycle for preview, draft, engineering configuration, connection, validation, commit, post-commit selection and recovery; show which state is transient, persisted draft or committed network. | F21–F30 |
| V3-UI-REQ-006 | P1 | Make SLD connection authoring predictable and recoverable: endpoint/snap feedback, compatible-terminal guidance, wire routing, duplicate/crossing feedback, undo/cancel and precise commit diagnostics. Validation timing must follow the approved engineer workflow. | F24–F26, F30 |
| V3-UI-REQ-007 | P1 | Provide structured, object-linked validation results with severity, code, source, affected object/terminal, explanation, correction guidance and navigation. Do not collapse multiple findings into an opaque exception string. | F05, F26, F37, F46, F54 |
| V3-UI-REQ-008 | P1 | Separate validation findings, application events, operational alarms, study execution messages and data-quality diagnostics as distinct types with appropriate lifecycle and acknowledgement semantics. | F05, F19, F34, F37, F46 |
| V3-UI-REQ-009 | P1 | Provide a Control canvas workflow for placing, connecting, configuring and validating logic with clear signal direction/type, rung/component context, interlock/action binding and cycle outcome explanation. | F31–F34 |
| V3-UI-REQ-010 | P1 | Provide a Control cycle monitor showing evaluated logic, decisions, blocked actions, diagnostics and output intent; distinguish execution completion from actual device actuation/feedback. | F34, F40 |
| V3-UI-REQ-011 | P1 | Provide Protection channel discovery and binding from all eligible project measurement channels, not only channels already represented as canvas nodes. | F35 |
| V3-UI-REQ-012 | P1 | Expose Protection measurement provenance and runtime quality: instrument/source terminal, channel identity, engineering quantity/unit, timestamp/freshness, quality/availability and fail-closed reason. | F36, F39, F45 |
| V3-UI-REQ-013 | P1 | Make Protection inspection and configuration modes explicit; support controlled editing of relay elements, function settings, channel bindings and typed output targets without bypassing Application commands. | F38 |
| V3-UI-REQ-014 | P1 | Provide a traceable but authority-preserving view of Protection decision → output command → configured Control/interlock context → device feedback. Never imply that Control owns or can suppress independent Protection trip authority. | F40 |
| V3-UI-REQ-015 | P1 | Define end-to-end Protection journeys for function selection, relay configuration, measurement mapping, coordination, validation, commissioning and event review, preserving object context across ANSI catalogue, relay, TCC and study views. | F37–F41 |
| V3-UI-REQ-016 | P1 | Define study-specific progressive disclosure for Power Flow, Short Circuit and Transient Stability, with contextual input validation, explicit run state, result provenance and result-to-source navigation. | F08, F14 |
| V3-UI-REQ-017 | P1 | Establish a single focus-aware keyboard routing contract and authoritative shortcut catalogue, with context precedence, collision detection, visible shortcut hints and keyboard alternatives for all critical tasks. | F07, F16, F43, F44 |
| V3-UI-REQ-018 | P1 | Ensure keyboard focus order, focus visibility/restoration, accessible names/descriptions and semantic access to custom controls, panels and engineering canvas objects. | F06, F43, F44, F50 |
| V3-UI-REQ-019 | P1 | Provide a structured persistent Diagnostics Centre with severity, timestamp, source/domain, object/channel identity, project/session context, filtering, acknowledgement where appropriate, correction guidance and navigation. | F05, F19, F37, F46, F54 |
| V3-UI-REQ-020 | P1 | Define consistent feedback modality: transient status for low-impact acknowledgement, persistent diagnostics for recoverable findings, and modal decisions only for explicit blocking/irreversible choices. | F19, F26, F37, F46, F54 |
| V3-UI-REQ-021 | P1 | Persist user preferences separately from engineering project truth, including window geometry/state, active workspace, region visibility/sizes, appearance and keyboard preferences, with schema versioning and safe migration. | F02, F20, F47, F49 |
| V3-UI-REQ-022 | P1 | Persist per-project/per-document viewport state (centre, zoom, rotation, grid and snap visibility) using stable document identity and bounded/safe restoration. | F03, F48 |
| V3-UI-REQ-023 | P1 | Provide project draft recovery and safe session restoration without reviving transient pointer gestures or treating an uncommitted preview as committed engineering data. Preserve Save/Discard/Cancel safeguards. | F27, F28, F53 |
| V3-UI-REQ-024 | P1 | Ensure engineering state is never communicated by color alone; define semantic colors plus text, shape, line pattern, icon or explicit state label. Validate contrast on canvas and panels. | F06, F39, F51 |
| V3-UI-REQ-025 | P1 | Provide a user-selectable high-contrast/accessibility presentation profile and scalable typography with visible focus and readable engineering annotations. | F06, F49, F50, F51 |
| V3-UI-REQ-026 | P2 | Provide coherent light/dark themes, adjustable density and consistent icon/label systems across tool shelves, palettes, menus and toolbars. | F06, F07, F17, F32, F49 |
| V3-UI-REQ-027 | P2 | Validate window resizing, splitter behavior, minimum useful panel dimensions, 100/125/150/200% DPI, mixed-DPI monitors, monitor transitions and icon asset quality. | F17, F52 |
| V3-UI-REQ-028 | P2 | Provide a contextual start/recent-project/recovery entry surface and optional sample projects/onboarding, without obstructing expert users who prefer direct workspace startup. | F15 |
| V3-UI-REQ-029 | P2 | Provide a user-configurable toolbar/panel arrangement and clear navigation taxonomy distinguishing canonical workspaces, editor surfaces and auxiliary views. | F12–F14, F17, F20 |
| V3-UI-REQ-030 | P2 | Provide consolidated task-oriented help and contextual guidance for complex Protection, Control and Study workflows, with references to applicable engineering concepts rather than generic widget instructions. | F08, F09, F10, F41 |
| V3-UI-REQ-031 | P2 | Provide scalable navigation and rendering feedback for large diagrams, dense projects and long-running study views; measure performance and avoid blocking UI interaction. | F03, F10, F31 |
| V3-UI-REQ-032 | P2 | Provide a configurable status-bar field policy that prioritizes current workspace context and relevant channel/Control/Protection execution state without duplicating the Diagnostics Centre. | F34, F39, F45 |
| V3-UI-REQ-033 | P3 | Allow optional expert shortcut customization, user-defined workspace presets and per-role/personal layout profiles after the canonical interaction contract is stable. | F17, F20, F43, F47 |

### C. Engineering user journeys and traceability

| Journey | Primary user goal | Required UI capabilities | Minimum acceptance evidence |
|---|---|---|---|
| J01 — First launch / project entry | Start a new or existing engineering project and reach the correct work surface | Start/recent/recovery entry, clear project identity, SLD-first navigation, discoverable panels, safe defaults | First-time engineer can identify project state, open/create a project and reach SLD without hidden prerequisite knowledge; expert can bypass onboarding |
| J02 — SLD build and commit | Build an electrical network and commit valid engineering objects | Tool discovery, live preview, equipment configuration, terminal-aware connection, draft state, validation, commit, diagnostics and undo/recovery | Engineer can place multiple equipment objects without earlier objects disappearing; can configure each item, connect required terminals, understand validation, commit and inspect the resulting network |
| J03 — SLD inspect/edit/reopen | Review an existing network, change a property, save and reopen | Contextual Inspector, typed edits, selection persistence, project save/close, viewport and draft persistence | Selection and edit target remain unambiguous; saved engineering state is restored independently of machine-specific preferences; unsaved changes trigger explicit decision |
| J04 — Control logic engineering | Build logic, bind signals/actions/interlocks and understand execution | Ladder canvas, palette, signal browser, typed connection feedback, Inspector, cycle monitor and diagnostics | Engineer can identify eligible signals, connect only valid directions/types, configure timer/action/interlock, run or inspect a cycle and distinguish blocked intent from physical actuation |
| J05 — Protection configuration | Configure relay functions and measurement channels | Channel browser, provenance inspector, relay configure mode, ANSI function catalogue, typed target mapping, validation | Engineer can discover eligible CT/PT/CVT channels, inspect source and quality, configure function settings and output target, and see why unavailable/stale inputs fail closed |
| J06 — Protection coordination and event trace | Coordinate protection and investigate a decision/trip | TCC/coordination workflow, Analysis Coverage, diagnostics, decision-command-feedback trace | Engineer can navigate from relay/function to coordination evidence and from a Protection decision to its command and device feedback without conflating Protection and Control authority |
| J07 — Study setup and interpretation | Configure and run an engineering study and inspect results | Study-specific forms, input validation, execution state, results and source navigation | User sees only relevant inputs, understands required/invalid values, sees run outcome and can navigate from a result to its source project objects and study configuration |
| J08 — Diagnose/recover | Correct an error or recover after interruption | Persistent diagnostic centre, object navigation, recovery candidates, safe save/restore, undo/redo | User can identify severity/source/object, apply a correction or navigate to it, preserve diagnostic history, and recover saved drafts without silently committing transient state |
| J09 — Keyboard/accessibility operation | Complete core workflows without relying exclusively on pointer/color cues | Focus-aware shortcuts, logical focus order, accessible names, semantic canvas navigation, high contrast and scalable text | A keyboard-only walkthrough completes defined critical tasks; assistive technology can identify custom controls and current selection/state; non-color cues communicate engineering status |
| J10 — Workspace/session adaptation | Adapt workspace to role, screen and task, then return later | Workspace presets, persistent geometry/region state, per-document viewport, density/theme preferences | Workspace and view restore predictably after restart and monitor change; invalid or stale settings fall back safely without affecting project engineering data |

### D. Shared UI interaction contract

Every editor/canvas shall implement or explicitly declare support for the following contract:

1. **Identity and context:** active project/document, workspace, discipline, current selection and current tool are visible and queryable.
2. **Tool lifecycle:** idle → activate → preview/target → apply/place → configure → validate/commit as applicable → return to selection/idle. Escape behavior is defined at each state.
3. **Selection:** consistent single/multi-selection semantics, selection feedback, keyboard access, focus restoration and deterministic property target.
4. **Navigation:** pan, zoom, fit, zoom-to-selection, grid/snap controls and coordinate feedback; domain-specific gestures must not silently override common navigation.
5. **Editing:** inspector changes are typed intent through Application commands; calculated/read-only values are visually distinct from editable values.
6. **History:** undo/redo availability and scope are visible; draft and committed changes have defined transaction boundaries.
7. **Feedback:** every user action has a visible outcome, failure reason and recovery path; transient feedback does not replace persistent diagnostics.
8. **Accessibility:** focus, accessible naming, keyboard alternatives, readable status and color-independent visual encoding.
9. **Persistence:** project engineering data, user preferences and transient interaction state are separate persistence classes with explicit restore policy.
10. **Extensibility:** plugin-contributed tools/panels use public UI contracts, route mutations through Application and declare keyboard, accessibility and lifecycle metadata.

### E. Cross-cutting data and authority rules for UI

- UI projections may display Core/Application read models but must not infer or manufacture domain truth from widget state.
- Equipment identity, terminal identity, topology, measurement quality, ProtectionDecision, Control intent, DeviceCommand, DeviceFeedback and StudyResult remain distinct typed concepts.
- A configured measurement channel is not proof of a fresh/valid sample. Display configuration status separately from runtime sample quality and freshness.
- A Protection decision is not proof of command delivery; a command is not proof of physical actuation. Each stage must be traceable with its own state and timestamp.
- Control interlock context may be shown alongside a Protection output trace where configured, but the UI must preserve separate execution authorities and the independent fail-safe Protection path.
- Canvas symbols, ladder contacts/coils, signal-flow nodes and study charts are projections/interaction affordances, not domain entities or execution authorities.
- User workspace/theme/keyboard settings are not canonical electrical project data. Per-document viewport settings may be stored in a project only if explicitly approved as portable view metadata, versioned and separated from engineering truth.
- No plugin is allowed to bypass Application commands or write Core state through UI callbacks.

### F. Dependencies and recommended delivery sequence

**Stage 0 — Requirements and evidence baseline**
- Approve user roles, task scenarios, terminology, UI requirements and measurable acceptance thresholds.
- Capture current application runtime/screenshots for the active composition, first-use state and representative workflows.
- Confirm which source-observed gaps remain present in the intended V3 branch.
- Deliverable: reviewed UX requirements specification and traceability matrix.

**Stage 1 — Shared interaction foundations**
- Establish action/shortcut catalogue and focus-aware routing.
- Establish shared editor/canvas interaction contract and active-tool lifecycle.
- Establish common Inspector contract and typed diagnostic record model.
- Establish accessibility metadata conventions and semantic status vocabulary.
- Dependencies: V3-UI-REQ-001, 002, 004, 007, 017–020, 024–025.
- Deliverable: public UI contracts and design-system specification, not four separate canvas rewrites.

**Stage 2 — Project shell, navigation and persistence**
- Improve first-use/start/recent/recovery entry and workspace navigation taxonomy.
- Persist user preferences, workspace layout and window state; persist per-document viewport independently.
- Establish session recovery policy and migration/fallback rules.
- Dependencies: V3-UI-REQ-003, 021–023, 028–029.
- Deliverable: predictable application entry and restorable work context.

**Stage 3 — SLD workflow**
- Define preview/draft/configure/connect/validate/commit state transitions and selection invariants.
- Implement consistent connection feedback, typed validation and diagnostic navigation.
- Preserve project persistence and undo/redo transaction boundaries.
- Dependencies: Stage 1 contracts, Stage 2 project/session lifecycle, V3-UI-REQ-005–008.
- Deliverable: complete SLD engineer journey J02/J03.

**Stage 4 — Control workflow**
- Apply shared contracts to Ladder canvas without flattening ladder-specific semantics.
- Add signal discovery, contextual Inspector, cycle monitor and diagnostics.
- Expose intent, blocked action, command and feedback as separate states.
- Dependencies: Stage 1 contracts; Measurement/Signal read models; Control Application service contracts; V3-UI-REQ-009–010.
- Deliverable: complete Control journey J04.

**Stage 5 — Protection workflow**
- Add eligible channel discovery, provenance/quality inspection, explicit configuration workflow and diagnostics.
- Build task flow across ANSI catalogue, relay details, TCC, analysis coverage and coordination.
- Add decision-command-Control-context-device-feedback trace while preserving separate authorities.
- Dependencies: Stage 1 diagnostic/Inspector contracts; Signal/Measurement read models; Protection and Control/Application integration contracts; V3-UI-REQ-011–015.
- Deliverable: complete Protection journeys J05/J06.

**Stage 6 — Study workflow**
- Introduce study-specific progressive disclosure, input validation, run state and result provenance/navigation.
- Dependencies: shared Inspector/diagnostics; Study Application read models and immutable result provenance; V3-UI-REQ-016.
- Deliverable: complete Study journey J07.

**Stage 7 — Accessibility, visual profiles and display adaptation**
- Validate high contrast, color independence, scalable typography, density, icons, DPI/mixed-monitor and resizing.
- Dependencies: shared design tokens and interaction contract; V3-UI-REQ-024–027.
- Deliverable: accessibility and display-support evidence across all primary editors.

**Stage 8 — Integrated usability evaluation and release evidence**
- Run scenario-based evaluations across J01–J10 with novice and expert users.
- Measure completion, critical errors, time, recovery, unnecessary actions, task workload and accessibility barriers.
- Prioritize corrective work from observed evidence; do not set arbitrary numeric thresholds before a baseline.
- Deliverable: traceable acceptance evidence and approved residual-risk register.

**Critical path:** Stage 0 → Stage 1 → Stage 2 → Stage 3. Control, Protection and Study can proceed in parallel after the shared contracts and relevant domain read models are stable, but their integration journeys require cross-domain review. Accessibility is a continuous design constraint from Stage 1, not a final-stage retrofit; Stage 7 is formal verification and profile completion.

### G. Requirement acceptance evidence model

For every P1 requirement, the V3 implementation plan must define:
- **Scenario:** named user journey and preconditions.
- **Observable outcome:** what the user can see, select, edit, navigate to or recover.
- **Engineering correctness:** proof that the UI invokes the correct Application command/read model and does not own domain truth.
- **Failure behavior:** invalid, unavailable, stale, conflicting and interrupted states; expected fail-closed or recoverable behavior.
- **Accessibility:** keyboard reachability, focus order, accessible name/description and color-independent state.
- **Persistence:** what is saved, where it is saved, schema/version, migration and restore fallback.
- **Evidence artifact:** source trace, interaction recording/screenshots, structured diagnostic trace, accessibility inspection or user-study observation as appropriate.
- **Traceability:** requirement ID → finding ID → workflow ID → implementation component/contract → evidence artifact → residual risk.

A requirement is not accepted solely because a widget/class exists or a screenshot looks correct. Conversely, the absence of a runtime evaluation in this research pass does not prove a runtime failure. Source review, runtime verification and user evaluation are distinct evidence classes.

### H. Scope boundaries and decisions reserved for approval

**Included in the V3 baseline:** coherent multi-editor interaction, SLD/Control/Protection/Study workflows, contextual engineering Inspector, structured diagnostics, keyboard/focus/accessibility, preference and viewport persistence, safe recovery, visual profiles and DPI adaptation.

**Not authorized by this consolidation:** V2 source changes; changes to frozen Core/Application/domain ownership; replacement of domain-specific canvases merely for visual uniformity; redesign of electrical/protection/control semantics; changing engineering validation policy; changing Protection/Control execution authority; adding test/CI acceptance gates contrary to the user's stated governance; or claiming runtime behavior without reproducing it.

**Decisions still requiring product/engineering approval:** exact role/persona scope; first-launch experience vs direct SLD startup; which viewport metadata is portable with project files; whether diagnostic acknowledgement is needed for each diagnostic class; supported screen-size/DPI envelope; exact keyboard shortcut customization scope; autosave/recovery retention policy; measurable usability thresholds and accessibility conformance target.

### I. Consolidation conclusion

The most consequential V3 UI work is not cosmetic. It is to make the engineering workflow state explicit and recoverable: what is selected, which tool is active, whether an object is preview/draft/committed, what data is configured versus measured, whether a signal is fresh and valid, what Protection decided, what Control requested, what command was issued, and whether the device responded.

The shared interaction contract, structured diagnostics, contextual Inspector and persistence/recovery foundations are prerequisites for reliable discipline-specific workflows. SLD, Control, Protection and Study should then be improved as complete user journeys rather than disconnected panels.

**Next research step:** conduct a requirements challenge/reconciliation pass against the frozen V2 architecture and current V3 research branch, identify duplicate or conflicting requirements, validate the priority/dependency model, and prepare an approval-ready V3 UI/UX specification. No implementation is authorized by this section.

## 8I-7. UI/UX requirements challenge and architecture reconciliation (2026-11-04)

**Purpose:** Challenge section 8I-6 against the frozen V2 architecture baseline and the source findings in 8I–8I-5. Resolve duplicate/overlapping requirements, tighten authority and persistence language, clarify priority and delivery dependencies, and identify decisions that must remain open until runtime/user evidence exists. This is still research/specification; no implementation is authorized.

### A. Architecture compatibility review

The consolidated UI/UX baseline is **architecturally compatible in principle** with the frozen baseline, subject to the clarifications below.

| Frozen architecture invariant | Requirements affected | Reconciliation |
|---|---|---|
| Core owns electrical/domain truth; UI is projection and interaction | REQ-001–016, REQ-019 | Retain. UI may display read models and collect typed user intent; no widget/canvas state becomes authoritative equipment, topology, measurement, Control, Protection or Study state. |
| Application owns commands, services, controlled mutation and orchestration | REQ-004–007, REQ-009–016, REQ-019 | Retain explicit Application command/service boundary for all configuration, draft, commit, execution and recovery mutations. Diagnostics navigation is read-side; correction actions route through Application. |
| Universal path UI → Controller → Command → Application → Core → Event → Projection → UI | REQ-001, REQ-004–023 | Clarify that this is the engineering mutation/readback path, not a mandatory call stack for every local presentation interaction. Focus, zoom, panel layout and tool hover are UI-local presentation state; engineering changes use the canonical path. |
| Control and Protection are separate domains and execution authorities | REQ-010, REQ-014, REQ-015 | Preserve. A cross-domain trace may show configured Control/interlock context only where an explicit integration exists. It must not imply Control authorizes, owns, delays or suppresses an independent Protection trip. |
| Measurement owns typed sample semantics and trusted ingress; Application owns active project and orchestration | REQ-011, REQ-012, REQ-019, REQ-032 | Retain. UI distinguishes configured channel/binding from actual sample availability, timestamp, freshness, quality and trusted-ingress status. UI must not calculate or promote a stale/invalid sample to healthy. |
| DeviceCommand and DeviceFeedback are distinct from Control intent and ProtectionDecision | REQ-010, REQ-014 | Retain and strengthen. Show decision/intent, command acceptance/dispatch, acknowledgement and physical feedback as separate typed lifecycle states; absence of feedback must never be rendered as successful actuation. |
| Project is persistence root; canonical project data is engineering truth and SLD layout | REQ-021–023 | Separate persistence classes. User machine preferences remain outside canonical project data. Project-scoped viewport metadata is optional, versioned presentation metadata only if explicitly approved. Draft/recovery content must use existing Application/project persistence contracts and never serialize widget or QGraphicsScene objects as engineering truth. |
| Plugins extend through public contracts and Application-controlled mutation | REQ-002, REQ-004, REQ-017–020, REQ-026, REQ-033 | Add UI contribution metadata requirements to plugin contracts, but do not let plugin UI bypass Application. Keyboard/accessibility declarations are contribution metadata, not permission to own global shortcuts or global presentation state. |
| Domain-specific canvas/editor semantics remain distinct | REQ-001, REQ-005, REQ-009, REQ-015, REQ-016 | Clarify shared interaction contract as a minimum common capability/behavior contract with explicit capability declarations and domain-specific extensions, not a single implementation or identical gesture/undo model. |

**Architecture challenge conclusion:** no requirement justifies moving domain truth into UI, merging Control and Protection execution, storing UI runtime objects in the project, or making Core depend on Qt/plugins. Those would be rejected as V2-boundary violations and V3 design regressions.

### B. Duplicate and overlapping requirement reconciliation

The 33 requirements are retained as traceable IDs, but several are parent/child or cross-cutting requirements rather than independent implementation work items. Avoid building duplicate subsystems for each row.

| Overlap group | Existing requirements | Consolidated interpretation |
|---|---|---|
| Shared interaction and tool lifecycle | REQ-001, REQ-002, REQ-017, REQ-018 | One Interaction Contract. It owns active-tool lifecycle, context/focus precedence, shortcut resolution, keyboard access, selection and cancellation. Tool catalogues provide metadata; editors declare capabilities/extensions. |
| Inspector and engineering diagnostics | REQ-004, REQ-007, REQ-008, REQ-019, REQ-020 | One read-side Diagnostic/Validation presentation model with distinct typed categories and lifecycles. Inspector presents object-local details; Diagnostics Centre presents cross-project/history views; transient status/dialogs are delivery channels, not separate diagnostic stores. |
| Operational state and status | REQ-010, REQ-012, REQ-014, REQ-032 | Domain read models own their execution state. A contextual status summary may link to the detailed Control/Protection/measurement trace but must not duplicate or reinterpret domain state. |
| Workspace and view persistence | REQ-003, REQ-021, REQ-022, REQ-023, REQ-028, REQ-029 | Separate startup/navigation, user preferences, optional portable view metadata and engineering-project recovery. Do not make a monolithic session blob the owner of all four. |
| Visual accessibility and display | REQ-024, REQ-025, REQ-026, REQ-027 | One design-token/accessibility system. High contrast, color independence, focus and text scaling are baseline requirements; light/dark choice, density and DPI adaptation are presentation-profile features verified against the same tokens. |
| Workflow-specific editors | REQ-005–006, REQ-009–016 | Keep SLD, Control, Protection and Study as separate journey specifications consuming shared contracts. Do not duplicate the common shell, diagnostics or Inspector infrastructure in each discipline. |

**Requirement catalogue disposition:** keep IDs REQ-001–033 stable for traceability, but implement parent capabilities once and map each discipline-specific requirement to those capabilities. Do not interpret every requirement row as a separate service, package or plugin.

### C. Specific wording corrections and constraints

1. **REQ-001 shared interaction contract:** replace any interpretation of uniform undo/redo, gestures or canvas behavior with a capability contract. Each editor declares supported history scope and domain-specific navigation; common keyboard/focus/feedback semantics remain consistent.
2. **REQ-003 first-use workspace:** SLD-first remains the default engineering entry point, consistent with the established product direction. It must not prevent a user from opening a recent project directly into a supported discipline workspace where saved project context and authorization permit.
3. **REQ-006 connection authoring:** duplicate/crossing/snap behavior is interaction feedback; electrical validity remains Core/Application policy. Do not introduce new endpoint restrictions or shift validation timing without an approved engineering workflow decision.
4. **REQ-007/008/019/020 diagnostics:** distinguish validation result, application event, operational alarm, data-quality condition, study execution outcome and user-action feedback as typed categories. They may share presentation infrastructure but must retain category-specific severity, acknowledgement, retention and navigation rules. An operational alarm lifecycle must not be inferred from generic validation severity.
5. **REQ-010 Control monitor:** display evaluated logic, Control decisions, blocked intent and issued commands as separate states. Device feedback must come from the device/adapter feedback path, not be inferred from a successful Control cycle.
6. **REQ-011/012 Protection channels:** eligible channel discovery and provenance are read-side presentation over Measurement/Application contracts. UI selection must not create an untrusted channel or bypass measurement authorization/quality policy.
7. **REQ-014 Protection/Control trace:** make Control/interlock context conditional and optional. The canonical trace is Protection decision → Application output handling → DeviceCommand/dispatch result → DeviceFeedback where available. A Control association is included only when an explicit configured integration and provenance exist.
8. **REQ-016 Study:** study setup and result navigation must use immutable study input/result read models and preserve source revision/provenance; the UI does not become an alternate result archive.
9. **REQ-021/022 persistence:** distinguish (a) machine/user preferences, (b) workspace layout preferences, (c) per-document viewport metadata, (d) engineering project/draft data and (e) transient interaction state. Each has separate owner, schema, retention, migration and restore policy. A portable viewport inside a project is a product decision, not implied by the current .gridforge engineering schema.
10. **REQ-023 recovery:** this requirement does not itself authorize continuous autosave or a new journal. First inventory existing draft/project persistence and define recovery-point, retention, corruption and user-consent policies. Never silently commit a draft or restore an in-progress pointer gesture.
11. **REQ-024/025 accessibility:** keyboard reachability, visible focus, accessible names/descriptions and non-color state indicators are design-time requirements from Stage 1. High-contrast and font-scale profiles are not postponed until Stage 7; Stage 7 is their integrated verification.
12. **REQ-027 DPI:** avoid promising 100–200% or mixed-monitor support as a proven capability until supported platforms, Qt version and asset policy are confirmed. Treat the range as a proposed verification matrix pending product approval.
13. **REQ-033 personalization:** expert customization is optional and subordinate to safe canonical defaults. User-customized shortcuts must not override safety-critical command confirmation or platform-reserved keys.

### D. Priority and dependency corrections

**Priority review:**
- P1 remains appropriate for the core engineering workflow, clear state/authority presentation, actionable diagnostics, safe project transitions, keyboard operation for critical tasks and non-color status communication.
- P1 for full screen-reader semantic navigation of every complex canvas (REQ-018) is too broad to accept without platform/accessibility feasibility research. Keep the outcome mandatory for critical controls and object inspection; define canvas semantic navigation capability-by-capability with an accessibility design and verification plan.
- P1 for a complete crash recovery journal (REQ-023) is premature. P1 is safe recovery of already-persisted project/draft state and explicit unsaved-change handling; automatic journaling, retention policy and crash-recovery UX require a separate approved product/security decision.
- P1 for a user-selectable high-contrast profile (REQ-025) is retained as a V3 accessibility target, but acceptance depends on supported platform/Qt behavior and verified contrast rather than the existence of a theme name.
- P2 remains appropriate for configurable toolbar layouts, start/recent/sample onboarding, broad density choices and performance enhancements until user evidence establishes release-critical need.
- P3 remains appropriate for arbitrary user-defined workspace/shortcut profiles.

**Dependency corrections:**
- Accessibility and keyboard operation are cross-cutting constraints in Stage 1–6, not a final Stage 7 retrofit. Stage 7 is formal integrated verification.
- Typed diagnostics and domain status read models are shared foundations. Control and Protection UI work cannot complete independently of trustworthy Measurement/Signal and command/feedback read models.
- Project recovery depends on project/draft persistence integrity and Application lifecycle; it must not be delivered as a UI-only session feature.
- Study result navigation depends on stable study input/result provenance and source identity, not only a redesigned form.
- Status summaries depend on the relevant domain read models; do not add status fields before their authoritative source and staleness semantics are defined.
- Stage 2 workspace preference persistence may proceed independently of optional project-portable viewport metadata. The latter remains a decision gate.
- Stage 4 and Stage 5 can proceed in parallel only after shared contracts and Signal/Measurement read models are stable; Protection-to-Control trace integration needs its own explicit end-to-end acceptance scenario.

### E. Open decisions — do not silently resolve

| Decision ID | Decision required | Why evidence/approval is needed | Safe interim rule |
|---|---|---|---|
| UI-DEC-01 | Should recent projects reopen into their last discipline workspace or always start in SLD? | First-use simplicity vs expert continuity | New projects open SLD; preserve current explicit navigation for existing projects until approved |
| UI-DEC-02 | Should viewport state be machine-local, project-portable or both? | Portability, collaboration, display geometry and project schema implications | Keep user-machine viewport preferences separate; no project schema change |
| UI-DEC-03 | Which diagnostic categories require acknowledgement and retention? | Validation, alarms, events and quality warnings have different lifecycles | Do not add universal acknowledgement semantics |
| UI-DEC-04 | What crash-recovery/autosave guarantees and retention are required? | Data integrity, storage, security and operator expectations | Preserve explicit save/close behavior and existing persisted drafts; no implied silent autosave |
| UI-DEC-05 | What native accessibility target and platform matrix are supported? | Qt/platform assistive-technology support and complex canvas semantics | Apply keyboard, focus, naming and non-color principles immediately; claim no conformance until verified |
| UI-DEC-06 | What screen/DPI/monitor envelope is a supported product target? | Hardware, Qt version and icon/rendering resource constraints | Avoid compatibility claims until measured on approved matrix |
| UI-DEC-07 | Which user roles and novice/expert scenarios define the first release? | Acceptance thresholds depend on context of use | Use J01–J10 as candidate scenarios, not final personas or performance thresholds |
| UI-DEC-08 | What are the explicit Control/Protection integration trace points? | Avoid implying Control participation in every Protection output | Show only configured, provenance-backed relationships |

### F. Corrected implementation dependency graph

Corrected dependency order:
1. Stage 0: user/task requirements, runtime evidence and decision closure.
2. Stage 1: shared interaction, Inspector, diagnostics and accessibility contracts.
3. Stage 2: shell/workspace preferences and project lifecycle, alongside shared Signal/Measurement and domain-status read models.
4. Stage 3: SLD workflow.
5. Stages 4 and 5: Control and Protection after shared contracts and trusted Signal/Measurement read models; they may proceed in parallel where integration dependencies are met.
6. Stage 6: Study when immutable study input/result provenance contracts are stable.
7. Stage 7: integrated accessibility, DPI, recovery and usability evidence; accessibility remains a continuous constraint throughout implementation.
8. Stage 8: release decision and residual-risk acceptance.

This is a dependency view, not a mandatory single-thread schedule. Study may be parallelized when immutable result/provenance contracts are ready. Protection/Control integration must be validated across the actual configured signal/command/feedback path.

### G. Updated acceptance rules

- A shared contract is accepted only when each editor declares its supported capabilities, deviations and domain-specific extensions.
- A diagnostic presentation is accepted only when typed source data, lifecycle, timestamp, object identity and navigation target are preserved; rendering strings is insufficient.
- A status indicator is accepted only when its authoritative source, freshness/quality semantics and unavailable state are defined.
- A recovery feature is accepted only when it distinguishes persisted engineering draft from transient UI interaction and cannot silently convert one into the other.
- A cross-domain trace is accepted only when each stage is independently sourced and timestamped; missing stages remain explicitly unknown/unavailable, never inferred successful.
- Accessibility acceptance requires task-specific keyboard and assistive-technology evidence; source-level accessibleName calls or focus QSS alone are insufficient.
- Persistence acceptance requires restart/upgrade/invalid-state fallback evidence and proof that user preferences cannot mutate canonical project engineering data.
- No numeric task-time, completion-rate, contrast or DPI threshold is declared here without an approved baseline and target matrix.

### H. Reconciliation outcome and next action

**Outcome:** The 33 requirement IDs remain as the stable traceability catalogue, but their ownership is consolidated into shared capability groups. The baseline is compatible with the frozen architecture after the explicit clarifications in this section. No new Core authority, UI-owned domain state, plugin bypass, or Control/Protection authority merger is permitted.

**Not approved yet:** final personas, measurable usability thresholds, project-portable viewport policy, diagnostic acknowledgement semantics, autosave/crash-recovery guarantee, screen/DPI support envelope, accessibility conformance claim and final release priority of the broad canvas screen-reader requirement.

**Next:** produce the approval-ready V3 UI/UX specification package: normalized requirement catalogue, shared UI contract definitions, discipline-specific acceptance scenarios, decision log and verification matrix. It remains a proposed specification pending explicit review/approval; do not implement.


## 8I-8. Proposed V3 UI/UX specification package — normalized contracts and verification matrix (2026-11-04)

**Status:** Proposed for review; not approved implementation scope. This section operationalizes 8I-6 and 8I-7. It does not authorize changes to V2 `main`, a project schema change, a new persistence mechanism, or tests/CI as acceptance gates.

### A. Normalized capability catalogue

Keep V3-UI-REQ-001 through V3-UI-REQ-033 stable for traceability. Consolidate ownership into eight capability groups; these are capability boundaries, not a mandate to create eight packages/services/plugins.

| Capability | Scope | Requirement mapping |
|---|---|---|
| UI-CAP-01 Editor interaction | Tool lifecycle, selection, focus, navigation, shortcuts, keyboard access | REQ-001, 002, 017, 018 |
| UI-CAP-02 Contextual Inspector | Typed configuration intent, read-only values, units, provenance, validation | REQ-004, 013 |
| UI-CAP-03 Diagnostics and feedback | Typed validation/events/alarms/quality/study outcomes, lifecycle and navigation | REQ-007, 008, 019, 020 |
| UI-CAP-04 Application shell | Startup, workspace taxonomy, user preferences and customization | REQ-003, 021, 028, 029, 033 |
| UI-CAP-05 Document state and recovery | SLD lifecycle, connection authoring, viewport and safe draft recovery | REQ-005, 006, 022, 023 |
| UI-CAP-06 Domain workflow presentation | Control, Protection and Study journeys and execution/result traceability | REQ-009–016 |
| UI-CAP-07 Accessible visual system | Color-independent status, high contrast, typography, DPI and layout | REQ-024–027 |
| UI-CAP-08 Status, guidance and scale | Contextual status, task help and large-project responsiveness | REQ-030–032 |

**Ownership rule:** UI capability code coordinates presentation and typed user intent only. Existing Core/Application/domain owners remain authoritative for engineering validation, measurement quality, Control evaluation, Protection decisions, study results, command dispatch and device feedback. Reuse existing contracts; do not create duplicate backend services merely to match this catalogue.

### B. Shared editor interaction contract

Each editor publishes a versioned capability declaration. Each item is supported, unsupported or explicitly extended; unsupported behavior must not be represented by a misleading affordance.

| Contract area | Required behavior | Required editor declaration |
|---|---|---|
| Context | Identify project/document, workspace, discipline, selection and active tool | Available identity/read-model references |
| Tool lifecycle | Define activate, preview/target, apply/place, configure, validate/commit, complete and cancel as applicable | Supported states and Escape semantics |
| Selection | Deterministic single/multi-select, deselect, Inspector target and keyboard access | Selection model and unsupported operations |
| Navigation | Document pan/zoom/fit, grid/snap and coordinate behavior where meaningful | Gestures and domain-specific navigation |
| Editing | Distinguish editable, calculated, observed and historical values; route engineering edits through Application | Command route, validation owner and apply/reject behavior |
| History | Show availability and scope of undo/redo | History owner and transaction boundaries |
| Feedback | Visible outcome, failure reason and recovery route | Transient vs persistent vs blocking outcomes |
| Accessibility | Keyboard reachability, visible/restorable focus, semantic names and non-color status | Canvas/object navigation support and known limits |
| Persistence | Separate project data, persisted draft, user preference, viewport metadata and transient gesture state | Save/restore owner, schema and fallback |
| Extension | Plugin tools/panels declare identity, shortcut and accessibility metadata | Public contribution contract/version |

The contract standardizes user expectations, not rendering technology, electrical semantics, gestures or history implementation. SLD, Ladder, Protection and Study surfaces remain distinct domain editors.

### C. Inspector, diagnostics and status contracts

**Inspector**
- Show object identity/type, then task-oriented editable configuration.
- Derive units, bases, ranges and enumerations from authoritative metadata.
- Visually distinguish editable configuration, calculated values, live measurements and historical values.
- Show source/provenance for linked measurements and runtime observations.
- Route edits through typed Application commands; distinguish pending, accepted, rejected and unapplied states.
- Do not represent a widget value as committed engineering state before the owning command/application confirms it.

**Diagnostics**
- Preserve category, stable code/identity where available, severity, source/domain, timestamp, project/session context, affected object/channel, explanation and navigation target.
- Keep validation, application events, operational alarms, data-quality conditions, study outcomes and user-action feedback semantically distinct, even if one centre renders them.
- Acknowledgement, shelving, clearing and retention are category-specific. Do not add a universal acknowledgement action until policy is approved.
- Grouping/filtering must not erase individual source identity or lifecycle.
- Correction is an Application command; opening a diagnostic is read-side navigation.
- Modal dialogs are for explicit decisions/blocking conditions, not the default error transport.

**Status**
- Every status has an authoritative source, timestamp/freshness rule and explicit unknown/unavailable state.
- Status is a summary/navigation affordance, not a duplicate execution-state store.
- Configuration is not sample health; cycle completion is not actuation; command dispatch is not feedback; absence of an error is not proof of success.
- Measurement quality, Protection decision, Control intent, DeviceCommand dispatch/acknowledgement and DeviceFeedback remain separate typed states.

### D. Persistence and recovery classification

| State class | Examples | Owner / restore rule |
|---|---|---|
| Canonical engineering project | Equipment, terminals, topology, committed configuration and approved SLD layout | Existing project/Core persistence; restore as engineering truth only through validated loading |
| Persisted engineering draft | Explicitly persisted uncommitted draft | Existing Application/project draft contract; restore as draft, never silently commit |
| User/machine preferences | Window geometry, theme, font scale, panel sizes, shortcuts | User settings; restore locally with safe defaults |
| Workspace presentation | Active workspace, visible panels, splitter arrangement | User settings unless a future project policy is approved |
| Per-document viewport | Centre, zoom, rotation, grid/snap visibility | Policy unresolved; machine-local interim behavior; no canonical project schema change |
| Transient interaction | Pointer drag, hover, preview and in-progress connector gesture | Editor runtime only; cancel on shutdown/restart, never restore as engineering truth |

Recovery acceptance must prove these classes remain separate, malformed/obsolete preferences fall back safely, and existing Save/Discard/Cancel safeguards remain intact. This specification does not mandate autosave, journaling, recovery intervals or retention periods.

### E. Discipline-specific candidate acceptance scenarios

| Scenario | Action | Required observable result | Authority invariant |
|---|---|---|---|
| UI-ACC-SLD-01 | Place multiple equipment items, select/configure each, connect and commit | Earlier items remain visible; selection target is clear; preview/draft/commit are distinct | Only successful Application/Core commit changes authoritative network |
| UI-ACC-SLD-02 | Attempt invalid/incomplete connection or commit | Affected object/terminal, typed reason and correction route are shown; valid draft remains recoverable | UI does not invent compatibility or bypass validation |
| UI-ACC-SLD-03 | Save/reopen project with committed network and persisted draft | Both restore separately; transient gesture/preview does not | Draft is never silently promoted to topology |
| UI-ACC-CTL-01 | Discover/bind a signal, configure logic/interlock/action and inspect cycle | Direction/type/provenance, evaluated logic, blocked intent and command are distinguishable | Cycle completion is not physical actuation |
| UI-ACC-CTL-02 | Block action or delay/omit device feedback | Block reason, dispatch and feedback states are separately visible; absent feedback remains unknown | No inferred successful operation |
| UI-ACC-PROT-01 | Discover CT/PT/CVT channels and bind relay inputs | Source instrument/terminal, quantity/unit, timestamp/freshness and quality are inspectable | UI cannot manufacture trusted samples or bypass ingress policy |
| UI-ACC-PROT-02 | Evaluate with stale/invalid/unavailable measurement | Fail-closed reason and affected input are explicit | Protection authority remains domain-owned and independent of UI/Control |
| UI-ACC-PROT-03 | Trace decision through output handling, command and feedback | Each stage is independently sourced/timestamped; missing stage is unknown | No fabricated acknowledgement/actuation; Control context only when explicitly configured |
| UI-ACC-STUDY-01 | Configure/run study, inspect result and navigate to source | Relevant inputs, run state, immutable input/result identity and source revision are visible | UI does not become alternate StudyResult authority |
| UI-ACC-DIAG-01 | Open diagnostics from supported categories and navigate to source | Category lifecycle and severity survive filtering/navigation | No universal acknowledgement semantics |
| UI-ACC-KEY-01 | Complete nominated critical tasks by keyboard | Focus, shortcut precedence, cancellation and text-entry behavior are deterministic | Canvas shortcuts do not steal text input or platform-reserved keys |
| UI-ACC-REC-01 | Restart with valid/missing/malformed preferences and persisted draft | Safe fallback; project remains intact; draft remains draft | Preferences cannot mutate canonical project data |

These are candidate cases, not release gates until roles, project fixtures, platform matrix and critical-task subset are approved.

### F. Verification and evidence matrix

| ID | Evidence method | Required evidence | Pass condition |
|---|---|---|---|
| UI-VER-01 | Source/architecture inspection | Ownership/dependency map | No Core→Qt/UI/plugin dependency; engineering mutations use Application-owned routes |
| UI-VER-02 | Runtime walkthrough | Approved journey recordings/screenshots and observations | Observed workflow matches scenario; deviations recorded |
| UI-VER-03 | State-transition inspection | SLD, Control, Protection and Study state traces | Draft/commit, intent/decision/command/feedback and study input/result are not conflated |
| UI-VER-04 | Diagnostic inspection | Representative typed records and navigation | Provenance/lifecycle fields survive presentation |
| UI-VER-05 | Persistence/restart walkthrough | Project/preference fixtures and migration/fallback notes | Correct state class restores; invalid settings fail safely |
| UI-VER-06 | Keyboard/accessibility walkthrough | Task scripts, focus maps and assistive-technology observations | Approved critical tasks do not rely solely on pointer/color; limits documented |
| UI-VER-07 | Display walkthrough | Approved OS/Qt/DPI/monitor matrix | No clipped critical controls or unreadable annotations within approved envelope |
| UI-VER-08 | Performance observation | Representative project sizes and latency/render traces | Responsive against baseline-derived, approved targets |
| UI-VER-09 | Domain trace inspection | Signal, Protection/Control, command/feedback and study provenance | Every displayed state has authoritative source; missing data explicit |
| UI-VER-10 | User evaluation | Role-based task completion, error/recovery observations | Approved usability targets met; thresholds derived from baseline |

No numeric latency, task-time, completion-rate, contrast, DPI or conformance claim is set here without an approved baseline and target matrix. These are source/runtime/design/user-evaluation evidence methods, not a request to add tests or CI as acceptance gates.

### G. Approval gates and unresolved decisions

| Gate | Approval required | Decision references | Interim constraint |
|---|---|---|---|
| UI-GATE-01 Context of use | Roles, novice/expert balance, critical tasks, representative project sizes | UI-DEC-07 | J01–J10 remain candidate journeys |
| UI-GATE-02 Project/session | Recent-project workspace, viewport portability, autosave/recovery guarantees | UI-DEC-01, 02, 04 | New projects open SLD; no schema change or new autosave guarantee |
| UI-GATE-03 Diagnostics | Category-specific acknowledgement, retention and clearing | UI-DEC-03 | No universal acknowledgement |
| UI-GATE-04 Accessibility/platform | OS/Qt matrix, native accessibility target, complex-canvas strategy | UI-DEC-05 | Apply foundational practices; make no conformance claim |
| UI-GATE-05 Display/performance | DPI/monitor envelope and representative performance targets | UI-DEC-06 | No unverified compatibility/performance claim |
| UI-GATE-06 Cross-domain trace | Explicit Protection/Control integration and feedback contracts | UI-DEC-08 | Show configured, provenance-backed relationships only |
| UI-GATE-07 Scope/priority | Final P1/P2/P3 release scope and acceptance subset | All gates | No implementation authorization until approved |

### H. Review checklist and disposition

Reviewers should mark each item **Approve**, **Revise** or **Defer**, with rationale:
1. Does capability ownership preserve Core/Application/domain boundaries?
2. Does the shared editor contract preserve distinct canvas semantics?
3. Do Inspector/diagnostics/status prevent configuration, measurement, decision, command and feedback from being conflated?
4. Are persistence classes and restore rules correct?
5. Do candidate scenarios cover critical engineering workflows and failure paths?
6. Are evidence methods feasible on the intended V3 branch/platforms?
7. Are decisions assigned to accountable owners and closure points?
8. Is the proposed priority/scope appropriate for the first V3 delivery?

**Disposition:** The normalized catalogue, interaction contract, Inspector/diagnostics/status contracts, persistence classification, candidate scenarios and evidence model are proposed and ready for review. Personas, numeric thresholds, autosave/recovery guarantees, viewport portability, diagnostic acknowledgement, platform/DPI envelope, accessibility conformance and final release scope remain unapproved. No source change, migration, redesign, schema change, persistence mechanism or test/CI gate is authorized. Next step is focused review and closure/assignment of the approval gates, followed by a specification freeze before implementation work packages are created.
