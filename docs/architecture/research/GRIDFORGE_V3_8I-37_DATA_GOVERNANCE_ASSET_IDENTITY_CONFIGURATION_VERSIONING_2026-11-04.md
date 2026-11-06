# GridForge V3 Architecture Research — 8I-37
## Engineering data governance, asset identity, configuration versioning and cross-domain lineage
**Research date:** 2026-11-04  
**Register lineage:** GridForge V3 Research and Change Register; 8I-21, 8I-22, 8I-25, 8I-33–8I-36  
**Status:** Proposed V3 architecture; research record only; approval required before implementation.

## 1. Objective and boundary

Establish the information-governance foundation for GridForge V3 so that every engineering object, configuration, relationship, measurement definition and operational record has an unambiguous identity, explicit authority/ownership, controlled revision history and traceable provenance throughout its lifecycle.

The system must distinguish identity from naming, classification, location, drawing representation, configuration revision and operational state. A renamed bus, moved SLD symbol, changed relay setting, replaced physical breaker, revised signal mapping and imported CIM/SCL identifier are not the same kind of change and must not have the same invalidation or persistence effects.

This section is a cross-domain governance contract. It composes Core electrical truth, Application-controlled mutation, SLD projection, Signal/Measurement, Protection, Control, operational traceability, alarm/SOE/historian and plugin contracts. It does not reopen frozen V2 architecture or authorize implementation.

## 2. Principal architecture decisions

1. **Immutable internal identity; mutable human designation.** Every persistent domain object receives a stable opaque identity. Names, tags, reference designations, aliases, labels and external identifiers are attributes or mappings, not primary keys.
2. **Separate asset, engineering object, product/type and installed instance.** A manufacturer model/type is not an installed physical asset; a logical engineering object is not automatically an asset-register record; an SLD symbol is only a view representation.
3. **Typed, versioned relationships.** Ownership, containment, electrical connectivity, functional association, measurement association, reference designation, replacement/successor and visual projection are distinct relationship types with explicit direction, cardinality, validity and provenance.
4. **Authority is domain-owned.** Each attribute and relationship has a declared authoritative owner. Replicas and external imports are projections or proposals until accepted through the owning Application service.
5. **Configuration is immutable by revision.** Approved configurations are immutable snapshots. Changes create a new revision/change set; historical operational evidence continues to reference the exact configuration that was active at the time.
6. **Separate configuration, state and observation.** Design/engineering configuration, commissioned/as-built baseline, live operational state, measured observation and simulation state are separate data planes. A measurement must not silently rewrite a nameplate rating or design parameter.
7. **Bitemporal provenance where needed.** Distinguish when a fact is valid in the engineered/physical world from when GridForge learned or recorded it. Late-arriving corrections must not rewrite the historical knowledge state without an explicit amendment.
8. **Semantic interoperability, not schema imitation.** IEC 81346, IEC 61360, IEC 61970 CIM and IEC 61850 SCL provide useful designation, classification, dictionary, power-system and configuration exchange models. GridForge retains its canonical domain model and uses explicit, versioned adapters/mappings.
9. **No global revision counter as a substitute for dependency tracking.** Revision domains are granular. A display-label change must not stale a Protection decision; a CT ratio/calibration/source mapping change may affect measurement derivation and selected Protection functions.
10. **Audit and lineage are first-class.** Every accepted change records actor/origin, reason, authority, source, before/after values or snapshots, affected objects, validation, approval and causal references.

## 3. Identity model and object taxonomy

### 3.1 Identity classes

Use distinct identifiers for distinct concepts:

