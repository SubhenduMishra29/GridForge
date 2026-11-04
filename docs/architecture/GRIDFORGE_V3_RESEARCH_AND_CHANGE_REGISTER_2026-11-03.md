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


## 8I-9. V3 source-branch provenance and specification traceability baseline (2026-11-04)

**Purpose:** Verify whether a designated V3 implementation branch exists before asserting source-to-specification traceability. Inspect the current V2 `main` snapshot only as a legacy baseline, and distinguish source-confirmed capability, partial evidence, unverified integration and V3 implementation status.

### A. Branch provenance result

The repository branch search for `v3` returned:
- `research/gridforge-v3-architecture-register` — the V3 research/specification branch.
- `fix/palette-symbol-painter-geometry-overloads-main-sync-v3` — an older implementation/fix branch.

The latter was inspected at head `b9e95259419c204d598360cbad34db8b456388b7`. Comparing it with `main` showed:
- `main` head at inspection: `b420b768c29629adf690dfff6f71d935b5f5640a`.
- The fix branch is **529 commits behind** `main` and **one commit ahead**.
- Its one ahead commit changes only `ui/equipment/symbol/palette_symbol_adapter.py`.
- The branch therefore does not represent a current V3 implementation baseline.

The current `main` head was also inspected and contains later engineering/UI work. However, `main` is the V2 integration baseline and must not be relabelled as V3. No dedicated, current, named V3 implementation branch was identified in this branch search.

**Provenance decision:** V3 source-to-specification conformance is **blocked pending designation of the intended V3 source branch/ref**. Do not use the stale `main-sync-v3` branch as a proxy. Do not treat current V2 source observations as proof that a V3 requirement is implemented or absent.

### B. Legacy V2 source baseline inspected

The following current-`main` files were fetched at commit `b420b768c29629adf690dfff6f71d935b5f5640a` and inspected selectively:
- `main.py`, `ui/main_window.py`
- `ui/editors/common/editor_host.py`, `ui/editors/common/tool_shelf.py`
- `ui/editors/sld/sld_editor.py`, `ui/editors/control/control_editor.py`, `ui/editors/protection/protection_editor.py`, `ui/editors/study/study_editor.py`
- `ui/interaction/interaction_session.py`, `ui/tools/tool_shortcuts.py`
- `ui/plugins/status_plugin.py`, `ui/panels/messages_panel.py`, `ui/panels/engineering_parameter_editor.py`
- `ui/control/control_workspace.py`, `ui/control/control_inspector.py`, `ui/control/control_status_bar.py`
- `ui/protection/protection_workspace.py`, `ui/protection/protection_presentation.py`
- `ui/workspace/workspace_manager.py`, `ui/workspace/workspace_state.py`, `ui/workspace/workspace_layout.py`, `ui/workspace/viewport_state.py`

Source-confirmed observations from that baseline:
1. `main.py` composes distinct SLD, Control, Protection and Study surfaces; the default workspace manager is configured with SLD as its default. This supports the existing SLD-first product direction but does not prove a first-launch/recent-project UX journey.
2. `MainWindow` is a host surface and delegates workspace realization/orchestration. The shared `EngineeringEditorHost` supplies editor hosting/context, but does not make all discipline editors use the same interaction implementation.
3. `ToolShelf` exposes active tool state, labels, shortcut hints and fallback glyph behavior. `ToolShortcutRegistry` exists as a semantic registry, but its presence alone does not prove one focus-aware runtime dispatcher or complete integration with QAction/menu shortcuts.
4. `InteractionSession` explicitly owns transient UI selection/tool/connection/drag/preview/intent state and clears it on close. This is consistent with the persistence separation principle; it is not proof that persisted engineering drafts are recoverable across process restart.
5. SLD editor source explicitly initializes Explorer, Inspector, Diagnostics/Messages and Tool Settings as hidden/contextual regions. Its Messages region is separate from the status strip.
6. `MessagesPanelWidget` stores validation and event messages as strings and renders them into one `QListWidget`. This does not satisfy the proposed typed, object-linked diagnostic record contract.
7. `StatusPlugin` projects tool, selection, coordinates, project dirty state, validation summary and workspace into status fields. It is not itself the source of detailed measurement quality, Protection execution or device feedback state.
8. Control has a dedicated Ladder view and Control-specific interaction/status. Its current status projection reports basic project/rung/component context; the inspected excerpt does not establish the complete cycle-decision-blocked-action-command-feedback trace.
9. Protection builds a distinct graphics surface and reads Protection and configuration projections. Configured input channel IDs are rendered into channel/input nodes; the inspected path does not establish discovery of all eligible unbound Measurement channels or display of sample freshness/quality/provenance in the channel node.
10. `EngineeringParameterEditor` creates typed configuration intent and submits through its Application reference. This is a useful existing pattern, not evidence that every Inspector or Protection configuration path conforms.
11. `ViewportState` has toolkit-independent fields and `to_dict/from_dict` serialization. This alone does not establish persistence ownership, per-document identity, user preference separation or restart restoration.
12. The inspected `WorkspaceManager`, `WorkspaceState` and `WorkspaceLayout` provide logical workspace state/models. Their existence alone does not prove durable user layout persistence or migration.
13. Discipline editors expose Diagnostics/Status regions with differing composition and visibility. A shared region name is not proof of a common diagnostic data model or lifecycle.
14. No runtime walkthrough was performed for this traceability pass. These are source observations only; visual behavior, focus arbitration, accessibility, restart behavior and live domain traces remain runtime-unverified.

### C. Requirement-to-source traceability disposition

The following disposition is **against the inspected V2 baseline only**, not against V3 implementation. “Partial” means a related source mechanism exists but the complete requirement is not evidenced. “Unverified” means the selected source inspection did not establish the required behavior; it is not a claim of nonexistence.

| Requirement family | V2 baseline evidence | Traceability disposition | V3 conclusion |
|---|---|---|---|
| REQ-001–002 shared editor/tool interaction | Editor host, tool shelf, separate editor surfaces and interaction runtimes | Partial | Retain shared capability contract; inspect actual V3 editor adapters and focus behavior |
| REQ-003 shell/first use | SLD default and contextual SLD panels | Partial | First-use and recent-project journey still needs V3 evidence |
| REQ-004 Inspector | Typed EngineeringParameterEditor pattern and domain-specific inspectors | Partial | Audit all editable/read-only/provenance states and command routes |
| REQ-005–006 SLD lifecycle/connections | Separate transient InteractionSession, SLD document/editor and draft/projection mechanisms | Partial | Verify complete preview→draft→configure→connect→validate→commit/recovery path on V3 |
| REQ-007–008, 019–020 diagnostics | Messages panel combines validation/event strings; status and modal feedback are separate presentation paths | Gap against proposed typed contract | V3 must demonstrate typed categories, source identity, lifecycle and safe navigation |
| REQ-009–010 Control | Ladder workspace, Inspector, status projection | Partial | Cycle decision/blocked intent/command/feedback trace not established |
| REQ-011–012 Protection channels | Configured channel IDs projected from relay configuration | Partial | Eligible unbound-channel discovery, measurement provenance and runtime quality remain unverified |
| REQ-013–015 Protection workflow/trace | Protection workspace, relay/configuration projection and distinct canvas | Partial | Configuration completeness, commissioning journey and independently sourced output/feedback trace require V3 evidence |
| REQ-016 Study | Study editor and Study workspace composition | Partial | Study-specific progressive disclosure and immutable result/source provenance require V3 evidence |
| REQ-017–018 keyboard/accessibility | Shortcut registry, tool shortcut hints, some accessible names in SLD panel controls | Partial/unverified | Focus-aware dispatcher, complete critical-task keyboard path and assistive-technology semantics require direct V3 evidence |
| REQ-021 workspace/user preference persistence | Logical workspace state and QMainWindow host | Unverified | Identify actual V3 preference owner, serialization, migration and restart path |
| REQ-022 viewport persistence | Serializable `ViewportState` model | Partial | Prove document identity, save owner and restore integration |
| REQ-023 draft/session recovery | Transient InteractionSession clears on close; separate draft persistence mechanisms exist in baseline | Partial | Verify project draft recovery independently from transient gestures and process restart |
| REQ-024–027 visual accessibility/display | Theme/style and Qt widget composition exist | Unverified for contrast, high-contrast profile, font scaling and DPI matrix | Require measured evidence on approved V3 platform matrix |
| REQ-028–030 start/help/customization | No complete user journey established by selected files | Unverified | Inspect designated V3 start/recent/help/customization surfaces |
| REQ-031–032 performance/status | StatusPlugin has basic authoritative projection; no approved performance baseline in this pass | Partial/unverified | Define source/freshness and baseline-derived performance evidence |
| REQ-033 expert personalization | Tool and workspace models exist | Unverified for persisted user-defined profiles | Keep optional until V3 preference model and safe shortcut policy are evidenced |

### D. Confirmed specification clarifications arising from source trace

1. **Do not equate shared hosting with shared interaction.** The common editor host and distinct Control/Protection surfaces confirm that V3 should standardize the contract and capability declarations, not force a single canvas class.
2. **Do not equate a serializable model with persistence.** `ViewportState.to_dict/from_dict` and workspace dataclasses require a real owner, storage path, identity, migration and restore evidence before REQ-021/022 can be marked implemented.
3. **Do not equate status text with diagnostics.** The existing string-based Messages panel and compact status fields motivate a typed read-side diagnostic model with separate category lifecycles.
4. **Do not equate configured channels with live measurements.** Protection's configured input channel projection is not proof of channel discovery, trusted sample ingress, freshness or quality.
5. **Do not equate a Control cycle with actuation.** Basic Control status must remain distinct from blocked intent, command dispatch/acknowledgement and DeviceFeedback.
6. **Do not equate shortcut metadata with keyboard routing.** Registry, menu QAction shortcuts and editor key handling must be traced into one effective focus/context policy before acceptance.
7. **Do not infer runtime UX from source composition.** Hidden panels, visible panels, splitter behavior, focus, accessibility and error navigation require a runtime walkthrough.

### E. Required next audit inputs and bounded work plan

**Required input:** identify the exact V3 implementation repository/branch/ref (and commit SHA if a pinned snapshot is intended). If V3 is not yet branched, explicitly designate the intended development baseline and confirm whether the audit should treat it as a new branch from current `main` or a different implementation repository. Do not create or move branches on the user's behalf.

After designation:
1. Pin the V3 source commit and capture its branch ancestry/relationship to V2 `main`.
2. Map each V3-UI-REQ and UI-CAP to exact source modules, classes, command/read-model contracts and plugin contribution points.
3. Mark each requirement **Implemented / Partial / Missing / Not applicable / Runtime-unverified**, with source references and evidence type.
4. Trace each UI-ACC scenario through the complete path: input → UI/controller → Application command/read model → Core/domain result/event → projection → user-visible outcome.
5. Inspect affected `__init__.py` exports and Qt boundary only where relevant to a finding; do not widen into unrelated architecture refactoring.
6. Record defects as findings with severity, reproducible evidence or explicit static-only status, owner/dependency and closure evidence.
7. Produce an ordered implementation work-package map only after traceability is complete and approval gates are addressed.

**Scope boundary:** no source files were modified in this pass. No V2 architecture or implementation was changed. No tests or CI were run or used as acceptance gates. The branch-provenance blocker is the current result; V2 source evidence is a reference baseline only.


## 8I-10. UI/UX specification approval and implementation hand-off controls (2026-11-04)

**Purpose:** Convert the open UI-GATE-01..07 list into an approval-ready decision register and define the minimum evidence needed before implementation work packages are authorized. This is a process/control specification; it does not approve unresolved product decisions or authorize implementation.

### A. Gate disposition model

Each gate must have one recorded disposition:
- **Approved:** decision is explicit, rationale is recorded, accountable approver is identified, and required evidence is attached or referenced.
- **Approved with constraints:** accepted only within stated limits; constraints become traceable requirements and acceptance conditions.
- **Deferred:** no implementation may rely on unresolved behavior; a named owner and revisit trigger/date are required.
- **Rejected:** proposal is declined with rationale; affected requirements and scenarios are revised.
- **Blocked:** required source, domain contract, platform decision or evidence is unavailable.

A gate cannot be marked Approved solely because related source code exists. Source presence, runtime behavior, domain correctness and user acceptance are separate evidence classes. Silence or a “next” instruction is not approval.

### B. Seven gate closure records

| Gate | Decisions that must be explicit | Minimum closure evidence | Consequence while open |
|---|---|---|---|
| UI-GATE-01 Context of use | Target roles; novice/expert balance; critical tasks; project-size and operational context | Approved role/task matrix; representative project fixtures; prioritized critical-task list | Candidate journeys only; no final usability thresholds |
| UI-GATE-02 Project/session | Start/recent-project behavior; canonical project vs preferences vs viewport ownership; draft/autosave/recovery guarantees; portability and migration | State ownership matrix; save/restore lifecycle; failure/recovery policy; migration/fallback decision | No new persistence/schema/autosave guarantee; canonical project scope unchanged |
| UI-GATE-03 Diagnostics | Category taxonomy; severity/source identity; acknowledge, suppress, clear, retain and navigate semantics per category | Typed diagnostic contract; category lifecycle table; representative SLD/Control/Protection/Study records | No universal acknowledgement/clear operation |
| UI-GATE-04 Accessibility/platform | Supported OS/Qt versions; native accessibility target; keyboard-critical tasks; canvas semantic/assistive strategy; conformance target | Approved platform matrix; focus/keyboard map; accessible-name/role strategy; assistive-technology evaluation plan and evidence | Foundational practices only; no blanket conformance claim |
| UI-GATE-05 Display/performance | DPI/mixed-monitor envelope; scaling; representative project sizes; performance measures and targets | Display matrix; representative workloads; baseline capture; approved latency/rendering targets and method | No numeric performance or compatibility claim |
| UI-GATE-06 Cross-domain trace | Measurement → Protection decision → Control/interlock context (where configured) → command → acknowledgement/feedback; stale/missing-data behavior | Domain sequence diagrams; typed read-model contracts; provenance/freshness/quality rules; normal, blocked and unavailable-data examples | Show configured, provenance-backed relationships only; never synthesize acknowledgement or feedback |
| UI-GATE-07 Scope/priority | Release scope; P1/P2/P3 classification; mandatory scenarios; exclusions; implementation-start authorization | Signed requirement disposition; scenario map; dependency/owner map; explicit implementation authorization | Research/specification only; no implementation package approved |

### C. Required decision record fields

Every gate decision must capture:
1. Gate ID and decision ID.
2. Decision statement and alternatives considered.
3. Disposition from section A.
4. Rationale and engineering/user impact.
5. Approver role and accountable owner (not inferred).
6. Affected requirement IDs, capability IDs, scenarios and domain contracts.
7. Constraints, exclusions and unresolved dependencies.
8. Evidence references and evidence class (source, runtime, domain, platform, performance or user evaluation).
9. Effective specification/register revision.
10. Revisit trigger for deferred or conditional decisions.

### D. Implementation work-package template

This template does not authorize implementation. Once the V3 source ref is designated and applicable gates are approved, each package must contain:

| Field | Required content |
|---|---|
| Package ID/title | Stable identifier and bounded outcome |
| User/task outcome | Observable engineering workflow improvement |
| Traceability | Requirement → capability → acceptance scenario → finding |
| Ownership | UI/controller, Application command/service, Core/domain owner, projection/read model, plugin contract as applicable |
| Current-state evidence | Exact V3 ref, file/class/symbol, source evidence and runtime status |
| Change boundary | Expected files/modules and explicit non-goals |
| Domain invariants | Authoritative owner, mutation path, lifecycle and failure semantics |
| Dependencies | Prior packages, unresolved decisions, public contracts and migrations |
| Acceptance evidence | Scenario walkthrough, state/provenance trace, accessibility/display/performance evidence as applicable |
| Regression surface | Adjacent editor/domain/plugin workflows requiring inspection; not an automatic test/CI mandate |
| Closure criteria | Observable pass conditions, register updates and reviewer sign-off |
| Risk/rollback | Failure impact, safe fallback and reversibility |

Packages must be vertically coherent and avoid duplicate managers, event buses, domain services or plugin registries. UI work must not move engineering truth into widgets or canvas objects. Cross-domain packages must preserve separate Protection and Control execution authority and explicit signal/command/feedback provenance.

### E. Specification review sequence

1. Review capability ownership and interaction contracts before visual styling proposals.
2. Resolve state ownership and diagnostics lifecycle before designing save/recovery and notification affordances.
3. Resolve measurement/Protection/Control provenance before designing live status indicators.
4. Approve roles, critical tasks and representative project fixtures before setting usability/performance thresholds.
5. Approve platform/accessibility envelope before compatibility or conformance claims.
6. Close or explicitly defer each gate with an owner and constraint.
7. Freeze the approved specification revision and only then derive implementation packages against the designated V3 source ref.

### F. Current disposition

- UI-GATE-01..07: **Open — decision/approval evidence not supplied.**
- UI-ACC-SLD-01..03, UI-ACC-CTL-01..02, UI-ACC-PROT-01..03, UI-ACC-STUDY-01, UI-ACC-DIAG-01, UI-ACC-KEY-01 and UI-ACC-REC-01: **Candidate scenarios — not approved release acceptance criteria.**
- V3 source-to-spec traceability: **Blocked — exact implementation repository/branch/ref remains undesignated.**
- Implementation packages: **Not authorized.**
- V2 main: remains legacy comparison baseline, not a substitute V3 implementation source.

**Next bounded activity:** obtain the intended V3 source ref and product/domain owners' gate decisions. Until then, further source-to-spec claims or implementation prioritization would be speculative. No source implementation files were changed; only this research register is updated. No tests or CI were run.


## 8I-11. Proposed typed engineering diagnostics contract (2026-11-04)

**Purpose:** Provide a reviewable candidate contract for UI-GATE-03. The contract standardizes how diagnostic information is identified, transported and presented without transferring acknowledgement, clearing, alarm-management or engineering decision authority into the UI. This is a proposal for V3 review, not an approved schema or implementation directive.

### A. Design decision: common envelope, category-owned lifecycle

Adopt one **typed diagnostic read-model envelope** for cross-workspace presentation, backed by category-specific payloads and lifecycle policies.

The shared envelope is a presentation/interoperability contract. It must not become a universal diagnostic engine, event bus, alarm manager or mutation API. The originating domain/service remains authoritative for determining whether a condition exists and its severity; deciding whether it is active, cleared, superseded, inhibited or otherwise resolved; defining whether acknowledgement, shelving, suppression or operator disposition is meaningful; authorizing and recording state-changing operator actions; and retaining the authoritative event/history record.

The UI consumes read models and submits explicitly typed intent only through the owning Application service/command. It never changes a diagnostic record locally to imply domain acknowledgement or clearance.

### B. Candidate diagnostic categories

| Category | Meaning | Authoritative owner (candidate) | Lifecycle authority |
|---|---|---|---|
| Engineering validation | Invalid/incomplete equipment, terminal, topology, configuration or study input | Owning Core validator/domain service, surfaced by Application | Validation run/result owner; re-evaluated against relevant revision |
| Protection operation/diagnostic | Relay function evaluation, pickup/trip decision, blocked evaluation, supervision or Protection subsystem fault | Protection domain/runtime | Protection policy; operation records are historical facts, not generic dismissible messages |
| Control execution diagnostic | Logic evaluation, interlock, blocked action, cycle fault or execution diagnostic | Control domain/runtime | Control execution/cycle policy; a blocked action is not an alarm acknowledgement |
| Alarm/event/SOE | Process alarm, state transition, sequence-of-events or operator event | Signal/alarm/event subsystem and configured alarm policy | Alarm-management policy; acknowledgement and shelving only where supported |
| Measurement/instrumentation quality | Stale, invalid, uncertain, out-of-range, unavailable, bad-quality or calibration/provenance issue | Signal and Measurement infrastructure | Measurement quality/source lifecycle; UI cannot promote bad data to good |
| Command/actuation/feedback | Dispatch, acceptance/rejection, timeout, device feedback mismatch or unavailable feedback | Application command orchestration and device/actuation integration; device feedback source | Command lifecycle and device-feedback authority; never infer acknowledgement from dispatch |
| Application/platform diagnostic | Persistence, import/export, plugin load, communication transport or recoverable application fault | Owning Application service/platform adapter | Owning service recovery and operation policy |
| User guidance/information | Non-fault contextual information or workflow hint | Producing workflow/service | Usually ephemeral; no alarm semantics unless explicitly classified otherwise |

Categories must not be collapsed merely because they share severity colors or appear in one panel. Alarm, Protection operation, Control block and engineering validation are not interchangeable.

### C. Candidate common envelope

| Field | Semantics | Requiredness / constraints |
|---|---|---|
| diagnostic_id | Stable identifier for this diagnostic instance/read-model item | Required; unique within owning authority identity namespace |
| category | Closed, versioned category discriminator | Required; one of approved categories |
| type_code | Stable machine-readable condition code | Required; not localized display text |
| title / summary | Localizable concise human-readable description | Required for presentation; not used as identity |
| severity | Domain-supplied severity/priority classification | Required where category defines severity; no UI-inferred escalation |
| lifecycle_state | Category-specific state projected into a typed common state vocabulary | Required; source remains authoritative |
| source | Originating subsystem/service/device identity | Required; stable source reference where available |
| subject_refs | Typed references to affected project objects, equipment, terminal, channel, relay, control element, study or command | Empty only when genuinely not attributable |
| project_revision | Canonical project/configuration revision relevant to evaluation | Required when diagnostic depends on project state |
| topology_revision | Physical topology revision where relevant | Optional; must not substitute for instrumentation/configuration revisions |
| domain_state_revision | Relevant Protection, Control, signal/measurement or study-state revision | Required when that domain revision affects interpretation |
| observed_at | Time condition was observed by authoritative producer | Required when time-based; preserve source clock semantics |
| recorded_at | Time accepted/recorded by receiving service | Required; do not overwrite observed_at |
| last_changed_at | Time of most recent authoritative lifecycle transition | Required when lifecycle is stateful |
| correlation_id | Links related evaluation, cycle, trip, command, event or study execution | Optional but strongly preferred for traceability |
| provenance | Producer, acquisition path, input/sample references and processing lineage | Required for measurement- and decision-derived items |
| quality_context | Measurement quality/freshness or source availability when relevant | Conditional; preserve unknown/unavailable distinctly |
| evidence_refs | References to validation details, measurements, relay function, control cycle, command, feedback or study result | Optional; typed and resolvable, not opaque UI-only strings |
| available_actions | Explicit action capabilities returned by the owner | Required as empty or populated set; never inferred from category/severity |
| schema_version | Read-model contract version | Required for evolution and compatibility |

The envelope is a read model. It does not itself authorize a command. Any action must revalidate current state and authorization at the owning Application boundary; a stale diagnostic card is not a valid command precondition.

### D. Lifecycle and operator-action constraints

| Category | Candidate lifecycle | Permitted UI behavior | Prohibited inference |
|---|---|---|---|
| Engineering validation | Current / superseded / resolved by revalidation | Navigate to object/input; rerun validation through owning workflow | Acknowledge does not make invalid configuration valid |
| Protection operation | Evaluated / picked up / operated / blocked / reset or superseded as defined by Protection | Inspect function, inputs, decision and associated equipment; navigate to trace | Dismissal cannot erase a trip/operation fact or reset relay state |
| Control execution | Evaluated / blocked / executed / failed / superseded by next cycle | Inspect rung/element, inputs, blocked-action reason and cycle trace | Acknowledging a block cannot force execution or bypass interlocks |
| Alarm/event/SOE | Policy-defined active / acknowledged / returned-to-normal / shelved / suppressed / archived states as applicable | Expose only actions granted by alarm policy and role | Returned-to-normal is not acknowledged; shelving is not clearance |
| Measurement quality | Good / uncertain / bad / stale / unavailable / not-yet-established as defined by signal contract | Show value, unit, source, timestamp, quality and calibration/provenance context | Never silently coerce unknown, stale or bad quality to good |
| Command/actuation/feedback | Created / dispatched / accepted or rejected / timed out / completed / feedback-confirmed or mismatch, according to command contract | Show each independently sourced transition and correlation | Dispatch is not acceptance; acceptance is not physical operation; timeout is not proof of failure or success |
| Application/platform | Active / retrying / recovered / failed / superseded according to owning service | Show recovery guidance and supported retry/navigation actions | UI dismissal cannot mark service recovered |
| User guidance | Presented / expired / dismissed | Allow local dismissal where harmless | Do not apply alarm acknowledgement semantics |

These are candidate lifecycle labels, not a mandate that every category implement every state. Each owner must define its valid transition graph and terminal/retention semantics.

### E. Presentation and interaction contract

1. Provide a unified Diagnostics workspace/panel with category filters, severity/source filters where meaningful, search, stable sorting and direct navigation to a resolvable subject.
2. Preserve category identity in every row/card; never rely on color alone.
3. Show observed time and recorded time distinctly when latency or clock provenance matters.
4. Provide a detail view with source, subject, revisions, provenance, correlation and evidence references.
5. Show stale/unavailable/unknown states explicitly. Do not render missing data as zero, healthy or acknowledged.
6. Make action controls capability-driven from the owner; hide or disable unsupported actions with a reason where useful.
7. Separate transient workflow feedback (toast/status) from persistent diagnostic records and alarm/event history.
8. Group related items by correlation/evaluation/command only where this does not hide individual records or chronology.
9. Support navigation from a diagnostic to the relevant editor, object, channel, relay function, rung, command or study result when the reference is valid.
10. Do not silently clear, delete, acknowledge, shelve or suppress records when a panel is closed, a filter changes or a workspace is switched.

### F. Boundary and data-flow contract

Candidate flow:

`Domain / Application owner → typed diagnostic read model → projection/query service → UI presentation`

For an operator action:

`UI intent → owning controller → Application command/service → owner validation/authorization → authoritative state transition → event/read-model refresh → UI`

Constraints:
- Core/domain code must not depend on Qt widgets, graphics items or UI plugin implementations.
- A plugin may contribute a diagnostic producer or presentation adapter only through a public contract; it must not create a parallel global diagnostic store or event bus.
- The shared envelope may be consumed by multiple workspaces, but each workspace may provide domain-specific detail and action affordances.
- Historical event storage and alarm lifecycle remain separate from transient UI notification state.
- Diagnostic identity and correlation must survive projection refresh; localized title text is not an identifier.
- Revision dimensions remain distinct: topology, equipment/instrumentation configuration, Protection configuration/runtime, Control configuration/runtime, measurement sample sequence and study execution are not one generic project revision.

### G. Candidate acceptance scenarios for UI-GATE-03

