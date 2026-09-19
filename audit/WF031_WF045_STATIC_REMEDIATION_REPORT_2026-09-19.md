# GridForge V2 — WF-031–WF-045 Static Remediation Report

Date: 2026-09-19
Repository: pandaraseswari03-collab/GridForge
Branch: main
Status: STATICALLY REMEDIATED — VERIFICATION DEFERRED

## Scope

This remediation was performed from static inspection of the current repository. No tests, pytest, CI, application startup, or runtime verification were executed.

The correction preserves the frozen Core → Application → UI/SLD architecture and extends the existing ProjectLifecycleService activation/rollback transaction rather than introducing a parallel lifecycle.

## Consolidated correction results

| RCA / finding cluster | Static correction |
|---|---|
| RCA-1 / WF-035, WF-036, WF-038–WF-040 | Added Application-owned SAVE/DISCARD/CANCEL transition decision contract. Dirty transitions are resolved before target activation. SAVE persists first; DISCARD reconstructs the persisted project; CANCEL returns without transition. |
| RCA-2 / WF-031, WF-034, WF-035, WF-041, WF-044, WF-045 | Presentation/workspace activation is now an Application lifecycle activation callback. Workspace state is snapshotted and restored on failure. The previous-project rollback path no longer calls Application.close_project(). |
| RCA-3 / WF-044–WF-045 | Semantic mutation events carry project_id + activation_generation. ValidationResult now carries the same project/generation scope plus model/topology revision. |
| RCA-4 / ProjectLoaded | ProjectLoaded is explicitly documented as an Application project-activation event, not proof of UI workspace readiness. UI workspace publication remains a separate presentation boundary. |
| RCA-5 / WF-042-A | ProjectLifecycleService remains an internal lifecycle primitive; Application remains the public study-interlocked orchestration boundary. No second study state machine was introduced. |
| WF-037-A | Static inspection established Network.rebuild_topology() as derived-state synchronization: NetworkState.topology_rebuilt() clears topology_dirty without incrementing topology_revision. Save therefore retains the existing derived-only normalization behavior. |
| WF-031-C | create_application() remains a headless composition root. GUI presentation is supplied explicitly by the UI adapter through a presentation factory/serializer/deserializer contract. No fake Qt-free presentation implementation was added. |
| WF-032-D | RevisionService now marks successful Application model/control/protection/application mutation commands dirty. SLD commands retain the separate presentation revision path. Undo/redo continue to operate on the same revision transition history. |

## Key affected modules

- core/application/application.py
- core/application/project_lifecycle.py
- core/application/project_transition.py
- core/application/revision_service.py
- core/application/validation.py
- core/application/events.py
- core/application/__init__.py
- ui/workspace/project_workspace.py
- ui/workspace/project_workspace_adapter.py
- audit/MASTER_AUDIT_REGISTER.csv

## Transaction invariant

The corrected transition path is:

REQUEST
→ DIRTY CHECK
→ SAVE / DISCARD / CANCEL
→ PREPARE
→ PRESENTATION/WORKSPACE ACTIVATE
→ NETWORK/RUNTIME ACTIVATE
→ PROJECT-STATE ACTIVATE
→ COMMIT
→ PUBLISH

For a failed A → B activation, the existing ProjectLifecycleService rollback stack restores the previous Application network/runtime/project state. The UI workspace activation now participates in that same stack, so a presentation failure cannot deliberately convert a valid A → B failure into A → NO_PROJECT.

## Discard semantics

Discard is implemented as persisted-state reconstruction through the Application lifecycle loader/activation boundary. It does not use undo, redo, history clearing, or a blind dirty flag mutation. A load/reconstruction failure occurs before target transition and leaves the existing project unchanged.

For an unnamed project with no persisted checkpoint, discard is treated as abandonment of its unsaved state at the surrounding transition boundary; no persisted state is invented.

## Save-time topology semantics

Static inspection of Network.rebuild_topology() and NetworkState.topology_rebuilt() establishes that the rebuild operation reconstructs derived topology state and marks it synchronized. It does not create a new authoritative topology revision. The persistence-time normalization remains inside the existing atomic save path.

## Verification state

All affected entries remain:

**REMEDIATED — VERIFICATION DEFERRED**

No claim of runtime verification is made. Runtime/test verification is intentionally deferred to the later verification phase.
