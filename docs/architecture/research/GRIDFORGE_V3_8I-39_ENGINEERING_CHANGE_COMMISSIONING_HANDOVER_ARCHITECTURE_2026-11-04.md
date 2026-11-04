# GridForge V3 Architecture Research — 8I-39
## Engineering change lifecycle, design review, commissioning and operational handover
**Research date:** 2026-11-04  
**Register lineage:** GridForge V3 Research and Change Register; 8I-22, 8I-25, 8I-35–8I-38  
**Status:** Proposed V3 architecture; research record only; approval required before implementation.

## 1. Objective and boundary

Define an auditable lifecycle connecting engineering intent, approved design, procurement, installed/as-built condition, test evidence, commissioning, operational acceptance and later modification. GridForge must preserve the exact configuration that was reviewed, built, tested and handed over. Deviations and changes must be recorded without silently rewriting the approved baseline.

The lifecycle distinguishes engineering change requests and authorizations; design revisions and AFC/IFC baselines; procurement and vendor submittals; installation and mechanical completion; FAT/FIT/SAT/SIT; loop checks and equipment-specific tests; precommissioning, cold/hot commissioning and performance testing; energization/return-to-service authorization; operational handover; defect-liability and post-handover modifications.

These are not one universal linear status field. Work packages, systems, subsystems, equipment and plant sections progress independently with explicit prerequisites and evidence. This is a lifecycle evidence/workflow model, not an operational control system, permit-to-work system, safety instrumented system, or replacement for the owner’s commissioning authority.

## 2. Principal architecture decisions

1. **Baseline continuity:** every approved design/configuration baseline is immutable and identified by exact revision/digest. Procurement, construction, test and handover records reference the baseline they realize.
2. **Change before deviation becomes truth:** field deviations are recorded as observed/as-built differences and are not silently accepted as design.
3. **Scoped state machines:** project, system, subsystem, equipment, work package, test campaign and handover package have distinct states and transition rules.
4. **Evidence before transition:** a milestone requires evidence, validation and authorized acceptance appropriate to its scope. A status label is not evidence.
5. **Requirements-to-test traceability:** each test case traces to a requirement, design object, configuration revision, method, acceptance criterion, result and evidence.
6. **Distinct test stages:** FAT/FIT/SAT/SIT, loop checks, commissioning and SIS validation are separate activities with separate scopes.
7. **Open items remain visible:** punch-list items, deviations, temporary measures and conditional acceptance retain owner, severity, due date, compensating measures, expiry and closure evidence.
8. **Impact-based retest:** changed dependencies invalidate affected evidence; unaffected evidence is not discarded indiscriminately, and old evidence is never assumed applicable when coverage is uncertain.
9. **Owner retains acceptance authority:** GridForge assembles readiness evidence and records authorization; it cannot infer permission to energize or declare a plant safe.
10. **Protection/Control retain domain authority:** commissioning checklists cannot override live fail-closed Protection guards or Control safety boundaries.
11. **As-built differs from design intent:** installed condition, approved design, vendor data, device readback and operational state are distinct records.
12. **One plugin host:** equipment-family test templates extend through the consolidated engineering plugin host; no duplicate workflow engine or lifecycle manager.

## 3. Lifecycle layers and state boundaries

Model lifecycle across linked aggregates:
- project/plant programme and plant sections;
- engineering system/subsystem and system boundaries;
- equipment and installed physical item;
- engineering baseline and change set;
- construction/installation/test/commissioning work package;
- test campaign and individual test case;
- handover package and operational asset context.

Each layer references stable identities from 8I-37 and immutable configuration/evidence revisions. A plant section may be mechanically complete while another remains under construction; a subsystem may pass SAT while overall SIT is pending.

Candidate baseline states: draft, submitted for review, under review, approved, released for procurement/construction, superseded, withdrawn.

Candidate physical execution states: not released, released, procurement, received/inspected, installed, mechanically complete, precommissioning, ready for commissioning, cold commissioned, hot commissioned, performance tested, accepted/handed over, in service, out of service, decommissioned.

These are examples, not a global enum. Equipment, drawings, test campaigns and plants require different state machines. Every milestone records type/scope, planned/actual time, responsible party, accountable authority, prerequisite evidence, accepted baseline, linked reports/open items, decision, conditions, signatures and provenance. Corrections append amendments or superseding records.

## 4. Engineering change management (MOC / ECR / ECN)