| Scenario | Setup/action | Expected evidence |
|---|---|---|
| UI-ACC-DIAG-02 Mixed categories | Present validation error, Protection operation, Control block, bad-quality measurement and alarm/event together | Category, source, severity and lifecycle remain distinguishable; no universal acknowledgement action appears |
| UI-ACC-DIAG-03 Revision supersession | Change relevant configuration after a validation or evaluation result | Prior result is marked superseded/stale by its owner; UI does not silently present it as current |
| UI-ACC-DIAG-04 Measurement provenance | Open a Protection/Control diagnostic derived from a measurement | Source instrument/channel, sample time, quality and provenance can be traced; unavailable data stays explicit |
| UI-ACC-DIAG-05 Command trace | Follow a Control/Protection output through dispatch and device feedback | Dispatch, acceptance, physical feedback and mismatch/timeout are separate sourced facts |
| UI-ACC-DIAG-06 Action authorization | Attempt an action from a stale diagnostic or a category without that capability | Owner revalidates; unsupported or unauthorized action is not executed and UI reports authoritative outcome |
| UI-ACC-DIAG-07 Navigation | Navigate from mixed diagnostics to affected object/editor | Correct workspace/object opens where resolvable; unresolved references remain identifiable without fabricated navigation |

### H. Open decisions before approval

1. Final category taxonomy and ownership for communications, alarm, event and platform diagnostics.
2. Whether severity is universal, category-specific or a typed combination; mapping must not erase domain meaning.
3. Stable diagnostic identity, deduplication and correlation policy.
4. Retention/history policy and distinction between active state and immutable event record.
5. Role/authorization model and category-specific action catalogue.
6. Clock source, time synchronization and ordering policy for SOE/Protection/command traces.
7. Whether diagnostics are project-scoped, session-scoped, device-scoped or historian-scoped, and how offline projects display unavailable sources.
8. Versioning and compatibility policy for plugin-contributed diagnostic types.
9. Ownership and service contract for shared read-side projection/query; avoid a second event bus or manager.

### I. Gate disposition

**UI-GATE-03 remains Open.** This proposal supplies a candidate envelope, category taxonomy, lifecycle constraints, UI behavior and acceptance scenarios. It does not settle alarm-management policy, authorization, retention, identity, timing or plugin schema governance. Domain owners must review and approve those decisions before the contract is frozen.

**Scope boundary:** research register only. No implementation files, domain contracts or persistence schemas were changed. No V2 behavior was modified. No tests or CI were run.


## 8I-12. Proposed cross-domain operational traceability contract (2026-11-04)

**Purpose:** Define a reviewable V3 contract for UI-GATE-06 so an engineer can inspect how field measurements, Protection evaluation, optional Control/interlock context, command dispatch and device feedback relate. The trace must preserve independent domain authority, temporal evidence and explicit uncertainty. This is a proposed read-side contract, not an implementation authorization or a claim that the complete path currently exists.

### A. Governing principle: linked facts, not a synthetic outcome

The operational trace is a **correlated evidence graph and timeline** assembled from independently authoritative records. It is not one mutable workflow state and must not manufacture a single end-to-end success/failure flag.

Each record retains its own producer, identity, timestamp, revision, lifecycle and authority. Relationships between records must state what is known:
- **caused_by / evaluated_from:** only where the owning domain or execution contract explicitly records the causal/evaluation reference;
- **input_to:** a measurement or signal was supplied as an input to a particular evaluation;
- **requested_by / issued_for:** an output intent or command is linked to its originating decision/operation;
- **interlocked_by / permitted_by / blocked_by:** a Control/interlock result is linked only where an explicit configured policy and execution record establish that relationship;
- **acknowledged_by:** a command transport/device acknowledgement record references the command;
- **feedback_confirms / feedback_disagrees_with:** a feedback observation is explicitly evaluated against the expected device state;
- **correlated_with:** records share a correlation context but causality is not established.

A shared correlation ID alone proves association, not causality. The UI must visually distinguish authoritative causal links from correlation-only links.

### B. Trace stages and ownership

| Stage | Evidence record | Authoritative owner | UI must show | Must not infer |
|---|---|---|---|---|
| 1. Physical instrument | Instrument identity, type, ratio/rating, installation/terminal association and configuration revision | Equipment/instrumentation model and owning Application services | Instrument tag/type, primary association, secondary terminal/channel mapping where configured | That a configured CT/PT/CVT is currently healthy or producing valid samples |
| 2. Acquisition/channel | Channel identity, source binding, acquisition path, scaling, engineering unit and channel configuration revision | Signal and Measurement infrastructure / acquisition adapter | Source instrument, channel, terminal/source mapping, units, scaling and acquisition status | That channel configuration proves a fresh measurement exists |
| 3. Sample/quality | Typed sample value, unit, sample timestamp, receive timestamp, quality, freshness and provenance | Measurement producer/acquisition and signal-quality contract | Value, units, source time, receive time, quality, age/freshness and lineage | That missing, stale, uncertain or bad-quality data is zero, healthy or acceptable |
| 4. Protection evaluation | Evaluation identity, relay/function, input sample references, settings revision, result/decision and decision timestamp | Protection domain/runtime | Function code, configured element, measured inputs, quality/freshness, settings revision, pickup/operate/block/no-decision result and reason | That a displayed pickup equals a trip; or a Protection decision means a breaker physically operated |
| 5. Control/interlock context (conditional) | Control cycle/evaluation, interlock policy, input references, blocked/permitted intent and execution result | Control domain/runtime | Whether a Control relationship was configured and actually evaluated; relevant rung/logic and block reason | That every Protection trip must pass through Control, or that a Control cycle can rewrite a Protection decision |
| 6. Output intent | Typed trip/close/operate intent and target reference | Protection or Control owner that produced the intent | Originating authority, target, requested operation, preconditions and decision link | That intent is a command already dispatched |
| 7. Command lifecycle | Command identity, target, payload/type, dispatch attempt, transport response, acknowledgement/rejection/timeout and timestamps | Application command orchestration and communication/device adapter | Separate created, dispatched, transport-accepted/rejected, timed-out and terminal states with correlation | That transport acceptance proves actuator movement or contact position |
| 8. Device feedback | Independently acquired auxiliary contact, position/status or other device feedback with timestamp, quality and source | Device feedback/acquisition and Measurement infrastructure | Actual observed state, source, sample time, quality, freshness and expected-vs-observed comparison | That command acknowledgement is physical feedback; or that absent feedback means success |
| 9. Historian/event record | Persisted time-series, alarm/event/SOE, command, feedback and disturbance references | Historian/event services and source domains | Historical sequence, time basis, provenance and gaps in retained evidence | That a missing historian record proves an event did not occur |

The stages are a trace navigation model, not a mandatory serial execution pipeline. For example, a Protection trip may command a breaker through the Protection/Application output path without a Control logic execution stage. Control context appears only when a configured, authoritative relationship exists.

### C. Typed trace record and relationship model

Candidate record envelope:

| Field | Meaning | Constraint |
|---|---|---|
| trace_record_id | Stable identity of an individual evidence record | Required; identity assigned by its authoritative producer |
| record_kind | Instrument, channel, sample, quality transition, Protection evaluation/decision, Control evaluation, intent, command, acknowledgement, feedback, event or historian reference | Required; versioned discriminator |
| authority_domain | Equipment, Signal/Measurement, Protection, Control, Application/Actuation, DeviceFeedback or Historian | Required; one authoritative producer |
| source_ref | Producer/device/service identity | Required |
| subject_refs | Typed project/domain object references | Required where attributable |
| event_time | Time at which the source says the event/sample occurred | Preserve source clock and uncertainty |
| ingest_time | Time received/recorded by the consuming service | Distinct from event_time |
| sequence | Source-local sequence or monotonic ordering token where available | Optional; never fabricate global ordering |
| project_revision | Canonical project/configuration revision relevant to the record | Conditional |
| topology_revision | Physical topology revision relevant to association | Conditional; not a universal revision |
| instrumentation_revision | Instrument, channel and measurement configuration revision | Conditional |
| protection_revision | Protection settings/configuration revision | Conditional |
| control_revision | Control logic/configuration revision | Conditional |
| execution_revision | Evaluation/cycle/runtime sequence reference | Conditional |
| payload_ref | Typed reference to the authoritative record/payload | Required; avoid copying mutable domain state into UI |
| quality/provenance | Sample quality and lineage where measurement-derived | Required for sample-derived evidence |
| correlation_refs | Explicit related record IDs and correlation identifiers | Optional; relation semantics must be typed |
| completeness | Whether required source segments are present, unavailable, not configured, not retained or not yet received | Required at trace-view level; unknown must remain explicit |

Candidate edge envelope includes: edge identity; source and target record IDs; typed relation; asserting producer; evidence reference; valid/recorded time where applicable; and an explicit distinction between authoritative and correlation-only relationships. Confidence/strength must only be included if a defined domain contract supplies it; no UI-generated confidence score.

The graph service may assemble and index links, but it must not invent missing edges or upgrade correlation to causation. Any inferred association based on timestamp proximity must be labelled as a candidate association and excluded from authoritative causal claims until confirmed by a source contract.

### D. Time, ordering and revision semantics

1. Preserve source event time and receiving/ingest time separately. Display clock source, timezone and known synchronization quality where operationally relevant.
2. Do not sort asynchronous records into a false total causal order merely by arrival time. Use source sequence numbers and explicit references where available; otherwise show a time-ordered view with uncertainty.
3. Distinguish sample time, evaluation time, decision time, command creation/dispatch time, acknowledgement time and feedback observation time.
4. Calculate freshness against a domain-approved policy and relevant sample period; the UI must not invent one universal stale threshold.
5. A record remains historically true for the revision under which it was produced. A later configuration change does not rewrite the historical Protection decision or sample.
6. Show whether current configuration differs from the configuration used by the historical decision. Never silently relabel a past decision as if evaluated using current settings.
7. Keep topology, instrumentation/channel, Protection settings, Control logic, execution/cycle and sample-sequence revisions distinct. A single project revision is insufficient to explain all runtime evidence.
8. If clocks are unsynchronized or time uncertainty is unknown, show that limitation; do not claim sub-millisecond ordering or sequence-of-events accuracy without evidence.
9. Retention gaps, disconnected devices, late-arriving samples and unavailable historian segments must appear as explicit gaps, not as proof of no event.

### E. UI presentation: operational trace workspace

Candidate layout:
- **Trace header:** target equipment/device, initiating record, correlation context, current project and relevant revision identifiers.
- **Evidence timeline:** chronological view of samples, evaluations, decisions, intents, command transitions, acknowledgements, feedback and events; distinct lanes by authority domain.
- **Relationship graph:** causal/evaluation links solid and labelled; correlation-only links visually distinct; absent/unverified links never drawn as confirmed edges.
- **Evidence inspector:** source identity, typed payload, event/ingest timestamps, quality, provenance, revisions, references and lifecycle.
- **Completeness panel:** present, unavailable, not configured, not retained, late or unresolved evidence segments.
- **Current-vs-historical context:** explicitly separate live device state from historical trace state and identify configuration drift since the event.

Interaction rules:
1. Entry points may include a relay operation, breaker, instrument/channel, command, alarm/event or device feedback record.
2. The user can traverse backward from decision to exact input samples and forward from decision to intent, command and feedback where links exist.
3. Every stage can be opened in its owning domain workspace without transferring authority to the trace UI.
4. Filters may hide records from view but must not delete or acknowledge them.
5. The UI must distinguish “no relationship configured”, “relationship configured but not evaluated”, “evaluated and blocked”, “source unavailable”, “record not retained” and “relationship unknown”.
6. An end-to-end summary may state only the strongest evidenced outcome. For example: “Protection decision issued; command dispatched; device feedback not received” is valid; “breaker tripped” is not valid without authoritative feedback evidence.
7. If feedback contradicts the command expectation, show mismatch as an observed discrepancy and link the independent feedback record; do not automatically mutate the Protection decision or Control state.

### F. Failure and edge-case behavior

| Condition | Required trace behavior |
|---|---|
| CT/PT/CVT configured but no channel binding | Show configuration gap; do not fabricate a channel or sample |
| Channel bound but no sample received | Show no sample/unavailable with last-known sample time if one exists |
| Sample stale/bad/uncertain | Preserve value and quality context; mark evaluation eligibility according to Protection/Control owner's actual decision |
| Protection evaluation has no valid input | Show no-decision/blocked/unavailable exactly as Protection reports; never synthesize pickup/no-pickup |
| Protection decision exists but no output intent | Show decision and missing/not-configured output mapping as separate facts |
| Intent exists but no command created | Show intent; command stage absent/pending with explicit owner-supplied status |
| Command dispatched but no acknowledgement | Show dispatched/awaiting/timeout according to command owner; do not mark accepted or failed without evidence |
| Command acknowledged but no physical feedback | Show transport acknowledgement and feedback unavailable separately |
| Feedback contradicts expected state | Show mismatch with source/time/quality; preserve command and feedback as distinct records |
| Control interlock not configured | Mark not configured/not applicable, not passed |
| Control interlock configured but not evaluated | Mark not evaluated; do not imply permissive |
| Historian data missing | Show retention/availability gap and live-source availability separately |
| Configuration changed after operation | Preserve historical revision and show current-vs-event configuration difference |

### G. Candidate acceptance scenarios for UI-GATE-06

| Scenario | Setup/action | Expected evidence |
|---|---|---|
| UI-ACC-TRACE-01 Full trace | Valid instrument sample, Protection evaluation, output intent, command, acknowledgement and independent feedback | Each stage is independently sourced, timestamped, revisioned and linked; no synthetic state replaces records |
| UI-ACC-TRACE-02 Direct Protection path | Protection trip path has no Control logic dependency | Trace correctly shows Protection → command path; Control is not invented as a mandatory stage |
| UI-ACC-TRACE-03 Configured interlock | A configured Control interlock is evaluated and blocks or permits an action | Control evaluation and result are linked to the action; Protection decision remains unchanged |
| UI-ACC-TRACE-04 Measurement quality failure | Stale/bad/unavailable measurement reaches an evaluation boundary | Source quality and Protection/Control owner response are visible; UI does not decide eligibility |
| UI-ACC-TRACE-05 Command/feedback divergence | Command accepted but feedback indicates device did not reach expected state | Transport acceptance and physical mismatch are shown independently |
| UI-ACC-TRACE-06 Revision drift | Settings or topology changes after historical decision | Historical decision retains its original revisions; current configuration is shown separately |
| UI-ACC-TRACE-07 Time uncertainty | Event, sample and ingest clocks differ or are unsynchronized | UI preserves timestamps and uncertainty without asserting false causal ordering |
| UI-ACC-TRACE-08 Missing evidence | One or more stages are unavailable, unconfigured or not retained | Completeness panel identifies exact gap category; no missing stage is inferred as success |
| UI-ACC-TRACE-09 Historian reconstruction | Reopen a historical operation from retained records | Timeline reconstructs only retained authoritative records and identifies missing segments |
| UI-ACC-TRACE-10 Cross-workspace navigation | Navigate from trace to instrument, relay function, Control rung, command or breaker | Correct owning workspace opens with stable identity and context; no duplicate authority is created |

### H. Required domain and platform decisions

1. Canonical identity and stable references for instrument, channel, sample, relay function, ProtectionDecision, Control evaluation, DeviceCommand, acknowledgement and DeviceFeedback.
2. Explicit producer-owned relationship contract for Protection decision → output intent → command and for any Control interlock relationship.
3. Direct Protection-to-actuation routing semantics versus Control-mediated or interlocked routing; no universal Control stage.
4. Device acknowledgement taxonomy: transport receipt, protocol acceptance, command acceptance and device operation confirmation must be separately defined.
5. Feedback source contract: auxiliary contact, position sensor, status telemetry, simulated feedback and manually entered state must retain source type and trust/quality.
6. Clock synchronization, timestamp precision, sequence numbering and uncertainty representation for SOE-grade traces.
7. Retention and historian query contract, including disturbance records and late-arriving data.
8. Authorization boundaries for viewing sensitive control/operation details and initiating any follow-on command from a trace.
9. Graph/query projection ownership, bounded query performance and plugin extension/version policy; avoid a parallel runtime/event architecture.
10. Offline/simulation mode semantics: simulated sample/feedback must be unmistakably identified and never confused with field telemetry.

### I. Gate disposition and architectural constraints

**UI-GATE-06 remains Open.** This proposal defines trace stages, record/edge semantics, temporal/revision rules, UI behavior, failure handling and candidate acceptance scenarios. It does not approve canonical IDs, protocol acknowledgement semantics, clock accuracy, retention, authorization or a production graph/query service.

The following constraints are mandatory for subsequent design review:
- Protection and Control remain separate execution authorities.
- Shared Signal/Measurement infrastructure supplies typed measurements, units, timestamps, quality and provenance; it does not itself decide Protection operation or Control execution.
- ProtectionDecision, output intent, DeviceCommand, transport acknowledgement and DeviceFeedback remain distinct records.
- Device feedback must be independently sourced; no fabricated acknowledgement or actuation success.
- Correlation is not causation.
- Historical records retain the revisions and source timestamps under which they were produced.
- UI is a read-side projection plus typed navigation/action intent; it is not a new orchestration authority.

**Scope boundary:** research register only. No implementation files, domain contracts, persistence schemas or runtime services were changed. No V2 behavior was modified. No tests or CI were run.


## 8I-13. Proposed V3 project and session lifecycle contract (2026-11-04)

**Purpose:** Define a reviewable V3 contract for UI-GATE-02 covering project identity, canonical persistence, drafts, preferences, workspace presentation, viewport metadata, transient interaction, save/restore, recovery and multi-document behavior. This proposal preserves the established GridForge project boundary and does not authorize a new file format, schema migration, autosave guarantee or implementation.

### A. Governing principle: one engineering source of truth, explicitly scoped auxiliary state

The Project remains the persistence root for canonical engineering data. The .gridforge package remains a ZIP-based project artifact with:
- manifest.json describing package/schema/version metadata;
- canonical project.json containing the saved engineering scope, including SLD representation/layout and required Core equipment, connections and topology;
- no external file dependencies for the canonical project to be valid and portable.

The package is not a container for arbitrary machine-specific UI state. Any extension to package contents requires an explicit schema/version decision, ownership, compatibility and migration policy. This proposal does not add such an extension.

The six persistence classes below have distinct owners, durability and portability. A save operation must state which class it saves; the generic word Save must not ambiguously imply that all six are persisted.

### B. Six state classes and ownership

| State class | Examples | Candidate owner/storage | Project portability | Dirty-state semantics |
|---|---|---|---|---|
| 1. Canonical engineering project | Equipment, terminals, topology, connections, committed SLD layout, engineering configuration and approved project metadata | Core/Application project model and .gridforge package | Travels with project; machine-independent | Canonical project dirty flag |
| 2. Persisted engineering draft | Uncommitted equipment/configuration/wiring work that the product explicitly promises to recover | Application draft model with explicit project association and versioned draft persistence policy | Project-associated; portability depends on approved packaging/sidecar policy | Separate draft dirty/recovery status; never silently mark canonical project clean |
| 3. User/machine preferences | Theme, density, font scale, default folders, recent-project list, personal tool preferences | User settings service / OS-appropriate settings store | Machine/user scoped; not copied as project engineering truth | Preferences dirty/save status separate from project |
| 4. Workspace presentation | Panel visibility, dock placement, active workspace, window geometry, workspace profile | Workspace/layout settings service | User/machine scoped by default; optional named portable profiles only by explicit decision | Presentation state dirty/save status separate from project |
| 5. Per-document viewport metadata | Zoom, pan, active sheet/view, per-document display framing | Document-view state service, keyed by stable project/document identity | User/machine scoped by default; not canonical engineering data | View-state save status separate from project |
| 6. Transient interaction state | Hover, current drag, rubber-band selection, in-progress gesture, temporary snap candidate, open context menu, pointer capture | Active UI interaction session/controller | Not persisted; must be discarded safely on close/restart | Never contributes to canonical project dirty state |

**Boundary rules**
1. Canonical engineering data is mutated only through Application commands/services and owning Core/domain rules.
2. Persisted drafts are engineering work-in-progress, not transient pointer state. Draft persistence must not bypass domain validation or become a second canonical project.
3. Preferences and workspace presentation cannot change equipment, topology, Protection settings, Control logic or study inputs.
4. Viewport metadata cannot change SLD geometry or project ownership. A deliberate engineering layout move is a project command; pan/zoom is view state.
5. Transient state is cancelled or safely unwound when its owning interaction ends; it must not be serialized as a half-completed command.
6. If a state item could fit multiple classes, classify by semantics and authority, not by the widget that currently stores it.

### C. Project lifecycle state model

Candidate project lifecycle:
- Closed: no active project context.
- Opening: package discovery, manifest/schema validation, integrity checks and staged loading are in progress.
- Open-clean: canonical project loaded and no uncommitted canonical changes.
- Open-dirty: canonical project has uncommitted changes.
- Saving: a consistent snapshot is being serialized and atomically committed.
- Save-failed: previous durable project remains authoritative; unsaved changes remain recoverable in the active session.
- Closing: close policy resolves canonical changes, drafts and transient interactions independently.
- Recovery-required: a recoverable draft/session record exists or an interrupted save/recovery condition needs explicit handling.
- Read-only/degraded: package can be inspected but cannot safely be mutated or fully loaded; exact cause and permitted operations must be stated.

These states are not all mutually exclusive flags. For example, canonical project may be clean while a persisted draft is dirty, or the project may be open while workspace preferences are unsaved. Model independent state dimensions rather than one boolean modified flag.

### D. Save contract

1. Save persists canonical engineering project state only, unless a separately approved user-visible policy explicitly states otherwise.
2. Save As creates a new project identity/package and must define how project-associated drafts are handled; it must not silently copy machine-specific preferences or transient UI state.
3. Before serialization, Application establishes a consistent project snapshot/revision. UI must not serialize live widget or graphics-scene state as canonical engineering truth.
4. The package write must be failure-safe: write to a temporary target, validate the completed package, then atomically replace/rename where the platform/filesystem supports it. Preserve the last known-good package if writing fails.
5. A successful save response is emitted only after durable commit is confirmed by the persistence owner. UI must not clear dirty state optimistically.
6. Save failure retains the in-memory edits and reports the failure cause and recovery path; it must not silently discard changes or replace the last good project with a partial package.
7. If the project changes while a snapshot is being written, the persistence contract must identify the saved revision and leave later edits dirty.
8. Save status should distinguish queued, serializing, writing, validating, committed and failed where those phases are observable and useful.
9. A project save must not imply that a draft, workspace layout, preferences or viewport state was also saved.
10. Import/export, autosave, backup and recovery are separate operations with explicit semantics; none may be inferred from the Save command.

### E. Draft persistence and recovery contract

1. Define which engineering draft classes are recoverable (e.g., draft network, draft equipment configuration, draft wiring) and which are deliberately ephemeral (e.g., pointer preview, incomplete drag).
2. Persisted draft identity must reference the project identity and relevant base project revision. A draft based on an incompatible project revision must be flagged for reconciliation, not blindly replayed.
3. Draft storage must preserve typed operations/data and provenance; it must not serialize QGraphicsScene, Qt widgets, graphics item instances or renderer-owned object graphs.
4. Draft restore is a staged proposal to the engineer: show draft timestamp, source project, base revision, recoverable objects/operations, conflicts and validation status before applying.
5. Restoring a draft does not commit it into canonical Core topology/equipment. It restores the draft workflow state; canonical mutation still follows explicit commit commands and domain validation.
6. Draft conflict resolution must be explicit: retain draft, discard draft, compare/reconcile or open a recoverable copy where supported. Never auto-overwrite canonical project state.
7. A recovery record must distinguish clean shutdown, application crash, process termination, machine failure, failed save and interrupted draft persistence where evidence permits; do not claim a cause that cannot be established.
8. Draft retention, location, encryption/permissions, expiry, size limits, cleanup and cross-machine portability require explicit policy.
9. If recovery data is corrupt or incompatible, preserve the original artifact for diagnosis where safe and offer a non-destructive fallback; do not repeatedly apply a partially decoded draft.
10. Autosave cadence, write amplification, performance, privacy and user notification are product decisions; no interval or guarantee is implied by this proposal.

### F. Open, close, switch and multi-document behavior

**Open**
- Validate package structure, manifest, schema compatibility and canonical payload before replacing the current active project.
- Load into a staged project context; failure must leave the existing project context intact.
- Identify missing, unsupported or corrupt optional data separately from canonical project corruption.
- Warn or offer recovery when a matching persisted draft exists; never apply it silently.

**Close**
- Resolve canonical project changes, persisted draft changes and preference/layout changes independently.
- Cancel transient interactions through their owning controller before destroying document/view objects.
- Present Save / Discard / Cancel only for state classes whose policy requires a user decision; do not overload one prompt with ambiguous consequences.
- If a save fails, remain open or provide an explicitly recoverable close path; do not claim the project is saved.

**Switch**
- Preserve independent document identity, dirty state, draft association and viewport state for each open document.
- Switching workspace or tab must not commit, clear or acknowledge engineering diagnostics or drafts.
- Rebind inspectors, selection and context actions to the active document; stale references from the previous document must not mutate the newly active one.

**Multi-document**
- Every command, selection, inspector context, draft and viewport record must be bound to an explicit project/document identity.
- Global preferences remain separate from per-document state.
- Cross-project copy/import must use explicit domain transfer/validation, not share mutable object instances.
- A background save must identify its target project and snapshot revision; completion for one document must not clear another document's dirty state.

### G. Versioning, portability and failure policy

1. manifest.json owns package format/schema/version metadata; project.json remains canonical engineering payload under the frozen package contract.
2. Schema migrations must be deterministic, versioned, reviewable and non-destructive. Preserve an original backup or immutable source before migration where feasible.
3. An older application encountering a newer unsupported schema must fail safely or enter a clearly limited read-only mode; it must not rewrite the package with dropped fields.
4. Unknown optional extension data must follow an explicit preserve/ignore/reject policy; silently deleting it during save is prohibited.
5. Relative paths, if ever permitted for optional attachments, need a package security and portability policy. Canonical project validity must not depend on external absolute paths.
6. Recovery and auxiliary settings stores require corruption handling independent of canonical project package validation.
7. Concurrent writers and external modification need conflict detection using project identity and durable revision/fingerprint; last-writer-wins must not be assumed.
8. File-system atomicity, locking, permissions, disk-full behavior and interrupted replacement vary by platform; define supported guarantees rather than asserting universal atomicity.
9. Backup retention and recovery points must be explicit and discoverable; a recent-project list is not a backup.

### H. Candidate UI presentation

- Project header shows project identity, location, canonical dirty/save state and schema compatibility.
- Separate indicators show draft recovery/dirty status, workspace-layout persistence and preference persistence where relevant.
- Save action label and confirmation describe what is being saved.
- Recovery center lists recoverable drafts/session artifacts with source project, timestamp, base revision, conflict status and preview.
- Close/switch dialogs enumerate affected state classes and consequences in plain language.
- Workspace and viewport restoration are visually distinct from engineering model restoration.
- Read-only/degraded mode identifies the restricted operations and reason.
- Never use one generic green Saved indicator to imply all state classes are durable.

