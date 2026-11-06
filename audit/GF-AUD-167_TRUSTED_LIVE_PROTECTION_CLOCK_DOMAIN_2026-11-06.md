# GF-AUD-167 — trusted live Protection evaluation clock domain

Date: 2026-11-06

## Finding
The prior live Protection path validated numeric timestamps and bounded sample age but did not prove that the supplied evaluation time and each MeasurementChannel sample belonged to the same clock domain. Numeric ordering is not a clock-domain contract.

## Correction
- `Application.evaluate_protection_cycle()` now requires an explicit canonical `evaluation_time_domain`.
- Before creating an audit claim or entering the relay-evaluation path, the Application compares that value with the read-only trusted `MeasurementChannelService.clock_domain`. Missing, malformed, or mismatched domains fail closed.
- The authenticated measurement-publication callback obtains the domain from the configured MeasurementChannelService and passes it to the live Protection cycle. It does not trust a producer/caller-supplied label for the evaluation clock.
- The internal unlocked evaluator repeats the trusted-domain check, preventing a private direct call from bypassing the public boundary.
- Every configured live Protection input channel must carry the exact same timestamp domain as the evaluation clock. Missing/mismatched sample domains reject the cycle before relay execution.
- The sample domain is included in the immutable validated measurement snapshot and is rechecked during the sample-coherence window.
- The validated evaluation domain is recorded in ProtectionContext metadata and durable audit metadata.
- Offline/scenario Protection evaluation remains on its separate study-time path; this live clock contract is not applied to solver time.

## Caller migration
- Authenticated live sample ingress is updated internally and resolves the trusted domain from MeasurementChannelService.
- Any external/direct caller of `Application.evaluate_protection_cycle(evaluation_time, ...)` must now pass `evaluation_time_domain=application.measurement_channel_service.clock_domain`. A configured trusted clock domain is mandatory; there is no fallback to numeric-only evaluation.
- Offline studies must continue using the study/scenario evaluation path and must not label solver time as the live acquisition domain.

## Verification boundary
Static source and caller review only. No tests, CI, syntax/import execution or runtime clock-skew experiments were performed.

## Register handling
The authoritative `Modification_Register.txt` is too large for the available GitHub file retrieval path to return its complete contents. It was not overwritten or truncated. This dedicated audit record is supplementary; a future register update must append this entry using a full-file-safe repository workflow.
