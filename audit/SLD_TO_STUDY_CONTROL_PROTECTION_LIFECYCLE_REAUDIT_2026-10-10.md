# GridForge V2 — Complete SLD-to-Study/Control/Protection Lifecycle Re-Audit

**Date:** 2026-10-10  
**Implementation repository:** `madhuri196mishra-cpu/GridForge`  
**Branch:** `main`  
**Inspected baseline:** `5304c53541ddb889d533263762c40546899c17c0`  
**Audit mode:** current-source static inspection and cross-boundary tracing  
**Production changes:** none  
**Runtime / pytest / CI / GUI:** not run  
**Disposition:** AUDIT COMPLETE AT STATIC SOURCE LEVEL; LIFECYCLE RUNTIME CLOSURE NOT ESTABLISHED

## 1. Authority and architecture

This report audits the implementation repository above. Historical repository references elsewhere in the audit history are provenance only. The frozen authority contract is retained:

`UI / Tool → immutable Command → Application.execute() → CommandManager / transaction → Core → semantic event → read model / projection → UI`

Core owns electrical/domain truth. Application owns mutation coordination, transactions, history, lifecycle, semantic event publication, read models and integration orchestration. SLDDocument owns authored presentation structure, not electrical truth. No second renderer, topology authority, command/history owner, selection manager, or execution route is authorized.

## 2. Lifecycle coverage

| Stage | Static evidence reviewed | Result |
|---|---|---|
| Engineer drawing and placement | `ui/sld/sld_document.py`, `ui/canvas/sld_canvas_projection.py`, `ui/canvas/sld_canvas_render_system.py`, draft command handlers | Authoring/document/projection/render boundaries exist. Runtime place → edit → connect sequence not exercised. |
| Terminal/wire identity and commit | `core/application/commands/draft_commands.py`, `core/application/draft/handlers.py`, Application SLD service, topology snapshot | Draft-to-Core commit and canonical topology contracts exist. Atomic failure, undo/redo and identity reconciliation not runtime-proven. |
| Persistence/reopen | `core/persistence/project_persistence.py`, `core/persistence/migration.py`, project lifecycle | Canonical package/migration/lifecycle mechanisms exist. Save-close-reopen semantic equivalence and activation rollback not runtime-proven. |
| Study execution | `core/application/study.py`, `core/application/study_preparation.py`, Power Flow and Short-Circuit preparation, topology snapshot | Detached preparation and topology provenance contracts exist. Numerical correctness, stale-result rejection and lifecycle cancellation not executed. |
| Control | `core/application/control_signal_mapping.py`, `control_cycle.py`, `control_execution.py`, `control_feedback.py` | Application-owned mapping/evaluate/dispatch/result contracts exist. Full measurement-to-action-to-observed-feedback chain not proven. |
| Protection | `core/protection/preparation.py`, `runtime.py`, `protection_measurement_binding.py`, `core/application/protection_execution.py` | Relay composition and explicit action resolver boundaries exist. End-to-end CT/PT/CVT-to-channel-to-relay-to-trip wiring remains a previously recorded open integration question (GF-PROT-042); runtime behavior not proven. |
| Cross-domain invalidation | Study revision and topology provenance, project lifecycle, signal and protection mappings | No complete runtime evidence that all topology edits invalidate or reject affected studies, Control bindings and Protection inputs. Keep as verification gap, not a proven production defect. |

## 3. New current-source findings

These findings are source-backed contract gaps observed on the inspected baseline. They are recorded as open/re-audit-required, not as corrected and not as runtime failures.

### GF-MASTER-0116 — Control signal snapshot only shallow-freezes external inputs
- **Severity:** HIGH
- **Source:** `core/application/control_signal_mapping.py`, `ControlSignalResolution.__post_init__`.
- **Evidence:** `external_inputs` wraps each component's values in `MappingProxyType(dict(values))`; nested dict/list/set values are not recursively detached/frozen. `interlock_inputs` uses the existing recursive `_freeze_snapshot`, demonstrating the intended pattern already exists.
- **Impact:** a nested value can be mutated after resolution, changing an allegedly immutable Control input snapshot and potentially changing the values consumed by evaluation.
- **Required correction:** use the established recursive detach/freeze helper for external inputs as well; preserve scalar value, quality, timestamp and binding semantics.
- **Verification:** test nested mapping/list/set mutation through both the original input object and the returned resolution.

### GF-MASTER-0117 — Control feedback metadata remains mutable
- **Severity:** MEDIUM
- **Source:** `core/application/control_feedback.py`, `ControlFeedback.__post_init__`.
- **Evidence:** the frozen dataclass stores `dict(self.metadata or {})`; the returned `metadata` dictionary remains mutable and nested values are shared.
- **Impact:** feedback records can be changed after publication, undermining stable audit/acknowledgement evidence.
- **Required correction:** define and apply a detached immutable metadata snapshot policy consistent with other Application result contracts.
- **Verification:** mutate original nested metadata and attempt mutation through returned feedback metadata.

