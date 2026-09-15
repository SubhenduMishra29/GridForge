# Relay Protection Control Platform Implementation Plan

## Goal
Complete the GridForge V2 Relay, Protection, Trip, and Control platforms by reconciling the existing canonical Core implementations with the frozen Application mutation architecture. Do not create parallel models or bypass Application.

## Authoritative existing Core contracts
- `core/model/relay.py` — canonical physical Relay.
- `core/protection/relay_input.py` — canonical measurement-to-protection input boundary.
- `core/protection/relay_base.py` — canonical executable protection-function contract.
- `core/protection/protection_element.py` — canonical protection element boundary.
- `core/protection/decision.py` — canonical immutable ProtectionDecision.
- `core/protection/protection_system.py` — canonical protection orchestration.
- `core/protection/breaker_manager.py` — canonical protection/control breaker-operation boundary.
- Existing headless Control `LogicEngine`, `ControlEngine`, logic primitives, interlocks and `ControlDecision`.

## Global constraints
- Preserve the frozen GridForge V2 architecture.
- One canonical implementation per responsibility.
- Core Protection/Control must have no UI/Qt/QGraphics dependency.
- Protection and Control emit semantic decisions; Application owns mutation orchestration.
- Do not represent incomplete algorithms as production-complete.
- Newly created GridForge source files use the repository header convention and `Author: Subhendu Mishra`.
- Write tests but do not execute them, per user instruction.
- UI remains deferred until Core/Application boundaries are complete.

## Task 1 — Freeze Application integration map
1. Inventory existing Application command, service, event, handler, read-model and `CommandManager` infrastructure.
2. Trace one existing canonical equipment mutation end-to-end.
3. Identify/reuse the canonical equipment/breaker command.
4. Identify/reuse the canonical event publication and read-model mechanism.
5. Document the exact protection/control integration boundary before changing Core.

**Status: COMPLETE — current-head reconciliation.**

Canonical mutation path confirmed:

```text
ProtectionDecision
    ↓
TripBreakerCommand (model.trip_breaker)
    ↓
Application.execute()
    ↓
CommandManager
    ↓
ModelCommandHandlers.trip_breaker()
    ↓
ModelService.trip_breaker()
    ↓
SwitchingModelService.trip_breaker()
    ↓
Authoritative Core Breaker.trip()
```

Canonical semantic event path is `Application._publish_semantic_events()` through the single `ApplicationEventBus`. Control already follows the same Application boundary through `ControlCommandDispatcher` and `ControlExecutionService`.

No second command system, event bus, breaker API, or Application layer is required for this platform.

## Task 2 — Reconcile measurement semantics
1. Verify CT/PT/CVT associations to current/voltage measurement paths.
2. Verify `MeasurementChannel` engineering values, units, quality, validity and timestamps.
3. Verify `RelayInput` remains a live semantic reference rather than copied authoritative state.
4. Verify per-unit conversion follows existing Core conventions.
5. Add focused headless tests.

**Status: ARCHITECTURALLY COMPLETE — test coverage already present; no production change required in this pass.**

Confirmed:
- `MeasurementChannel` is the authoritative logical signal and stores source/source-terminal references without copying physical source state.
- `engineering_value = raw_value * scale * polarity` is the sole channel-level conversion.
- CT/PT/CVT physical ratios are applied by `MeasurementGeneration`, not by protection functions.
- Current conversion follows PU → physical primary current → CT secondary current.
- Voltage conversion follows PU → physical primary voltage → PT/CVT secondary voltage.
- `MeasurementChannel` carries unit, quality, availability, timestamp, sample sequence, stale-age configuration and explicit validity semantics.
- `RelayInput` exposes live read-through access to engineering value, availability, usability, validity, quality, signal type, phase, unit and source metadata.
- Existing `tests/core/measurement/test_measurement_conversion_contract.py` covers CT, PT, CVT conversion and source-identity binding.

No duplicate measurement abstraction was introduced.

## Task 3 — Complete ANSI 50
1. Add tests for below-pickup, exact-pickup and above-pickup cases.
2. Implement instantaneous overcurrent using the existing `RelayBase`/`ProtectionElement` boundary.
3. Produce canonical `ProtectionDecision` values.
4. Validate invalid measurement/settings through existing protection contracts.
5. Do not inspect arbitrary project/equipment objects from the function.

**Status: IMPLEMENTED — verification deferred.**

Added:
- `core/protection/overcurrent/instantaneous_relay.py`
- `tests/core/protection/test_instantaneous_overcurrent.py`

