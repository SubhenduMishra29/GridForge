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

Core must remain headless and must not import Qt, QGraphics, SLD, plugin, or UI types.

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

**Phase C — Instrument and measurement association**
1. Resolve explicit CT/PT/CVT terminal references using canonical EndpointReference and Core Terminal contracts.
2. Do not assume each primary instrument terminal maps directly to a Bus.
3. Support multi-core and multi-secondary CT modelling only where physical model contracts support it.
4. Reuse MeasurementProvisioning, MeasurementChannelService and ProtectionMeasurementBinding.
5. Validate phase, sequence, polarity, units, ratio, source result mapping, channel freshness and quality policy.

**Phase D — Protection scheme and operation**
1. Reconcile start/operate/output logic and explicit output-to-target mappings.
2. Support multiple designated trip targets and backup targets where the scheme requires them.
3. Integrate breaker-failure supervision, retrip and backup trip paths.
4. Preserve Application command, transaction, acknowledgement and postcondition contracts.

**Phase E — Engineering algorithms and coordination**
1. Complete IDMT curve equations and curve-family catalogues.
2. Implement stateful time-overcurrent accumulation/reset semantics separately from static curve evaluation.
3. Implement TCC read models, overlays, fault-current markers and grading-margin calculations.
4. Complete 50/51/50N/51N and directional input semantics before expanding to differential, distance, bus and transformer schemes.
5. Classify each function honestly and prevent unsupported functions from entering production execution.

**Phase F — Study results and UI**
1. Publish typed result/read models only after successful study completion.
2. Add relay/instrument/protection matrix, trip matrix, diagnostics and TCC visualization.
3. Keep UI read-only with respect to calculation results; all edits flow through Application commands.
4. Add persistence and reopen compatibility through canonical project configuration.

**Phase G — Static acceptance and freeze**
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