### 4.1 Change scope

Support changes to topology, equipment ratings/type, protection zones, replacement/relocation, CT/PT/CVT ratio/polarity/association, Protection settings and trip mapping, Control logic/interlocks/I/O, signal/calibration/communication/IED mapping, studies/assumptions, drawings/cable schedules, asset/maintenance data, firmware/software/plugins and schema/integration versions.

The request defines proposed scope; Application impact analysis resolves affected objects, revisions, studies, Protection elements, Control tasks, signals, drawings, documents, tests, installed assets and operational records.

### 4.2 Change lifecycle

Candidate states:
1. Proposed — originator, reason, affected plant/system and urgency.
2. Screening — technical scope, risk class, temporary/permanent status and reviewers.
3. Impact assessed — dependencies, safety-review references, standards, outage constraints and retest scope.
4. Designed — alternatives, calculations, drawings, settings and specifications.
5. Reviewed — discipline and interdisciplinary review.
6. Authorized — approvers accept exact change-set digest and conditions.
7. Released — controlled revision issued for procurement/construction/configuration.
8. Implemented — field execution and deviations recorded.
9. Verified/commissioned — affected tests and acceptance evidence complete.
10. Closed — as-built baseline, documents, training, asset records and handover updated.
11. Rejected/deferred/cancelled — disposition retained.

Emergency changes may use an expedited policy-defined route, but retain authorization, compensating controls, time limit and retrospective review. Emergency status does not bypass Protection/Control safeguards.

### 4.3 Impact and risk

Impact analysis includes topology/network model, equipment duty and study assumptions, Protection zones and measurement paths, Control I/O/interlocks/feedback, signals/calibration/historian mappings, IED/SCL datasets, SLD/schematics/cable schedules, installed assets/spares/maintenance, FAT/SAT/SIT/loop/commissioning records, training and operating procedures.

Record the source and accountable reviewer of risk assessment. A software impact graph is not a complete process hazard analysis, arc-flash study, functional-safety assessment or permit-to-work authorization.

### 4.4 Temporary changes and bypasses

Record exact scope, reason, risk assessment, approved operating envelope, compensating measures, authority, time bounds, monitoring, restoration plan, owner and expiry/escalation. Expiry creates a high-priority finding; it must not silently actuate or restore equipment. A bypass record cannot turn an inhibited protection/interlock into a valid dispatch path or weaken runtime fail-closed controls.

## 5. Design review and baseline release

### 5.1 Review gates

Configurable gates may include concept/design-basis review, architecture/interface review, project-defined 30/60/90 percent reviews, interdisciplinary coordination, detailed design verification, Protection/Control settings review, constructability/maintainability review, design freeze, approved-for-procurement, approved-for-construction and as-built review. Percentages are project conventions, not universal normative milestones.

Each gate defines deliverables, reviewers, checklist, open-item thresholds and acceptance criteria. Comments link to exact object/property/document/revision and have dispositions: accepted, corrected, rejected with rationale, deferred with due date, or not applicable with evidence.

### 5.2 Baseline manifest

An approved baseline is a manifest of immutable revision references, not an unstructured copy of current files. Bind project/system scope, Core equipment/topology revisions, Protection/Control configurations, Signal/Measurement mappings and calibration assumptions, SLD/schematic/document revisions, study assumptions/results, vendor documents, IED/SCL mappings, rule-pack/standards profile, approvals, timestamp, digest and supersession lineage.

Keep the canonical project package self-contained under the frozen V2 .gridforge contract. This proposed V3 baseline concept must not change V2 package semantics or require external services to reopen a project.

### 5.3 Approval integrity

Approval binds to exact content digest, scope, reviewer capability, timestamp and validation reports. If content or a required dependency changes, approval becomes stale. Authorship/review/approval separation is policy-configurable and enforced for high-consequence changes.

## 6. Procurement, vendor data and receipt

Track technical requisition, vendor bid evaluation, approved vendor document register, purchase order/line items, vendor submittals/revisions, inspection/test certificates, shipping/receipt, material identification, storage/preservation and release to installation.

A purchased product model is not the installed asset. Receipt associates actual manufacturer/model/serial/nameplate evidence and inspection records with the installed-item identity. A discrepancy from approved specification creates a finding/change request; delivered nameplate data does not silently overwrite design ratings.

