# GridForge V3 Architecture Research — 8I-36
## Unified engineering event, alarm, SOE, historian and disturbance-record architecture
**Research date:** 2026-11-04  
**Register lineage:** GridForge V3 Research and Change Register, sections 8I-21, 8I-33, 8I-34 and 8I-35  
**Status:** Proposed V3 architecture; research record only; approval required before implementation.

## 1. Objective and boundary

Define a coherent V3 information architecture for recording, correlating, retaining, querying and presenting engineering observations and operational evidence across electrical networks, Protection, Control, automation, simulation and field devices.

The word *event* must not become a universal record type. A threshold crossing, breaker transition, alarm lifecycle change, Protection decision, command dispatch, sampled analogue value, waveform capture and configuration edit have different semantics, rates, timing guarantees, retention requirements and authority. They may be correlated in a common operational view, but must remain distinct typed records and services.

This section composes the shared Signal and Measurement Infrastructure (8I-33), Protection/Control consumer contracts (8I-34), and end-to-end command/feedback lifecycle (8I-35). It does not replace domain ownership, create a common execution engine, or authorize any change to frozen V2 architecture.

## 2. Principal architectural decisions

1. **Typed records, shared correlation.** Alarm, SOE, general event, historian sample, disturbance waveform, audit record, domain evaluation, command lifecycle and reconciliation remain separate record families. A shared correlation envelope and query/read model may link them.
2. **Event occurrence is not alarm state.** An event is a fact that something occurred. An alarm is an abnormal-condition notification with a managed lifecycle and operator response. A condition can generate multiple event records while one alarm instance remains active; an event need not generate an alarm.
3. **SOE is not a historian.** SOE preserves discrete transitions and their source timing/sequence evidence. Historian stores time-series observations and quality. They may share acquisition and time services but require different indexing, compression, retention and ordering semantics.
4. **Disturbance records are immutable evidence packages.** High-rate waveforms and triggered records are stored as bounded binary/time-series artifacts with channel metadata, trigger context, clock quality, integrity and provenance. They are not expanded into ordinary event rows.
5. **Audit is a separate trust boundary.** User actions, settings changes, calibration, mapping, bypass, authorization and administrative changes are append-only audit facts, not ordinary alarms or operator events. Audit integrity and access control must be stronger than convenience telemetry.
6. **Event time is evidence, not display order alone.** Preserve source event time, source clock identity, time quality, source sequence, receive time and processing time. A UI sort order must not imply causality or synchronization that the sources cannot establish.
7. **Domain authority remains separate.** Protection and Control generate their own typed outcomes. The shared event infrastructure records and correlates those outcomes; it does not reinterpret, authorize or modify them.
8. **Operational records do not become project configuration.** The frozen .gridforge package remains a self-contained canonical project snapshot. Unbounded operational history and waveform retention belong to explicit external stores or export packages, with no silent dependency for opening a project.

## 3. Canonical record taxonomy

| Record family | Meaning and lifecycle | Primary owner |
|---|---|---|
| Engineering event | Immutable occurrence/fact: state transition, threshold crossing, communication state change, task completion/failure, topology/configuration event | Producing domain/service |
| Alarm instance | Abnormal condition requiring operator awareness/response; raised, active, acknowledged, returned-to-normal, shelved/suppressed where policy permits, cleared/closed | Alarm Management |
| SOE record | Discrete point/state transition with source timestamp, quality, sequence and point identity | SOE acquisition/ordering |
| Historian sample | Value or vector observation with engineering unit, timestamp, quality, source and lineage | Historian |
| Disturbance record | Triggered high-resolution waveform and associated digital/analogue channels, trigger metadata and file manifest | Disturbance recorder |
| Audit record | Security/administrative/engineering change with actor, action, scope, before/after revision and reason | Audit/security service |
| Domain evaluation record | Immutable Protection/Control evaluation and input snapshot reference | Protection or Control |
| Command lifecycle record | Intent, authorization, command, dispatch, endpoint response, feedback and reconciliation facts | Operational command services |
| Diagnostic record | Structured technical condition about software, adapter, data quality or subsystem health | Diagnostics |

