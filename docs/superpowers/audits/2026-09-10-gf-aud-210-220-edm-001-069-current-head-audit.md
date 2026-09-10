# GridForge GF-AUD-210–220 / GF-EDM-001–069 — Current-HEAD Re-audit

Date: 2026-09-10  
Branch: `remediation/gf-aud-210-220-edm-001-069`  
Base: `418765f5f100ed20ca22795a30d63679a7e3075c`

## Purpose

Reconfirm the remediation contract against the branch before implementation. Findings below are based on the current branch contents, not the historical audit alone.

## Contract Matrix

| Area | Current status | Current evidence / consequence |
|---|---|---|
| Branch endpoint ownership | **FIXED** | `Branch` owns the authoritative `from_terminal` / `to_terminal`; specialized models do not create a second endpoint state. |
| Line engineering R/X/B | **PARTIALLY FIXED / RECONCILE CONSUMERS** | `Line` exposes `resistance_ohm`, `reactance_ohm`, and `shunt_susceptance_siemens`. Preparation converts these values to PU. Downstream flow code is already prepared-data based. Remaining consumers/import paths still require sweep. |
| Cable engineering truth | **PARTIALLY FIXED / RECONCILE MIGRATION** | `Cable` stores per-km positive/zero-sequence engineering values and derives total engineering R/X/B from length. The constructor rejects ambiguous `r/x/b` inputs, but legacy persistence/import paths still need explicit audit for proven-PU vs ambiguous data. |
| Transformer impedance basis | **PARTIALLY FIXED** | `Transformer` requires `impedance_basis` and accepts `pu` / `engineering`. Power-flow preparation currently supports `pu` and rejects `engineering` because authoritative transformer engineering basis/rating conversion is not yet implemented. Persistence/import consumers must be reconciled. |
| Canonical per-unit utility | **FIXED** | `core/base/per_unit.py` is the active `PerUnitSystem`. No second generic PU system is required. |
| Canonical endpoint resolver | **FIXED / MUST BE ENFORCED EVERYWHERE** | `core/network/endpoint.py` is used by Power Flow preparation. Remaining analysis/protection/SC consumers require sweep for direct endpoint interpretation. |
| Prepared Power Flow branch boundary | **PARTIALLY FIXED** | `PreparedBranch`, `PreparedTransformer`, and `PreparedShunt` already exist and are detached dataclasses. Identity mapping beyond element IDs/solver ordering is not yet explicit. Snapshot immutability is incomplete because `YBus` contains a mutable SciPy CSR matrix. |
| YBus engineering interpretation | **FIXED AT CURRENT IMPLEMENTATION** | `YBusBuilder` accepts prepared data and stamps only PU values. It has no Network constructor dependency and does not import engineering models. |
| YBus direct callers | **REQUIRES CONSUMER SWEEP** | Power Flow preparation calls `YBusBuilder().build(snapshot)`. All other direct `YBusBuilder` construction/build call sites must be verified and migrated if any remain. |
| Power Flow preparation | **PARTIALLY FIXED** | It prepares buses, injections, branches, transformers, and shunts into a detached snapshot. It still calls `network.ensure_bus_index()`, which is a live-network operation and must be assessed against the no-analysis-mutation rule. |
| Reactive equipment | **PARTIALLY FIXED** | `PreparedShunt` exists and Power Flow preparation reads `network.shunts`; Capacitor/Reactor integration must be checked against the actual model collections and semantics. |
| Line flow | **FIXED AT CURRENT IMPLEMENTATION** | `LineFlowCalculator` consumes `PreparedPowerFlow` / `PreparedBranch`; it does not read live Line electrical quantities. |
| Transformer flow | **FIXED AT CURRENT IMPLEMENTATION / SEMANTICS REVIEW** | `TransformerFlowCalculator` consumes `PreparedTransformer`. Tap/shift stamping and flow equations must remain aligned with the declared prepared convention. |
| Numerical solver boundary | **MOSTLY FIXED FOR POWER FLOW / SWEEP REQUIRED** | Power Flow solver receives `PowerFlowInput` and `YBus`; Short Circuit, Protection, and Dynamics require the same detached-boundary audit. |
| Analysis mutation of Network | **OPEN** | Power Flow preparation explicitly invokes `ensure_bus_index()`. Other analysis modules need inspection for topology/model mutation. |
| Short Circuit preparation | **OPEN / INCOMPLETE** | Current `short_circuit.py` exists, but a detached sequence-network preparation boundary has not yet been established/reconfirmed. |
| Protection preparation | **OPEN / INCOMPLETE** | Existing protection architecture must be audited for offline-vs-simulation path separation and measurement-chain correctness. |
| Dynamics preparation | **OPEN / INCOMPLETE** | Existing dynamic solver must be preserved; the PowerFlowResult → DynamicInitializationPreparation → DynamicStudySnapshot bridge remains to be implemented if absent. |
| Persistence / migration | **OPEN / INCOMPLETE** | Engineering truth must be persisted. Legacy Cable/Transformer R/X/B data requires explicit metadata handling; ambiguous data must not be silently interpreted. |

## Important Current-HEAD Observations

### 1. The YBus boundary has already been moved in the right direction

`core/numerical/ybus.py` is already a detached numerical builder. It stamps `PreparedBranch`, `PreparedTransformer`, and `PreparedShunt` data using `r_pu/x_pu/b_pu`, tap, and shift. No engineering-unit conversion belongs in this module.

### 2. PowerFlowPreparation is now the main remaining numerical-boundary pressure point

`core/analysis/power_flow_preparation.py` performs engineering-to-PU conversion and constructs the detached snapshot. This is the correct architectural location, but it still couples preparation to live Network access by necessity and currently calls `network.ensure_bus_index()`. That call must not become an accidental topology mutation contract.

### 3. Cable is already engineering-first

Cable's positive-sequence total resistance/reactance are derived from per-km engineering parameters and length. Preparation currently consumes those totals once. Short Circuit must consume the zero-sequence engineering data separately rather than routing it through a second positive-sequence conversion.

### 4. Transformer basis is explicit but incomplete

The model correctly refuses a missing basis. The remaining issue is not to loosen that contract; it is to establish authoritative engineering-basis conversion only if the repository contains sufficient transformer rated MVA/voltage semantics. Otherwise engineering-basis records must remain rejected/quarantined rather than guessed.

### 5. PreparedPowerFlow is structurally detached but not deeply immutable

The dataclasses are frozen, tuples are used for collections, and voltage bases are wrapped in `MappingProxyType`. However, `PreparedPowerFlow.ybus.matrix` is a mutable SciPy sparse matrix. This is a Task 5 concern, not a reason to duplicate the YBus abstraction.

## Scope Decision

The implementation sequence remains valid. Tasks 2–4 should reconcile the existing Line/Cable/Transformer partial remediation before Task 5 strengthens the prepared numerical boundary. No new generic manager, parallel PU system, or duplicate branch hierarchy is warranted.

Tests may be added/updated as contracts change, but **no tests are to be executed during this remediation cycle unless explicitly authorized by the user**.