### GF-MASTER-0118 — Prepared Protection settings are only shallowly frozen
- **Severity:** HIGH
- **Source:** `core/protection/preparation.py`, `PreparedProtectionInput.__post_init__` and `ProtectionPreparation.prepare`.
- **Evidence:** `settings` is wrapped with `MappingProxyType(dict(self.settings))`; preparation passes the relay settings mapping into the DTO without recursive detachment. Nested settings can therefore remain mutable after the protection input is prepared.
- **Impact:** a prepared protection evaluation may observe changed settings rather than the settings captured for that evaluation.
- **Required correction:** recursively detach/freeze supported configuration containers without converting typed domain contracts or changing setting meaning.
- **Verification:** nested settings mutation after preparation must not change the prepared input; verify supported relay functions still consume it correctly.

### GF-MASTER-0119 — StudyRequest configuration does not honor its immutable snapshot contract
- **Severity:** MEDIUM
- **Source:** `core/application/study.py`, `StudyRequest.__post_init__`.
- **Evidence:** `StudyRequest` stores `MappingProxyType(dict(self.configuration))`, while the same module defines `_freeze_study_value` for recursive container freezing and uses it for `StudyCaseDefinition`.
- **Impact:** nested mutable configuration supplied to a StudyRequest can change after request construction and before downstream conversion/dispatch.
- **Required correction:** apply a consistent request snapshot policy, preserving typed Power Flow, Short-Circuit and Transient Stability configuration objects.
- **Verification:** mutate nested request input after construction and confirm downstream StudyCaseDefinition/request handling retains the captured values.

### GF-MASTER-0120 — SLD canvas snapshot properties are shallowly immutable
- **Severity:** MEDIUM
- **Source:** `ui/canvas/sld_canvas_projection.py`, `SLDCanvasProjection._project_node` and `_project_connection`.
- **Evidence:** both projection paths use `MappingProxyType(dict(...))`, protecting only the outer properties mapping. Nested mutable values remain shared with the model.
- **Impact:** a supposedly immutable renderer-neutral snapshot can change after projection, bypassing the document → projection → renderer boundary and making render results depend on later model mutation.
- **Required correction:** detach/freeze nested property containers at projection time, with serialization-compatible handling for supported values.
- **Verification:** mutate nested source properties after projection and verify snapshot values remain stable; verify the render system still consumes supported properties.

### GF-MASTER-0121 — ProtectionExecutionResult does not normalize or validate its public result contract
- **Severity:** MEDIUM
- **Source:** `core/application/protection_execution.py`, `ProtectionExecutionResult`.
- **Evidence:** the frozen dataclass declares tuple fields but has no `__post_init__`; callers can construct it with lists or invalid element types. The service's own return path currently passes tuples, but the public result type itself does not enforce the documented immutable result contract.
- **Impact:** result mutability and invalid result contents can enter through alternate constructors/callers, weakening downstream audit and feedback assumptions.
- **Required correction:** normalize sequence fields and validate their element types/identity relationships to the same extent required by the established Protection/Control result contract. Do not conflate command dispatch with physical acknowledgement.
- **Verification:** constructor tests for mutable input sequences, invalid members, and consistency among actionable decisions, translated intents, commands and Application results.

## 4. Existing finding explicitly retained

**GF-PROT-042 — OPEN — INTEGRATION GAP** remains an existing finding, not a newly invented duplicate. The historical register identifies the unresolved need to statically establish the authoritative CT/PT/CVT → MeasurementProvisioning → channel registration/collection → protection mapping → `ProtectionRuntime.compose()` consumer path. This audit confirms that `ProtectionRuntime.compose(channels)` composes configured relay inputs from supplied channel IDs, but the complete upstream provisioning/registration path and its invalidation lifecycle are not proven by the source paths inspected here. Preserve its historical identity and require a dedicated consumer inventory.

## 5. Cross-domain acceptance checklist

The following is required before declaring the whole lifecycle closed:

1. Place incomplete equipment, edit it, save, close, reopen, then connect it later without premature Core creation or loss of authored presentation.
2. Commit valid and invalid networks; prove rollback, undo/redo, deterministic identity, and topology revision consistency.
3. Save/reopen multiple SLD documents and compare persisted SLD semantics before and after reopen; prove failed project activation restores the prior active context.
4. Run representative Power Flow, Short Circuit, Contingency and Transient Stability studies; reject results whose project, activation generation or topology revision no longer matches.
5. Trace a real engineering measurement through Control mapping, freshness/quality/interlock checks, Application command execution and observed feedback; prove failures are not reported as physical acknowledgement.
6. Trace CT/PT/CVT provisioning through channel registration, ProtectionRuntime composition, relay evaluation, actionable decision, target resolution, Application command, breaker state and feedback.
7. Change/delete an electrical element and prove all dependent study results, signal bindings, relay input mappings and trip targets are refreshed or explicitly rejected.
8. Verify no UI, canvas, renderer, Control or Protection surface mutates Core directly or owns duplicate command, topology, selection or execution authority.

## 6. Final status

- **Static audit:** completed for the paths and contracts listed in this report.
- **New source findings:** GF-MASTER-0116 through GF-MASTER-0121 recorded as open.
- **Existing integration finding:** GF-PROT-042 retained as open.
- **End-to-end lifecycle closure:** not established.
- **Production source modifications:** none.
- **Tests, CI, startup and GUI:** not run; runtime verification remains deferred.

**Author:** Subhendu Mishra