- **Project identity:** stable identity of the GridForge project aggregate; package filename/path is not its identity.
- **Domain object identity:** immutable opaque ID for each Core object (equipment, terminal, connection, bus, protection function, control function, signal definition, measurement channel, etc.).
- **Asset identity:** identity of a physical asset tracked across organizational lifecycle, maintenance and replacement. It may be associated with one or more engineering objects over time.
- **Type/catalogue identity:** identity for a generic equipment class, standardized component concept, manufacturer product family or specific product model.
- **Installed-instance identity:** identity for a particular installed physical instance, including serial number and installation context where applicable.
- **Representation identity:** identity for an SLD symbol, canvas node, drawing annotation or other projection object. It never substitutes for Core identity.
- **Configuration identity/revision:** immutable identity of a configuration snapshot and its revision lineage.
- **Record identity:** family-specific identity for event, alarm, SOE, historian, disturbance, audit and command evidence as specified in 8I-36/8I-35.
- **External identifier:** source-system-scoped identifier such as CIM mRID, IEC 61850 IED/LN reference, ERP tag, CMMS asset number or vendor serial. Always namespaced by issuer/system and valid scope.

Prefer UUIDv7 or another opaque, collision-resistant ID strategy with documented generation and offline behavior. The chosen algorithm must not encode business meaning, plant hierarchy, equipment class, user identity or mutable designation. Distributed/offline creation must avoid collisions and support deterministic reconciliation; IDs must never be regenerated merely because an object is renamed, moved, reclassified or imported again.

A human-readable ID such as BUS-001 or CB-101 is a designation/tag governed by a naming policy. It may be unique within a declared scope, but it is not the canonical key. Reuse after retirement should be prohibited by default or require explicit policy and retained history.

### 3.2 Asset, equipment and product distinction

Model at least these concepts separately:

- **Asset:** an item with organizational value and lifecycle accountability; may be physical or non-physical, individual or a system/portfolio grouping.
- **Engineering equipment object:** the canonical electrical/domain object used in topology, calculations, Protection, Control and studies.
- **Physical installed item:** the actual manufactured/installed device with serial, manufacturer, model, manufacturing and installation facts.
- **Equipment type/class:** generic electrical function/type and its engineering schema/required characteristics.
- **Manufacturer product model:** catalogue product with manufacturer-specific ratings, options and technical documents.
- **SLD representation:** one or more projections of an engineering object in a particular sheet/view.
- **Operational endpoint/IED:** communication-addressable device identity and its protocol/IED configuration, which may host multiple logical functions and points.

Relationships may connect these concepts but they must not be collapsed. One engineering object may be associated with an installed physical item over a validity interval; replacement may create a new installed-item identity while preserving the logical engineering role or creating a new engineering object depending on the engineering change. A product model may be used by many installed items. One physical device may expose many signals and host multiple Protection/Control functions.

### 3.3 Stable identity and replacement

Replacement is not renaming. Record a typed succession/replacement relationship with effective time, reason, work package/reference, approval and commissioning evidence. Preserve the old asset/installed-item identity and all historical measurements, alarms, commands, maintenance and settings. The new item gets its own identity and serial; link it as successor/replacement. Engineering topology may be updated by a controlled change set and may require a new equipment object or an explicit continuity mapping. Never silently transfer historical operational records to the replacement object.

## 4. Designation, tags, classification and naming

### 4.1 Separate naming dimensions

Store separately:
- immutable internal ID;
- preferred display name;
- plant tag / equipment number;
- reference designation;
- functional location / plant hierarchy path;
- equipment class and type;
- manufacturer and model;
- serial / asset register identifier;
- aliases and legacy names;
- external system identifiers.

Each name/identifier must declare issuer, namespace, scope, uniqueness rule, language/locale if relevant, validity interval, source and status (preferred, alias, legacy, retired, disputed). Do not assume the same string has global uniqueness across projects, plants, drawings or source systems.

### 4.2 Reference designation system

IEC 81346-1:2022 provides general principles for structuring information and forming unambiguous reference designations across technical disciplines; it includes aspects and relationships. IEC 81346-2:2019 defines object classification schemes and letter codes and is currently marked for revision in the ISO catalogue. GridForge should support configurable RDS profiles and aspect-aware designation, not hard-code one universal tag syntax.

Reference designation must not be confused with object identity. A change to an aspect, hierarchy or designation may change the displayed reference while the underlying domain object identity remains stable. The system should support:
- functional aspect;
- product aspect;
- location aspect;
- project/plant-specific aspects where governed;
- single-level and multi-level designations;
- multiple valid designations for different aspects;
- explicit designation history and collision diagnostics.

