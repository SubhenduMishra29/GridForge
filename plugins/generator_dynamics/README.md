# Generator Dynamics Plugin

Initial engineering foundation for GridForge V2's universal generator plugin.

## Scope

- Diesel and gas engines, steam and gas turbines, hydro, wind (DFIG and
  full-converter), synchronous, induction, permanent-magnet, inverter-based,
  fuel-cell and microturbine families.
- Immutable nameplate and model parameter contracts.
- Synchronous-machine d/q transient and subtransient parameter validation.
- AVR/exciter, governor/actuator and prime-mover parameter contracts.
- Executable generic first-order AVR, TGOV1-style governor/turbine lag, and washout/lead-lag PSS models implementing the existing DynamicPlugin equation contract.
- Technology-specific instrumentation point templates.
- Explicit physical instrument/secondary-terminal mapping through Core's
  MeasurementProvisioning and canonical MeasurementChannel.
- Capability-gated CPU/GPU/NPU workload selection using Core's shared
  BackendCapability and select_backend policy.

## Measurement point rule

Templates are definitions, not live signals. Every point must be explicitly
mapped to a physical source instrument, its authoritative Core terminal, and
an EndpointReference. The Core provisioning boundary validates instrument
identity and secondary terminal ownership. Project-managed sample updates
remain owned by MeasurementChannelService.

The initial point catalogue includes three-phase current and voltage,
line-to-line voltage, neutral current, MW/MVAr/MVA, power factor, frequency,
phase angle, speed, torque, vibration, bearing/stator temperatures, field
voltage/current, governor reference/actuator, synchronizing quantities,
breaker/trip status, and family-specific fuel, pressure, exhaust and
converter DC-link points.

## Compute policy

- CPU is the reference/fallback backend.
- GPU may execute only workloads its runtime adapter explicitly declares.
- NPU is eligible only for generator condition/anomaly inference.
- No hardware discovery, runtime import, device assumption or AI-based
  protection/trip decision is performed by this package.
- Existing shared numerical policy remains authoritative for compatibility,
  precision, fallback and diagnostics.

## Dynamic controller model boundary

The first controller set is explicitly identified as generic first-order AVR,
TGOV1-style governor/turbine lag and washout/lead-lag PSS. They expose local
initial-state, derivative and output equations through the existing
DynamicPlugin contract. They do not own integration or simulation time.

These controller equations are not yet wired into the transient DAE. The
current DAESolver state layout is machine-only; the transient network solver
also consumes that exact machine-state vector, while the classical machine
uses constant Efd and the DAE accepts a fixed mechanical-power map. A correct
integration requires a single augmented global state layout, time-stage
controller evaluation, governor-to-mechanical-power coupling, AVR-to-internal
emf/network-source coupling, and a consistent algebraic solution strategy for
terminal-voltage feedback. Merely calling controller derivatives beside the
existing solver would create unsynchronized state and is intentionally not
implemented.

## Parameterized IEEE TGOV1 steam-governor block

A separate `TGOV1SteamGovernor` implementation is provided rather than
presenting the generic droop/turbine-lag block as a complete TGOV1 model.
Its two states are valve position and reheater/turbine power. On the connected
machine per-unit base, the model evaluates:

- Governor/valve command: `g = (P_ref - speed_deviation) / R - valve`
- Valve derivative: `dvalve/dt = g / T1`, with hard outward-limit blocking
- Turbine derivative: `dPt/dt = (valve + T2*dvalve/dt - Pt) / T3`
- Mechanical output: `Pm = Pt - Dt*speed_deviation`

The initialization routine derives the equilibrium valve and turbine states
from the requested mechanical power and speed, and rejects a supplied power
reference inconsistent with that equilibrium. The model requires the caller
to supply the reference and speed at each derivative/output evaluation.

This implementation is a focused TGOV1 block, not a claim that all steam
turbine/governor variants are represented. Turbine rating/base conversion,
deadband variants, nonlinear valve characteristics, boiler dynamics, and
model-specific limiter extensions remain explicit future work. The generic
droop block remains separately available and must not be identified as IEEE
TGOV1 in engineering studies.

Reference model documentation used for the parameter/equation structure:
- ORNL GridKit TGOV1 model: https://github.com/ORNL/GridKit/blob/develop/GridKit/Model/PhasorDynamics/Governor/Tgov1/README.md
- Dynawo TGOV1 model documentation:
  https://build.openmodelica.org/Documentation/Dynawo.Electrical.Controls.Machines.Governors.Standard.Steam.TGov1.html
- PowerWorld TGOV1 model parameter reference:
  https://www.powerworld.com/WebHelp/Content/TransientModels_HTML/Governor%20TGOV1%20and%20TGOV1D.htm

## Integration boundary

GeneratorDynamicsPlugin is activated only by the canonical
EngineeringPluginHost and requires the Application composition root to
supply generator_dynamics_composition.register_generator_extension.
This first milestone intentionally does not wire a fake composition service
or bypass the Application command/study/persistence lifecycle. UI, commands,
study handlers, persistent equipment configuration and result projections
are subsequent integration work.

## Current status

This is a foundation milestone, not a complete generator simulator or a
claim of standards certification. Family-specific electrical machine dynamic equations, validated machine
parameter sources, instrument-specific CT/PT/CVT error/saturation models,
protection function wiring, DAE-integrated control execution, persistence
migration, SLD editors and runtime-specific accelerator adapters remain open.
