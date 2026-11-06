# GridForge V2 — GF-DYN-WF Remediation Specification

**Baseline:** `main` commit `4edcfd511300c868a30f2813ea1951fdc279374a`
**Target:** close verified GF-DYN-WF Application/UI study-workflow findings without violating the frozen architecture.

## Frozen boundary

```text
Study UI
  -> Study Controller/Coordinator
  -> Application Study Case boundary
  -> typed Core Study Configuration
  -> StudyRequest
  -> Application.execute_study()
  -> StudyService
  -> StudyPreparationService
  -> Core Analysis
  -> Core Result
  -> Application Result Adapter
  -> immutable Application Read Model
  -> semantic Study lifecycle event
  -> Study Projection
  -> UI
```

The Application layer is the sole UI/Core orchestration boundary. Core remains authoritative for engineering state, typed study configuration, preparation contracts, and analysis. UI does not import or interpret Core study-result classes.

## Study Case

`StudyCase` is Application/project-owned durable state. It has a stable `case_id`, user-facing `name`, `study_type`, typed Core configuration, and Application metadata. It is not a Core electrical object and is not placed in the Network topology.

Existing Core configuration classes remain authoritative:

- `PowerFlowStudyConfiguration`
- `ShortCircuitStudyConfiguration`
- `TransientStabilityStudyConfiguration`

No duplicate Application electrical-parameter classes are introduced.

## Study Request

A request represents one execution. It carries execution identity and a typed configuration reference/value plus an explicit runtime dependency context where a study requires derived artifacts. Persistent Study Case configuration and transient execution artifacts are not stored in the same generic mapping.

Transient Stability specifically requires a derived power-flow preparation/result dependency. Those objects are execution inputs and never become Study Case persistence data.

## Results

Core results are converted by study-specific Application adapters into immutable, UI-safe read models:

- `PowerFlowReadModel`
- `ShortCircuitReadModel`
- `TransientStabilityReadModel`

Lifecycle events identify the execution and result (`study_id`, `study_type`, `result_id`) rather than transporting arbitrary Core result graphs. Application read-model lookup is the result presentation contract.

## UI

`StudyCasesPanelWidget` stores semantic `study_case_id` independently from its display text. A dedicated Study Controller/Coordinator translates selection into an Application execution request. The panel remains a presentation surface and does not own persistence, Core analysis, or Core result interpretation.

## Persistence

`LoadedProject` and canonical project JSON gain durable `study_cases`. Only Study Case identity, name, type, typed configuration, and durable metadata are persisted. Prepared numerical objects, solver instances, event managers, runtime state, Qt objects, and Core result graphs are excluded.

Existing package/schema/version rules must be respected; no migration shortcut may bypass the current persistence contract.

## Failure/cancellation

Invalid case, invalid configuration, missing dependency, preparation failure, Core failure, cancellation, result conversion failure, and projection failure must be observable and must not be represented as a successful study completion.

## Verification

Tests are written before implementation changes. Runtime claims require actual execution evidence. The authoritative audit register is not assumed to exist merely because the requested path was named; its actual repository authority must be established before register mutation. Existing historical findings are preserved.

## Out of scope

- Reopening GF-DYN-WF-003, 004, 007, 009, or 017 without regression evidence.
- Recreating `DynamicMachineModel` or `state_vector.py`.
- Refactoring unrelated engineering systems.
- Moving Study Case identity into Core Network.
- Introducing a generic `Any` result envelope as the UI contract.
