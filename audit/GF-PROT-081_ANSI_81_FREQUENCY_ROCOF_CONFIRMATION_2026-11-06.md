# GF-PROT-081 — ANSI 81 frequency and RoCoF confirmation

Date: 2026-11-06
Repository: SubhenduMishra29/GridForge
Issue: #848
Branch: fix/ansi-81-frequency-rocof-confirmation

## Scope

Implement the previously fail-closed ANSI 81 function using the canonical
MeasurementChannel -> RelayInput -> RelayBase -> ProtectionDecision path.
This correction does not add solver-output differentiation or global
frequency smoothing.

## Engineering contract

- One real scalar frequency input, signal type FREQUENCY, phase NONE, exact
  engineering unit Hz. No implicit unit conversion is performed.
- All settings are explicit and required: under-frequency pickup (Hz),
  over-frequency pickup (Hz), RoCoF confirmation magnitude (Hz/s), sample
  rate (Hz), estimator window (s), sample interval tolerance (s), and
  operating delay (s).
- Under-frequency threshold must be below over-frequency threshold.
  Thresholds, sample rate, window and RoCoF confirmation magnitude must be
  finite and positive. Timing values must be finite and non-negative.
- The configured estimator window must contain an integral number of
  configured sample intervals.

## Estimator and sample integrity

- Uses a sliding window of timestamped frequency samples and least-squares
  linear regression of frequency against sample time; the slope is RoCoF in
  Hz/s.
- Requires a complete configured window before RoCoF confirmation is
  available. The estimator window starts at the first sample of each
  continuous under/over-frequency pickup episode; pre-pickup frequency
  trends cannot confirm a later pickup.
- Requires finite non-negative frequency (zero remains a valid under-frequency
  pickup value), valid/usable/available GOOD-quality
  samples, producer sequence numbers, strictly increasing timestamps,
  consecutive sample sequence numbers, configured sample-rate cadence,
  configured freshness, and an exact trusted timestamp-domain match.
- Rejects duplicate, skipped, stale, irregular, non-monotonic, incomplete,
  invalid, or cross-domain sample evidence. Rejection clears transient
  estimator and confirmation state and returns an invalid non-trip decision.
- RelayInput exposes timestamp, timestamp domain and sequence from the
  immutable Application-validated cycle snapshot. Application rechecks the
  sample timestamp domain after evaluation as part of the sample-coherence
  fence.
- Offline solver/scenario samples without acquisition timestamps are not
  relabelled as live measurements; ANSI 81 remains fail-closed on that path.

## Decision sequence

1. Frequency reaches the configured under- or over-frequency pickup.
2. A complete-window RoCoF estimate with matching sign and configured
   magnitude confirms that pickup.
3. The configured operating delay is measured continuously from confirmed
   pickup using the same trusted sample clock domain.
4. Only after the delay elapses can ANSI 81 issue a trip request.

RoCoF without an under/over-frequency pickup can never assert pickup,
operate, or trip. Loss of pickup or matching RoCoF confirmation resets the
confirmation timer. No engineering thresholds or defaults are fabricated.

## Files changed

- core/protection/frequency/frequency_relay.py (new)
- core/protection/frequency/__init__.py (new)
- core/protection/relay_input.py
- core/protection/input_contracts.py
- core/protection/function_catalog.py
- core/protection/__init__.py
- core/application/application.py

## Verification boundary

Source-level review of the changed contracts and integration points. No
tests, CI, runtime waveform experiment, or hardware validation is claimed.
This implementation is not a substitute for protection-setting studies,
commissioning, or relay coordination review.
