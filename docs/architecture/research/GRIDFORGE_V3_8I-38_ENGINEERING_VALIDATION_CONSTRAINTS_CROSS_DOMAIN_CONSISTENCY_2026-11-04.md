# GridForge V3 Architecture Research — 8I-38
## Engineering validation, constraint management and cross-domain consistency
**Research date:** 2026-11-04  
**Register lineage:** GridForge V3 Research and Change Register; 8I-11, 8I-22, 8I-33–8I-37  
**Status:** Proposed V3 architecture; research record only; approval required before implementation.

## 1. Objective and boundary

Define a coherent validation architecture for engineering data, topology, equipment, instrumentation, Protection, Control, studies, configuration exchange and operational workflows. Validation must provide trustworthy, explainable findings while preserving domain authority and avoiding a monolithic rule engine that silently becomes the owner of engineering truth.

The architecture must answer:
- What invariant or requirement is being checked?
- Which domain owns that rule and its interpretation?
- Against which immutable input/configuration snapshot was it evaluated?
- At what workflow stage must it run?
- Is the finding blocking, advisory, conditional or informational?
- Which objects, dependencies and downstream consumers are affected?
- Can the result be reproduced and audited?
- What changes invalidate the result, and what remains valid historically?

This is V3 research only. It does not authorize implementation, alter V2, or close existing issue/UI gates. It does not assert that GridForge is certified or compliant with any cited standard.

## 2. Principal architecture decisions

1. **Domain-owned rules, coordinated execution.** Core and each domain own their invariants. Application orchestrates rule execution for commands, change sets, imports, studies and commissioning workflows. There is no second, parallel engineering authority.
2. **One validation contract, multiple rule authorities.** Standardize rule metadata, execution context, findings, evidence and lifecycle; do not centralize domain-specific algorithms or constraints in one generic rules module.
3. **Validation is not authorization.** A clean validation report does not authorize a device command, bypass dispatch interlocks, or replace Protection's live fail-closed preconditions.
4. **Separate static, contextual and runtime checks.** Schema/type correctness, topology consistency, configuration compatibility, live measurement quality and dispatch eligibility are different validation contexts.
5. **Stage-aware enforcement.** A finding may be advisory during draft design and blocking at approval, commit, commissioning or dispatch. Severity and enforcement policy are explicit, not inferred from UI color or message text.
6. **Immutable validation evidence.** A report references exact object revisions, dependency fingerprints, rule-pack versions, standards editions, input snapshots and evaluator versions.
7. **Incremental but conservative.** Dependency metadata determines which checks need rerunning. Missing or corrupt dependency metadata must never create a false clean result for a safety-relevant consumer.
8. **No false precision.** Unknown, stale, unavailable or untrusted data is represented explicitly. A validator must not invent values, infer missing topology from drawing proximity, or convert uncertainty into a pass.
9. **Findings are actionable records.** Each finding has a stable identity, severity, scope, evidence, remediation guidance, lifecycle and disposition history.
10. **Plugins extend through public contracts.** Plugin rules are registered through the consolidated engineering plugin host and execute under declared capabilities; they cannot mutate Core or bypass Application, authorization, audit or Protection safeguards.

## 3. Validation taxonomy and ownership

### 3.1 Rule families

Use typed rule families with explicit ownership:

- **Schema and structural rules:** required fields, data types, enumerations, cardinality, schema compatibility and unknown-field handling.
- **Identity and reference rules:** immutable ID integrity, designation uniqueness within namespace, reference resolution, alias conflicts and external mapping validity.
- **Electrical equipment rules:** equipment-specific ratings, terminal definitions, phase/sequence compatibility, connection limits and parameter plausibility.
- **Topology rules:** terminal-to-terminal connectivity, graph consistency, bus membership, phase compatibility, grounding, open/closed interpretation and topology model integrity.
- **Engineering constraint rules:** voltage/current/power ranges, thermal limits, equipment duty, insulation/clearance assumptions and design envelope checks where supported by authoritative data.
- **Instrumentation and measurement rules:** CT/PT/CVT ratios, polarity, burden/accuracy data where modeled, source association, channel mapping, units, calibration, timestamps, freshness and quality.
- **Protection rules:** function-specific setting constraints, input availability, measurement suitability, zone/CT association, breaker/target mapping, setting coordination evidence and evaluation preconditions.
- **Control rules:** typed I/O, logic graph consistency, interlock dependencies, execution-cycle assumptions, command target typing, safe-state and feedback contracts.
- **Study and solver rules:** model completeness, assumption consistency, solver applicability, convergence status, result validity and reproducibility metadata.
- **Signal and communication rules:** signal type/quality semantics, endpoint identity, protocol mapping, IED/SCL consistency, subscription and data-set references.
- **Cross-domain consistency rules:** relationship compatibility across Core, Signal/Measurement, Protection, Control, asset/configuration, operational event and study domains.
- **Governance and workflow rules:** approval, effective date, authority, provenance, change-set scope, required evidence and separation-of-duty policy.
- **Operational readiness rules:** commissioned baseline, active configuration match, communications health, required live feedback and device/plant readiness; these do not replace live dispatch guards.