The same physical occurrence may legitimately create several linked records. Example: a breaker auxiliary contact changes state (SOE); the state differs from the expected command outcome (engineering event and reconciliation result); an alarm may be raised if the deviation meets a rationalized alarm definition; the associated analogue samples remain historian data; a triggered fault capture remains a disturbance artifact. No one record should be copied into another family as a substitute for the original.

### 3.1 Common correlation envelope

Every persisted record should have its own stable family-specific identifier and schema version, plus a common envelope where applicable:

- project_id and installation/site identity;
- record_id, record_type, schema_version and producer/service identity;
- source_id, source_point/channel identity and source configuration revision;
- target equipment/device identity where applicable;
- event_time, receive_time, ingest_time and processing_time as separate fields;
- clock_domain_id, time_quality, sequence/counter and timestamp uncertainty where known;
- measurement quality/status where the record carries measured values;
- causation_id, correlation_id, parent_record_ids and related_record_refs;
- origin mode: live, simulation, replay, test, commissioning or imported;
- security classification, retention class and integrity metadata.

Do not require every record to have a command, alarm or domain decision parent. External/local actions, spontaneous events and imported disturbance records may have no known parent. Missing causal links are represented as absent or unknown, never fabricated.

## 4. Alarm Management domain

Alarm Management is a dedicated domain service, not a boolean flag on an event or measurement.

### 4.1 Alarm definition and rationalization

An AlarmDefinition should identify the monitored condition, source/logic, alarm class, priority, operator consequence, required response, deadband/hysteresis, on-delay/off-delay, latching policy, suppression/shelving policy, operating-mode applicability, owner, revision and rationalization evidence.

A configured alarm should have a defensible operator action. Notifications, advisories, prompts, status indications and diagnostic messages must not be inflated into alarms merely to make them visible. Alarm priority is based on consequence/time-to-respond and approved rationalization, not raw signal magnitude or software severity alone.

### 4.2 Alarm instance lifecycle

Separate the condition state from the operator response state. Model at least:
- condition: normal, active, returned-to-normal, invalid/unknown;
- acknowledgement: unacknowledged, acknowledged (with actor and time);
- shelving/suppression: active, reason, owner, scope, expiry and audit trail;
- lifecycle: raised, updated, returned-to-normal, cleared/closed under explicit policy.

Acknowledgement does not clear an active alarm. Return-to-normal does not imply acknowledgement. Shelving does not change the underlying process condition. Alarm reset is not Protection reset, equipment reset, command acknowledgement or SOE acknowledgement. Chattering, fleeting and stale-source behavior require explicit policies and visible diagnostics; the system must not hide bad quality behind a normal alarm state.

### 4.3 Alarm performance and governance

Provide alarm flood analysis, standing alarm counts, priority distribution, rate-of-change, chattering/bad-actor analysis, shelving duration and operator response metrics. Metrics must identify the operating context and denominator; do not rank operators using unqualified acknowledgement time. Alarm definition changes require controlled revision, review, approval and audit. Dynamic alarm limits or suppression require explicit mode/context, bounds, reason, expiry and audit evidence.

IEC 62682:2022 describes alarm-system management for process industries and covers alarms presented through control systems/HMIs, including alarm/event logs, alarm historians and performance metrics. Its scope is a strong reference for process-plant alarm management, but it does not by itself define power-system SOE, Protection relay logic or GridForge's entire event model. ISA-18.2 material is a related reference family; exact edition and applicability require catalogue verification.

## 5. Sequence of Events (SOE)

SOE is a specialized discrete-event record stream for reconstructing state transitions in engineering time. It must retain source-originated evidence rather than only the server's arrival order.

