# GF-DYN-WF Workflow Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a complete, deterministic, auditable Power Flow, Short Circuit, and Transient Stability study workflow from semantic Study Case selection through Application execution, Core analysis, typed result conversion, read-model projection, persistence, reload, and failure/cancellation handling.

**Architecture:** Keep existing typed Core study configurations and preparation/analysis contracts authoritative. Add only the missing Application-owned Study Case, explicit request/runtime separation, study-specific result adapters/read models, Application result lookup, semantic lifecycle payloads, and a thin UI Study Controller that passes stable case identity to Application. Persist durable Study Cases with the existing project package and never persist derived execution artifacts.

**Tech Stack:** Python, dataclasses, UUID, MappingProxyType, pytest, existing Qt presentation layer, existing GridForge project JSON/package persistence.

**Spec:** `docs/superpowers/specs/2026-09-17-gf-dyn-wf-remediation.md`

## Global Constraints

- Frozen architecture takes precedence over legacy code.
- The Application layer is the sole communication/orchestration boundary between UI and Core.
- Existing typed Core study configuration classes remain authoritative and are not duplicated.
- Prepared numerical objects are derived execution snapshots and are never persisted as Study Cases.
- UI must not call Core analysis/solvers or interpret Core result classes.
- Study lifecycle events must carry semantic lifecycle information, not arbitrary Core result graphs.
- No obsolete Dynamics implementation such as `DynamicMachineModel` or removed `state_vector.py` may be recreated.
- Tests must be written before implementation for each behavior group.
- No finding may be marked CLOSED without actual verification evidence.
- Historical audit findings must remain traceable.

---

## Repository Change Map

### Create

- `core/application/study_case.py` — immutable Application-owned Study Case and typed case catalogue/state contract.
- `core/application/study_results.py` — study-specific immutable Application read models and Core-result adapters.
- `ui/controllers/study_controller.py` — thin UI/Application study orchestration adapter.
- `tests/application/test_study_case.py` — Study Case identity/type/configuration validation.
- `tests/application/test_study_results.py` — result adapter/read-model contract tests.
- `tests/application/test_study_workflow.py` — Application execution/failure/cancellation/result lookup tests.
- `tests/projects/test_study_case_persistence.py` — persistence round-trip and runtime-artifact exclusion tests.
- `tests/ui/test_study_cases_panel.py` — semantic case identity and controller invocation tests.
- `audit/MASTER_AUDIT_REGISTER.md` — only if repository evidence confirms this is the requested canonical authority after inspection.
- `audit/MASTER_AUDIT_REGISTER.csv` — only if repository evidence confirms this is the requested canonical authority after inspection.

### Modify

- `core/application/study.py` — replace overloaded configuration/result `Any` contracts with explicit typed Application request/runtime/result boundaries while preserving registered study types and cooperative cancellation.
- `core/application/application.py` — expose Study Case catalogue/execution/result-read APIs and preserve the existing Application facade role.
- `core/application/bootstrap.py` — compose Study Case state, typed request construction, runtime dependencies, result adapters, and the three registered studies.
- `core/application/events.py` — make study lifecycle payloads explicitly semantic and result-reference based without transporting Core results.
- `core/application/project_lifecycle.py` — install/replace Study Case state on new/open project and pass it to persistence on save.
- `core/persistence/project_persistence.py` — load/save durable `study_cases` while excluding derived/runtime objects.
- `ui/panels/study_cases_panel.py` — retain `study_case_id` separately from display text and emit stable identity to the injected handler.
- `ui/projection/study_projection.py` — consume Application study lifecycle/read-model semantics rather than Core result objects.
- relevant UI bootstrap/composition file discovered during the implementation audit — compose the Study Controller through the existing UI/Application bridge rather than MainWindow-owned execution.
- agent-facing architecture guidance discovered during the implementation audit — document Study Case/Request/Prepared Study/Result/Read Model ownership.
- canonical audit register/reconciliation documents discovered during the implementation audit — record only evidenced remediation status.

## Task 1: Freeze the current contracts and test harness

**Files:**
- Read: `core/application/study.py`, `core/application/application.py`, `core/application/bootstrap.py`, `core/application/events.py`, `core/application/project_lifecycle.py`
- Read: `core/persistence/project_persistence.py`, `ui/panels/study_cases_panel.py`, `ui/projection/study_projection.py`
- Read: existing `tests/application`, `tests/projects`, and UI test conventions.
- Test: `tests/application/test_study_workflow.py`

