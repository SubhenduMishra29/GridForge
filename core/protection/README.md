# GridForge V2 Protection Subsystem

## Overview

The `core/protection/` package provides the protection-system execution framework for GridForge V2.

The subsystem is responsible for representing, executing, and collecting results from protection functions while maintaining a strict separation between:

* physical equipment;
* measurement infrastructure;
* protection-function logic;
* protection decisions;
* protection schemes;
* breaker/output operation.

The protection subsystem is designed for **multifunction protection architecture**.

A physical **Relay** is therefore **not** assumed to represent one protection function.

A single relay may host multiple independent protection functions:

```text
Relay R1
│
├── 50      Instantaneous Overcurrent
├── 51      Time Overcurrent
├── 46      Negative Sequence
├── 67      Directional Overcurrent
└── 50BF    Breaker Failure
```

Each function is represented and executed independently while referencing the same authoritative physical Relay.

---

# 1. Architectural Position

The protection subsystem sits between the measurement/model layers and the protection output/scheme layer.

```text
                    Physical System
                          │
          ┌───────────────┴────────────────┐
          │                                │
          ▼                                ▼
     Physical Relay                 CT / PT / CVT
          │                                │
          │                                ▼
          │                       MeasurementChannel
          │                                │
          │                                ▼
          │                          RelayInput
          │                                │
          └───────────────┬────────────────┘
                          │
                          ▼
                   ProtectionElement
                          │
                          ▼
                      RelayBase
                          │
                          ▼
                 ProtectionContext
                          │
                          ▼
                ProtectionDecision
                          │
                          ▼
                 ProtectionSystem
                          │
                          ▼
              Protection Scheme /
                Output Logic
                          │
                          ▼
                  Trip Command
                          │
                          ▼
                 BreakerManager
                          │
                          ▼
                  Physical Breaker
```

The protection subsystem does **not** directly operate physical equipment.

---

# 2. Core Architectural Principle

The fundamental V2 relationship is:

```text
Physical Relay
     │
     ├── ProtectionElement
     │       └── RelayBase
     │
     ├── ProtectionElement
     │       └── RelayBase
     │
     └── ProtectionElement
             └── RelayBase
```

This deliberately avoids the V1 assumption:

```text
Relay = One Protection Function
```

Instead:

```text
Relay = Physical Protection Device

ProtectionElement = One Function Instance Hosted by the Relay

RelayBase = Executable Protection-Function Contract
```

This permits realistic multifunction numerical relay configurations.

---

# 3. Package Structure

The protection foundation consists of:

```text
core/
└── protection/
    ├── __init__.py
    ├── README.md
    ├── context.py
    ├── decision.py
    ├── relay_input.py
    ├── relay_base.py
    ├── protection_element.py
    └── protection_system.py
```

The package is intentionally divided into stable architectural contracts rather than putting all protection logic into a single `protection.py` module.

---

# 4. Module Responsibilities

## 4.1 `context.py`

Defines:

```text
ProtectionContext
```

`ProtectionContext` is the immutable execution-time context supplied to a protection function.

It may contain:

* evaluation time;
* timestep;
* event identifier;
* event type;
* authoritative network-state reference;
* authoritative simulation-state reference;
* supervision information;
* execution metadata.

It does **not** own or duplicate system state.

Example:

```python
context = ProtectionContext(
    time=simulation_time,
    timestep=simulation_timestep,
    event_id="FAULT_001",
    event_type="FAULT",
)
```

The context does not own a clock.

The caller supplies the evaluation time.

---

## 4.2 `decision.py`

Defines:

```text
ProtectionDecision
```

A `ProtectionDecision` is the authoritative result of one protection-function evaluation.

The major decision states are deliberately separated:

```text
pickup
   │
   ├── criterion crossed
   │
   ▼
operate
   │
   ├── operating criterion satisfied
   │
   ▼
trip_request
   │
   └── downstream protection logic may issue a trip
```

Additional states include:

* `blocked`;
* `valid`.

The distinction is important.

A function may produce:

```text
pickup       = True
operate      = False
trip_request = False
```

For example, a time-overcurrent function may have picked up but not yet completed its operating delay.

Likewise, a function can produce an operating decision without directly changing breaker state.

Therefore:

```text
ProtectionDecision = Protection Logic State
```

and not:

```text
ProtectionDecision = Equipment State
```

