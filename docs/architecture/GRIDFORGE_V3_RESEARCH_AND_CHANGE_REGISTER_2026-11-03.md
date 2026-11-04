

## 8I-41. Proposed V3 engineering assurance, configuration baselines, verification, validation and controlled release architecture (2026-11-04)

### 8I-41.1. Research scope and assurance objective

This section defines a traceable engineering assurance lifecycle from requirements and design through analysis, review, factory/site testing, commissioning, acceptance, operational release and as-operated configuration. It is a V3 research proposal, not an assertion of current implementation or standards conformity.

The architecture must distinguish:
- Verification: objective evidence that a work product satisfies specified requirements.
- Validation: evidence that the resulting system satisfies intended use and stakeholder needs in its operational context.
- Review: a defined examination by competent reviewers; review alone is not verification or acceptance.
- Acceptance: an authorized stakeholder's formal disposition of a defined deliverable/scope and its deviations.
- Operational release: authorization to use a particular approved configuration for a stated operational purpose and boundary.
- Commissioning: controlled activities demonstrating installation, integration and functional readiness against project-specific procedures.
- Handover: transfer of defined configuration, records, responsibilities and outstanding actions; not an implicit acceptance of unresolved safety-critical deviations.

No single status field may represent all of these concepts.

### 8I-41.2. Assurance object model

Propose distinct, revision-bound objects:
- Requirement, stakeholder need, design constraint, regulatory/contractual obligation and acceptance criterion.
- System breakdown structure, engineering scope, subsystem, equipment, functional location and interface.
- Configuration item and configuration baseline.
- Design artifact, model, calculation, study case, drawing, schedule, specification and report.
- Verification/validation plan, procedure, test case, test run, observation, measurement, evidence item and result.
- Review record, finding, nonconformance, deviation, concession, waiver, corrective action and closure evidence.
- FAT/FIT/SAT/SIT package, inspection/test certificate, loop-check record, commissioning package and performance-test record.
- Acceptance certificate, release authorization, handover package and as-operated baseline.

These are related by typed references and evidence links, not by copying mutable status text between records. A test run must identify the exact subject revision, procedure revision, test environment, equipment/instrument identity and calibration state, operator, witness where applicable, timestamps, raw observations, acceptance criteria and disposition.

### 8I-41.3. Requirements and traceability

Requirements need stable identity, source, authority, rationale, owner, applicability, priority, verification method, validation method, acceptance criteria, revision, status and approval provenance.

Support bidirectional traceability:
- stakeholder need → system requirement → subsystem/equipment requirement → design element;
- requirement → implementation/model/configuration item;
- requirement → verification method and test case;
- test case → execution, observations and evidence;
- finding/deviation → corrective action → retest or approved disposition;
- requirement → accepted baseline and release decision.

Traceability completeness must be measurable. A link is not proof of satisfaction. A requirement marked verified must point to valid evidence and an approved disposition. Unverified, not-applicable, deferred, waived and rejected states must remain distinct and carry rationale/authority.

### 8I-41.4. Verification and validation separation

Verification is work-product and requirement oriented. Validation is context-of-use and intended-outcome oriented. The system must support analytical verification, inspection, demonstration, simulation, test, independent calculation and review as distinct methods with defined applicability.

A successful power-flow convergence, relay logic simulation, Control sequence simulation, model check or report generation is not automatically proof that the complete plant is safe, correctly installed or fit for service.

Verification evidence must record:
- subject revision and dependency snapshot;
- requirement and acceptance criterion revisions;
- method, procedure, tool and tool version;
- input dataset, model fidelity, assumptions and operating conditions;
- expected and observed outcomes, tolerances and uncertainty;
- execution environment and relevant hardware/software configuration;
- reviewer/witness, approval and timestamp;
- anomalies, deviations, limitations and reproducibility status.

Validation records additionally describe the user/operational context, representative scenarios, boundaries, stakeholder participation, limitations and residual risks.

### 8I-41.5. Engineering configuration identification and baselines

Adopt configuration-management concepts consistent with ISO 10007 as a candidate reference:
- configuration management plan and authority;
- configuration item identification and unique identity;
- baseline definition and controlled change;
- configuration status accounting;
- configuration audit and evidence retention.

