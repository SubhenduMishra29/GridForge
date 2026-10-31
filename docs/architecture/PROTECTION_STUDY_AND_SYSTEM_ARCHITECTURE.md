# GridForge V2 — Protection System and Unified Protection Study Architecture

**Date:** 2026-10-30  
**Repository authority:** `SubhenduMishra29/GridForge`, branch `main` baseline  
**Author:** Subhendu Mishra  
**Status:** Architecture baseline for phased implementation; not a production-readiness declaration.

## 1. Purpose and architectural decision

Protection System Engineering is a complete engineering discipline. It is not synonymous with relay execution, CT association, or a collection of ANSI-numbered algorithms. GridForge shall provide one unified **Protection Study** workflow that configures, validates, calculates, coordinates, evaluates, records, and reports the protection system for a project/network snapshot.

The Protection Study is the engineering workflow and result lifecycle. The Protection System is the configured protection arrangement being studied and evaluated. They are related but are not interchangeable domain objects.

Protection remains a distinct subsystem with explicit interfaces to:
- the electrical model and committed network topology;
- physical instrument transformers and measurement infrastructure;
- physical relays and executable protection functions;
- switching equipment and breaker operation;
- short-circuit and other electrical study results;
- control/interlocking and, later, digital-substation communication;
- project persistence, revision provenance, events, and UI projections.

The architecture must reuse existing GridForge V2 contracts. It must not create a parallel study lifecycle, topology model, measurement channel, relay model, breaker state, command bus, event bus, or result authority.

## 2. Frozen cross-layer boundary

The universal mutation and publication path remains:

`UI / SLD → Controller → immutable Command → Application.execute()
→ CommandManager / Transaction → Core → semantic Event
→ Application Read Model / Projection → UI`

**Core owns authoritative engineering truth:** physical electrical equipment, terminal contracts, topology, measurement semantics, protection-function contracts and calculations, validation, and immutable engineering results.

**Application owns workflow and controlled mutation:** Protection Study lifecycle, project-scoped configuration, commands, transactions, orchestration, study provenance, event publication, persistence coordination, and read-model assembly.

**UI/SLD owns authoring interaction and projection:** equipment placement, explicit terminal selection, relay/function configuration, curve/coordination visualization, diagnostics, and result presentation. It does not infer electrical connectivity, protection coverage, or trip targets from graphics.

Core must remain headless and must not import Qt, QGraphics, SLD, plugin, or UI types. The existing frozen `core/model/` and `core/network/` contracts are preserved; changes there require a separately demonstrated foundational gap and must not be used to bypass the established architecture.

## 3. Domain vocabulary and ownership

| Concept | Meaning and owner |
|---|---|
| Physical instrument | CT/PT/CVT model and its primary/secondary terminal contracts; `core.model` |
| Network connectivity | Committed terminal-to-terminal connectivity and derived topology; `core.network` |
| Measurement channel | Authoritative logical signal, units, quality, freshness, availability and source reference; `core.measurement` |
| Relay | Physical protection device; `core.model.relay` |
| Relay input | Named protection-facing binding to a MeasurementChannel; `core.protection.relay_input` |
| RelayBase | Executable protection-function contract and numerical function implementation |
| Protection element | One configured function instance hosted by a physical relay; `core.protection.protection_element` |
| Protection decision | Immutable function evaluation outcome; `core.protection.decision` |
| Protection system | Atomic orchestration/collection of ProtectionElement evaluations; `core.protection.protection_system` |
| Protection scheme | Explicit logic and relationships that combine function outputs, interlocks, permissives, blocking, transfer-trip and targets |
| Action mapping | Explicit mapping from a protection output/decision to an authorised target and action; Application configuration/execution |
| Breaker operation | Controlled switching operation through existing BreakerManager/Application command boundary |
| Protection Study | One Application-owned engineering workflow, configuration snapshot, execution lifecycle and result provenance |

A physical relay can host multiple independent ProtectionElements. One ProtectionElement represents one function instance; it does not own the physical CTs, measurement state, network topology, breaker operation, or a universal protection zone.

## 4. Two independent signal paths

### 4.1 Measurement and energising path

`Primary network quantity
→ CT/PT/CVT primary terminals
→ instrument secondary circuit / configured secondary terminal
→ MeasurementChannel
→ RelayInput
→ ProtectionElement / RelayBase`

Measurement channels carry measured electrical quantities and their quality/freshness semantics. CT/PT/CVT ratio and instrument conversion remain in the measurement subsystem. Protection functions consume engineering values through RelayInput and do not repeat instrument conversion.

The configured association must preserve separate identities for:
- the primary electrical source and terminal used to select the study result quantity;
- the physical instrument and the relevant primary terminal relationship;
- the physical secondary terminal/circuit;
- the logical MeasurementChannel;
- the named RelayInput;
- the ProtectionElement input contract.

Reuse `ProtectionMeasurementBinding` as the correlation contract where its fields are sufficient. Do not create a second binding type with overlapping authority.

CT P1/P2 are primary-side orientation/location references. CT S1/S2 are secondary-circuit references. They are not interchangeable. PT and CVT roles must be read from their actual Core model contracts; no guessed role aliases are allowed. A CT does not select a feeder, protection zone, relay, or breaker merely by being placed on the SLD.

### 4.2 Protection output and control path

`ProtectionDecision
→ Protection Scheme / output logic
→ explicit output-to-action mapping
→ Application command
→ BreakerManager / switching service
→ authoritative breaker state
→ feedback / postcondition observation`

Trip, alarm, start, block, intertrip, close, breaker-failure and other binary/control outputs are not MeasurementChannels. A trip request is not proof of breaker operation. The action boundary must preserve command acceptance, observed Core state, physical acknowledgement and postcondition verification as separate evidence.

No ProtectionElement may mutate a breaker directly. No breaker may consume CT measurement data as if it were a trip command.

## 5. Protection coverage and zones

Do not introduce a universal element-owned `ProtectionZone` abstraction.

Protection coverage is an engineering interpretation assembled from function-specific configuration, instrument locations, network topology, protected equipment, switching arrangement, and explicit output/action relationships.

- **Differential (87):** the selected CT measurement boundaries define the differential measurement region. The function consumes the configured set of boundary currents and applies its own compensation, restraint, bias, inrush/overexcitation blocking and operating criteria as applicable. Two-terminal and multi-terminal arrangements must be representable. Bus, line, transformer, generator and motor differential applications are not assumed to be identical.
- **Overcurrent (50/51):** coverage and selectivity depend on current measurement association, direction/phase or residual quantity, network fault levels, relay settings, upstream/downstream relationships, and explicit trip target(s). The breaker target alone does not define the complete zone.
- **Earth-fault (50N/51N/67N/64/REF):** the input contract must distinguish residual current derived from phase channels, neutral CT current, core-balance CT current, and voltage polarising/reference inputs. These are not interchangeable without an explicit configuration/derivation.
- **Directional (67):** current and polarising voltage associations, phase sequence, angle convention, forward/reverse characteristic and directional supervision are explicit.
- **Distance (21):** voltage/current input associations, impedance reach, zones, line parameters, load encroachment, power-swing/blocking and trip logic are function-specific.
- **Transformer protection:** differential, restricted earth fault, overcurrent, thermal, overfluxing, pressure/gas and temperature functions have different sensors, models, operating criteria and actions.
- **Busbar protection:** bus arrangement, CT locations, disconnector/breaker status, check zone, zone selection and breaker-failure interaction must be represented explicitly.
- **Breaker failure (50BF):** initiation, current/position supervision, retrip, backup trip targets and timing form a distinct protection scheme function; it is not merely another trip target on the initiating element.

The architecture may expose derived coverage/read models, but their provenance and function-specific rules must be explicit. SLD geometry is never used as a substitute for electrical terminal connectivity.

## 6. Unified Protection Study workflow

One Protection Study workflow owns the complete engineering lifecycle:

1. **Study definition** — project, study identity, standard/profile, frequency, nominal voltage/base assumptions, scenario and scope.
2. **Network snapshot** — committed model/topology snapshot and revision provenance; unresolved draft topology is not silently treated as committed network truth.
3. **Protection inventory** — physical relays, CT/PT/CVTs, breakers, trip circuits, communication interfaces and protected equipment in scope.
4. **Instrument configuration** — CT core, ratio, rated secondary, polarity, accuracy/protection class, burden/saturation data where modelled, primary terminal association, secondary terminal/circuit, PT/CVT ratios and voltage references.
5. **Measurement binding** — provision or reuse MeasurementChannels; bind named RelayInputs; validate quantity, phase/sequence, units, polarity, ratio, quality/freshness policy and source provenance.
6. **Relay/function configuration** — physical Relay → one or more ProtectionElements → RelayBase function code, settings, input contract, enable/block state and execution priority.
7. **Protection scheme configuration** — explicit start/operate/trip/alarm/block/permissive/intertrip relationships; output mapping to one or more designated action targets; breaker-failure and backup relationships.
8. **Study input preparation** — prepare short-circuit/fault scenarios and required operating points from the same compatible project/network snapshot. Record assumptions and unavailable input data.
9. **Function calculation** — evaluate each configured function using immutable ProtectionContext and authoritative MeasurementChannel/RelayInput inputs.
10. **Protection performance assessment** — sensitivity, pickup, operating time, reach, stability/security, dependability, selectivity, backup, breaker duty and instrument adequacy as applicable to the function and available data.
11. **Coordination** — primary/backup pairs, fault-current scenarios, operating-time margins, breaker/fuse/cable/transformer damage constraints, curve families and tolerances.
12. **Results and diagnostics** — typed results, input/configuration fingerprints, revision provenance, warnings, errors, unsupported features and traceability to source equipment/terminal/channel/relay/element/action target.
13. **Review and reporting** — SLD overlay, relay settings schedule, instrument schedule, protection matrix, trip matrix, fault-by-fault results and log-log TCC charts.
14. **Re-run/invalidation** — model, topology, instrument, channel, relay setting, scheme, breaker, standard-profile or scenario changes invalidate the affected result scope. Stale results are rejected or clearly marked, never presented as current.

