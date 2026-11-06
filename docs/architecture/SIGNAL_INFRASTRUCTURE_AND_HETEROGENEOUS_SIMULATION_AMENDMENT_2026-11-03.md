# GridForge V2 — Signal Infrastructure and Heterogeneous Simulation Architecture Amendment

**Decision date:** 3 November 2026  
**Repository authority:** `SubhenduMishra29/GridForge`, branch `main`  
**Status:** Approved architectural direction; implementation and runtime verification remain separate  
**Relationship:** Additive amendment to `GRIDFORGE_V2_ARCHITECTURE_2026-11-02.md`. It does not replace or reopen frozen Core, Application, UI, SLD, Protection, Control, persistence or plugin boundaries.

## 1. Purpose

Define one coherent lifecycle for physical and simulated measurements, their acquisition and distribution to Protection and Control, device actuation and feedback, historical recording, and CPU/GPU/NPU-accelerated equipment simulation.

The central principle is:

> One shared Signal and Measurement Infrastructure; separate Protection and Control execution systems; a common device command/feedback boundary; a common Historian; and hardware-independent equipment physics models executed by a heterogeneous runtime.

## 2. Signal and measurement lifecycle

The canonical lifecycle is:

```text
Physical instrument OR virtual instrument
  → acquisition interface / channel
  → typed measurement conversion and processing
  → canonical SignalValue + quality + timestamp + provenance
  → signal routing / subscriptions
  → Protection and/or Control consumers
  → decision evaluation
  → Application-authorized device command
  → physical or simulated actuator response
  → device feedback acquisition
  → event and time-series recording
  → SCADA / HMI projections
```

The Historian is an observer of the lifecycle, not merely a terminal stage. It records measurements, quality changes, decisions, commands, output execution, feedback, alarms and events.

### 2.1 Instrument and channel families

Support distinct acquisition contracts rather than treating all instruments as generic analog inputs:

- CT and PT/CVT secondary measurement interfaces, with explicit ratios, polarity, phase/terminal association, burden/interface semantics and appropriate isolation.
- RTD and thermocouple temperature acquisition.
- Analog inputs such as 4–20 mA and voltage transducers.
- Digital inputs for contacts, limit switches, breaker auxiliary contacts and equipment status.
- Analog and digital outputs for actuators and command interfaces.
- Communication-derived values, including supported IEC 61850 Sampled Values, GOOSE and other protocol adapters where explicitly implemented.
- Virtual instruments that derive measurements from simulation model outputs while preserving the same downstream measurement contract.

BTD, OTD and WTD are instrument/application designations whose actual sensing element and acquisition interface must be explicitly configured; do not assume every such detector is inherently an RTD.

CT/VT safety and wiring constraints must be represented in engineering configuration and diagnostics. In particular, a live CT secondary must not be left open-circuited; PT secondary circuits require suitable protection.

### 2.2 Canonical measurement contracts

The shared domain vocabulary should include, subject to reconciliation with existing implementations before introducing duplicate classes:

- `Instrument` / `SignalSource`
- `IOHardware` / `IOChannel`
- `MeasurementChannel`
- `Signal` / `SignalRoute` / `SignalSubscription`
- `SignalValue` carrying value, engineering unit, timestamp, quality, source identity and provenance
- consumer-side `ProtectionInput` and `ControlInput`
- `ControlOutput`
- `DeviceCommand` and `DeviceFeedback`
- `HistorianRecord`, `AlarmEvent`, `SequenceOfEventsRecord` and `DisturbanceRecord`

Do not create a parallel measurement authority inside Control or Protection. Both consume compatible canonical signals through their own domain-facing contracts.

### 2.3 Signal quality and failure semantics

Signal quality is mandatory metadata, not an optional decoration. The contract must represent at least good, bad, uncertain, stale, communication-lost, out-of-range and not-configured states (exact enum vocabulary to reconcile with current code).

Missing or invalid measurements must never silently become numeric zero. Protection and Control define explicit per-function/per-loop behavior for invalid, stale or unavailable inputs. Protection behavior is fail-closed where required by the protection function and approved engineering policy; no generic policy may accidentally suppress a required trip. Input freshness, time quality, range, calibration and source provenance are available to consumers.

## 3. Separate Protection and Control execution

A measurement can be subscribed to by multiple consumers, but processing and decision ownership remain separate:

- Protection evaluates relay functions/elements and creates a typed `ProtectionDecision`.
- Control evaluates PLC/logic/PID/sequencing/interlocks and creates a control decision/request.
- SCADA/HMI presents live state and operator workflows; it is not the authoritative protection or control execution engine.
- Historian records values and lifecycle events without becoming the decision authority.

