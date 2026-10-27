# GridForge V2 — Shared Plugin SDK Architecture Amendment

**Status:** Architecture-principle freeze candidate; concrete SDK API remains deliberately unfrozen until reference-plugin reconciliation.
**Authority:** Subordinate to the GridForge V2 Core/Application/UI boundaries and the existing Plugin Platform contract.
**Scope:** Reusable infrastructure for future domain, study, integration, and UI plugins.
**Change control:** Reconcile this amendment against the current repository before implementation. Do not create a parallel plugin framework or duplicate an existing authoritative service.

## 1. Decision

GridForge plugins MUST reuse shared platform and Application infrastructure for common behavior. A plugin MUST NOT reimplement lifecycle orchestration, registry mechanics, study scheduling, cancellation plumbing, canonical event delivery, common result publication, configuration mechanics, capability discovery, diagnostics, or UI projection lifecycle when an authoritative shared contract/service already exists.

Plugins own their domain-specific behavior: domain models where permitted, engineering equations/algorithms, input interpretation, result schemas, specialized integrations, and plugin-specific presentation.

This amendment is intended to reduce duplication and complexity without introducing a large universal base class or a second Application layer.

## 2. Non-negotiable boundaries

- **Core** remains authoritative, headless, and independent of plugins, Qt, QGraphics, SLD, and UI controllers.
- **Application** owns commands, controlled mutation, transactions/history, study orchestration, cancellation/status, canonical events, and authoritative read/result publication contracts.
- **Plugin Platform / SDK** provides stable public extension contracts and lifecycle/registration orchestration. It composes existing Application services; it does not clone them.
- **UI plugins** are presentation and interaction adapters. They cannot mutate Core directly or make graphics the source of engineering truth.
- **Domain plugins** call public Core/Application contracts and cannot access private internals or bypass validation.
- Qt access remains behind `ui.core.qt`; no Qt or graphics objects cross into Core.
- All user-originated mutation follows the established path: UI → Controller → Command → Application → Core → Event → Projection → UI.

## 3. Shared SDK capability areas

The SDK should expose small, typed, documented contracts for these capability areas, reusing existing owners wherever present:

1. **Identity and descriptors** — stable plugin ID, version/API compatibility, plugin kind, declared capabilities, dependencies, and metadata.
2. **Lifecycle** — Discover → Validate → Load → Resolve Dependencies → Register → Activate → Use → Deactivate → Unload. Lifecycle state has one owner; registration and cleanup are deterministic and idempotent where possible.
3. **Registration** — explicit registries with a single owner, deterministic lookup, conflict detection, and explicit unregister/rollback behavior.
4. **Study integration** — an adapter contract that conforms to the existing `StudyService` callable boundary (`StudyRequest`, `StudyExecutionContext`, `StudyCancellationToken`) and delegates scheduling, cancellation, status, error classification, event emission, and result registration to that canonical Application service. Do not introduce a second study scheduler or a parallel handler lifecycle.
5. **Events** — use `ApplicationEventBus` and its existing `subscribe`/`unsubscribe` contract, with lifecycle-bound cleanup. Plugins must not create parallel event buses. UI/plugin-specific notification mechanisms may adapt canonical events for presentation but must not become an engineering-truth event source.
6. **Results and read models** — use the existing `StudyResult` and `StudyService` result-registration contract as the canonical study outcome. Plugin-specific result/read models may project a successfully stored result, preserving project/study/generation/revision identity. Failed or cancelled studies must not publish successful results. Do not create a competing general-purpose result store.
7. **Configuration** — typed schemas, defaults, validation, versioning/migration hooks, and explicit persistence ownership.
8. **Compute capabilities** — a common backend interface and capability report for CPU/GPU/NPU or other accelerators. CPU is the required portable baseline when the algorithm supports it; accelerators are optional and capability-gated, with deterministic fallback/reporting. Do not advertise a backend merely because a device or inference provider exists. NPU support requires a suitable implementation for the actual computation and validation.
9. **Diagnostics** — structured error codes, actionable details, backend selection/fallback explanations, and lifecycle failure reporting.
10. **UI projection contracts** — optional, read-only view-model/projection hooks that refresh from canonical successful events and read models. UI construction remains separate from domain computation.