The exact adopted RDS profile, use of prefixes/signs, class-code mapping and BIS adoption must be decided through project standards governance.

### 4.3 Naming service

A designation service should generate proposed names, reserve scopes, detect collisions, apply templates and validate references. Auto-numbering (e.g. BUS-001) is a convenience policy, not identity generation. Rename operations should be explicit Application commands and should update only approved references/read models. Historical event payloads and external source identifiers retain their original value plus the resolved canonical object ID.

## 5. Typed relationships and canonical engineering graph

The canonical model is a graph of typed objects and typed relations, not an untyped collection of foreign keys or labels.

Relationship families include:
- **composition/containment:** project, plant, system, bay, panel, device assembly and component;
- **electrical topology:** terminal-to-terminal connection, bus membership, conductor/branch endpoint, grounding and phase/sequence relation;
- **functional association:** protection zone, relay function, control loop, interlock, process unit and equipment function;
- **measurement association:** physical source, CT/PT/CVT, sensor, transducer, channel, signal and derived measurement;
- **communication association:** IED, logical device, logical node, data object, dataset, report/control block, endpoint and protocol point;
- **asset lifecycle:** installed-at, owned-by, maintained-by, replaced-by, successor-of, removed-from-service;
- **designation/classification:** classified-as, has-reference-designation, alias-of, mapped-to-external;
- **representation:** represented-by, placed-on-sheet, annotated-by;
- **provenance/dependency:** derived-from, configured-by, validated-against, supersedes, approved-by.

Every relation must declare relation ID, source/target IDs, relation type, cardinality/constraints, owner, revision, validity interval, recorded interval, provenance, status and applicable schema version. Avoid storing the same relation as independently editable copies in multiple domains. Cross-domain references should be stable IDs with explicit ownership and read-model projections.

Electrical topology is owned by Core and must remain distinct from asset containment and SLD drawing placement. A symbol's coordinates or sheet ownership cannot create electrical connectivity. Moving an asset in a plant hierarchy cannot silently move its terminals or change network topology. A reference designation relationship cannot substitute for a terminal connection.

## 6. Attribute ownership and master-data authority

Every governed attribute must declare:
- owning domain/service;
- authoritative source/system;
- mutability and command path;
- validation/schema rule;
- quality requirements and evidence;
- revision domain;
- downstream dependency categories;
- synchronization/import/export policy;
- whether it is engineering design, nameplate, as-built, live state, observation, derived or display-only data.

Illustrative ownership:
- equipment electrical parameters and terminals: Core/equipment domain;
- electrical connectivity/topology: Core topology domain;
- SLD coordinates, symbol style and sheet membership: SLD projection/layout domain;
- relay function settings and protection configuration: Protection domain;
- Control logic/program configuration: Control domain;
- sensor/channel calibration and source mapping: Signal/Measurement domain;
- live values and quality: acquisition/measurement records;
- manufacturer product data: governed catalogue/reference-data domain;
- asset ownership, installation/maintenance and lifecycle: Asset Management domain;
- protocol endpoint and IED configuration: communication/integration domain;
- external IDs: integration mapping registry;
- alarm rationalization and alarm lifecycle: Alarm Management domain.

The UI is never the authority. Plugins and adapters may propose changes through Application commands; they cannot write canonical records directly. Imports are staged, validated and reconciled before acceptance.

### 6.1 Data quality dimensions

Define machine-checkable quality controls at property level:
- identity completeness and uniqueness within namespace;
- semantic validity against type/dictionary;
- unit and quantity-kind correctness;
- allowed range and engineering plausibility;
- referential integrity and relationship cardinality;
- source/provenance completeness;
- temporal validity and freshness where applicable;
- consistency across related attributes;
- lifecycle status correctness;
- duplicate/conflict detection.

ISO 8000-100:2016 addresses master-data quality, including quality at the property-value level and quality requirements for exchange between systems; ISO reports it was reviewed and confirmed in 2026. Apply its data-quality concepts to exchange and governance, but do not claim it defines all GridForge engineering validation.

