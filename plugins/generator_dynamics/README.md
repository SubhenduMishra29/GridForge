# Generator Dynamics Plugin

Initial engineering foundation for GridForge V2's universal generator plugin.

## Scope

- Diesel and gas engines, steam and gas turbines, hydro, wind (DFIG and
  full-converter), synchronous, induction, permanent-magnet, inverter-based,
  fuel-cell and microturbine families.
- Immutable nameplate and model parameter contracts.
- Synchronous-machine d/q transient and subtransient parameter validation.
- AVR/exciter, governor/actuator and prime-mover parameter contracts.
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
claim of standards certification. Dynamic solver equations, validated
machine parameter sources, instrument-specific CT/PT/CVT error/saturation
models, protection function wiring, control execution, persistence migration,
SLD editors and runtime-specific accelerator adapters remain open.