### 3.2 Ownership matrix

| Rule subject | Rule authority | Application role |
|---|---|---|
| Core object/schema invariants | Core owning domain | Invoke and aggregate |
| Electrical equipment parameters | Core equipment domain | Coordinate command validation |
| Connectivity/topology | Core topology domain | Coordinate topology transaction |
| SLD representation/layout | SLD projection domain | Validate projection consistency only |
| Signal definitions, acquisition and quality | Signal/Measurement domain | Coordinate dependencies and evidence |
| Protection settings and evaluation preconditions | Protection domain | Coordinate lifecycle and dispatch boundary |
| Control logic and I/O | Control domain | Coordinate compile/activation lifecycle |
| Study assumptions and numerical model | Study/solver domain | Coordinate immutable run snapshot |
| Asset lifecycle/governance | Asset Management / Data Governance domains | Coordinate approvals and change sets |
| SCL/CIM/vendor exchange | Integration adapter plus target domain | Stage, map, validate, reconcile |
| UI presentation | UI | Display findings; never authoritatively pass/fail Core constraints |

A cross-domain rule must have a named owner for its semantic decision. Application may compose evidence from multiple owners but must not reimplement their rules. If no domain owns a rule, that is an architecture gap to resolve before the rule becomes blocking.

## 4. Canonical validation contract

### 4.1 Rule definition

Each rule definition should declare:

- stable rule ID and semantic version;
- owning domain and responsible capability;
- rule family and target object/relationship types;
- human-readable title, explanation and remediation guidance;
- executable implementation/evaluator version;
- input fields and typed dependency declarations;
- required context and minimum data quality;
- applicable workflow stages;
- severity defaults and policy-overridable enforcement class;
- applicability predicate and explicit exclusions;
- standards/reference mapping, edition and clause where verified;
- deterministic/non-deterministic behavior declaration;
- performance and resource classification;
- plugin identity/signature and capability requirements where applicable;
- rule lifecycle: draft, active, deprecated, withdrawn.

Rule IDs are stable identifiers, not localized message text. Changing semantics requires a new rule version and a migration/compatibility note. Rules must not be silently reinterpreted when a standard edition changes.

### 4.2 Validation request/context

A validation request is an immutable description of what is being checked. It should identify:

- project and target object IDs;
- target revision(s) and change-set ID, if applicable;
- workflow stage and requested validation profile;
- snapshot timestamp and effective-time policy;
- topology/configuration/measurement revision fingerprints relevant to the request;
- exact rule-pack versions and policy version;
- data-quality and freshness requirements;
- execution purpose: draft feedback, commit gate, approval, commissioning, study, import or runtime readiness;
- caller principal and authorization context;
- explicit operating mode: design-time, offline study, replay, commissioning or live operation.

The request must not contain mutable object references that can change underneath evaluation. Resolve all inputs to immutable snapshots or version-qualified read models before execution.

### 4.3 Finding/report contract

A finding should include:

- stable finding ID and rule ID/version;
- severity and enforcement class;
- status: open, acknowledged, waived, resolved, superseded or accepted-with-condition;
- affected object IDs and precise property/relationship paths;
- concise diagnostic and engineering explanation;
- observed value, expected constraint and units where applicable;
- evidence references and provenance;
- exact revisions/snapshot and evaluator/rule-pack versions;
- first detected and last evaluated times;
- dependency fingerprint and invalidation cause;
- remediation options or corrective action reference;
- waiver/exception authority, reason, scope and expiry where permitted;
- links to related findings and parent/child aggregation.

