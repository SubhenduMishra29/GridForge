# GF-AUD-210–220 / GF-EDM-001–069 Static Verification and Final Review

Date: 2026-09-10
Branch: `remediation/gf-aud-210-220-edm-001-069`

## Scope

Final static verification of the remediation branch after the Line, Cable, Transformer, prepared numerical boundary, YBus, Power Flow, Short Circuit, Protection, Dynamics, persistence/migration, and compatibility work.

Per the authoritative remediation contract, tests and numerical runtime execution were **not performed**.

## Verification Results

### 1. Core architectural boundary

The reviewed remediation path preserves the intended dependency direction: engineering models feed Study Preparation; prepared numerical data feeds numerical construction/solvers; downstream flow consumers use prepared data rather than reinterpreting live engineering objects.

No Qt/UI dependency was introduced by the remediation work reviewed here. This final review was static and focused on the changed and boundary-critical Core modules; it is not a claim of an exhaustive repository-wide import graph execution.

### 2. YBusBuilder

`core/numerical/ybus.py` remains numerical-only. `YBusBuilder` has no Network constructor dependency and builds from prepared bus IDs and prepared PU branch/transformer/shunt values. It performs no engineering-unit conversion, base selection, terminal resolution, or live-model inspection.

The numerical boundary is therefore preserved.

**Residual static finding:** `YBus` is a frozen dataclass, but its public SciPy CSR matrix is intrinsically mutable. The dataclass freeze prevents field reassignment but does not make the sparse matrix contents immutable. This is recorded as a residual immutability hardening item rather than introducing a new matrix abstraction during this remediation cycle.

### 3. Study Preparation

`core/analysis/power_flow_preparation.py` remains the authoritative engineering-to-PU preparation boundary. Prepared branch/transformer/shunt structures are frozen dataclasses and the prepared snapshot stores tuples and a read-only bus-voltage mapping.

The preparation module imports the engineering models, canonical endpoint resolver, and existing `PerUnitSystem`; `core/numerical/ybus.py` does not.

### 4. Numerical solver inputs

The reviewed Power Flow, Line Flow, and Transformer Flow consumers use prepared numerical representations. Line and Transformer flow calculations use prepared PU values rather than reading engineering impedance from live equipment. The compatibility sweep found no justified downstream production change.

Short Circuit uses detached sequence data and detached fault-study input rather than reconstructing a live-network numerical YBus path.

### 5. Persistence / migration

`core/persistence/migration.py` is deliberately narrow. It validates explicit metadata for legacy Cable `r/x/b` and Transformer impedance representations and raises `AmbiguousElectricalDataError` when required interpretation metadata is absent. It does not guess engineering units, system bases, or transformer impedance bases.

This preserves the rule that persistence/migration retains engineering truth and explicit representation metadata rather than silently creating numerical solver state.

### 6. Duplicate-architecture check

No second generic per-unit system, endpoint resolver, branch manager, numerical network manager, or parallel dynamic architecture was introduced by the reviewed remediation work.

## Contract Review

| Contract | Static result |
|---|---|
| Core owns engineering truth | PASS |
| Study Preparation is engineering→PU boundary | PASS |
| YBusBuilder consumes prepared PU data only | PASS |
| Numerical flow does not reinterpret engineering models | PASS |
| Transformer basis must be explicit | PASS |
| Cable must not be double-converted | PASS |
| Ambiguous legacy electrical data is not guessed | PASS |
| Persistence avoids solver-state serialization | PASS |
| Detached prepared snapshots are used downstream | PASS, subject to YBus matrix mutability noted above |
| No duplicate architecture added | PASS |
| Runtime/test verification | NOT PERFORMED by contract |

## Final Review Disposition

The remediation contracts reviewed at this stage are structurally satisfied by static inspection, with one explicit residual hardening item: the SciPy CSR payload inside `YBus` is mutable despite the frozen dataclass wrapper.

No further production architecture change is justified solely by this static review. Hardening the nested sparse-matrix mutability should be handled as a focused follow-up if full deep immutability is required by the final numerical snapshot contract; it should not be solved by introducing a parallel YBus abstraction.

## Verification Limitation

This report is based on repository/static inspection of the remediation branch and previously recorded compatibility findings. Tests, numerical studies, and application runtime execution were intentionally not performed. Therefore this report makes no runtime-correctness or numerical-result claim.
