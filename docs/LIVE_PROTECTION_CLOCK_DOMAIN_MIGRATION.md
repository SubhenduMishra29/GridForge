# Live Protection evaluation clock-domain migration

## Required API change

Direct callers of `Application.evaluate_protection_cycle()` must now provide:

```python
application.evaluate_protection_cycle(
    evaluation_time,
    evaluation_time_domain=application.measurement_channel_service.clock_domain,
)
```

The configured `MeasurementChannelService.clock_domain` must be a canonical non-empty string backed by the trusted Application clock configuration. Do not pass an arbitrary caller label.

## Authenticated live publication

The canonical `MeasurementChannelService.publish_sample()` callback resolves the evaluation domain from the service itself. Application callers should use this authenticated publication route rather than manually invoking the live Protection cycle with a producer-provided domain.

## Offline and transient studies

Do not pass solver simulation time as the live acquisition clock domain. Offline/scenario Protection evaluation remains separate and uses its captured study-time/topology provenance. Dynamic Control must continue rejecting live MeasurementChannel sources until a study-scoped simulation-clock measurement snapshot adapter is implemented.

## Failure behaviour

A missing trusted clock domain, absent/non-canonical evaluation domain, domain mismatch, or sample-domain mismatch blocks live Protection evaluation before relay execution. Configure the trusted clock and channel domains consistently before enabling live Protection.
