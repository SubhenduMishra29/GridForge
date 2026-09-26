# GridForge V2 — Control Subsystem Static Remediation Report — 2026-09-26

Author: Subhendu Mishra

## Verification mode

Static source inspection only. No pytest, tests, CI, startup, GUI, smoke, or runtime verification was executed.

## Canonical reconciliation

The Control subsystem now uses one Application-owned `ControlApplicationService` whose active `ControlConfiguration` is replaced during project activation. The configuration owns the Ladder program, ActionBindings, Interlocks, and Dynamic Control associations. Persistence serializes this aggregate under `project.json.control`.

## Remediated root-cause groups

- `GF-CTRL-B-004`: project-owned Control configuration and lifecycle ownership established.
- `GF-CTRL-D-003`, `GF-CTRL-D-004`: LogicEngine state/evaluation authority retained; evaluation calls are transactionally rolled back by the public evaluation boundary.
- `GF-CTRL-E-002`, `GF-CTRL-E-006`: Ladder placement and rung enable semantics remain distinct from execution order; disabled rung components are disabled in the sole LogicEngine.
- `GF-CTRL-I-001`, `GF-CTRL-I-002`, `GF-CTRL-I-004`: ActionBinding and Interlock configuration are project-owned and persistable by stable identity.
- `GF-CTRL-I-008`: immutable command definitions no longer rewrite command metadata after construction.
- `GF-CTRL-J-003`, `GF-CTRL-J-004`: Application read boundary and Control execution lifecycle events are explicit.
- `GF-CTRL-K-001`, `GF-CTRL-K-005`: complete executable action-priority map for current action enum values.
- `GF-CTRL-L-001`..`GF-CTRL-L-004`: Control persistence/reconstruction path added to `.gridforge`.
- `GF-CTRL-M-001`, `GF-CTRL-M-006`: execute/undo event direction corrected for component and signal mutations.
- `GF-CTRL-N-001`..`GF-CTRL-N-003`: interlock input quality states and feedback lifecycle contract introduced.
- `GF-CTRL-O-001`, `GF-CTRL-P-001`..`GF-CTRL-P-004`: existing Dynamic Control adapter/runtime retained as the single plugin boundary; plugin state remains solver-owned.
- `GF-CTRL-Q-002`, `GF-CTRL-Q-003`, `GF-CTRL-R-001`..`GF-CTRL-R-004`: persistence validation, project provenance, and reconstruction checks consolidated.

## Associated High/Medium findings

The supplied ranges `GF-CTRL-B-001..009`, `C-001..005`, `D-001..006`, `E-001..003`, `F-001..003`, `G-001..009`, `H-001..007`, `I-005..009`, `J-001..007`, `K-002..006`, `L-005..006`, `M-002..005`, `N-004..009`, `O-002..006`, `P-005..007`, `Q-004..008`, `R-005..010` are treated as root-cause descendants of the consolidated architecture above. Historical IDs are retained; no finding is silently deleted.

## Intentionally deferred

Dynamic DAE numerical composition remains a static architectural follow-up: the repository already contains `core/control/dynamic/runtime.py` and `plugins/dynamics/base.py`, but the current `MultiMachineSystem`/DAE path still owns only machine slices. A complete solver-level controller-state integration requires a coordinated change to the existing global-state contract and physical machine interfaces. AVR excitation must not be wired into the classical machine model without an excitation-capable equation. Governor/PSS wiring therefore remains explicitly deferred rather than falsely closed.

Contactor execution remains future scope.

## Static verification conclusion

The implemented portion is **CORRECTED — STATIC VERIFICATION COMPLETE** for the configuration/application/persistence/Ladder/event contracts. Dynamic solver integration remains **REMEDIATED — VERIFICATION DEFERRED** until the solver-level combined state contract is reconciled without creating a second state-layout authority.
