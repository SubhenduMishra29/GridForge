# GridForge V2 — Open / Partial Remediation Status

Author: Subhendu Mishra

Date: 2026-09-10

Baseline audited HEAD:

`7f2cf46c144606efc26b5bfc858467306c261008`

Remediation branch:

`remediation/open-partial-findings-2026-09-10`

## Important status rule

A finding is not marked CLOSED until its targeted executable regression test has been run successfully and the conflicting implementation has been removed or reconciled. The current GitHub-backed execution environment permits repository inspection and commits but does not provide a repository checkout/test runner, so the targeted tests added in this phase are **not yet executed**.

## Phase 1 — measurement

### GF-AUD-204

Previous status: OPEN / PARTIAL

Current status: PARTIALLY CLOSED

Root cause addressed:

- Measurement Generation now treats analysis current/voltage values as numerical PU quantities.
- Current conversion is explicitly PU -> physical primary A -> CT secondary A.
- Voltage conversion is explicitly PU -> physical primary kV -> PT/CVT secondary V.
- Short-circuit current conversion now requires the prepared numerical base and no longer applies a CT ratio directly to a PU result.
- Channel signal type is validated against the conversion family.

Remaining:

- Targeted tests must execute successfully.
- The MeasurementChannel contract still relies on its existing signal-type/unit/source binding rather than introducing a second conversion object; any remaining audit gap must be resolved from executable evidence.

### GF-AUD-205

Previous status: OPEN

Current status: PARTIALLY CLOSED

Root cause addressed:

- `core/application/commands/measurement_transformer_commands.py` was a duplicate command authority.
- It has been removed.
- A regression test locks the canonical `measurement_commands.py` module as the command authority.

Remaining:

- Targeted test execution.
- Import/consumer verification from a real repository checkout.

## Phase 2 — transformer / PU boundary

### GF-AUD-212 / GF-AUD-217 / GF-AUD-218

Current status: PARTIALLY CLOSED

Corrections:

- Transformer impedance basis is explicit: `pu` or `engineering`.
- The original impedance MVA basis is retained explicitly.
- The impedance reference voltage is retained explicitly.
- Application-created transformers use the declared FROM-side nominal voltage as the documented impedance reference contract.
- `PreparedTransformer` is the numerical boundary.
- `YBusBuilder` continues to consume prepared numerical quantities rather than engineering transformer values.

Remaining:

- Targeted preparation/model tests must execute.
- Persistence must serialize and restore the new impedance-basis metadata.
- Any legacy transformer payload migration must be verified against explicit basis metadata.

### GF-AUD-220

Current status: PARTIALLY CLOSED

Corrections:

- Existing `PerUnitSystem` remains authoritative.
- Transformer PU values are converted from their declared original MVA basis to the study base during preparation.
- Engineering transformer ohms/siemens are converted during preparation.
- Cable and Line conversion remains in the same Power Flow preparation boundary.

Remaining:

- Targeted cross-equipment preparation tests must execute.
- Full supported-branch audit remains pending.

## Reactive equipment

### GF-EDM-028 / GF-EDM-047 / GF-EDM-067

Current status: PARTIALLY CLOSED

Corrections:

- Capacitors and reactors are no longer treated as fixed P/Q injections in Power Flow preparation.
- They are converted into the existing `PreparedShunt` representation.
- Capacitor/reactor MVAr is converted to PU susceptance using the canonical system MVA base.
- The existing generic `Shunt` numerical representation remains unchanged.
- No `PreparedCapacitor` or `PreparedReactor` duplicate numerical architecture was introduced.

Remaining:

- Targeted tests must execute.
- Y-bus numerical contribution must be verified by executable integration tests.

## Other findings

The following groups have not yet been changed in this phase and therefore remain OPEN or DEFERRED pending re-verification:

- GF-AUD-206 / GF-AUD-216 persistence
- GF-EDM-001–019 remaining engineering-model gaps
- GF-EDM-030–045 protection-specific gaps not already satisfied by the existing protection architecture
- GF-EDM-049–057 study/result gaps not covered by existing contracts
- GF-EDM-058–061 and GF-EDM-068 dynamic boundary/sample gaps, subject to confirmation of whether dynamic functionality is currently implemented
- GF-EDM-063–065 cross-cutting preparation/completeness/snapshot gaps beyond the Power Flow work above
- GF-EDM-069 protection study versus simulation execution boundary pending final integration verification

No finding in these groups is claimed CLOSED merely because a class or module exists.

## Regression protection

The following previously closed findings were not intentionally reopened by this phase:

- GF-AUD-207
- GF-AUD-208
- GF-AUD-209
- GF-AUD-210
- GF-AUD-213
- GF-AUD-214
- GF-AUD-215
- GF-AUD-219
- GF-EDM-046
- GF-EDM-048
- GF-EDM-066

## Test policy

The full repository suite has **NOT RUN**.

Targeted tests added/updated in this phase are awaiting execution in a repository checkout with the GridForge Python dependencies installed.
