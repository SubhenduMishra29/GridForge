# GridForge Branch Engineering-to-PU Boundary

**Author:** Subhendu Mishra  
**Status:** Frozen Option B remediation contract

## Canonical flow

```text
Engineering Model
       ↓
PowerFlowPreparation
       ↓
PreparedPowerFlow
       ↓
YBusBuilder
       ↓
YBus
       ↓
Solver
```

Engineering model state is authoritative. Prepared PU state is derived, immutable numerical study state.

## Line

Authoritative electrical quantities:

- `resistance_ohm`
- `reactance_ohm`
- `shunt_susceptance_siemens`

Generic `Branch.r/x/b` must not silently define a universal physical basis.

## Cable

Canonical engineering quantities are per kilometre:

- `r1_ohm_per_km`, `x1_ohm_per_km`, `b1_us_per_km`
- `r0_ohm_per_km`, `x0_ohm_per_km`, `b0_us_per_km`
- `length_km`
- `rated_voltage_kv`, `rated_current_a`

Cable values are converted to total engineering quantities and then to PU exactly once during preparation.

## Transformer

The legacy repository does not establish whether `r/x/b` are ohms, percent impedance, transformer-rating PU, or system-base PU. No basis is to be invented. Transformer input therefore requires explicit `impedance_basis` metadata; ambiguous legacy data is rejected or requires explicit migration metadata.

## Per-unit boundary

`PowerFlowPreparation` owns study MVA base, branch voltage base, terminal-to-bus resolution, engineering-to-PU conversion, and detached numerical branch snapshots. It must reuse `core/base/per_unit.py::PerUnitSystem`.

For engineering impedance:

```text
Zbase = Vbase² / Sbase
Rpu = RΩ / Zbase
Xpu = XΩ / Zbase
Bpu = BSiemens × Zbase
```

## Prepared state

Prepared standard branches contain only:

```text
branch_id, from_bus_id, to_bus_id, r_pu, x_pu, b_pu, in_service
```

Prepared transformers additionally contain `tap` and `shift`.

## YBusBuilder

`YBusBuilder` consumes prepared PU data only. It must not read live branch electrical parameters, select bases, convert engineering units, interpret transformer impedance basis, or infer units.

For a prepared branch:

```text
y_series = 1 / (r_pu + j*x_pu)
y_shunt_half = j*b_pu/2
```

Transformer tap/phase-shift stamping is applied only to already prepared PU impedance.

## Persistence and migration

Engineering quantities remain canonical persisted state. Known PU legacy data may be preserved only with explicit PU metadata. Ambiguous legacy `r/x/b` must never be silently reinterpreted.

The remediation preserves canonical terminal resolution, deterministic BusIndex ordering, existing PowerFlowInput/PowerFlowResult semantics, GF-AUD-207/208 behavior, and the GF-AUD-204 Measurement Generation boundary.