Vendor document statuses (submitted, reviewed, approved with comments, approved for manufacture, final/as-built) are configurable and revision-controlled. Vendor data approval does not itself establish installation or commissioning acceptance.

## 7. Construction, installation and mechanical completion

A work package binds released baseline, scope/system boundary, equipment/cable/instrument IDs, drawings/procedures, contractor/inspector, inspection/quality records, non-conformances, redlines, field change proposals and completion checklist.

Evidence may include torque/termination records, earthing/bonding, cable tests, alignment, nameplate/serial capture, CT/PT polarity/ratio, panel inspection and wiring verification as applicable. Exact checks are equipment- and project-specific.

Mechanical completion is a scoped milestone indicating that erection/installation checks meet the defined prerequisite for precommissioning/cold commissioning. Record scope, accepted drawings/specifications/redlines, installation checks, punch list and dispositions, owner/contractor sign-off, date and limitations. Partial completion is valid only for an explicit boundary; one completed package does not make the whole plant mechanically complete.

## 8. Test and acceptance architecture

### 8.1 Test campaign and test case

A campaign defines scope, stage, requirements, equipment, configuration, participants, procedure, acceptance criteria, schedule and evidence. Each test case records stable ID/revision, requirement/design reference, objective/preconditions, equipment/system, exact hardware/firmware/software/configuration, method/tools/calibration, stimulus/expected response, acceptance criterion/source, actual result/units/time, pass/fail/inconclusive/not-run, performer/witness/reviewer, attachments, deviations and retest lineage.

Separate plan approval, execution, result review and formal acceptance. A signed PDF alone is not sufficient structured evidence when step-level data is available.

### 8.2 FAT and optional FIT

FAT verifies specified automation/equipment scope at the vendor/factory before shipment. It may cover hardware/software configuration, simulated I/O, HMI/alarm behavior, logic sequences, communications, failure modes and interfaces per project specification. FIT is optional factory integration testing of combined subsystems.

FAT identifies tested build/configuration and simulated interfaces. It does not prove field wiring, site installation, final process interface or live Protection trip path.

### 8.3 SAT and SIT

SAT verifies each installed subsystem against applicable specification, codes, instructions and installation conditions. SIT verifies integrated operation across subsystems against the approved integration test plan. Preserve separate reports and scope. A post-test change triggers dependency-based retest analysis; shared interface, firmware, IED mapping or logic changes may require integration regression.

### 8.4 Loop checks

Loop checks validate field device through wiring, termination, I/O/channel and control-system indication/action according to scope. Record point-to-point and functional evidence, signal range, polarity, scaling, thresholds, fail state, feedback and channel mapping. Loop-check completion is not full functional or safety validation.

### 8.5 Electrical equipment and Protection tests

Equipment-specific templates may cover insulation/resistance, winding/transformer tests, breaker timing/contact resistance, CT/PT ratio/polarity, earthing, cable tests, motor rotation/protection, relay secondary/primary injection where specified, trip-circuit continuity, breaker operation and end-to-end schemes.

Protection evidence binds relay/IED identity and firmware/configuration, Protection function and approved setting revision, CT/PT/CVT identity/ratio/polarity/association, test set calibration/method, injected quantities/phase/sequence, measured response and timing, approved tolerance source, binary I/O/trip mapping, breaker identity and trip-circuit evidence, result, witness and limitations.

A relay injection pass alone does not prove CT primary wiring, complete trip circuit, breaker mechanical operation, end-to-end scheme behavior or correct live zone association. Each covered and uncovered test scope must be explicit.

### 8.6 Control and interlock tests

Trace requirements to I/O, logic revision, operating modes, permissives, interlocks, sequence, alarms, communication loss, feedback, fail-state and recovery. Distinguish simulated FAT I/O from field loop checks and live functional tests. Where SIS/SIF scope exists, apply the functional-safety lifecycle and validation; generic Control acceptance is not SIS validation.

### 8.7 Deviations, retest and regression

A failed/inconclusive test creates a finding with severity, scope, cause, owner, corrective action and retest plan. Retest references original test and changed inputs. Partial retest is allowed only when dependency/independence boundaries are established. Uncertain identity, coverage or dependencies make prior evidence applicability-unknown and require review/retest.

## 9. Commissioning phases and readiness

### 9.1 Precommissioning

After accepted mechanical completion, precommissioning may include non-operating checks, cold alignment, cleaning, calibration/adjustment, continuity/insulation and project-defined preparation. GridForge records evidence but does not replace field procedures or responsible supervision.