## 7. Configuration, state and observation planes

Never put every value into one mutable equipment dictionary. Distinguish:

1. **Type definition:** schema, required properties, constraints, allowed units, defaults and classification.
2. **Design configuration:** approved engineering intent and calculated/design values.
3. **Nameplate/manufacturer data:** manufacturer-declared values with source documents and revision.
4. **As-built/commissioned baseline:** verified installed configuration and commissioning evidence.
5. **Operational setting/configuration:** active relay, controller, IED, device or plant settings with effective period.
6. **Live state:** current discrete/continuous state reported by device or application.
7. **Observation:** acquired sample with timestamp, quality, source and calibration/mapping revision.
8. **Derived result:** calculated value/result with algorithm, input snapshot and lineage.
9. **Presentation metadata:** labels, units formatting, colors, symbol positions and view preferences.

These planes may be related by explicit derivation or adoption commands. A live measured voltage cannot silently overwrite nominal voltage. A manufacturer nameplate rating cannot silently overwrite a study assumption. A relay online setting readback cannot silently overwrite the approved engineering setting; it should create a comparison finding and controlled reconciliation workflow.

## 8. Revision and configuration versioning model

### 8.1 Immutable revision records

Every accepted configuration change produces an immutable revision record with:
- revision_id and parent revision(s);
- aggregate/object identity and revision domain;
- schema version and canonical content digest;
- author/principal, origin, timestamp and reason;
- change set and before/after references;
- validation report and unresolved findings;
- approval/review evidence and approver identity;
- effective-from/effective-to where applicable;
- source document/import package and provenance;
- compatibility and migration metadata.

Do not mutate an approved revision in place. Corrections create a new revision and an explicit supersession/amendment link. A revision number is scoped to its aggregate/domain; do not use one global project revision to invalidate every subsystem.

### 8.2 Change sets and controlled transactions

A change set groups intended edits with explicit scope and dependencies. Lifecycle: draft → validated → review-required → approved → applied/effective → superseded/withdrawn. Rejected, abandoned and conflicted change sets remain auditable but do not become active configuration.

A change set should include affected object IDs, attribute paths, relationship changes, dependency impact preview, validation results, required approvals and effective-time policy. Application services execute the accepted change atomically within the defined consistency boundary. If multiple domains require coordinated activation, use explicit staged activation/compensation semantics; never imply a cross-database atomic transaction without evidence.

### 8.3 Revision domains and selective invalidation

Maintain separate revision dimensions, for example:
- physical topology;
- equipment electrical parameters;
- instrumentation association;
- signal source/mapping;
- calibration;
- Protection settings/function configuration;
- Control logic/configuration;
- communication/IED configuration;
- asset lifecycle/installation;
- alarm definition/rationalization;
- SLD layout/presentation;
- study assumptions and solver configuration.

Dependencies are explicit and typed. A label or layout change should invalidate only relevant projections. A topology revision may invalidate network model snapshots and dependent studies. A CT ratio, polarity, calibration or channel mapping revision may invalidate only the affected measurement derivations and Protection elements that consume them. A relay setting revision should invalidate the corresponding Protection evaluation state, not unrelated relay functions or topology. The invalidation engine must fail closed when dependency metadata is missing or corrupt for a safety-relevant consumer, while not broadening invalidation indiscriminately when integrity is proven.

A revision vector or dependency fingerprint may summarize relevant revision IDs for an immutable snapshot. It must not replace the underlying typed dependency graph or be treated as a single project-wide counter.

### 8.4 Branching, comparison and merge

Engineering workflows may need parallel design alternatives, review branches and staged plant changes. Model a branch as a named pointer to an immutable revision/change-set lineage, not a copy of live equipment identities. Provide three-way comparison against a common ancestor; detect attribute conflicts, relationship/topology conflicts, incompatible schema versions and conflicting effective dates.

Never auto-merge safety-relevant changes (topology, protection settings, interlocks, CT/PT ratios, calibration, device mapping) solely because fields do not overlap syntactically. Require domain validation and designated approval. A merge produces a new revision with parent links and a recorded reconciliation decision. A project branch must not be mistaken for a physical plant operating state.