A report includes request identity, start/end times, completion status, rule coverage, skipped/inapplicable rules with reasons, findings, evaluator metadata and content digest. Distinguish **pass**, **fail**, **blocked/incomplete**, **not applicable** and **not evaluated**. An execution error or skipped rule is never equivalent to pass.

### 4.4 Determinism and reproducibility

For deterministic rules, the same immutable inputs, rule versions, policy and evaluator version must produce equivalent findings. Rules that depend on live or external data must capture source timestamp, quality, identity and snapshot provenance and be labeled contextual/non-repeatable as appropriate.

Never rewrite a prior report after a rule changes. Produce a new report and link it as a re-evaluation. Preserve the old report as evidence of what was known under the old rule pack and inputs.

## 5. Severity, enforcement and exception policy

### 5.1 Separate severity from enforcement

Severity describes engineering consequence; enforcement describes what a workflow is allowed to do.

Suggested severity:
- **Critical:** credible risk of unsafe or invalid engineering/operation if ignored.
- **Major:** material engineering inconsistency or missing prerequisite.
- **Moderate:** incomplete or questionable data that may affect downstream use.
- **Minor:** limited-quality or documentation issue.
- **Informational:** notice, recommendation or non-blocking observation.

Suggested enforcement:
- **Hard block:** operation/transition cannot proceed.
- **Conditional block:** proceed only after explicit named prerequisite/evidence.
- **Review required:** designated review/approval required.
- **Warning:** proceed with visible recorded acknowledgement where policy permits.
- **Information:** no workflow block.

The mapping is domain- and stage-specific. A low-severity-looking missing dependency can still be a hard block for a safety-relevant dispatch precondition. Conversely, a major design-quality issue need not prevent exploratory draft placement. Never use a single numeric score to collapse severity, uncertainty and enforcement.

### 5.2 Waivers and accepted deviations

Waivers are controlled governance records, not edits to findings. A waiver must specify rule/finding, object and revision scope, rationale, risk owner, authorizer, evidence, start/expiry, compensating controls and review trigger. Some rules must be non-waivable, especially runtime Protection fail-closed preconditions, authorization checks and command-target integrity.

A waiver must not silently propagate to a successor equipment item, changed revision, new project branch or changed operational context. Re-evaluate scope after relevant dependency changes. Expired, invalidated or unauthorized waivers restore the applicable enforcement.

### 5.3 Unknown and unavailable values

Represent missing, unknown, stale, substituted, estimated, invalid and unavailable distinctly. Do not treat null as zero, stale as current, bad quality as good, or missing as default unless a domain rule explicitly defines a safe default and records it. For safety-relevant checks, insufficient evidence yields blocked/indeterminate, not pass.

## 6. Workflow-stage validation

### 6.1 Draft editing and live feedback

During interactive design, validate cheap local rules continuously or on change:
- field type/unit/range;
- required terminal and property definitions;
- local connection compatibility;
- designation collision;
- obvious reference-resolution errors.

Debounce or schedule expensive cross-project checks; avoid blocking canvas interaction with full-network validation on every pointer movement. Draft validation may show incomplete work as expected, but must label findings as provisional and identify the missing context.

### 6.2 Command preconditions and transaction validation

Before an Application command mutates canonical state:
- validate command shape and authorization;
- validate domain invariants against the proposed transaction;
- validate relationship cardinality and identity/reference integrity;
- verify the expected revision has not changed;
- verify required dependencies are available and version-consistent;
- ensure mutation and emitted events describe the same accepted state.

A failed command must not partially mutate canonical state. If a multi-domain workflow cannot be atomic, use explicit staged/compensating activation with durable status and recovery semantics; do not imply distributed atomicity.

### 6.3 Change-set validation and approval

A change set receives:
1. structural validation;
2. domain validation;
3. cross-domain impact/consistency validation;
4. policy and approval validation;
5. final revision/fingerprint check before approval or activation.

Approval must bind to the exact change-set digest and validation report(s). If any relevant input, rule pack or change-set content changes after approval, approval becomes stale and the required validation/approval stages repeat.

### 6.4 Commit and persistence boundary

Before a user-visible engineering commit:
- ensure canonical objects and relationships are valid;
- ensure the transaction's expected revision is current;
- persist the change and audit record coherently;
- emit events only for accepted committed changes;
- update projections asynchronously or through defined consistency guarantees.