A baseline is an immutable, named, revisioned set of identified configuration items and their dependency relationships. It must include exact references to electrical topology, equipment data, SLD layout, instrument/measurement configuration, Protection settings, Control logic, study inputs, model/library versions, solver/tool versions and relevant external interface definitions.

Baseline types are distinct: requirements baseline, design baseline, approved-for-procurement baseline, approved-for-construction baseline, FAT baseline, installed/as-built baseline, commissioned baseline, accepted baseline and as-operated baseline. A project may use a subset or project-specific names, but transitions and scope must be explicit.

A baseline is not merely a Git branch, commit, file timestamp or latest saved project. Git provenance may support source change traceability but cannot replace engineering configuration identity and approval.

### 8I-41.6. Change control and impact assessment

Every proposed change creates a change record with origin, reason, initiator, affected scope, requested effective date, risk class and disposition. Change impact is computed across explicit dependency and relationship graphs: topology, equipment, instrument channels, Protection elements, Control logic, studies, reports, interfaces, commissioning evidence and released baselines.

Impact analysis must distinguish:
- technically affected artifacts;
- potentially affected artifacts requiring review;
- evidence invalidated by changed assumptions or dependencies;
- evidence that remains valid because its immutable inputs and scope are unchanged;
- external approvals and site procedures requiring reauthorization.

Never invalidate all evidence merely because a project revision number changed. Conversely, never retain a verified/accepted status when a relevant dependency changed. Selective invalidation must use dependency identity and revision, not tag/name similarity alone.

A change to a released baseline produces a new candidate baseline. It must not mutate the accepted historical baseline or rewrite prior test evidence. Emergency changes require a defined expedited path, compensating review, traceability and subsequent reconciliation; emergency does not mean undocumented.

### 8I-41.7. Independent review and separation of duties

Support configurable review policies based on risk and project governance:
- author, checker, approver, witness, acceptance authority and release authority are distinct roles;
- self-approval is prohibited where policy requires independent review;
- two-person control applies to selected high-consequence changes;
- review scope and competence requirements are explicit;
- comments, findings, responses, closure evidence and dissent are retained.

The system must not assume every project needs identical approval chains. Policy profiles are configurable, but authority and separation-of-duty constraints cannot be bypassed by UI, plugin or report template.

### 8I-41.8. Test architecture and test evidence

Model test definition separately from execution. A reusable test case contains preconditions, configuration, steps, stimulus, expected result, tolerance, safety constraints, required instruments, evidence capture and pass/fail/blocked/inconclusive rules.

A test run is immutable evidence. Re-running a test creates a new run; it does not overwrite a failed or superseded run. Support manual, instrument-assisted, automated, simulated and hybrid execution with explicit method and confidence boundaries.

Test results must include raw observations where practicable, normalized engineering quantities, unit/reference conditions, timestamps and time quality, instrument calibration, measurement uncertainty, environment, operator and witnesses. A pass result cannot be generated from missing mandatory evidence. Tolerance comparison must account for units, precision, rounding, uncertainty and acceptance-rule version.

Simulation evidence must identify simulator/model/solver versions, model fidelity, assumptions, initial conditions, input snapshots, time step or solver settings and hardware execution path where relevant. Simulation must not be represented as physical FAT/SAT evidence unless the approved procedure explicitly defines the simulated scope.

### 8I-41.9. FAT, FIT, SAT and SIT

Support project-configurable test stages:
- FAT: vendor/factory verification against agreed specification and factory configuration.
- FIT: integration of factory systems or packages before site deployment, where required.
- SAT: verification at the installation site against site conditions and agreed scope.
- SIT: end-to-end integration across systems and interfaces in the site context.

These stages are not universally interchangeable, nor does one passing stage imply all others passed. Each package records boundaries, exclusions, responsibility matrix, configuration under test, witness/hold points, punch items, deviations, retest requirements and signed disposition.

IEC 62381:2024 is the candidate reference for automation-system FAT/FIT/SAT/SIT planning. GridForge should provide configurable evidence structures, not hard-code one industry or contract's checklist as universal.

### 8I-41.10. Electrical, instrumentation, Protection and Control commissioning

