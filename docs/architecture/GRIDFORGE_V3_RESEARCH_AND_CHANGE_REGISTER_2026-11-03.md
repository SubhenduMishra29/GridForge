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