Do not confuse a draft canvas action, UI save, project package write, study run or command dispatch with one universal commit. Each has a defined consistency boundary.

### 6.5 Study execution

A study run must capture an immutable model snapshot, assumptions, solver settings/version, input provenance and validation report. Validation must distinguish:
- structurally incomplete model;
- unsupported model feature;
- invalid study assumption;
- numerically ill-conditioned or non-convergent case;
- successful computation with limited applicability;
- successful computation whose input data quality is poor.

A solver's numerical convergence is not proof that the engineering model is correct. A study may be allowed in exploratory mode with explicit limitations, while an approved design report may require stricter completeness and provenance.

### 6.6 Commissioning and as-built acceptance

Commissioning validation compares approved design, installed/as-built facts, device settings/readbacks, signal mappings, calibration evidence, functional tests and required operational records. Differences become explicit reconciliation findings; do not silently overwrite approved design or as-built baselines.

A commissioning acceptance record binds to equipment identity, installed-item identity, configuration revision, test evidence, responsible roles and effective time. Operational readiness is separate from engineering design validation.

### 6.7 Live Protection dispatch

Protection dispatch uses its own synchronous, fail-closed guard contract. It must not depend on an asynchronous project-wide validation report or cached green dashboard. Immediately before state mutation, validate the exact current Protection decision and target authorization against the required live dependency state, including:
- decision freshness and validity;
- element-specific dependency fingerprint;
- required measurement availability, quality and freshness;
- topology/instrumentation/configuration revisions required by that element;
- target mapping and breaker/device identity;
- interlocks, operating mode and command authorization;
- expiry, duplicate/replay and command lifecycle preconditions.

Any missing, stale, inconsistent or unverifiable safety dependency blocks dispatch. A recent successful offline validation report cannot override a failed live precondition. Revalidation must isolate only the affected Protection element when dependency integrity is established; if it is not established, fail closed for the affected safety boundary rather than claiming unaffected status.

## 7. Cross-domain consistency and constraint graph

### 7.1 Typed consistency edges

Cross-domain rules traverse explicit typed relationships, never labels, display text, matching tags or visual proximity. Candidate dependency paths include:

- equipment → terminal → topology connection → network model;
- CT/PT/CVT → primary association → secondary channel → signal → typed measurement;
- measurement → Protection input → Protection element → decision → authorized target;
- Control logic input/output → signal/measurement → command target → feedback;
- IED/SCL logical node/data object → communication mapping → signal/control point;
- equipment configuration → study snapshot → result → report;
- installed asset → engineering equipment → commissioning evidence;
- operational event/alarm/SOE/historian/disturbance → source object and exact configuration lineage.

Each edge has owner, relation type, revision and provenance as defined in 8I-37. Cross-domain validation reads these contracts; it does not duplicate or own the relationships.

### 7.2 Rule graph and dependency graph are distinct

Maintain two related but different graphs:
- **Rule applicability graph:** which rules apply to which object types, workflows and conditions.
- **Data dependency graph:** which inputs and revisions a rule actually consumed.

A rule may apply to an object but not be evaluated because a prerequisite is absent. A finding must state this. The data dependency graph records actual inputs; it is the basis for invalidation and reproducibility.

### 7.3 Constraint categories

Support:
- scalar bounds and engineering ranges;
- enumerations and allowed combinations;
- dimensional/unit/quantity constraints;
- cardinality and uniqueness;
- graph reachability and connectivity;
- phase, voltage-level and equipment compatibility;
- temporal ordering, freshness and expiry;
- cross-object equations/consistency;
- state-machine transition preconditions;
- resource/capacity and operating envelope constraints;
- reference/namespace resolution;
- provenance and approval completeness.

Rules must declare whether a bound is inclusive/exclusive, nominal/absolute, phase-specific, temperature-dependent, manufacturer-specific or project-policy-defined. A validator must not invent tolerances. Engineering limits need a traceable source: standard/edition/clause, manufacturer data, approved design basis or explicit project policy.

## 8. Incremental validation and selective invalidation

### 8.1 Dependency declaration

Every rule declares the exact properties, relationships, revisions and contextual sources it reads. At execution, record the resolved dependency set and fingerprint. Avoid broad "whole project changed" dependencies unless the rule genuinely depends on the entire project.

### 8.2 Invalidation