ANSI 50 criterion is explicitly `|I| >= pickup`, with `operating_time=0.0` on operation. The function reads current only through `RelayInput`, rejects unusable measurements without asserting a trip, and returns the canonical `ProtectionDecision` without operating equipment.

Runtime tests were intentionally not executed.

## Task 4 — Reconcile ANSI 51
1. Test pickup/non-operation.
2. Test existing IEC inverse-time curves and TMS.
3. Verify operating time comes from the existing curve equation.
4. Verify reset/repeated evaluation behavior.
5. Remove/reconcile any alternate 51 implementation found by audit.

## Task 5 — Reconcile requested protection functions
Inventory and explicitly classify `50`, `51`, `50N`, `51N`, `27`, `59`, `46`, `49`, `67`, `87`, and `21` as implemented, partial, contract-only or missing. Function code/function ID must be stable. Unsupported algorithms must fail explicitly rather than fabricate results.

## Task 6 — Complete trip-circuit boundary
1. Determine whether a canonical TripCircuit/TripCoil abstraction already exists.
2. If absent, introduce only one semantic trip boundary, without duplicating Breaker state/API.
3. Protection logic must not directly perform physical breaker mutation as its decision mechanism.
4. Route actual breaker mutation through the Application command path established in Task 1.
5. Add decision → trip → breaker integration tests.

## Task 7 — Reconcile Control I/O and execution
1. Inventory DigitalInput, DigitalOutput, AnalogInput and AnalogOutput implementations.
2. Reconcile them with existing control signal/state contracts.
3. Verify contacts, coils, timers, counters, latches, alarms, trips, interlocks and permissives.
4. Add only genuinely missing primitives.
5. Keep ladder execution headless.

## Task 8 — Reconcile ControlInterlock vs LogicInterlock
Keep the semantic distinction explicit: `LogicInterlock` is an executable logic component; `ControlInterlock` is an action-level permissive gate. Verify both through focused tests and prevent competing authoritative state.

## Task 9 — Application Protection orchestration
Using the frozen Application architecture, add/complete only the canonical command/service/event integration needed to:
- request protection evaluation;
- execute the canonical protection system;
- translate actionable decisions into the canonical trip/equipment command;
- publish protection/trip events through the existing event mechanism.

## Task 10 — Application Control orchestration
Using the frozen Application architecture, add/complete only the canonical integration needed to:
- request control execution;
- invoke the existing headless ControlEngine;
- convert permitted ControlDecision results into the canonical equipment command;
- publish control/alarm/interlock events through the existing event mechanism.

## Task 11 — Headless integration
Verify with tests, without executing them:

```text
CT/PT/CVT → Measurement → Relay → Protection → ProtectionDecision
→ Application trip command → Trip boundary → Breaker
```

and:

```text
Control Input → Logic → Interlock/Permissive → ControlDecision
→ Application equipment command → Equipment
```

Add transient/study integration only where existing stable measured-value interfaces support it; do not couple protection to one solver.

## Task 12 — Architecture tests
Add tests verifying:
- no Qt/PySide/QGraphics imports in Core protection/control;
- no UI dependencies in Relay/Protection/Control;
- protection/control evaluation does not directly mutate equipment;
- Application remains the mutation boundary.

## Task 13 — UI projections, last
Inventory existing UI protection/control surfaces first. Bind UI only to Application commands and read models. Add Protection, Relay Configuration, Coordination, Control & Automation, Ladder Logic and Trip/Control Simulation projections only after Core/Application completion.

## Acceptance
The implementation is not complete until the two end-to-end semantic chains above work through the canonical architecture, ANSI 50 is real, ANSI 51 timing is verifiable, requested function status is explicit, no duplicate responsibility remains, and no new architectural violation exists.

## Current explicit gaps
1. Application-level protection orchestration is partially present as `ProtectionOutputService`; remaining work is to expose/compose protection evaluation through the Application facade without bypassing the existing command/event architecture.
2. Application-level control orchestration is already present as `ControlCycleService` + `ControlExecutionService` + `ControlCommandDispatcher`; it requires reconciliation/tests rather than a parallel service.
3. ANSI 50 genuine implementation is now present; runtime verification is deferred.
4. ANSI 51 needs focused integration tests and status verification, not replacement.
5. TripCircuit/TripCoil semantic abstraction is not present in the repository tree; the existing canonical trip boundary is `ProtectionOutputService` → `TripBreakerCommand` → Application.
6. CT/PT/CVT engineering associations/scaling are implemented through the existing MeasurementGeneration boundary and covered by existing conversion-contract tests.
7. `50N/51N/27/59/46/49/67/87/21` still require explicit implementation-status mapping and non-fabrication verification.
8. UI is deferred until Core/Application boundaries are complete.