Each SOE record should include point identity, old/new state where meaningful, source event timestamp, receive timestamp, source clock identity/quality, source sequence number, data quality, producer/IED identity, mapping revision and optional causation references. Preserve raw source timestamp/quality fields alongside normalized UTC representation. Never discard original time zone/offset or time-quality flags during normalization.

### 5.1 Ordering contract

A single globally correct order cannot be guaranteed merely by sorting timestamps from unsynchronized devices. The ordering service should expose:
- source sequence order within a source's documented sequence domain;
- source timestamp order with declared time quality and uncertainty;
- receive order at the ingestion boundary;
- deterministic tie-breaking for equal timestamps;
- explicit unordered/ambiguous relations when uncertainty intervals overlap or clock quality is inadequate.

A displayed sequence may use a deterministic composite key, but it must label the ordering basis and surface clock-quality warnings. Sequence gaps, duplicate counters, clock steps, loss of synchronization, wraparound and device restart are first-class diagnostics.

### 5.2 SOE source classes

Support event sources such as IED reports, digital input acquisition, breaker/isolator auxiliary contacts, Protection indications, Control state transitions, PLC/RTU points and imported records. Protocol adapter semantics must remain visible: report timestamp, server timestamp, event buffer, sequence counter and quality fields are not interchangeable. A polled value change may have an observation time interval rather than a precise occurrence time; do not fabricate a precise source event timestamp.

## 6. Historian and measurement archive

Historian stores time-series measurements from the shared signal/measurement infrastructure. A sample is not an event merely because it has a timestamp.

A historian sample contract should include:
- signal/measurement identity and channel/source identity;
- engineering value, canonical unit and optional raw value;
- event/sample time, receive/ingest time and clock/time quality;
- measurement quality, validity, substitution/estimated status and processing provenance;
- calibration, scaling, mapping and configuration revisions;
- acquisition mode/rate, aggregation interval and compression/deadband metadata;
- origin mode and retention class.

Preserve the distinction between raw acquired samples, processed/derived values and aggregates. Aggregates must record method, interval, source population, missing-data treatment and quality summary. Do not silently interpolate missing samples or treat substituted/estimated values as measured values. Any resampling must be an explicit derived series with lineage.

Historian query capabilities should support time range, signal/equipment, quality, source, event markers and aggregation. Provide trend overlays with event/alarm/SOE markers while retaining the underlying data distinctions. High-rate waveform data should not be forced through a low-rate historian path.

## 7. Disturbance recording and waveform evidence

Disturbance records are triggered capture packages, not just a list of samples. A record manifest should reference:
- capture_id, recorder/IED identity and firmware/configuration revision;
- trigger source, trigger time, trigger reason and pre-/post-trigger window;
- channel definitions, phase/sequence labels, units, scaling and sample rates;
- analogue and digital channel sample data, sample count and time-base segments;
- timestamp source, clock quality and synchronization state;
- file format, format version, encoding, byte size and cryptographic digest;
- source device, export/import history and integrity verification result;
- related Protection decisions, SOE records, alarms and fault/operation context where known.

Support native recorder formats and standardized interchange. IEC 60255-24:2013 / IEEE/IEC C37.111-2013 COMTRADE is a relevant transient waveform/event-data exchange format. It defines file interchange, not a real-time network streaming transport. The IEEE SA page currently marks the 2013 publication inactive-reserved and lists a successor project (PC37.111) as an active PAR; therefore the exact current edition/status must be rechecked before claiming conformance or freezing parser behavior. Keep an extensible format adapter boundary and preserve original files byte-for-byte.

Provide waveform viewer, channel selection, time alignment, phasor/sequence views where engineering-valid, cursor measurements, trigger/event overlay and export. Any derived calculation must identify algorithm/version, source channels, sample quality and time alignment assumptions. Imported COMTRADE must be validated for channel count, sample-rate segments, scaling, timestamp, file integrity and unsupported features before being admitted as trusted evidence.