Protection-to-Control and Control-to-Protection signals are explicit engineered interfaces (for example trip status, lockout, blocking, permissive and interlock signals). They are not implicit cross-domain object mutation.

## 4. Device command, actuation and feedback

A decision is not an operation. Keep these facts distinct and traceable:

1. protection/control decision or request;
2. Application-authorized `DeviceCommand`;
3. command routing and output-channel activation;
4. output circuit / actuator status where modeled;
5. physical or simulated device response;
6. acquired `DeviceFeedback` and postcondition reconciliation;
7. failure/timeout/discrepancy event where expected feedback is absent.

A ProtectionDecision must never be reported as a successful breaker trip by itself. Breaker position is reconciled from authoritative equipment state and feedback semantics, including 52a/52b where configured. Physical installations require appropriately engineered independent protection/trip circuits; a general-purpose desktop GridForge process is not the sole safety-critical protection controller.

## 5. Historian and event recording

Establish a shared Historian/Time-Series service with distinct recording policies:

- analog time-series values with configurable sampling, deadband, compression and quality;
- digital state changes;
- alarm lifecycle events;
- protection function evaluations and decisions;
- device commands, output activation and feedback;
- operator actions and audit events;
- high-resolution SOE records with source time-quality and clock provenance;
- high-speed pre-fault/post-fault waveform and disturbance records where the source supports them.

Sampling intervals are configurable by signal class and study/plant requirements; illustrative rates are not universal guarantees. Do not force all records into one sampling rate or one storage representation.

Every record must distinguish physical/live data from simulated data and preserve project, equipment, instrument, channel, source, timestamp/time-quality, model/version and simulation-run provenance as applicable. Historian storage and result archives remain separate from canonical project engineering state unless a deliberate persistence contract says otherwise.

## 6. Heterogeneous Engineering Simulation Runtime

Equipment physics models are hardware-independent. A single model contract defines initialization, input application, time advancement, state retrieval, output publication and reset/checkpoint semantics. Execution backends implement that contract; do not maintain separate CPU and GPU physics definitions.

Conceptual components, names subject to reconciliation with existing modules:

- `EquipmentSimulationModel` contract
- `SimulationModelRegistry`
- `SimulationBackend` contract
- `CPUBackend`, `GPUBackend`, `NPUBackend`
- `SimulationBackendRegistry` / capability registry
- `SimulationOrchestrator` and scheduler
- `SimulationExecutionPlan`
- `SimulationTimeManager`
- `SimulationStateBuffer` and `SimulationResult`
- profiling, diagnostics, checkpoint and failure-recovery interfaces

### 6.1 Backend responsibilities

**CPU — universal reference and fallback**

General numerical computation, orchestration, sequential/dependent workloads, small simulations, control/protection logic simulation, unsupported accelerator operations and reference numerical results. Candidate technologies include NumPy, SciPy and Numba where appropriate.

**GPU — parallel numerical physics**

Suitable batched equipment dynamics, parameter sweeps, scenario ensembles, large sparse/dense numerical workloads, thermal/electromagnetic discretizations and parallel solver kernels. NVIDIA CUDA/CuPy/PyTorch or other adapters are optional backend implementations, not domain dependencies.

**NPU — supported AI inference**

Predictive maintenance, anomaly detection, fault classification, condition monitoring and learned surrogate inference, only where model operators, precision, driver and device provider are supported. ONNX Runtime or vendor-specific providers may be used behind the backend contract. NPU output is advisory/analytical unless separately validated for a non-safety function; it must not replace deterministic protection calculations or make safety-critical trip decisions.

Backend selection depends on workload shape, supported operations, precision, memory, transfer cost, device availability and execution constraints. GPU/NPU are not selected merely because hardware exists.

### 6.2 Numerical and runtime guarantees

- CPU is the reference path; accelerated paths define and demonstrate numerical tolerances against it.
- Backend, device, precision, model version, solver/integrator, timestep and execution-plan provenance are recorded.
- Accelerator failure or loss must not corrupt authoritative model state; fallback is allowed only where state continuity and numerical semantics are valid, otherwise stop/mark the run failed with diagnostics.
- Use bounded batches and explicit memory budgets; avoid unbounded device copies.
- Simulation time is explicit and separate from wall-clock time.
- Synchronous dependencies, solver step barriers and data exchange are explicit.
- Ordinary desktop/Windows execution must not be advertised as hard real-time. Deadline misses and overruns are detected and reported.
- GUI event processing must not be the simulation scheduler or a protection execution dependency.
- HIL requires a separate interface, timing, isolation, watchdog and commissioning architecture.

## 7. Virtual instruments and closed-loop simulation

