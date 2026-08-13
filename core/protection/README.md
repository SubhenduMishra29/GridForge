# GridForge V2 Protection Subsystem

## Overview

The `core/protection/` package provides the protection-system execution
framework for GridForge V2.

The subsystem is responsible for representing, executing, and collecting
results from protection functions while maintaining a strict separation
between:

- physical equipment;
- measurement infrastructure;
- protection-function logic;
- protection decisions;
- protection schemes;
- breaker/output operation.

The protection subsystem is designed for multifunction protection
architecture.

A physical Relay is therefore **not** assumed to represent one protection
function.

A single Relay may host multiple independent protection functions:

```text
Relay R1
│
├── 50  Instantaneous Overcurrent
├── 51  Time Overcurrent
├── 46  Negative Sequence
├── 67  Directional Overcurrent
└── 50BF Breaker Failure
Each function is represented and executed independently while referencing
the same authoritative physical Relay.

Architectural Position

The protection subsystem sits between the measurement/model layers and the
protection output/scheme layer.

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

The protection subsystem does not directly operate physical equipment.

Core Architectural Principle

The fundamental V2 relationship is:

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

This deliberately avoids the V1 assumption:

Relay = One Protection Function

Instead:

Relay = Physical Protection Device

ProtectionElement = One Function Instance Hosted by the Relay

RelayBase = Executable Function Contract

This permits realistic multifunction relay configurations.

Package Structure

The current protection foundation consists of:

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

The package is intentionally divided into stable architectural contracts
rather than putting all protection logic into a single protection.py
module.

Module Responsibilities
context.py

Defines:

ProtectionContext

ProtectionContext is the immutable execution-time context supplied to a
protection function.

It may contain:

evaluation time;
timestep;
event identifier;
event type;
authoritative network-state reference;
authoritative simulation-state reference;
supervision information;
execution metadata.

It does not own or duplicate system state.

Example:

context = ProtectionContext(
    time=simulation_time,
    timestep=simulation_timestep,
    event_id="FAULT_001",
    event_type="FAULT",
)

The context does not own a clock.

The caller supplies the evaluation time.

decision.py

Defines:

ProtectionDecision

A ProtectionDecision is the authoritative result of one protection
function evaluation.

The major decision states are deliberately separated:

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

Additional states include:

blocked
valid

The distinction is important.

A function may:

pickup = True
operate = False
trip_request = False

For example, a time-overcurrent function may have picked up but not yet
completed its operating delay.

Likewise, a function can produce an operating decision without directly
changing breaker state.

A decision therefore represents protection logic state, not equipment
state.

relay_input.py

Defines:

RelayInput

RelayInput is the protection-facing binding to an authoritative
MeasurementChannel.

The measurement architecture is:

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

RelayInput does not:

own measurement state;
calculate CT ratios;
calculate PT ratios;
perform scaling;
perform polarity transformation;
simulate measurements;
model CT/PT/CVT equipment.

The authoritative measurement remains the responsibility of the
measurement subsystem.

Example:

IA ──> MeasurementChannel
IB ──> MeasurementChannel
IC ──> MeasurementChannel

A 50/51 function can therefore consume:

self.get_input("IA")
self.get_input("IB")
self.get_input("IC")

without owning the underlying measurement channels.

relay_base.py

Defines:

RelayBase

RelayBase is the abstract executable protection-function contract.

One instance represents one protection function.

Examples:

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

A concrete function derives from RelayBase:

class Overcurrent51(RelayBase):
    ...

The required execution interface is:

decision = function.evaluate(context)

The function must return a:

ProtectionDecision

The protection function must not directly perform:

breaker.open()
breaker.trip()
switch.open()
network.topology_change()

The function produces a decision.

Downstream layers interpret that decision.

protection_element.py

Defines:

ProtectionElement
ProtectionElementState

ProtectionElement is the composition boundary connecting:

Physical Relay
      │
      ▼
ProtectionElement
      │
      ▼
RelayBase

It owns:

protection-element identity;
physical Relay reference;
protection-function reference;
function classification;
enable/disable state;
execution priority;
element lifecycle state;
latest protection decision;
element metadata.

It does not own:

physical Relay state;
measurement channels;
CT/PT/CVT state;
protection mathematics;
breaker operation;
network topology;
system-wide coordination.
Protection Element Identity

A critical distinction is maintained between:

relay_id

and:

element_id

For example:

Physical Relay:
    RLY-001

Protection elements:

    RLY-001-50
    RLY-001-51
    RLY-001-46
    RLY-001-50BF

The physical Relay remains one authoritative equipment object.

Each protection function receives its own stable function-instance identity.

Protection Element State

ProtectionElementState provides orchestration-level state:

DISABLED
IDLE
PICKUP
OPERATED
TRIPPED
BLOCKED
FAILED

These states do not replace ProtectionDecision.

The complete decision remains available through:

element.last_decision

This prevents loss of protection information such as:

pickup;
operation;
trip request;
blocking;
validity;
reason;
measured values;
diagnostic values.
protection_system.py

Defines:

ProtectionSystem

ProtectionSystem is the system-level orchestration service.

Its responsibilities include:

protection-element registration;
element removal;
element lookup;
multifunction-relay grouping;
deterministic execution ordering;
evaluation;
reset;
decision collection;
status reporting;
compatibility views.

Example:

system = ProtectionSystem()

system.add_element(
    overcurrent_element
)

system.add_element(
    distance_element
)

The system can then identify all functions belonging to a physical Relay:

system.elements_for_relay(relay_id)
Multifunction Relay Architecture

The architecture explicitly supports:

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

The measurement architecture can simultaneously be:

CT-A ──> MeasurementChannel IA ──┐
CT-B ──> MeasurementChannel IB ──┤
CT-C ──> MeasurementChannel IC ──┤
                                 │
                                 ├──> RelayInput
                                 │
                                 ├──> 51
                                 ├──> 67
                                 └──> 46

Measurements are therefore not duplicated merely because several
protection functions consume them.

Execution Flow

A typical evaluation follows:

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

The protection subsystem ends at the protection-decision/orchestration
boundary.

Measurement Ownership

Measurement ownership is deliberately separated.

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

The protection function must not create its own:

CT state
PT state
VT state
CVT state
scaled measurement cache

This prevents different protection functions from developing inconsistent
copies of the same electrical measurement.

Decision Ownership

Protection decisions follow:

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

ProtectionDecision is immutable.

It represents the result of one evaluation.

It does not operate equipment.

Breaker Operation Boundary

Protection logic must not directly operate breakers.

The intended architecture is:

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

This separation is essential for supporting:

breaker trip delays;
breaker failure;
trip circuit supervision;
interlocking;
permissive schemes;
blocking;
transfer trip;
autoreclose;
event sequencing;
multi-breaker schemes.
What This Package Does Not Do

The protection package is deliberately not a power-system solver.

It does not perform:

Y-bus construction
Load flow
Short circuit calculation
Power flow
Network topology calculation
Fault calculation
Generator dynamics
Transient stability
EMT simulation

Those responsibilities belong to their respective GridForge subsystems.

Similarly, this package does not own:

Physical Relay model
Breaker model
CT model
PT model
CVT model
MeasurementChannel model
Network topology
GUI state
Project persistence
Protection Function Plugins

Concrete protection functions should derive from RelayBase.

For example:

from core.protection import RelayBase

A function implementation may then define:

class Overcurrent51(RelayBase):

    def evaluate(self, context):
        ...

The implementation is responsible for:

interpreting its assigned inputs;
applying its function-specific settings;
maintaining its transient runtime state;
evaluating the protection criterion;
producing ProtectionDecision.

It is not responsible for:

finding its own measurement channels;
operating breakers;
modifying topology;
coordinating other relays.
Example Function Architecture

A simplified 51 function might conceptually look like:

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

The function should never directly perform:

breaker.trip()

Instead:

return ProtectionDecision(...)
Deterministic Execution

ProtectionSystem executes elements in deterministic order.

The ordering mechanism is based on the protection-element priority and
element identity.

This priority is an execution ordering mechanism only.

It must not be interpreted as:

relay coordination;
time grading;
protection selectivity;
fault-clearing priority.

Actual protection coordination belongs to the coordination layer.

Static Blocking vs Dynamic Supervision

The architecture distinguishes local/static blocking from contextual
supervision.

RelayBase may contain a local:

blocked

state.

However, dynamic conditions such as:

permissive
interlock
scheme block
test mode
breaker status
communication supervision

should be supplied through the appropriate execution/scheme context.

They should not be hidden inside RelayBase.

Runtime State

Protection functions may require transient state.

Examples include:

pickup timer
integrator
memory polarization
previous current
previous voltage
sequence history
thermal accumulation
frequency estimation state
breaker-failure timer

This state belongs to the protection-function instance:

self._runtime

It is separate from persistent configuration:

self._settings

Conceptually:

Protection Function
│
├── Configuration
│      └── settings
│
└── Runtime
       └── transient execution state

Runtime state is not the authoritative project persistence model.

Reset Semantics

Calling:

element.reset()

or:

system.reset()

resets protection-function runtime state.

It does not reset:

the physical Relay;
measurement channels;
CT/PT/CVT state;
breaker state;
network topology;
protection scheme state.

This distinction is necessary for deterministic simulation and event
processing.

Public API

The package exports the stable protection contracts:

from core.protection import (
    ProtectionContext,
    ProtectionDecision,
    RelayInput,
    RelayBase,
    ProtectionElement,
    ProtectionElementState,
    ProtectionSystem,
)

The package intentionally does not expose every concrete protection
function through core.protection.

Concrete functions should remain in their dedicated modules or plugin
packages.

Compatibility Views

ProtectionSystem provides compatibility views such as:

system.oc_relays
system.distance_relays

These are compatibility interfaces only.

They are not authoritative storage.

New code should prefer:

system.elements_by_type("OVERCURRENT")

or:

system.elements_by_type("DISTANCE")

This preserves the multifunction-relay architecture.

Architectural Invariants

The following invariants should be preserved throughout GridForge V2.

1. One physical Relay may host multiple functions
Relay ≠ Protection Function
2. Measurement state has one authoritative owner
MeasurementChannel

Protection functions must not maintain duplicate measurement state.

3. RelayBase represents one executable function
RelayBase = Protection Function

not physical equipment.

4. ProtectionElement is a composition boundary
Relay + RelayBase

are connected through ProtectionElement.

5. ProtectionDecision represents logic state

It does not represent physical breaker state.

6. Protection functions do not operate breakers
ProtectionDecision
        ↓
Output / Scheme
        ↓
BreakerManager
7. ProtectionContext does not own system state

It carries references and evaluation-time information.

8. Runtime state is separate from configuration

Transient protection state must not be confused with persistent
protection settings.

9. Coordination is a separate concern

Protection execution priority is not protection coordination.

10. The GUI is outside the protection core

No protection object should depend on GUI state or GUI services.

Dependency Direction

The intended dependency direction is:

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

The protection package must not depend on GUI implementation.

Likewise, concrete protection functions should consume authoritative
measurements and context rather than reaching into unrelated solver
internals.

Future Expansion

The architecture is intentionally prepared for additional protection
domains.

Potential future functions include:

50      Instantaneous Overcurrent
51      Time Overcurrent
50N     Instantaneous Earth Fault
51N     Time Earth Fault
67      Directional Overcurrent
67N     Directional Earth Fault

21      Distance
21G     Ground Distance

27      Undervoltage
59      Overvoltage
47      Negative Sequence Voltage

32      Reverse Power
40      Loss of Excitation
46      Negative Sequence Current

81U     Underfrequency
81O     Overfrequency

87B     Bus Differential
87T     Transformer Differential
87G     Generator Differential

25      Synchronism Check
50BF    Breaker Failure
79      Autoreclose

These functions should be added as implementations of the established
protection contracts rather than by modifying the architectural role of
RelayBase, ProtectionElement, or ProtectionSystem.

Design Philosophy

GridForge V2 protection follows a layered engineering model:

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

Each layer has a distinct responsibility.

This prevents protection logic from becoming tightly coupled to
equipment models, measurement implementation, solver internals, or GUI
state.

The result is a protection subsystem capable of supporting both simple
single-function relays and realistic multifunction numerical relays while
remaining suitable for future:

relay coordination;
TCC analysis;
protection schemes;
event-driven simulation;
transient protection studies;
breaker failure;
autoreclose;
communication-assisted protection;
real-time execution.
Current Foundation Status

The following protection foundation files are considered the V2 baseline:

core/protection/
├── __init__.py
├── context.py
├── decision.py
├── relay_input.py
├── relay_base.py
├── protection_element.py
└── protection_system.py

These files establish the protection framework, not the complete set
of engineering protection functions.

Concrete functions should be implemented on top of this foundation.

Summary

The GridForge V2 protection subsystem is based on five fundamental
separations:

Physical Relay
       ≠
Protection Function

Measurement
       ≠
Protection Logic

Protection Decision
       ≠
Trip Command

Trip Command
       ≠
Breaker Operation

Execution Priority
       ≠
Protection Coordination

The resulting architecture is:

             Physical Relay
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
 ProtectionElement     ProtectionElement
          │                 │
          ▼                 ▼
      RelayBase          RelayBase
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

This is the architectural foundation for GridForge V2 protection.


**`core/protection/README.md` → FINALIZE / FREEZE** as the package-level architectural documentation.