**Interfaces:**
- Consumes: current `StudyRequest`, `StudyResult`, `StudyService`, event bus, project lifecycle, and three registered study handlers.
- Produces: executable regression tests that describe current failure modes before contract migration.

- [ ] **Step 1: Add failing tests for the target Study Case and result contracts**

```python
from uuid import UUID

import pytest

from core.application.study_case import StudyCase
from core.application.study import StudyRequest


def test_study_case_has_stable_semantic_identity_and_typed_configuration():
    case = StudyCase.create("Base Power Flow", "power_flow", configuration={})
    assert isinstance(case.case_id, UUID)
    assert case.name == "Base Power Flow"
    assert case.study_type == "power_flow"


def test_study_request_requires_explicit_case_identity():
    with pytest.raises(TypeError):
        StudyRequest(study_type="power_flow", configuration={})
```

- [ ] **Step 2: Run the focused test file and confirm the new contract is not yet implemented**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: FAIL because the Application Study Case module and explicit request contract do not yet exist.

- [ ] **Step 3: Do not weaken the test to match the old `Any` contract**

The test must continue to require semantic case identity and must not accept display strings as execution identity.

- [ ] **Step 4: Record the exact baseline failure output in the remediation log/PR notes**

Use the actual command output; do not write a success claim before execution.

- [ ] **Step 5: Commit the test-only baseline**

```bash
git add tests/application/test_study_workflow.py
git commit -m "test: define GF-DYN-WF study workflow contract"
```

## Task 2: Implement Application-owned Study Case and catalogue

**Files:**
- Create: `core/application/study_case.py`
- Test: `tests/application/test_study_case.py`

**Interfaces:**
- Consumes: existing typed Core configuration classes; UUID identity conventions used by Application.
- Produces: `StudyCase`, `StudyCaseCatalogue` with stable case lookup/add/remove/replace operations.

- [ ] **Step 1: Write validation tests**

```python
from uuid import uuid4

import pytest

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.application.study_case import StudyCase, StudyCaseCatalogue


def test_study_case_rejects_empty_identity_and_type():
    with pytest.raises(ValueError):
        StudyCase(case_id=uuid4(), name="Base", study_type="", configuration=PowerFlowStudyConfiguration())


def test_study_case_rejects_wrong_configuration_for_study_type():
    with pytest.raises(TypeError):
        StudyCase(case_id=uuid4(), name="Base", study_type="power_flow", configuration=object())


def test_catalogue_rejects_duplicate_case_ids():
    case = StudyCase.create("Base", "power_flow", PowerFlowStudyConfiguration())
    catalogue = StudyCaseCatalogue([case])
    with pytest.raises(ValueError):
        catalogue.add(case)
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `pytest tests/application/test_study_case.py -q`

Expected: FAIL because the module does not yet exist.

- [ ] **Step 3: Implement the minimum immutable Study Case**

The constructor must accept `case_id: UUID`, `name: str`, `study_type: str`, `configuration: object`, and optional immutable metadata. Validation must map the three supported study types to their existing Core configuration classes. Do not copy electrical fields into Application classes.

- [ ] **Step 4: Implement the catalogue**

Use a private dictionary keyed by UUID. Expose immutable snapshots through `cases()` and lookup through `get(case_id)`. Reject duplicate IDs and unknown IDs. Preserve insertion order for UI presentation.

- [ ] **Step 5: Run focused tests**

Run: `pytest tests/application/test_study_case.py -q`

Expected: PASS for identity, duplicate identity, type/configuration, lookup, and immutable metadata tests.

- [ ] **Step 6: Commit**

```bash
git add core/application/study_case.py tests/application/test_study_case.py
git commit -m "feat: add application-owned study cases"
```

## Task 3: Replace overloaded Study Request and Result contracts

**Files:**
- Modify: `core/application/study.py`
- Test: `tests/application/test_study_workflow.py`

**Interfaces:**
- Consumes: `StudyCase`, typed Core configurations, `StudyCancellationToken`.
- Produces: explicit `StudyRequest(case_id, study_id, study_type, configuration, runtime_context)`, immutable execution result metadata, and existing cancellation behavior.

- [ ] **Step 1: Add tests for request/runtime separation**

```python
from uuid import uuid4