## 8. Time service and clock-quality architecture

A shared time service should expose clock sources, synchronization state, holdover, offset/uncertainty estimates, last synchronization, time-quality flags and source hierarchy. It must not overwrite source timestamps or convert an unsynchronized time into a false high-confidence UTC timestamp.

Candidate mechanisms include PTP profiles for power utility automation (IEC/IEEE 61850-9-3), IEEE 1588, NTP, GNSS, IRIG-B and device/protocol-specific time services. These are not equivalent in accuracy, failure modes or deployment assumptions. The PTP profile standard defines a profile; actual end-to-end accuracy depends on grandmaster, boundary/transparent clocks, network asymmetry, device implementation, configuration, holdover and monitoring. A profile name alone is not a measured performance result.

Clock quality should be an explicit typed value such as synchronized-within-declared-bound, holdover-with-known-uncertainty, unsynchronized, time-source-lost, invalid/unknown. The numeric uncertainty and evidence basis should accompany quality where available. Clock transitions and time corrections should be recorded as events; do not silently rewrite historical event times when a clock is corrected.

## 9. Persistence, storage and recovery

Separate storage by workload and integrity needs while presenting a unified query/read model:
- append-oriented event/SOE store for discrete records and ordering metadata;
- alarm state store plus immutable alarm lifecycle history;
- time-series historian store for sampled values and aggregates;
- object/blob store for disturbance waveforms and large artifacts;
- append-only audit store with stricter access and tamper-evidence;
- metadata/catalogue store for signal definitions, record schemas, source mappings and retention policies.

This is a logical separation, not a mandate for six databases or six deployable services. V3 should begin with modular boundaries and explicit repository interfaces; physical deployment can consolidate stores when scale and integrity constraints permit. Do not prematurely introduce distributed infrastructure solely because record families differ.

Every store needs schema evolution, idempotent ingestion, duplicate detection, gap detection, bounded backpressure, retry/dead-letter policy, retention, export and recovery semantics. If storage is degraded, acquisition must report data loss/backlog and quality consequences. Never silently discard records or mark unpersisted evidence as durable. Define durability acknowledgement at the ingestion boundary and preserve the original source sequence for replay/recovery.

Retention is policy-driven by record family, legal/contractual requirements, engineering need and storage capacity. Retention expiry, legal hold, export, deletion and archival must be auditable. A deletion policy for ordinary telemetry must not silently erase audit evidence or referenced disturbance artifacts. Referential integrity across stores requires stable IDs, manifests and verifiable export bundles.

The frozen .gridforge ZIP remains a self-contained canonical project package with manifest and project.json. It may store project definitions, signal/alarm configurations and explicitly selected project-scope records, but not an unbounded live historian or waveform archive. External operational stores must be optional for project reopen; imported records should be portable through explicit evidence bundles with manifests and checksums.

## 10. Ingestion, processing and query pipeline

Recommended logical path:

Source/IED/PLC/RTU/Simulation → protocol or acquisition adapter → validated typed input → time/quality normalization (without destroying raw fields) → record-family router → durable ingestion boundary → family-specific store → correlation/index service → read models and UI.

Processing rules:
- validate identity, schema, units, source mapping revision and payload bounds;
- preserve original payload or a verifiable raw representation where required;
- distinguish source event time from ingest time;
- deduplicate only within a declared source/sequence/idempotency scope;
- detect gaps and out-of-order arrivals without discarding late data;
- route one occurrence to multiple record families only through explicit domain rules;
- keep alarm evaluation separate from raw event persistence;
- make derived events and analytics reproducible with rule/model revision and input references;
- never allow a read-model failure to mutate or suppress canonical records.

Query services should provide a unified operator timeline as a projection over typed records, not a universal mutable event table. Queries must filter by project, site, equipment, time interval, record family, quality, origin mode, alarm priority/state, source and correlation. Pagination and export must use stable cursors/snapshots to avoid omissions during active ingestion.

