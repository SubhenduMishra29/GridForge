# GridForge V2 — Plugin Infrastructure Reuse Matrix

**Status:** Implementation audit, branch `fix/study-service-handler-lifecycle`  
**Authority:** Subordinate to the frozen GridForge V2 Core/Application/UI architecture and the shared Plugin SDK principles merged by PR #675.  
**Purpose:** Make existing ownership explicit before introducing any shared SDK package or template.

## Reuse matrix

| Responsibility | Existing authoritative owner / contract | Plugin rule | Confirmed gap / action |
|---|---|---|---|
| Core engineering model and topology | Core model/network contracts and Core validation | Never create a plugin-owned competing electrical network or use graphics as engineering truth | Motor Dynamics represents a motor as a one-terminal injection/load and uses the canonical draft/topology path |
| Controlled mutation and transactions | `core/application/command.py`, `command_manager.py`, Application services and `Transaction` | Submit typed commands through Application; do not commit/rollback independently | Motor command adapter delegates transaction lifecycle to CommandManager; host composition adapter remains an integration prerequisite |
| Headless study request/context | `core/application/study.py`: `StudyRequest`, `StudyExecutionContext`, `StudyCancellationToken` | Handler signature must match the canonical callable contract | Reuse existing contracts; do not create a plugin scheduler |
| Study scheduling, cancellation and outcomes | `StudyService` in `core/application/study.py` | One scheduler and one canonical `StudyResult` store | Added identity-safe handler unregister in this change; active studies block removal and stale plugin instances cannot unregister replacements |
| Canonical events | `ApplicationEventBus` in `core/application/event_bus.py`; typed events in `core/application/events.py` | Subscribe/unsubscribe to the Application bus and release subscriptions on teardown | No new event bus; completion projections must read the canonical stored result |
| Study result lookup | `StudyService.get_result()`; Application compatibility lookup `study_result()`; active-project read models via `read_study_result(s)` | Preserve project ID, activation generation, study ID and source revision | Keep the typed stored result authoritative; plugin read models are projections only |
| UI plugin lifecycle | `ui/plugins/plugin_contract.py` plus loader, registry, manager, state store and context | Reuse UI composition lifecycle only for UI contributions | Keep distinct from the headless `StudyService` lifecycle |
| Plugin command/service composition | Existing Application command/service contracts and explicit `PluginContext` | Plugin lifecycle adapter composes host services; it must not duplicate a registry or transaction manager | Motor Dynamics requires a host-provided `motor_dynamics_composition`; do not silently synthesize one in the plugin |
| Configuration and persistence | Existing project/persistence ownership plus explicit plugin persistence adapter | Validate schemas and versioning at the appropriate owner; plugin-specific records remain plugin-specific | Do not introduce a global configuration store without evidence from multiple plugins |
| Compute backend dispatch | Domain algorithm's backend adapter plus explicit capability detection | CPU is baseline; advertise GPU/NPU only for implemented computations and report unsupported explicit selections | Motor solver currently has CPU and limited CUDA batch path; no NPU physics path is claimed |
| Diagnostics | Existing Application error/event contracts plus domain-specific structured diagnostics | Reuse canonical errors and add plugin-specific context; do not add a second general diagnostics bus | Consolidate only after a second plugin demonstrates common diagnostic shape |
| Read-only UI projections | Existing Application events/read models and `ui/plugins/` composition | Project canonical results; never mutate Core or treat chart state as truth | Motor telemetry projection remains plugin-specific |
| Descriptor/version/dependency validation | Existing plugin contracts where they apply; no single cross-namespace SDK API yet | Do not create a universal base class or duplicate UI registry | Defer concrete SDK package/API until this matrix and a second distinct plugin prove stable requirements |

## Motor Dynamics reconciliation

1. `MotorTransientStudyHandler` already matches the canonical callable signature: `(StudyRequest, StudyExecutionContext, StudyCancellationToken)`.
2. It returns a detached envelope; `StudyService` stores the resulting `StudyResult` and publishes `StudyCompleted`; the plugin publisher then retrieves the stored successful result before updating plugin read models.
3. The plugin lifecycle expects `StudyService.unregister(study_type, handler)`, which was absent on the prior `main` baseline. This change adds that method with identity-safe ownership and refuses removal while a study of that type is active.
4. The plugin also expects the existing Application `study_service`, `event_bus`, and `study_result` interfaces. Static source inspection found these on the current baseline; no runtime integration is claimed.
5. `motor_dynamics_composition` is an explicit host integration dependency. Its presence and transactional behavior must be reconciled separately before declaring the plugin end-to-end operational.
6. CPU is the portable baseline; CUDA dispatch is restricted to the implemented constant-input batch path. NPU acceleration for the recurrence-based physics solver is not implemented and must not be inferred from ONNX inference providers.

## Extraction decision

Do **not** create a general SDK runtime, new plugin manager, scheduler, event bus, result store, or configuration store in this change. The proven immediate shared gap is lifecycle-safe unregister for the existing canonical `StudyService`; solve it at that existing owner. Keep SDK descriptors, package placement, protocols, and template open until a second materially different plugin has been mapped against this matrix.

## Verification boundary

Static source/documentation review only. No tests, CI, syntax checks, imports, application startup, numerical validation, or CPU/GPU/NPU hardware validation were run.