A change invalidates findings/reports whose recorded dependencies intersect the changed revision domains or source snapshots. Examples:
- display label or SLD coordinate: invalidate affected presentation/read-model checks only;
- terminal connectivity/topology: invalidate topology, network model and dependent study/Protection checks;
- CT ratio/polarity/calibration/channel mapping: invalidate only measurements and Protection/Control consumers depending on that instrumentation path;
- one Protection function setting: invalidate that function's checks and dependent decisions, not unrelated functions;
- Control logic revision: invalidate affected compile/logic/sequence/target checks;
- SCL/IED mapping change: invalidate mapped communication/signal/control/Protection consumers;
- alarm presentation text: do not invalidate electrical topology or Protection calculations.

### 8.3 Unknown dependencies

If a rule or consumer does not provide trustworthy dependency metadata:
- mark its result as dependency-incomplete;
- do not reuse a cached pass;
- rerun the conservative scope defined by its owning domain;
- for live Protection, block dispatch if required safety dependencies cannot be established.

Do not default every change to whole-project invalidation. Conservative fallback is scoped to the rule's declared safety boundary and must be measurable and diagnosable.

### 8.4 Cache correctness

A cached report is reusable only when rule/evaluator/policy versions, exact dependency fingerprint, context/stage, effective-time assumptions and required data-quality/freshness conditions match. A cache hit must be observable in diagnostics. Time-sensitive rules expire based on explicit freshness/expiry semantics even if no configuration revision changes.

## 9. Diagnostics, remediation and finding lifecycle

### 9.1 Diagnostic quality

Every user-facing finding should answer:
- What is wrong or unknown?
- Where exactly is it?
- Why does it matter?
- Which rule and authority produced it?
- What evidence and input revisions were used?
- What workflow is blocked or limited?
- What is the safest next corrective action?
- What will be revalidated after correction?

Use engineering terms and measured values/units. Avoid vague "invalid configuration" messages without a path and evidence. Never expose stack traces as the primary engineering diagnostic; retain technical details in logs/audit evidence.

### 9.2 Lifecycle

Suggested finding lifecycle:
- detected;
- triaged/assigned;
- acknowledged;
- correction proposed;
- revalidated;
- resolved;
- accepted deviation/waived (only where permitted);
- superseded by a newer rule/revision;
- reopened when a dependency changes or waiver expires.

Acknowledgement is not resolution. A resolved finding is tied to a new report proving the relevant condition is corrected. Superseded findings remain historically visible.

### 9.3 Remediation model

Remediation may be:
- direct property correction through an owning Application command;
- relationship/topology correction through Core/Application;
- mapping reconciliation through integration workflow;
- measurement source/calibration correction;
- configuration change set and review;
- data acquisition repair or refresh;
- documented design deviation/waiver;
- explicit unsupported/unknown limitation.

Do not let a generic "auto-fix" mutate safety-critical values. Suggested fixes are proposals; changes require domain command, authorization, validation and audit. Bulk remediation must preview all affected objects and downstream dependencies.

## 10. Rule packs, standards and plugin governance

### 10.1 Versioned rule packs

A rule pack groups versioned rules for a domain, project profile, equipment family, standard edition or workflow. It declares:
- pack ID/version and content digest;
- included rule IDs/versions;
- source standard editions and clause references;
- applicability profile and exclusions;
- severity/enforcement policy defaults;
- compatibility and migration notes;
- approval status and effective date.

Project reports pin exact rule-pack versions. Updating a standard or rule pack creates a new version; it does not silently rewrite historical results or automatically change the active project policy.

### 10.2 Standards traceability

Maintain a standards register with publication number, edition/amendments/corrigenda, status, jurisdiction/adoption, clauses, interpretation notes, verification date and rule mappings. Distinguish:
- normative requirement directly transcribed from an accessible verified standard;
- project engineering policy;
- manufacturer limit;
- engineering recommendation;
- GridForge internal integrity invariant.

Do not claim a rule is "IEC compliant" because it is inspired by a standard. Record clause-level mapping and independent review before making a compliance assertion. BIS adoption and applicable Indian editions require separate catalogue verification.

### 10.3 Plugin rules