The Study is a design/analysis workflow; it does not imply that a simulated protection decision is permission to operate live plant equipment.

## 7. Engineering function catalogue and calculation layers

Protection algorithms must be classified by actual implementation status. A catalogue entry, ANSI number, placeholder class, or UI editor is not evidence of a complete engineering function.

### 7.1 Overcurrent and earth-fault
- 50 instantaneous phase overcurrent.
- 51 time overcurrent: definite time and supported inverse families (IEC standard/normal inverse, very inverse, extremely inverse, long-time inverse; IEEE families only when their equations and reset behaviour are implemented).
- 50N/51N earth/residual overcurrent with explicit residual/neutral measurement semantics.
- 67/67N directional overcurrent with explicit polarising quantity and direction convention.
- 46 negative-sequence current and 49 thermal overload where their inputs and thermal model are supported.

For inverse-time functions, separate curve mathematics from stateful relay timing. A static TCC equation, a stateful integrating relay model, reset memory, definite-time behaviour, tolerances and manufacturer-specific curves are distinct concerns. IEC and IEEE curves must not be conflated or silently substituted. IEEE C37.112 includes an integral equation for varying current and reset characteristics; a simple constant-current closed-form curve is not a complete dynamic relay model.

### 7.2 Voltage, frequency and directional functions
Implement only against explicit phase/sequence, RMS/phasor, polarising, frequency estimation, time-window and quality contracts. Include 27/59, 81U/81O, 25 synchronism check and directional elements as independent function contracts with supervision and output semantics.

### 7.3 Differential functions
Provide function-specific models for 87T/87M/87G/87N and later bus/line differential. Requirements include CT ratio/phase compensation, vector group and winding connections where relevant, operate and restraint quantities, percentage bias/slopes, unrestrained high-set, inrush/overexcitation restraint or blocking, CT saturation/security supervision, zero-sequence treatment and multi-terminal input validation. Do not claim generic 87 is complete because one differential equation exists.

### 7.4 Distance, bus, transformer and breaker-failure
These are separate engineering work packages with their own input contracts, models, settings, performance criteria and output logic. Do not flatten them into a universal RelayBase settings dictionary with unvalidated arbitrary keys.

### 7.5 Curve mathematics and coordination
Pure numerical primitives belong in the existing protection numerical layer. They must be deterministic and independent of Relay, MeasurementChannel, ProtectionSystem, UI and plotting libraries. The TCC workspace consumes immutable curve/read-model data and is a projection.

The coordination engine must model:
- relay curve family, pickup, time multiplier/dial, definite-time and instantaneous stages;
- primary and backup devices and their sequence;
- fault current at relevant locations and operating scenarios;
- CT ratio and relay secondary/primary current conversion;
- breaker opening/clearing time and interrupting limits;
- fuse minimum-melt/total-clearing curves and equipment thermal/damage curves where supplied;
- grading margin, relay overshoot/reset, tolerances and uncertainty;
- min/max fault current and topology/source operating cases;
- coordination violations with exact fault-current point and time margin.

A curve overlay alone is visualization, not proof of coordination. A coordination result must state its assumptions, current basis, device data, margin definition and violated constraints.

## 8. Result and provenance contracts

Every Protection Study result must be immutable and attributable to:
- project identity and activation generation;
- model/topology revision and topology snapshot identity;
- Protection Study configuration revision/fingerprint;
- protection function catalogue/algorithm version;
- relay and element identities/settings;
- instrument and channel identities/configuration;
- source study/fault scenario identity and operating point;
- output/action mapping and breaker data;
- standard/profile and curve-family selection;
- warnings, unsupported inputs, diagnostics and calculation status.

Distinguish at least: not configured, invalid configuration, blocked, unavailable input, stale input, not picked up, picked up/timing, operated, trip requested, command accepted, breaker state observed, physical acknowledgement unavailable, postcondition matched/mismatched/unavailable. Never compress these into one boolean called `tripped`.

## 9. Standards and engineering reference layer

The implementation shall use standards as traceable engineering requirements, not reproduce copyrighted standard text. Exact standard editions and applicability must be configurable and reviewed by the project engineer.

Initial reference matrix:
- IEC 60255-1:2022 — common requirements for measuring relays/protection equipment and distributed protection schemes.
- IEC 60255-151:2009 — over/under-current functional requirements, measurement and time characteristics.
- IEC 60255-121:2014 — distance protection function requirements and performance evaluation.
- IEC 60255-187-1:2021 plus corrigendum — restrained/unrestrained motor, generator and transformer differential protection.
- IEC 61869-1:2023 and relevant instrument-specific parts — instrument transformer general and specific characteristics.
- IEC 61850 series, including 7-4 and digital interface requirements — logical-node information models and digital inputs/outputs, sampled values, GOOSE, time synchronisation.
- IEC 62271-100:2021+AMD1:2024 — applicable AC circuit-breaker equipment requirements.
- IEEE C37.112-2018 — inverse-time overcurrent equations, varying-current integration and reset behaviour.
- Relevant IEEE C37 application guides for line, bus, transformer, CT and breaker-failure protection.

Standards editions must be checked for amendments/corrigenda before a release claims conformance. A software calculation is not a certification or type test.

## 10. Package boundaries and implementation sequence

Reuse the current modules and public contracts:
- `core/model/`: physical Relay, CT/PT/CVT, breaker and equipment.
- `core/network/`: canonical terminal connectivity and topology.
- `core/measurement/`: channel, quality, provisioning and instrument conversion.
- `core/protection/`: RelayBase, RelayInput, ProtectionElement, ProtectionSystem, decisions, preparation, numerical functions and coordination primitives.
- `core/application/study.py` and study preparation/lifecycle: one Study lifecycle and immutable provenance.
- `core/application/services/protection_configuration_service.py`, protection configuration handlers, protection execution and protection output service: project-scoped configuration and controlled action integration.
- `core/application/commands/`: immutable commands and existing command/transaction path.
- `ui/editors/protection/`, `ui/protection/`, study editor and study projections: authoring and read-only result projection.

Implementation phases, in dependency order:

**Phase A — Contract audit and architecture freeze**
1. Audit current ProtectionSystem/RelayBase/ProtectionElement, project configuration, measurement, action mapping, study lifecycle and persistence contracts.
2. Reconcile the existing Protection README and implementation against this architecture.
3. Create a requirement-to-module-to-status matrix; distinguish implemented, partial, contract-only, missing and unverified.
4. Correct the CT association PR independently; do not merge it as a substitute for Protection Study implementation.

**Phase B — Study lifecycle and configuration integrity**
1. Add Protection Study to the existing StudyCase type/lifecycle rather than create a parallel runner.
2. Define typed study configuration, preparation snapshot, execution request, result and provenance.
3. Validate all instrument/channel/relay/element/scheme/action references against one project snapshot.
4. Enforce atomic configuration activation and stale-result invalidation.

**Phase C — Fault-scenario preparation and calculation**
1. Accept explicit, uniquely identified fault scenarios using the existing ShortCircuitStudyConfiguration contract.
2. Prepare each scenario from one detached ProjectSnapshot and canonical TopologySnapshot.
3. Reuse ShortCircuitPreparation and ShortCircuitAnalysis; do not create another fault solver or Study lifecycle.
4. Preserve project, activation-generation and topology-revision provenance in each result.
5. Retain typed scenario results and cancellation diagnostics without mutating live MeasurementChannels.
6. Do not claim relay response until the instrument/measurement conversion path is complete.

**Phase D — Instrument and measurement association**
1. Resolve explicit CT/PT/CVT terminal references using canonical EndpointReference and Core Terminal contracts.
2. Do not assume each primary instrument terminal maps directly to a Bus.
3. Support multi-core and multi-secondary CT modelling only where physical model contracts support it.
4. Reuse MeasurementProvisioning, MeasurementChannelService and ProtectionMeasurementBinding.
5. Convert scenario quantities through explicit instrument ratios, polarity and secondary-side contracts into detached, scenario-specific measurement samples.
6. Validate phase, sequence, polarity, units, ratio, source result mapping, channel freshness and quality policy.

**Phase E — Protection scheme and operation**
1. Reconcile start/operate/output logic and explicit output-to-target mappings.
2. Support multiple designated trip targets and backup targets where the scheme requires them.
3. Integrate breaker-failure supervision, retrip and backup trip paths.
4. Preserve Application command, transaction, acknowledgement and postcondition contracts.

**Phase F — Engineering algorithms and coordination**
1. Complete IDMT curve equations and curve-family catalogues.
2. Implement stateful time-overcurrent accumulation/reset semantics separately from static curve evaluation.
3. Implement TCC read models, overlays, fault-current markers and grading-margin calculations.
4. Complete 50/51/50N/51N and directional input semantics before expanding to differential, distance, bus and transformer schemes.
5. Classify each function honestly and prevent unsupported functions from entering production execution.

**Phase G — Study results and UI**
1. Publish typed result/read models only after successful study completion.
2. Add relay/instrument/protection matrix, trip matrix, diagnostics and TCC visualization.
3. Keep UI read-only with respect to calculation results; all edits flow through Application commands.
4. Add persistence and reopen compatibility through canonical project configuration.

**Phase H — Static acceptance and freeze**
1. Verify architecture ownership and imports.
2. Verify affected package exports and `ui/core/qt.py` if Qt integration changes.
3. Verify Python syntax and import integrity without running tests/CI unless explicitly requested.
4. Verify no accidental files, duplicate implementations, or unrelated diff.
5. Update `Modification_Register.txt` and freeze only the verified scope.

## 11. Non-negotiable acceptance rules