These are capability areas, not a mandate to create one file or class per bullet. First reuse existing authoritative services and contracts; extract a shared abstraction only where a real repeated requirement is confirmed.

## 4. Plugin kinds and existing plugin subsystems

GridForge already distinguishes the broader `plugins/` extension namespace from `ui/plugins/`, which owns UI composition. The current UI plugin architecture has an explicit `Plugin` contract and separates `PluginLoader`, `PluginRegistry`, `PluginManager`, `PluginStateStore`, and `PluginContext` responsibilities. This amendment does **not** replace that architecture or collapse UI lifecycle and domain/study execution into one manager.

Use a small set of capability contracts rather than one oversized base class:

- **Domain/study capability:** supplies domain algorithms and/or a callable adapted to the canonical StudyService contract.
- **Integration capability:** adapts an external format, device, or service through approved Application contracts.
- **UI/presentation capability:** contributes views, inspectors, dashboards, tools, or actions through the existing `ui/plugins/` composition contracts.
- **Equipment/model capability:** contributes only through established Core model contracts; it cannot duplicate Core topology or validation.

A plugin package may provide more than one capability, but each capability must have a clear owner and dependency direction. Reuse the existing UI plugin manager for UI composition; do not route headless engineering calculations through UI lifecycle machinery. Do not introduce another manager/registry for a capability already owned by an existing subsystem.

## 5. Dependency direction and ownership

```text
Core domain contracts ← Application services (commands, studies, events, results)
                                ↑
                  domain/study plugin adapters

Existing UI composition: PluginManager → PluginRegistry/PluginStateStore
                                      → PluginContext → UI plugin

UI plugin/projection → public Application commands, read models, and events
```

The SDK is a **thin public contract/adaptation layer**, not a new architectural tier that owns a second copy of Application services. Its runtime location must be decided only after auditing existing ownership and import dependencies. Core must never depend on the SDK or concrete plugins. UI presentation dependencies must not leak into headless study/domain code. The existing UI lifecycle remains distinct from the Application StudyService lifecycle.

## 6. New-plugin implementation rule

A new plugin should contain only its descriptor/registration contribution, domain-specific inputs and validation, domain calculation or integration, typed result mapping, and genuinely plugin-specific UI. Shared lifecycle, dispatch, event cleanup, cancellation, status, diagnostics, and publication are supplied by existing services/SDK contracts.

Illustrative shape only (not a prescribed runtime API):

```python
class ExampleStudyHandler:
    study_type = "example_study"

    def execute(self, request, context):
        inputs = self.validate_domain_inputs(request)
        result = self.run_domain_calculation(inputs, context)
        return self.build_typed_result(result)
```

The actual method names and signatures must match the audited canonical StudyService contract; do not copy this illustrative snippet as production code without reconciliation.

## 7. Complexity and reuse rules

- Prefer composition and small protocols over deep inheritance or a universal base class.
- Do not duplicate a service merely to make a plugin self-contained.
- Do not create a second registry, lifecycle manager, study scheduler, event bus, result store, or configuration store where an authoritative owner already exists.
- Avoid speculative abstractions: promote shared code after confirming at least one real cross-plugin reuse case and a stable contract.
- Keep plugin dependencies explicit, versioned, and validated before activation.
- Fail registration on conflicting canonical identifiers or incompatible contracts; never silently choose based on import order.
- Cleanup must be scoped to resources actually registered by that plugin and must not unregister a replacement owned by another component.
- Preserve source-level and runtime verification honesty: document unverified integration, numerical correctness, and hardware capability explicitly.

## 8. Migration strategy