### I. Candidate acceptance scenarios for UI-GATE-02

| Scenario | Setup/action | Expected evidence |
|---|---|---|
| UI-ACC-SESSION-01 Canonical save | Modify equipment/topology through Application commands and save | .gridforge canonical payload reflects the committed project revision; UI reports success only after durable commit |
| UI-ACC-SESSION-02 View-only change | Pan/zoom, change panel layout and theme; save project | Canonical project payload is unchanged; auxiliary settings follow their own policy |
| UI-ACC-SESSION-03 Engineering draft recovery | Create a supported persisted draft, close/crash and reopen | Draft is offered with project/base revision and preview; canonical project remains unchanged until explicit commit |
| UI-ACC-SESSION-04 Save failure | Simulate disk-full, permission or replacement failure at persistence boundary | Last known-good package remains intact; dirty state remains; actionable error is shown |
| UI-ACC-SESSION-05 Save during edits | Mutate project while a save snapshot is in progress | Saved revision is identified; subsequent edits remain dirty and are not falsely marked saved |
| UI-ACC-SESSION-06 Multi-document isolation | Open two projects, edit/save/switch between them | Dirty flags, commands, drafts and viewport state remain bound to correct document |
| UI-ACC-SESSION-07 Incompatible draft | Restore draft against a changed base project revision | Conflict is detected; no blind replay or canonical overwrite occurs |
| UI-ACC-SESSION-08 Schema compatibility | Open older, newer unsupported and malformed packages | Migration/read-only/reject behavior is explicit and non-destructive |
| UI-ACC-SESSION-09 Interrupted save | Interrupt package write/replace | Previous valid package remains recoverable; incomplete output is not treated as committed |
| UI-ACC-SESSION-10 Transient interaction cleanup | Close/switch document during active drag, preview or tool gesture | Interaction is safely cancelled/unwound; no half-created canonical object is persisted |
| UI-ACC-SESSION-11 Preference failure | Preference/layout store is unavailable or corrupt | Project open/save remains independent; user receives scoped warning and safe defaults |
| UI-ACC-SESSION-12 External modification | Project changes outside the running application before save | Conflict is detected or explicit policy is applied; silent overwrite is prohibited |

### J. Open decisions before approval

1. Which draft classes are persisted and what is their storage location: inside package, project-associated sidecar, or managed recovery store?
2. Is autosave supported? If so, which state classes, cadence, retention and user controls apply?
3. What is the canonical project identity and durable revision/fingerprint contract?
4. What guarantees are required for atomic save, backup, file locking and concurrent access on supported operating systems/filesystems?
5. What is the migration policy for schema versions and unknown extension/plugin data?
6. Which workspace/viewport preferences are global, per user, per machine, per project or portable profiles?
7. How are multiple open documents and project switching supported?
8. What recovery behavior is promised after application crash, process termination, OS crash and power loss?
9. What privacy, permission and cleanup policies govern drafts, recent projects and recovery artifacts?
10. Which operations are permitted in read-only/degraded mode?
11. What is the UX policy when project save succeeds but auxiliary settings persistence fails, or vice versa?
12. How are project copies, Save As, imports and external file modifications reconciled?

### K. Gate disposition and invariants

**UI-GATE-02 remains Open.** This proposal separates the six state classes and defines candidate lifecycle, save, draft recovery, multi-document, compatibility and failure behavior. It does not approve autosave, sidecar/package changes, recovery guarantees, migration policy or multi-document release scope.

Frozen project constraints remain:
- .gridforge remains the project package; manifest.json describes package/schema/version and project.json is canonical engineering payload.
- Project persistence stores engineering model/topology and SLD layout, not screenshots or serialized Qt graphics scenes.
- Core owns engineering truth; Application owns controlled mutation and persistence orchestration; UI owns presentation and transient interaction only.
- Draft state is not committed Core state; commit remains explicit and domain-validated.
- Preferences, workspace layout and viewport state do not mutate canonical engineering data.

**Scope boundary:** research register only. No package format, schema, persistence service, source implementation or V2 behavior was changed. No tests or CI were run.


## 8I-14. Proposed V3 accessibility and platform usability contract (2026-11-04)

**Purpose:** Establish a discipline-aware accessibility contract for UI-GATE-04 across the main shell, SLD, Control, Protection, Study, diagnostics and engineering data entry. This is a design proposal, not a conformance claim or implementation authorization.

### A. Research basis and applicability

Primary technical references reviewed 2026-11-04:
1. W3C, Web Content Accessibility Guidelines (WCAG) 2.2: https://www.w3.org/TR/WCAG22/
2. W3C WAI, What's New in WCAG 2.2: https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
3. Qt 6.12, Accessibility for QWidget Applications: https://doc.qt.io/qt-6/accessible-qwidget.html
4. Qt 6.12, QAccessibleInterface: https://doc.qt.io/qt-6/qaccessibleinterface.html
5. Qt 6.12, High DPI: https://doc.qt.io/qt-6.12/highdpi.html
6. Microsoft, High DPI Desktop Application Development on Windows: https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows

**Applicability qualification:** WCAG is a web-content standard, not by itself a native Qt desktop certification. Its principles and measurable criteria are useful design references for GridForge, but V3 must define a native desktop accessibility profile, platform support matrix and verification method. Do not claim WCAG conformance merely because selected criteria were adapted.

Qt provides accessibility interfaces for built-in widgets and supports custom accessible interfaces for custom widgets/objects. Its accessibility model exposes roles, names, descriptions, states, actions, relationships and navigation to assistive technologies. Custom canvas items and custom controls therefore require deliberate semantic exposure and accessibility event handling; visual rendering alone is insufficient. Qt 6 documentation describes per-monitor DPI support on Windows, but this does not prove application-owned icons, custom painting, cached pixmaps, geometry assumptions or mixed-monitor transitions are correct.

### B. Accessibility principles for engineering software

1. **Equivalent task completion:** Every essential engineering task must have a supported non-pointer route where technically meaningful.
2. **Semantic equivalence:** Visual symbols, wires, alarms, status indicators and graph edges expose structured accessible names, roles, states and relationships.
3. **Predictable focus:** Focus order follows task and document context; it is not silently lost when panels, tabs, editors or documents change.
4. **Visible focus:** Keyboard focus is unambiguous, not colour-only, and not obscured by docks, overlays or tool palettes.
5. **No colour-only meaning:** Severity, connectivity, selection, alarm and signal quality use text, shape, pattern or accessible metadata in addition to colour.
6. **User control:** Text/display density and nonessential motion are adjustable without hiding task-critical information.
7. **Error prevention and recovery:** Validation identifies the affected object/field, explains the issue, provides navigation to the source and preserves user input.
8. **Consistent semantics, specialized interaction:** Shared accessibility behavior is common infrastructure; SLD, Control and Protection retain their domain-specific object models and workflows.
9. **Assistive technology parity:** Meaningful selection, diagnostic, execution and project-lifecycle changes are exposed to assistive technology without excessive announcements.
10. **No unsafe inference:** Descriptions must not imply energized/de-energized, tripped/healthy, command accepted or device operated without authoritative evidence.

### C. Keyboard and focus architecture

- A single focus-aware dispatcher coordinates application commands, active workspace, active document, canvas tool and text-entry controls.
- Text editors, numeric fields, tables, combo boxes and property editors retain native editing keys. Global shortcuts must not steal text-editing input.
- Shortcut scopes are explicit: global, workspace, document, canvas/tool and focused control. Conflicts are detectable and discoverable.
- Every pointer-only menu, dock, tab, palette, property action and diagnostic navigation action has a keyboard equivalent.
- Tool activation, cancellation, selection mode and active tool are visibly indicated and announced.
- Escape behavior is deterministic for nested states (dialog, tool, gesture, selection, popup); it must not unexpectedly close or discard a project.
- Tab/Shift+Tab traverse logical shell regions; arrows operate controls that conventionally use arrow navigation.
- Canvas keyboard operation supports focus entry/exit, object traversal, selection, property inspection, command invocation, zoom and pan without requiring a mouse.
- Focus restoration uses stable semantic context (document, panel, object/field), not stale widget pointers.
- On panel close, focus returns to the invoking control or a documented fallback.
- Shortcuts are discoverable in menus/tooltips and a searchable reference; remapping requires conflict resolution and reset-to-default.

### D. Canvas accessibility: preserve discipline semantics

**SLD**
- Expose equipment, terminals, connections, buses, labels and selection groups with stable identity and engineering type.
- Provide a navigable object/connection outline synchronized with canvas selection.
- Describe equipment name/tag, type and relevant terminal/connectivity summary without dumping every property into one spoken label.
- Expose terminal and wire endpoint relationships without pixel-precise targeting.
- Provide keyboard alternatives for select, move, rotate, connect, delete, inspect and fit/zoom, subject to safe confirmation and domain validation.
- Distinguish visual/layout movement from topology or ownership change.
- Announce draft preview and committed project object as different lifecycle states.

**Control**
- Ladder/rung/logic elements expose semantic roles and relationships (rung, contact, coil, timer, gate, signal reference, interlock), not generic graphics-item labels.
- Provide structured rung/logic navigation and textual summaries for branches and connections.
- Execution indications include actual cycle and quality context; colour alone cannot establish execution state.
- Clearly distinguish editing logic configuration from starting/stopping execution.

**Protection**
- Relay, protection function, measurement channel, input mapping, decision, trip intent and device feedback are distinct accessible entities.
- Expose freshness, quality and provenance alongside measurements where material.
- Diagnostic/trip-history navigation preserves timestamp, source and relay/function identity.
- Never flatten Protection decision, command acknowledgement and physical breaker feedback into one generic status.

**Study**
- Study setup exposes labelled fields, units, valid ranges and explicit defaults.
- Errors identify exact parameters and units.
- Results expose structured tables and textual plot/curve summaries; chart meaning cannot depend on colour or visual position alone.
- Progress, cancellation and completion are announced without repeated noise; numerical results retain units and meaningful precision.

A shared accessible canvas abstraction must not force one generic geometry or interaction model across disciplines.

### E. Accessible data entry, diagnostics and tables

1. Every input has a programmatic label, role, unit, current value, constraints where available, and error/help relationship.
2. Required, optional, read-only, disabled, calculated and inherited values are distinguishable in text and state metadata.
3. Validation summaries provide severity, category, source object, field/parameter, timestamp and actionable navigation.
4. Validation failure preserves entered values; focus moves according to a predictable policy.
5. Live announcements are prioritized and throttled; high-rate telemetry and canvas repaint events are not announced continuously.
6. Alarm, event, warning, diagnostic and informational message roles remain distinct; acknowledgement, shelving and clearance are described accurately.
7. Tables/trees expose row and column headers, current cell, sort/filter state, selection and hierarchy.
8. Search/filter/pagination preserve keyboard position and announce result counts and empty states.
9. Tooltips supplement but do not replace persistent labels, help text or accessible names.
10. Engineering units remain part of accessible value descriptions; display formatting must not obscure the underlying engineering value.

### F. Visual presentation, contrast and non-colour cues

- Text and essential control boundaries maintain defined contrast thresholds in every supported theme, measured on rendered states rather than inferred from palette tokens.
- Focus indicators are persistent, high-contrast and distinct from selection, hover and active-tool styling.
- Selection, focus, hover, alarm severity, validation, signal quality, energized state and connectivity are not represented by the same colour-only convention.
- Use redundant cues: text, icons with accessible names, line styles, patterns, shape changes or explicit state columns.
- Support light and dark themes; evaluate high-contrast/forced-colour behavior on supported platforms.
- Text scaling must not clip engineering units, tags, property values, diagnostics, menus or dialog actions. Dense views adapt layout rather than silently shrinking text.
- Density is user-controlled independently of font scale; compact mode cannot remove labels or focus visibility.
- Avoid flashing/high-frequency animation and provide reduced-motion behavior for nonessential transitions.
- Critical information remains available in grayscale, under colour-vision differences and when themes change.

WCAG 2.2 provides useful reference criteria for keyboard operation, focus visibility/not-obscured, contrast, non-text contrast, target sizing and programmatic name/role/value. Any adopted thresholds must be mapped to native controls and verified with native tooling; CSS pixels must not be blindly equated with physical Qt geometry.

### G. High-DPI, mixed-monitor and platform behavior

1. Define supported operating systems, Qt versions, windowing systems, display-scale ranges and assistive-technology combinations.
2. Use device-independent logical geometry for UI layout; convert to device pixels only at rendering/resource boundaries with explicit device-pixel-ratio handling.
3. Re-evaluate geometry, fonts, icon assets, cached pixmaps, canvas overlays and hit-testing when a window moves between monitors with different scale factors.
4. Avoid fixed-pixel assumptions for hit targets, panel widths, font sizes, symbol handles and tool icons.
5. Cover fractional scales, mixed-DPI laptop/external-monitor setups, monitor hot-plug, remote desktop and runtime scale changes.
6. Prefer vector assets or resolution-appropriate variants; cache keys account for device-pixel ratio and theme.
7. Canvas geometry and engineering symbol dimensions remain internally consistent when device-pixel ratio changes; monitor scaling cannot mutate saved engineering layout or topology.
8. Verify floating docks, dialogs, tooltips and menus after scale transitions.
9. Qt platform DPI behavior is a foundation, not proof that custom painting or third-party widgets are correct.
10. Document platform-specific accessibility backend support and limitations; do not claim identical assistive-technology behavior across Windows, macOS and Linux without evidence.

### H. Architecture and ownership

- **Core:** owns engineering semantics and typed domain descriptions where required; no Qt or assistive-technology dependencies.
- **Application:** exposes typed read models, commands, validation and diagnostic navigation targets; remains authoritative for mutations.
- **UI accessibility layer:** maps UI/domain projections to Qt accessibility roles, names, states, relationships, actions and event notifications.
- **Custom canvas adapters:** expose semantic object trees/actions for SLD, Control and Protection without placing renderer objects in Core.
- **Interaction/focus service:** coordinates focus scopes, shortcut precedence, keyboard navigation and restoration.
- **Theme/display service:** owns theme, density, font scaling, contrast tokens and DPI-aware asset selection.
- **Verification harness:** records platform, Qt build, screen reader, display scale, theme, input modality, scenario and observed result.

Do not place QAccessible types, QWidget classes, screen-reader APIs or platform accessibility APIs in Core or domain plugin contracts. Domain plugins may contribute typed semantic descriptors through public UI-facing extension contracts; the shared UI accessibility layer translates them into platform interfaces.

### I. Candidate evidence and acceptance scenarios

Evidence categories:
- UI-VER-A11Y-01 Keyboard-only completion records for each critical workflow.
- UI-VER-A11Y-02 Focus order, focus restoration and shortcut-conflict matrix.
- UI-VER-A11Y-03 Screen-reader inspection of shell, dialogs, inspectors, tables and diagnostics.
- UI-VER-A11Y-04 Custom canvas semantic-tree/action/event coverage.
- UI-VER-A11Y-05 Contrast, focus visibility, non-colour cue and text-scaling measurements.
- UI-VER-A11Y-06 High-DPI/mixed-monitor matrix with geometry observations.
- UI-VER-A11Y-07 Reduced-motion and announcement-frequency checks.
- UI-VER-A11Y-08 Platform/Qt/assistive-technology compatibility matrix.

| Scenario | Setup/action | Expected evidence |
|---|---|---|
| UI-ACC-A11Y-01 Keyboard shell navigation | Navigate menus, docks, tabs, palette, Inspector and diagnostics without pointer | Essential controls reachable; focus visible and ordered; no keyboard trap |
| UI-ACC-A11Y-02 Shortcut focus precedence | Edit numeric/text fields while global/workspace shortcuts exist | Text editing is not intercepted; scoped shortcuts resolve predictably |
| UI-ACC-A11Y-03 SLD semantic navigation | Navigate equipment, terminals and wires via keyboard/outline | Stable identity, type and connectivity exposed; select/inspect actions available |
| UI-ACC-A11Y-04 Control logic navigation | Traverse ladder rungs, contacts, coils and branches | Logical relationships and execution/configuration distinction exposed |
| UI-ACC-A11Y-05 Protection evidence navigation | Inspect relay inputs, quality, decisions, trip intents and feedback | Distinct identities, timestamps, source and quality announced |
| UI-ACC-A11Y-06 Study data and results | Configure a study and inspect tables/plots with assistive technology | Units, labels, errors, progress and numerical summaries accessible |
| UI-ACC-A11Y-07 Non-colour state interpretation | Change theme/grayscale and inspect alarm, quality, selection and connectivity | No critical state depends on colour alone |
| UI-ACC-A11Y-08 Focus under overlay | Open panels/popovers/overlays while focus is on an underlying control | Focus remains visible or can be revealed without advancing it |
| UI-ACC-A11Y-09 Text scaling and density | Increase text scale and change density | No clipped/inaccessible essential values or actions |
| UI-ACC-A11Y-10 Mixed-DPI transition | Move window between monitors with different fractional scales | Text/assets/hit targets remain crisp and aligned; model geometry unchanged |
| UI-ACC-A11Y-11 Screen-reader live updates | Change selection, validation, project save and operational status | Relevant changes announced at appropriate priority without excessive repetition |
| UI-ACC-A11Y-12 Reduced motion | Enable reduced-motion preference and navigate workspaces | Nonessential animations reduced without loss of state feedback |

### J. Open decisions before approval

1. Which operating systems and assistive technologies are in the supported V3 release matrix?
2. Which WCAG 2.2 criteria and thresholds are adopted as native-desktop design references, and what native verification maps them?
3. What is the minimum keyboard-only task set for SLD, Control, Protection, Study and project lifecycle?
4. Which semantic navigation model is selected for dense canvases: synchronized object tree, semantic canvas focus traversal, textual relationship view, or a combination?
5. Which screen-reader announcement classes are immediate, queued, summarized or suppressed for high-rate updates?
6. What high-contrast/forced-colour support is required on each platform?
7. What minimum/maximum text scale, density and DPI combinations are required?
8. Which custom canvas widgets require dedicated QAccessibleInterface implementations and who owns their lifecycle?
9. How are user-defined shortcuts stored, migrated and conflict-checked?
10. What accessibility evidence is mandatory before feature release?

### K. Gate disposition and invariants

**UI-GATE-04 remains Open.** This proposal establishes discipline-aware accessibility requirements, Qt semantic exposure, keyboard/focus behavior, non-colour cues, DPI behavior, ownership and candidate evidence. It does not claim WCAG conformance, platform certification or complete assistive-technology parity.

Frozen architecture invariants:
- Core remains independent of Qt and platform accessibility APIs.
- UI accessibility is a presentation adapter over typed domain/application semantics.
- SLD, Control and Protection retain separate discipline-specific interaction models.
- Accessibility alternatives must not weaken domain validation, command authorization or engineering state truth.
- Device feedback, Protection decisions, Control execution and measurement quality retain distinct semantics when announced.

**Scope boundary:** research register only. No implementation files, accessibility adapters, theme behavior, platform configuration or V2 behavior were changed. No tests or CI were run.


## 8I-15. Proposed V3 display performance and rendering usability contract (2026-11-04)

**Purpose:** Establish UI-GATE-05 requirements for responsive engineering canvases and large-project usability. This is a research/specification proposal, not a benchmark result, confirmed bottleneck diagnosis, renderer selection or implementation authorization.

### A. Technical research basis

Primary references:
1. Qt 6.12 QGraphicsView: https://doc.qt.io/qt-6/qgraphicsview.html
2. Qt 6.12 QGraphicsScene: https://doc.qt.io/qt-6/qgraphicsscene.html
3. Qt 6.12 QPainter performance: https://doc.qt.io/qt-6/qpainter.html

Relevant Qt behavior:
- QGraphicsView offers multiple viewport update modes. MinimalViewportUpdate is the default and generally minimizes redraw area, but many small changes can make damage-region calculation more expensive than repainting. FullViewportUpdate can be preferable when many small items repeatedly change or when the viewport does not support partial updates. No mode is universally optimal. (Qt QGraphicsView documentation.)
- QGraphicsScene uses BSP indexing by default, suited to largely static scenes. NoIndex avoids index-maintenance costs for frequently changing scenes but makes location queries linear. A fixed scene rectangle avoids the expensive fallback of computing bounds from every item. BSP depth trades lookup behavior against memory and should not be tuned without representative data. (Qt QGraphicsScene documentation.)
- QPainter performance varies by paint engine, device, composition mode, transforms, clipping, antialiasing and image formats. Qt documents high-performance subsets but recommends benchmarking other combinations on target systems. OpenGL-backed painting is an option, not proof of a universal speedup over raster. (Qt QPainter documentation.)

**Research conclusion:** performance must be measured end-to-end on representative engineering workloads. Selecting an update mode, BSP policy, cache, OpenGL viewport or batching strategy from intuition alone is not an acceptable architecture decision.

### B. User-perceived performance contract

Measure complete user-visible operations, not only paint-event duration:
1. Open/load: project selection to interactive document; separately measure package I/O, deserialization, projection construction, first useful paint and full detail availability.
2. First paint: shell and canvas become useful without waiting for all optional labels, overlays, diagnostics or secondary indexes.
3. Pan/zoom: navigation remains predictable; no stale transform, jump, disappearing geometry or delayed pointer response.
4. Selection/hit testing: pointer or keyboard selection returns the correct engineering object and Inspector context without a long UI stall.
5. Placement/preview: preview follows pointer smoothly; snap candidates and compatibility hints do not block the UI thread.
6. Wire/connect: preview geometry and terminal targeting remain responsive while domain validation and topology operations remain authoritative.
7. Move/rotate/multi-select: only affected visual regions and dependent projections are recomputed where possible.
8. Property editing: field changes update only necessary projection/validation/display; expensive studies are not triggered synchronously by accident.
9. Telemetry/operational overlay: high-rate samples are coalesced for display; rendering does not become a second acquisition or historian pipeline.
10. Save/reopen and workspace switching: long operations expose progress and safe cancellation without freezing unrelated interaction.

### C. Proposed rendering pipeline and ownership

Candidate pipeline:
1. Core/Application own engineering truth, revisions, commands, validation and typed read models.
2. Projection adapters produce immutable or safely versioned render snapshots for a document, discipline, viewport and revision.
3. A view-specific render layer converts snapshots into display primitives and semantic hit-test/accessibility structures.
4. Viewport culling and level-of-detail (LOD) select detail for the visible region and scale.
5. Renderer paints visible content and transient interaction overlays.
6. Input/hit testing resolves a stable semantic object reference; command/controller revalidates current document/revision before mutation.

Ownership rules:
- Qt widgets, QGraphicsItem, QGraphicsScene and renderer caches remain UI infrastructure, never Core state or canonical project persistence.
- Render snapshots are disposable projections, rebuildable from authoritative project/read-model data; they are not a second engineering truth.
- Background workers may perform pure data preparation, indexing, routing/layout calculation or image preparation when inputs are immutable and outputs versioned. Qt scene/widget mutation and final UI presentation remain on the owning UI thread.
- Every asynchronous result carries document identity and source revision/generation. Discard stale results rather than applying them to a changed document or newly active project.
- Rendering optimization cannot change topology, connectivity, terminal identity, Protection zone, Control logic, measurement quality or numerical results.
- Renderer does not own engineering validation or decide whether a wire/equipment placement is valid.

### D. Scalability and rendering techniques to evaluate

**1. Viewport culling**
- Draw only visible objects plus a controlled margin for labels, wire joins, selection handles and interaction affordances.
- Use spatial queries over stable projection geometry; avoid scanning all domain objects on every paint or pointer move.
- Ensure culling never hides semantically relevant connectivity or produces false endpoint hit targets.
- Bound and instrument visibility-query cost.

**2. Level of detail**
- Define zoom bands for symbols, labels, terminal markers, wire decorations, grid, measurement overlays and Control/Protection annotations.
- At overview scale, simplify labels and decorative detail while preserving essential topology and status distinctions.
- At detail scale, expose terminals, tags, values and interaction affordances.
- Use hysteresis around LOD thresholds to avoid flicker during small zoom changes.
- Hidden details remain available through object outline, Inspector, search and accessible navigation.

**3. Batching and draw-call reduction**
- Evaluate batched drawing for homogeneous static geometry (grid, repeated markers, simple wires) where selection, z-order, accessibility and per-object styling remain correct.
- Retain stable semantic hit-test mapping from rendered batches to domain object references.
- Avoid one heavyweight widget/proxy per decorative primitive.
- Do not batch objects with incompatible update rates/lifecycles in ways that force full-batch invalidation.

**4. Caching**
- Cache only expensive deterministic revision-keyed results: static symbol paths, text layouts, background/grid tiles, stable geometry and derived display fragments.
- Cache keys include project/document identity, source revision, symbol/library version, theme, scale/LOD and device-pixel ratio where applicable.
- Bound cache memory; expose hit/miss, eviction and rebuild cost.
- Invalidate narrowly when an object, style, theme, zoom or document revision changes.
- Never cache mutable engineering authority or treat cached data as proof of current operational state.

**5. Scene/index policy**
- Benchmark spatial index policies against real static SLD networks and dynamic Control/Protection overlays.
- Set and maintain an explicit scene/view bounds strategy; avoid repeatedly deriving global bounds from every item.
- Compare BSP indexing with NoIndex or purpose-built spatial indexes for distinct workloads; do not assume one policy fits all canvases.
- Avoid unbounded scene rectangles and excessive index retuning during edits.
- Profile item count, bounding-rectangle complexity, shape/path complexity, index rebuilds and hit-test latency.

**6. Update/damage policy**
- Track changed regions and update only what is needed when damage is sparse.
- Compare minimal, bounding-rect and full viewport update behavior under sparse edits, high-rate overlays and mass state changes.
- Coalesce multiple events into one presentation update where freshness requirements permit.
- Avoid repeated synchronous layout, text measurement, scene-wide bounds calculation or full projection rebuild during pointer movement.
- Preserve correct repaint after expose, resize, dock movement, DPI transition and theme change.

**7. Rendering backend**
- Benchmark supported raster and accelerated viewport options on target hardware and driver combinations.
- Use fallback behavior when accelerated context creation fails or remote desktop/driver conditions make it unsuitable.
- Do not promise GPU acceleration until measured on the supported platform matrix.
- Backend changes cannot alter rendering semantics, hit testing, text legibility or accessibility exposure.

**8. Labels and overlays**
- Defer nonessential labels at overview zoom; prioritize selected objects, warnings and user-requested annotations.
- Avoid label-overlap algorithms that block interaction or repeatedly recompute globally.
- Separate fast operational overlays from static network geometry and high-rate telemetry ingestion.
- Display timestamps/quality and stale-state cues without repainting the entire network for every sample.

### E. Discipline-specific performance requirements

**SLD**
- Large electrical networks remain navigable with predictable pan, zoom, fit-to-content, search, selection, terminal inspection and wire tracing.
- Static topology/layout is not rebuilt for unrelated status/measurement updates.
- Selection/hit testing distinguishes overlapping wires, terminals, bus segments and equipment at different zoom levels.
- Draft previews and committed objects retain visual continuity without full-scene reconstruction.
- Label simplification does not hide topology-critical connection meaning.