A plugin rule must declare its owner, rule ID/version, target types, dependencies, execution stage, resource budget, trust level and output contract. The consolidated plugin host controls discovery, version compatibility, registration and capability boundaries. Plugin rules:
- receive immutable read-only snapshots;
- cannot write Core state or invoke hidden mutation paths;
- cannot suppress or downgrade a core/domain hard block;
- cannot change Protection dispatch guard policy;
- cannot impersonate trusted standard rules;
- must preserve provenance and plugin version in findings;
- must be isolated from the critical synchronous dispatch path unless explicitly reviewed and approved as part of that path.

A missing plugin must not erase stored findings or plugin-defined data. If a required plugin rule is unavailable, report incomplete validation; do not mark the project clean.

## 11. UI/UX architecture: engineering validation at the point of work

### 11.1 Unified Validation Center

Provide one Validation Center as a cross-domain read model, not a central rule owner. It should support:
- project summary by domain and workflow stage;
- severity/enforcement filters;
- open, acknowledged, waived, resolved and stale findings;
- rule pack and report provenance;
- affected object and dependency navigation;
- batch assignment and review;
- exportable evidence report.

Show counts with scope and timestamp. "0 errors" must not be displayed if rules were skipped, validation was incomplete or required live checks were not evaluated.

### 11.2 Contextual diagnostics

Expose relevant findings in the active workspace:
- SLD: highlight affected equipment/terminal/connection; do not alter geometry or topology to hide an issue.
- Equipment inspector: field-level constraints, source and units, with links to affected studies/Protection/Control consumers.
- Protection editor: function-specific settings, measurement quality, zone and target mapping; separate design findings from live dispatch status.
- Control canvas: I/O typing, unresolved references, logic reachability and execution/feedback contract.
- Signal inspector: source/channel mapping, unit, calibration, quality, timestamp and freshness.
- Study workspace: model completeness, assumptions, solver diagnostics and result applicability.
- Import/reconciliation: source-vs-canonical diff, unmatched/ambiguous mappings and staged validation.

### 11.3 Progressive disclosure and remediation

Prioritize blockers relevant to the current task. Provide concise summary, expandable engineering explanation, exact evidence, then corrective action. Group duplicates by root cause while preserving individual affected object references. Do not flood users with repeated downstream findings when one upstream missing mapping explains them; retain traceability to every affected consumer.

Actions such as "Fix", "Review", "Open object" or "Revalidate" must route through the owning Application/domain workflow. A UI acknowledgement never changes finding state unless a valid command records the acknowledgement and actor.

### 11.4 Validation profiles and user control

Offer named profiles such as:
- Draft feedback;
- Engineering commit;
- Design review;
- Protection configuration review;
- Control logic review;
- Study readiness;
- Import reconciliation;
- Commissioning acceptance;
- Operational readiness.

Users may request a profile, but cannot disable non-waivable Core invariants or live Protection guards. Profiles specify rules and stage policy transparently; they are not opaque "strictness" sliders.

## 12. Proposed V3 logical module boundaries

- `core/validation_contracts`: minimal value types for validation context, rule references, finding identity and immutable evidence references only where Core needs them; no generic engine or UI.
- `domains/<domain>/validation`: domain-owned rules, constraints, evaluators and semantic interpretation.
- `application/validation_orchestration`: request planning, scheduling, transaction/change-set integration, report aggregation and workflow enforcement.
- `application/impact_analysis`: dependency traversal and affected-consumer previews, reusing the shared dependency infrastructure.
- `application/finding_lifecycle`: assignment, acknowledgement, disposition and waiver commands/policy.
- `infrastructure/rule_registry`: versioned rule/pack discovery and persistence; no domain authority.
- `infrastructure/validation_execution`: bounded execution, deterministic context resolution, caching and diagnostics.
- `infrastructure/standards_registry`: verified standard editions and traceability mappings.
- `plugins/engineering`: one consolidated extension host for domain-aligned rule packs and adapters through public contracts.
- `ui/validation_center`: read models, filters, contextual overlays, remediation navigation and evidence presentation.

These are logical boundaries, not a prescription to create one service/manager per folder. Reuse existing Application services, event infrastructure, revision/dependency graph, typed diagnostics and plugin host. Avoid a second event bus, scheduler, registry, transaction manager or policy engine.

## 13. Standards and reference map — candidate baseline