Virtual instruments publish through the same canonical MeasurementChannel/Signal contracts as physical instruments. Simulated actuators receive the same command contract and publish feedback through the same acquisition abstraction.

Reference closed-loop scenario:

```text
Induction motor physics (CPU/GPU)
  → virtual CT / PT / RTD / bearing-temperature / vibration instruments
  → acquisition and signal processing
  → canonical signals and quality
  → Protection and Control evaluation
  → Application command authorization/routing
  → simulated contactor or breaker response
  → motor model electrical/mechanical state transition
  → virtual auxiliary contacts and measurement feedback
  → Historian trends, SOE, alarms and operation trace
```

The simulation model must not bypass signal quality, routing, Protection/Control contracts, device command handling or Historian provenance. Physical and simulated sources are distinguishable, while their consumer interfaces remain compatible.

## 8. Integration with frozen GridForge boundaries

- Core owns authoritative domain models, typed signal/measurement semantics and equipment state; Core remains headless and imports no Qt/UI/graphics/plugin types.
- Application owns controlled mutation, command/transaction boundaries, orchestration, lifecycle, routing coordination, publication and persistence coordination. Reuse existing shared managers and services; do not duplicate them.
- Protection owns protection function evaluation and typed decisions.
- Control owns logic, controller, interlock and sequencing evaluation.
- Device management/application services own command routing and feedback reconciliation, without conflating decision and actuation.
- Plugins provide domain-aligned equipment physics, solvers, instrument adapters and AI models through public contracts; plugins do not create parallel managers or mutate Core directly.
- UI/SLD/Control canvas/Protection UI configure and visualize the model through Application. Canvas geometry is never a signal route or electrical topology authority.
- SCADA/HMI is an operator-facing projection and supervisory interaction layer.
- Historian is a shared service with source/time provenance and query/read-model contracts.

Existing universal UI mutation path remains unchanged:

```text
UI → Controller → Command → Application → Core → Event → Projection → UI
```

Acquisition and simulation execution use dedicated application/runtime pathways and do not synchronously depend on GUI event processing.

## 9. First reference implementation and acceptance scenario

Use the existing Motor Dynamics plugin as the first reference integration, reusing a shared physics/ODE/runtime foundation rather than building a plugin-specific execution stack.

The first end-to-end acceptance scenario should demonstrate:

1. configure a motor and its physical parameters;
2. run the same model on CPU and, where available, GPU;
3. produce motor electrical/mechanical/thermal states;
4. generate virtual CT/PT/RTD and selected status measurements;
5. route the measurements into Protection and Control;
6. evaluate a configured protection function and a separate control function;
7. issue a simulated contactor/breaker command through the common device boundary;
8. update motor physics from the simulated switching event;
9. acquire auxiliary feedback and reconcile command postconditions;
10. record analog trends, quality, protection/control events, commands, feedback and SOE with simulation provenance;
11. compare CPU and accelerated results against declared tolerances.

The NPU path is a separate AI-inference demonstration (for example temperature prediction or anomaly classification), with model/provider/device support and confidence/provenance exposed. It is not a prerequisite for CPU/GPU physics acceptance.

## 10. Delivery sequence

1. Audit existing measurement, channel, CT/PT/CVT, sensor, Control and Protection contracts; identify reuse and gaps.
2. Define canonical signal identity/value/quality/time/provenance and acquisition-channel contracts.
3. Implement signal routing/subscription and channel availability/diagnostics.
4. Reconcile device command/output/feedback lifecycle across Protection and Control.
5. Define Historian time-series, event, SOE and disturbance-record contracts.
6. Define hardware-independent simulation model and CPU reference runtime.
7. Integrate the Motor Dynamics plugin with the shared physics/runtime contracts.
8. Add GPU backend for measured suitable workloads and numerical equivalence checks.
9. Add NPU inference adapter for supported AI workloads.
10. Integrate virtual instruments and simulated actuators for the closed-loop scenario.
11. Add SCADA/HMI trend, event and diagnostic projections.

## 11. Change-control and evidence policy

This amendment establishes architectural direction; it does not assert that the listed contracts or workflows are implemented. Every implementation claim must identify source evidence and distinguish static inspection, runtime verification, numerical validation and production/HIL commissioning. Existing policy remains: do not add tests or CI as acceptance gates unless explicitly requested; perform the agreed source, syntax/import, boundary and diff checks and report exactly what was done.

Do not reopen the frozen Core/Application/UI/SLD architecture. Reconcile existing code before adding similarly named classes, services or managers. Record findings and corrections in the authoritative audit workflow:

```text
FETCH → AUDIT → RECONCILE → CORRECT → CHECK → FREEZE
```