- One Protection Study workflow; no separate competing protection-study lifecycle.
- One canonical ProtectionSystem and one canonical Study lifecycle.
- No universal element-owned ProtectionZone.
- No inferred feeder, relay, zone, input or breaker mapping from graphical proximity, geometry, collection order or matching Bus pairs.
- Measurement and protection output/control paths remain separate.
- No direct breaker mutation from Core protection functions.
- No measurement conversion inside protection algorithms.
- No stale result presented as current.
- No unsupported protection function marked implemented.
- No test/CI execution or requirement unless the user explicitly requests it.
- No claim of production readiness without engineering validation and the applicable verification evidence.

## 12. Research basis

This architecture was reconciled against the published scope and summaries of IEC 60255-1:2022, IEC 60255-151:2009, IEC 60255-121:2014, IEC 60255-187-1:2021, IEC 61869-1:2023, IEC TS 60255-216-1:2025, IEC 61850-7-4, IEC 62271-100:2021+AMD1:2024, IEEE C37.112-2018 and IEEE application guides for line and bus protection. These references inform requirement coverage; they do not imply GridForge compliance or replace access to the full standards and engineering review.


## 13. Phase B implementation status — existing Study lifecycle

The first Protection Study lifecycle slice is now implemented on the
architecture branch. It adds an immutable `ProtectionStudyConfiguration`
whose protection-system configuration is captured by value when the Study
Case is defined. It carries explicit evaluation time/timestep, event and
scenario correlation, supervision and non-authoritative metadata.

The existing Application `StudyService` registers `protection` as a
study type. `StudyCaseDefinition` validates the typed configuration.
The handler uses the existing Application protection evaluation path, so
measurement quality, availability, freshness, sample coherence, configured
input contracts and directional phasor validation remain authoritative.
The result carries project activation, source revision, topology revision,
configuration fingerprint, decisions and diagnostics.

**Safety boundary:** this is a non-operating study. The handler supplies an
explicit action resolver that returns no target, so a Protection Study cannot
trip or otherwise operate a breaker. Operational protection execution remains
a separate Application runtime path.

**Current scope:** one validated measurement-snapshot evaluation. It is not
yet a fault-scenario sweep or a complete engineering assessment. Short-circuit
scenario integration, sensitivity/selectivity, IDMT/TCC read models,
coordination, differential protection, instrument adequacy, breaker-failure
schemes and reports remain open implementation phases.

### Phase B files

- `core/application/protection_study.py` — typed configuration, result and handler.
- `core/application/study.py` — typed Study Case validation.
- `core/application/application.py` — handler registration, property-contract correction and explicit ProtectionContext inputs.
- `core/application/__init__.py` — public exports.
- `Modification_Register.txt` — implementation record.



## 14. Phase C implementation status — detached fault scenarios

The Protection Study configuration now accepts an immutable sequence of
`ProtectionFaultScenario` values. Each scenario carries a stable scenario
identity and the existing typed `ShortCircuitStudyConfiguration`; GridForge
does not introduce a duplicate fault taxonomy or short-circuit configuration
schema.

For each scenario, the Application handler:

1. Validates the configured fault Bus against the captured canonical
   `TopologySnapshot`.
2. Uses the detached `ProjectSnapshot.network`, not the live active Network,
   with the execution's canonical topology snapshot.
3. Reuses `ShortCircuitPreparation` to create the immutable numerical input
   and `ShortCircuitAnalysis` to execute the existing solver.
4. Verifies project identity, activation generation and topology revision in
   the returned short-circuit provenance.
5. Retains the typed `ShortCircuitResult` in a
   `ProtectionFaultScenarioResult` correlated to the scenario ID.
6. Preserves the solver's independent `ContributionStatus` and diagnostics;
   a numerically successful fault solve is not treated as measurement-ready
   when source/branch current contributions are partial or unavailable.
7. Checks cancellation and active project/revision provenance between scenario
   calculations.

A Protection Study containing fault scenarios is reported as
`fault_scenarios_calculated` only when the fault solve and contribution
coverage are complete. Otherwise the study result is `partial`. It does not
also evaluate live measurement samples and present them as fault-derived relay
inputs. The result explicitly records
`measurement_snapshot_evaluated=False` for this mode. The existing
measurement-snapshot mode remains unchanged when no fault scenarios are
configured.

**Engineering boundary not yet implemented:** short-circuit result quantities
are not yet transformed through the configured CT/PT/CVT physical instrument
models, ratios, polarity and secondary measurement paths into detached
scenario-specific MeasurementChannel/RelayInput samples. Therefore no relay
pickup, operating time, trip decision, scheme target, or selectivity result is
claimed for these fault scenarios. Live MeasurementChannel objects are never
modified to inject simulated fault values. Phase D must implement and validate the instrument-to-measurement adapter
and scenario-specific relay evaluation without weakening the Application
measurement-snapshot authority.

### Phase C files

- `core/application/protection_study.py` — immutable fault scenario/result
  contracts, detached short-circuit preparation/execution and provenance checks.
- `core/application/__init__.py` — public exports.
- `Modification_Register.txt` — implementation record.


## 15. Phase D audit — instrument-to-scenario measurement boundary