**Control**
- Ladder/rung navigation and editing remain responsive as logic, branch and signal-reference counts grow.
- Runtime updates are coalesced and scoped to affected elements; UI refresh does not throttle or join the Control execution cycle.
- Logic graph layout/route preparation may be asynchronous, but connections remain tied to stable logic identities and revisions.
- Execution overlays cannot delay or change Control evaluation or actuation.

**Protection**
- Relay, function, measurement-channel, decision and event overlays update without rebuilding the electrical network.
- Time-series plots and TCC/coordination curves use resolution-aware data reduction while preserving extrema, trip intersections and engineering-relevant features.
- Curve visibility, selection and legend updates remain responsive with multiple relays/functions; expensive recalculation is explicit and cancellable where safe.
- Rendering never changes Protection evaluation cadence or decision authority.

**Study**
- Large result tables, profiles and plots use lazy retrieval/virtualized presentation rather than a widget per visual cell/point.
- Numerical calculation runs outside the UI thread through Application-owned execution services; progress and cancellation are explicit.
- Display decimation never overwrites/reduces canonical numerical result data.
- Result rendering/export identifies whether data are full-resolution, sampled or decimated.

### F. Threading, event flow and responsiveness

1. UI event loop must not perform long numerical studies, large project parsing, expensive global layout, bulk projection rebuild or synchronous external I/O.
2. Application services own task lifecycle, cancellation, progress and result publication; UI consumes typed progress/result events.
3. Worker inputs are immutable snapshots or explicitly synchronized data. Do not share mutable QGraphicsItem/QWidget or live Core entities across threads.
4. Each result includes document identity, task identity, input revision and cancellation state.
5. On document close/switch, cancel or detach tasks according to lifecycle; stale completion cannot mutate the active document.
6. High-frequency signal updates are sampled/coalesced for display at a bounded presentation cadence. Acquisition/historian paths retain independent timing/fidelity.
7. Prioritize user input, active viewport and visible diagnostics over offscreen decoration or background precomputation.
8. Avoid unbounded task queues; backpressure and drop/coalesce policies are explicit for display-only events.
9. Report long-running work with meaningful stages; do not fabricate percentage completion when total work is unknown.
10. Unsupported acceleration must degrade to a correct supported path where feasible, with a visible diagnostic rather than a blank canvas.

### G. Candidate performance measurement model

Measure per operation and workload:
- input-to-visible-feedback latency (p50, p95, p99);
- frame/presentation interval distribution and missed-frame rate;
- paint duration split by background, geometry, labels, overlays and selection;
- projection build and invalidation duration;
- spatial query/hit-test latency;
- scene/index rebuild time;
- project load to first useful paint and full interactive readiness;
- memory for project model, projection, scene/items, caches and peak transient allocation;
- worker queue depth, cancellation latency and stale-result discard count;
- CPU and GPU/backend utilization where measurable;
- telemetry-to-visible-overlay age, separately from acquisition sample age;
- save/close responsiveness while background tasks are active.

Build reproducible workload tiers from representative GridForge projects:
- small: interactive editing and normal study;
- medium: typical plant/substation project with multiple workspaces and overlays;
- large: high object/connection counts, dense labels, multiple studies and live/simulated overlays;
- stress: pathological geometry, dense overlap, high-rate status events and rapid zoom/pan/selection.

Do not set object-count targets using arbitrary round numbers alone. Derive them from real project samples, product scale and customer use cases. Record dataset generator/version and workload characteristics.

### H. Provisional targets and decision policy

Candidate target bands for product review, not approved release criteria:
- common direct interactions should provide visible acknowledgement within 100 ms at p95;
- continuous navigation should target stable 60 Hz presentation on agreed reference hardware where supported (16.7 ms frame interval), with a separately agreed lower-tier fallback;
- first useful canvas paint should precede optional offscreen detail, with numeric budget set from representative load measurements;
- long operations expose progress/cancellation or staged availability rather than freezing the UI;
- memory/cache budgets are set per supported hardware tier and measured under multi-document use.

These are provisional usability goals, not a claim that every operation/device must meet them. Release profile specifies reference hardware, resolution, DPI, Qt build, backend, power mode, data scale, warm/cold cache and measurement methodology. Report p50/p95/p99, not only averages. One best-case screenshot or one machine's subjective impression is insufficient.

### I. Candidate UI performance diagnostics

A developer/engineering diagnostics view may expose:
- active document and renderer/backend;
- visible/total object counts by semantic class;
- visible/culled counts and LOD band;
- projection revision and render snapshot generation;
- frame interval, paint duration and invalidation region size;
- hit-test/spatial-query duration;
- cache occupancy/hit rate/evictions;
- pending worker tasks, stale results and cancellation state;
- telemetry overlay age and coalescing/drop counts;
- warnings for repeated full-scene invalidation, expensive bounds calculation or excessive item churn.

Diagnostics are read-only; they do not expose mutable renderer objects or change engineering state. Performance instrumentation is not permanently visible in normal engineering workspaces.

### J. Candidate acceptance scenarios for UI-GATE-05

| Scenario | Setup/action | Expected evidence |
|---|---|---|
| UI-ACC-PERF-01 Large SLD navigation | Open representative large network; pan, zoom, fit and search | Input latency/frame distribution recorded; topology and selection remain correct |
| UI-ACC-PERF-02 Dense hit testing | Select terminals/wires/equipment in overlapping regions at several zoom levels | Correct stable object resolution; p95 query latency recorded |
| UI-ACC-PERF-03 Local edit invalidation | Move one object/change one property in a large network | Unrelated geometry not unnecessarily rebuilt; dirty region and projection work measured |
| UI-ACC-PERF-04 High-rate overlay | Update measurement/operational overlays while navigating | Display coalesces safely; acquisition/history fidelity and UI responsiveness remain independent |
| UI-ACC-PERF-05 Control execution display | Run representative large ladder/control model with active overlays | UI refresh does not block or alter Control cycle/execution |
| UI-ACC-PERF-06 Protection overlay and curves | Show many relay/function states, TCC curves and event markers | Network remains navigable; curve decimation preserves relevant engineering features |
| UI-ACC-PERF-07 Study result scale | Open large result tables/plots while calculation executes | UI remains interactive; display sampling does not alter canonical results |
| UI-ACC-PERF-08 Save/load responsiveness | Load/save representative project sizes | First useful paint, full readiness and save stages measured; no partial project reported saved |
| UI-ACC-PERF-09 Background task staleness | Switch/close document while projection/layout task runs | Stale result discarded/detached; no cross-document mutation |
| UI-ACC-PERF-10 Backend fallback | Force accelerated backend unavailable/unsupported | Correct fallback or clear failure; no blank canvas or semantic mismatch |
| UI-ACC-PERF-11 Cache invalidation | Change theme, scale, DPI, symbol revision and document revision | Correct invalidation; no stale visual or unbounded memory growth |
| UI-ACC-PERF-12 Stress/recovery | Exercise dense geometry, repeated edits, rapid zoom and high-rate events | No crash/data corruption; responsiveness and memory degradation characterized |

### K. Open decisions before approval

1. What are reference hardware tiers and minimum GPU/driver/platform configurations?
2. Which renderer remains V3 default: QGraphicsView/QPainter raster, accelerated QOpenGLWidget, custom painter/scene or another Qt-supported approach?
3. What are supported project-size/workload tiers and representative real-world datasets?
4. Which p95/p99 latency, frame pacing, load-to-first-paint and memory targets are release gates?
5. Which LOD/label suppression rules are acceptable to engineers for SLD, Control, Protection and Study?
6. Which rendering operations may run asynchronously, and what immutable snapshot/revision contract governs them?
7. What display cadence/coalescing policy applies to measurement, Protection, Control and device-feedback overlays?
8. Which cache budgets and invalidation dimensions apply to theme, DPI, symbol library and project revision?
9. What backend fallback and remote-desktop support are required?
10. Who owns performance instrumentation, dataset corpus, benchmark reproducibility and regression review?
11. What is the minimum multi-document memory/responsiveness profile?
12. Which visual details may be reduced at overview zoom, and which engineering semantics must never be hidden?

### L. Gate disposition and invariants

**UI-GATE-05 remains Open.** This proposal defines end-to-end measurement, rendering ownership, culling/LOD/caching/indexing choices to benchmark, discipline-specific behavior, threading boundaries, provisional target bands and candidate acceptance scenarios. No renderer, cache policy, object-count limit or performance threshold is approved.

Frozen architecture invariants:
- Core and Application remain authoritative for engineering state; render snapshots are disposable projections.
- UI rendering and telemetry display cannot become part of Protection/Control execution authority or acquisition/historian fidelity.
- Qt scene/widgets and renderer caches are not project persistence data.
- Asynchronous work is revision- and document-bound; stale results cannot mutate a changed or newly active document.
- Optimizations cannot alter electrical topology, terminal identity, Control logic, Protection decisions, numerical study results or feedback truth.
- Discipline-specific canvas semantics remain distinct even when they share rendering infrastructure.

**Scope boundary:** research register only. No renderer, scene policy, cache, threading model, benchmark harness, project schema, source implementation or V2 behavior was changed. No tests or CI were run.


## 8I-16. Proposed V3 UI/UX scope, priority and dependency-aware delivery roadmap (2026-11-04)

### A. Purpose and status

This section consolidates the UI/UX research and proposed contracts recorded in 8I-1 through 8I-15 into a candidate delivery roadmap. It is a planning and decision aid, not an implementation authorization, approved release scope, resource commitment or declaration that a V3 implementation baseline exists.

The roadmap is constrained by the frozen GridForge architecture: Core owns engineering truth; Application owns controlled mutation, orchestration and lifecycle services; UI is a projection and interaction layer; Control and Protection retain separate execution authorities; shared signal infrastructure supplies typed measurements and provenance without collapsing domain ownership. Qt and other UI implementation details remain outside Core.

**Current baseline limitation:** the V3 implementation repository/branch/ref has not been established by the provenance audit in 8I-9. V2 `main` remains a legacy reference and is not to be relabelled as V3. Consequently, work packages below are candidate requirements and cannot yet be mapped to verified V3 source files, modules, owners or migration costs.

### B. Scope classification

The following classification is proposed for owner review. "Candidate release foundation" means a prerequisite for a coherent, safe and maintainable engineering UI; it does not mean approved release-blocking status.

| Scope class | Candidate work | Rationale / boundary |
|---|---|---|
| Candidate release foundation | Establish V3 source baseline and requirements traceability; stable document/object identity and revision semantics; typed read-model/projection boundary; command/intent and validation feedback contract; project/session lifecycle and recovery semantics; shared navigation, focus and shortcut arbitration; typed diagnostics and status ownership; accessibility baseline | Without these contracts, later workspace work risks inconsistent state, unsafe ambiguity, non-recoverable edits or duplicated interaction logic |
| Candidate core workflow delivery | Shared application shell and workspace composition; SLD authoring/inspection; Control canvas and execution visibility; Protection configuration/operation visibility; Study setup/results workflow; task-oriented Inspector and contextual tool settings | These are the principal engineering tasks and must preserve discipline-specific semantics and execution ownership |
| Candidate operational integration | Signal/channel discovery and provenance presentation; measurement quality/freshness; cross-domain operational trace; command/acknowledgement/feedback distinction; alarm/event/SOE and diagnostic navigation | Makes live and simulated engineering behavior explainable without inventing status or merging authorities |
| Candidate quality and scale | Performance instrumentation and representative workload corpus; culling/LOD/cache/backend evaluation; DPI/theme/font scaling; keyboard/screen-reader and high-contrast validation; multi-document and recovery validation | Provides evidence that the product remains usable across realistic engineering workloads and supported environments |
| Candidate later enhancements | Advanced workspace customization; optional accelerated rendering; advanced trace graph layouts; richer collaboration/review workflows; optional automation conveniences and additional visualization modes | Defer until core workflows, semantic correctness, evidence and platform support are demonstrated; each requires a separate value/risk decision |

The classification is provisional. A feature must not be called mandatory, release-blocking or deferred permanently until the product owner records the applicable decision, rationale, affected users, risks and acceptance evidence.

### C. Dependency-aware delivery sequence

The sequence below is a dependency proposal, not a requirement to execute strictly serially. Parallel work is permissible only after its interface contracts and ownership are agreed.

| Stage | Work package | Required inputs / dependencies | Candidate outputs and exit evidence |
|---|---|---|---|
| 0 | V3 baseline and scope establishment | Repository/branch/ref decision; V2/V3 provenance separation; owner and target-user context | Identified V3 source baseline; requirements-to-source traceability method; explicit in/out-of-scope list; recorded decisions and unresolved gaps |
| 1 | Engineering identity, revision and projection foundations | Stage 0; Core/Application ownership map | Stable document and domain-object identity; distinct topology, instrumentation, Protection, Control, study and document revisions where applicable; immutable typed read-model/projection contracts; stale-result rejection rules; evidence that UI cannot mutate Core directly |
| 2 | Interaction and application-shell foundations | Stage 1; context-of-use findings | Workspace composition contract; navigation and panel visibility rules; consistent selection/activation semantics; focus-aware shortcut arbitration; command/undo affordances; non-modal feedback/navigation conventions; keyboard-operable core tasks |
| 3 | Project and session lifecycle | Stage 1 identity/revision; application command and persistence ownership | Explicit lifecycle for new/open/save/save-as/close, dirty state, draft handling, recovery, migration and failure; atomicity and corruption behavior; canonical project versus preferences/layout/viewport/transient state separation; recovery evidence |
| 4 | Inspector, diagnostics and status foundations | Stages 1–3; typed domain/application diagnostic ownership | Task-oriented Inspector sections; typed diagnostic envelope and lifecycle; status/read-model ownership; filtering, severity, timestamp, source/object context and navigation; explicit separation of validation, alarm, Protection event, Control execution, measurement quality and command/feedback |
| 5 | Discipline-specific workflow delivery | Stages 1–4; each domain's public Application contracts and product workflow approval | SLD authoring and inspection; Control logic/canvas and cycle diagnostics; Protection configuration, channel association, operation and TCC/coordination views; Study setup and result exploration. Each retains domain-specific interaction and authority |
| 6 | Operational signal and trace integration | Stages 1, 4 and 5; shared signal/measurement contracts; Protection/Control integration contracts | Source/channel discovery and provenance; engineering units, timestamps, freshness and quality; correlated timeline/evidence graph; distinct measurement, decision, intent, command, acknowledgement and physical feedback stages; missing-evidence and revision-drift handling |
| 7 | Accessibility, platform and performance qualification | Stages 2–6; supported platform/hardware and workload decisions | Accessibility semantics and keyboard/screen-reader evidence; DPI/theme/font/high-contrast evidence; representative workload corpus; measured rendering/input/load/save behavior; backend/fallback decision supported by benchmark results |
| 8 | Release-scope review and controlled implementation freeze | All prior stages; owner decisions and evidence | Approved scope and release criteria; accepted/deferred risks; traceability from requirements to source and evidence; migration and support plan; explicit implementation freeze/version baseline |

**Dependency guardrails**
- Do not build discipline workspaces on unversioned or ambiguous object/read-model identity.
- Do not implement persistence behavior until canonical project data, persisted drafts, user preferences, workspace layout, per-document viewport metadata and transient interaction state have explicit ownership and serialization boundaries.
- Do not create a universal canvas that erases SLD, Control and Protection interaction semantics. Share contracts and infrastructure only where behavior is genuinely common.
- Do not derive Protection or Control execution status from a UI refresh, renderer event, generic alarm string or untrusted measurement.
- Do not present a command as successful merely because it was issued; distinguish request, dispatch, acceptance/acknowledgement and physical feedback.
- Do not make visual decimation or LOD modify canonical engineering values, study datasets, topology or operational evidence.
- Do not use performance targets as acceptance gates until hardware tiers, workload corpus and measurement methods are approved.

### D. Candidate priority model

Each work package and requirement should be scored qualitatively against the following dimensions. Scores support discussion; they must not be summed into a false-precision ranking.

1. **Engineering/safety consequence:** could ambiguity or incorrect presentation contribute to an unsafe engineering decision or conceal a material condition?
2. **Task criticality:** is the capability required to complete a primary engineering task?
3. **Architectural dependency:** does it unblock several other packages or prevent incompatible implementations?
4. **Operational exposure:** does it affect live/simulated operation, data integrity, traceability or recovery?
5. **User frequency and reach:** how often is the task performed and how many roles/workflows depend on it?
6. **Failure recoverability:** can a user detect, understand and safely recover from failure?
7. **Evidence and uncertainty:** is the requirement source-confirmed, runtime-unverified, inferred or still a hypothesis?
8. **Implementation and migration cost:** what is the verified V3 change surface, compatibility burden and rollout risk?

Suggested priority labels:
- **P0 — Foundation blocker:** unresolved contract or provenance issue prevents safe, traceable implementation of dependent work.
- **P1 — Primary workflow:** required for an approved primary engineering workflow or its trustworthy operational interpretation.
- **P2 — Usability and scale:** materially improves efficiency, accessibility, resilience or performance after core correctness is established.
- **P3 — Enhancement:** optional capability with lower dependency or task criticality.

Priority labels remain proposals until the product owner approves them. A high-severity safety or data-integrity concern may be a blocker even if implementation frequency is low.

### E. Work-package definition of done

Every implementation work package should record, before implementation authorization:

- unique work-package ID and linked requirement/finding IDs;
- user role, context of use and engineering task;
- explicit scope, exclusions and affected discipline(s);
- verified V3 repository, branch, commit and source paths;
- Core, Application, domain and UI ownership boundaries;
- public contracts, typed inputs/outputs, identity and revision behavior;
- dependencies, migration/compatibility impact and rollback strategy;
- failure, stale-data, missing-data and recovery behavior;
- accessibility and platform implications;
- acceptance scenarios and required evidence, including runtime walkthrough where relevant;
- performance/workload expectations where applicable;
- risks, unresolved decisions, accountable owner and approval disposition.

A package is not complete merely because a widget or screen exists. Completion requires demonstrated task flow, truthful state presentation, correct command/validation behavior, failure handling, domain-boundary compliance and evidence appropriate to the risk.

### F. Candidate release gates and decision records

The existing gate register remains authoritative for approval structure:

- UI-GATE-01 Context of use
- UI-GATE-02 Project/session
- UI-GATE-03 Diagnostics
- UI-GATE-04 Accessibility/platform
- UI-GATE-05 Display/performance
- UI-GATE-06 Cross-domain trace
- UI-GATE-07 Scope/priority

For each gate, record one disposition: **Approved**, **Approved with constraints**, **Deferred**, **Rejected** or **Blocked**. The decision record must include owner, date, scope, rationale, constraints, evidence reviewed, accepted risks, follow-up actions and affected work packages. An open gate cannot be treated as approved by implication, silence, roadmap ordering or a candidate acceptance scenario.

Candidate release review should verify at minimum:
- all approved P0/P1 requirements are traceable to implementation and evidence;
- no Core/UI dependency inversion or cross-domain authority collapse has been introduced;
- canonical project integrity, draft semantics and recovery behavior are demonstrated;
- Protection and Control decisions, commands and physical feedback remain distinct;
- measurements expose source, unit, timestamp and quality/freshness where relevant;
- critical engineering tasks are operable with keyboard and accessible semantics;
- performance claims are supported by reproducible workloads and agreed hardware;
- unresolved defects and limitations are explicitly accepted, deferred or blocking.

### G. Open decisions

1. Which repository, branch and commit are the authoritative V3 implementation baseline, and who owns its creation/maintenance?
2. Which user roles, plant/utility contexts and primary task journeys define the initial V3 release?
3. Which candidate release-foundation items are genuinely release-blocking versus staged post-initial-release work?
4. Which engineering workflows must be complete in the first V3 usable increment: SLD, Control, Protection, Study, or a defined subset?
5. What are the approved boundaries for persisted engineering drafts, recovery snapshots, preferences, workspace layout and viewport state?
6. Which cross-domain trace capabilities are required for the initial release, and which are advanced diagnostics?
7. What supported operating systems, DPI configurations, GPU tiers and remote/virtual desktop scenarios are in scope?
8. Which accessibility standard/target and conformance evidence will be claimed, and for which supported workflows?
9. Who approves workload datasets, latency targets, memory budgets and renderer/backend choices?
10. What staffing, sequencing and migration constraints should alter the dependency proposal?
11. Which candidate acceptance scenarios become formal release criteria, and who signs off each discipline?
12. What is the process for handling a safety-relevant defect discovered after a gate has been approved?

### H. Gate disposition and scope boundary

**UI-GATE-07 remains Open.** This section proposes a dependency-aware roadmap, candidate scope classes, priority criteria, work-package definition of done and release decision process. It does not approve the proposed priority labels, mandatory scope, delivery dates, resource allocation, implementation branch, renderer, acceptance thresholds or release criteria.

All earlier UI gates remain subject to their recorded dispositions; no approval is inferred from this roadmap. The V3 source baseline remains an explicit prerequisite for source-level implementation planning.

**Scope boundary:** research register only. No source implementation, UI behavior, project schema, V2 code, tests or CI were changed or run.


## 8I-17. Proposed V3 role-based engineering workflow and task-journey contracts (2026-11-04)

### A. Purpose, evidence class and boundary

This section translates the V3 architecture and UI/UX contracts into candidate end-to-end engineering task journeys. It defines what each user is trying to accomplish, the information required, the interaction sequence, the system response, failure/recovery behavior and completion evidence.

These are **proposed task models**, not findings from observed user research, usability testing or a runtime walkthrough. The role names describe common responsibilities, not mutually exclusive account types or permission groups. One engineer may perform several roles. The journeys must be validated with representative engineers and actual project workflows before they become approved product requirements.

The journeys do not alter the frozen domain boundaries:
- Core remains the authority for engineering entities, terminals, topology, domain validation, Protection/Control models and study calculations.
- Application services and commands own controlled changes, orchestration, persistence and event publication.
- UI gathers user intent, displays typed read models and diagnostics, and routes commands through the approved application boundary.
- SLD, Control, Protection and Study retain discipline-specific models and interactions. A shared shell or interaction contract must not turn them into one generic editor.
- Signal/measurement infrastructure provides typed values, source identity, units, timestamps, calibration and quality/provenance. It does not own Protection or Control execution decisions.
- ProtectionDecision, Control evaluation/action, DeviceCommand, transport acknowledgement and physical DeviceFeedback remain distinct evidence stages.

### B. Common task-journey contract

Every primary journey should use the following structure:

1. **Orient:** identify the active project/document, workspace, saved/dirty state, active operating context and relevant revision.
2. **Locate:** find the equipment, network object, channel, logic element, study case or operational event through the appropriate explorer, canvas, list or search.
3. **Inspect:** see identity, engineering properties, source/provenance, status, units, quality and applicable constraints without confusing missing information with a valid default.
4. **Act:** make a typed user request through a task-appropriate editor/tool; distinguish preview/draft from committed engineering state.
5. **Validate:** show object-specific and cross-object validation with severity, source, affected object, revision and corrective guidance. Do not silently repair or discard user intent.
6. **Commit or execute:** make the explicit transition through the owning Application/domain contract. Editing a UI projection is never a domain mutation.
7. **Verify outcome:** display the authoritative resulting state and any asynchronous processing, command acknowledgement or physical feedback separately.
8. **Recover or continue:** preserve the user's work where safe; provide actionable recovery, undo/redo where supported, and navigation to related evidence.
9. **Close or hand off:** identify what was saved, committed, executed, blocked or left as a draft; expose unresolved issues and next required action.

Common UI requirements:
- Persistent document/workspace identity and clear active-selection context.
- A predictable distinction between selection, editing, preview, draft, committed state and execution.
- No success indication before the owning service reports success.
- Validation and operational diagnostics must not be collapsed into one untyped message stream.
- All actionable errors must identify the affected object/context and provide a safe next step or explain why no action is available.
- High-impact actions require explicit confirmation or a domain-defined authorization mechanism; confirmation dialogs must not replace domain validation.
- Long-running work must expose progress/cancellation semantics where cancellation is actually supported, and must not block the UI event loop.
- On document switch/close, late asynchronous results must remain bound to their originating document and revision.
- Keyboard access and accessible names/semantics must exist for the primary journey, not merely for surrounding panels.

### C. Journey E-01 — Electrical engineer: create and maintain the network in SLD

**User goal:** construct or revise a single-line representation that corresponds to canonical electrical equipment and connectivity, then inspect and save a valid project.

**Entry context**
- Start or open a named project; SLD is the primary electrical-network workspace for a new project.
- The project/session indicator identifies the active document and whether it is saved, dirty, recovering or read-only.
- Project Explorer, equipment palette, canvas and Inspector are discoverable without requiring the engineer to infer hidden panel state.

**Candidate sequence**
1. Create/open project and confirm project identity and initial workspace state.
2. Select equipment from a searchable, categorized palette; inspect symbol/type and required engineering properties.
3. Place equipment using a live preview. The preview is explicitly non-domain state.
4. Commit placement through the owning command, creating the Core equipment and a separate SLD representation. The symbol is not itself the equipment.
5. Select the placed equipment and enter/edit required engineering values through a typed Inspector. Show units, valid ranges, defaults and required fields.
6. Place additional equipment and connect terminals using the SLD wire/connection workflow. Show compatible terminals and snap candidates without allowing a visual snap to silently imply a valid electrical connection.
7. Inspect the connection and endpoint identities; expose validation for incompatible, missing, duplicate or ambiguous connectivity at the appropriate commit/validation boundary.
8. Run project/network validation. Present findings by severity, object and corrective action, and allow navigation from a finding to the affected equipment or connection.
9. Save the canonical project. Show save completion and document revision only after persistence succeeds.
10. Reopen or revisit the project and verify the saved equipment, topology and SLD layout are restored.

**Required information**
- Equipment identity/type, rating and applicable engineering parameters.
- Terminal identity and compatibility.
- Connection endpoint identities and connectivity state.
- Object/project revisions, validation result and save state.
- Clear distinction between committed Core objects, SLD projection/layout and transient tool preview.

**Failure and recovery**
- Failed placement must not leave an orphan symbol or hidden Core object.
- Failed connection must preserve the pre-existing network and explain the rejected intent.
- Invalid/incomplete equipment properties must remain inspectable and correctable; do not imply the network is validated.
- Stale selection or asynchronous projection updates must not redirect an edit to a different object.
- Save failure must leave the project visibly unsaved and preserve recoverable user work.
- Reopening must not convert a screenshot or graphics-scene serialization into the canonical electrical model.

**Completion evidence**
- Equipment and terminal identities resolve to Core-owned objects.
- Connections/topology match the committed engineering model.
- Validation findings are explicit and navigable.
- Canonical project save/reopen preserves the agreed project scope and layout.
- No UI symbol, graphics item or scene object is treated as engineering truth.

