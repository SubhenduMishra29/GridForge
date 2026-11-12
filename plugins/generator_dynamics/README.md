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

## Hydro and legacy gas-turbine governor model selection

HYGOV is a distinct hydro governor/penstock model, not a generic droop
controller. Its published parameter contract includes permanent and temporary
droop, governor and filter time constants, gate-servo time constant, gate
velocity and position limits, water starting time, turbine gain and damping,
and no-load flow. Its turbine/penstock response is operating-point dependent;
the linearized penstock transfer function depends on water time constant,
initial flow and initial head. A future implementation must preserve the
nonlinear water-flow/head relationship or state clearly which linearization
and operating point it uses. It must not silently replace HYGOV with the
existing generic two-lag governor.

The legacy PSS/E GAST model is also a distinct model, with governor/valve,
combustion-chamber/turbine and exhaust/load-limit dynamics. It is retained as
a compatibility model only if implemented; it must not be selected as the
default model for a modern digitally controlled gas turbine. NERC's 2017
modeling notification describes GAST as a simplified early model, notes that
it omits important heavy-duty gas-turbine physics, and recommends transition
to a more representative GGOV1 model after verification. Any future GAST
implementation must therefore be explicitly labeled legacy, preserve its
ambient-temperature load limit and low-value-gate behavior, and require
plant-specific verification. A modern gas-turbine controller should be
represented by a separately parameterized model such as GGOV1 only after its
full state/limiter contract and machine-base conversions are implemented.

References for model selection and parameter boundaries:
- NERC, *Gas Turbine Governor Modeling* (2017), Appendix B and recommendations:
  https://www.nerc.com/comm/PC/NERCModelingNotifications/Gas_Turbine_Governor_Modeling.pdf
- ORNL GridKit HYGOV parameter contract and documented limitations:
  https://gridkit.readthedocs.io/en/latest/GridKit/Model/PhasorDynamics/Governor/HYGOV/README.html
- OpenIPSL HYGOV model parameters and connectors:
  https://build.openmodelica.org/Documentation/OpenIPSL.Electrical.Controls.PSSE.TG.HYGOV.html
- Argonne, *Hydro Turbine-Governor Simulation Models in PSS/E* (2013), including
  the operating-point-dependent penstock linearization:
  https://www.osti.gov/servlets/purl/1098022

These model-selection notes do not claim full HYGOV, GAST or GGOV1 plant-model
equivalence. The plugin contains a reduced nonlinear HYGOV block and a
GGOV1 frequency-control PID/reset sub-block; neither is a complete plant
model. Model-specific hydro and gas-turbine actuator, turbine/fuel and limiter
paths remain separate implementation milestones. No controller is connected
to the transient DAE until the canonical augmented-state contract is available.

## Reduced nonlinear HYGOV hydro-governor block

`HYGOVReducedHydroGovernor` is the first executable hydro-governor milestone. It is deliberately named **reduced**: it implements a permanent-droop PI governor, first-order error filter, gate servo with position and velocity limits, and a nonlinear inelastic single-penstock water column. The parameter contract is explicit about per-unit quantities and seconds.

With speed deviation Δω, reference Pref, filtered error xf, integrator xi, gate g, flow q and head H, the implemented equations are:

- `e = Pref - Δω - R*g`
- `d(xf)/dt = (e - xf)/Tf`
- `c = xi + xf/r`; `d(xi)/dt = xf/(r*Tr)`
- Gate command is clamped to `[GMIN, GMAX]`; `dg/dt = (clamped_command - g)/Tg`, bounded by `±VELM`. Motion farther through a hard gate-position limit is blocked, as is integrator motion that drives further into command saturation.
- `H = (q/g)^2`; `dq/dt = (Hdam - H)/Tw` for an open gate. At the closed-gate, zero-flow point the model uses nominal head.
- `Pm = At*H*(q - qNL) - Dturb*Δω*g`

