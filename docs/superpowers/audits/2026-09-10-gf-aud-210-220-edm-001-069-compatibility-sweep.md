# GF-AUD-210–220 / GF-EDM-001–069 Compatibility Sweep

Date: 2026-09-10
Branch: `remediation/gf-aud-210-220-edm-001-069`

## Scope

Compatibility sweep after the completed Line, Cable, Transformer, prepared numerical boundary, YBus, Power Flow, Short Circuit, Protection, Dynamics, and persistence remediation tasks.

Tests were **not executed**, per the remediation contract.

## Reconfirmed Consumers

### Power Flow

`core/analysis/power_flow.py` constructs analysis from `PreparedPowerFlow` and passes the prepared numerical input/YBus to the numerical solver. The `from_network()` path performs preparation first; the numerical analysis does not construct YBus from the live Network.

### Line Flow

`core/analysis/line_flow.py` requires `PreparedPowerFlow`. Line electrical parameters are not read from the live Line model. Flow calculations use `PreparedBranch.r_pu`, `x_pu`, and `b_pu` only.

### Transformer Flow

`core/analysis/transformer_flow.py` requires `PreparedPowerFlow` and calculates from `PreparedTransformer` values only. Transformer engineering impedance is not reinterpreted by the flow calculator.

### Dynamics

The existing dynamic solver/model boundary remains separate from Power Flow/YBus construction. `MultiMachineSystem` coordinates machine state and differential equations; machine models expose engineering/dynamic parameters and explicit mechanical/electrical inputs. No duplicate dynamic preparation architecture was introduced during this sweep.

### Short Circuit / Protection / Persistence

The previously completed remediation work established detached sequence, protection, measurement, and migration boundaries. These boundaries remain the intended consumers of prepared/detached representations rather than live numerical construction.

## Boundary Checks

1. **Engineering-to-PU conversion:** retained at study preparation; downstream Line/Transformer flow consumers consume prepared PU values.
2. **YBus:** no downstream engineering interpretation was introduced; YBus remains a PU-only numerical boundary.
3. **Live Network in numerical flow:** Line and Transformer flow calculators retain an optional compatibility `network` reference but do not use it as a numerical source. Prepared data is mandatory.
4. **Transformer basis:** preparation/migration remains responsible for explicit impedance-basis interpretation; downstream flow does not guess a basis.
5. **Cable conversion:** no downstream Cable-specific second conversion was identified in the inspected flow consumers.
6. **Endpoint resolution:** branch preparation remains responsible for canonical endpoint resolution; numerical flow operates on prepared bus IDs.
7. **Identity mapping:** prepared branch/transformer IDs and prepared bus ordering are used consistently by downstream flow consumers.

## Result

No compatibility-breaking production change was justified by the inspected downstream consumers. Existing compatibility surfaces were preserved where they do not violate the authoritative numerical boundary.

No duplicate per-unit system, endpoint resolver, branch manager, numerical network manager, or dynamic machine architecture was added.

## Verification Limitation

This is a static repository review. Runtime tests and numerical execution were intentionally not performed. The compatibility sweep therefore makes no runtime-success claim.