### D. Journey P-01 — Protection engineer: configure measurement inputs and protection functions

**User goal:** configure a protection device using trustworthy measurement sources, establish protection functions/settings and verify that the configuration is complete without confusing configuration with live operation.

**Entry context**
- Open a project with the relevant network and protection equipment.
- Protection workspace identifies relay/device, configuration revision and available measurement channels.
- The engineer can discover eligible channels, not only channels already bound to the selected relay.

**Candidate sequence**
1. Locate the relay/protection device and inspect identity, installed functions, settings revision and configuration status.
2. Discover candidate CT/PT/CVT instruments and measurement channels through source identity and electrical association; show physical instrument, primary/secondary terminals, channel, units, scaling/calibration and source provenance.
3. Inspect sample availability, timestamp, freshness and quality separately from configuration validity. A configured channel is not automatically a trusted live measurement.
4. Bind or change the measurement source using a typed configuration action. Show the target relay input/function and the exact source being associated.
5. Configure protection elements and settings using the applicable function catalogue and typed engineering units/ranges.
6. Validate instrument association, input type, phase/polarity/scaling where modeled, function configuration, setting dependencies and required measurement inputs.
7. Commit the configuration through the Protection/Application contract; show the resulting configuration revision and any rejected fields.
8. Inspect operational evaluation separately: input measurements and quality, evaluation status, ProtectionDecision (if produced), target mapping and subsequent command/feedback evidence if the system has progressed to those stages.
9. Inspect TCC/coordination views and analysis coverage using canonical settings/results; clearly identify unavailable or incomplete model coverage.
10. Save the project/configuration and record unresolved configuration or operational limitations.

**Required information**
- Relay/device identity, function identity/code and configuration revision.
- Instrument/channel identity and source-terminal/network association.
- Measurement units, timestamp, quality, calibration/scaling and availability.
- Function settings, validation results and model/coverage limitations.
- Distinct ProtectionDecision, output intent/mapping, DeviceCommand, acknowledgement and DeviceFeedback evidence.

**Failure and recovery**
- Missing, stale, bad-quality or uncalibrated measurements must not be displayed as trusted live inputs.
- A missing channel must not be silently substituted with another source.
- A configuration edit must not silently alter physical topology revision.
- Instrumentation/configuration changes must be distinguishable from topology changes in revision and audit history.
- Unsupported or incomplete protection-function model coverage must be disclosed; do not fabricate a result.
- No command or trip success is implied by a ProtectionDecision alone.
- Failed configuration commit must preserve the previous accepted configuration and show field/object-level diagnostics.

**Completion evidence**
- Each configured input traces to an identifiable instrument/channel and source.
- Configuration and measurement quality are independently visible.
- The accepted Protection configuration revision is known.
- Evaluation and downstream actuation stages are presented only when supported by actual evidence.
- Protection remains a separate execution authority.

### E. Journey C-01 — Control engineer: build, inspect and evaluate control logic

**User goal:** construct or modify control logic, map its inputs/outputs, evaluate the logic and understand blocked actions and resulting device commands/feedback.

**Entry context**
- Open the Control workspace and its dedicated canvas/model.
- Control palette exposes categorized equipment/logic elements with meaningful names, icons, keyboard access and tool descriptions.
- The active Control document and revision are visible.

**Candidate sequence**
1. Locate the target control scheme and inspect its current logic, I/O mappings and revision.
2. Add logic elements (contacts, coils, timers, gates, latches or supported control blocks) using a preview-then-commit workflow.
3. Connect logic terminals/channels using Control-specific connection semantics. Do not reuse SLD electrical wire rules merely because both canvases use lines.
4. Configure each element's parameters and equipment action binding through distinct, task-oriented Inspector sections.
5. Discover available input/output channels and inspect source, direction, type, units/value representation, quality, freshness and binding status.
6. Validate logic connectivity, required inputs, type compatibility, output mapping, interlocks and action targets before accepting the configuration.
7. Commit the logic/configuration revision through the Control/Application contract.
8. Request an evaluation or observe the configured execution cycle. Present cycle identity, inputs, evaluated logic, decisions, blocked actions, diagnostics and execution timing as read-only evidence.
9. Where an action is authorized, distinguish Control intent/decision from DeviceCommand dispatch, transport acknowledgement and physical DeviceFeedback.
10. Inspect the result and navigate from blocked action or diagnostic to the relevant logic element, input, interlock or target.

**Required information**
- Control element identity/type, parameters and connection graph.
- Channel identity, direction, data type, quality/freshness and binding.
- Logic/configuration revision and cycle/evaluation identity.
- Interlock condition, blocked-action reason and authorized target.
- Command, acknowledgement and physical feedback as separate records.

**Failure and recovery**
- Missing channel availability must be visible before or during binding; do not invent a channel or treat a placeholder as a live source.
- Type/connection errors must identify both endpoints and the violated contract.
- A blocked action must show the specific interlock/condition and must not be represented as a successful actuation.
- An evaluation completion message must not be interpreted as every requested action succeeding.
- UI refresh and rendering cadence must not throttle or alter Control execution cadence.
- Failed edits/commit must preserve the last accepted logic revision and expose recovery.
- Late cycle results must remain bound to their originating Control document/configuration revision.

**Completion evidence**
- The Control logic graph and channel mappings are accepted by the Control domain.
- The evaluated cycle and its inputs/diagnostics are traceable.
- Blocked actions and commands are not conflated.
- Device feedback is displayed only when actually received and correlated.
- Control remains a separate execution authority from Protection.

### F. Journey S-01 — Study engineer: configure, run and interpret an engineering study

**User goal:** configure a reproducible study from a known project state, execute the selected solver and inspect results without confusing display transformations with canonical numerical data.

**Entry context**
- Select a project and a named study case.
- Show the project/model revision and study configuration revision used by the case.
- Identify the study type and required model inputs before exposing advanced options.

**Candidate sequence**
1. Create or select a study case and choose the study type.
2. Inspect the applicable model snapshot and required inputs. Identify missing or invalid model data before execution.
3. Configure study options using progressive disclosure: common settings first, advanced solver/model settings when requested.
4. Validate the configuration and show the exact model/configuration revisions that will be used.
5. Start the study through the owning Application service; show queued/running/completed/failed/cancelled states only when supported by actual task state.
6. Present result summary, convergence/status, warnings and limitations. Distinguish a valid completed result from partial, failed or unsupported output.
7. Explore results through tables, plots, one-line overlays or reports while preserving units, sign conventions, base values, reference directions and relevant numerical precision.
8. Compare cases only when their model/configuration basis is visible and comparison is technically meaningful.
9. Export/report results with source project, study case, revisions, solver/options and result provenance.
10. Save study configuration/results according to the approved project persistence contract.

**Required information**
- Study type, case identity and solver/configuration options.
- Source project/model revision and input snapshot identity.
- Execution lifecycle, diagnostics, convergence and limitations.
- Result units, bases, precision, provenance and canonical dataset identity.
- Display transformations such as filtering, decimation or resampling, clearly separated from source numerical data.

**Failure and recovery**
- Missing model data must not be replaced with guessed defaults without an explicit domain-approved rule.
- Solver failure or non-convergence must not appear as a valid result.
- Stale background results must not attach to a changed project or another active document.
- Plot decimation/LOD must not alter canonical result datasets or exported numerical values.
- Cancellation must be reported only if the solver/service confirms cancellation semantics.
- Export failure must not mark the study result as saved or exported.

**Completion evidence**
- Study execution is traceable to an immutable or otherwise identified input snapshot and configuration.
- Result status and limitations are explicit.
- Plots/tables preserve engineering interpretation and canonical values.
- Exported reports identify source and result provenance.

### G. Journey O-01 — Operations/commissioning engineer: trace a condition across measurement, Protection, Control and actuation

**User goal:** investigate an operational condition and determine what was measured, evaluated, decided, commanded, acknowledged and physically observed.

**Entry context**
- Enter from a typed alarm/event, device, relay, Control scheme, measurement channel or time-window search.
- Identify the selected asset/project and time basis; distinguish current live state from historical evidence.

**Candidate sequence**
1. Locate the event/condition and inspect its source, timestamp, severity, acknowledgement state and affected asset.
2. Navigate to the originating measurement or input sample; inspect source identity, units, timestamp, quality, calibration and freshness.
3. Inspect the relevant Protection evaluation or Control cycle without implying that one domain owns the other's execution.
4. Follow explicit typed relationships: input/evidence, evaluation, decision, interlock, output intent, command dispatch, transport acknowledgement, physical feedback and correlated event.
5. Compare event times and revision identities; expose clock uncertainty, missing historian intervals, stale samples and configuration/topology drift.
6. Inspect the affected equipment and network context in its discipline-specific workspace.
7. Acknowledge or otherwise act on the event only through the category's authorized lifecycle; acknowledgement must not clear a physical condition or alter a Protection/Control decision.
8. Produce/export an investigation record with linked evidence and explicit gaps.

**Required information**
- Event and sample identities, source and timestamps.
- Quality/freshness and historian completeness.
- Protection and Control execution identities/revisions.
- Typed causal/evidence relationships with provenance.
- Command/acknowledgement/feedback state and correlation confidence.
- Current versus historical context and revision drift.

**Failure and recovery**
- Missing evidence must appear as a gap, not a synthetic link or inferred success.
- Correlation by timestamp alone must not be presented as proven causation.
- An alarm acknowledgement must not be treated as clearance, reset or physical restoration.
- A Protection decision must not be represented as a Control command; a command must not be represented as physical feedback.
- If data sources disagree or clocks are uncertain, expose the uncertainty and preserve original timestamps.
- Historical investigation must not mutate current operational state.

**Completion evidence**
- The investigation record distinguishes measured fact, domain evaluation, decision, command, acknowledgement and physical feedback.
- Every relationship is typed and traceable to its source.
- Gaps, stale data and revision drift are explicit.
- User acknowledgement/action follows the owning lifecycle and leaves operational authority unchanged.

### H. Journey X-01 — Project owner/reviewer: open, review, save, recover and hand off work

**User goal:** manage the project and session safely across normal work, interruption, failure and handoff.

**Candidate sequence**
1. Create/open a project and verify identity, package validity and schema compatibility.
2. Inspect recent/recovery candidates without silently opening or overwriting a different project.
3. Review dirty-state scope: canonical engineering model, persisted engineering draft, workspace layout, preferences and viewport metadata must be distinguishable.
4. Save or Save As with clear target path, overwrite behavior and atomic success/failure reporting.
5. Close or switch documents with explicit Save/Discard/Cancel semantics for each relevant dirty scope.
6. Recover after interrupted work using an identified recovery point and show which changes are restored, omitted or unresolved.
7. Migrate an older package only through an explicit, versioned and recoverable migration path.
8. Hand off the project with canonical content and required dependencies contained in the approved package contract; machine-specific preferences and transient state must not silently contaminate canonical engineering content.

**Required information**
- Project/package identity, schema version and integrity state.
- Canonical model revision, draft state and per-scope dirty indicators.
- Save destination, atomicity and overwrite consequences.
- Recovery point identity/time and restoration scope.
- Migration source/target versions and warnings.

**Failure and recovery**
- Corrupt or incompatible project packages must fail safely and preserve the original.
- Save failure must not clear dirty state.
- Recovery must not silently overwrite newer canonical data.
- Discard must identify the state being discarded; no hidden draft or committed engineering mutation may be lost without the corresponding user decision.
- Workspace and viewport restoration failures must not corrupt the canonical project.
- No external dependency may be required for a portable canonical project where the frozen package contract requires self-containment.

**Completion evidence**
- Open/save/close/recovery/migration outcomes are explicit and reproducible.
- Canonical engineering content remains portable and integrity-checked.
- Drafts, preferences, workspace layout, viewport metadata and transient state follow approved persistence boundaries.
- The reviewer can identify what is committed, saved, recoverable and unresolved.

### I. Cross-journey navigation and handoff requirements

The journeys should be connected through stable semantic references, not duplicated or loosely matched display labels.

- Selecting an equipment object in SLD should allow navigation to related Protection, Control and Study views only where a real typed relationship exists.
- A Protection measurement input should navigate to its instrument/channel provenance and relevant network location without changing topology.
- A Control channel mapping should navigate to the channel source and affected Control element; the UI must preserve the distinction between input source and output target.
- A Study result should navigate to the source case, model revision and relevant network objects without mutating the study snapshot.
- An operational event should navigate to source measurement, Protection/Control evaluation, command and feedback evidence using typed relationships.
- Navigation across documents/workspaces must preserve origin context, selection identity and revision; if the target is stale or unavailable, explain why and offer a safe refresh/reload path.
- Cross-domain links are evidence/navigation relationships; they do not transfer domain ownership or execution authority.

### J. Candidate journey acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-JRN-01 | Place and configure SLD equipment | Preview is transient; commit creates domain equipment and separate SLD projection; properties are typed and editable |
| UI-ACC-JRN-02 | Connect SLD terminals | Committed connection resolves exact terminal identities; invalid connection is rejected with actionable diagnostics |
| UI-ACC-JRN-03 | Save/reopen SLD project | Canonical equipment/topology and approved layout persist; no scene/screenshot is treated as model |
| UI-ACC-JRN-04 | Discover and bind Protection channel | Eligible source channels can be discovered; source, instrument and quality are visible before accepted binding |
| UI-ACC-JRN-05 | Change Protection configuration | Configuration revision changes independently from physical topology revision; failed commit preserves accepted configuration |
| UI-ACC-JRN-06 | Inspect Protection-to-actuation chain | Decision, output intent, command, acknowledgement and physical feedback remain distinct and evidence-backed |
| UI-ACC-JRN-07 | Build and evaluate Control logic | Control-specific graph semantics and channel mapping validate; cycle and blocked-action diagnostics are navigable |
| UI-ACC-JRN-08 | Trace Control action | Evaluation, interlock, command, acknowledgement and physical feedback are separate and correlated by explicit evidence |
| UI-ACC-JRN-09 | Configure and run Study | Run identifies source snapshot/configuration; failed or partial results are not shown as valid completion |
| UI-ACC-JRN-10 | Explore/export Study results | Display transformations do not change canonical numerical data; export includes provenance and units |
| UI-ACC-JRN-11 | Investigate cross-domain event | Timeline/graph exposes typed links, data gaps, time uncertainty and revision drift; no causation is invented |
| UI-ACC-JRN-12 | Recover and hand off project | Recovery scope is explicit; canonical package remains portable; save/recovery failures preserve user data |
| UI-ACC-JRN-13 | Complete primary task by keyboard | Core journey can be completed without pointer-only controls; focus and shortcut behavior are predictable |
| UI-ACC-JRN-14 | Switch document during background work | Late results remain bound to origin document/revision and cannot contaminate active document |
| UI-ACC-JRN-15 | Navigate from diagnostic to object | Typed diagnostic retains source, severity, timestamp and object identity through navigation |

These scenarios are candidates for future validation. They are not approved release criteria and do not establish that the current application passes them.

### K. Research and validation still required

1. Conduct contextual interviews and task observation with electrical, Protection, Control, Study and commissioning/operations engineers across representative plant and utility contexts.
2. Validate role/task overlap, actual terminology, common task frequency, exception paths and handoff responsibilities.
3. Collect representative project artifacts and workflows, with sensitive operational data protected and appropriately anonymized.
4. Observe real SLD placement/edit/connect/validate/save workflows, including large and partially configured networks.
5. Validate instrument/channel discovery and configuration with real CT/PT/CVT and measurement-channel models, including missing, stale and bad-quality samples.
6. Validate Control logic editing, channel availability, interlocks, cycle diagnostics and command/feedback visibility against supported Control equipment and execution semantics.
7. Validate Protection function configuration and live evaluation with actual supported function models and model-coverage boundaries.
8. Validate study setup, solver progress, result interpretation and export with domain engineers and canonical numerical datasets.
9. Validate operational trace with historian gaps, clock skew, revision drift, missing acknowledgements and unavailable physical feedback.
10. Run moderated usability sessions and record task completion, errors, recovery, time-on-task and user confidence; do not infer usability from code inspection alone.
11. Confirm keyboard, screen-reader and accessibility behavior on the supported Qt/platform matrix.
12. Reconcile findings into requirement IDs, priority proposals, domain ownership and implementation work packages before authorization.

### L. Gate disposition and invariants

**UI-GATE-01 remains Open pending owner approval of context-of-use and role/task evidence. UI-GATE-07 remains Open pending approval of initial release scope and priority.** The candidate journeys also depend on the project/session, diagnostics, accessibility, performance and cross-domain trace gates already recorded in this register.

Frozen invariants:
- The SLD symbol is a representation, not the electrical equipment.
- Control and Protection remain separate execution authorities.
- Shared measurement infrastructure does not own domain decisions.
- UI status is derived from typed, authoritative evidence and cannot invent acknowledgement, success, clearance or physical feedback.
- Draft, committed model, persisted project, workspace preferences and transient interaction remain distinct.
- A rendering, navigation or display optimization cannot alter engineering truth or canonical numerical data.
- Every mutation follows the UI → Controller → Command → Application → Core → Event → Projection → UI path, with the owning domain contract enforced.

**Scope boundary:** research register only. No source implementation, UI behavior, permission model, project schema, V2 code, tests or CI were changed or run.


## 8I-18. Proposed V3 information architecture and navigation model (2026-11-04)

**Purpose:** define a coherent application information architecture that lets engineers understand where they are, find the right engineering object or task, move between related workspaces and inspect authoritative evidence without collapsing distinct engineering disciplines into one generic editor.

**Status:** research proposal. This section does not approve a final navigation design, role/permission model, workspace implementation or V3 release scope.

### A. Information architecture principles

1. **Project is the navigation root.** A project groups canonical engineering content and its related study/configuration artefacts under the approved project lifecycle contract. A workspace is a task-oriented view over project-owned or explicitly associated data; it is not a second project database.
2. **Domain ownership remains explicit.** Electrical/SLD, Protection, Control, Instrumentation & Signals, Studies and Diagnostics/Operations are distinct task areas. Shared navigation does not imply shared domain execution or a generic canvas.
3. **Stable identity over labels.** Navigation targets use stable semantic object/document IDs and typed relationships. Display names, tree paths and search text are not identity.
4. **Context-preserving navigation.** A cross-workspace transition carries origin workspace, document identity, selected object/evidence identity, relevant revision and time context. The destination must report when an object or revision is stale, unavailable or historical.
5. **Progressive disclosure.** Expose the common engineering task and its current context first; reveal advanced configuration, specialist tools and secondary metadata when relevant. Do not hide essential state or validation behind deep menus.
6. **One visible authority per action.** Each mutating action is presented by the workspace/controller that owns it and routes through Application commands/services. Shared shell controls must not create alternate mutation paths.
7. **Search complements, not replaces, hierarchy.** Project hierarchy supports known structural context; global/project search supports discovery by identity, designation, type, property and supported relationships.
8. **Navigation is not evidence.** A link between Protection, Control, measurement, topology or Study objects is only as strong as its typed source relationship. The UI must not infer causation or ownership from proximity, names or timestamps alone.
9. **Workspace state is not engineering truth.** Open tabs, panel visibility, selection, active tool, viewport and navigation history follow the approved session/presentation persistence policy and never mutate canonical engineering state.
10. **Accessibility is structural.** Every navigation destination and action must have a keyboard-accessible route, meaningful accessible name, predictable focus behavior and screen-reader-readable hierarchy/state.

### B. Proposed top-level application hierarchy

The following is a candidate navigation taxonomy, not a mandatory left-menu implementation:

| Level | Candidate area | Primary responsibility | Typical contents |
|---|---|---|---|
| Project root | Project Overview | Project identity, health and entry points | Project summary, model revision, validation summary, recent work, recovery notices |
| Engineering | Electrical / SLD | Electrical network authoring and inspection | SLD documents/sheets, equipment, terminals, connections, layout |
| Engineering | Instrumentation & Signals | Instrument and signal/channel lifecycle | CT/PT/CVT, sensors, acquisition channels, typed signals, quality, calibration, routing |
| Engineering | Protection | Protection configuration and evaluation | Relays, functions, settings groups, inputs, zones, decisions, TCC/coordination |
| Engineering | Control | Control logic authoring and evaluation | Control documents, logic elements, I/O mapping, interlocks, cycles, blocked actions |
| Engineering | Studies | Reproducible engineering analyses | Study cases, configurations, runs, result sets, comparisons and reports |
| Engineering | Equipment & Assets | Cross-document equipment identity and properties | Equipment register, designation, nameplate, lifecycle and references |
| Assurance | Validation & Diagnostics | Typed validation and engineering diagnostics | Findings, severity, owner, source, object links, resolution lifecycle |
| Assurance | Operational Trace | Evidence-based cross-domain investigation | Timeline, typed evidence graph, measurement-to-feedback trace |
| Project services | Reports & Exchange | Controlled outputs and interoperability | Reports, exports, imports, schema/migration summaries |
| Application | Preferences / Workspace | User and machine presentation settings | Theme, density, keyboard map, workspace layout, panel state |

The final taxonomy must be validated against actual engineer terminology and task frequency. Do not create duplicate navigation entries merely because an object participates in multiple domains; use typed cross-references and contextual links.

### C. Shared application shell and workspace frame

Candidate shell regions:

- **Application menu / command access:** project lifecycle, edit/history, view/workspace, tools, window/document and help commands. Commands should have one discoverable canonical action with consistent shortcut, enablement and explanatory state.
- **Workspace switcher:** clearly identifies canonical workspaces (SLD, Instrumentation & Signals, Protection, Control, Studies, Diagnostics/Operations) separately from compatibility or auxiliary views.
- **Project Explorer:** hierarchical, searchable project/document/object navigation. Supports filtering, expand/collapse, object-type grouping and contextual actions owned by the selected object/domain.
- **Central workspace/document area:** hosts the active discipline-specific editor or read-only view. Multiple documents may be open where approved; active document and revision must remain visible.
- **Inspector:** contextual properties and configuration for the current selection/document. Separates read-only engineering facts, editable configuration intent, calculated values and live/observed values.
- **Tool Palette / task tools:** context-sensitive tools for the active workspace; tool names, icons, shortcuts, availability and disabled reasons are explicit. A tool from one domain must not silently carry into another domain.
- **Diagnostics / Messages:** typed findings and event streams with category, source, time, severity, lifecycle, object navigation and filtering. Not a single untyped message list.
- **Status / activity region:** project/document dirty state, active tool, selection, coordinates where meaningful, validation state, background task status and domain-specific quality/freshness/operation summaries only where authoritative evidence exists.

Panel docking, floating, hiding, resizing and workspace presets are presentation capabilities. Essential actions and critical state must remain discoverable when panels are collapsed or layouts are reset.

### D. Workspace-specific information architecture

**D1. Electrical / SLD**
- Primary hierarchy: project → electrical network/document → sheet/area → equipment and connections.
- The canvas is the main electrical-network projection; Explorer and Inspector provide complementary structural/property views.
- Equipment, terminal, topology and connection identity remain Core-owned; symbol and layout are separate projection data.
- Context actions distinguish equipment operations, terminal/connectivity operations and drawing/layout operations.
- Selecting a symbol resolves the semantic equipment identity; selection of a conductor/terminal resolves the actual connection/terminal identity.
- Cross-links to Protection, Instrumentation, Control or Study appear only where typed relationships exist.

**D2. Instrumentation & Signals**
- Primary hierarchy: instrument/source → measurement or signal → acquisition/communication channel → consumer/subscription.
- Provide separate views for physical instrument configuration, channel allocation/availability, signal processing/routing and consumer bindings.
- Show source identity, terminal/connection where relevant, channel direction/type, units, scaling, timestamp, quality, freshness, calibration and provenance as separate attributes.
- A configured channel is not automatically allocated, connected, healthy, fresh or valid; lifecycle dimensions must remain visible.
- Navigation to a Protection or Control consumer is a reference/handoff, not a change in domain ownership.

**D3. Protection**
- Primary hierarchy: Protection scheme/relay → function elements/settings → input bindings and measurement provenance → evaluation/decision evidence → output/actuation trace.
- Separate configuration, read-only runtime/evaluation, diagnostics and coordination/analysis tasks.
- Display configuration revision independently of physical topology revision and instrumentation/channel revision.
- Show unsupported or restricted model coverage explicitly; do not imply a complete catalogue from a partial function list.
- Protection remains the authority for Protection evaluation and ProtectionDecision.

**D4. Control**
- Primary hierarchy: Control document/scheme → logic network → elements/connections → I/O bindings → interlocks/actions → execution-cycle evidence.
- Keep Control-specific graph/ladder/function-block semantics; do not inherit SLD electrical connection semantics solely for visual consistency.
- Separate logic editing, channel mapping, equipment action binding, cycle monitoring and diagnostics.
- Control execution, blocked-action decisions and output intent remain distinct from command transport and physical feedback.
- UI refresh, navigation and rendering must not throttle or alter Control execution.

**D5. Studies**
- Primary hierarchy: study type → study case → immutable/identified input snapshot → execution/run → result set → report/export.
- Distinguish configuration from run history and canonical numerical results.
- Show model revision, input snapshot, solver/options, standard basis, assumptions, convergence and limitations at the point of result interpretation.
- Tables/plots may use filtering or visual decimation, but canonical numerical datasets remain unchanged.
- A Study result is historical evidence against its identified input basis, not an implicit live view of the current model.

**D6. Diagnostics and Operational Trace**
- Diagnostics are grouped/filterable by typed category and lifecycle; each item retains source, timestamp, severity, object/evidence identity and authorized action.
- Operational Trace is a cross-domain evidence view, not a new execution authority or substitute for historian/domain records.
- Timeline and graph views distinguish input, evaluation, decision, interlock, output intent, command, acknowledgement, physical feedback and correlation-only relationships.
- Missing evidence, clock uncertainty, historian gaps and revision drift are visible as gaps/limitations rather than filled with inferred links.

### E. Project Explorer, Inspector and search contracts

**Project Explorer**
- Tree nodes have stable IDs, type, parent/relationship semantics and explicit lazy-loading/error states.
- Support text search, designation/ID search, type filters and domain-aware facets; results navigate to the canonical object/document.
- Avoid presenting duplicate copies of one object as independent entities when it appears in multiple views.
- Context menus are type- and permission-aware; disabled actions explain the missing precondition or unsupported capability.
- Large projects require incremental expansion/search and bounded rendering; the tree must not force full-project materialization on every navigation action.

**Inspector**
- Use task-oriented sections such as Identity, Electrical/Physical, Connections, Instrumentation, Protection, Control, Studies, Calculated/Observed values and Presentation.
- Only show sections supported by the selected object and available contracts; no speculative generic property bags.
- Distinguish authoritative configuration, derived/calculated values, live measurements, historical values and user presentation metadata.
- Each editable field exposes type, unit, range/constraint, validation state, source and commit behavior.
- Multi-selection shows common properties and explicitly reports mixed values; it must not silently overwrite heterogeneous values.
- Editing a draft/preview is visually distinct from accepted configuration; failed commits preserve the prior accepted revision and expose typed diagnostics.