---

## 4.3 `relay_input.py`

Defines:

```text
RelayInput
```

`RelayInput` is the protection-facing binding to an authoritative `MeasurementChannel`.

The measurement architecture is:

```text
CT / PT / CVT
      │
      ▼
MeasurementChannel
      │
      ▼
RelayInput
      │
      ▼
Protection Function
```

`RelayInput` does **not**:

* own measurement state;
* calculate CT ratios;
* calculate PT ratios;
* perform scaling;
* perform polarity transformation;
* simulate measurements;
* model CT/PT/CVT equipment.

The authoritative measurement remains the responsibility of the measurement subsystem.

Example:

```text
IA ──> MeasurementChannel
IB ──> MeasurementChannel
IC ──> MeasurementChannel
```

A 50/51 function can therefore consume:

```python
self.get_input("IA")
self.get_input("IB")
self.get_input("IC")
```

without owning the underlying measurement channels.

> **Architectural rule:** Measurement infrastructure is authoritative. Protection functions consume measurements; they do not recreate them.

---

## 4.4 `relay_base.py`

Defines:

```text
RelayBase
```

`RelayBase` is the abstract executable protection-function contract.

One instance represents **one protection function**.

Examples include:

```text
50
51
21
27
32
46
50BF
59
67
81U
87B
87T
```

A concrete function derives from `RelayBase`:

```python
class Overcurrent51(RelayBase):
    ...
```

The required execution interface is:

```python
decision = function.evaluate(context)
```

The function must return a:

```text
ProtectionDecision
```

The protection function must **not** directly perform:

```python
breaker.open()
breaker.trip()
switch.open()
network.topology_change()
```

The function produces a decision.

Downstream layers interpret that decision.

---

## 4.5 `protection_element.py`

Defines:

```text
ProtectionElement
ProtectionElementState
```

`ProtectionElement` is the composition boundary connecting:

```text
Physical Relay
      │
      ▼
ProtectionElement
      │
      ▼
RelayBase
```

It owns:

* protection-element identity;
* physical Relay reference;
* protection-function reference;
* function classification;
* enable/disable state;
* execution priority;
* element lifecycle state;
* latest protection decision;
* element metadata.

It does **not** own:

* physical Relay state;
* measurement channels;
* CT/PT/CVT state;
* protection mathematics;
* breaker operation;
* network topology;
* system-wide coordination.

---

# 5. Protection Element Identity

A critical distinction is maintained between:

```text
relay_id
```

and:

```text
element_id
```

For example:

```text
Physical Relay:
    RLY-001

Protection Elements:
    RLY-001-50
    RLY-001-51
    RLY-001-46
    RLY-001-50BF
```

The physical Relay remains one authoritative equipment object.

Each protection function receives its own stable function-instance identity.

---

# 6. Protection Element State

`ProtectionElementState` provides orchestration-level state:

```text
DISABLED
IDLE
PICKUP
OPERATED
TRIPPED
BLOCKED
FAILED
```

These states do **not** replace `ProtectionDecision`.

The complete decision remains available through:

```python
element.last_decision
```

This prevents loss of protection information such as:

* pickup;
* operation;
* trip request;
* blocking;
* validity;
* reason;
* measured values;
* diagnostic values.

---

# 7. `protection_system.py`

Defines:

```text
ProtectionSystem
```

`ProtectionSystem` is the system-level orchestration service.

Its responsibilities include:

* protection-element registration;
* element removal;
* element lookup;
* multifunction-relay grouping;
* deterministic execution ordering;
* evaluation;
* reset;
* decision collection;
* status reporting;
* compatibility views.

Example:

```python
system = ProtectionSystem()

system.add_element(overcurrent_element)
system.add_element(distance_element)
```

The system can identify all functions belonging to a physical Relay:

```python
system.elements_for_relay(relay_id)
```

---

# 8. Multifunction Relay Architecture

The architecture explicitly supports:

```text
Relay R1
│
├── ProtectionElement
│       │
│       └── RelayBase: 51
│
├── ProtectionElement
│       │
│       └── RelayBase: 67
│
├── ProtectionElement
│       │
│       └── RelayBase: 21
│
└── ProtectionElement
        │
        └── RelayBase: 50BF
```

The measurement architecture can simultaneously be:

```text
CT-A ──> MeasurementChannel IA ──┐
CT-B ──> MeasurementChannel IB ──┤
CT-C ──> MeasurementChannel IC ──┤
                                 │
                                 ├──> RelayInput
                                 │
                                 ├──> 51
                                 ├──> 67
                                 └──> 46
```

Measurements are therefore **not duplicated** merely because several protection functions consume them.

---

# 9. Execution Flow

A typical evaluation follows:

```text
1. Solver / simulation produces authoritative system state
                         │
                         ▼
2. Measurement subsystem updates MeasurementChannels
                         │
                         ▼
3. RelayInputs expose measurement values
                         │
                         ▼
4. ProtectionSystem evaluates enabled elements
                         │
                         ▼
5. ProtectionElement invokes RelayBase.evaluate()
                         │
                         ▼
6. RelayBase evaluates its protection algorithm
                         │
                         ▼
7. RelayBase produces ProtectionDecision
                         │
                         ▼
8. ProtectionElement records the decision
                         │
                         ▼
9. ProtectionSystem collects decisions
                         │
                         ▼
10. Protection Scheme / Output layer interprets them
                         │
                         ▼
11. Trip command may be generated
                         │
                         ▼
12. BreakerManager operates physical breaker
```

The protection subsystem ends at the **protection-decision/orchestration boundary**.

---

# 10. Measurement Ownership

Measurement ownership is deliberately separated.

```text
Physical Instrument
       │
       ▼
Measurement Infrastructure
       │
       ▼
MeasurementChannel
       │
       ▼
RelayInput
       │
       ▼
Protection Function
```

The protection function must not create its own:

* CT state;
* PT state;
* VT state;
* CVT state;
* scaled measurement cache.

This prevents different protection functions from developing inconsistent copies of the same electrical measurement.

The authoritative measurement infrastructure is located in the GridForge measurement subsystem.

---

# 11. Decision Ownership

Protection decisions follow:

```text
RelayBase
    │
    ▼
ProtectionDecision
    │
    ▼
ProtectionElement
    │
    ▼
ProtectionSystem
```

`ProtectionDecision` is immutable.

It represents the result of one evaluation.

It does not operate equipment.

---

# 12. Breaker Operation Boundary

Protection logic must not directly operate breakers.

The intended architecture is:

```text
Protection Function
        │
        ▼
ProtectionDecision
        │
        ▼
Protection Scheme / Output Logic
        │
        ▼
Trip Command
        │
        ▼
BreakerManager
        │
        ▼
Physical Breaker
```

This separation is essential for supporting:

* breaker trip delays;
* breaker failure;
* trip-circuit supervision;
* interlocking;
* permissive schemes;
* blocking;
* transfer trip;
* autoreclose;
* event sequencing;
* multi-breaker schemes.

---

# 13. What This Package Does Not Do

The protection package is deliberately **not** a power-system solver.

It does not perform:

* Y-bus construction;
* load flow;
* short-circuit calculation;
* power flow;
* network topology calculation;
* fault calculation;
* generator dynamics;
* transient stability;
* EMT simulation.

Those responsibilities belong to their respective GridForge subsystems.

Similarly, this package does not own:

* Physical Relay model;
* Breaker model;
* CT model;
* PT model;
* CVT model;
* MeasurementChannel model;
* Network topology;
* GUI state;
* project persistence.

---

# 14. Protection Function Plugins

Concrete protection functions should derive from `RelayBase`.

For example:

```python
from core.protection import RelayBase


class Overcurrent51(RelayBase):

    def evaluate(self, context):
        ...
```

A function implementation is responsible for:

* interpreting its assigned inputs;
* applying its function-specific settings;
* maintaining its transient runtime state;
* evaluating the protection criterion;
* producing `ProtectionDecision`.

It is **not** responsible for:

* finding its own measurement channels;
* operating breakers;
* modifying topology;
* coordinating other relays.

---

# 15. Example Function Architecture

A simplified 51 function might conceptually look like:

```text
Overcurrent51
│
├── RelayBase
│
├── Settings
│   ├── pickup
│   ├── curve
│   └── TMS
│
├── RelayInputs
│   ├── IA
│   ├── IB
│   └── IC
│
├── Runtime
│   └── operating_time / timer
│
└── evaluate(context)
        │
        ▼
ProtectionDecision
```

The function should never directly perform:

```python
breaker.trip()
```

Instead:

```python
return ProtectionDecision(...)
```

---

# 16. Deterministic Execution

`ProtectionSystem` executes elements in deterministic order.

The ordering mechanism is based on:

1. protection-element priority;
2. element identity as the deterministic tie-breaker.

Execution priority is an **execution-ordering mechanism only**.

It must not be interpreted as:

* relay coordination;
* time grading;
* protection selectivity;
* fault-clearing priority.

Actual protection coordination belongs to the coordination layer.

---

# 17. Static Blocking vs Dynamic Supervision

The architecture distinguishes local/static blocking from contextual supervision.

`RelayBase` may contain a local:

```text
blocked
```

state.

However, dynamic conditions such as:

* permissive;
* interlock;
* scheme block;
* test mode;
* breaker status;
* communication supervision;

should be supplied through the appropriate execution or scheme context.

They should not be hidden inside `RelayBase`.

---

# 18. Runtime State

Protection functions may require transient state.

Examples include:

* pickup timer;
* integrator;
* memory polarization;
* previous current;
* previous voltage;
* sequence history;
* thermal accumulation;
* frequency estimation state;
* breaker-failure timer.

This state belongs to the protection-function instance:

```python
self._runtime
```

It is separate from persistent configuration:

```python
self._settings
```

Conceptually:

```text
Protection Function
│
├── Configuration
│      └── settings
│
└── Runtime
       └── transient execution state
```

Runtime state is not the authoritative project-persistence model.

---

# 19. Reset Semantics

Calling:

```python
element.reset()
```

or:

```python
system.reset()
```

resets protection-function runtime state.

It does **not** reset:

* the physical Relay;
* measurement channels;
* CT/PT/CVT state;
* breaker state;
* network topology;
* protection scheme state.

This distinction is necessary for deterministic simulation and event processing.

---

# 20. Public API

The package exports the stable protection contracts:

```python
from core.protection import (
    ProtectionContext,
    ProtectionDecision,
    RelayInput,
    RelayBase,
    ProtectionElement,
    ProtectionElementState,
    ProtectionSystem,
)
```

The package intentionally does **not** expose every concrete protection function through `core.protection`.

Concrete functions should remain in their dedicated modules or plugin packages.

---

# 21. Compatibility Views

`ProtectionSystem` provides compatibility views such as:

```python
system.oc_relays
system.distance_relays
```

These are compatibility interfaces only.

They are **not authoritative storage**.

New code should prefer:

```python
system.elements_by_type("OVERCURRENT")
```

or:

```python
system.elements_by_type("DISTANCE")
```

This preserves the multifunction-relay architecture.

---

# 22. Architectural Invariants

The following invariants must be preserved throughout GridForge V2.

### 22.1 One Physical Relay May Host Multiple Functions

```text
Relay ≠ Protection Function
```

A physical Relay may contain multiple `ProtectionElement` instances.

---

### 22.2 Measurement State Has One Authoritative Owner

```text
MeasurementChannel
```

Protection functions must not maintain duplicate authoritative measurement state.

---

### 22.3 `RelayBase` Represents One Executable Function

```text
RelayBase = Protection Function
```

It does not represent physical equipment.

---

### 22.4 `ProtectionElement` Is the Composition Boundary

```text
Physical Relay + RelayBase
             │
             ▼
    ProtectionElement
```

The element connects the physical relay identity with one executable protection-function instance.

---

### 22.5 `ProtectionDecision` Represents Logic State

```text
ProtectionDecision ≠ Breaker State
```

A protection decision does not represent physical breaker operation.

---

### 22.6 Protection Functions Do Not Operate Breakers

The required direction is:

```text
ProtectionDecision
        ↓
Output / Scheme
        ↓
BreakerManager
```

---

### 22.7 `ProtectionContext` Does Not Own System State

It carries references and evaluation-time information.

It does not become a second system-state container.

---

### 22.8 Runtime State Is Separate from Configuration

Transient protection state must not be confused with persistent protection settings.

```text
Configuration ≠ Runtime
```

---

### 22.9 Coordination Is a Separate Concern

```text
Execution Priority ≠ Protection Coordination
```

Execution priority controls deterministic evaluation order.

Protection coordination belongs to the coordination subsystem.

---

### 22.10 The GUI Is Outside the Protection Core

No protection object should depend on:

* GUI state;
* GUI widgets;
* GUI services;
* rendering infrastructure.

---

# 23. Dependency Direction

The intended dependency direction is:

```text
core.model
    │
    ▼
measurement infrastructure
    │
    ▼
core.protection
    │
    ▼
protection schemes / output logic
    │
    ▼
breaker/control orchestration
```

The protection package must not depend on GUI implementation.

Likewise, concrete protection functions should consume authoritative measurements and execution context rather than reaching directly into unrelated solver internals.

---

# 24. Future Expansion

The architecture is intentionally prepared for additional protection domains.

## Overcurrent and Directional

```text
50      Instantaneous Overcurrent
51      Time Overcurrent
50N     Instantaneous Earth Fault
51N     Time Earth Fault
67      Directional Overcurrent
67N     Directional Earth Fault
```

## Distance

```text
21      Distance
21G     Ground Distance
```

## Voltage

```text
27      Undervoltage
59      Overvoltage
47      Negative Sequence Voltage
```

## Power and Sequence

```text
32      Reverse Power
40      Loss of Excitation
46      Negative Sequence Current
```

## Frequency

```text
81U     Underfrequency
81O     Overfrequency
```

## Differential

```text
87B     Bus Differential
87T     Transformer Differential
87G     Generator Differential
```

## Control and Special Protection

```text
25      Synchronism Check
50BF    Breaker Failure
79      Autoreclose
```

These functions should be added as implementations of the established protection contracts rather than by modifying the architectural role of:

* `RelayBase`;
* `ProtectionElement`;
* `ProtectionSystem`.

---

# 25. Design Philosophy

GridForge V2 protection follows a layered engineering model:

```text
Equipment
    ↓
Measurement
    ↓
Protection Function
    ↓
Protection Decision
    ↓
Protection Scheme
    ↓
Trip Command
    ↓
Physical Operation
```

Each layer has a distinct responsibility.

This prevents protection logic from becoming tightly coupled to:

* equipment models;
* measurement implementation;
* solver internals;
* GUI state.

The resulting architecture is capable of supporting both:

* simple single-function relays;
* realistic multifunction numerical relays.

It is also suitable for future:

* relay coordination;
* TCC analysis;
* protection schemes;
* event-driven simulation;
* transient protection studies;
* breaker failure;
* autoreclose;
* communication-assisted protection;
* real-time execution.

---

# 26. Current Foundation Status

The following protection foundation files constitute the GridForge V2 protection baseline:

```text
core/protection/
├── __init__.py
├── context.py
├── decision.py
├── relay_input.py
├── relay_base.py
├── protection_element.py
└── protection_system.py
```

These files establish the **protection framework and architectural contracts**, not the complete set of engineering protection functions.

Concrete protection functions should be implemented on top of this foundation.

---

# 27. Summary

The GridForge V2 protection subsystem is based on five fundamental separations:

```text
Physical Relay
       ≠
Protection Function
```

```text
Measurement
       ≠
Protection Logic
```

```text
Protection Decision
       ≠
Trip Command
```

```text
Trip Command
       ≠
Breaker Operation
```

```text
Execution Priority
       ≠
Protection Coordination
```

The resulting architecture is:

```text
                    Physical Relay
                          │
                 ┌────────┴────────┐
                 │                 │
                 ▼                 ▼
        ProtectionElement   ProtectionElement
                 │                 │
                 ▼                 ▼
             RelayBase         RelayBase
                 │                 │
                 └───────┬─────────┘
                         │
                   RelayInput(s)
                         │
                 MeasurementChannel
                         │
                         ▼
              ProtectionDecision
                         │
                         ▼
                ProtectionSystem
                         │
                         ▼
              Scheme / Output Logic
                         │
                         ▼
                   Trip Command
                         │
                         ▼
                 BreakerManager
                         │
                         ▼
                Physical Equipment
```

This architecture forms the foundation for GridForge V2 protection.

It preserves clear ownership boundaries, supports multifunction numerical relays, prevents duplicated measurement state, separates protection decisions from physical operation, and provides a stable foundation for future protection functions, coordination, schemes, event processing, and real-time execution.

---

## Freeze Status

**`core/protection/README.md` → FINALIZE / FREEZE**

This document is the package-level architectural reference for the GridForge V2 protection foundation.

Changes to the protection architecture should preserve the invariants and dependency boundaries defined in this document.