## 9. Bitemporal and lifecycle semantics

For facts where historical validity matters, store:
- **valid time:** when the fact was true in the engineering/physical/operational world;
- **transaction/recorded time:** when GridForge accepted or learned the fact.

This supports late discovery (e.g. a field replacement happened last week but was entered today), corrections, retroactive commissioning evidence and historical reconstruction. Use explicit unknown/approximate intervals where exact effective time is unavailable. Never fabricate a precise effective timestamp.

Lifecycle status should be typed and context-specific: proposed, designed, approved, procured, installed, commissioned, in-service, out-of-service, under-maintenance, decommissioned, removed, archived. Not every object uses every status; transitions require domain-specific preconditions and audit evidence. Asset lifecycle does not equal electrical network availability, and an engineering object can remain in the model after a physical asset is removed for historical traceability.

## 10. External dictionaries and interoperability mappings

### 10.1 IEC 81346 — structure and reference designation

Use IEC 81346-1:2022 as the general structuring/reference-designation framework and IEC 81346-2 classification as a candidate object-class code source. Keep project RDS profiles configurable and retain the exact standard edition/profile used. The ISO catalogue currently marks IEC 81346-2:2019 as to be revised, so the next edition and transition must be checked before locking code lists.

### 10.2 IEC 61360 / IEC Common Data Dictionary

Use IEC 61360 principles for well-defined classes, properties, data types and coded units; consult IEC CDD for electrotechnical catalogue semantics. IEC 61360-7:2024 introduces cross-domain concepts in an IEC CDD dictionary domain. Dictionary concepts should be mapped to GridForge property definitions, not copied as arbitrary string labels. Store dictionary identifier, version/edition, concept ID, unit/quantity kind, language and mapping status.

### 10.3 IEC 61970 CIM

IEC 61970-301:2020 (with applicable amendment/consolidation) defines a Common Information Model representing major electric-utility objects and relationships to facilitate exchange among independently developed applications. Use CIM as an exchange/interoperability model for network/enterprise integration, not as a mandate to make CIM classes the internal Core class hierarchy. Explicitly map terminals, connectivity nodes, conducting equipment, assets, measurements and operational resources; record lossy mappings and unsupported extensions.

### 10.4 IEC 61850 SCL

IEC 61850-6:2009+AMD1:2018+AMD2:2024 specifies the SCL file format for exchanging IED capability/configuration, communication-system configuration, switchyard functional structures and their relationships between engineering tools. Treat SCL as a versioned import/export boundary. Preserve source file, schema/edition, IED identity, logical-device/logical-node/data-object structure, communication configuration, templates and mapping diagnostics. SCL logical nodes/functions and data objects must map to GridForge canonical Protection/Control/Signal objects through explicit mappings; do not equate an SCL path with a Core object ID.

### 10.5 External mapping registry

For each external identifier mapping, store source system, source namespace, external ID, canonical object ID, mapping type, confidence/status, valid time, source revision, mapping revision and provenance. Support one-to-many/many-to-one only where the external standard's semantics allow it and the mapping is explicit. Conflicts and unmatched records go to a reconciliation queue; never silently create duplicate equipment from an unknown external ID.

## 11. Schema evolution and migration

Every persisted object/configuration/record family has a schema version. Migrations must be:
- explicit, deterministic and versioned;
- validated against source and target schema;
- reversible where feasible or accompanied by a tested backup/restore strategy;
- provenance-preserving, with source digest and migration tool/version;
- staged before active project mutation;
- able to report unsupported fields/extensions without silently dropping them.

Unknown fields and plugin-defined records should be preserved where possible for forward compatibility. A plugin absence must not destroy stored plugin data. Breaking changes require an explicit migration plan and compatibility statement. Do not use import-time mutation or implicit schema upgrade.

Project package migration remains compatible with the frozen V2 .gridforge contract: manifest.json carries package/schema/version metadata and canonical project.json remains the authoritative project content. V3 may propose versioned schemas and migration tools, but must not add an implicit external runtime dependency or mutate V2 package semantics.