**Search**
- Search scope is explicit (current document, project, supported connected evidence or catalogue).
- Results show type, designation, parent/context, status/revision and why the result matched.
- Search must respect applicable access controls and must not expose inaccessible project or operational information.
- Search result activation uses semantic identity and revision-aware navigation, not display-label matching.
- Search history and suggestions are presentation/session data subject to user settings and privacy policy.

### F. Navigation and interaction rules

1. Workspace switch changes the task context but does not silently change project, active document or engineering revision.
2. Opening a related object may reuse an existing document view or open a new one according to an explicit document policy; never create hidden duplicate editing sessions.
3. Back/forward navigation restores a safe view context (document, selection, relevant revision and time basis), but does not roll back engineering mutations.
4. Breadcrumbs describe actual semantic containment or navigation context; they must not invent ownership for cross-referenced objects.
5. Cross-domain navigation shows the relationship type and source; if only a weak correlation exists, label it as such.
6. Selection synchronization between Explorer, canvas, Inspector and diagnostics uses stable object identity and guards against stale projection revisions.
7. If an object is deleted, replaced or migrated, navigation reports the unresolved reference and offers safe alternatives; it must not silently select a similarly named object.
8. Tool availability and keyboard shortcuts are focus-aware. Text editing, canvas tools, panel commands and global commands have deterministic precedence and visible conflict handling.
9. Modal workflows are reserved for operations requiring an explicit blocking decision; routine inspection and non-destructive diagnostics should avoid unnecessary modal interruption.
10. All navigation actions have keyboard equivalents and preserve a visible focus location; focus is not lost when panels or documents change.

### G. Information architecture data and ownership boundaries

| Concern | Authoritative owner | UI responsibility |
|---|---|---|
| Project/package identity and canonical content | Project/Application services and Core-owned domain data | Present identity, integrity, revisions and lifecycle outcomes |
| Equipment, terminals, topology and connections | Core electrical/domain model | Navigate and project stable semantic identities |
| Measurement and channel lifecycle | Shared Signal/Measurement domain services | Present distinct lifecycle, quality, freshness and provenance |
| Protection settings/evaluation/decision | Protection domain | Present configuration and evidence; no UI decision authority |
| Control logic/configuration/execution | Control domain | Present logic and cycle evidence; no UI execution authority |
| Study inputs, solver execution and results | Study/Application and solver contracts | Present provenance, progress and canonical result data |
| Diagnostics/events and operational evidence | Owning domain/Application services and historian | Aggregate typed read models without changing source lifecycle |
| Workspace layout, panels, navigation history | UI/session layer | Persist only under approved session/preferences policy |
| Selection, hover, active tool and transient preview | UI interaction layer | Keep transient; never serialize as engineering truth |
| Search index/cache | Application/query service or bounded read-model infrastructure, to be decided | Treat as rebuildable derived data; preserve access and revision correctness |

No UI tree node, tab, breadcrumb, search result, canvas item or inspector widget becomes a new domain entity or mutation authority.

### H. Candidate information-architecture acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-IA-01 | Identify current project/workspace/document | User can distinguish project, canonical workspace, active document and revision without opening a dialog |
| UI-ACC-IA-02 | Navigate from Explorer to an SLD object | Stable semantic identity selects the correct projection and Inspector target |
| UI-ACC-IA-03 | Navigate from SLD equipment to Protection | Only a typed relationship is offered; destination shows its own configuration/revision |
| UI-ACC-IA-04 | Trace an instrument to a channel and consumer | Source, channel lifecycle and consumer binding remain separate and traceable |
| UI-ACC-IA-05 | Switch between Control and SLD | Each workspace retains its own interaction semantics, tool state and document context |
| UI-ACC-IA-06 | Inspect mixed multi-selection | Common values and heterogeneous values are explicit; no accidental bulk mutation |
| UI-ACC-IA-07 | Search by designation/type/property | Results show object type and context; activation resolves stable identity |
| UI-ACC-IA-08 | Navigate from diagnostic to source object | Diagnostic identity, lifecycle and evidence survive navigation |
| UI-ACC-IA-09 | Return using navigation history | Prior safe view context is restored without reverting engineering changes |
| UI-ACC-IA-10 | Collapse/reset workspace panels | Essential task access, keyboard navigation and critical state remain available |
| UI-ACC-IA-11 | Open historical Study result | Input snapshot/revision and historical basis remain explicit |
| UI-ACC-IA-12 | Navigate with stale/deleted target | UI explains the unresolved reference; it does not substitute a same-name object |
| UI-ACC-IA-13 | Complete workspace navigation by keyboard | Focus order, shortcut precedence and accessible names are predictable |
| UI-ACC-IA-14 | Open large project hierarchy | Expansion/search remains responsive and does not require eager rendering of all nodes |
| UI-ACC-IA-15 | Inspect operational trace | Typed relationships, evidence gaps, time basis and domain authority are visible |

These are candidate scenarios for later moderated usability and technical validation. They are not approved release criteria and do not assert current implementation conformance.

### I. Open decisions and evidence required

1. Validate the proposed top-level taxonomy with electrical, Protection, Control, instrumentation, Study and commissioning/operations engineers; determine whether Instrumentation & Signals is a primary workspace or a cross-domain service workspace with dedicated views.
2. Decide whether Equipment & Assets is a standalone workspace, a project-wide Explorer facet or a register view; avoid duplicating the equipment authority.
3. Define canonical document/tab behavior, multi-document policy, navigation history and safe restoration when revisions change.
4. Define search scopes, indexing ownership, update consistency, access-control integration and offline behavior.
5. Define workspace preset ownership and persistence across user, machine and project boundaries in alignment with 8I-13.
6. Reconcile Inspector sections with typed domain property contracts and command ownership; identify which values are editable, derived, live or historical.
7. Validate menu, toolbar, palette and shortcut organization against the role-based journeys in 8I-17.
8. Determine supported display density, multi-monitor, panel docking and accessibility requirements with the platform matrix.
9. Establish a named V3 source repository/branch/commit before claiming that any information-architecture contract is implemented.
10. Record explicit owner disposition for UI-GATE-01 through UI-GATE-07; this proposal does not close or approve any gate.

### J. Gate disposition and frozen invariants

**UI-GATE-01 and UI-GATE-07 remain Open.** Other UI gates retain their previously recorded status and evidence requirements. This section is a candidate information-architecture specification and must be reconciled with contextual research, role journeys, project/session lifecycle, diagnostics, accessibility, performance and operational traceability before implementation authorization.

Frozen invariants:
- Project remains the persistence root; workspace hierarchy does not create duplicate project or domain authorities.
- Core owns engineering truth; Application owns controlled mutation/orchestration; UI owns presentation and interaction.
- Core has no Qt, graphics, widget, canvas or UI-plugin dependency.
- SLD, Control and other discipline-specific workspaces retain distinct semantic interaction models.
- Protection and Control remain separate execution authorities.
- Shared Signal/Measurement infrastructure supplies typed data and provenance; it does not own Protection or Control decisions.
- Navigation and search resolve stable semantic identities and typed relationships; labels and visual proximity are not identity or causality.
- UI-derived status cannot invent validation, command acceptance, acknowledgement, alarm clearance or physical feedback.
- Workspace layout, selection, navigation history and transient tools remain outside canonical engineering truth unless a separately approved persistence contract states otherwise.
- All mutation follows UI → Controller → Command → Application → Core → Event → Projection → UI.

**Scope boundary:** research register only. No V2 or V3 source implementation, UI behavior, project schema, permissions, tests or CI were changed or run.


## 8I-19. Proposed V3 command, action and keyboard interaction architecture (2026-11-04)

**Purpose:** define one discoverable and predictable user-action model across GridForge workspaces while preserving domain-owned command semantics, focus-aware keyboard behavior, transaction boundaries and engineering safety.

**Status:** research proposal. This section does not approve a command API, keyboard map, undo model, permission system, confirmation policy or implementation.

### A. Architectural invariants

1. **One action identity, multiple presentation surfaces.** A user operation has one stable command/action identity and one authoritative execution path whether invoked from a menu, toolbar, palette, context menu, keyboard shortcut, Inspector or accessibility action.
2. **Presentation does not own mutation.** Widgets and canvas items express typed user intent; they do not directly mutate Core state, project persistence or domain runtime state.
3. **Application controls mutation.** Mutating actions route through the owning Controller/Command/Application service and then the appropriate Core/domain contract. UI-only presentation actions may remain within the UI layer.
4. **Domain ownership is explicit.** SLD, Instrumentation/Signals, Protection, Control and Study actions retain their owning domain and validation rules. A common command framework must not become a second domain service, event bus, scheduler, transaction manager or execution authority.
5. **Command identity is not a shortcut.** A shortcut is one possible binding to a command, not its identity or implementation.
6. **Availability is contextual and explainable.** Enabled, disabled, hidden, unavailable, unsupported and permission-denied states are distinct. Disabled actions expose a concise reason and, where safe, the missing precondition.
7. **No silent semantic substitution.** If an action cannot run in the current workspace, selection, revision or permission context, the system must not redirect it to a similarly named action or a different domain.
8. **Revision-aware execution.** Mutating commands identify the target document/object and expected revision or concurrency token where required. Stale intents are rejected or explicitly reconciled by the owning service.
9. **Asynchronous work is explicit.** Long-running commands report accepted/queued/running/completed/failed/cancelled only according to actual service/task state. UI timeout or dialog closure is not proof of cancellation.
10. **Undo is a domain capability, not a visual illusion.** Undo/redo reverses supported accepted operations through the owning transaction/history contract. It must not rewind physical reality, Protection/Control runtime execution, external commands or irreversible side effects.
11. **Safety and authority are not delegated to UI confirmation.** Confirmation can prevent accidental invocation but cannot replace domain validation, authorisation, interlocks, fail-closed behavior or device acknowledgement.
12. **Accessible invocation parity.** Every discoverable command has a keyboard and assistive-technology route where applicable, meaningful name/description, deterministic focus behavior and visible outcome feedback.

### B. Candidate command descriptor and lifecycle

A shared command catalogue may expose typed metadata without centralizing command implementation. Candidate descriptor fields:

| Field | Purpose |
|---|---|
| command_id | Stable namespaced identity, independent of display text or shortcut |
| display_name / description | Localizable user-facing label and concise purpose |
| owner_domain | Owning domain/Application capability |
| target_types | Supported semantic object/document types |
| invocation_contexts | Supported workspace, selection and focus contexts |
| parameter_schema | Typed inputs, units, constraints and required references |
| precondition_query | Read-only capability/availability evaluation |
| permission_requirement | Required capability/authorisation, resolved by security owner |
| execution_kind | UI-only, synchronous Application action or asynchronous task |
| revision_policy | Required target revision/concurrency behavior |
| undo_policy | Reversible, compensatable, non-reversible or unsupported |
| confirmation_policy | None, contextual warning, explicit confirmation or domain-controlled authorisation |
| result_contract | Typed outcome, diagnostics, affected identities and resulting revision/task reference |
| shortcut_bindings | Optional context-scoped key bindings |

This is metadata, not a proposed universal execute method. Domain commands may require richer typed request/result interfaces and retain those interfaces.

Candidate lifecycle:
1. Resolve invocation source and current focus/workspace/document/selection.
2. Resolve command identity and validate supported context.
3. Query availability and preconditions without mutating state.
4. Collect typed parameters and show units, defaults, assumptions and constraints.
5. Revalidate permission, target identity and revision at the execution boundary.
6. Request confirmation only when action risk/policy requires it; identify target and consequence.
7. Dispatch through the owning Controller and Application service.
8. Present typed success, partial outcome, rejection, diagnostics or task reference based on actual response.
9. Refresh affected projections using returned identities/revisions/events; do not fabricate a successful update.
10. Preserve an audit/evidence reference where the domain lifecycle requires one.

### C. Single command catalogue and invocation surfaces

Candidate platform capability: a command registry/catalogue that stores descriptors and resolves command identities. It is not a second command bus or service locator for domain mutation.

- Menus, toolbars, palette buttons, context menus, Inspector actions, command search and accessibility actions reference the same command identity.
- A command appears only where relevant; canonical metadata and owning handler remain singular.
- Searchable command access supports name, synonym, category and shortcut discovery; results show contextual availability and disabled reason.
- Tooltips explain purpose and important consequences, not merely repeat the label.
- Toolbars prioritize frequent context-relevant operations; menus retain complete discoverability; palettes expose domain-specific construction tools; context menus expose selection-specific actions.
- Context menus cannot bypass normal availability, permission or validation checks.
- Plugin-provided commands register through approved versioned plugin contracts and capability declarations. Core must not import plugin command implementations.
- Duplicate IDs, conflicting shortcut bindings and missing handlers are registration errors, not arbitrary last-registration-wins behavior.
- Compatibility aliases resolve explicitly to a canonical command and have a documented deprecation lifecycle.

### D. Focus-aware keyboard dispatch and shortcut policy

A single focus-aware dispatcher is a candidate service at the UI/application-shell boundary. It resolves bindings but does not execute domain logic.

Proposed precedence, subject to platform conventions and usability validation:
1. Active modal dialog/editor control consumes keys required for its own input operation.
2. Active specialized editor (SLD canvas, Control canvas, plot/table) receives keys explicitly reserved by that editor.
3. Focused panel or document-level commands resolve when no higher-priority control claims the key.
4. Active workspace bindings resolve next.
5. Application-global bindings resolve last.
6. Unhandled keys remain available to the platform/window manager.

Additional requirements:
- Every binding declares scope, priority, platform conflicts, repeat behavior and whether it is safe during text editing.
- Shortcut conflicts are detected at registration/configuration. Resolution is deterministic and discoverable; no silent shadowing.
- User remapping, if approved, preserves required safety/accessibility commands and offers reset-to-default.
- Menus and command search display the effective shortcut for the current context.
- Key-down/key-up handling avoids duplicate invocation when focus changes mid-sequence.
- Press-and-hold/repeat behavior is explicit; destructive or irreversible actions must not repeat unintentionally.
- Canvas navigation, tool activation, selection, text editing and panel focus have documented workspace-specific bindings.
- Platform-reserved shortcuts and international keyboard layouts are part of the supported platform matrix.
- A shortcut is never the only way to invoke a critical command; provide a visible and accessible route.
- Tool/workspace changes cannot leave stale shortcut ownership attached to the prior editor.

### E. Command availability, preconditions and feedback

Availability is typed, not a Boolean that loses its reason:

- **Available:** known contextual and permission preconditions currently pass.
- **Unavailable in context:** command does not apply to current workspace/target type.
- **Selection required:** a supported target is not selected.
- **Configuration required:** required data or setup is missing.
- **Validation blocked:** domain validation reports a blocking condition.
- **Permission denied:** security/authorisation layer denies the action.
- **Unsupported capability:** current model/plugin/domain capability does not implement it.
- **Stale target:** target identity/revision is no longer current.
- **Busy/locked:** owning service reports a conflict or operation in progress.
- **Unknown:** availability cannot be determined; fail closed for safety-relevant mutation.

Availability is advisory and can become stale. The owning Application/domain service revalidates at execution. The UI displays authoritative rejection details returned by the service.

Feedback requirements:
- Distinguish accepted request from completed operation and completed operation from physical/device outcome.
- Provide inline parameter errors, object-level engineering diagnostics and task-level progress for asynchronous operations.
- Preserve diagnostic identity/source when navigating from a failed command to its target.
- Do not show generic success for partial completion, warnings, queued work or later failure.
- Retry is offered only where the operation is idempotent or the owner defines safe retry semantics.
- Command feedback is not the only record of a safety-relevant or operational action.

### F. Undo, redo, transactions and irreversible actions

| Policy class | Meaning | Candidate UI behavior |
|---|---|---|
| Reversible edit | Accepted project/configuration change with a valid inverse | Undo/redo with affected objects and revision |
| Compensatable operation | Original action cannot be erased; owner provides a compensating action | Present as a new action; do not claim historical erasure |
| Non-reversible operation | External, physical, runtime or irreversible action | No ordinary undo; explain why and expose approved recovery path |
| Unsupported | No reliable inverse/compensation contract | Disable undo and identify the history boundary |

Requirements:
- History entries identify command, owner, actor/session where applicable, target identities, before/after revisions and meaningful summary.
- Transaction atomicity and rollback are defined by the owning Application/domain service, not by UI grouping.
- Multi-step workflows may use an explicit transaction/saga where supported; partial success and compensation outcomes remain visible.
- Failed transactions are not recorded as completed undo entries; partial external effects require explicit owner-reported status and recovery.
- Undo/redo revalidates current state, permissions and revisions; stale inverses are rejected or reconciled safely.
- Selection, zoom, pan, panel resizing, hover, tooltips and navigation are not engineering undo entries unless a separate presentation-history feature is approved.
- Draft edits and committed configuration changes have clear history boundaries. Draft-local undo may be distinct from project command history if documented.
- Save/open/close, import/migration and project replacement need explicit history-boundary behavior.
- Protection decisions, Control cycles, device commands, trip outputs, acknowledgements and physical feedback are records of events, not reversible edits. Reset/reclose/reissue is a new authorised domain action.
- Undo never fabricates reversal of a physical process or deletes audit/evidence records.

### G. Confirmation, destructive actions and engineering safety

- Low-risk, reversible presentation actions generally need no confirmation.
- Destructive project/object operations disclose target, scope, dependency impact and recovery/undo availability.
- Bulk operations disclose object count, eligible/ineligible items and partial-outcome behavior before commit.
- Irreversible/external actions require domain/security policy and explicit target/context; a generic dialog is insufficient.
- Protection and Control paths enforce domain interlocks, authorisation and fail-closed validation independently of UI confirmation.
- Disabled safety-relevant actions state the actual known blocker without exposing protected information.
- Confirmation identifies concrete target, consequence and expected transition; avoid vague prompts.
- Confirmation is invalidated if target identity, revision, selection scope or precondition changes before execution.
- Dangerous actions cannot depend on accidental key repeat, ambiguous shortcuts or context-menu position alone.
- Closing a confirmation is not evidence that an already-dispatched asynchronous/external operation was cancelled.

### H. Workspace-specific command semantics

**H1. SLD / Electrical**
- Place, configure, connect, move-layout, validate, commit, delete and edit-property operations have distinct identities and preconditions.
- Preview placement remains transient; commit creates/updates Core-owned equipment through Application and a separate SLD projection.
- Equipment mutation and symbol/layout manipulation must not share ambiguous labels or undo semantics.
- Wire/connect actions resolve stable terminal identities; snapping is an intent aid, not topology authority.
- Topology-changing commands revalidate terminal compatibility and target revisions in the owning domain.
- Selection and viewport commands do not enter electrical model history.

**H2. Instrumentation & Signals**
- Instrument configuration, channel allocation/binding, calibration, signal processing/routing and subscription are distinct actions.
- Channel binding must not silently alter physical topology or Protection/Control configuration without an explicit owner-approved workflow.
- Availability/quality/freshness inspection is read-only unless an authorised configuration command is invoked.
- Calibration/scaling changes retain source, revision and effective-time semantics.

**H3. Protection**
- Relay settings, function configuration, measurement binding, evaluation request, reset/enable/bypass and coordination analysis are distinct commands with owner-defined permissions/preconditions.
- UI availability is never the sole Protection interlock.
- ProtectionDecision, trip/output intent, command dispatch, acknowledgement and physical breaker feedback remain separate outcomes.
- Runtime decision history is not undoable; settings changes are separate configuration revisions and do not rewrite historical evaluations.
- Restricted or unsupported function coverage is explicit before an action is offered.

**H4. Control**
- Logic edit, connection, parameter configuration, channel mapping, validation, accepted configuration, evaluation/cycle request and equipment action are distinct.
- Control-specific graph semantics remain independent of SLD electrical connectivity.
- A blocked action is a domain result, not a failed UI command; evaluation may complete while action eligibility is blocked.
- Cycle completion does not imply every output command was dispatched, acknowledged or physically realised.
- Undo applies only to supported configuration edits, not executed cycles or physical actions.

**H5. Studies**
- Study configuration, input snapshot creation, run request, cancellation request, result inspection, comparison and export are separate commands.
- Study runs bind to identified input/configuration revisions; late results cannot attach to a different active document.
- Result visualization actions do not mutate canonical numerical datasets.
- Cancellation semantics/final state come from the solver/task owner, not from closing a progress view.

### I. Plugin and extension command contracts

- Plugins declare commands as capabilities with stable namespaced IDs, supported host/API versions, target types, invocation contexts, parameter/result schemas and permission requirements.
- Descriptors are validated before registration; incompatible or untrusted plugins cannot expose active commands.
- Registration is deterministic and scoped to plugin lifecycle; unload removes availability and prevents new invocation while in-flight work follows an explicit safe lifecycle.
- Plugin code invokes public Application/domain contracts; it cannot mutate Core directly or create a parallel event bus/command history.
- Host diagnostics report duplicate IDs, missing handlers, unsupported schemas, unavailable dependencies and failed registration.
- Plugin commands participate in undo only when their owner supplies a valid inverse/compensation contract accepted by the host.
- Plugin commands cannot override reserved safety or application-global command identities.

### J. Candidate command/action acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-CMD-01 | Invoke one action from menu, toolbar and shortcut | All surfaces resolve the same command identity and owner handler |
| UI-ACC-CMD-02 | Type in Inspector while shortcuts are active | Text editing receives keys; global/editor shortcuts do not steal input |
| UI-ACC-CMD-03 | Switch SLD to Control with a tool active | Prior workspace shortcut/tool ownership is cleared or safely restored |
| UI-ACC-CMD-04 | Resolve shortcut conflict | Conflict is detected and deterministic resolution is visible |
| UI-ACC-CMD-05 | Execute against stale selected object | Owner rejects/reconciles stale revision; no same-name substitute is mutated |
| UI-ACC-CMD-06 | Invoke command with missing precondition | Disabled reason is actionable; service revalidates at execution |
| UI-ACC-CMD-07 | Undo accepted configuration edit | Supported inverse restores prior accepted state and records new revision |
| UI-ACC-CMD-08 | Attempt undo after physical command | UI does not imply physical reversal; compensation is a separate action |
| UI-ACC-CMD-09 | Bulk delete mixed selection | Scope and eligible/ineligible objects are explicit before/after execution |
| UI-ACC-CMD-10 | Asynchronous study cancellation | UI distinguishes cancellation request from confirmed cancelled state |
| UI-ACC-CMD-11 | Protection trip path | Confirmation does not replace interlocks, authorisation or feedback evidence |
| UI-ACC-CMD-12 | Control evaluation with blocked output | Evaluation completion and blocked action are separate facts |
| UI-ACC-CMD-13 | Plugin registers duplicate command | Registration fails deterministically with actionable diagnostic |
| UI-ACC-CMD-14 | Invoke by keyboard/screen reader | Accessible name, focus, keyboard invocation and outcome are available |
| UI-ACC-CMD-15 | Retry after uncertain external outcome | UI prevents blind retry and exposes owner-defined reconciliation |

These scenarios are candidates for design review and validation. They are not approved release criteria and do not establish current implementation conformance.

### K. Open decisions and research evidence required

1. Establish the authoritative V3 Application command abstraction and compose it with existing Controller, Command, transaction and event contracts without duplicating managers or buses.
2. Inspect the actual V3 source repository/branch/commit before defining exact package placement or migration steps; V2 is not a V3 implementation source.
3. Build a complete command inventory from representative SLD, Instrumentation, Protection, Control and Study workflows; classify read-only, reversible, compensatable and non-reversible actions.
4. Review shortcut registrations, menu QAction metadata, ToolShortcutRegistry and focus handling in the selected baseline; validate collisions across supported keyboard layouts/platforms.
5. Decide command search/discovery behavior and whether user remapping is in initial scope.
6. Define permission/role ownership with security architecture; do not infer roles from workspace names.
7. Define project/draft/document undo boundaries, transaction atomicity, partial failure and history persistence.
8. Identify asynchronous task lifecycle/cancellation contracts for studies, imports, exports, plugin operations and supported external command paths.
9. Define audit/evidence requirements for safety-relevant configuration and operational actions, including retention and privacy.
10. Conduct moderated task validation with electrical, Protection, Control and Study engineers, including keyboard-only and screen-reader interaction.
11. Reconcile command descriptors and availability states with plugin platform research and versioned capability contracts.
12. Obtain explicit owner disposition for UI-GATE-01 through UI-GATE-07 before treating proposed behavior as approved.

### L. Gate disposition and frozen invariants

**UI-GATE-03, UI-GATE-04 and UI-GATE-07 remain Open** for diagnostic feedback, accessibility/keyboard and scope/priority decisions implicated here. Other gates retain their previously recorded status and evidence requirements. This section is not authorization to implement a new command framework or change existing command APIs.

Frozen invariants:
- UI emits typed intent; Application and the owning domain control mutation and validation.
- No duplicate command bus, event bus, transaction manager, scheduler, domain service or history authority is introduced.
- Core remains independent of Qt, widgets, graphics, UI plugins and command-presentation metadata.
- Stable command identity is independent of menu text, shortcut and widget instance.
- Focus-aware dispatch cannot steal normal text input or accessibility navigation.
- Availability display is advisory; the owning service revalidates preconditions, permission and revision at execution.
- Undo/redo applies only where the owner provides a valid inverse or explicit compensation contract.
- Physical operations, Protection decisions, Control execution, commands, acknowledgements and feedback are never erased or reversed by ordinary UI undo.
- Confirmation is an accidental-operation safeguard, not a substitute for engineering interlocks, authorisation or fail-closed domain validation.
- Plugin commands extend public contracts and cannot directly mutate Core or override reserved safety actions.
- Every mutating action follows UI → Controller → Command → Application → Core → Event → Projection → UI.

**Scope boundary:** research register only. No V2 or V3 source implementation, command API, shortcut map, permission policy, project schema, tests or CI were changed or run.


## 8I-20. Proposed V3 engineering Inspector and property-editing architecture (2026-11-04)

**Purpose:** establish a technically rigorous, consistent property-inspection and configuration workflow across GridForge domains while preserving typed domain ownership, engineering units, validation authority, revision semantics and the distinction between configured, calculated, live and historical values.

**Status:** research proposal. This section does not approve a universal property schema, editor implementation, configuration workflow, validation engine or V3 release requirement.

### A. Governing principles