1. Audit current plugin and Application implementations and map repeated responsibilities to their authoritative owners.
2. Reconcile contracts with `core/application/study.py`, `core/application/event_bus.py`, `core/application/events.py`, the existing `ui/plugins/` lifecycle contract, plugin contexts/registries, read models, and projection infrastructure.
3. Maintain a reuse matrix: responsibility, current owner/API, proven duplicate call sites, gap, proposed adapter, migration owner, and compatibility impact.
4. Extract only genuinely missing shared behavior. Prefer adapting existing services over moving or renaming them.
5. Refactor Motor Dynamics as the first study-plugin reference only after reconciling its current feature-branch assumptions with the canonical base API. In particular, the audited `main` StudyService exposes `register()` but does not currently expose `unregister()`; any lifecycle-safe unregister addition must be separately reconciled and explicitly implemented rather than assumed to exist.
6. Apply the abstraction to a second, materially different plugin before freezing concrete SDK class names and method signatures.
7. Publish a minimal plugin template only after the contracts are stable.
8. Keep the architecture principles frozen after merge, while treating concrete SDK APIs and file placement as a later, evidence-driven design decision subject to controlled amendment.

Do not expand the scope of an unrelated feature PR solely to add the SDK. Prefer a focused architecture PR, then migrate Motor Dynamics in a follow-up or an explicitly scoped follow-on PR.

## 9. Freeze boundary and acceptance criteria

### Frozen now: architectural principles

- No parallel or competing plugin lifecycle/registry/study/event/result infrastructure.
- One authoritative owner per shared responsibility; SDK contracts adapt existing owners.
- Core remains headless; Application owns study execution, controlled mutation, canonical events, and study result registration; UI remains projection/interaction.
- Existing UI plugin lifecycle remains distinct from the headless StudyService lifecycle.
- Plugin dependencies, registration conflicts, rollback, and teardown must have explicit semantics in the subsystem that owns them.
- Study success/failure/cancellation and publication of plugin-specific projections must preserve canonical result identity/status.
- CPU fallback and optional accelerator capabilities must be explicit; unsupported GPU/NPU paths are reported rather than implied.
- Architecture and Modification Register are updated together.

### Not frozen yet: concrete SDK API and implementation layout

- Exact package path, public class names, protocol method signatures, descriptor schema, and versioning mechanism.
- Whether a missing common service should be added or an existing service extended.
- The claim that one generic plugin base contract should cover every plugin kind.

These remain open until the current APIs are mapped, Motor Dynamics is reconciled against them, and a second distinct plugin demonstrates the abstraction. No tests/CI are run unless explicitly authorized; any later verification is reported precisely.

## 10. Relationship to existing architecture

This amendment freezes reuse and ownership principles only. It does not supersede the established Core/Application/UI boundaries, the current `ui/plugins/` contract, or the separate `plugins/` engineering-extension namespace. It is not permission to create a parallel plugin framework. Concrete SDK implementation must follow the frozen principles and a separately reconciled API design.


## 11. Static reconciliation findings (2026-10-27)

The following repository contracts were inspected directly:

- `core/application/study.py`: `StudyService` is the canonical study execution owner. Its handler is currently a callable accepting `StudyRequest`, `StudyExecutionContext`, and `StudyCancellationToken`. It stores typed `StudyResult` outcomes and emits started/completed/cancelled/failed Application events. The audited `main` version has `register()`, `execute()`, `cancel()`, `get_result()`, and `results()`; it does not have `unregister()`.
- `core/application/event_bus.py`: `ApplicationEventBus` already provides synchronous event publication plus `subscribe()` and `unsubscribe()`. The SDK must reuse this bus.
- `ui/plugins/plugin_contract.py` and `ui/plugins/README.md`: UI composition already has a small protocol and separate loader, registry, manager, state-store, and context owners. Do not replace or merge these lifecycle roles with the study-handler contract.
- `contract.md` and the architecture reconciliation matrix distinguish the broader engineering extension namespace from UI composition. Historical authority statements in the reconciliation matrix must be treated as chronology where superseded, not copied as current repository authority.
- Motor Dynamics on `feature/motor-dynamics-extension-v2` currently expects `StudyService.unregister()`. That assumption is not present on the audited `main` baseline. This is a concrete integration dependency to reconcile before the plugin is treated as a reference implementation.

Decision:
    Freeze the reuse/ownership principles in this amendment. Keep concrete SDK APIs,
    package placement, and any required StudyService API changes open until the
    reuse matrix and reference-plugin reconciliation are complete.

Verification boundary:
    Static source inspection only. No tests, CI, syntax checks, imports, runtime,
    numerical, or hardware validation were run.
