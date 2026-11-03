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