## 11. UI/UX and engineering workflows

The operational workspace should provide distinct views over a common context:
- **Alarm summary/list:** priority, active/unacknowledged state, source, response guidance, acknowledgement and shelving controls governed by authorization.
- **SOE viewer:** high-resolution discrete sequence, source time/quality, sequence gaps, clock warnings and filterable point list.
- **Historian trends:** value, unit, quality, source and derived/raw distinction; overlay alarms/events/SOE without conflating them.
- **Disturbance viewer:** capture metadata, channel tree, waveform plots, trigger markers and export/validation status.
- **Audit viewer:** actor, change, scope, reason, before/after revision and integrity status with restricted access.
- **Causal operation trace:** link measurement snapshot → Protection/Control evaluation → intent → authorization → command/dispatch → acknowledgement → feedback → reconciliation → event/SOE/alarm references.

A unified timeline may group and visually differentiate record types, but must not reduce their independent lifecycle actions to one generic “acknowledge” or “clear” command. Alarm acknowledgement applies only to the selected alarm instance. SOE records are immutable. Historian samples are not acknowledged. Disturbance evidence is annotated or dispositioned through a separate audit-aware workflow. Audit entries cannot be edited from the operational timeline.

UI performance should use virtualized/paged lists, server-side filtering, indexed time windows, progressive waveform loading and explicit limits for high-volume data. Large query windows should be cancellable and show query scope, partial-result state and ingestion lag. No UI action should block Protection/Control execution or device acquisition.

## 12. Security, data integrity and plugin boundaries

- Apply role/capability checks to alarm acknowledgement, shelving, configuration changes, exports, audit access and retention administration.
- Keep audit writes append-only; use tamper-evident chaining/signatures or equivalent controls appropriate to the threat model, with key custody and verification procedures.
- Encrypt data in transit and at rest according to deployment policy; protect device identity, certificates, credentials and exported evidence.
- Treat imported files, protocol payloads, timestamps, metadata and plugin-produced records as untrusted input.
- Plugins may register typed producers, decoders, alarm rules, historian adapters, waveform decoders and read-model contributions through public contracts. They must not directly write another domain's store, mutate Core, bypass audit, or invent source timestamps/quality.
- A plugin must declare record types, schema versions, capabilities, permissions, storage/retention needs and migration strategy. Unknown plugin records must remain safely preservable/exportable even if the plugin is absent.
- Simulation/replay records must carry explicit provenance and must never be mistaken for live operational evidence or dispatched to physical endpoints.

## 13. Standards and reference map — candidate only

| Reference | Relevance | Evidence boundary |
|---|---|---|
| IEC 62682:2022 | Alarm-system management for process industries, including HMI alarm presentation, alarm/event log, alarm historian and performance metrics | Strong alarm-management reference; not a universal SOE or electrical protection model |
| ANSI/ISA-18.2 family | Alarm lifecycle, rationalization and management practices | Edition/technical-report applicability must be checked; do not assume all ISA documents are normative |
| IEC 61850-7-4:2010+A1:2020 | IED logical-node/data-object information models, including monitoring and historical/statistical extensions | Use as interoperability mapping reference, not as GridForge's internal domain model |
| IEC 61850-8-1:2011+AMD1:2020 | Mapping ACSI to MMS/Ethernet for real-time and non-real-time exchange, indications, control and reporting | Verify exact consolidated edition and device profile before adapter implementation |
| IEC/IEEE 61850-9-3:2016; active successor project P61850-9-3 | PTP profile for power utility automation | Profile does not prove deployed end-to-end clock accuracy; recheck successor status |
| IEC 61850-5:2013+AMD1:2022 | Communication requirements for power utility automation functions and device models | Use for applicable functional communication requirements, not as a blanket time-accuracy claim |
| IEC 60255-24:2013 / IEEE/IEC C37.111-2013 COMTRADE | Transient waveform and event data file exchange | File format, not network streaming; 2013 publication status/successor must be verified |
| IEEE PC37.111 | Successor COMTRADE revision activity | Active PAR is a project, not a published standard; do not implement draft content as normative |
| IEEE 1588 / relevant PTP profiles | Clock synchronization foundations | Profile and network/device engineering determine actual performance |
| IEC 62351 series | Cybersecurity for power-system information exchange | Map relevant parts to each protocol, role and deployment threat model |

