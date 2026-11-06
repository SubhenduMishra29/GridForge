# GF-MASTER-0092 — Duplicate / Legacy Contingency Authority

**Repository:** `pandaraseswari03-collab/GridForge`  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Verification mode:** Static source/dependency inspection only

## Root Cause

Migration from the legacy solver architecture to the V2 Application/StudyService architecture was incomplete, leaving the old contingency implementation as a competing authority.

## Correction

The canonical authority is now:

```text
Application StudyRequest
  -> Application StudyService
  -> StudyExecutionContext
  -> StudyPreparationService
  -> core.analysis.contingency
  -> isolated ProjectSnapshot Network
  -> canonical topology rebuild/snapshot
  -> PowerFlowPreparation
  -> PowerFlowAnalysis
  -> ContingencyResult
  -> Application StudyResult
```

The Application composition root now registers exactly one `contingency` study handler. The handler consumes the detached study snapshot and delegates engineering execution to `core.analysis.contingency.ContingencyAnalysis`.

The canonical contingency module continues to own only contingency-specific case generation/evaluation. Power-flow preparation and numerical execution remain delegated to the existing V2 `PowerFlowPreparation` and `PowerFlowAnalysis` authorities.

A static defect in the canonical element-type filter was also corrected: `_normalize_element_types()` now correctly receives the analysis instance required to inspect the canonical Network registry.

## Legacy Authority Disposition

The executable legacy package was removed:

- `core/solver/contingency/contingency_analyzer.py`
- `core/solver/contingency/contingency_case.py`
- `core/solver/contingency/n_minus_one.py`
- `core/solver/contingency/violation_checker.py`

The removed implementation previously performed its own outage mutation, `Network.build_ybus()`, injected load-flow solver execution, and independent violation checks. Those responsibilities are no longer available through a second contingency entry point.

## Static Dependency Reconciliation

- Current source tree contains `core/analysis/contingency.py` as the only contingency implementation module.
- Application study registration is in `core/application/bootstrap.py`.
- `StudyService`, `StudyRequest`, `StudyExecutionContext`, and `StudyResult` remain the single Application study boundary.
- Contingency returns the canonical `ContingencyResult` as the `StudyResult.value` payload; no second Application result registry was introduced.
- No active documentation/specification path inspected during this remediation identified the deleted legacy package as the current implementation authority.
- Existing historical audit references to the legacy architecture are retained as historical evidence.

## Verification Boundary

**Finding status:** REMEDIATED  
**Static verification:** COMPLETE  
**Runtime verification:** DEFERRED

No startup, GUI, numerical contingency run, pytest, or CI verification is claimed by this remediation.