Commissioning procedures must be domain-specific while sharing evidence infrastructure:
- Electrical: installation inspection, continuity, insulation, earthing, phasing, transformer and switchgear tests, CT/PT polarity/ratio and relevant functional tests.
- Instrumentation: instrument identity, range, calibration, loop checks, wiring, channel mapping, scaling, quality and end-to-end signal verification.
- Protection: CT/PT measurement path, relay settings revision, element enablement, injection test evidence, trip matrix, breaker interface, trip circuit supervision and approved functional test results.
- Control: I/O checks, interlock/permissive logic, sequence tests, fail-state behavior, communication loss response, alarm and operator-interface verification.
- Integrated systems: trip/interlock cause-and-effect, command/feedback reconciliation, time synchronization, event sequence and interface behavior.

Protection testing evidence must not be confused with authorization to operate or proof of actual fault-clearing performance in every possible network condition. Control simulation must not be represented as validation of physical actuator behavior unless the physical interface has been tested.

GridForge remains an engineering evidence and workflow platform; it does not replace site permit-to-work, isolation/LOTO, switching authorization, safety management or owner-approved commissioning authority.

### 8I-41.11. Nonconformance, punch lists and deviations

Findings need severity, safety/operational consequence, affected configuration, discovery stage, owner, due date, containment, root-cause status, corrective action and closure criteria.

Disposition options include correction, retest, accepted deviation/concession, deferred action with restrictions, rejection or no-fault-found. Waivers and concessions require named authority, rationale, scope, expiry/review condition and compensating controls. A waiver does not silently rewrite the original requirement or turn a failed test into a pass.

Punch-list items must carry stage, priority, responsibility, due date, blocking status and evidence of closure. Safety-critical and Protection/Control functional defects must be blocked from release according to project policy; a generic severity label must not override defined release constraints.

### 8I-41.12. Acceptance, handover and release gates

Acceptance is a decision over a named scope and baseline. The acceptance package identifies deliverables, evidence index, deviations, outstanding punch items, residual risks, exclusions, warranties/interfaces and authorized signatories.

Release states should be explicit and policy-configurable, for example:
- draft / under development;
- submitted for review;
- verified;
- validated for stated use;
- approved for procurement/construction;
- approved for factory/site testing;
- commissioned;
- accepted with stated conditions;
- released for defined operation;
- superseded / withdrawn / suspended.

These are not necessarily a single linear enum. A design can be verified while not validated; a system can be commissioned with open non-blocking punch items; an accepted baseline can later be superseded without losing historical acceptance. State transitions require guards, evidence, actor authority and audit events.

Operational release must be tied to the exact installed/commissioned baseline, approved operating boundary, restrictions, protection/control configuration and outstanding conditions. It must not automatically actuate equipment or issue commands to plant systems.

### 8I-41.13. As-built and as-operated reconciliation

Maintain distinct as-designed, as-procured, as-manufactured, as-installed, as-tested, as-commissioned, as-accepted and as-operated records. A difference is a typed deviation/change, not a silent overwrite.

Support redline capture, field markups, actual tag/serial/terminal mapping, equipment replacement, instrument calibration state, firmware/settings versions and field-measured parameters. Reconciliation must identify whether the change is documentation-only, engineering-affecting, safety-affecting, Protection/Control-affecting or requires new verification/commissioning.

The as-operated baseline is a controlled snapshot of known configuration and effective time, not a claim that every live device has been continuously observed. Device readback and communication evidence must carry source, timestamp, quality and completeness.

### 8I-41.14. Evidence integrity and reproducibility

Reuse 8I-36 event/audit/historian architecture and 8I-37 report provenance. Evidence objects are immutable after finalization; corrections are appended as amendments with actor, reason and links to the superseded item.

Integrity hashes establish content identity, not signer identity or engineering validity. Where signatures are used, record signer identity, certificate chain/trust policy, signing time, revocation/validation evidence and the exact signed payload. Preserve original raw data, derived values, calculation method and transformation lineage.

Long-term evidence packages must remain interpretable when plugins, tools, libraries or certificates become unavailable. Store schema and format identifiers, relevant metadata, versioned procedures and durable export options. Do not promise perpetual executable reproducibility when external runtimes or hardware are no longer available; distinguish reproducible inputs, reproducible method and reproducible execution.