The IEC catalogue identifies IEC 62682:2022 as Edition 2.0 and describes the alarm management scope. IEC's consolidated IEC 61850-7-4:2010+A1:2020 publication describes logical-node/data-object models and monitoring/historical-statistical extensions. IEEE SA describes COMTRADE as transient waveform/event file exchange and explicitly says it is not a network transfer protocol; its page lists the 2013 standard as inactive-reserved and PC37.111 as an active project. IEEE SA describes IEC/IEEE 61850-9-3:2016 as a PTP profile for power utility automation and lists an active revision project. These are research observations as of this entry, not a completed BIS catalogue verification or certification assessment.

## 14. Proposed V3 module boundaries

Keep implementation modular and consolidated by domain responsibility; do not create one plugin per record type.

- `core/events`: immutable domain event contracts and identity/correlation primitives only; no Qt, transport, database or plugin-host dependencies.
- `application/operations`: orchestration of event persistence, alarm lifecycle commands, SOE ingestion, historian queries and evidence export through explicit ports.
- `infrastructure/ingestion`: durable adapters, validation, deduplication, buffering and source protocol translation.
- `domains/alarm_management`: alarm definitions, rationalization metadata, lifecycle rules and authorization-facing commands.
- `domains/soe`: discrete event source semantics, sequence tracking, ordering and gap/clock diagnostics.
- `domains/historian`: sample persistence, quality-aware query and aggregation/lineage.
- `domains/disturbance`: waveform manifests, COMTRADE/native format adapters, validation and analysis read models.
- `domains/audit`: append-only security/engineering audit contract and verification.
- `application/correlation`: cross-domain causal links and unified read models; it must not become a new authority over source domains.
- `plugins/engineering`: one consolidated extension host for domain-aligned providers/adapters/decoders through public contracts; plugin code cannot bypass Application services or write Core directly.
- `ui`: views and interactions only; no domain record creation or persistence outside Controller → Command → Application.

The above are logical boundaries, not a prescribed physical folder tree or microservice topology. Before implementation, map them against the existing V3 register and avoid duplicating the shared signal infrastructure or 8I-35 operational trace services.

## 15. Candidate acceptance scenarios (not executed)