The next integration was audited against the current Protection Study branch
and the open CT association branch
`feature/sld-derived-ct-measurement-association` (PR #905). The audit found
that the existing contracts are not yet sufficient for a correct
scenario-derived relay evaluation.

### Confirmed existing contracts

- `ShortCircuitResult.branch_currents` contains typed branch records with
  from/to Bus identities, phase currents and sequence currents.
- `ProtectionMeasurementBinding` correlates a source equipment terminal,
  electrical side, quantity, physical instrument, channel and RelayInput.
- `MeasurementChannel` records the physical instrument and its secondary
  terminal reference.
- The CT association contract resolves CT P1/P2 into separate canonical SimpleWire topology components and retains S1/S2 secondary terminal references. It does not assign a protection zone.
- Application already creates immutable, per-cycle RelayInput sample
  snapshots and enforces project/configuration/channel provenance.

### Blocking contract gaps

1. The current `MeasurementGeneration.generate_short_circuit` path only
   accepts quantities at the fault Bus. It explicitly rejects arbitrary
   branch-current mapping, so it cannot yet supply a CT located on a feeder
   branch from `ShortCircuitResult.branch_currents`.
2. The binding previously identified RelayInput only by its local input
   name. This has been corrected by making each binding explicitly
   element-scoped and persisting the collection in
   `ProtectionProjectConfiguration`.
3. Branch selection is carried explicitly by each binding's
   `source_equipment_id` and `source_terminal_reference`; the Application
   service now requires a current binding to identify a canonical Branch
   FROM/TO terminal and validates that exactly one CT primary terminal
   resolves to that selected terminal Bus while the other resolves to the
   opposite Bus. It does not infer a branch from CT location.
4. The current short-circuit contribution status is preserved by
   `ProtectionFaultScenarioResult`; incomplete branch/source contributions
   make the Protection Study partial and must not be used for relay evaluation.

### Phase D implementation order and status

1. **Implemented:** each binding identifies its
   protection element and RelayInput name, and the binding collection is
   serialized with the project protection configuration.
2. **Implemented:** Application service mutation
   validates element/input/channel correlation, active RelayInput identity,
   physical source equipment terminal identity, instrument family, and
   configured ratio against the physical CT/PT/CVT.
3. **Implemented — topology association guard:** CT current bindings may
   explicitly select (a) a Branch FROM/TO terminal, (b) a terminal of
   monitored equipment such as a transformer, motor or load, or (c) a
   canonical Bus attachment. The Application service resolves the selected
   endpoint and CT P1/P2 through canonical SimpleWire topology components,
   requires the selected endpoint to belong to exactly one CT primary side,
   and requires P1/P2 to remain on distinct components. A Branch uses an
   explicit FROM/TO side; an equipment terminal uses its exact terminal role;
   a Bus attachment is explicitly declared as a Bus-side measurement.
   This records physical measurement location only and does not infer a
   feeder, protected equipment zone, or differential scheme.
4. **Implemented — CT primary-side locator and Branch conversion primitive:**
   CTMeasurementAssociation.locate_measurement_endpoint() identifies
   P1_SIDE or P2_SIDE for an explicitly selected Branch terminal,
   equipment terminal, or Bus attachment. The existing numerical conversion
   primitive remains limited to short-circuit Branch FROM/TO contributions;
   it derives direction from the configured Branch terminal, uses that
   side's Bus current base, and applies physical CT polarity and ratio once.
   Equipment-terminal and Bus-side scenario-current source adapters remain
   pending. Detached scenario RelayInput samples and ProtectionSystem
   evaluation also remain pending. Preserve phase and sequence values,
   including the residual-current convention required by 50N/51N.
5. **Pending:** keep simulated values detached from live MeasurementChannel
   objects. Extend Application's sealed sample-snapshot path to accept
   validated scenario samples keyed by protection element/input; preserve
   freshness, quality, unit, project and topology guards.
6. **Pending:** evaluate ProtectionSystem against scenario-specific samples
   and retain decisions as simulated study results. The Study remains
   non-actuating.

No branch-current-to-CT conversion or scenario-derived relay decision is
claimed by the current Phase C implementation.


## 16. Phase D implementation update — element-scoped measurement bindings

The binding identity is now explicit and stable across project persistence:

- `binding_id`: canonical binding record identity.
- `protection_element_id`: consuming configured ProtectionElement identity.
- `relay_input_id`: protection-local RelayInput name.
- `source_equipment_id` and `source_endpoint_reference`: explicit analysis
  source equipment and canonical terminal or Bus-attachment identity.
- `instrument_id` and `instrument_ratio`: physical CT/PT/CVT identity and
  explicitly captured ratio.
- `channel_id`: authoritative MeasurementChannel identity.
- `measurement_type`, `phase_or_sequence`, `electrical_side`, and
  `result_quantity`: declared mapping semantics.

`ProtectionProjectConfiguration` owns the binding collection and includes
it in `to_dict`/`from_dict`. It rejects duplicate binding IDs, duplicate
element/input bindings, references to missing protection elements, and
bindings whose channel does not match the configured element input. Replacing
an element configuration cannot silently invalidate a persisted binding;
removing an element is blocked until its bindings are explicitly removed.

`ProtectionConfigurationService` provides transactional create/remove
operations. Creation validates the active element/input/channel relationship,
the live RelayInput channel reference, source equipment and terminal identity,
physical instrument family, and the persisted ratio against the actual
instrument ratio. For current measurements it additionally requires the
explicit source equipment to be a Branch, requires the selected FROM/TO side
to match the canonical branch terminal role, and resolves both CT primary
terminals through Core connectivity. Exactly one CT primary terminal must
share the selected branch-terminal Bus and the other must resolve to a
distinct Bus. This is an explicit association check, not a branch inference.

**Still pending:** branch-current per-unit conversion and signed CT secondary
phasors, detached scenario measurement sample creation, and non-actuating
scenario relay evaluation.


## 17. SLD instrument placement and primary connectivity contract

Instrument placement is governed by the physical electrical role of each
instrument, not by a generic "measurement device" connection rule.

### Current Transformer (CT)

- A CT is inserted inline on an SLD SimpleWire connection. The wire is
  represented as two terminal-to-terminal SimpleWire segments around the CT:
  one segment reaches P1 and the other reaches P2.
- P1/P2 are primary power-path terminals. They must remain in distinct
  SimpleWire topology components; joining them into one component bypasses
  or shorts the CT and is invalid for a series CT insertion.
- The engineer explicitly associates the CT with the monitored Branch and
  its FROM/TO terminal side. This association is not inferred from the CT's
  screen position, nearest Bus, or matching graphical coordinates.
- The association validator uses ConnectivityResolver terminal components
  to confirm that the selected Branch terminal shares exactly one primary
  CT terminal's SimpleWire component. It does not require the CT itself to
  be a Branch or mistake the SimpleWire segment for an analysis Branch.
- S1/S2 are isolated measurement-secondary terminals. They are not part of
  the primary power path and are not ordinary Bus attachments.

### Potential Transformer (PT) and Capacitive Voltage Transformer (CVT)

- PT/CVT primary terminals are connected at the intended voltage
  measurement point: to the relevant SimpleLine/line connection or directly
  to the selected Bus, as appropriate to the SLD arrangement.
- The persisted protection binding now accepts either a canonical terminal
  EndpointReference (for example, a Line/Branch terminal exposed by the
  SimpleLine projection) or a canonical Bus attachment EndpointReference.
  The binding field is named source_endpoint_reference; older persisted
  source_terminal_reference mappings remain readable.
- Application resolves the selected endpoint and PT/CVT primary terminals
  through ConnectivityResolver. Exactly one primary terminal must share the
  selected endpoint's topology component, while the two PT/CVT primary
  terminals must remain on distinct components.
- SimpleLine remains an SLD/projection concept in this inspected Core
  contract; the SLD adapter must supply its canonical Core line terminal
  reference. A graphical SimpleLine or symbol anchor is never accepted as
  electrical truth.
- PT/CVT secondary terminals remain measurement interfaces. They do not
  become primary network Buses or power-path conductors.

### Layer boundary

The SLD expresses placement and the engineer's explicit associations.
Core ConnectivityResolver validates terminal-to-terminal SimpleWire
components and Bus attachments. The analysis Branch identity remains the
source of branch-current results. Measurement conversion consumes that
explicit Branch result only after the CT-to-Branch association has been
validated. No SLD graphics, coordinates, or symbol anchors are used as
electrical truth.


## 18. Bus-capable measurement source binding

ProtectionMeasurementBinding now persists a canonical
`source_endpoint_reference` rather than assuming every measurement source
is a physical equipment terminal. The endpoint may be either:

- a terminal EndpointReference, retaining equipment type, equipment ID,
  and terminal role; or
- a Bus attachment EndpointReference, retaining Bus ID and canonical
  attachment slot.

The legacy `source_terminal_reference` persistence key is accepted during
deserialization for existing project configurations. New serialization
writes only `source_endpoint_reference`.

Current measurement remains stricter: CT branch-current bindings require an
explicit Branch terminal and cannot use a Bus attachment as a substitute.
Voltage measurement accepts an explicit Bus attachment or a canonical
terminal endpoint. Application validates the selected endpoint against the
PT/CVT primary terminal topology and confirms the two primary terminals
remain on distinct connectivity components. This enables direct Bus
measurement and line-terminal measurement while preserving the SLD/Core
boundary.


## 17. Explicit differential protection scheme configuration

Differential scheme membership is a project-scoped engineering configuration,
not a property inferred from CT placement, SimpleWire connectivity, Bus
identity, or an individual ProtectionElement. The initial
`DifferentialProtectionSchemeConfiguration` records:

- a stable scheme identity;
- the explicitly protected Core object type and ID (Bus, transformer, line,
  generator, motor, or reactor);
- at least two distinct, explicitly selected current-measurement binding IDs;
- an explicit `INTO_ZONE` or `OUT_OF_ZONE` current direction for every
  member binding; current direction is never inferred from CT P1/P2 placement;
- optional per-binding phase-compensation degrees, recorded as engineering
  configuration but not yet applied by a differential calculation;
- enabled state and detached metadata.

The aggregate validates that every member binding exists and is a current
measurement binding. A member binding cannot be removed or changed to a
non-current binding while a scheme references it. The configuration is
persisted with `ProtectionProjectConfiguration`. Application create/delete
operations are transactional; when a Core Network provider is available,
creation also validates that the declared protected object exists and its
type matches.

This contract permits Bus differential membership to reference CTs at
different Bus attachments and transformer differential membership to
reference CTs at the transformer's configured measurement boundaries. The
scheme is not inferred from a Bus-to-Bus CT placement or from two CTs merely
being present in the network.

**Not implemented by this configuration pass:** CT ratio/vector-group
compensation, phase mapping execution, zero-sequence compensation, differential
and restraint current calculation, percentage-bias characteristic, harmonic
or waveform restraint, CT saturation/stability supervision, operate/restraint
decision logic, trip mapping, and differential study result reporting. The
stored phase compensation is configuration only and must not be mistaken for
an applied correction.


## 18. Differential calculation kernel — Phase E2

The Core differential kernel is a pure, non-actuating calculation boundary.
It consumes one detached three-phase complex-current sample for every binding
explicitly named by a DifferentialProtectionSchemeConfiguration. Each
sample declares a common reference_basis_id and supplies fundamental RMS
complex phasors in amperes. Scalar magnitudes are not accepted as substitutes
for phasors because the operating quantity is a vector sum.

For each phase, the configured INTO_ZONE direction contributes the sample
phasor with positive sign and OUT_OF_ZONE contributes it with negative sign.
The operating current is the magnitude of the signed phasor sum. The
restraint current is selected explicitly from HALF_SUM_MAGNITUDES,
SUM_MAGNITUDES, or MAX_MAGNITUDE; these are selectable mathematical
definitions, not interchangeable universal conventions.

DifferentialProtectionSettings requires an explicit positive pickup,
restraint method, one or more non-negative bias slopes, and strictly
increasing restraint-current breakpoints. The resulting piecewise-linear
bias threshold is continuous at each breakpoint. An optional high-set pickup
is evaluated independently of the biased stage. The result reports phase
operate current, restraint current, threshold, margins and a non-actuating
operate indication.

The kernel rejects missing/extra member samples, mismatched sample identity,
inconsistent current bases, non-finite phasors, incomplete A/B/C phase sets,
and disabled schemes. It does not infer current direction from CT P1/P2,
SimpleWire topology, Bus attachment, SLD geometry, or protected-object type.
Non-zero configured phase compensation is explicitly rejected until an
equipment-specific compensation adapter is implemented; it is never silently
ignored.

Scope limitations: input CT/relay current normalisation is an upstream
responsibility and must be proven before connecting real ProtectionStudy
samples. This kernel does not perform CT ratio/polarity conversion, transformer
vector-group or winding compensation, phase permutation, zero-sequence
treatment, inrush/overexcitation restraint, CT saturation supervision,
waveform/transient analysis, differential element timing, ProtectionDecision
integration, action mapping, or breaker operation. It is a numerical primitive,
not a complete 87T/87B/87M/87G function or production-ready protection scheme.

The selected restraint definition and piecewise characteristic are explicit
because practical differential relays use differing restraint definitions
and slope characteristics; the engineer must select settings consistent with
the applicable relay/application. See the reviewed SEL percentage-restraint
paper and PNNL technical report PNNL-36067.


## 19. Persisted differential protection characteristics — Phase E3

DifferentialProtectionSchemeConfiguration now optionally persists its own
differential_settings as part of the project ProtectionProjectConfiguration.
The stored characteristic contains pickup_current_a, restraint_method,
slopes, breakpoints_a and optional high_set_pickup_a. The aggregate validates
the supported keys, finite non-negative numeric values, positive pickup,
slope/breakpoint cardinality and strictly increasing breakpoints before the
scheme is accepted or reconstructed from persistence.

DifferentialProtectionSettings provides typed to_dict/from_dict conversion.
The Core differential kernel accepts an explicit settings object or can
reconstruct the typed settings from the scheme's persisted characteristic.
No default characteristic is silently assigned: a scheme without persisted
settings still requires explicit settings at evaluation.

The persisted values are expressed in the scheme's declared current reference
basis. This pass does not create that basis, perform CT conversion or prove
that independent CT channels are normalised to it. Scenario-derived CT phasor
generation and ProtectionStudy integration remain separate outstanding work.


## 20. Detached CT fault-scenario measurement adapter — Phase D4

The first scenario-to-measurement adapter increment converts an explicitly
configured Branch FROM/TO CT binding from a complete short-circuit branch
contribution into an immutable `ProtectionScenarioMeasurementSample`.
It consumes the existing complex `phase_currents.<phase>` or
`sequence_currents.<sequence>` contribution, the persisted binding, the
authoritative CT object, its MeasurementChannel and a CT association resolved
against the same topology revision.

The adapter validates scenario/result completeness, contribution completeness,
Branch identity and terminal side, CT association membership, channel/instrument
identity, physical CT ratio, and the exact phase/sequence member declaration.
It applies the existing per-unit-to-primary-A, branch orientation, CT polarity
and CT-ratio conversion path. The output is detached and carries scenario,
project, activation, topology, Branch, Bus, CT, base and ratio provenance.
It never calls `MeasurementChannel.update` and cannot overwrite live values.

**Strict boundary:** this is a CT-secondary sample expressed in the canonical
ampere unit (`A`), not a common primary-current reference basis. Each sample
declares an instrument/channel-specific CT-secondary basis identity so samples
from different CT ratios cannot accidentally satisfy the differential kernel's
common-basis guard. Differential protection still requires an explicit,
engineering-valid CT normalisation/compensation stage before its samples can
be evaluated. Bus-attached and equipment-terminal CT contribution adapters,
PT/CVT fault-voltage conversion remain pending. Phase D5 now assembles
detached RelayInput snapshots and evaluates eligible current protection
functions for explicitly bound Branch FROM/TO CT samples. Unsupported
instrument/input paths still fail closed, and no breaker action is dispatched.


## 21. Detached fault-scenario RelayInput evaluation — Phase D5

Protection Study fault scenarios now have a bounded path from complete
short-circuit branch contributions to non-actuating protection-function
evaluation:

`ShortCircuitResult
→ explicit ProtectionMeasurementBinding
→ CTMeasurementAssociationService
→ Branch FROM/TO CT conversion
→ immutable ProtectionScenarioMeasurementSample
→ Application validation and snapshot assembly
→ RelayInput evaluation snapshot
→ ProtectionSystem
→ per-scenario ProtectionExecutionResult`

The Application validates the exact binding, element/input/channel identities,
CT instrument identity and ratio, CT secondary terminal, phase/sequence,
canonical engineering unit, channel engineering scale/polarity,
scenario/project/activation/topology provenance, and the declared protection
input representation before installing any evaluation snapshot. Missing, duplicate, extra, stale, or unsupported inputs
block the complete scenario evaluation before a protection element executes.

The snapshot is installed only for the duration of the ProtectionElement
evaluation through the existing Application-authorized snapshot mechanism.
The underlying MeasurementChannel object and its value, timestamp, quality,
availability and sample sequence are not modified. Study-derived quantities
carry no fabricated acquisition timestamp. Their snapshot uses
`MeasurementQuality.UNKNOWN` to avoid claiming sensor quality and
`MeasurementValidity.VALID` only after the complete solver result and
correlation contract have passed.

**Current supported scope:** explicitly bound Branch FROM/TO CT phase-current
and sequence-current members whose channel units and phase/sequence contracts
match the protection function. This supports eligible configured current
functions such as 50/51 and 46 when their full input contracts are satisfied.

**Not yet supported:** Bus-attached or non-Branch equipment-terminal current
contributions; PT/CVT fault-voltage conversion; ANSI 67 scenario polarising
voltage/angle snapshots; residual-current semantics for 50N/51N; transformer
differential compensation and shared primary-current normalisation; and
automatic output/action dispatch. Unsupported inputs fail closed. Differential
protection remains outside this D5 relay-snapshot path until CT normalisation
and function-specific compensation are implemented.

Each `ProtectionFaultScenarioResult` now retains its own
`ProtectionExecutionResult` and an explicit `relay_evaluation_completed`
flag. A completed evaluation with no ProtectionDecision is a valid
no-operation result and is not confused with a scenario where relay evaluation
never ran. The Study result exposes combined decision/diagnostic views while
retaining per-scenario records. No breaker command is dispatched and no live
measurement channel is injected.


## 22. Short-circuit terminal-current result contract — Phase D6 foundation

The detached `ShortCircuitResult` distinguishes aggregate Branch current from
current at a physical equipment terminal. Each immutable terminal-current
record is keyed by exact equipment ID and terminal role and identifies the
equipment type, canonical Bus attachment, complex phase/sequence currents,
per-unit current basis, and a fixed reference direction of positive current
INTO the equipment. For a series-only Branch primitive, the FROM terminal
current is the Branch current and the TO terminal current is its negative.
Both values are calculated from solved sequence voltages and prepared series
impedance; they are not inferred from SLD geometry or CT P1/P2 orientation.

Terminal-current status is independent of source/Branch contribution status.
COMPLETE requires both terminal records for every prepared Branch; PARTIAL
reports incomplete coverage; UNAVAILABLE means no supported terminal records
could be produced. Diagnostics identify unsupported equipment rather than
silently treating an equipment aggregate as a terminal measurement.

At the time of Phase D6, terminal-current records were supported only
for series-only Line and Cable primitives. The transformer gap identified
here was subsequently narrowed by Phase D7 (tap-aware sequence-network
stamping) and Phase D8 (balanced three-phase transformer terminal currents).
Unbalanced transformer terminal currents remain unavailable until winding
connection/vector-group and neutral-grounding sequence models are implemented.
Shunt charging, mutual coupling, multi-winding transformers, machine stator
terminals, load contributions and Bus-boundary injection records remain
outside the implemented terminal-current scope. Protection Study CT adapters
still do not consume the generic terminal-current records.


## 21. Transformer sequence-network tap primitive — Phase D7

The canonical short-circuit sequence-network preparation stamps a
two-terminal transformer using the explicit Core Transformer from-side
complex tap a = t * exp(j * theta), where t is the persisted tap ratio and
\(\theta\) is the Core phase-shift value in radians. The primitive is:

\[
Y_{ff}=\frac{y}{|a|^2},\quad
Y_{ft}=-\frac{y}{a^*},\quad
Y_{tf}=-\frac{y}{a},\quad
Y_{tt}=y
\]

Line/Cable and single-Bus source stamps retain unity-tap behaviour. The
detached SequenceBranchSnapshot preserves the transformer's tap ratio and
phase shift so the result layer can use the same primitive rather than
reconstructing transformer state from live Core.

**Strict scope:** this increment applies only the explicit Core scalar tap and
phase-shift fields. It does not apply optional plugin VectorGroup clock
displacement, winding connection mapping, neutral grounding/zero-sequence
paths, transformer magnetising/shunt admittance, tertiary windings, or
unbalanced transformer sequence coupling. Consequently, unbalanced
transformer short-circuit studies requiring those behaviours remain
unsupported and must not be represented as complete. Phase D8 implements
transformer terminal-current output for balanced three-phase fault cases only.
Unbalanced transformer terminal currents remain unavailable. When a caller
supplies an external SequenceNetwork alongside a transformer with non-unity
tap or non-zero phase shift, the matrix must explicitly declare the
FROM_SIDE_COMPLEX_TAP_V1 convention; otherwise preparation rejects it.

Verification: remote source review and contract reconciliation only. No tests
or CI run. Python syntax/import/runtime checks remain outstanding.


## 22. Transformer terminal-current equations — Phase D8

For a balanced three-phase short-circuit case, the detached solver now
calculates transformer terminal currents from the same from-side complex tap
and positive-sequence series admittance used by the canonical Ybus stamp:

\[
I_f = y\left(\frac{V_f}{|a|^2}-\frac{V_t}{a^*}\right),\qquad
I_t = y\left(V_t-\frac{V_f}{a}\right)
\]

Both currents are positive into the transformer at their respective physical
terminals. The terminal records retain each terminal's Bus identity and
canonical terminal role. The Branch current contribution is the FROM-terminal
current, preserving the established branch orientation.

This is deliberately restricted to balanced three-phase faults, for which
the current model has the positive-sequence transformer primitive. The
transformer model currently does not provide the negative/zero sequence
winding-connection, vector-group, and neutral-grounding network required for
unbalanced fault terminal currents. Those cases remain unavailable rather
than reusing the positive-sequence current or assuming a grounded-wye path.
Transformer magnetising/shunt current, tertiary windings and detailed
multi-winding equivalents remain outside this two-terminal series primitive.

Verification: remote source-level review only. No tests or CI run. Python
syntax/import/runtime checks remain outstanding.


## 23. CT measurement conversion from equipment-terminal currents — Phase D9

Protection Study scenario conversion now consumes the detached
ShortCircuitTerminalCurrent record selected by the engineer's persisted
ProtectionMeasurementBinding. The binding must identify one equipment
terminal by equipment ID and terminal role, one CT, one MeasurementChannel,
one RelayInput, and one explicit phase/sequence quantity.

The converter verifies the terminal record identity, Bus, per-unit basis,
INTO_EQUIPMENT reference direction, result status, terminal-current
availability, topology revision, CT association, physical CT polarity,
secondary channel source/terminal, and configured CT ratio. It converts
terminal per-unit current to primary amperes using the terminal Bus voltage
base. Because terminal current is positive into equipment, a measured endpoint
on the CT P1-side component reverses that sign relative to P1-to-P2, while an
endpoint on the P2-side component retains it. The configured CT polarity is
then applied before conversion to CT secondary amperes. The operation creates a detached scenario sample and
does not mutate live MeasurementChannel state.

A PARTIAL terminal-current set may still supply a sample when the exact
configured terminal record is present and valid; missing or unsupported
records remain blocked. This avoids rejecting a valid configured measurement
solely because an unrelated equipment terminal elsewhere in the network is
unsupported. FAILED or UNAVAILABLE terminal-current sets are rejected.

The terminal-current adapter supports only terminal records actually emitted
by the short-circuit solver (currently Line, Cable, and balanced three-phase
Transformer series primitives). Bus attachments, PT/CVT voltage conversion,
unbalanced Transformer terminal currents, unsupported equipment, and
protection-zone inference remain outside scope. The CT association resolver
continues to report physical P1/P2 connectivity only; it does not assign a
protection zone or infer the engineer's measurement target.

Verification: remote source review only. No tests or CI run. Python syntax,
import integrity and runtime checks remain outstanding.


## Protection Study D10 — explicit residual-current input configuration

ANSI 50N/51N residual-current input configuration is represented by
`ResidualCurrentInputConfiguration`, persisted on the configured protection
function and restricted to those function codes. The configured source mode
is exactly one of:

- `THREE_PHASE_SUM`: three distinct, explicitly assigned A/B/C measurement
  binding IDs at one engineer-declared measurement point.
- `NEUTRAL_CT`: one explicit neutral CT measurement binding.
- `CBCT`: one explicit core-balance CT measurement binding.

The Core resolver calculates a complex phasor sum, never a sum of magnitudes.
For a three-phase sum it requires each source sample to declare canonical
amperes, its explicit phase, scenario identity, measurement-point identity,
topology revision, and an identical CT-secondary reference basis. Incompatible
CT ratios/bases are rejected; the resolver does not silently add unlike
secondary currents. Dedicated neutral and CBCT modes are not interchangeable
with the three-phase mode and require source-mode provenance to match the
persisted configuration.

This increment establishes the persisted source contract and isolated
fail-closed resolver only. It does not yet connect the resolver to
ProtectionStudyHandler/Application snapshot creation, populate
measurement-point/source-mode provenance in D9 samples, normalize unequal CT
ratios to a common primary-current basis, or enable 50N/51N input contracts.
Those functions remain fail-closed until that integration is complete.
No protection zone is inferred from CT placement. No live MeasurementChannel
state is mutated.


## Protection Study D11a — residual-current primary-current normalization

Residual-current source samples are normalized independently to a common primary-current basis before phasor combination. The normalization boundary consumes a validated detached CT-secondary sample and the active binding's CT ratio plus MeasurementChannel scale and polarity. It applies channel scale, channel polarity and CT ratio exactly once. The measurement adapter has already applied CT primary-side P1/P2 orientation and physical CT polarity; those operations must not be repeated.

The resulting immutable source sample declares amperes on the `PRIMARY_AMPS` basis and carries provenance confirming normalization, the engineer-configured measurement point, topology revision, CT ratio and channel scale/polarity. Three-phase residual current remains the complex phasor sum Ia + Ib + Ic. Different CT ratios are valid only after independent normalization to primary amperes.

This increment adds the normalization contract and resolver enforcement only. Application multi-binding RelayInput snapshot assembly, direct neutral/CBCT source-mode population, and ANSI 50N/51N input-contract enablement remain outstanding. 50N/51N therefore remain fail-closed. No protection zone is inferred from CT placement and no live MeasurementChannel state is mutated.

Verification: remote source review only. No tests or CI run; Python syntax, import integrity and runtime execution remain outstanding.

### D11b — Residual-current source binding relation

The project configuration aggregate accepts multiple explicitly declared physical measurement bindings for the residual_current input of ANSI 50N/51N only when their binding IDs exactly belong to the persisted ResidualCurrentInputConfiguration. This supports the configured A/B/C source set without relaxing the ordinary one-physical-input/one-binding invariant. Configuration replacement cannot orphan existing source bindings, and removal of a referenced source binding is rejected.

This is a configuration/persistence boundary correction only. It does not compose a derived relay input, assemble Application-authorized residual snapshots, or enable ANSI 50N/51N. Those remain fail-closed pending end-to-end integration and source validation.


### D11c — End-to-end ANSI 50N/51N residual-current scenario input

ANSI 50N and 51N now use a first-class `DerivedRelayMeasurement` as the `residual_current` RelayInput source. It is not a physical `MeasurementChannel` and is not inserted into the MeasurementChannel registry. Runtime composition requires a persisted `ResidualCurrentInputConfiguration` and creates this derived source only for 50N/51N.

The canonical input contracts declare a complex-capable current input in amperes. Application validates the exact configured binding set, active in-service CT identity, CT secondary channel identity, phase classification, terminal-current reference direction, per-unit result provenance, project activation and topology revision, CT ratio and physical polarity, channel scale/polarity, and the explicit measurement-point declaration. Each CT-secondary sample is normalized independently to signed primary amperes; three-phase residual is the complex phasor sum `Ia + Ib + Ic`, not a sum of magnitudes. Direct neutral-CT/CBCT modes remain fail-closed: the current short-circuit terminal-current model has no dedicated neutral-conductor primitive or multi-conductor CBCT source model. The resulting detached snapshot carries source binding IDs, source mode, measurement point, scenario and topology provenance, and a derived-input identity checked by `ProtectionElement` before evaluation.

The existing ANSI 50N instantaneous pickup and ANSI 51N IEC inverse-time/latching/reset algorithms consume the same derived residual phasor through their ordinary RelayInput accessors. No physical MeasurementChannel is mutated, no protection zone is inferred from the CT location, and ordinary single-channel protection inputs retain their existing one-binding contract.

Both ANSI 50N and 51N pickups are interpreted in primary amperes because the derived residual snapshot is normalized to PRIMARY_AMPS. The operating quantity is residual current 3I0 = Ia + Ib + Ic; it is not the zero-sequence component I0 alone.

Each fault scenario is composed against a fresh ProtectionRuntime. This isolates ANSI 51N pickup timing/latching state between independent fault cases and prevents scenario evaluation from mutating the active live protection runtime.



Engineering configuration requirement: every residual source binding must declare `measurement_point_id` equal to the function's configured point. For the currently executable `THREE_PHASE_SUM` mode, A/B/C source bindings must use three distinct CT instruments, three phase-specific current channels, and the same explicit measurement point. `NEUTRAL_CT` and `CBCT` configurations are persisted but rejected at runtime until their physical source models and solver contributions exist.



### D12 — Explicit Line zero-sequence impedance for earth-fault studies

The Line Core model now accepts optional `zero_sequence_resistance_ohm` and `zero_sequence_reactance_ohm` as a required pair. These values are physical series impedance data, are persisted by the generic ModelDTO slot/state serializer, and can be created or updated through the Application command and transactional `LineModelService` path. Existing Line projects deserialize with both values absent and remain valid for positive-sequence studies.

`SequenceNetworkPreparation` converts an explicitly supplied Line Z0 to the study per-unit base. Unsymmetrical fault preparation still fails closed when Z0 is absent or zero; it never substitutes Z1 for Z0. The solver then uses the prepared zero-sequence network when calculating SLG/LLG branch terminal-current records. This is a prerequisite for 50N/51N residual-current measurements on line-connected CT locations, not a declaration that every transformer or neutral return path is supported.


### D13 — Transformer negative-sequence primitive

For the existing passive, static two-winding Transformer model, the negative-sequence series impedance is prepared from the same physical series impedance as positive sequence. The negative-sequence complex tap uses the conjugate phase displacement, reversing the phase-shift angle while retaining the tap ratio. This does not infer transformer zero-sequence behavior: winding connections, vector group, neutral grounding and zero-sequence transfer remain unsupported, and earth-fault preparation through a transformer must still fail closed.

### D14A — Transformer winding and neutral-grounding input contract

The Transformer model now records explicit HV/LV winding connections (`DELTA`, `WYE_GROUNDED`, `WYE_UNGROUNDED`) and explicit complex neutral grounding impedance in ohms for grounded-wye windings. A solidly grounded neutral must be declared as `0j`; absent values are never interpreted as solid grounding. The create/update commands and transactional Application TransformerModelService carry these inputs. Updates validate the complete candidate atomically, support changing winding connection with corresponding grounding changes, and restore the exact prior configuration on transaction rollback. Transformer summaries expose the configured winding and neutral values. Core validation also rechecks restored/persisted winding and neutral combinations and rejects boolean or non-finite neutral impedance values.

This phase establishes engineering configuration only. It does **not** yet stamp a transformer zero-sequence equivalent. Delta circulating paths, grounded-wye transfer/blocking, winding-pair coupling, vector-group clock mapping and the `3Zn` neutral contribution remain unimplemented. Sequence preparation therefore fails closed with a transformer-specific diagnostic when zero sequence is requested.

### D14B — Transformer zero-sequence input and terminal-reference contract

Transformer configuration now has explicit HV/LV terminal-role mapping (FROM or TO), an explicit impedance_reference_winding (HV or LV), and paired physical zero-sequence resistance/reactance in ohms. A declared transformer Z0 is rejected unless the HV/LV terminal mapping and reference winding are also declared. The Application create/update command payloads and transactional TransformerModelService now carry these fields; update rollback captures and restores the complete prior D14B state. The generic ModelDTO slot serializer persists the scalar and enum-valued fields without a second persistence representation.

The Z0 pair is physical series impedance referred to the explicitly named winding. It is not the transformer neutral impedance and does not include either neutral's 3Zn contribution. Sequence preparation remains fail-closed: this contract does not establish zero-sequence transfer, delta circulating current, winding-pair equivalent circuits, core-return paths, vector-group clock behavior, or transformer terminal-current provenance. No earth-fault path through a transformer is enabled by D14B.


### D14C — Explicit transformer magnetic-core construction and Z0 data provenance

Transformer models now accept an explicit magnetic-core construction: THREE_LIMB, FIVE_LIMB, or SHELL_FORM. Transformer Z0 input additionally requires a declared data provenance basis: MEASURED_ZERO_SEQUENCE_TEST or MANUFACTURER_ZERO_SEQUENCE_DATA. These are persisted as normal typed model state, exposed through create/update commands and TransformerModelService, included in transactional rollback, and surfaced in Transformer summaries. The construction declaration is not a substitute for measured Z0; the physical Z0 pair remains explicit and referred to its declared winding.

All three core constructions are representable. No generic correction factor or default return-path assumption is applied from core type alone. The zero-sequence sequence-network result remains unavailable for every transformer construction until the winding-pair primitive can represent grounding, delta circulation/blocking, magnetic return paths, and supported test-data applicability. Missing core construction or Z0 provenance rejects a transformer Z0 declaration. A declared construction without valid Z0 data does not make the transformer zero-sequence equivalent available.


### D14D — Transformer zero-sequence winding-path classification

Added a Core/Analysis topology classifier that distinguishes (a) no externally grounded zero-sequence path where neither winding is grounded-wye, and (b) a one-sided grounded-wye return candidate where exactly one winding is grounded-wye. It explicitly reports delta internal-circulation possibility without treating that circulation as an external bus path. The one-sided candidate requires explicit Z0 data referred to the grounded winding, explicit core construction and Z0 data provenance; neutral grounding impedance remains separate and must contribute 3Zn in a future equivalent stamp.

The classifier deliberately rejects grounded-wye/grounded-wye transfer because the current transformer contract does not yet include vector-group, clock-number, winding-polarity and applicable test-configuration data. It returns a topology descriptor only: no numerical equivalent impedance, Ybus stamp, transformer terminal current or earth-fault result is produced. SequenceNetworkPreparation therefore remains fail-closed for all transformer zero-sequence stamps at this phase. This avoids representing a one-sided grounded return as a two-terminal series branch or interpreting internal delta circulation as an external terminal path.


## D14E — transformer vector-group and zero-sequence test contracts

Integration completion:
- Transformer owns both immutable contract values as authoritative slots and exposes them in summaries.
- CreateTransformerCommand and UpdateTransformerCommand carry the typed values; ModelCommandHandlers forwards command payloads without dropping fields.
- TransformerModelService create/update propagates them. Update rollback captures and restores both values atomically.
- Transformer construction, update validation and restored-state validation enforce vector-group/winding consistency and test applicability whenever Z0 is declared.
- ModelDTO encodes/decodes frozen dataclass values with explicit type identity, in addition to enum encoding, for the generic model-state persistence path.
- D14D classification requires and validates these contracts for one-sided grounded-wye candidates. For grounded-wye/grounded-wye, it validates declarations and still fails closed because the numerical two-winding equivalent is not implemented.
- Test configurations declaring neutral return included are rejected: stored transformer Z0 excludes neutral 3Zn, which remains a separate network contribution.

The contracts are model/command/service/persistence integrated. This does not enable transformer zero-sequence Ybus stamping, numerical equivalent calculation, or terminal-current generation. Legacy persisted transformer state lacking these contracts remains unavailable for Z0 classification.


## D14F — One-sided grounded-wye zero-sequence return equivalent

A transformer with exactly one grounded-wye winding may contribute a
zero-sequence shunt return on that grounded-wye Bus when its explicit Z0
reference winding, winding connections, vector-group declaration,
core-construction metadata, data provenance and test configuration are
applicable. This is not a two-terminal HV-LV series branch.

The numerical equivalent is formed on the grounded-wye winding side:

\[Z_{0,return}=Z_{0,transformer}+3Z_n\]

The stored transformer Z0 is physical ohms referred to the explicitly
declared grounded winding and excludes neutral return. The corresponding
neutral impedance is multiplied by three and added exactly once. The total
is converted to per unit using the grounded Bus line-to-line voltage base
and the study MVA base, then stamped as a shunt admittance at that Bus in
the zero-sequence Ybus. No shunt is stamped on the opposite winding Bus.

Test applicability is deliberately narrow: a delta opposite winding
requires an explicitly DELTA_CLOSED test condition; an ungrounded-wye
opposite winding requires OPEN_CIRCUIT. A short-circuit test condition is
not interpreted as this one-sided equivalent. Core construction is retained
as provenance only; no empirical multiplier is inferred from limb count or
shell form. Delta circulation remains internal and does not create an
external zero-sequence path on the delta Bus.

Grounded-wye/grounded-wye transfer remains fail-closed. No transformer
zero-sequence terminal-current primitive, earth-fault result, or relay
measurement path is enabled by this phase. A network containing a floating
or disconnected zero-sequence island remains unsolvable and is rejected by
the existing matrix singularity checks.


## D14G — Component-aware sequence-network solvability

Sequence-network preparation partitions each sequence network by its actual
sequence-conducting branches. A transformer without a supported zero-sequence
transfer primitive does not connect its HV and LV Buses in the zero-sequence
graph. Explicit source impedances and supported grounding shunts anchor
components; an island without a valid reference/return remains unavailable
rather than receiving a fictitious ground or pseudo-inverse.

Each grounded, numerically invertible component is independently reduced to
its own Zbus block. Floating or singular components are retained as explicit
unavailable Bus-index metadata in the immutable sequence snapshot. They do
not prevent unrelated grounded components from being prepared. A fault is
rejected only when its required sequence network is unavailable at the fault
Bus. LL faults require positive and negative sequence; LG and LLG faults also
require an available zero-sequence return. Contribution and terminal-current
records are suppressed for equipment whose required sequence endpoints lie
in unavailable components, and coverage diagnostics remain partial rather
than fabricating zero currents.

No Moore-Penrose inverse or arbitrary grounding impedance is introduced.
A blocked delta-side Bus therefore remains electrically isolated in Z0, while
a grounded-wye-side shunt can independently establish the grounded-side
return. This phase does not implement grounded-wye/grounded-wye transformer
transfer or transformer zero-sequence terminal-current primitives.


## D14H — Grounded-wye transformer zero-sequence terminal-current integration

The one-sided grounded-wye return shunt is now carried from sequence-network
preparation into the immutable short-circuit execution snapshot with explicit
transformer identity, grounded Bus index, winding side, terminal role,
per-unit impedance, physical Z0, separate neutral 3Zn, base values, core
construction and test-data provenance.

For LL studies, transformer terminal currents are composed from positive- and negative-sequence two-port currents. For LG/LLG studies, transformer terminal currents are composed from:
- the tap-aware positive-sequence two-port current at each physical terminal;
- the tap-aware negative-sequence two-port current at each physical terminal,
  using the conjugated complex tap;
- the zero-sequence grounded-side shunt current, calculated as
  `I0 = V0 / (Z0,transformer + 3Zn)` on the prepared per-unit base and
  assigned only to the explicitly grounded-wye terminal.

The opposite winding receives no externally reported zero-sequence terminal
current. Internal delta circulation is not represented as an external Bus
terminal current. Terminal records retain the `INTO_EQUIPMENT` reference
direction and include immutable sequence-model provenance. The existing CT
terminal adapter consumes the resulting phase/sequence values and now carries
that terminal derivation provenance into the detached CT sample; CT orientation
and physical polarity are still applied exactly once.

The solver fails closed when the immutable snapshot lacks the grounded-wye
shunt identity, when its Bus/terminal mapping does not match the transformer
branch, or when the required sequence component is unavailable. It does not
infer a zero-sequence path from a transformer Z0 value alone. Grounded-wye /
grounded-wye transfer remains unsupported, and no opposite-delta external
zero-sequence path is created.

Verification boundary: source changes are committed remotely on the feature
branch. No tests/CI, Python syntax/import checks, persistence round-trip or
numerical short-circuit runtime execution have been run.


## D14I — grounded-wye / grounded-wye three-test T-equivalent foundation

Added an immutable Core input contract for the three zero-sequence driving-point
measurements required to identify a two-winding grounded-wye T equivalent:
HV open-circuit Z0, LV open-circuit Z0 explicitly referred to the HV winding,
and HV short-circuit Z0. All values are physical ohms on one declared test
MVA basis. The contract records HV/LV test voltage bases, requires a non-empty
source reference, and rejects data that has not explicitly been referred to
HV or that includes neutral return impedance. Neutral 3Zn remains a separate
network contribution and must not be embedded in the measured transformer
T parameters.

The Analysis layer now derives the T parameters using the three-test
relations: ZM = sqrt(Z2' * (Z1 - Z3)), ZH = Z1 - ZM, and
ZX' = Z2' - ZM. The complex square-root branch is selected deterministically;
individual fitted series-leg resistances are not forced positive because a
valid fitted equivalent can contain a negative individual leg. The measured
impedances themselves must be finite, non-zero and non-negative-resistance.
The implementation verifies that the derived T network reconstructs all three
measured driving-point impedances within stated numerical tolerances.

**Integration boundary:** the immutable test-data contract is now stored on
Transformer, exposed in summaries, propagated through Create/UpdateTransformerCommand
and TransformerModelService, included in transactional update rollback, and
handled by the generic model-state dataclass persistence path. The Core model
requires grounded-wye/grounded-wye winding declarations and a Yy vector group;
Analysis classification requires explicit core construction, test-data basis,
and the applicable HV test declaration, then validates the derived T model.
D14I solver integration now builds the reduced two-Bus zero-sequence
admittance stamp from the three-test T equivalent. HV and LV neutral 3Zn are
added once to their respective T series legs; LV neutral impedance is referred
to HV by the square of the explicit test voltage ratio. The builder requires
both Bus nominal voltage bases to match the declared HV/LV test bases and
rejects non-unity tap or phase shift until a tap-adjusted zero-sequence test
model is implemented. The coupled admittance stamp joins the two Bus sequence
components, is inverted with the rest of the zero-sequence component, and is
copied into an immutable SequenceNetworkSnapshot. The solver calculates both
transformer terminal I0 values from the frozen two-port admittance matrix,
retains test/neutral/base provenance, and emits the normal INTO_EQUIPMENT
terminal-current records for the downstream CT adapter.


### D14I-03 — Three-phase CT measurement-point coherence

For `THREE_PHASE_SUM` residual-current configuration, the Application
scenario aggregator now requires all three configured A/B/C CT samples to
refer to the same canonical measured equipment terminal, identified by the
same equipment ID and terminal role. This check supplements the explicit
persisted measurement-point ID and the existing project, activation generation,
topology revision, CT identity, CT polarity, instrument ratio, channel, and
phase-member checks. A configuration that combines phase currents from
different equipment terminals is rejected rather than producing a plausible
but electrically incoherent residual phasor. CT placement and endpoint
association remain engineer-configured; no protection zone or endpoint is
inferred by the relay element.

This is source-integrated only. No tests/CI, syntax/import checks, or
end-to-end runtime execution were performed.


### D15A — Explicit neutral-CT and CBCT physical construction contracts

The residual-current configuration now requires a typed physical construction declaration for direct-source modes. NEUTRAL_CT identifies the exact neutral conductor, owning equipment terminal, neutral node and positive current reference. CBCT identifies a physical window and explicitly lists the enclosed A/B/C conductors, with optional N conductor membership and an explicit per-conductor current reference direction. The configuration rejects missing construction, duplicate conductor identities, missing phase conductors, ambiguous neutral inclusion and unsupported current-reference directions.

These declarations are construction metadata, not solver evidence. The short-circuit model still has no neutral-conductor network/current primitive and no CBCT window-current assembly from multiple enclosed conductor records. Accordingly, Application and protection input validation continue to reject both direct modes for execution; a complete-looking configuration cannot manufacture a measurement. The next implementation must add canonical Core conductor topology and immutable solver conductor-current records, then validate the configured CT conductor/window against those records before normalization to primary amperes.


### D15B — Immutable physical conductor-current result boundary

Added a typed ShortCircuitConductorCurrent record to the short-circuit result
contract. Each record identifies one physical conductor at one owning
equipment terminal and carries conductor ID, equipment/type, terminal role,
Bus, phase/conductor role, complex current, explicit terminal reference
direction, topology revision, MVA/voltage bases, per-unit basis and derivation
provenance. A physical conductor at
opposite ends of a branch is represented by two terminal-scoped records.
ShortCircuitResult now exposes an immutable conductor_currents mapping,
strict composite-key validation, a typed lookup helper, independent coverage
status and diagnostics.

The solver now reports conductor-current coverage as UNAVAILABLE rather than
promoting aggregate branch phase currents to physical conductor currents.
Current SequenceBranchSnapshot records do not carry explicit physical
conductor inventories or per-conductor electrical parameters. Therefore this
phase deliberately emits no conductor-current records. Neutral current and
CBCT aperture-current summation remain unavailable. This is an explicit
result contract and fail-closed integration point, not a claim that the
neutral or CBCT solver primitive is complete.

Next work must add persisted physical conductor identities to Core branch
models and commands, carry those identities into immutable prepared branch
snapshots, and calculate per-conductor current only where the electrical
model contains the required conductor impedance/return path. In particular,
a neutral conductor must not be assigned the negative sum of phase currents
unless the network model explicitly proves that it is the sole return path.


## D15C — Canonical Core physical-conductor inventory

GridForge now has an explicit Core value model for physical conductors carried by
two-terminal Branch equipment. `PhysicalConductor` provides a stable
branch-local conductor identity and a distinct physical role: A, B, C, neutral,
protective earth, screen, pilot, or other. Material, designation, cross-section,
and rated current are explicit optional construction data; none is inferred
from a phase label or conductor count.

`BranchConductorSystem` owns the ordered conductor inventory, physical length,
and a full reciprocal series-impedance matrix in ohms per kilometre. Matrix
rows and columns are bound to an explicit `matrix_conductor_ids` ordering.
Diagonal entries represent self impedance and off-diagonal entries represent
mutual impedance. The real resistance matrix must be positive definite.
Optional shunt-admittance matrix data is preserved separately; absence is not
rewritten as a measured zero.

The Branch Core model owns the immutable conductor-system value. Line and Cable
constructors accept it; Cable additionally requires the declared physical
inventory count and conductor-system length to agree with Cable configuration.
Generic ModelDTO slot/dataclass persistence preserves the contracts without a
parallel persistence schema. Application Line/Cable services and immutable
create/update command payloads accept the same typed value. Removal is explicit
through `clear_conductor_system`; omission on update preserves the existing
inventory. Transaction rollback restores the previous conductor system.

Engineering boundary:
- Conductor IDs are unique within their owning Branch; project identity is the
  equipment ID plus conductor ID.
- Neutral, protective earth, and screen remain separate physical conductors.
- A conductor spans the owning Branch FROM/TO terminal pair. D15C does not
  create additional Network nodes or infer terminal-to-earth/neutral return
  connectivity.
- Existing Cable `conductor_count` is only a count and never synthesizes
  identities or electrical parameters.
- The full impedance matrix is explicit and reciprocal. No uncoupled/zero
  mutual impedance is invented.
- This phase does not calculate conductor currents, stamp a multi-conductor
  network, derive neutral current from phase-current sum, or enable neutral CT
  and CBCT measurements. Those remain D15E/D15F-D15G work.
- Legacy Line/Cable models without a conductor system remain loadable, but
  cannot be promoted to physical conductor-current coverage.

Verification:
Remote GitHub source edits only. No tests/CI, Python syntax/import checks,
persistence round-trip, or numerical matrix fixtures were run.


## D15D — Physical conductor branch-topology association

The Network layer now resolves each explicit Line/Cable `BranchConductorSystem`
against the canonical `TopologySnapshot`. It produces immutable
`PhysicalConductorTopologySnapshot` and
`PhysicalConductorBranchTopology` records containing project/activation/
topology provenance, equipment identity/type, canonical FROM/TO terminal
roles, resolved FROM/TO Bus IDs, in-service state, and the complete immutable
conductor-system data.

Every physical conductor identity is exposed as a
`PhysicalConductorBranchAssociation` tied to its owning branch and that
branch's resolved FROM/TO Bus attachment pair. This association explicitly
does not claim separate phase/neutral/PE terminal nodes or conductor-to-earth
bonds. A Line/Cable branch has one canonical FROM and one canonical TO terminal;
the individual conductor inventory is carried inside that branch boundary.

Fail-closed behavior:
- The snapshot must match the current Network topology revision and a valid,
  rebuilt topology.
- An in-service conductor-equipped branch must have exactly one canonical Bus
  attachment at FROM and TO.
- Multiple Bus attachments, same-Bus endpoints, invalid terminal ownership,
  non-canonical terminal roles, or missing active endpoints are rejected.
- Out-of-service branches may retain incomplete endpoint associations; they
  are not promoted to active physical paths.
- No neutral, PE, screen, or ground bond is synthesized. No SLD symbol or
  graphics item participates in resolution.

`SequenceNetworkPreparation` attaches the immutable physical-conductor
topology snapshot to its prepared sequence network. The short-circuit
`SequenceNetworkSnapshot` preserves and validates that detached topology
against its Bus identity set. This is provenance/topology integration only:
the existing sequence-domain matrix builder does not yet consume the
multi-conductor impedance matrix and no physical conductor currents are
calculated.

D15E remains responsible for the multi-conductor numerical preparation and
current solution; explicit neutral/PE grounding and CBCT window semantics
remain subsequent work.

Verification:
Remote source edits and static source review only. No tests/CI, Python syntax/
import checks, topology runtime fixture, persistence round-trip, or numerical
conductor-current calculation was run.


## D15E — Physical conductor impedance preparation and branch-local current solution

D15E adds a separate physical multi-conductor numerical preparation product. It converts explicit Line/Cable series impedance matrices from ohm/km to total ohms and per-unit on the declared three-phase MVA and line-line voltage base. Full mutual coupling is retained by matrix inversion. Explicit shunt-admittance matrices are converted from S/km to total siemens and per-unit; missing shunt data remains unavailable.

The immutable prepared snapshot carries conductor matrix order and roles, branch and Bus identities, project/activation/topology provenance, physical length, study bases and source reference. FROM/TO Bus voltage bases must match for a Line/Cable primitive. Stale inventory, stale topology, missing study base, unsupported voltage-level transition or singular matrix fails closed.

The branch-local current solver accepts complete explicit conductor-voltage vectors at both terminals and solves the full coupled series impedance equation. When shunt data exists it also calculates the two nominal-pi half-shunt terminal contributions. Without explicit shunt data it returns series current only; it does not treat missing shunt as zero.

This phase does not create conductor nodes or infer neutral, earth, PE or screen return paths. Existing sequence-network fault results do not provide all conductor terminal potentials, so no physical conductor-current, neutral-CT or CBCT result is synthesized. Global phase-domain conductor-node network stamping and integration into fault-current execution remain subsequent work. NEUTRAL_CT and CBCT remain fail-closed.


## D15F-01 — Authoritative phase-domain conductor graph foundation

The Core Network aggregate now owns explicit phase-domain conductor graph
contracts. A graph node identifies one physical conductor node or one
explicit earth-reference node. A connection identifies a declared continuity,
bond, equipment bond, screen bond, grounding-electrode connection, or
earth-return impedance. Each connection carries its own complex impedance
in ohms; an ideal connection is represented only by an explicitly supplied
zero-ohm value.

The graph is detached and deterministic. Its snapshot carries project,
activation-generation, and topology-revision provenance. Duplicate identities,
dangling endpoints, non-finite/negative-resistance impedances, self-links,
and invalid connection semantics are rejected. Ground-electrode connections
must terminate at an explicit EARTH_REFERENCE node. Screen bonding requires
a SHIELD conductor, and equipment bonding requires a PE conductor.
Earth reachability is a graph property only; it does not imply zero-ohm earth
or a valid fault-current return without the declared connection impedances.

The authoritative `Network` aggregate now owns the registered node and
connection records. Mutations invalidate derived topology, and removal of a
node is rejected while connections still reference it. The graph remains
headless and independent of SLD graphics.

**Not yet enabled:** branch conductor terminal-to-node binding, global
phase-domain admittance assembly, source and fault boundary stamping,
phase-domain short-circuit execution, and solver-produced physical
conductor-current records. The existing sequence solver is unchanged.
Neutral CT and CBCT remain unavailable to protection execution until
physical current records are produced and validated against their explicit
construction declarations.