from core.application.study import StudyRequest


def test_request_keeps_runtime_context_separate_from_configuration():
    case_id = uuid4()
    request = StudyRequest(
        study_id=uuid4(),
        case_id=case_id,
        study_type="transient_stability",
        configuration=object(),
        runtime_context={"prepared_power_flow": object(), "power_flow_result": object()},
    )
    assert request.case_id == case_id
    assert request.runtime_context["prepared_power_flow"] is not request.configuration
```

- [ ] **Step 2: Add tests that arbitrary Core result objects cannot be exposed as the Application UI result contract**

The test must assert that `StudyService.execute()` stores the adapted Application read model/result reference rather than accepting a raw Core result as a UI-facing `value` field.

- [ ] **Step 3: Run focused tests and confirm the old contract fails them**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: FAIL against the old `configuration: Mapping[str, Any]` / `value: Any` contract.

- [ ] **Step 4: Implement explicit request fields**

Use `case_id: UUID`, `study_id: UUID`, `study_type: str`, typed `configuration: object`, and immutable `runtime_context: Mapping[str, object]`. Validate that the configuration is one of the registered typed Core study configuration classes for the declared study type. Runtime context must be separate and must not be serialized by project persistence.

- [ ] **Step 5: Keep cooperative cancellation intact**

Preserve `cancel()` and cancellation token behavior. A cancelled execution must produce a cancelled lifecycle state and must never publish `StudyCompleted`.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: PASS for request validation, unknown type rejection, runtime separation, failure, cancellation, and result lookup behavior after subsequent adapter integration.

- [ ] **Step 7: Commit**

```bash
git add core/application/study.py tests/application/test_study_workflow.py
git commit -m "refactor: separate study configuration from runtime context"
```

## Task 4: Add study-specific result adapters and read models

**Files:**
- Create: `core/application/study_results.py`
- Test: `tests/application/test_study_results.py`

**Interfaces:**
- Consumes: actual Core result classes returned by Power Flow, Short Circuit, and Transient Stability analyses.
- Produces: immutable `PowerFlowReadModel`, `ShortCircuitReadModel`, `TransientStabilityReadModel`, plus adapters with deterministic `from_core(...)` conversion.

- [ ] **Step 1: Inspect exact Core result fields before writing adapter assertions**

Fetch the current result-producing modules and record the actual field names. Do not invent fields such as `converged`, `line_loading`, or `transformer_loading` when they are absent from the authoritative producer.

- [ ] **Step 2: Write adapter tests against actual producer fields**

```python

def test_power_flow_adapter_exposes_application_semantics_without_core_object():
    read_model = PowerFlowResultAdapter.from_core(core_result)
    assert read_model.result_id
    assert read_model.success == core_result.success
    assert not hasattr(read_model, "core_result")
```

Equivalent tests must exist for Short Circuit and Transient Stability using the actual Core result contract.

- [ ] **Step 3: Run focused tests and confirm the adapters are missing**

Run: `pytest tests/application/test_study_results.py -q`

Expected: FAIL because the adapter/read-model module does not yet exist.

- [ ] **Step 4: Implement immutable read models**

Each read model must contain stable `result_id`, `study_id`, `study_type`, status, and study-specific scalar/collection semantics required by current UI presentation. Collections must be immutable snapshots. Do not retain a reference to the Core result object.

- [ ] **Step 5: Implement adapters using only real Core fields**

For each study, explicitly copy the fields that the Application/UI needs. If a UI field cannot be derived from the current Core result contract, record it as a residual contract gap rather than inventing it.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/application/test_study_results.py -q`

Expected: PASS with no Core result leakage.

- [ ] **Step 7: Commit**

```bash
git add core/application/study_results.py tests/application/test_study_results.py
git commit -m "feat: add typed study result read models"
```

## Task 5: Make StudyService own adapted result registration and semantic lifecycle events

**Files:**
- Modify: `core/application/study.py`
- Modify: `core/application/events.py`
- Modify: `core/application/application.py`
- Test: `tests/application/test_study_workflow.py`

**Interfaces:**
- Consumes: study-specific result adapters/read models and existing Application event bus.
- Produces: `execute_study(request)`, `study_result(study_id)`, semantic lifecycle events with `study_id`, `study_type`, and `result_id` where a result exists.