### 9.2 Cold commissioning

Cold commissioning uses test media or non-production conditions where applicable to verify operability before actual process material/energy conditions are introduced. Readiness requires approved scope, test evidence, required loops, protections/interlocks and safe operating conditions.

### 9.3 Hot commissioning and start-up

Hot commissioning introduces actual process/operating conditions under an approved startup plan. Record sequence, operating envelope, authorization references, process conditions, alarms/events, permitted trip tests, exceptions and acceptance. GridForge does not issue or automate energization/start-up authorization merely because evidence is complete.

### 9.4 Performance testing

Compare measured operation against contractual/design guarantees under agreed conditions, duration, instrumentation, correction factors and acceptance criteria. Preserve raw measurements, calibration/quality, operating conditions, calculation method and signed report. Performance acceptance is distinct from electrical/Protection commissioning and plant handover.

### 9.5 Readiness gates

A configurable readiness gate evaluates approved baseline/current field configuration, mechanical completion/punch list, test coverage, Protection/Control verification, instrument calibration/signal quality, IED integration, procedures/operating limits/emergency response, training/spares/maintenance, open deviations/temporary measures, and authorization references/sign-offs.

Readiness is an evidence summary and recommendation. The owner's designated authority retains energization, startup, acceptance and return-to-service decisions.

## 10. As-built reconciliation and configuration activation

Preserve separate approved design, released construction baseline, vendor-approved data, installed/as-built condition, tested configuration, commissioned/accepted configuration, active operational configuration and observed device readback/live state.

For each discrepancy: capture observed value/source/time and equipment ID; compare with approved/released baseline; classify documentation error, tolerance, installation deviation, vendor substitution, approved field change or unauthorized change; assess impact; route to domain owner/change authority; correct installation or approve controlled revision; update as-built documents and affected tests; close with evidence.

A device readback does not become approved setting automatically. An as-built drawing update does not prove physical change was tested.

Activation records exact revision IDs/digest, scope/effective time, change approval, validation/commissioning evidence, authorizer, rollback reference, dependent consumers/endpoints and audit event. Activation is an Application/domain workflow; switching and device commands retain separate authorization/runtime safeguards.

## 11. Handover and acceptance

### 11.1 Handover manifest

A versioned handover package for a defined system/plant scope may include:
- approved design/as-built drawings, final SLD, schematics, cable schedules and I/O lists;
- equipment register, nameplate/asset/serial mapping;
- Protection settings/coordination documents and Control logic/cause-and-effect/interlock documentation;
- IED/SCL, network and communication configuration;
- FAT/FIT/SAT/SIT, loop-check and equipment test reports;
- calibration certificates and test-equipment records;
- commissioning logs, startup and performance reports;
- operating, maintenance and emergency procedures;
- vendor manuals, datasheets, certificates and warranties;
- training/competency records, spares and special tools;
- punch list, deviations, concessions and temporary measures;
- warranty/defect-liability dates and obligations;
- asset/maintenance-system mappings;
- final configuration manifest, provenance and approvals.

Each artifact has revision, digest, source, status, scope, owner and retention class. External documents may be linked, but canonical project reopening must not depend on external services.

### 11.2 Conditional acceptance

Open items are classified by consequence and policy. Conditional acceptance requires named authority, exact scope/equipment, risk assessment, compensating controls, owner/due date, expiry/review, operating restrictions and closure evidence.

No safety-critical defect, unverified Protection trip path or unresolved mandatory interlock can be hidden by a generic accepted-with-punch-list state. Non-waivable gates remain blocking.

### 11.3 Formal handover and post-handover baseline

Record transferring parties, authority, date/time, system boundary, accepted baseline, evidence-manifest digest, open obligations, training and limitations. Handover does not erase contractor defect-liability obligations or historical work ownership.

After acceptance, the operationally accepted configuration becomes the reference baseline for maintenance and future MOC. Maintenance, replacement, firmware, setting or logic changes create controlled records and update as-maintained/as-left evidence.

## 12. Roles, evidence integrity and audit

Scoped roles include originator, discipline owner, electrical design authority, Protection authority, Control/automation authority, instrumentation authority, asset/maintenance owner, procurement/vendor quality, construction contractor, test performer/witness, commissioning manager, operations/plant owner, functional-safety authority where applicable, document/configuration controller, reviewer/approver and auditor.