## 12. Governance roles, approvals and provenance

Define scoped capabilities, not one generic editor role:
- project owner / data steward;
- electrical design engineer;
- Protection engineer;
- Control/automation engineer;
- instrumentation/measurement engineer;
- asset-data steward;
- commissioning authority;
- operations authority;
- reviewer/approver;
- integration/service identity;
- plugin maintainer/administrator;
- read-only auditor.

Separate authorship, review and approval for changes according to risk. High-consequence changes (topology, Protection settings, interlocks, instrument transformer ratios/polarity, command routing, calibration) require policy-defined independent review/approval and commissioning/effective-time evidence. The exact approval matrix is configurable by organization and project governance; no universal dual-approval claim is made.

Each change record captures actor, authenticated principal, role/capability, source, reason, work order/change request, approvals, before/after, validation, timestamp and effective interval. Automated imports and plugins are identified as service principals, never impersonated as human engineers.

## 13. Cross-domain lineage and impact analysis

Provide a traversable lineage graph across:
physical asset/installed item → engineering equipment → terminals/topology → instrumentation association → signal/channel/calibration → measurement snapshot → Protection/Control evaluation → decision/action intent → authorization/command → device feedback → SOE/alarm/historian/disturbance/audit.

Each edge is typed and revision-qualified. A result must be reproducible from the exact input snapshot, configuration revision vector, schema versions, algorithm/solver version and source provenance. If a dependency is missing, stale, ambiguous or unavailable, the lineage view must say so rather than infer a relationship from matching labels.

Impact analysis should answer:
- Which studies, Protection elements, Control tasks, alarms, signals and read models depend on this changed property?
- Which decisions/results were calculated from the prior revision?
- Which live consumers must be re-evaluated before activation?
- Which external mappings and reports require update?
- Which installed physical items and documents are affected?
- What historical evidence remains valid under its original configuration?
- What changes require operator/commissioning notice?

Do not retroactively mark historical results invalid merely because a newer configuration exists. Mark them as computed under a superseded revision and distinguish historical validity from current applicability.

## 14. UI/UX governance workflows

Provide a unified engineering data inspector with clear separation of:
- identity and aliases;
- classification and reference designation;
- asset/installed-item and manufacturer data;
- engineering properties and units;
- topology/functional/measurement relationships;
- configuration revisions and effective dates;
- source/provenance and quality findings;
- dependency/impact graph;
- review/approval/change-set state;
- external mappings and import conflicts.

Key workflows:
1. Create equipment from a typed schema; allocate immutable ID and proposed designation.
2. Associate a manufacturer product and physical asset/serial without conflating them.
3. Assign or revise RDS aspects with collision checking and history.
4. Import CIM/SCL/catalogue data into a staging area; inspect matches, conflicts and unsupported properties.
5. Compare revisions side-by-side, including relationship changes and dependency impact.
6. Submit change set for domain review/approval; show validation and required commissioning evidence.
7. Activate the approved revision through Application commands and display the exact effective revision.
8. Trace a Protection decision or study result to the exact input/configuration revisions used.
9. Inspect stale consumers and selectively re-evaluate affected dependencies.
10. Retire/replace an asset while preserving historical identity and records.

Use progressive disclosure and domain-specific property editors; do not present hundreds of unfiltered fields in one panel. Show canonical ID, current designation and revision together where useful. Warn clearly when a user edits a display-only property versus a domain-authoritative property. Bulk edits require preview, impact report and explicit commit.

## 15. Proposed V3 logical module boundaries

- `core/identity`: opaque identity value objects and identity invariants; no persistence, Qt or external APIs.
- `core/reference_designation`: RDS concepts and designation values, separate from IDs.
- `core/relationships`: typed relation contracts and cardinality/validity semantics.
- `core/configuration`: immutable configuration revision/change-set contracts and revision domains.
- `core/provenance`: source, actor, valid-time/recorded-time and lineage reference contracts.
- `domains/asset_management`: asset lifecycle, installed-item association, ownership/maintenance context.
- `domains/data_governance`: stewardship, data-quality policy, classification and approval policy.
- `application/change_management`: commands, validation orchestration, review/approval and activation.
- `application/impact_analysis`: dependency traversal and affected-consumer reports; not an authority over domain rules.
- `infrastructure/interoperability`: CIM/SCL/IEC CDD/ERP/CMMS adapters and mapping registry.
- `infrastructure/migrations`: versioned schema migrations and validation reports.
- `plugins/engineering`: one consolidated extension host for type catalogues, adapters and domain-aligned capabilities through public contracts.
- `ui`: inspectors, comparison, staging, review and lineage projections only.