This corresponds to the nonlinear inelastic penstock relationship and turbine power form documented in GridKit; parameter names are cross-checked against OpenIPSL and OPAL-RT documentation. References: GridKit HYGOV equations and limitations (https://gridkit.readthedocs.io/en/latest/GridKit/Model/PhasorDynamics/Governor/HYGOV/README.html), OpenIPSL HYGOV parameter contract (https://build.openmodelica.org/Documentation/iPSL.Electrical.Controls.PSSE.TG.HYGOV.html), and OPAL-RT HYGOV parameter definitions (https://opal-rt.atlassian.net/wiki/spaces/PDOCHS/pages/150276051/HYGOV).

### Explicit reduced-model limitations

This is **not a drop-in claim of complete PSS/E or IEEE PES-TR1 HYGOV equivalence**. This first block uses a linear gate-to-flow characteristic (`P_GV(g)=g`) and fixed nominal dam head; it does not yet model the full gate characteristic curve, head-dependent dam/tailrace conditions, deadband/backlash variants, Kaplan blade servo, or turbine-rating conversion. Initialization requires a steady operating point satisfying `q = g * sqrt(Hdam)` and `Pref = Δω + R*g`; it sets the filtered error to zero and the integrator to the requested gate position for a bumpless initial command. Plant-specific parameter validation and comparison against a trusted reference implementation are still required.

The class follows the existing `DynamicPlugin` local-state contract only. It does not own a clock, mutate Core, or connect itself to the transient DAE.


## GGOV1 gas-turbine governor parameter contract

\`GGOV1Parameters\` is the validated, immutable parameter contract for the next gas-turbine governor implementation milestone. It captures the distinct turbine MW rating, droop feedback selector (\`Rselect\`), fuel-speed selector (\`Flag\`), PID governor gains, electrical-power measurement lag, governor error and valve limits, actuator time/rate limits, turbine lead-lag and transport constants, no-load fuel flow, load limiter, plant power controller, acceleration limiter, speed deadband, temperature-detection lead/lag, and load-limit slew rates.

The parameter contract is accompanied by `GGOV1PIDGovernor`, an executable PSS/E-derived frequency-control PID and supervisory reset sub-block. The plugin descriptor advertises both `ggov1_parameter_contract` and `ggov1_pid_subblock`, but deliberately does not advertise a complete `ggov1_executable` capability. The block is not a complete GGOV1 governor and must not be selected as a full plant model. The PID sub-block exposes local initialization, derivatives and output through the existing DynamicPlugin contract; it is not connected to the transient DAE. The separate `GGOV1ValveActuator` implements the first-order `Tact` response with asymmetric `Ropen`/`Rclose` slew limits and `Vmin`/`Vmax` position stops. It accepts the already selected and limited fuel-stroke command. The separate `GGOV1LowValueSelector` now provides the minimum-selection and tracking-error contract, while detailed OEM calibration and integrated plant-level control remain open.

The turbine rating is explicit, positive, and is not inferred from generator MVA. \`system_to_turbine_power_base_ratio()\` exposes the numerical system-base/turbine-rating ratio; the caller must still apply the correct MW/MVA and per-unit convention for the connected machine and study. No hidden base conversion is performed. The selector contract follows the NERC PSS/E definition: \`Rselect\` values 1, 0, -1 and -2 select electrical power, no feedback, valve stroke and governor output respectively; \`Flag\` is binary. Parameter checks enforce ordered error/valve limits, positive opening and negative closing rates, and the turbine lead/lag zero-time consistency rule. Mechanical damping is finite but intentionally not constrained to be positive because published manufacturer data can use a negative value.

The implemented PID sub-block follows the PSS/E-derived OpenIPSL topology for selected droop feedback, filtered electrical-power measurement, dead-zone/error limiting, proportional/integral/filtered-derivative control, bounded supervisory reset integration, and operating-point initialization. It deliberately does not claim the complete GGOV1 behavior: valve actuator rate/position dynamics, fuel/turbine response, load-controller tracking, low-value selection among governor/load/acceleration/temperature limiters, OEM-specific temperature maps and ambient compensation, complete limiter scheduling, optional transport delay, and integrated DAE execution remain open. The block is not connected to the transient DAE. See `GGOV1_PID.md` for the state and equation boundary.

NERC describes GGOV1 as a general-purpose PID governor with valve actuation, fuel-system dynamics, exhaust-temperature load limiting, load control, acceleration limiting, and governor deadband. It also emphasizes plant-specific verification, correct turbine MW rating, and avoiding confusion between turbine rating and generator MVA base. Manufacturer default values are starting points, not universal settings. References:

- NERC, *Gas Turbine Governor Modeling* (2017), Appendix A and parameter/base guidance: https://www.nerc.com/comm/PC/NERCModelingNotifications/Gas_Turbine_Governor_Modeling.pdf
- NERC, *Application Guide for Modeling Turbine-Governor and Active Power-Frequency Controls in Interconnection-Wide Stability Studies* (2019), Appendix C: https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/ppmvtf/reliability_guideline-application_guide_for_turbine-governor_modeling-2019-05-07-CLEAN.pdf
- OpenIPSL GGOV1 parameter/model package documentation: https://build.openmodelica.org/Documentation/iPSL.Electrical.Controls.PSSE.TG.GGOV1.GGOV1.html
- ORNL GridKit GGOV1 equations and explicit implementation caveats: https://github.com/ORNL/GridKit/blob/develop/GridKit/Model/PhasorDynamics/Governor/GGOV1/README.md

ORNL GridKit currently marks multiple GGOV1 damping, fuel-flow, PID, limiter, temperature and transport-delay paths incomplete or unverified. Its equations are therefore useful for cross-checking signal/parameter names, but are not treated here as sufficient proof of a complete reference implementation. Plant/OEM data and disturbance-based model verification remain mandatory before study use.


**Selector-source reconciliation:** NERC's PSS/E GGOV1 table defines `Rselect` as `1 = Pelec`, `0 = no feedback`, `-1 = fuel-valve stroke`, and `-2 = governor output`. The ORNL GridKit explanatory equations currently document a different mapping for the non-default values and omit selector 0 in its validation set. The executable selector helpers now follow the NERC/PSS/E mapping. The PID and supervisory reset sub-block are executable locally; the low-value selector and explicit PID tracking input are also available as separate contracts. Acceleration/load/temperature limiter dynamics and tracking for limiter controllers remain incomplete. The GGOV1D deadband variant is also kept distinct from GGOV1 rather than silently applied to both.


The selector helpers have deliberately narrow responsibilities: \`droop_feedback_signal()\` returns Pelec for Rselect=1, zero for isochronous Rselect=0, valve stroke for -1, and governor output for -2; \`fuel_speed_multiplier()\` returns shaft speed for Flag=1 and unity for Flag=0. \`GGOV1PIDGovernor\` uses the selected feedback in its speed-error summing junction and implements the local PID and supervisory reset states. It does not implement fuel/turbine dynamics or the outer low-value selector. The NERC block diagram also shows controller tracking during low-value-select transfers; that behavior remains a required part of full GGOV1 integration rather than being approximated by the selector helpers.


### GGOV1 fuel-valve actuator sub-block

`GGOV1ValveActuator` contributes one solver-owned state, actual valve position.
Its continuous-time response is the first-order actuator request
`(bounded_command - valve_position) / Tact`, limited to the configured
negative closing and positive opening rates. Position stops prevent further
motion beyond `Vmin` and `Vmax`; an out-of-range numerical trial state may
move back toward the admissible interval. Initialization clamps the supplied
initial position to the configured bounds.

The input is explicitly the post-selector, post-limiter fuel-stroke request.
This block does not choose between the speed, temperature and acceleration
controllers, and does not implement controller tracking during selector
transfers. It is a valve actuator sub-block, not a complete GGOV1 turbine
model and is not yet coupled to the transient DAE.

### GGOV1 turbine fuel-to-mechanical-power sub-block

`GGOV1TurbineFuelPath` adds the turbine fuel response after the actual valve
stroke. `Flag=0` makes fuel flow equal to valve stroke; `Flag=1` multiplies
valve stroke by absolute shaft speed in per-unit. The no-load fuel flow
`Wfnl` is subtracted before the turbine gain. For `Tb > 0`, one solver-owned
state represents the lagged net fuel flow and the output applies the
`(1+s*Tc)/(1+s*Tb)` lead-lag response. `Tb=Tc=0` is an algebraic bypass.
Mechanical output is `Kturb * turbine_response - Dm * speed_deviation`; this
uses a linear damping correction and is not a substitute for every
manufacturer-specific speed-dependent capability curve.

`Teng` is deliberately not implemented with an internal queue or private
clock. When `Teng > 0`, the caller must supply `delayed_fuel_flow_pu` from a
solver-owned transport-delay facility at every evaluation; initialization
requires an explicit initial fuel-flow value. When `Teng=0`, the delay input
is not used. This keeps all integration history and time ownership in the
host solver. The block does not implement the outer low-value selector,
limiter tracking, exhaust-temperature/acceleration/load limiting, or DAE
coupling. It is a GGOV1 turbine/fuel response sub-block, not a complete
GGOV1 model.


### GGOV1 low-value selector and governor tracking

`GGOV1LowValueSelector` selects the smallest active fuel request from the
speed governor, acceleration limiter and combined load/temperature limiter.
Disabled limiter inputs are omitted; the governor request is mandatory.
Equal values use a stable source priority so the selected-source identity is
repeatable. The immutable result includes each active controller's
selected-minus-requested tracking error.

The selector does not fabricate acceleration or load/temperature controller
outputs. Those controllers must calculate their own requests on the same
fuel-command base before selection. The combined load/temperature candidate
must itself already reflect the applicable plant-specific limiter logic.

`GGOV1PIDGovernor.derivatives()` accepts the selected fuel command and an
explicit positive tracking time constant together. It adds
(selected command - raw governor PID output) / tracking time to the governor
integral derivative. If either input is omitted, the existing standalone PID
integrator equation is retained. This makes limiter tracking an explicit
solver/composition input rather than embedding an undocumented universal
constant. The selector and tracking hook do not implement the missing
acceleration, load, or exhaust-temperature controller dynamics, nor do they
make the complete GGOV1 plant model executable.




### GGOV1 acceleration, load and temperature paths

The acceleration controller follows the PSS/E/OpenIPSL block topology. Its
single solver-owned state filters machine speed deviation with the `Ta`
derivative filter. The algebraic acceleration request is
`FSRA = FSR + Ka * DELT * (ASET - d(SPEED)/dt)`. The host supplies the
currently selected `FSR` command and the model's discrete sample interval
`DELT`; this feedback is the reference tracking path. `Ta` must be positive.

`GGOV1LoadLimiter` follows OpenIPSL `LoadLimiter.mo`:
`TREF = Wfnl + LDREF / Kturb`, `eT = TREF - TEXM`,
`d(integral)/dt = Kiload * eT`, and
`FSRT = min(1.0, Kpload * eT + integral)`. The integral starts from
`(PELEC + Dm) / Kturb + Wfnl`. The block's upper-only 1.0 pu clamp matches
that reference component; the common Vmin/Vmax clamp is applied after the
three-way low-value selector in the outer GGOV1 path.

`GGOV1TurbineFuelPath.temperature_proxy_input()` supplies the pre-filter
temperature proxy: net fuel flow multiplied by the PSS/E `Dm_select(speed)`
factor. `GGOV1TemperatureMeasurement` then cascades the `(1+s*Tsa)/(1+s*Tsb)`
temperature-detection lead/lag with the `1/(1+s*Tfload)` lag to produce
`TEXM`, which feeds the load limiter. This is the model's calculated
temperature proxy, not a thermocouple measurement or OEM firing-temperature
map.

The three candidate requests—governor `FSRN`, acceleration `FSRA`, and
temperature/load `FSRT`—feed `GGOV1ControlCoordinator`. It applies the
low-value selector followed by the common `[Vmin, Vmax]` clamp and returns an
immutable `GGOV1ControlDecision`. Its `actuator_command_pu` is the one final
command to pass to `GGOV1ValveActuator.derivatives()` and back to the
acceleration limiter. Pass the same command as `selected_fuel_command_pu`
to PID and load-limiter derivatives when enabling their explicit tracking
inputs. The decision exposes final-command-minus-request tracking errors for
each active candidate. The coordinator owns no dynamic state or solver clock.
 
 `calculate_ggov1_operating_point()` provides a pure shared initialization
 calculation from initial electrical/mechanical power at nominal shaft speed. It
 derives the common initial FSR, actual valve target, Flag-dependent fuel
 flow, modeled temperature-proxy input, and Rselect-consistent PID power
 reference for zero initial governor error, and the initial governor-output
 feedback value. It also reports the PID/load-PI
 integral alignment residual and the load-limiter output residual. Set `load_limiter_enabled=False` when that path is disabled. Call
`require_balanced()` when it is enabled and all initialized paths must agree.
The helper rejects an initial FSR outside common valve limits, and above the
1.0 pu ceiling when the load limiter is enabled. The host still calls each block's own `initial_state()`;
 the helper owns no solver state or lifecycle.

 The acceleration limiter is sampled: calculate FSRA using the previous
 selected FSR feedback and the host's positive `DELT`, then perform the
 three-way selection and common clamp. Feed the resulting command to the
 actuator and use it as the FSR feedback for the next acceleration sample.
 The host owns sample ordering and the DELT clock; do not evaluate this
 feedback loop as an instantaneous algebraic cycle. `Rup`/`Rdown` are retained as model data
but are not applied by the OpenIPSL GGOV1 reference implementation used
here; they must not be confused with actuator `Ropen`/`Rclose`.

These are reference-derived sub-blocks, not a complete integrated GGOV1
plant model. Vendor-specific thermal maps, ambient compensation, transport
delay execution, complete tracking composition, DAE integration and
disturbance-based validation remain open.