A person may hold multiple roles, but policy should prevent prohibited self-approval for high-risk change/test classes. Vendor evidence and owner acceptance are distinct. Test tools/integrations are service principals with version and calibration metadata, not human witnesses.

Lifecycle records include change requests/decisions, review comments, baseline releases, vendor submittals, installation/inspection, test plans/execution/results, calibration, punch items/deviations, commissioning logs, readiness reports, handover and activation. Records are immutable or append-only with amendment/supersession. Evidence metadata includes issuer, actor, source, time/clock quality, revision, digest, equipment/configuration identity, witness, approval and retention. A file hash alone does not prove authenticity; signatures, trust chain, timestamping and custody are separate controls.

## 13. UI/UX workflows

### 13.1 Engineering Change workspace

Show request/state, affected system/equipment graph, before/after revisions, risk/impact findings, review route, implementation work packages, required test/commissioning regression, field deviations and as-built/handover completion. Navigation from a changed CT ratio should reach affected channels, Protection elements, tests and operational baseline.

### 13.2 Commissioning dashboard

Use system/subsystem hierarchy with evidence-backed indicators for mechanical completion, precommissioning, FAT/FIT/SAT/SIT, loop checks, equipment tests, Protection/Control verification, cold/hot commissioning, performance and handover. Distinguish complete, blocked, overdue, not applicable and not evaluated. A green plant-wide indicator must not hide a blocked subsystem or incomplete coverage.

### 13.3 Test execution and field UI

Provide procedure runner with test step/expected result, equipment/configuration, measured result/units, attachments/waveforms/logs, pass/fail/inconclusive/not-run, witness/time, deviation and retest. Offline field capture preserves device/user identity, local clock quality and synchronization/conflict status; later sync must not invent authoritative ordering.

Support touch-friendly controls, barcode/QR lookup, photos, offline work and low bandwidth. A scan resolves a scoped identifier; it does not prove asset identity or authorize a change. Field edits remain staged proposals until reconciled through Application commands.

### 13.4 Handover navigator

Show deliverable matrix by system/discipline, artifact revision, approval, missing evidence, open obligations and acceptance signature. Export a deterministic manifest/evidence bundle rather than an undifferentiated document dump.

## 14. Proposed V3 logical module boundaries

- domains/change_management: change request semantics, classifications and MOC lifecycle.
- domains/configuration_management: baseline manifests, release states, supersession/status accounting; reuse 8I-37.
- domains/project_delivery: work packages, procurement/submittal/installation and milestones.
- domains/testing_commissioning: campaigns, procedures, execution records, evidence and milestones.
- domains/handover: acceptance package, operational handover and open obligations.
- application/change_workflow: commands, orchestration, impact analysis and approval transitions.
- application/test_workflow: test plan/execution transitions and evidence aggregation.
- application/readiness: stage-specific evaluation using 8I-38 and domain-owned evidence.
- infrastructure/evidence_store: immutable artifact references, digests, retention and custody metadata.
- infrastructure/document_control: document revision, transmittal and status integration.
- plugins/engineering: one consolidated extension host for equipment-family templates and vendor adapters.
- ui/change_workspace, ui/commissioning, ui/handover: projections/interactions only.

These are logical boundaries, not one manager/service per folder. Reuse Application transaction/event infrastructure, validation orchestration, dependency graph, typed diagnostics, identity/configuration model and consolidated plugin host. Do not duplicate project managers, workflow engines, event buses, approval engines or document registries.

## 15. Standards and reference map — candidate baseline

| Reference | Relevance | Evidence boundary |
|---|---|---|
| IEC 62337:2012 | E&I commissioning phases/milestones from completion of erection through mechanical completion, commissioning, performance test and plant acceptance | Process-industry lifecycle reference; IEC webstore lists stability date 2026; verify current status/successor |
| IEC 62381:2024 Ed.3 | FAT, optional FIT, SAT and SIT requirements/checklists for process-industry automation | Does not replace loop checks, commissioning or SIS validation |
| IEC 62382:2012 Ed.2 | E&I loop-check steps between loop construction/point-to-point checks and cold commissioning | Verify current status and project applicability |
| IEC 61850-10:2012+AMD1:2025 CSV | Conformance testing for IEC 61850 client/server/sampled-value devices and engineering tools | Device/tool conformance, not proof of complete site scheme |
| IEC 61511-1:2016+AMD1:2017 CSV | SIS lifecycle for specification, design, installation, operation and maintenance | Apply where SIS/SIF scope exists |
| ISO 10007:2017 | Configuration management planning, identification, change control, status accounting and audit | ISO catalogue reports confirmed current in 2023; recheck status |
| IEC 60255 series | Measuring relay and protection equipment/function testing | Select applicable part/edition; criteria need approved source |
| IEC 61970 / IEC 61850 series | Network model and substation automation configuration exchange | Interoperability evidence, not replacement for canonical model |
| ISO 55000:2024 / ISO 55001 | Asset management and lifecycle governance | Does not define electrical commissioning methods |