- [ ] **Step 1: Write event tests**

```python

def test_completed_event_references_result_without_embedding_core_result(event_bus, application):
    events = []
    event_bus.subscribe("study.completed", events.append)
    result = application.execute_study(valid_request)
    assert result.result_id is not None
    assert events[-1].payload["study_id"] == str(result.study_id)
    assert events[-1].payload["result_id"] == str(result.result_id)
    assert "value" not in events[-1].payload
```

- [ ] **Step 2: Add failure and cancellation tests**

Assert that failure publishes `study.failed`, cancellation publishes `study.cancelled`, and neither path publishes `study.completed`.

- [ ] **Step 3: Implement result registration after adaptation**

The registered result must be an Application result/read-model record with a generated `result_id`. `StudyService` must never publish a raw Core result in event payloads.

- [ ] **Step 4: Expose lookup through `Application.study_result(study_id)`**

Return the Application result/read model, not a Core result object.

- [ ] **Step 5: Run focused tests**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: PASS for success, unknown type, failure, cancellation, event semantics, and result lookup.

- [ ] **Step 6: Commit**

```bash
git add core/application/study.py core/application/events.py core/application/application.py tests/application/test_study_workflow.py
git commit -m "feat: expose semantic study lifecycle and results"
```

## Task 6: Recompose bootstrap and establish the canonical configuration path

**Files:**
- Modify: `core/application/bootstrap.py`
- Modify: `core/application/application.py` if required by composition
- Test: `tests/application/test_study_workflow.py`

**Interfaces:**
- Consumes: `StudyCaseCatalogue`, typed Core configurations, `StudyPreparationService`, existing Core analysis classes.
- Produces: one Application-owned execution path from Study Case ID to typed Study Request to registered Core handler.

- [ ] **Step 1: Add a test that constructs an Application Study Case and executes it by case ID**

The test must create a Power Flow Study Case with the existing `PowerFlowStudyConfiguration`, register/use the normal bootstrap composition, and invoke the Application case-execution method without importing or invoking `PowerFlowAnalysis` from the test's UI-facing path.

- [ ] **Step 2: Run the test and confirm current bootstrap cannot execute a case ID**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: FAIL because bootstrap currently registers handlers that expect generic request mappings and does not provide a Study Case catalogue/execution method.

- [ ] **Step 3: Compose the Study Case catalogue in the Application**

New/open project state must own the catalogue. Bootstrap must not create a second study execution service; it must compose the existing `StudyService` and the new Application state around it.

- [ ] **Step 4: Construct requests from cases**

Add an Application operation whose only semantic input is `case_id`. It retrieves the Study Case, creates one execution `study_id`, copies the typed configuration, and builds an explicit runtime context only when the selected study requires derived dependencies.

- [ ] **Step 5: Handle Transient Stability dependencies explicitly**

Move `prepared_power_flow` and `power_flow_result` out of `request.configuration`. Put them into the request runtime context after obtaining them through the existing Application/Core preparation path. Do not persist them.

- [ ] **Step 6: Keep the three registrations**

Verify `power_flow`, `short_circuit`, and `transient_stability` remain registered. No valid registration may be removed.

- [ ] **Step 7: Run focused tests**

Run: `pytest tests/application/test_study_workflow.py -q`

Expected: PASS for case selection, typed configuration construction, three study registrations, and explicit transient runtime dependencies.

- [ ] **Step 8: Commit**

```bash
git add core/application/bootstrap.py core/application/application.py tests/application/test_study_workflow.py
git commit -m "feat: execute studies from application study cases"
```

## Task 7: Add project persistence for durable Study Cases

**Files:**
- Modify: `core/persistence/project_persistence.py`
- Modify: `core/application/project_lifecycle.py`
- Modify: `core/application/bootstrap.py`
- Test: `tests/projects/test_study_case_persistence.py`

**Interfaces:**
- Consumes: `StudyCaseCatalogue` and existing project package persistence.
- Produces: `LoadedProject.study_cases`, JSON `study_cases` durable state, round-trip load/save, and project lifecycle installation.

- [ ] **Step 1: Write persistence tests**

