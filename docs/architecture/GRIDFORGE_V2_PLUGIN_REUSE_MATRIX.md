# GridForge V2 — Plugin Infrastructure Reuse Matrix

**Status:** Current-main architecture reuse audit (2026-11-02)  
**Authority:** Subordinate to the frozen GridForge V2 Core/Application/UI architecture and the shared Plugin SDK principles merged by PR #675.  
**Purpose:** Make existing ownership explicit before introducing any shared SDK package or template.

## Reuse matrix

| Responsibility | Existing authoritative owner / contract | Plugin rule | Confirmed gap / action |
|---|---|---|---|
| Core engineering model and topology | Core model/network contracts and Core validation | Never create a plugin-owned competing electrical network or use graphics as engineering truth | Plugin equipment/model capabilities must use canonical Core model and terminal/network contracts |
| Controlled mutation and transactions | Application command manager, services and Transaction | Submit typed commands through Application; do not commit/rollback independently | Host composition must supply the existing Application services; plugins do not own a second transaction manager |
| Headless study request/context | `StudyRequest`, `StudyExecutionContext`, `StudyCancellationToken` | Handler signature must match the canonical callable contract | Reuse existing contracts; do not create a plugin scheduler |
| Study scheduling, cancellation and outcomes | Canonical Application StudyService | One scheduler and one canonical StudyResult store | Identity-aware handler lifecycle and active-study protection remain owned by StudyService |
| Canonical events | ApplicationEventBus and typed Application events | Subscribe/unsubscribe to the Application bus and release subscriptions on teardown | No new event bus; completion projections read canonical stored results |
| Study result lookup | StudyService result lookup and Application read services | Preserve project ID, activation generation, study ID and source revision | Plugin read models are projections only |
| UI plugin lifecycle | Existing `ui/plugins/` contracts, loader, registry, manager, state store and context | Reuse UI composition lifecycle only for UI contributions | Keep distinct from headless StudyService lifecycle |
| Plugin command/service composition | Existing Application command/service contracts and PluginContext | Plugin lifecycle adapter composes host services; it must not duplicate a registry or transaction manager | Required host composition remains an explicit integration dependency |
| Configuration and persistence | Existing project/persistence ownership plus explicit plugin persistence adapter | Validate schemas and versioning at the appropriate owner; plugin-specific records remain plugin-specific | Do not introduce a global configuration store without evidence from multiple plugins |
| Compute backend dispatch | Domain algorithm backend adapter plus explicit capability detection | CPU is baseline; advertise GPU/NPU only for implemented computations and report unsupported explicit selections | Hardware/device availability alone is not evidence of algorithm support |
| Diagnostics | Existing Application error/event contracts plus domain-specific structured diagnostics | Reuse canonical errors and add plugin-specific context; do not add a second general diagnostics bus | Consolidate only after repeated concrete plugin requirements establish stable semantics |
| Read-only UI projections | Existing Application events/read models and `ui/plugins/` composition | Project canonical results; never mutate Core or treat chart state as truth | Plugin telemetry/read models remain projections |
| Descriptor/version/dependency validation | Existing plugin contracts where they apply; no single cross-namespace SDK API yet | Do not create a universal base class or duplicate UI registry | Keep concrete SDK API provisional until materially different plugins establish shared requirements |

## Motor Dynamics reconciliation

1. The Motor Dynamics study handler must conform to the canonical Application study callable contract.
2. StudyService owns scheduling, cancellation, status, canonical StudyResult storage and event publication.
3. Plugin result publishers must retrieve the canonical stored successful result before updating plugin-specific read models.
4. The plugin must receive its host Application services through explicit composition; it must not silently construct parallel infrastructure.
5. CPU is the portable baseline. CUDA/GPU or NPU support may be claimed only for the exact implemented solver path and must report capability/fallback semantics. An inference provider is not proof of NPU physics execution.
6. Motor model-to-network representation must preserve canonical equipment and terminal identity. A plugin-specific numerical representation must not become a competing persistent motor model or network.

## Extraction decision

Do **not** create a general SDK runtime, new plugin manager, scheduler, event bus, result store, transaction manager or configuration store merely to make plugin code convenient. Reuse the canonical owners. Extract a shared abstraction only after multiple materially different plugins demonstrate the same stable requirement and the abstraction does not weaken existing ownership boundaries.

## Current integration evidence boundary

This matrix is an architecture/reuse contract, not an end-to-end plugin activation or compute-backend verification report. Host composition, transactional behavior, numerical results and CPU/GPU/NPU execution must be verified independently. Open/draft PRs are not mainline capabilities until reconciled and merged.

## Verification boundary

Static source/documentation review only. No tests, CI, syntax checks, imports, application startup, numerical validation, or hardware validation are claimed by this document.