1. Domain-owned property semantics: Core/domain contracts define engineering meaning, type, units, constraints and lifecycle. The Inspector renders typed read models and emits typed configuration intent; it does not define engineering truth.
2. No universal untyped property bag. Shared presentation may reuse editor primitives and metadata conventions, but domain schemas remain explicit and versioned.
3. Every value has state and provenance. Identify whether it is configured, defaulted, derived, calculated, measured, estimated, historical or presentation metadata.
4. Units are first-class. Store/exchange values in defined canonical units; display conversion must not change stored quantity or silently reinterpret input.
5. Validation has an owner. UI validation improves immediate feedback; Application/domain validation remains authoritative at commit/evaluation boundaries.
6. Draft is not accepted configuration. Draft edits, preview values, accepted configuration revisions and runtime-observed values are distinct.
7. Revision-aware editing. An edit is bound to target identity and expected configuration revision; concurrent or stale changes are explicitly reconciled.
8. Multi-selection is conservative. Common values may be inspected; bulk edits require explicit scope, compatibility and per-object outcome.
9. Calculated/live/historical values are not casually editable. Read-only values expose source, timestamp, quality, revision and calculation basis.
10. Cross-domain visibility is not cross-domain ownership. Inspector may display typed references to other domains but routes configuration to the owning domain.
11. Failure preserves accepted state. A rejected edit must not partially overwrite accepted configuration; supported partial operations are reported explicitly.
12. Accessibility and auditability are intrinsic. Editors expose labels, units, constraints, errors, focus order, accessible descriptions and change provenance.

### B. Candidate typed property read model

| Attribute | Purpose |
|---|---|
| property_id | Stable domain-owned property identity |
| owner_domain | Core/domain owner of meaning and mutation |
| target_id / target_type | Stable semantic object identity and type |
| value_type | Boolean, integer, decimal, enum, text, structured value, quantity, reference, curve/table or explicit type |
| value | Typed value or structured value reference |
| unit | Canonical engineering unit or explicit dimensionless marker |
| display_unit_options | Permitted presentation conversions, where supported |
| value_state | Configured, defaulted, derived, calculated, measured, estimated, historical or presentation-only |
| source | User/configuration, standard catalogue, calculation, instrument/channel, solver or typed provenance |
| quality | Applicable validity/quality state for observed values; not fabricated for static configuration |
| timestamp | Effective/sample/calculation time as appropriate |
| revision | Configuration, model, measurement sequence or result revision |
| constraints | Type, range, enum, dependency and cross-field constraints |
| edit_policy | Read-only, editable draft or owner-specific command workflow |
| visibility_policy | Context, role/permission and applicability rules |
| description | Engineering meaning, assumptions and standard/reference |

The model must not force every property to carry every field. A static nameplate rating does not need a measurement freshness timestamp; a live measurement does. Missing and not-applicable are distinct.

### C. Value-state and provenance presentation

Distinguish:
- **Configured:** accepted value belonging to a specific configuration revision.
- **Draft:** proposed, uncommitted edit; no implication of domain acceptance.
- **Defaulted:** supplied by a declared default/catalogue rule; show whether inherited or explicitly accepted.
- **Derived:** computed from other model data; identify dependencies where useful.
- **Calculated:** solver/analysis output with input snapshot, method/options, result identity and limitations.
- **Measured/live:** sample with source identity, unit, timestamp, quality and freshness.
- **Estimated/predicted:** model/inference output, explicitly not an authoritative measurement or Protection decision.
- **Historical:** value retained for a past revision/time basis; never present as current without evidence.
- **Presentation-only:** user display preference such as label position, formatting or local annotation; separate from engineering configuration.

State must be textual and accessible, not colour-only. Stale or bad-quality live values must not appear as normal current values.

### D. Engineering units, numeric input and precision

- Domain contracts define physical dimension, canonical storage unit, supported display units, precision and rounding rules.
- Unit conversion uses dimensionally valid conversions; incompatible dimensions are rejected, not guessed.
- Display unit changes presentation only. Changing physical quantity requires an explicit value edit.
- Parse decimal separators/localized number formats under explicit locale policy while preserving canonical numeric semantics.
- Distinguish significant digits, display precision, solver tolerance, instrument resolution and configured setting increments.
- Do not silently round an entered value to a different engineering value. If quantization is required, show accepted value and rule before commit.
- Preserve full canonical value for calculations and export even when engineering notation/scaling is used.
- Complex values, phasors, per-unit quantities, ranges, curves and matrices need domain-specific editors, not generic scalar controls.
- Validate finite values and explicit NaN/infinity/overflow policy; missing values are not zero.
- Show min/max/increment and constraint source when available. Conditional constraints are re-evaluated by the owner.
- Validate conversions/formatting around boundaries, negative values, very small/large magnitudes and locale changes before release criteria are approved.

### E. Inspector layout and progressive disclosure

Candidate layout:
1. Identity header: designation, object type, owner domain, document/context and configuration revision.
2. State/provenance strip: accepted/draft/default/calculated/live/historical state and relevant source/time/quality.
3. Task sections: Identity, Ratings/Nameplate, Electrical/Physical, Connections, Instrumentation, Protection, Control, Studies/Calculated, Diagnostics and Presentation, only when applicable.
4. Field editor: label, current value, unit, constraints, description, validation and edit affordance.
5. Change summary: pending edits, affected targets, dependency warnings and expected commit boundary.
6. Validation region: typed field/object/cross-object findings, severity, source and navigation.
7. Actions: Apply/Commit, Revert, Reset-to-default, Open owner workflow and inspect provenance, only where supported.

Frequent task-critical properties appear first; advanced fields are progressively disclosed without hiding safety-critical or required configuration state. Avoid unstructured forms and duplicate labels. Keep object and revision visible while scrolling. Search large property sets by stable property identity. Preserve focus/scroll context after validation or refresh where safe. Use explicit task workflows for complex configuration.

### F. Edit, validate, commit and revision lifecycle

1. Select a semantic object and obtain typed property read model at a known revision.
2. Open edit session bound to target ID, owner domain and expected configuration revision.
3. Validate syntax, type, dimensions and obvious bounds locally; label this preliminary feedback.
4. Collect related edits into typed change request; preserve entered value and unit context.
5. Run owner-provided preview/precondition checks where available; distinguish warnings, errors and unresolved checks.
6. Present affected fields/objects, dependencies and expected scope.
7. Submit through Controller → Application → owning domain service with expected revision/concurrency token.
8. Owner performs authoritative field, cross-field, cross-object, permission and domain validation.
9. On success, return accepted configuration revision, normalized values, affected identities and diagnostics; refresh projections from returned result/event.
10. On rejection/conflict, preserve prior accepted state and user's draft where safe; show typed diagnostics and offer refresh/rebase/review rather than silent overwrite.
11. Record change summary/audit reference according to domain lifecycle and retention policy.
12. Clear or retain draft state according to explicit Apply/Commit/Cancel and recovery semantics; never silently imply persistence.

No universal autosave or automatic commit is assumed. Apply versus Commit semantics must be defined per workflow and project/session policy.

### G. Multi-selection and bulk editing

- Identify selection count, object types and homogeneous/heterogeneous selection.
- Show common properties only when semantic property identity, type/dimension and edit policy are compatible.
- Display mixed values as mixed/indeterminate, not blank, zero or an arbitrary selected object's value.
- Offer bulk edit only when the owner exposes a safe batch command/transaction.
- Disclose target count, eligible/ineligible objects, constraints, dependency effects and atomicity/partial-success semantics.
- Atomic batch failure leaves accepted values unchanged. Supported partial success reports each target outcome and preserves evidence.
- Equal labels across equipment classes do not prove equal property semantics.
- Undo is available only through the owning reversible/compensatable contract in 8I-19.

### H. Domain-specific Inspector contracts

**H1. Electrical equipment and SLD**
- Separate Core-owned electrical properties (ratings, terminals, topology references, equipment type) from SLD presentation (symbol variant, label position, rotation, layer/annotation).
- Terminal/connectivity facts are read-only projections of Core topology except through explicit topology commands.
- Placement preview values remain draft; accepted equipment configuration is revisioned and distinct from symbol geometry.
- Bus, transformer, line/cable, breaker, CT/PT/CVT and load sections use type-specific schemas and applicable catalogue basis.
- The engineering property target is equipment identity, never a graphics item or symbol object.

**H2. Instrumentation & Signals**
- Separate instrument nameplate/calibration/configuration, acquisition channel settings, signal processing/routing and consumer bindings.
- Display engineering unit, range, scaling, calibration revision, source terminal/instrument identity, channel identity, sample timestamp, quality and freshness separately.
- Configured does not imply allocated, connected, active, healthy, fresh or valid.
- Calibration/channel reconfiguration retain effective-time/revision semantics; historical samples retain the calibration context used at acquisition.
- Distinguish raw, calibrated, filtered, derived and substituted values; never silently display inferred values as raw measurement.

**H3. Protection**
- Separate relay hardware identity, settings group, function elements, CT/PT/CVT input bindings, model coverage, evaluation status and historical ProtectionDecision evidence.
- ANSI/IEC settings show function identity, units, characteristic/curve, tolerances and standard/model basis.
- Measurement inputs expose source instrument/channel, phase/polarity/ratio/scaling, timestamp, quality and freshness.
- Show topology revision separately from instrumentation and Protection configuration revisions.
- Live evaluation/decision/operation records are read-only evidence; settings change through Protection-owned commands.
- Restricted/unsupported model coverage is explicit.

**H4. Control**
- Separate logic element parameters, typed I/O bindings, channel mappings, interlocks, action target configuration and execution-cycle evidence.
- Control graph connectivity remains Control-owned, not SLD electrical topology.
- Show signal source, data type, unit, quality/freshness, scaling and mapping direction where relevant.
- Execution decisions, blocked actions and cycle results are read-only runtime evidence; configuration edits follow Control-owned validation/commit.
- Do not edit live measurement or device feedback through a Control property field.

**H5. Studies**
- Separate study setup, input snapshot, solver/options, standard assumptions, run metadata, numerical results and report presentation.
- Results identify units, input revision/snapshot, solver version/options, convergence, assumptions and limitations.
- Result datasets are immutable/identified outputs; plot range, sorting, filtering and visual decimation are presentation operations.
- Re-running creates a new run/result identity; it does not silently replace historical evidence.

### I. Standards, catalogue and derived-property handling

- Catalogue values identify publisher/standard/catalogue edition, item identity, source date and jurisdiction where known.
- Distinguish normative requirement, manufacturer data, project specification, user-entered value, engineering assumption and default.
- Standard-derived constraints identify exact edition and clause/characteristic where licensed and available; never fabricate references.
- Derived properties expose dependency information and update when source revisions change.
- If a dependency changes, mark derived/calculated properties stale or pending recomputation.
- Manufacturer/catalogue values are not automatically valid for project duty; project-specific validation remains required.
- Property metadata schema evolution needs explicit migration and unknown-field behavior; unrecognized data must not be silently discarded.

### J. Candidate Inspector acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-INS-01 | Inspect accepted equipment rating | Type, unit, source and configuration revision visible |
| UI-ACC-INS-02 | Edit quantity in alternate display unit | Canonical quantity preserved; conversion dimensionally valid |
| UI-ACC-INS-03 | Enter out-of-range value | Preliminary error immediate; owner rejects at commit with typed diagnostic |
| UI-ACC-INS-04 | Concurrent configuration update | Stale edit rejected/reconciled; no silent overwrite |
| UI-ACC-INS-05 | Edit multiple compatible objects | Mixed values, target count, eligibility and outcome explicit |
| UI-ACC-INS-06 | Select heterogeneous equipment | Only semantically compatible common properties shown |
| UI-ACC-INS-07 | Inspect live measurement | Source, unit, timestamp, quality and freshness separate |
| UI-ACC-INS-08 | Inspect historical Study result | Input snapshot, solver basis and result identity visible |
| UI-ACC-INS-09 | Change CT ratio/calibration | Historical provenance retained; consumers see correct revision effects |
| UI-ACC-INS-10 | Edit Protection settings | Protection owner validates; historical decisions not rewritten |
| UI-ACC-INS-11 | Edit Control channel mapping | Control mapping revision changes through owner command; SLD topology unchanged |
| UI-ACC-INS-12 | Edit symbol position | Only SLD presentation changes; Core equipment/topology unchanged |
| UI-ACC-INS-13 | Commit partially eligible bulk change | Per-object result and partial/atomic semantics explicit |
| UI-ACC-INS-14 | Refresh Inspector during draft edit | User draft preserved or conflict explicitly presented |
| UI-ACC-INS-15 | Keyboard/screen-reader field navigation | Labels, units, constraints, errors and edit state announced predictably |

These scenarios are candidates for design review and validation. They are not approved release criteria and do not establish current implementation conformance.

### K. Open decisions and evidence required

1. Establish actual V3 repository/branch/commit before mapping this contract to source packages or APIs.
2. Inventory typed property contracts for representative electrical equipment, CT/PT/CVT, measurement channels, Protection functions, Control elements and Study settings/results.
3. Define canonical units and conversion/precision policy by quantity type and domain; avoid a UI-owned engineering units registry.
4. Determine how Application services expose draft/preview validation, commit, concurrency conflict and accepted revision.
5. Define which configuration classes support draft persistence, autosave, recovery, Apply, Commit and Cancel in alignment with project/session lifecycle research.
6. Define cross-field/cross-object validation response schemas and diagnostic navigation.
7. Define safe bulk-edit capabilities and atomicity/partial success for each owner.
8. Reconcile catalogue/standard provenance with licensing and exact-edition traceability.
9. Define role/permission visibility and authorization with security architecture; hiding a field is not access control.
10. Validate Inspector usability with domain engineers and assistive technology users.
11. Define migration and compatibility for property metadata and persisted configuration schemas.
12. Obtain explicit owner disposition for UI-GATE-01, UI-GATE-02, UI-GATE-03, UI-GATE-04 and UI-GATE-07 before implementation.

### L. Gate disposition and frozen invariants

**UI-GATE-02, UI-GATE-03, UI-GATE-04 and UI-GATE-07 remain Open** for project/session, diagnostic, accessibility and scope/priority decisions implicated here. Other gates retain previously recorded status and evidence requirements. This section does not authorize a universal property framework or changes to domain configuration APIs.

Frozen invariants:
- Core/domain contracts own property meaning, units, constraints and engineering truth.
- Application owns controlled mutation, validation orchestration, transactions and accepted revision publication.
- UI Inspector renders typed projections and emits typed intent; it is not a property database or alternate mutation authority.
- No untyped universal property bag replaces domain-specific schemas.
- Configured, draft, defaulted, derived, calculated, measured, estimated, historical and presentation-only values remain distinguishable.
- Display-unit conversion never changes canonical engineering quantity without explicit user edit.
- Live sample quality/freshness/provenance and historical calculation basis are never fabricated or hidden by generic formatting.
- Protection and Control configuration/runtime evidence remain owned by separate domains.
- SLD symbol/layout edits cannot mutate Core equipment or topology.
- Study visualization cannot modify canonical numerical results.
- Rejected edits preserve accepted state and report owner-provided diagnostics.
- All mutating property edits follow UI → Controller → Command → Application → Core → Event → Projection → UI.

**Scope boundary:** research register only. No V2 or V3 source implementation, property schema, unit registry, editor, project schema, tests or CI were changed or run.


## 8I-21. Proposed V3 diagnostics, alarms and event-management architecture (2026-11-04)

**Purpose:** define a coherent operator/engineer-facing diagnostics and event model without collapsing fundamentally different records—engineering validation, process alarms, Protection operations, Control execution, measurement quality, device commands/feedback, sequence-of-events (SOE), application faults and audit evidence—into one generic message list.

**Status:** research proposal. This section does not approve a universal alarm engine, event bus, historian implementation, alarm philosophy, priority matrix, retention schedule or operational workflow.

### A. Governing principles

1. **Typed records, shared presentation.** Common filtering, navigation, time display and accessibility may be reused; record semantics, lifecycle and authority remain with the originating domain.
2. **An event is not automatically an alarm.** An event records an occurrence or state transition. An alarm represents an abnormal condition requiring operator awareness/action under an approved alarm philosophy. A validation finding is not necessarily an operational alarm.
3. **Acknowledgement is not resolution.** Acknowledging an alarm records operator awareness; it does not clear the process condition, reset a relay, execute a command or repair a fault.
4. **Clearance is evidence-based.** An alarm returns to normal only when its source condition and configured return-to-normal criteria are satisfied. UI dismissal cannot clear the source condition.
5. **Shelving/suppression is controlled and visible.** It changes annunciation behavior under an authorized, time-bounded policy; it does not erase the source event or make the condition healthy.
6. **Preserve chronology and provenance.** Retain source identity, event time, receipt time, time quality, sequence/correlation identity, source revision and relevant domain context.
7. **Do not fabricate order or precision.** Distributed timestamps may be unsynchronized; preserve time quality and source sequence. Display uncertainty instead of claiming a total order unsupported by evidence.
8. **Separate detection from presentation.** Domain services determine conditions and typed records; UI projections aggregate and render them without becoming the alarm/Protection/Control authority.
9. **Fail visibly on data loss.** Missing, delayed, duplicated, out-of-order or invalid event streams are themselves observable diagnostics; absence of a displayed alarm is not proof of healthy operation.
10. **Safety actions remain domain-controlled.** Acknowledge, shelve, inhibit, reset, trip, close and operate are distinct actions with different permissions and safety implications.
11. **Historical evidence is immutable or append-corrected.** Corrections, annotations and operator notes add provenance; they do not rewrite the original record.
12. **Role and context determine presentation, not truth.** Role-specific views may filter or prioritize records but must not hide safety-relevant active conditions in a way that implies they do not exist.

### B. Typed record taxonomy

The following record families must remain distinct in storage/contracts even when displayed in a unified Diagnostics workspace:

| Record family | Meaning and owner | Lifecycle / acknowledgement semantics |
|---|---|---|
| Engineering validation finding | Model/configuration/topology violation owned by the validating domain/Application workflow | Open, resolved, superseded or waived under explicit engineering review; not operational alarm acknowledgement |
| Process alarm | Abnormal process condition defined by approved alarm philosophy and source owner | Active/return-to-normal; acknowledgement and shelving are separate states/actions |
| Event / state transition | Significant occurrence or state change from a domain/device | Append-only occurrence; may have no acknowledgement |
| SOE record | Time-ordered discrete state/event evidence, often requiring high-resolution source timestamps | Preserve source sequence and time quality; acknowledgement is not inherent |
| Protection diagnostic | Relay/input/model/evaluation/decision/operation evidence owned by Protection | Distinguish input invalidity, function blocked, decision, trip output and breaker feedback |
| Control execution diagnostic | Control cycle, logic evaluation, blocked action, interlock, dispatch and feedback evidence owned by Control | Cycle and action lifecycle; not generic alarm reset |
| Measurement quality notification | Invalid/stale/substituted/out-of-range/uncertain measurement or channel state owned by Signal/Measurement infrastructure | Quality state and freshness lifecycle; acknowledgement policy is separate if configured as an alarm |
| Command/actuation/feedback record | Intent, authorization, dispatch, acceptance, acknowledgement and physical feedback | Correlated but distinct typed stages; no stage implies the next |
| Application/platform diagnostic | UI, persistence, plugin, resource, communication or infrastructure fault | Operational support lifecycle; must not masquerade as process alarm |
| Audit/change record | User/system action, configuration revision, authorization and outcome | Append-only audit evidence; no alarm acknowledgement semantics |
| User annotation/operator note | Human-authored contextual information linked to records | Author/time/provenance; never silently changes source record |

One source condition may generate linked records in more than one family. Correlation links do not make those records identical.

### C. Canonical record envelope (candidate)

A typed envelope may provide shared navigation and query fields while preserving family-specific payload schemas:

- Stable record ID and schema/type discriminator.
- Originating domain, producer/service/device identity and source object identity.
- Event/occurrence time, source timestamp, receive/ingest time and explicit time-quality/synchronization status.
- Source-local sequence number where supplied; do not synthesize a source sequence.
- Severity/priority only where meaningful under the family contract; do not map every record to a universal severity.
- Typed condition/state, reason code, diagnostic code and structured payload.
- Configuration/model/topology/instrumentation/Protection/Control revision references as relevant.
- Correlation/causation references with relation type: caused-by, evaluated-from, command-for, feedback-for, same-operation, supersedes or contextual-only.
- Lifecycle state and lifecycle transition history where the record family defines one.
- Acknowledgement actor/time/reason and shelving/inhibition metadata only for applicable record types.
- Quality/completeness indicators for record delivery and source data.
- Retention/classification metadata and links to historian/source evidence.
- Localization key plus stable code/parameters; display text is not the machine identity.

Optional fields remain absent when not applicable. A process alarm must not inherit a meaningless solver revision; a solver warning must not receive a fabricated operator acknowledgement state.

### D. Alarm lifecycle and operator actions

Candidate process-alarm lifecycle:
1. **Normal:** source condition is below configured alarm activation criteria.
2. **Active/unacknowledged:** alarm condition is present and has not been acknowledged.
3. **Active/acknowledged:** operator awareness recorded while condition remains active.
4. **Return-to-normal/unacknowledged:** condition returned to normal but acknowledgement policy remains unsatisfied.
5. **Returned-to-normal/acknowledged:** condition has returned and acknowledgement requirement is complete.
6. **Shelved:** authorized temporary suppression of annunciation, with owner, reason, start and expiry; source condition continues to be evaluated and recorded.
7. **Out-of-service/inhibited:** explicitly engineered/authorized unavailable alarm state, with scope, reason, approval and restoration evidence.

Lifecycle details are alarm-philosophy-dependent; this is a candidate state model, not a claim that all standards mandate these exact state names.

Action semantics:
- **Acknowledge:** records awareness for a specific alarm instance/condition and operator identity; does not change the process variable or clear the alarm.
- **Shelve:** temporarily suppresses annunciation under limits and expiry; alarm remains visible in shelved view and history.
- **Unshelve/expire:** restores annunciation according to current condition; must not fabricate a new source transition.
- **Inhibit/out-of-service:** controlled engineering/operational action with explicit authorization, reason, duration/approval and audit; not a normal operator shortcut.
- **Reset:** only exists when the source device/domain defines a reset operation. It is not synonymous with acknowledge or clear.
- **Clear/return-to-normal:** determined by source condition and configured deadband/delay/latching semantics; never by dismissing a UI row.
- **Suppress/filter:** presentation query only unless it invokes an explicitly typed alarm-management action.

### E. Severity, priority and rationalization

- Keep event severity, alarm priority, diagnostic impact and software log level as distinct concepts.
- Alarm priority should reflect consequence and response urgency under an approved site/project alarm philosophy, not merely the apparent magnitude of a measurement or the source software's log level.
- Define alarm condition, cause, consequence, required operator response and allowable response time through a rationalization process owned by the project/operator.
- Avoid uncontrolled alarm floods: provide flood detection, rate/context summaries and filtering while retaining all source records and ensuring critical active alarms remain discoverable.
- Chattering/debouncing, deadband, on/off delays, latching and state-based suppression are source/configuration semantics; never implement them as ad hoc UI filtering.
- Acknowledgement state does not lower alarm priority.
- If priority/rationalization metadata is missing, show it as unconfigured/unknown rather than inventing a priority.
- Non-alarm events and engineering diagnostics should not inflate alarm counts or alarm-rate KPIs.

### F. Time, ordering and SOE integrity

- Preserve source occurrence time and ingestion/receipt time separately.
- Carry source clock quality/synchronization status and time-zone/UTC offset semantics; store an unambiguous instant plus the original source representation when required.
- Use source sequence numbers and device timestamp resolution where available. Do not reorder authoritative SOE evidence solely by UI arrival time.
- Where clocks differ, present time-quality warnings and avoid false precision in cross-device ordering.
- Duplicate delivery is handled through stable event identity/idempotency where the producer contract supports it; retain evidence of delivery anomalies.
- Late-arriving events remain late-arriving evidence; do not rewrite their occurrence time to receipt time.
- Time-window filters must state which time basis they use: source occurrence, receive time, acknowledgement time or historian ingestion time.
- Preserve sub-second/high-resolution timestamps supplied by source; do not claim a system-wide resolution without validating end-to-end acquisition and storage.
- Correlate events across domains using explicit causal/correlation links and bounded time windows, not timestamp proximity alone.

### G. Cross-domain diagnostic relationships

The Diagnostics workspace may provide linked views and a causal timeline, but each event remains owned by its source domain.

**G1. Signal/Measurement**
- Distinguish sensor fault, channel fault, communication loss, stale sample, bad quality, out-of-range and substituted/estimated value.
- Show raw/calibrated/processed stage, source channel, calibration/scaling revision, sample timestamp and quality reason.
- Measurement quality degradation can block Protection/Control inputs; display the actual consumer impact through typed dependency/evaluation evidence.
- A stale or invalid measurement must not be transformed into a healthy numeric value for display.

**G2. Protection**
- Distinguish relay self-diagnostic, invalid/missing input, stale measurement, unsupported function/model coverage, evaluation blocked, ProtectionDecision, trip signal/command, dispatch result and breaker/device feedback.
- Preserve function ID/code, relay identity, measurement provenance and relevant topology/instrumentation/Protection revisions.
- A Protection decision is not an alarm acknowledgement; a trip output is not proof that a breaker opened.
- Historical Protection evidence remains immutable and is not reset by changing current settings.

**G3. Control**
- Distinguish cycle started/completed, condition true/false/unknown, interlock block, action requested, command authorized/rejected, dispatch, acknowledgement and feedback.
- Show why an action was blocked and the exact inputs/quality/revisions used.
- Do not infer successful physical operation from a logic output or command dispatch.
- Control execution history is not a generic process alarm state machine.

**G4. Electrical/SLD and topology**
- Topology/connection validation findings are engineering diagnostics; they do not automatically become operational alarms.
- Show affected equipment/terminal/network identities and topology revision.
- A topology edit may invalidate dependent calculations or associations; surface typed stale/invalidation evidence without rewriting past results.

**G5. Studies**
- Distinguish solver warning, convergence failure, invalid input, assumption/limitation and result quality.
- Link diagnostics to run ID, input snapshot, solver version/options and result identity.
- Study warnings are not live process alarms; historical run diagnostics remain attached to the run.

**G6. Platform**
- Show persistence failures, event-stream gaps, plugin failures, resource exhaustion and projection errors as platform diagnostics with actionable support context.
- A platform outage must not be represented as process-normal simply because no new process alarms arrive.

### H. Diagnostics workspace and interaction model

Candidate workspace:
1. **Active alarms:** active/unacknowledged and active/acknowledged, with priority, source, age, state and response guidance where configured.
2. **Shelved/out-of-service:** separately visible with owner, reason, expiry and authorization context.
3. **Recent events/SOE:** chronological evidence with source time quality, sequence and filters.
4. **Engineering validation:** open/resolved findings grouped by project object/domain/revision.
5. **Protection and Control:** dedicated operational evidence views with domain-native state semantics.
6. **Measurement quality:** channel/instrument quality and affected consumers.
7. **Platform diagnostics:** application/infrastructure faults and stream health.
8. **Record details:** structured payload, provenance, related records, revisions, lifecycle history and permitted actions.