```python

def test_study_cases_round_trip_without_runtime_artifacts(tmp_path):
    project = make_project_with_one_power_flow_case()
    path = tmp_path / "example.gridforge"
    persistence.save(project.context, project.network, project.presentation, path,
                     study_cases=project.study_cases)
    loaded = persistence.load(path)
    assert loaded.study_cases[0].case_id == project.study_cases[0].case_id
    assert loaded.study_cases[0].study_type == "power_flow"
    assert "prepared_power_flow" not in json.dumps(loaded.study_cases[0].to_dict())
```

Also test missing `study_cases` defaults to an empty tuple for backward-compatible package loading if that is consistent with the existing schema/version policy.

- [ ] **Step 2: Run tests and confirm the current persistence signature lacks Study Cases**

Run: `pytest tests/projects/test_study_case_persistence.py -q`

Expected: FAIL because `ProjectPersistenceService.save/load` currently have no Study Case contract.

- [ ] **Step 3: Implement serialization of only durable fields**

Serialize UUIDs as strings, study type, display name, typed Core configuration fields, and durable metadata. Do not serialize runtime context, prepared objects, solver instances, event managers, Core result objects, Qt objects, or widgets.

- [ ] **Step 4: Integrate `LoadedProject.study_cases`**

Deserialization must validate case IDs, names, study types, and typed configuration payloads. Invalid Study Case data must raise `ProjectPersistenceError` with an actionable message.

- [ ] **Step 5: Integrate lifecycle installation**

New project gets an empty catalogue. Open project installs loaded cases before the UI receives the project-loaded event. Save passes the current catalogue to persistence.

- [ ] **Step 6: Run persistence tests**

Run: `pytest tests/projects/test_study_case_persistence.py -q`

Expected: PASS for save/load, round trip, invalid payload rejection, and runtime-artifact exclusion.

- [ ] **Step 7: Commit**

```bash
git add core/persistence/project_persistence.py core/application/project_lifecycle.py core/application/bootstrap.py tests/projects/test_study_case_persistence.py
git commit -m "feat: persist application study cases"
```

## Task 8: Wire the UI through a dedicated Study Controller

**Files:**
- Create: `ui/controllers/study_controller.py`
- Modify: `ui/panels/study_cases_panel.py`
- Modify: existing UI bootstrap/composition file identified during the audit
- Test: `tests/ui/test_study_cases_panel.py`

**Interfaces:**
- Consumes: Application Study Case catalogue and Application case execution method.
- Produces: panel rows carrying stable `study_case_id`, a controller callback that calls Application only, and no direct Core imports from the panel/controller.

- [ ] **Step 1: Write panel tests**

```python

def test_panel_keeps_case_id_separate_from_display_text(qtbot):
    panel = StudyCasesPanelWidget()
    panel.set_cases([{"case_id": "case-1", "name": "Base Power Flow"}])
    captured = []
    panel.set_run_handler(captured.append)
    panel._list.setCurrentRow(0)
    panel._run_selected()
    assert captured == ["case-1"]
```

The test must use the repository's actual Qt test fixture/setup conventions.

- [ ] **Step 2: Write controller test**

```python

def test_controller_forwards_case_id_to_application(mocker):
    application = mocker.Mock()
    controller = StudyController(application)
    controller.run_case("case-1")
    application.execute_study_case.assert_called_once_with("case-1")
```

- [ ] **Step 3: Run tests and confirm current panel passes display text**

Run: `pytest tests/ui/test_study_cases_panel.py -q`

Expected: FAIL because current `set_cases` accepts display strings and `_run_selected` sends `item.text()`.

- [ ] **Step 4: Implement semantic row storage**

Use the Qt item's user-data role or the repository's existing model/data-role convention to store `study_case_id`. Display name remains presentation text only.

- [ ] **Step 5: Implement the thin Study Controller**

Its run method accepts a case ID and invokes the Application facade. It must not import Core analysis classes, persistence services, or solver classes.

- [ ] **Step 6: Compose through existing UI bootstrap**

Wire the controller through the existing presentation composition boundary. Do not put study execution code in MainWindow or the panel.

- [ ] **Step 7: Run UI tests**

Run: `pytest tests/ui/test_study_cases_panel.py -q`

Expected: PASS for semantic identity and Application invocation.

- [ ] **Step 8: Commit**

```bash
git add ui/controllers/study_controller.py ui/panels/study_cases_panel.py tests/ui/test_study_cases_panel.py <actual-ui-composition-file>
git commit -m "feat: route study case execution through application controller"
```

