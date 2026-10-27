# GridForge V2 — Shared Plugin SDK Architecture Amendment

**Status:** Proposed architecture amendment; becomes part of the frozen V2 architecture only after review and merge.
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
4. **Study integration** — a typed study-handler contract that delegates scheduling, cancellation, status, error classification, and completion events to the canonical StudyService/Application flow.
5. **Events** — shared subscription and unsubscription contracts with lifecycle-bound cleanup. Plugins must not create parallel event buses.
6. **Results and read models** — canonical project/study identity, typed result/status contracts, and publication only through the approved Application/read-model boundary. Failed or cancelled studies must not publish successful results.
7. **Configuration** — typed schemas, defaults, validation, versioning/migration hooks, and explicit persistence ownership.
8. **Compute capabilities** — a common backend interface and capability report for CPU/GPU/NPU or other accelerators. CPU is the required portable baseline when the algorithm supports it; accelerators are optional and capability-gated, with deterministic fallback/reporting. Do not advertise a backend merely because a device or inference provider exists. NPU support requires a suitable implementation for the actual computation and validation.
9. **Diagnostics** — structured error codes, actionable details, backend selection/fallback explanations, and lifecycle failure reporting.
10. **UI projection contracts** — optional, read-only view-model/projection hooks that refresh from canonical successful events and read models. UI construction remains separate from domain computation.

These are capability areas, not a mandate to create one file or class per bullet. First reuse existing authoritative services and contracts; extract a shared abstraction only where a real repeated requirement is confirmed.

## 4. Plugin kinds

Use a small set of explicit extension contracts rather than forcing all extensions through one oversized base class:

- **Domain/study plugin:** provides a domain algorithm and/or typed study handler.
- **Integration plugin:** adapts an external format, device, or service through approved Application contracts.
- **UI/presentation plugin:** contributes views, inspectors, dashboards, tools, or actions without owning domain truth.
- **Equipment/model extension:** contributes declared equipment/domain capabilities through the established model contracts; it cannot duplicate Core topology or validation.

A plugin may declare more than one capability, but each capability must have a clear contract and owner. Do not introduce separate plugin managers for these kinds unless repository evidence demonstrates a necessary boundary.

## 5. Recommended dependency direction

```text
Core domain contracts
        ↑
Application services (commands, studies, events, results)
        ↑
Plugin Platform / SDK (public contracts + lifecycle composition)
        ↑
Domain, study, and integration plugins

UI composition / UI plugins → public Application read models and commands
UI projection → canonical events/read models
```

The SDK may depend on public Application contracts. Core must never depend on the SDK or concrete plugins. UI presentation dependencies must not leak into headless study/domain code.

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

1. Audit current plugin and Application implementations and map each repeated responsibility to its current authoritative owner.
2. Reconcile the proposed contracts with existing `core/application/study.py`, event contracts, plugin contracts/registries, read models, and UI projection infrastructure.
3. Record a reuse matrix: existing service, duplicate call sites, proposed shared contract, migration owner, and compatibility impact.
4. Extract only missing common behavior; prefer adapting existing services over moving or renaming them.
5. Refactor Motor Dynamics as the first study-plugin reference implementation after its StudyService/event/result contracts are source-audited.
6. Use a second genuinely different plugin to test the abstraction's fit before declaring the SDK stable.
7. Provide a minimal plugin template and migration guidance only after the contracts are stable.
8. Freeze the SDK contract and API compatibility policy after review; future changes follow controlled architecture amendment.

Do not expand the scope of an unrelated feature PR solely to add the SDK. Prefer a focused architecture PR, then migrate Motor Dynamics in a follow-up or an explicitly scoped follow-on PR.

## 9. Acceptance criteria for freezing

- No parallel or competing plugin lifecycle/registry/study/event/result infrastructure is introduced.
- Each shared responsibility has exactly one authoritative owner and a documented public contract.
- Core remains headless; Application owns study execution and mutation; UI remains projection/interaction.
- Plugin lifecycle, dependencies, registration conflicts, activation rollback, and teardown have explicit semantics.
- Study success/failure/cancellation and result publication are consistent across plugin kinds.
- CPU fallback and optional accelerator capabilities are explicit; unsupported GPU/NPU paths are reported rather than implied.
- A reference plugin and a second distinct plugin can use the shared contracts without copying infrastructure code.
- Architecture and Modification Register are updated together.
- No tests/CI are run or required unless explicitly authorized; any later verification is reported precisely.

## 10. Relationship to existing architecture

This document is an amendment proposal, not a parallel architecture. It supplements the existing GridForge V2 Architecture Freeze and plugin platform philosophy. If repository contracts conflict, stop and reconcile the conflict before implementation; the existing frozen architecture remains authoritative until this amendment is reviewed and merged.