### 8I-41.15. Cross-domain evidence integration

Assurance records must link to:
- Core domain objects and physical topology;
- Application commands, approvals and change transactions;
- Signal and Measurement Infrastructure samples, quality and calibration;
- Protection decisions, settings and test results;
- Control logic revisions, scan/task configuration and interlock evidence;
- study snapshots, solver versions, assumptions and results;
- asset lifecycle, maintenance and inspection records;
- operational command/feedback/SOE and historian evidence;
- report packages, external exchange and cybersecurity audit records.

A shared evidence graph provides navigation and traceability, but domain owners retain authority over technical meaning and acceptance rules. No generic assurance engine may reinterpret a Protection trip, Control interlock or electrical validation result.

### 8I-41.16. Data model and event contracts

Candidate canonical records include RequirementRevision, ConfigurationItemRevision, BaselineManifest, VerificationPlan, ValidationPlan, TestProcedureRevision, TestExecution, EvidenceRecord, Finding, Deviation, ReviewDecision, AcceptanceDecision, ReleaseAuthorization and HandoverPackage.

Every record needs stable identity, immutable revision, typed status, effective time, recorded time, provenance, actor/authority, scope and links to source revisions. Events include RequirementChanged, BaselineProposed, BaselineApproved, TestStarted, TestCompleted, EvidenceFinalized, FindingRaised, DeviationAuthorized, AcceptanceGranted, ReleaseAuthorized and BaselineSuperseded.

Events are evidence of recorded actions, not substitutes for authoritative current state or transactional command validation.

### 8I-41.17. UI/UX and role workflows

Provide an assurance workspace with:
- requirement-to-evidence trace matrix and gap indicators;
- baseline comparison and impact review;
- verification/validation plan and execution views;
- FAT/FIT/SAT/SIT and commissioning dashboards;
- findings, punch list and deviation disposition;
- review/approval queues with authority context;
- acceptance and release dossier builder;
- as-built/as-operated reconciliation.

Show why an item is blocked, what evidence is missing, which dependency invalidated it and who can authorize the next transition. Distinguish pass, fail, blocked, inconclusive, not applicable, waived and not yet executed with text and icon/shape cues, not colour alone. Never display a green compliance/acceptance indicator merely because all checklist boxes were clicked.

### 8I-41.18. Security, safety and authority constraints

Apply 8I-39 identity, authorization, signature and audit requirements to every approval and release. Approval must bind to exact payload hashes and revisions. A change after approval invalidates the approval for the changed scope.

Functional safety and electrical Protection requirements remain independently governed. GridForge assurance status cannot certify a safety instrumented function, relay, switchgear, installation or plant unless the applicable competent authority and certification process have done so. No plugin, report generator or administrator override may fabricate test evidence, bypass Core invariants or issue unauthorized operational commands.

### 8I-41.19. Candidate standards and applicability map

Candidate references for later clause-level verification:
- ISO/IEC/IEEE 15288:2023 — system lifecycle processes.
- ISO 10007:2017 — configuration management guidance; revision status requires monitoring.
- IEC 62381:2024 — automation FAT/FIT/SAT/SIT.
- IEC 62337:2012 — electrical, instrumentation and control commissioning phases/milestones.
- IEC 61508 and IEC 61511 — functional safety lifecycle where applicable; verify current editions, amendments and national adoption before use.
- ISO 9001 — quality management system context, where applicable.
- ISO/IEC/IEEE 15289 — lifecycle information item content, candidate for documentation governance.
- ISO/IEC/IEEE 29148 — requirements engineering, candidate for requirement quality and traceability.

This is a candidate map, not verified BIS adoption, clause-by-clause compliance, certification or a legal applicability determination. Project-specific contracts, owner specifications, statutory rules and jurisdictional requirements take precedence where applicable.

### 8I-41.20. Proposed acceptance scenarios

