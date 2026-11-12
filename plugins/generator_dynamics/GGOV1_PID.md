# GGOV1 PID sub-block

`GGOV1PIDGovernor` is a local continuous-time implementation of the PSS/E-derived
GGOV1 frequency-control PID sub-block and supervisory power reset path. It is
not a complete GGOV1 governor and must not be represented as a validated
plant-level gas-turbine model.

## Implemented sub-block

Four states are exposed to the host integrator:

1. Electrical-power measurement lag.
2. Derivative-filter input state.
3. Governor integral contribution.
4. Supervisory power-controller reset contribution.

The error summing junction follows the OpenIPSL PSS/E-derived
`PIDGovernor.mo` topology:

`e_raw = P_REF + reset - SPEED - R * selected_feedback`

The selected feedback is the existing `GGOV1Parameters.droop_feedback_signal()`
contract: `Rselect=1` electrical power, `0` none (isochronous),
`-1` valve stroke, and `-2` governor output. Electrical-power feedback uses
the filtered measurement state. The speed dead-zone is applied before the
configured minimum/maximum error limiter.

The PID output is the sum of proportional, integral and filtered derivative
terms. The derivative path uses the first-order filtered derivative transfer
`Kdgov*s/(1 + Tdgov*s)`. The supervisory reset path integrates
`Kimw * (PMW_SET - filtered_PELEC)` and blocks outward integration at
`±1.1*R`, matching the referenced bounded integrator topology.

Initialization follows the OpenIPSL reference structure: filtered electrical
power starts at its operating-point value; derivative filter state starts at
the initialized error (zero derivative output); governor integral contribution
starts at `(Pm0 + Dm)/Kturb + Wfnl`; supervisory reset starts at zero.
By default `Pm0` is taken from the supplied electrical power, as in the
reference implementation. A caller may supply an explicit mechanical-power
value when it has already reconciled the study base and operating point.

## Deliberate boundary

This block does **not** implement the GGOV1 actuator, fuel/turbine dynamics,
transport delay, temperature/load limiter, acceleration limiter, low-value
selector, or tracking/bumpless transfer among competing controllers. The
governor integrator is not given a fabricated anti-windup or outer-limiter
tracking path. It does not own a clock, persist state, mutate Core, or connect
itself to the transient DAE. Its inputs must already be expressed on the
correct model base; turbine MW rating versus generator MVA conversion remains
the caller's explicit responsibility.

The derivative gain may be zero with a zero derivative time constant; a
nonzero derivative gain requires a positive filter time constant. A zero
electrical-power time constant is treated as an algebraic measurement bypass.

## References

- OpenIPSL PSS/E-derived source:
  https://github.com/OpenIPSL/OpenIPSL/blob/master/OpenIPSL/Electrical/Controls/PSSE/TG/BaseClasses/GGOV1/PIDGovernor.mo
- OpenIPSL selector source:
  https://github.com/OpenIPSL/OpenIPSL/blob/master/OpenIPSL/Electrical/Controls/PSSE/TG/BaseClasses/GGOV1/R_select.mo
- OpenIPSL GGOV1 component documentation:
  https://doc.openipsl.org/files/doc-200/OpenIPSL_Electrical_Controls_PSSE_TG_BaseClasses_GGOV1.html
- NERC, *Application Guide for Modeling Turbine-Governor and Active Power-Frequency Controls in Interconnection-Wide Stability Studies* (2019), Appendix C:
  https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/ppmvtf/reliability_guideline-application_guide_for_turbine-governor_modeling-2019-05-07-CLEAN.pdf

OpenIPSL is used here as a transparent implementation reference, not as a
claim of equivalence to every vendor's GGOV1 variant. Plant/OEM data and
disturbance-based validation are still required.


## Low-value selector tracking hook

`GGOV1LowValueSelector` is a separate stateless block. It selects the minimum
of the active governor, acceleration and combined load/temperature fuel
requests. It returns a selected-minus-requested tracking error for every
active source. This allows each controller's own integrator to track the
active fuel request while it is not selected.

The PID sub-block accepts `selected_fuel_command_pu` and
`tracking_time_constant_s` together in `derivatives()`. The governor
integral derivative receives the tracking correction
`(selected_fuel_command - raw_PID_output) / Ttrack`. Ttrack is an explicit
caller-supplied value: no universal plant-independent tracking constant is
assumed. If both values are omitted, the standalone PID behavior is unchanged.
This hook does not add tracking to controllers that have not yet been
implemented, and does not claim the full GGOV1 limiter network is complete.


## Acceleration, load and temperature sub-block boundaries

The acceleration controller follows the PSS/E/OpenIPSL discrete block:
the `Ta` derivative filter estimates `d(SPEED)/dt`, then
`FSRA = FSR + Ka * DELT * (ASET - d(SPEED)/dt)`. It has one filtered-speed
state, not an FSRA integrator. The caller supplies the currently selected
`FSR` command and the model sample interval `DELT`; this is the feedback
tracking path. `Ta` must be positive.

`GGOV1LoadLimiter` implements the PSS/E-derived OpenIPSL `LoadLimiter.mo`
path. It forms `TREF = Wfnl + LDREF / Kturb`, computes
`eT = TREF - TEXM`, integrates `Kiload * eT`, and produces
`FSRT = min(1.0, Kpload * eT + integral)`. The integral operating-point
initialization is `(PELEC + Dm) / Kturb + Wfnl`. The LoadLimiter itself
applies only the upper 1.0 pu clamp; the common `[Vmin, Vmax]` clamp belongs
after the three-way low-value selector.

`GGOV1TurbineFuelPath.temperature_proxy_input()` computes net fuel flow
multiplied by the PSS/E `Dm_select(speed)` factor. The separate
`GGOV1TemperatureMeasurement` block cascades the `(1+s*Tsa)/(1+s*Tsb)`
temperature-detection lead/lag with `1/(1+s*Tfload)` and produces `TEXM`.
This is a calculated model proxy, not a physical thermocouple model or an
OEM firing-temperature map.

The three requests `FSRN`, `FSRA`, and `FSRT` feed the minimum selector;
its result is clamped to `[Vmin, Vmax]`, sent to the actuator, and fed back
to the acceleration limiter. `Rup` and `Rdown` remain unimplemented source
parameters in the OpenIPSL reference path and are not interchangeable with
the actuator's `Ropen` and `Rclose`.

These are reference-derived sub-blocks, not a complete integrated GGOV1
plant model. Vendor-specific thermal maps, ambient compensation, complete
tracking composition, delay execution, DAE integration and plant
disturbance validation remain open.
