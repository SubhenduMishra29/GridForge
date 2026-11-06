# GF-AUD-159 follow-up — draft terminal source-registry validation

Date: 2026-11-06

## Correction

- Draft terminal snap candidates are validated against the terminal names declared by their source `SymbolPreviewItem`, not only against a non-empty terminal ID and a self-consistent role/name pair.
- The draft terminal ID must equal the source preview contract's deterministic identity, `<draft_id>:<terminal_name>`.
- `EndpointIdentityAdapter` repeats the source-item check at the identity boundary, preventing a fabricated or bypassed `SnapResult` from promoting an unregistered draft terminal into an Application endpoint reference.
- The adapter also verifies that the candidate equipment type matches the source presentation item's declared element type.
- Draft Bus attachment identity remains a separate contract and is unchanged.

## Architecture

All validation remains in UI identity/presentation adapters. Core `EndpointReference` semantics and Application `DraftEndpointReference` commit translation remain unchanged.

## Verification boundary

Static source and diff inspection only. No tests or CI run. Issue #874 remains open pending an actual snap-to-commit interaction trace.

The authoritative `Modification_Register.txt` is preserved byte-for-byte in this reconciliation because the connector could not safely retrieve the complete 1 MB file for an append-only update. This note is the supplementary audit record; do not treat the issue as closed.