Candidate scenarios for later V3 acceptance planning:
- UI-ACC-ASSURE-01: Trace a stakeholder need through approved requirements, design, test and release evidence.
- UI-ACC-ASSURE-02: Prevent verification status without a valid requirement-linked evidence record.
- UI-ACC-ASSURE-03: Distinguish verification from validation in the user workflow.
- UI-ACC-ASSURE-04: Preserve immutable failed test execution when a retest passes.
- UI-ACC-ASSURE-05: Bind a test run to exact procedure, subject and dependency revisions.
- UI-ACC-ASSURE-06: Reject a test pass when mandatory observations or calibration evidence are missing.
- UI-ACC-ASSURE-07: Record measurement uncertainty and apply versioned acceptance tolerances.
- UI-ACC-ASSURE-08: Separate simulated evidence from physical FAT/SAT evidence.
- UI-ACC-ASSURE-09: Create and compare immutable design, construction and as-built baselines.
- UI-ACC-ASSURE-10: Invalidate only evidence affected by a relevant dependency change.
- UI-ACC-ASSURE-11: Preserve evidence whose immutable inputs and scope remain unchanged.
- UI-ACC-ASSURE-12: Require independent review for policy-designated high-consequence changes.
- UI-ACC-ASSURE-13: Prevent unauthorized self-approval or separation-of-duty bypass.
- UI-ACC-ASSURE-14: Manage FAT, FIT, SAT and SIT as distinct scoped stages.
- UI-ACC-ASSURE-15: Capture electrical, instrumentation, Protection and Control commissioning evidence independently.
- UI-ACC-ASSURE-16: Prevent a Protection settings test pass from implying plant operational authorization.
- UI-ACC-ASSURE-17: Record nonconformance, corrective action, retest and closure lineage.
- UI-ACC-ASSURE-18: Require authorized, scoped and expiring concession for accepted deviations.
- UI-ACC-ASSURE-19: Block release when mandatory safety-critical findings remain unresolved.
- UI-ACC-ASSURE-20: Grant acceptance only for a named baseline and defined scope.
- UI-ACC-ASSURE-21: Preserve historical acceptance after a newer baseline supersedes it.
- UI-ACC-ASSURE-22: Bind operational release to exact commissioned configuration and restrictions.
- UI-ACC-ASSURE-23: Reconcile field redlines and device readback without silently overwriting design intent.
- UI-ACC-ASSURE-24: Export a durable handover dossier with provenance, signatures and evidence index.

### 8I-41.21. Open architectural decisions

1. Define the minimum universal assurance object model versus project-configurable profiles.
2. Decide whether requirements authoring is native V3 capability or integrated through external requirements-management systems.
3. Define baseline granularity and the canonical manifest format across engineering domains.
4. Define approval/signature trust policy, certificate lifecycle and offline signing behavior.
5. Define policy profiles for FAT/FIT/SAT/SIT, commissioning, acceptance and release.
6. Define how field/device readback is reconciled with the as-operated baseline when connectivity is partial or data quality is poor.
7. Define long-term evidence retention, export formats and archival validation.
8. Define risk-class thresholds and non-waivable release constraints without hard-coding one owner's governance model.
9. Verify applicable BIS adoptions, editions, amendments and contract-specific requirements before any compliance claims.

### 8I-41.22. UI/UX gate impact

This section adds evidence and review needs to UI-GATE-02 (project/session lifecycle), UI-GATE-03 (diagnostics and evidence), UI-GATE-06 (cross-domain traceability) and UI-GATE-07 (scope and priority). UI-GATE-04 and UI-GATE-05 remain relevant to accessible assurance dashboards and large evidence sets. All gates remain open pending explicit decisions and acceptance evidence.

### 8I-41.23. Frozen V2 invariants and V3 migration boundary

Preserve the frozen V2 architecture as the baseline: Core owns domain truth; Application owns commands, services and controlled mutation; UI remains projection and interaction; plugins use public contracts and Application services; Protection and Control remain separate execution authorities; project persistence remains the canonical engineering project package.

V3 assurance capabilities must not introduce Qt/UI dependencies into Core, permit plugin bypass of Application, conflate project revisions with engineering baselines, or turn report/test evidence into mutable status flags. Migration is additive and requires explicit approval; this research does not authorize V2 source changes.

### 8I-41.24. Research disposition

Research-only proposal. No implementation, tests, CI, benchmarks, runtime validation, certification or compliance assessment was performed. No changes to V2 main. UI-GATE-02 through UI-GATE-07 remain open. BIS catalogue verification for Protection, Automation and Control remains a separate outstanding evidence task.