## Task 9: Project result projection and UI lifecycle read path

**Files:**
- Modify: `ui/projection/study_projection.py`
- Modify: Application result/event integration files as required by the actual projection contract
- Test: `tests/ui/test_study_projection.py` if an existing projection test file is present; otherwise create it.

**Interfaces:**
- Consumes: semantic StudyStarted/Completed/Failed/Cancelled events and Application read models.
- Produces: UI lifecycle/result rows without inspecting `result.value` or Core result objects.

- [ ] **Step 1: Write projection tests**

```python

def test_completed_projection_uses_result_id_and_application_read_model():
    projection = StudyProjection(read_result=lambda result_id: power_flow_read_model)
    projection.apply(study_completed_event)
    assert projection.rows[-1].result_id == power_flow_read_model.result_id
    assert not hasattr(projection.rows[-1], "core_result")
```

- [ ] **Step 2: Run projection tests and document the current behavior**

Run: `pytest tests/ui/test_study_projection.py -q`

Expected: the test should fail if the projection lacks result lookup/read-model consumption; if the existing projection already satisfies part of the contract, retain that behavior and only add missing assertions.

- [ ] **Step 3: Implement read-model projection**

The projection receives Application semantics only. It may display lifecycle state and selected read-model fields. It must never import Core result classes or inspect arbitrary `Any` values.

- [ ] **Step 4: Run the projection test**

Run: `pytest tests/ui/test_study_projection.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ui/projection/study_projection.py tests/ui/test_study_projection.py
 git commit -m "feat: project application study read models"
```

## Task 10: Agent-facing architecture guidance and register-authority resolution

**Files:**
- Read: all current audit/reconciliation documents and `audit/` tree if present.
- Modify/Create: canonical agent-facing architecture guidance identified by repository evidence.
- Modify/Create: canonical `audit/MASTER_AUDIT_REGISTER.md` and `.csv` only after authority is established.

**Interfaces:**
- Consumes: implemented contracts and verification evidence from Tasks 1–9.
- Produces: durable architectural training rules and synchronized audit status.

- [ ] **Step 1: Inspect current audit files directly**

Confirm whether `audit/MASTER_AUDIT_REGISTER.md` and `.csv` exist on the remediation branch. If absent, identify the actual authoritative register and do not silently invent a replacement.

- [ ] **Step 2: Write the architecture guidance tests/checks**

Search for prohibited concepts in the final code: UI imports of Core study analysis, panel calls to Core analysis, `StudyRequest.configuration` carrying `PreparedPowerFlow`/`PowerFlowResult`, UI access to Core result classes, and persisted runtime artifacts.

- [ ] **Step 3: Update guidance**

Document these exact distinctions: Study Case = reusable Application/project engineering intent; Study Request = one execution; Prepared Study = derived execution snapshot; Study Result = one execution output; Read Model = Application presentation/query representation; Controller = UI/Application coordinator; Application = orchestration boundary; Core = authoritative engineering truth.

- [ ] **Step 4: Update findings only from evidence**

For each GF-DYN-WF item touched, record finding ID, before status, evidence, root cause, architectural decision, affected files, tests, verification, after status, and residual risk. Keep GF-DYN-WF-003/004/007/009/017 closed/audited unless regression evidence appears.

- [ ] **Step 5: Synchronize Markdown and CSV**

Verify IDs, statuses, required evidence columns, and historical traceability agree between the two canonical formats if those files are confirmed authoritative.

- [ ] **Step 6: Commit documentation/register changes**

```bash
git add <confirmed-agent-guidance-files> <confirmed-register-files>
git commit -m "docs: close GF-DYN-WF remediation evidence"
```

## Task 11: Full verification and closure decision

**Files:**
- No production source changes unless a verification failure identifies a concrete defect.
- Read: all changed files and audit/register documents.

**Interfaces:**
- Consumes: all implemented workflows and tests.
- Produces: actual verification evidence and final closure matrix; unresolved items remain OPEN/AUDIT BLOCKED/DESIGN AMBIGUITY as appropriate.

- [ ] **Step 1: Run targeted Application tests**

Run:

```bash
pytest tests/application/test_study_case.py tests/application/test_study_results.py tests/application/test_study_workflow.py -q
```