IEC 62337:2012 describes E&I commissioning milestones and includes mechanical completion, cold commissioning/start-up, hot commissioning/start of production, performance test and plant acceptance. IEC's publication page lists a 2026 stability date; verify status or successor before V3 freeze. [IEC 62337:2012](https://webstore.iec.ch/en/publication/6871).

IEC 62381:2024 is the third edition and defines FAT, optional FIT, SAT and SIT requirements/checklists. Its scope distinguishes these tests from loop checks and commissioning; basic testing under this standard is not SIS validation. [IEC 62381:2024](https://webstore.iec.ch/en/publication/103863); [scope/exclusions reference](https://www.iteh.eu/catalog/standards/iec/7246e7b6-95e3-4ff2-9c71-d8719160a6de/iec-62381-2024).

IEC 62382:2012 describes loop checks from completion of loop construction/installation and point-to-point checks to the start of cold commissioning. [IEC 62382:2012 sample](https://cdn.standards.iteh.ai/samples/18026/efc32dd5cae141a89ea953e92743b4bf/IEC-62382-2012.pdf).

IEC 61850-10:2012+AMD1:2025 CSV covers conformance testing of client/server/sampled-value devices and engineering tools; the 2025 amendment updates/adds client, sampled-value, tool and GOOSE performance procedures. [IEC consolidated publication](https://webstore.iec.ch/en/publication/108858).

IEC 61511-1:2016+AMD1:2017 CSV addresses SIS lifecycle requirements for specification, design, installation, operation and maintenance. [IEC 61511-1](https://webstore.iec.ch/en/publication/24241).

ISO 10007:2017 provides configuration-management guidance covering planning, identification, change control, status accounting and configuration audit. ISO's catalogue page says it was reviewed and confirmed in 2023; recheck status before V3 freeze. [ISO 10007:2017](https://www.iso.org/standard/70400.html).

The standards map is a candidate baseline, not completed BIS catalogue verification, clause-level compliance assessment, certification claim or normative implementation decision. Verify editions, amendments, corrigenda, status, jurisdiction and Indian adoption before freezing requirements.

## 16. Candidate acceptance scenarios (not executed)

1. **V3-MOC-01:** change request identifies scope, origin, reason, risk class, impacted objects and authority.
2. **V3-MOC-02:** topology/Protection/Control/instrumentation change cannot be released without required domain reviews/approval.
3. **V3-MOC-03:** approval binds to exact digest; relevant post-approval change makes it stale.
4. **V3-MOC-04:** emergency changes preserve authorization, time limits, compensating controls and retrospective review.
5. **V3-MOC-05:** temporary bypass expiry raises findings without automatically actuating equipment or weakening runtime guards.
6. **V3-BASE-01:** approved baseline is immutable and contains exact revision references/digest.
7. **V3-BASE-02:** design, vendor data, as-built, tested, commissioned and active configurations remain distinguishable.
8. **V3-REV-01:** layout-only change does not invalidate unrelated electrical/Protection tests.
9. **V3-REV-02:** relay setting, CT ratio/polarity, IED mapping or topology change invalidates only dependent evidence.
10. **V3-PROC-01:** received item differing from approved specification creates discrepancy; nameplate does not overwrite design.
11. **V3-MC-01:** mechanical completion requires explicit boundary, installation evidence and punch disposition.
12. **V3-TEST-01:** each test binds to exact equipment, hardware/firmware/software and configuration revisions.
13. **V3-TEST-02:** FAT/FIT/SAT/SIT, loop checks and commissioning remain separate record types.
14. **V3-TEST-03:** post-test change triggers dependency-based retest/regression analysis.
15. **V3-TEST-04:** incomplete coverage, uncalibrated tools or missing evidence cannot pass.
16. **V3-PROT-01:** relay injection does not imply primary wiring, trip circuit, breaker operation or end-to-end validation unless separately evidenced.
17. **V3-PROT-02:** Protection test acceptance cannot override live fail-closed dispatch preconditions.
18. **V3-CTRL-01:** simulated Control I/O/FAT evidence differs from field loop checks and live functional tests.
19. **V3-SIS-01:** basic automation FAT/SAT/SIT is not SIS/SIF validation.
20. **V3-COM-01:** commissioning milestones require scoped prerequisites; plant-wide status cannot hide blocked subsystem.
21. **V3-COM-02:** readiness report cannot authorize energization/start-up.
22. **V3-ASB-01:** device readback/redline is as-built evidence first; approved configuration requires reconciliation/change control.
23. **V3-HO-01:** handover manifest contains revisioned evidence, approvals, open obligations and accepted baseline digest.
24. **V3-HO-02:** conditional acceptance requires scope, authority, restrictions, compensating measures, owner and expiry; safety gates remain blocking.
25. **V3-HO-03:** post-handover maintenance/replacement/firmware/settings changes preserve prior accepted baseline and create new records.
26. **V3-OFF-01:** offline field evidence preserves source identity, local time quality and sync/conflict status.
27. **V3-PLG-01:** absent optional test plugin does not destroy records; missing required capability is reported incomplete.
28. **V3-PRJ-01:** project remains reopenable without external document control, asset registry or historian.

These are proposed acceptance criteria for future specification. They have not been implemented or executed and do not imply current product capability.

## 17. Open decisions and dependencies

- Lifecycle profiles, system breakdown structure and milestone ownership.
- State machines and transition evidence by aggregate type.
- MOC risk classification, emergency change procedure and non-waivable controls.
- Approval matrix/separation of duties by change/test class.
- Baseline manifest and relationship to canonical project package.
- Vendor document statuses, procurement/receipt scope and ERP/CMMS integration.
- Mechanical completion certificate and punch-list classification.
- Test schema, procedure authoring, calibration register and offline capture.
- FAT/FIT/SAT/SIT scope and retest rules by equipment/subsystem.
- Protection test catalogue and function-specific acceptance criteria sources.
- Control/interlock and SIS validation boundaries.
- Commissioning profile and owner authorization references.
- Handover content, retention, digital signature/trust and evidence custody.
- Temporary bypass expiry governance.
- As-built/readback reconciliation and activation/effective-time model.
- BIS adoption/current status verification for IEC 62337, IEC 62381, IEC 62382, IEC 61511, IEC 61850-10 and applicable IEC 60255 parts.
- Integration with 8I-37 identity/revision lineage and 8I-38 validation/invalidation.
- UI-GATE-02 through UI-GATE-07 remain open; this research does not close them.

Dependencies: 8I-22 revision/change control; 8I-25 standards traceability; 8I-35 operational command lifecycle; 8I-36 operational event/evidence records; 8I-37 identity/configuration versioning/lineage; 8I-38 validation/selective invalidation; 8I-33 Signal/Measurement; 8I-34 Protection/Control; UI gates and existing project/document workflow research.

## 18. Frozen invariants and scope boundary

- Core owns electrical/domain truth; Application owns controlled mutation/workflow orchestration; UI is projection/interaction.
- Approved baselines, test evidence, commissioning records and handover decisions are immutable or append-only with amendment/supersession.
- Design intent, vendor data, installed/as-built condition, test configuration, commissioned configuration and live state are distinct.
- Change approval binds to exact content/dependencies; relevant changes invalidate approval and affected test evidence.
- FAT/FIT/SAT/SIT, loop checks, commissioning and SIS validation are distinct.
- Relay injection pass does not imply complete primary wiring, trip path or scheme validation.
- Readiness evidence cannot authorize energization, switching, startup or device commands.
- No lifecycle workflow weakens fail-closed Protection dispatch, Control safety boundaries, authorization or interlocks.
- External document/asset systems and optional plugins are not mandatory to reopen canonical project.
- V2 architecture, persistence and .gridforge package semantics remain frozen; all proposals are V3-only and require explicit approval before implementation.

**Scope boundary:** research and architecture specification only. No source code, MOC workflow, baseline manager, document-control service, test runner, commissioning module, handover UI, plugin, database, migration, benchmark, test or CI was implemented or executed. V2 main was not modified.
