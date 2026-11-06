# GF-EDM-069 — Protection Decision → Application → Breaker Closure

## Current-head reconciliation

The prior protection integration was insufficiently authoritative: `ProtectionOutputService` constructed `TripBreakerCommand` but then invoked `ModelService.trip_breaker(...)` directly. That bypassed `Application.execute()`, and therefore bypassed the canonical CommandManager transaction/history/event boundary.

The repository already provides the required canonical path:

```text
ProtectionDecision
    ↓
TripBreakerCommand
    ↓
Application.execute()
    ↓
CommandManager
    ↓
registered breaker handler
    ↓
SwitchingModelService
    ↓
Core Breaker mutation
```

## Minimum correction

`ProtectionOutputService` now accepts the authoritative `Application` facade and delegates the immutable `TripBreakerCommand` to `Application.execute()`.

It no longer accepts or invokes `ModelService` directly and no longer owns a transaction. Transaction ownership remains in `CommandManager`.

## Test specification

`tests/core/application/test_protection_trip_boundary.py` now specifies:

- actionable protection decisions produce `TripBreakerCommand` execution through `Application`;
- breaker state changes through the Application-owned command path;
- command history contains the committed `model.trip_breaker` command;
- non-actionable protection decisions are rejected before mutation.

## Status

**REMEDIATED — VERIFICATION DEFERRED**

Runtime tests were not executed. No pass/fail result is claimed.

## Scope discipline

No second command system, protection mutation mechanism, breaker manager, or control architecture was introduced. The existing Application command path was reused as required by the frozen architecture.