Expected: all targeted Application study tests pass. Record exact count and output.

- [ ] **Step 2: Run persistence/UI study tests**

Run:

```bash
pytest tests/projects/test_study_case_persistence.py tests/ui/test_study_cases_panel.py tests/ui/test_study_projection.py -q
```

Expected: all targeted persistence/UI tests pass. Record exact output.

- [ ] **Step 3: Run the complete repository test suite**

Run:

```bash
pytest -q
```

Expected: repository-wide result is recorded exactly. If failures are unrelated, classify them with evidence rather than claiming the workflow passed globally.

- [ ] **Step 4: Run import/startup verification**

Run the repository's documented startup command and import checks. At minimum verify `python main.py` or the current documented application startup path reaches the Application composition root without the previously audited dynamics import defect.

- [ ] **Step 5: Run persistence round-trip verification**

Create/save/load a project containing all three Study Case types and verify case identity/type/configuration survive reload while runtime artifacts do not appear in serialized JSON.

- [ ] **Step 6: Verify all three workflow traces**

Power Flow: Study Case → typed configuration → request → Application → preparation → Core analysis → adapter → read model → event → projection.

Short Circuit: same complete trace.

Transient Stability: Study Case → typed transient configuration → explicit derived PF runtime dependency → dynamic associations → preparation → solver → adapter → read model → event → projection.

- [ ] **Step 7: Verify failure/cancellation paths**

Exercise invalid case, invalid configuration, missing transient dependency, preparation failure, Core failure, cancellation, result conversion failure, and projection failure. Record actual outputs.

- [ ] **Step 8: Run architecture-boundary search**

Search the final branch for prohibited patterns. Zero matches are required for UI-to-Core execution paths and persisted runtime artifacts; legitimate Core imports in Application composition must remain documented rather than deleted.

- [ ] **Step 9: Update final register evidence**

Only findings with actual evidence become CLOSED. Any unverified runtime/GUI/persistence behavior remains `VERIFICATION DEFERRED` or `AUDIT BLOCKED` rather than being declared closed.

- [ ] **Step 10: Produce final closure report**

The final report must contain:

```text
A. Workflow Closure Matrix
Finding | Workflow | Before | Action | Verification | Final Status

B. Architecture Delta

C. Remaining Open Findings

D. Register Update Summary

E. Agent Training Update

F. Verification Evidence
```

- [ ] **Step 11: Commit final evidence**

```bash
git add audit docs tests core ui
 git commit -m "audit: verify GF-DYN-WF workflow closure"
```

## Spec Coverage Self-Review

- GF-DYN-WF-002: addressed by Task 11 import/startup verification without deleting valid dynamics infrastructure.
- GF-DYN-WF-003: explicitly protected from reopening unless regression occurs.
- GF-DYN-WF-004: explicitly protected from reopening unless regression occurs.
- GF-DYN-WF-005: addressed by Tasks 4, 5, and 9.
- GF-DYN-WF-006: addressed by Tasks 4 and 5.
- GF-DYN-WF-007: preserved as audited and regression-tested in Task 9.
- GF-DYN-WF-008: addressed by Tasks 3–5.
- GF-DYN-WF-009: preserved and verified in Task 6.
- GF-DYN-WF-010: addressed by Tasks 6 and 8.
- GF-DYN-WF-011: addressed by Task 8.
- GF-DYN-WF-012: addressed by Task 8.
- GF-DYN-WF-013: addressed by Task 2.
- GF-DYN-WF-014: addressed by Task 7.
- GF-DYN-WF-015: addressed by Task 7 after owner audit.
- GF-DYN-WF-016: addressed by Task 3 and Task 6.
- GF-DYN-WF-017: preserved as audited and explicitly excluded from persistence in Task 7.
- GF-DYN-WF-018: addressed by Tasks 2, 6, and 7.

## Type/Boundary Consistency

The plan uses one canonical naming set throughout: `StudyCase`, `StudyCaseCatalogue`, `StudyRequest`, `runtime_context`, `StudyResult`/Application execution result, `PowerFlowReadModel`, `ShortCircuitReadModel`, `TransientStabilityReadModel`, `StudyController`, `execute_study_case(case_id)`, and `study_result(study_id)`. Any implementation divergence must be justified by an existing repository contract and reflected in the plan before proceeding.