Interaction requirements:
- Filters support source/domain, object, record family, lifecycle, priority (where applicable), time basis/range, quality, project/workspace and correlation ID.
- Search uses stable IDs/codes as well as localized text.
- Saved views are query/presentation configuration, not changes to source records.
- Selecting a record navigates to the owning object/workspace while preserving the original diagnostic context.
- Related-record navigation explains relation type; correlation-only links are not labelled causal.
- Bulk acknowledgement/shelving, if supported, must display exact eligible record count, excluded types, target scope and outcome; never apply an alarm action to validation findings or events.
- Refresh/reconnect indicates stream freshness and gaps; no-data, disconnected and healthy-with-no-events are distinct states.
- Acknowledge/shelve controls are available only for typed alarm records and permitted actors.
- Detail panes show both concise human explanation and machine-stable code/structured evidence.

### I. Historian, retention and event-stream architecture

- Domain producers own creation of authoritative typed records; Application/platform infrastructure may route/persist them but does not reinterpret their semantics.
- Historian stores time-series samples and event/alarm/SOE/command/feedback evidence with source identity, time quality, sequence, schema version and provenance.
- Preserve the distinction between event store, time-series historian, audit log and current-state projections; storage technology may be shared only if contracts preserve semantics and retention requirements.
- UI reads projections/queries and must not subscribe directly to internal device transports or own durable event ingestion.
- Event delivery contracts define ordering guarantees, idempotency, retry, replay, gap detection, backpressure and schema evolution.
- A consumer outage/replay must not duplicate operator actions or mutate historical source records.
- Persist acknowledgement, shelving, inhibition and operator notes as separate actor-attributed records linked to the alarm/event identity.
- Retention, archival, export and deletion policies are configurable by record class and applicable regulation/site policy; do not impose one universal retention period.
- Event schema migration must preserve original source payload or a lossless/traceable representation where required.
- Provide integrity checks and exportable audit evidence for incident review; never claim cryptographic tamper evidence unless the storage design implements and verifies it.

### J. Candidate acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-DIAG-08 | Acknowledge an active alarm | Actor/time recorded; source condition remains active |
| UI-ACC-DIAG-09 | Alarm returns to normal while unacknowledged | Return-to-normal and acknowledgement states remain distinct |
| UI-ACC-DIAG-10 | Shelve an alarm | Reason, actor, scope and expiry visible; source event retained |
| UI-ACC-DIAG-11 | Shelving expires while condition remains active | Annunciation resumes without fabricating a new source transition |
| UI-ACC-DIAG-12 | Receive out-of-order SOE events | Source time/sequence and time-quality warning preserved |
| UI-ACC-DIAG-13 | Event stream disconnects | Gap/disconnected state is explicit; silence is not shown as healthy |
| UI-ACC-DIAG-14 | Measurement becomes stale | Quality/freshness and affected Protection/Control consumers are visible |
| UI-ACC-DIAG-15 | Protection issues trip decision | Decision, command/dispatch and breaker feedback remain separate |
| UI-ACC-DIAG-16 | Control action is blocked by interlock | Block reason and input evidence visible; no false command success |
| UI-ACC-DIAG-17 | Study solver fails convergence | Diagnostic links to immutable run/input snapshot; not an active alarm |
| UI-ACC-DIAG-18 | Topology edit invalidates a result | Current result is marked stale by dependency evidence; historical result preserved |
| UI-ACC-DIAG-19 | Bulk acknowledge selected records | Only eligible alarm records affected; excluded types and outcomes reported |
| UI-ACC-DIAG-20 | Search by stable diagnostic code | Correct source record found independent of localized display text |
| UI-ACC-DIAG-21 | Navigate from alarm to equipment | Owner workspace opens with diagnostic context and source revision preserved |
| UI-ACC-DIAG-22 | Historian replay after consumer restart | Idempotent replay; no duplicate source events or repeated operator actions |

These scenarios extend the earlier diagnostics scenarios in 8I-11. They are candidates, not approved release criteria or evidence of current conformance.

### K. Standards and governance references requiring project verification

- ISA-18.2 and IEC 62682 are relevant alarm-management lifecycle references for process-industry alarm systems. Exact applicable edition, jurisdiction, scope and licensed text must be verified before normative requirements are encoded.
- ISA-101 is relevant to human-machine interface design and operator display lifecycle; its applicability and exact edition must be confirmed for each deployment.
- IEC 61850 event/reporting and time-synchronization mechanisms may be relevant to substation automation integration; do not assume every GridForge event uses IEC 61850 semantics.
- IEC 60255 relay requirements and applicable device/protection standards inform Protection device/function diagnostics, but do not define the entire application diagnostics taxonomy.
- IEC 62443 security lifecycle principles are relevant to authorization, audit, role separation and secure operational actions; exact system security requirements require a threat/risk assessment.
- Standards catalogue verification, edition, clause mapping and licensing are explicit evidence tasks. This section does not claim clause-level compliance.

### L. Open decisions and evidence required

1. Establish V3 repository/branch/commit and inventory existing diagnostic, alarm, event, SOE, audit and historian contracts.
2. Identify domain producers and authoritative source for every record family; document current gaps and duplicate producers.
3. Approve project/site alarm philosophy, rationalization, priority, shelving, inhibition and response policy before defining operational alarm behavior.
4. Define timestamp/time-quality and sequence contracts across physical devices, simulated devices, acquisition, event transport and historian.
5. Define event delivery guarantees: identity, idempotency, ordering, replay, gap detection, retention and schema evolution.
6. Define separate lifecycle state machines and actor permissions for alarms, validation findings, Control actions, Protection evidence and platform diagnostics.
7. Determine whether event store, historian, audit and projections share infrastructure while preserving independent retention/integrity contracts.
8. Define correlation/causation relation types and rules for cross-domain trace; do not infer causality from time proximity.
9. Define alarm flood/chatter handling and KPI semantics with operator stakeholders.
10. Define bulk acknowledgement/shelving authorization and safety boundaries.
11. Verify applicable ISA/IEC editions, clauses, licences and deployment scope with the standards catalogue owner.
12. Obtain explicit disposition for UI-GATE-03, UI-GATE-04, UI-GATE-06 and UI-GATE-07 before implementation.

### M. Gate disposition and frozen invariants

**UI-GATE-03, UI-GATE-04, UI-GATE-06 and UI-GATE-07 remain Open** for diagnostics, accessibility, cross-domain traceability and scope/priority decisions implicated here. Other gates retain their previously recorded status.

Frozen invariants:
- Domain owners create and interpret typed diagnostics; shared UI presentation does not merge authority or lifecycle.
- Events, alarms, validation findings, SOE, Protection records, Control records, measurement quality, platform diagnostics and audit records remain distinct.
- Acknowledgement is not clearance, reset, command acceptance or physical feedback.
- Shelving/inhibition never erases source evidence or changes a condition to healthy.
- Alarm priority is governed by an approved alarm philosophy, not generic software log severity.
- Source occurrence time, receipt time, sequence and time quality remain distinguishable.
- No false total ordering or fabricated timestamp precision is introduced.
- ProtectionDecision, DeviceCommand/dispatch, acknowledgement and DeviceFeedback remain separate correlated records.
- Control cycle/interlock/blocked-action evidence remains Control-owned and cannot be reduced to generic alarm status.
- Measurement quality/freshness is explicit and its impact on consumers is traceable.
- Historical records and Study results are not rewritten by current configuration changes.
- UI queries/projections do not own durable ingestion or safety-critical state transitions.
- All mutating actions follow UI → Controller → Command → Application → owning domain → Event → Projection → UI, with typed authorization and audit.

**Scope boundary:** research register only. No V2 or V3 source implementation, alarm engine, event bus, historian, retention policy, alarm philosophy, tests or CI were changed or run.


## 8I-22. Proposed V3 engineering project collaboration, review and change-control architecture (2026-11-04)

**Purpose:** define controlled multi-engineer collaboration around the GridForge Project persistence root, with explicit ownership, revision-aware editing, review/approval, conflict resolution, auditability and safe project handover. Collaboration must not weaken domain validation, safety authority or the distinction between editing, engineering review and operational authorization.

**Status:** research proposal. This section does not approve a distributed collaboration service, locking mechanism, approval matrix, signature scheme, cloud synchronization design or project file format change.

### A. Governing principles

1. **Project remains the persistence root.** Collaboration operates on a project identity and its revisioned contents; it does not create competing persistence roots for SLD, Protection, Control, Studies or plugins.
2. **One authoritative accepted revision.** Every accepted project change has a stable identity, author/source, timestamp, parent revision and resulting revision. Local drafts and review proposals are not accepted project state.
3. **Concurrent editing is explicit.** Two engineers editing the same project or object must not silently overwrite each other's accepted work.
4. **Locking is a coordination aid, not correctness.** Domain validation and optimistic concurrency checks remain necessary even when a lease/lock is held.
5. **Review is not mutation authority.** Review comments and approval decisions do not directly mutate Core. Accepted changes still pass through Application commands and owning domain validation.
6. **Approval is scoped and revision-bound.** An approval applies to an identified change set and exact content revision, not an evolving project head.
7. **Engineering approval is not operational authorization.** A design review sign-off cannot authorize a Protection trip, Control dispatch, device operation or bypass.
8. **Immutable history with explicit supersession.** Accepted revisions and audit evidence are retained according to policy; corrections create new records rather than silently rewriting history.
9. **Conflict resolution is semantic.** Merge decisions account for domain meaning, dependencies, topology, configuration and provenance—not only text/file differences.
10. **Project handover is verifiable.** A receiving engineer can identify project revision, outstanding changes, unresolved findings, approval scope, external references and known limitations.
11. **Offline work is a first-class scenario.** Disconnected edits remain proposals until reconciled against the authoritative project revision.
12. **Least privilege and separation of duties.** Project access, editing, reviewing, approving, exporting and administrative actions are distinct permissions.
13. **Plugins participate through public contracts.** Extensions can contribute typed change metadata/review evidence but cannot bypass project transaction, audit or domain authority.
14. **No implied distributed transaction.** Cross-domain project changes need an explicit Application orchestration/transaction policy; collaboration transport does not make independent domain mutations atomic by itself.

### B. Project identity, revision and change-set model

Candidate concepts:

- **Project identity:** stable project ID independent of file path, display name, local checkout or storage location.
- **Project revision:** immutable accepted snapshot or revision identifier with parent relation and content digest/manifest as appropriate.
- **Working copy:** local editable view tied to a known base revision and user/session identity.
- **Draft change set:** typed collection of proposed changes with target IDs, expected object/configuration revisions, author, creation time and status.
- **Review request:** immutable reference to a draft change set and exact proposed revision, with review scope and requested reviewers.
- **Review decision:** reviewer identity, decision, timestamp, scope, comments and exact revision reviewed.
- **Approval record:** explicit authority, approval policy/version, approved scope and exact change-set/revision digest.
- **Accepted project revision:** project state resulting from validated and authorized change-set application.
- **Handover package:** project revision plus required manifest, provenance, review/approval state, unresolved findings and explicitly included evidence.
- **Local annotation/comment:** collaboration metadata linked to project/object/revision; not silently part of engineering model unless explicitly committed.

Do not assume a Git commit is the project revision identity. Source-control commits can be useful provenance for implementation artifacts, while the engineering Project has its own revision and transaction semantics.

### C. Ownership and permissions

Candidate permission dimensions:
- Project owner/administrator: membership, lifecycle, archive/restore and access policy.
- Engineer/editor: create and modify permitted project content through owning domain workflows.
- Reviewer: inspect a scoped revision, request changes and record review findings.
- Approver: approve a defined change scope under an approved authorization matrix.
- Read-only stakeholder: inspect authorized project state and review evidence.
- Export/handover operator: create a controlled delivery package without altering accepted engineering content.
- Platform administrator: manage infrastructure/security without inheriting engineering approval authority by default.

Permission evaluation must consider user, role, project, workspace/domain, object scope, action, revision state and contextual constraints. A hidden UI control is not access control; Application/domain services revalidate permission at execution.

Separation-of-duties controls may require:
- Author cannot approve their own change for designated high-risk scopes.
- Reviewer and approver may be distinct roles.
- Approval quorum or discipline-specific approvals for defined project classes.
- Emergency/expedited path is explicit, audited and retrospectively reviewed; never a silent bypass.
- Permission changes and membership changes are audited with actor, before/after state and effective time.

Exact roles, thresholds and mandatory dual control require project governance and risk classification; do not hard-code a universal matrix.

### D. Concurrent editing and coordination

Candidate strategy combines optimistic concurrency with optional scoped coordination:

1. Working copy records its base project revision and target object revisions.
2. On edit, the client may request a short-lived lease for high-conflict resources (e.g. project-wide settings, topology subgraph, Protection settings group), if the collaboration service supports it.
3. A lease identifies owner, scope, acquisition/expiry time, renewal policy and server authority; it is not a permanent lock.
4. Before commit, Application/domain service verifies expected revisions and validates the proposed change against current accepted state.
5. If revisions match and validation succeeds, accept the change set and publish the new revision.
6. If stale, return a typed conflict with base/current/proposed values and affected dependencies; do not silently last-write-wins.
7. Lease expiry, client crash or network partition releases/invalidates the lease under explicit policy; no client can claim exclusive ownership after expiry.
8. A user may continue offline in a local draft, but cannot represent it as accepted or approved project state.
9. Reconnection initiates reconciliation; it does not auto-commit or auto-approve queued changes.
10. High-risk changes may require explicit exclusive coordination, but safety-critical validation never relies solely on lock state.

Conflict classes:
- **Disjoint property edits:** may be auto-reconciled only when typed properties are independent and domain owner confirms no dependency conflict.
- **Same property edit:** explicit choose/rebase/resolve workflow; preserve both proposals.
- **Topology/connectivity edit:** semantic graph conflict; inspect affected terminals, edges, equipment and dependent studies/protection zones.
- **Instrumentation/measurement mapping:** compare source, channel, calibration and consumer bindings; stale dependent evidence is surfaced.
- **Protection settings/function edit:** conflict by relay/function/settings group and relevant input/configuration revision; no blind merge of protection curves or function parameters.
- **Control logic edit:** graph/element/binding conflict; require domain-aware review, not text merge alone.
- **Study setup/input edit:** separate immutable run inputs/results; re-run creates new result identity.
- **Presentation-only edit:** may be independently mergeable if it does not affect engineering model or shared layout ownership.
- **Project metadata/membership/policy edit:** governed by project administrator and explicit authorization.

### E. Semantic change sets and dependency impact

A change set should describe intent and impact, not merely serialize a file diff:

- Stable target identity and target type.
- Owning domain and typed operation.
- Base revision and expected target/object revisions.
- Before/after values or typed operation payload, with sensitive data redaction policy.
- Reason/engineering rationale and linked issue/requirement where applicable.
- Declared affected objects/domains and dependency references.
- Validation results, warnings, unresolved questions and validation revision.
- Author, creation time, tool/version and source workspace.
- Review scope, requested reviewers and required approvals.
- Commit/acceptance result and resulting project revision.

Impact analysis should identify:
- Electrical topology/connectivity and affected equipment/terminals.
- Instrumentation and measurement mappings/calibration revisions.
- Protection settings, input associations, coverage and affected zones.
- Control bindings, interlocks and action targets.
- Study input snapshots and results requiring recomputation.
- SLD/presentation-only changes versus engineering changes.
- Reports, exports and handover artifacts invalidated by the change.

Impact analysis is advisory until the owning domain validates it. Missing dependency knowledge must be marked incomplete/unknown rather than represented as “no impact”.

### F. Review and approval lifecycle

Candidate lifecycle:
1. **Draft:** author edits a working copy/change set; not accepted project state.
2. **Ready for validation:** author requests validation against a known base revision.
3. **Validation blocked / warnings:** typed findings are returned; author resolves or explicitly records allowed dispositions.
4. **Submitted for review:** immutable proposed revision/change set is frozen for review.
5. **In review:** assigned reviewers inspect scope, technical basis, impact and evidence.
6. **Changes requested:** review decision returns specific findings; author creates a new proposal revision or explicitly amends draft and resubmits.
7. **Approved:** authorized reviewers approve the exact change-set digest/revision and defined scope.
8. **Ready to accept:** all required approvals and preconditions remain valid; revalidate against current project head.
9. **Accepted:** Application commits through owning domain services and creates a new accepted project revision.
10. **Superseded/withdrawn/rejected:** proposal remains traceable and cannot be mistaken for accepted content.

Rules:
- Review comments refer to stable object/property/operation IDs and exact proposed revision.
- Approval expires or becomes invalid if the proposal content, relevant base revision, approval policy or required dependency revision changes.
- Any material edit after approval creates a new reviewable proposal; no silent mutation under an existing approval.
- Acceptance rechecks validation, permissions, expected revisions and approval validity.
- An approved proposal may still fail acceptance if the project head changed or a precondition is no longer true.
- Review completion does not guarantee that a physical device has been commissioned, tested or operated.
- Record reviewer rationale, findings and disposition; comments alone are not approval.
- Do not equate code review, engineering design review, project approval, safety authorization and commissioning acceptance.

### G. Domain-specific review controls

**G1. Electrical/SLD**
- Review topology, equipment identity/type, terminal compatibility, ratings, connection intent and layout/model distinction.
- Changes affecting topology require impact review of connected equipment, Protection zones, measurement associations and Study inputs.
- SLD presentation-only changes may use a lighter review path if project policy allows, but cannot alter engineering ownership.

**G2. Instrumentation & Signals**
- Review instrument type/ratio/range, calibration, channel mapping, signal units/quality, source provenance and consumer impact.
- Changes to CT/PT/CVT or measurement mapping must show affected Protection and Control consumers and revision effects.
- Historical measurements retain the calibration and mapping context effective at acquisition.

**G3. Protection**
- Review relay/function settings, characteristic/curve, CT/PT inputs, polarity/scaling, topology/zone impact, model coverage and validation evidence.
- Approval is tied to exact relay/function/settings revision and relevant topology/instrumentation revision.
- Protection setting approval does not authorize a trip, breaker operation, bypass or live setting change.

**G4. Control**
- Review logic graph, typed I/O, interlocks, action targets, execution semantics and failure behavior.
- Changes affecting device actions or permissives require explicit safety/operational review policy.
- Design approval does not itself authorize runtime dispatch or bypass.

**G5. Studies**
- Review input snapshot, assumptions, solver/options, convergence, result identity and report interpretation.
- A result cannot be approved independently of the exact inputs and solver context that generated it.
- Re-run creates a new result and, where required, a new review decision.

### H. Project revision, merge and conflict-resolution model

- Accepted revisions form an explicit parented history or equivalent immutable revision graph.
- Change application creates a new revision; accepted history is not rewritten by ordinary edit or conflict resolution.
- Semantic merge is delegated to owning domain services for topology, Protection, Control, measurement and Study content.
- Textual/structural three-way merge may be used for compatible metadata, notes or presentation data only where schema semantics permit.
- Merge UI presents base, current accepted, proposed change, owner validation and dependency impact.
- Unresolved conflict blocks acceptance for affected scope; unrelated independent changes may proceed only if the transaction contract supports scoped acceptance and makes partial outcome explicit.
- Rebase recalculates proposed change against a new base and reruns validation; it does not preserve old approval automatically.
- If a conflict cannot be resolved safely, preserve both proposals and require a human/domain owner decision.
- Project revision history supports compare, inspect, restore-as-new-revision and trace to prior approval/handover; “restore” must not delete intervening audit evidence.
- Content digest/integrity metadata may detect corruption or unauthorized change; cryptographic guarantees require a specified and verified design.

### I. Audit, evidence and signatures

Audit records should capture:
- Actor/service identity and effective role/authorization.
- Action, target, project ID, base and resulting revision.
- Before/after or typed operation reference under data minimization policy.
- Timestamp/time quality, client/tool version and source context.
- Validation results, warnings, approval references and conflict/rebase decisions.
- Review comments/dispositions and approval policy version.
- Export/handover creation, recipient, manifest/digest and delivery outcome.
- Administrative membership/permission changes and exceptional overrides.

Digital signatures or electronic approvals require explicit trust, identity, key custody, revocation, timestamping, canonicalization and legal/regulatory analysis. A username/password confirmation or UI badge must not be represented as a legally binding signature without the relevant controls.

Audit history is distinct from operational historian data and from source-control history. Retention and access controls are independently defined.

### J. Project handover and delivery

Candidate handover package contains:
1. Stable project identity, accepted revision and package/schema version.
2. Canonical project data and required internal dependencies according to the frozen Project persistence contract.
3. Change summary from the agreed baseline and relevant revision lineage.
4. Required discipline review/approval records bound to exact accepted revision.
5. Open validation findings, unresolved risks, deviations and explicit exclusions.
6. Study run identities, input snapshots and required reports.
7. Relevant alarm/event/Protection/Control evidence only where handover scope requires it; include time/provenance metadata.
8. Equipment/instrumentation/Protection/Control configuration revision summary.
9. External references, licences, catalogue editions and dependency availability; identify references not embedded.
10. Export manifest, content integrity information, creation actor/time and delivery/receipt evidence.

Handover workflow:
- Sender selects a specific accepted revision and delivery scope.
- System validates package completeness and flags unresolved/incompatible content.
- Required approvals are checked against exact revision.
- Package is generated as a reproducible artifact with manifest and integrity checks.
- Recipient verifies package integrity/schema, opens a separate working copy and records receipt/acceptance.
- Recipient acceptance does not retroactively modify sender's accepted project revision.
- Subsequent corrections are new revisions and, where required, new handover packages.

Do not silently include transient local drafts, private comments, credentials, tokens or unrelated user data in an engineering handover.

### K. Offline collaboration and recovery

- Offline work is a local working copy/change set tied to last known accepted revision and user identity.
- Clearly mark offline, stale, pending synchronization and unresolved conflict states.
- Local draft persistence and crash recovery must not imply server acceptance, approval or synchronization.
- On reconnect, fetch current revision and reconcile before any commit.
- Never replay queued physical operations, Protection commands, Control dispatches or device actions as part of project synchronization.
- Retry only idempotent collaboration operations with stable operation IDs; review/approval actions require fresh authorization and revision checks.
- Conflict recovery preserves original proposal and creates a new rebased proposal; it does not overwrite the prior record.
- Project backup/restore and collaboration synchronization are distinct workflows with distinct audit evidence.

### L. Candidate acceptance scenarios

| ID | Scenario | Candidate pass evidence |
|---|---|---|
| UI-ACC-COL-01 | Two engineers edit disjoint independent properties | Owner confirms independence; both changes accepted without lost update |
| UI-ACC-COL-02 | Two engineers edit the same property | Conflict surfaced with base/current/proposed values; no last-write-wins |
| UI-ACC-COL-03 | Concurrent topology edits | Semantic graph conflict and affected terminals/equipment/dependencies identified |
| UI-ACC-COL-04 | Edit Protection setting during review | Existing approval invalidated for changed proposal revision |
| UI-ACC-COL-05 | Reviewer approves a proposal | Approval bound to exact change-set digest/revision and scope |
| UI-ACC-COL-06 | Project head changes after approval | Acceptance revalidates and rejects/requires rebase where preconditions changed |
| UI-ACC-COL-07 | Author attempts self-approval | Policy enforced by Application authorization, not UI visibility |
| UI-ACC-COL-08 | Offline draft reconnects | Reconciliation occurs; no automatic acceptance or approval |
| UI-ACC-COL-09 | Rebase after conflict | New proposal revision and validation; original proposal retained |
| UI-ACC-COL-10 | Restore an earlier project state | Restore creates a new accepted revision; intervening audit history retained |
| UI-ACC-COL-11 | Handover to another engineer | Package identifies exact accepted revision, approvals, open findings and manifest |
| UI-ACC-COL-12 | Recipient verifies handover | Integrity/schema verification and receipt recorded independently |
| UI-ACC-COL-13 | Permission revoked during edit | Commit rechecks authorization and rejects stale permission |
| UI-ACC-COL-14 | Plugin contributes a project change | Change uses public contract and Application transaction/audit; no direct Core mutation |
| UI-ACC-COL-15 | Cross-domain change affects Study and Protection | Impact analysis identifies dependent revisions; each owner validates its scope |

These are candidate scenarios, not approved release criteria or evidence of current implementation conformance.

### M. Open decisions and evidence required

1. Establish V3 source repository/branch/commit and inspect existing project persistence, transaction, revision, audit and plugin contracts.
2. Decide whether collaboration is local-first, server-authoritative or hybrid; define supported deployment topologies and offline guarantees.
3. Define project identity, revision graph, digest, change-set schema and compatibility/migration policy.
4. Inventory domain semantic merge capabilities and identify which conflict classes must always require human review.
5. Define project roles, separation-of-duties, approval matrix, quorum, delegation and emergency override policy with engineering governance/security.
6. Determine whether leases/locks are needed for specific resource classes; define expiry, renewal, recovery and failure behavior.
7. Define transaction boundaries and acceptance policy for cross-domain change sets; no implied distributed atomicity.
8. Define approval invalidation rules for changed base revision, policy version, dependency revision or change-set digest.
9. Determine signature/electronic approval requirements, identity assurance, key management and legal applicability.
10. Define audit retention, privacy, export, archival and access policy.
11. Define handover manifest, package completeness checks, recipient verification and receipt semantics.
12. Validate usability and operational procedures with discipline engineers, reviewers, project owners and commissioning/handover stakeholders.

### N. Gate disposition and frozen invariants

**UI-GATE-02, UI-GATE-03, UI-GATE-06 and UI-GATE-07 remain Open** for project/session lifecycle, diagnostics, cross-domain traceability and scope/priority decisions implicated here. UI-GATE-04 remains Open from prior accessibility research. Other gates retain their previously recorded status.

Frozen invariants:
- Project remains the engineering persistence root; collaboration does not create domain-specific competing roots.
- Accepted project revisions are distinct from local drafts, review proposals and approvals.
- Approval is bound to an exact revision/change-set digest and scope; material change invalidates it.
- Review/approval does not directly mutate Core and does not authorize physical operation.
- Application and owning domain services revalidate authorization, expected revisions and domain constraints at acceptance.
- Locks/leases coordinate users but do not replace optimistic concurrency or domain validation.
- Semantic conflicts in topology, Protection, Control, instrumentation and Studies cannot be resolved by blind file overwrite.
- Disconnected drafts are not accepted project state; reconnect never auto-commits or auto-approves.
- Cross-domain impact is explicit; unknown dependency coverage is not reported as no impact.
- Audit, operational historian, project revision history and source-control history remain distinct evidence classes.
- Handover identifies exact accepted revision and does not leak local drafts or credentials.
- Plugins use public change contracts and Application services; no direct Core mutation.
- Physical commands, Protection dispatch and Control actions are never replayed as collaboration synchronization.
- All accepted engineering changes follow UI → Controller → Command → Application → owning domain → Event → Projection → UI.

**Scope boundary:** research register only. No V2 or V3 source implementation, collaboration server, locking service, approval engine, signature system, project schema, tests or CI were changed or run.
