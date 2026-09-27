# GF-MASTER-0094 — Study Cases Run Study Remediation

**Repository:** `pandaraseswari03-collab/GridForge`  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Mode:** Static source correction / static re-audit only. No tests, CI, startup, GUI, or runtime execution.

## Finding identity

GF-MASTER-0094 remains the authoritative finding for the Study Cases **Run Study** production wiring defect. It is not repurposed for GF-MASTER-0099 result-integrity work.

## Corrections

1. Added immutable Application-owned `StudyCaseDefinition` in `core/application/study.py`.
2. The definition preserves `study_id`, `study_type`, display identity, and the existing typed configuration contract. Known study types validate against:
   - `PowerFlowStudyConfiguration`
   - `ShortCircuitStudyConfiguration`
   - `TransientStabilityStudyConfiguration`
   - existing contingency use of `PowerFlowStudyConfiguration`
3. `Application.execute_study()` captures valid structured requests as Application-owned runnable Study Cases without changing its existing provenance/topology/snapshot safeguards.
4. Added `Application.study_case()`, `Application.study_cases`, and `Application.execute_study_case()`. The latter constructs a fresh immutable `StudyRequest` from the Application-owned case plus the current active project identity, activation generation, and current `ProjectRevision`, then delegates to `Application.execute_study()`.
5. `StudyProjection` now emits immutable structured `StudyCaseRow` objects instead of collapsing identity into display strings.
6. `StudyCasesPanelWidget` retains structured rows and selected `UUID`; Run Study no longer passes `QListWidgetItem.text()` as study identity and exposes `selected_case()` / `selected_case_id()`.
7. Added dedicated `ui/controllers/study_case_controller.py`. It resolves the structured case and calls the Application boundary only; it does not access Core, topology, snapshots, solvers, or `StudyService`.
8. `main.py` now constructs the dedicated controller and explicitly connects `study_cases_panel.set_run_handler(study_case_controller.run_study)`.
9. Existing `StudyService.execute()`, registered handlers, `StudyPreparationService`, lifecycle events, and GF-MASTER-0099 read/result projection remain authoritative.

## Static production path

```text
Study Cases Panel
  -> selected StudyCaseRow.study_id
  -> StudyCaseController.run_study(UUID)
  -> Application.study_case(UUID)
  -> Application.execute_study_case(UUID)
  -> StudyRequest(current project/generation/revision + typed configuration)
  -> Application.execute_study()
  -> canonical topology validation/snapshot
  -> detached ProjectSnapshot
  -> StudyExecutionContext
  -> StudyService.execute()
  -> registered study handler
  -> StudyPreparationService
  -> Core Analysis / Solver
  -> StudyResult + lifecycle event
  -> StudyProjection
  -> structured StudyCaseRow
  -> Study Cases Panel
```

## Persistence status

The repository audit found **no existing Study Case persistence authority** in the project package. `project.json` currently persists project/network, measurement, dynamic-model, protection, and control state, but not Study Cases. Study results are also runtime/transient under the existing Application StudyService.

Accordingly, this correction does **not** invent a second persistence store or hide Study Case state in Qt. Structured cases are retained for the active Application lifetime from canonical study requests. A fresh project activation does not manufacture persisted Study Cases that the repository currently has no persistence contract for.

## Static verification

- Run Study button exists: verified.
- Production run handler is connected in `main.py`: verified.
- Stable structured study identity is preserved through projection and panel: verified.
- Display-string parsing is absent from the execution path: verified.
- Dedicated Study Case controller exists and does not bypass Application: verified.
- `Application.execute_study()` remains the canonical orchestration entry point: verified.
- Current project identity, activation generation, `ProjectRevision`, topology snapshot, detached `ProjectSnapshot`, and `StudyExecutionContext` remain Application-owned: verified.
- `StudyService` remains the sole study execution authority: verified.
- Existing registered handlers remain unchanged: verified.
- Study lifecycle events continue into `StudyProjection`: verified.
- GF-MASTER-0099 result/read-model path is not bypassed: verified.
- No duplicate StudyService/StudyManager/ResultManager/persistence authority introduced: verified.
- Runtime/tests/CI/startup/GUI verification: **deferred / not performed**.

## Status

**REMEDIATED — VERIFICATION DEFERRED**

The source-level production Run Study path is now statically traceable end-to-end. Persistence of Study Case definitions across project save/reopen remains explicitly outside the repository's existing persistence contract and was not invented during this targeted remediation.
