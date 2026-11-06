# GF-AUD-166 — retire the unused caller-targeted Protection trip adapter

Date: 2026-11-06

## Audit finding
The project Protection cycle already uses the canonical Application execution chain: persisted function-code/target mapping, active-network target validation, typed ControlDecision translation, ControlCommandDispatcher, Application command execution, provenance fences, and a distinct Core postcondition observation. Physical field-device acknowledgement remains unknown/unavailable unless independently supplied.

The legacy `ProtectionOutputService.trip_from_decision(decision, breaker_id)` accepted a caller-selected breaker ID and issued `TripBreakerCommand` directly. It did not bind the Protection decision's relay/function identity to the active project's persisted target mapping and did not share the project-cycle provenance/outcome contract.

## Caller and export audit
- The helper was not exported from `core/application/services/__init__.py` or `core/application/__init__.py`.
- No production Application/bootstrap caller was found in the source audit.
- Its only identified caller was the obsolete standalone test `tests/core/application/test_protection_trip_boundary.py`, which explicitly encoded the unsafe caller-targeted contract.

## Correction
- Remove the unused `ProtectionOutputService` rather than relabel it as a manual/operator API; it has no operator identity, authorization evidence or audit context.
- Remove its obsolete standalone test. Canonical dispatch remains covered at the Control dispatcher and Protection execution boundaries; no production trip functionality is removed because the helper was not wired into production composition.
- Do not add an alternate caller-supplied target path. All Protection-originated automatic trips remain on the canonical persisted-mapping execution path.

## Verification boundary
Static source and caller/export inspection only. No tests, CI, syntax/import execution or runtime field-device acknowledgement validation performed.
