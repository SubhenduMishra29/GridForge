# SDD ledger — plan: docs/superpowers/plans/2026-09-02-short-circuit-option-a.md

## Constraints
- No tests added or run, per user instruction.
- Frozen Option A is binding: Analysis prepares immutable input; Solver executes only from immutable numerical data.
- `ShortCircuit` is retained pending compatibility/API confirmation.

## Pre-flight scan
| Task | Shared file/interface | Producer → consumer | Finding | Ruling |
|---|---|---|---|---|
| 2 ↔ 5 | `SequenceNetwork` / sequence data | Snapshot → UnsymmetricalFault | Solver must consume frozen data, not mutable container | Use `SequenceNetworkSnapshot`; preserve `SequenceNetwork` as preparation container. |
| 3 ↔ 6 | `ShortCircuitInput` / `ShortCircuitResult` | Input → Solver → Result | Solver needs bus IDs, prefault voltage, Zbus/Thevenin, sequence snapshot | Input carries only prepared immutable numerical data; Result stores standalone values. |
| 4 ↔ 5 | impedance/prefault helpers | Helpers → fault engines | Helpers must not retain live Core | Helpers accept prepared matrices/voltages. |
| 6 ↔ 7 | solver API | Analysis → Solver | Analysis prepares all live-Core data before execution | Solver constructor takes only `ShortCircuitInput`. |
| 7 ↔ 8 | public facade | Analysis → compatibility facade | Legacy API may remain | Retain `ShortCircuit`; remove duplicate numerical ownership. |
| 9 ↔ Power Flow | contingency integration | Contingency → prepared PF boundary | Separate dependent concern | Do not broaden short-circuit implementation until direct correlation requires it. |

## Rulings
- Ruling: `SequenceNetworkSnapshot.from_sequence_network(...)` is used as the explicit preparation conversion rather than rewriting the large legacy container solely to add a one-line forwarding method — preserves behavior and keeps execution detached; cost if wrong is a minor API placement adjustment.
- Ruling: `ImpedanceMatrix` accepts prepared YBus plus immutable bus IDs — removes the live Network dependency while preserving Zbus/Thevenin responsibilities; cost if wrong is adapter work for external callers.

## Progress
- Task 1: complete (existing public fault types, result fields, and live-Core reads correlated from repository evidence).
- Task 2: in progress.
- Task 3: complete.
- Task 4: complete.
- Task 5: complete.
- Task 6: pending.
- Task 7: pending.
- Task 8: pending.
- Task 9: pending.
- Task 10: pending.
- Task 11: pending.