These are logical responsibility boundaries, not a demand for one plugin/service per module or a prescribed physical folder tree. Reuse existing Application services, event infrastructure, signal/measurement contracts and plugin host rather than duplicating managers.

## 16. Candidate acceptance scenarios (not executed)

1. **V3-ID-01:** rename or re-tag an equipment object without changing its immutable ID or historical references.
2. **V3-ID-02:** move an SLD symbol or sheet without changing Core topology, equipment identity or Protection dependency fingerprints.
3. **V3-ID-03:** create a physical replacement with a new installed-item identity while preserving the retired item's records and successor link.
4. **V3-ID-04:** reject duplicate designations within their governed namespace while allowing same display text in explicitly different scopes.
5. **V3-REL-01:** reject invalid terminal/relationship cardinality and preserve relation owner/provenance.
6. **V3-OWN-01:** an external import or plugin cannot mutate Core-owned electrical properties outside Application command/validation paths.
7. **V3-DQ-01:** missing unit, invalid quantity kind, duplicate external ID or unresolved reference is surfaced as a quality finding.
8. **V3-CFG-01:** approved configuration revisions are immutable; correction creates a new revision and supersession link.
9. **V3-CFG-02:** historical Protection decisions retain exact setting, measurement and topology revisions used at evaluation time.
10. **V3-CFG-03:** display-name/layout changes do not invalidate unrelated Protection evaluations.
11. **V3-CFG-04:** CT ratio, polarity, calibration or source mapping change invalidates only dependent measurement/Protection consumers, with fail-closed behavior if safety dependency integrity is uncertain.
12. **V3-CFG-05:** conflicting Protection setting or topology branches require explicit domain reconciliation; no blind auto-merge.
13. **V3-TIME-01:** late-entered replacement/commissioning facts preserve both valid time and recorded time.
14. **V3-INT-01:** CIM/SCL imports preserve original artifacts and report unmapped/ambiguous/unsupported data before acceptance.
15. **V3-INT-02:** external identifiers are scoped by source namespace and do not become canonical primary keys.
16. **V3-MIG-01:** schema migration is explicit, deterministic, versioned and preserves unknown fields/provenance where supported.
17. **V3-LIN-01:** study/Protection/Control result lineage resolves exact input snapshot, configuration revisions, schema and algorithm versions.
18. **V3-GOV-01:** high-consequence changes require configured independent review/approval and retain actor/reason evidence.
19. **V3-PLG-01:** plugin-defined properties/records remain preservable and exportable when the plugin is unavailable.
20. **V3-PRJ-01:** canonical project package reopens without external asset registry, historian, catalogue or CMMS service availability.

These scenarios are proposed acceptance criteria for future specification. They have not been implemented or executed and do not imply current product capability.

## 17. Standards and reference map — candidate only