| Reference | Relevance | Evidence boundary |
|---|---|---|
| IEC TS 61850-6-3:2025 | Machine-processable OCL rule format for validating IEC 61850 XML/SCL files at engineering stages and after schema-version transformations | Applies to SCL validation rule representation; not a universal GridForge validation language |
| IEC 61850-6:2009+AMD1:2018+AMD2:2024 CSV | SCL configuration description and exchange for IEDs, communications and substation functional structures | Validate exchange artifacts and mappings; do not equate SCL validation with Core model validation |
| ISO/TS 8000-82:2022 | Processable data rules for identifiers, quantities, dates/times, rates, text, codes and keys | Data-quality rule design; specific engineering rules remain domain-owned |
| IEC 60255-1:2022 | Common requirements for measuring relays and protection equipment, including distributed protection schemes | Reference for Protection equipment/configuration rule research; passing GridForge checks is not product conformity |
| IEC 60255-187-1:2021 | Functional requirements, performance evaluation and test documentation for differential protection of motors, generators and transformers | Function-specific requirements; applicability depends on implemented function and adopted edition |
| IEC 60255-26:2023 | EMC requirements for measuring relays and Protection equipment | Relevant to product/device qualification evidence, not a substitute for software configuration validation |
| IEC 61970 CIM series | Utility network model and exchange consistency | Validate mapped exchange semantics; retain GridForge canonical domain ownership |
| IEC 61360 / IEC CDD | Property, data type, classification and unit semantics | Use for dictionary/property validation with explicit versioned mappings |
| ISO 8000 series | Data quality and master-data rule/quality concepts | Complementary governance reference; not a source of electrical limits |

IEC TS 61850-6-3:2025 explicitly describes a machine-processable OCL format for validation rules and supports validation at different SCL engineering stages. IEC's publication page identifies it as a 2025 Technical Specification. The associated IEC 61850-6 consolidated SCL publication is IEC 61850-6:2009+AMD1:2018+AMD2:2024 CSV. [IEC TS 61850-6-3:2025](https://webstore.iec.ch/en/publication/79695); [IEC 61850-6 consolidated version](https://webstore.iec.ch/en/publication/103863).