1. **V3-EVT-01:** one physical transition can create linked SOE, general event, reconciliation and optional alarm records without collapsing their identities.
2. **V3-EVT-02:** an alarm acknowledgement does not clear an active alarm or mutate SOE/Protection/command state.
3. **V3-EVT-03:** return-to-normal does not imply acknowledgement; shelving does not alter the underlying condition.
4. **V3-EVT-04:** alarm definitions require rationalized consequence, priority and operator response before operational activation.
5. **V3-SOE-01:** source timestamp, receive time, time quality and sequence are retained independently.
6. **V3-SOE-02:** unsynchronized clocks and overlapping uncertainty intervals do not produce a false globally precise order.
7. **V3-SOE-03:** sequence gaps, duplicate counters, clock steps and device restarts are diagnosed without deleting raw evidence.
8. **V3-HIS-01:** raw, processed and aggregated values remain distinguishable with units, quality and derivation lineage.
9. **V3-HIS-02:** missing or substituted samples are not silently interpolated or presented as measured values.
10. **V3-DST-01:** a COMTRADE import preserves original bytes, validates channel/time/scaling metadata and records format/version provenance.
11. **V3-DST-02:** a waveform viewer does not claim precision beyond source clock and sample-rate evidence.
12. **V3-AUD-01:** configuration, calibration, bypass and alarm-definition changes create append-only actor/reason/before-after audit evidence.
13. **V3-ING-01:** ingestion backlog or storage failure is visible; durability is not claimed before the configured durable boundary.
14. **V3-ING-02:** duplicate/out-of-order arrivals are handled by declared source sequence/idempotency scope and late data remains queryable.
15. **V3-COR-01:** unified timeline correlates records but retains family-specific actions and permissions.
16. **V3-PLG-01:** plugin absence does not make unknown stored records unreadable or destroy original evidence.
17. **V3-PRJ-01:** a project reopens from the canonical .gridforge package without requiring an operational historian or waveform store.
18. **V3-MODE-01:** simulation/replay evidence is visibly segregated from live evidence and cannot create physical outputs.
19. **V3-SEC-01:** unauthorized users cannot acknowledge/shelve alarms, alter definitions, export restricted evidence or change retention.
20. **V3-TRACE-01:** an engineer can traverse from a Protection/Control outcome to command, physical feedback, SOE, alarm, historian samples and disturbance evidence where those links actually exist.

These scenarios are proposed acceptance criteria for future specification. They have not been implemented or executed and do not imply current product capability.

## 16. Open decisions and dependencies

- Alarm priority model, rationalization workflow, shelving policy, alarm flood handling and role separation across electrical and process domains.
- SOE source capability matrix: source timestamp support, sequence counters, event buffering, quality flags, clock domain and maximum credible ordering precision per device/protocol.
- Required time-quality vocabulary and uncertainty propagation rules across IEC 61850, RTU/PLC and simulation sources.
- Historian sample rates, raw-data retention, compression, deadband, aggregation, missing-data and derived-series policies.
- Disturbance file formats, parser compatibility matrix, large-file storage, channel mapping and import trust policy.
- Storage durability boundaries, outage buffering, recovery objectives, data-loss declarations, retention/legal hold and evidence export format.
- Audit tamper-evidence, key management, access control and export signing.
- Cross-store correlation/index strategy without making the correlation service authoritative.
- Deployment sizing and whether logical stores should share one database or be physically separated.
- Exact current IEC/IEEE/ISA editions, BIS adoption status, Indian applicability and clause-level mapping.
- Integration with 8I-11 diagnostics, 8I-12 traceability, 8I-21 event model, 8I-22 revision control, 8I-25 standards traceability, 8I-27 simulation, 8I-33 signal/measurement and 8I-35 operational lifecycle.
- UI-GATE-02 through UI-GATE-07 remain open; this section does not close any UI gate.

## 17. Frozen invariants and scope boundary

- Event, alarm, SOE, historian, disturbance, audit, diagnostic and command-lifecycle records remain distinct typed facts with explicit correlation.
- Alarm acknowledgement, return-to-normal, shelving, Protection reset, command acknowledgement and physical feedback remain separate semantics.
- Source time, receive time, ingest time, processing time, clock quality and sequence are preserved independently.
- No global event ordering or timestamp accuracy is claimed beyond source and network evidence.
- Disturbance records preserve original artifacts and provenance; COMTRADE is treated as file interchange, not live transport.
- Protection and Control retain separate decision authority; shared recording/correlation cannot authorize or mutate their outcomes.
- Project package remains self-contained and does not require an external operational historian to reopen.
- Plugins extend through public contracts and Application services; no plugin writes Core directly or bypasses audit/security boundaries.
- V2 architecture and persistence remain frozen; all proposals here are V3-only and require explicit approval before implementation.

**Scope boundary:** research and architecture specification only. No source code, runtime service, database, event bus, alarm engine, historian, SOE engine, waveform parser, UI, plugin, benchmark, test or CI was implemented or executed. V2 `main` was not modified.