| Reference | Relevance | Evidence boundary |
|---|---|---|
| IEC 81346-1:2022 | System structuring and unambiguous reference designations across technical disciplines | Designation/structure framework; does not define GridForge immutable IDs |
| IEC 81346-2:2019 | Object classes and letter codes for classification/reference designation | ISO catalogue marks it to be revised; verify successor and BIS adoption |
| IEC 61360-1:2017 | Principles for defining properties, data types and classification hierarchies | Use for dictionary/property semantics; verify current edition/status |
| IEC 61360-7:2024 | Cross-domain concepts in IEC CDD | Dictionary concepts are mappings, not GridForge object identities |
| ISO 8000-100:2016 | Master-data quality, property-level quality and exchange requirements | ISO page says reviewed/confirmed in 2026; does not cover all engineering validation |
| IEC 61970-301:2020 (+ applicable amendments/consolidation) | CIM base model for utility objects and interoperability | Exchange model; verify consolidated publication and current stability/status |
| IEC 61850-6:2009+AMD1:2018+AMD2:2024 CSV | SCL configuration description and exchange for IEDs, communications and substation functional structures | Configuration exchange format; not GridForge internal identity model |
| ISO 55000:2024 | Asset management vocabulary, principles, outcomes and lifecycle framing | Asset-management governance reference, not electrical equipment schema |
| ISO 55001 / ISO 55002 | Asset management system requirements and guidance | Exact editions and organizational applicability require catalogue check |
| ISO 19650 series | Information management across built-asset lifecycle | Relevant where GridForge exchanges project/BIM information; not a substitute for electrical domain model |

The standards map is a candidate research baseline, not a completed BIS catalogue verification, clause-level compliance assessment, certification claim or normative implementation decision. Editions, amendments, corrigenda, status and Indian adoption must be checked against official IEC/ISO/BIS catalogues before V3 requirements are frozen.

## 18. Open decisions and dependencies

- UUID/opaque ID generation policy, offline allocation, collision handling and project import/merge behavior.
- Exact asset vs engineering equipment vs installed item relationship model and continuity rules during replacement.
- Adopted RDS profile, aspect usage, tag scope, numbering/reuse policy and classification code system.
- Attribute-level authority matrix and cross-domain ownership conflict resolution.
- Canonical quantity/unit/type dictionary and version policy; mapping to IEC CDD and existing engineering schemas.
- Configuration revision granularity, approval lifecycle, effective-time semantics and rollback/compensation rules.
- Branching/merge workflow, three-way conflict resolution and domain-specific merge restrictions.
- Bitemporal requirements by fact family and retention of superseded/historical configurations.
- Dependency metadata completeness, invalidation policy and fail-closed behavior for Protection/Control consumers.
- CIM profile/version and supported class/property mapping; SCL version/IED profile support; external system namespace rules.
- Migration compatibility, unknown-field preservation and package schema evolution.
- Stewardship roles, approval matrix, audit retention and evidence integrity.
- Asset registry/CMMS/ERP/BIM integration scope and optionality.
- UI-GATE-02 through UI-GATE-07 remain open; this section does not close any UI gate.
- BIS catalogue verification remains open for the relevant IEC/ISO standards and Indian adoption.

Dependencies: 8I-10 UI/UX gates, 8I-11 typed diagnostics, 8I-12 operational traceability, 8I-21 event model, 8I-22 revision/change control, 8I-25 standards traceability, 8I-27 simulation/replay, 8I-33 signal/measurement, 8I-34 Protection/Control consumers, 8I-35 operational command lifecycle and 8I-36 event/alarm/SOE/historian/disturbance architecture.

## 19. Frozen invariants and scope boundary

- Immutable internal identity is distinct from every human designation, asset tag, reference designation, external ID and representation ID.
- Core owns electrical/domain truth; Application owns controlled mutation; UI and SLD are projections/interactions.
- SLD symbols and coordinates cannot create or mutate electrical topology.
- Asset lifecycle, engineering configuration, live state, observation and derived result are separate planes.
- Approved configuration revisions and historical evidence are immutable and traceable.
- Revision domains and dependency invalidation are granular; global project revision is not a substitute for typed dependencies.
- External imports and plugins cannot bypass Core ownership, Application commands, validation, authorization or audit.
- CIM, SCL, IEC CDD and RDS standards are interoperability/reference models, not automatic replacements for GridForge's canonical model.
- .gridforge remains the self-contained canonical project package; external asset/catalogue/history services cannot be mandatory to reopen it.
- V2 architecture and persistence remain frozen; all proposals here are V3-only and require explicit approval before implementation.

**Scope boundary:** research and architecture specification only. No source code, database, identity service, asset registry, version-control engine, migration, integration adapter, UI, plugin, benchmark, test or CI was implemented or executed. V2 `main` was not modified.