ISO/TS 8000-82:2022 describes data rules for common data types and was confirmed current in January 2026. [ISO/TS 8000-82:2022](https://www.iso.org/standard/78707.html).

IEC 60255-1:2022 defines common requirements for measuring relays and Protection equipment; IEC 60255-187-1:2021 covers differential protection functional/performance evaluation for motors, generators and transformers. [IEC 60255-1:2022](https://webstore.iec.ch/en/publication/59762); [IEC 60255-187-1:2021](https://webstore.iec.ch/en/publication/32570).

The standards map is a candidate research baseline, not a completed BIS catalogue verification, clause-level compliance assessment, certification claim or normative implementation decision. Verify edition, amendments, corrigenda, status, jurisdiction and Indian adoption before freezing V3 requirements.

## 14. Candidate acceptance scenarios (not executed)

1. **V3-VAL-01:** a domain rule executes only through its declared owner/evaluator and reports its rule ID/version.
2. **V3-VAL-02:** an Application command is rejected atomically when a Core invariant fails; no partial canonical mutation or misleading committed event occurs.
3. **V3-VAL-03:** validation reports bind to exact immutable object revisions, rule-pack versions, policy and evaluator versions.
4. **V3-VAL-04:** incomplete/skipped/error states cannot be represented as a clean pass.
5. **V3-VAL-05:** identical deterministic inputs and evaluator versions produce equivalent findings.
6. **V3-VAL-06:** changing a standard/rule-pack version creates a new report and does not rewrite historical validation evidence.
7. **V3-VAL-07:** severity and enforcement are independently represented; a rule can be a warning in draft and a hard block at approval.
8. **V3-VAL-08:** a waiver records authority, rationale, scope, expiry and compensating controls; non-waivable runtime guards cannot be waived.
9. **V3-VAL-09:** null, unknown, stale, invalid and unavailable measurements remain distinct and cannot silently pass a safety-relevant check.
10. **V3-VAL-10:** a display label or SLD coordinate change invalidates only presentation-dependent rules.
11. **V3-VAL-11:** a topology change invalidates topology and only the dependent studies/Protection consumers.
12. **V3-VAL-12:** a CT ratio, polarity, calibration or channel mapping change invalidates only dependent measurements and Protection elements when dependency integrity is complete.
13. **V3-VAL-13:** missing/corrupt safety dependency metadata prevents cache reuse and blocks affected live Protection dispatch.
14. **V3-VAL-14:** a clean asynchronous validation report cannot override stale Protection decision, bad measurement quality, target mismatch or failed live authorization.
15. **V3-VAL-15:** a study report distinguishes numerical convergence from model validity and data-quality limitations.
16. **V3-VAL-16:** an SCL import is checked against the selected schema/rule pack, then separately reconciled against canonical GridForge domains.
17. **V3-VAL-17:** unavailable required plugin rules produce incomplete validation rather than false success; plugin rules cannot downgrade core/domain blocks.
18. **V3-VAL-18:** a finding can be traced from Validation Center to exact object/property, evidence, dependency and remediation command.
19. **V3-VAL-19:** acknowledgement does not resolve a finding; resolution requires a new validation result or approved disposition.
20. **V3-VAL-20:** a change after approval invalidates approval when it changes the approved change-set digest or relevant validation dependency.
21. **V3-VAL-21:** commissioning comparison preserves differences between approved design, as-built configuration and device readback.
22. **V3-VAL-22:** duplicate root-cause findings can be grouped in UI without losing per-object references or audit lineage.
23. **V3-VAL-23:** validation of a project without an optional historian, asset registry or external catalogue remains possible for rules whose declared dependencies do not require those services.
24. **V3-VAL-24:** rule execution limits, timeouts and evaluator errors are reported as incomplete/failed execution, never pass.

These are proposed acceptance criteria for future specification. They have not been implemented or executed and do not imply current product capability.

## 15. Open decisions and dependencies

- Final ownership matrix for every validation family and cross-domain rule.
- Canonical rule/finding/report schemas and stable identity strategy.
- Severity taxonomy, enforcement policy, workflow-stage matrix and non-waivable rule catalogue.
- Rule-pack governance, standards edition pinning, BIS adoption verification and clause-level review.
- Dependency declaration format and integration with 8I-22 selective invalidation and 8I-37 revision domains.
- Deterministic execution requirements, external/live input snapshot strategy and evaluator versioning.
- Transaction consistency and event publication semantics for failed/accepted validation-gated commands.
- Finding retention, acknowledgement, waiver, expiry and approval authority model.
- Safe execution/resource isolation for third-party plugin rules.
- SCL OCL rule import/adapter scope and supported IEC 61850 editions/profiles.
- Unit/quantity semantics and source of engineering limits (standard, manufacturer, design basis or project policy).
- Distinction between design-time readiness, study readiness, commissioning acceptance and live operational readiness.
- Validation Center information architecture and contextual diagnostic priority.
- Required behavior when domain owners, rules, plugins or dependency metadata are unavailable.
- BIS catalogue verification remains open for the relevant standards and Indian adoption.

Dependencies: 8I-11 typed diagnostics; 8I-22 revision/change control and selective invalidation; 8I-25 standards traceability; 8I-27 simulation/replay; 8I-33 Signal/Measurement; 8I-34 Protection/Control consumers; 8I-35 operational command lifecycle; 8I-36 event/alarm/SOE/historian/disturbance; 8I-37 identity, configuration versioning and lineage; UI-GATE-02 through UI-GATE-07.

## 16. Frozen invariants and scope boundary

- Core owns electrical/domain truth; each domain owns its engineering invariants; Application coordinates controlled mutation and validation workflows; UI is a projection and interaction layer.
- One validation contract does not mean one generic domain rule engine or duplicate central engineering authority.
- A validation pass never grants command authorization or replaces live Protection dispatch guards.
- Safety-relevant unknown, stale, missing or unverifiable dependencies fail closed.
- Validation evidence is immutable and bound to exact inputs, rule versions, policies and evaluator versions.
- Incremental invalidation follows typed dependencies; missing safety dependency metadata cannot produce a cached pass.
- Waivers cannot override non-waivable runtime safety, authorization or target-integrity invariants.
- Plugins cannot mutate Core or downgrade core/domain enforcement.
- SCL/CIM/dictionary standards are validation and interoperability references, not substitutes for GridForge's canonical domain model.
- V2 architecture, persistence and `.gridforge` package semantics remain frozen; all proposals here are V3-only and require explicit approval before implementation.

**Scope boundary:** research and architecture specification only. No source code, rule engine, validation service, schema, database, UI, plugin, migration, benchmark, test or CI was implemented or executed. V2 `main` was not modified.
