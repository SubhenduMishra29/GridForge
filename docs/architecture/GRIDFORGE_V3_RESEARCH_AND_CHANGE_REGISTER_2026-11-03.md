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

## 9. Status and next sequence

**Completed:** V3 research register opened and initial research tracks captured.  
**In progress:** Complete source/dependency audit; standards applicability and clause research; capability/gap mapping.  
**Not started:** V3 architecture approval, implementation, package migration, plugin consolidation or schema changes.

Next: finish repository dependency audit → complete standards applicability matrix → map current capabilities/gaps → refine and prioritise V3 requirements → submit V3 architecture baseline for review.

No tests, CI, runtime checks or implementation changes were performed as part of opening this register.
