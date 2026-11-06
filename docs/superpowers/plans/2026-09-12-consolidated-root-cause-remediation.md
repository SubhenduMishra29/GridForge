# GridForge V2 Consolidated Root-Cause Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile the current GridForge V2 HEAD with the frozen Application/UI/Core architecture across workspace lifecycle, semantic events, study orchestration, Short Circuit, Transient Stability, Dynamics initialization, and dynamic-model persistence.

**Architecture:** Preserve one Application boundary between UI and Core, one canonical WorkspaceManager/WorkspaceController/WorkspaceRealizer runtime, and one Application-owned study orchestration boundary. UI remains presentation/interaction only; Core remains authoritative engineering truth and numerical analysis; solver packages remain implementation-level.

**Tech Stack:** Python, PySide6/Qt UI, existing GridForge Core/Application architecture, existing project persistence/serialization, existing Power Flow and Dynamics numerical implementations.

**Spec:** Approved user remediation prompt in the current conversation, together with the current repository HEAD at `fcbf990a6d8b914337b0dbb75b71ab1a94509edb`.

## Global Constraints

- Current repository HEAD is the implementation authority.
- Do not introduce parallel architectures, obsolete compatibility paths, UI-to-Core shortcuts, duplicate domain models, or speculative abstractions.
- Core MUST NOT depend on Qt/PySide6/QGraphics/UI.
- UI/controllers/tools/canvas/plugins MUST NOT directly mutate Core.
- UI MUST NOT call Analysis or Solver `solve()` APIs directly.
- Application is the sole UI↔Core orchestration boundary.
- Preserve the existing Power Flow configuration/preparation/result architecture.
- Do not redesign numerical solvers unnecessarily.
- Every newly created or substantially modified GridForge source file retains `Author: Subhendu Mishra`.
- Do not add the full test campaign in this pass.
- Do not suppress architectural errors with optional imports, `try/except ImportError`, silent fallbacks, or dynamic attribute probing.
- If current source exposes an architectural ambiguity that cannot be resolved from the frozen architecture and repository evidence, stop that boundary and report it.

---

### Task 1: Reconcile workspace host contract

**Files:**
- Modify: `ui/main_window.py`
- Modify: current canonical WorkspaceRealizer/host adapter file discovered from HEAD
- Modify: related workspace contract/protocol file if one already exists

**Interfaces:**
- Consumes: existing `WorkspaceRealizer` realization requirements and MainWindow Qt host surface.
- Produces: one mechanical MainWindow host contract implementing the capabilities required by WorkspaceRealizer without moving workspace policy into MainWindow.

- [ ] Inspect the exact current WorkspaceRealizer host calls and MainWindow methods.
- [ ] Define the smallest mechanical host interface needed for floating, tabifying, central-surface installation, and teardown.
- [ ] Implement missing MainWindow host operations without workspace-policy decisions.
- [ ] Keep WorkspaceManager/Controller/Realizer responsible for workspace policy and realization sequencing.
- [ ] Verify imports of the workspace stack without running the full test campaign.
- [ ] Commit the isolated workspace-host correction.

### Task 2: Reconcile workspace teardown ownership

**Files:**
- Modify: canonical `WorkspaceController` implementation
- Modify: canonical `WorkspaceRealizer` implementation
- Modify: MainWindow host teardown methods only if required by Task 1

**Interfaces:**
- Consumes: Task 1 mechanical host contract.
- Produces: deterministic `WorkspaceController.close()` → realizer resource teardown → Qt host teardown ordering.

- [ ] Inspect current close/teardown calls and identify which object owns each resource.
- [ ] Implement realizer teardown for resources it actually owns.
- [ ] Keep lifecycle state ownership in WorkspaceController.
- [ ] Keep QWidget/QDockWidget resource ownership in MainWindow.
- [ ] Remove any empty or merely compatibility `close()` implementation.
- [ ] Verify repeated lifecycle teardown does not require a legacy workspace object.
- [ ] Commit the lifecycle ownership correction.

### Task 3: Canonical project-to-engineering-workspace activation

**Files:**
- Modify: `ui/workspace/project_workspace_adapter.py`
- Modify: `ui/workspace/project_workspace.py` / canonical project workspace lifecycle implementation
- Modify: canonical WorkspaceManager/WorkspaceController implementation
- Modify: Application project lifecycle only where its existing UI adapter boundary requires wiring

**Interfaces:**
- Consumes: Application project activation and existing ProjectWorkspaceAdapter.
- Produces: explicit canonical default engineering workspace activation without requiring callers to supply a workspace ID for normal project open/new.

- [ ] Identify the current default/explicit workspace selection behavior.
- [ ] Define the canonical engineering workspace identifier/configuration in the existing workspace architecture.
- [ ] Make `new_project()` and `open_project()` activate that default through ProjectWorkspaceAdapter.
- [ ] Keep Application free of Qt and Workspace classes.
- [ ] Ensure adapter remains thin and contains no independent workspace ownership.
- [ ] Commit the canonical activation correction.

### Task 4: Compose UILifecycle with project/workspace lifecycle

**Files:**
- Modify: `ui/lifecycle/*`
- Modify: `ui/bootstrap/*`
- Modify: `main.py` or current UI entry point
- Modify: project/workspace lifecycle wiring files identified during implementation

**Interfaces:**
- Consumes: canonical Application project lifecycle and Tasks 1–3 workspace stack.
- Produces: startup → shell → engineering workspace → project activation → close → workspace teardown → UI close composition.

- [ ] Trace current startup and shutdown entry points.
- [ ] Wire UILifecycle to the actual WorkspaceController/project lifecycle rather than creating another lifecycle.
- [ ] Establish shell-ready before workspace realization.
- [ ] Establish project activation through ProjectWorkspaceAdapter.
- [ ] Establish project close before workspace teardown.
- [ ] Establish UI close after workspace teardown.
- [ ] Commit the lifecycle composition.

### Task 5: Remove legacy Workspace runtime architecture

**Files:**
- Delete: `ui/workspace/workspace.py` after all required responsibilities are migrated and no runtime import remains
- Modify: `main.py`
- Modify: any remaining runtime imports/construction sites found by repository search
- Modify: `ui/workspace/__init__.py` only if it exports the obsolete runtime type

**Interfaces:**
- Consumes: canonical workspace lifecycle from Tasks 1–4.
- Produces: one runtime workspace ownership model.

- [ ] Search the repository for imports and constructions of `ui.workspace.workspace.Workspace`.
- [ ] Migrate only required document/view responsibilities to existing canonical services.
- [ ] Remove runtime imports and constructions of the legacy Workspace.
- [ ] Delete the legacy module once no runtime dependency remains.
- [ ] Verify no parallel workspace construction path remains.
- [ ] Commit the legacy-path removal.

### Task 6: Reconcile panel logical state with rendered widgets

**Files:**
- Modify: current panel state/read-model classes
- Modify: current `PanelsPlugin` implementation
- Modify: current panel widget implementations only where they consume state
- Modify: UI update boundary/presentation coordinator if required

**Interfaces:**
- Consumes: Application read state and semantic UI update events.
- Produces: explicit logical panel state → presentation state → QWidget rendering bridge without Core object ownership in widgets.

- [ ] Identify the current logical panel state objects and QWidget consumers.
- [ ] Define which values are Application read state versus UI presentation state.
- [ ] Add the smallest existing-pattern bridge between those states.
- [ ] Keep PanelsPlugin ownership intact.
- [ ] Remove any widget-level Core object ownership or mutation path exposed by this reconciliation.
- [ ] Commit the panel-state reconciliation.

### Task 7: Install canonical CanvasComposition as central surface

**Files:**
- Modify: `ui/main_window.py`
- Modify: `ui/canvas/*` only where CanvasComposer/CanvasComposition wiring is incomplete
- Modify: `CanvasPlugin` registration/wiring only where required

**Interfaces:**
- Consumes: canonical CanvasComposer → CanvasComposition → CanvasPlugin chain.
- Produces: MainWindow central surface containing canonical engineering Canvas.

- [ ] Trace CanvasComposer, CanvasComposition, and CanvasPlugin construction.
- [ ] Remove generic central QWidget construction used instead of the canonical Canvas surface.
- [ ] Install the canonical CanvasComposition through the existing plugin/composition mechanism.
- [ ] Keep MainWindow unaware of Core/Application engineering state.
- [ ] Commit the canonical central-surface correction.

### Task 8: Complete ToolManager input-dispatch contract

**Files:**
- Modify: `ui/interaction/interaction_manager.py`
- Modify: canonical `ToolManager` implementation
- Modify: `ui/interaction/tools/*` only if existing ToolBase signatures need reconciliation

**Interfaces:**
- Consumes: Qt/Canvas input events forwarded by InteractionManager.
- Produces: `mouse_press`, `mouse_move`, `mouse_release`, `key_press`, and `key_release` dispatch to the active Tool through ToolManager.

- [ ] Enumerate InteractionManager dispatch calls and current ToolManager API.
- [ ] Add the matching ToolManager dispatch methods with the existing ToolBase/Application injection model.
- [ ] Ensure ToolManager resolves only the active Tool and does not access Core.
- [ ] Ensure GraphicsView/Canvas never invokes Tools directly.
- [ ] Ensure tool mutations remain immutable Command → Application.execute().
- [ ] Commit the interaction boundary correction.

### Task 9: Reconcile semantic event classification and publication

**Files:**
- Modify: `core/application/application.py`
- Modify: current event classification/semantic event module
- Modify: command metadata/classification module if present
- Modify: UI event boundary/presentation coordinator consuming these events

**Interfaces:**
- Consumes: successful Application command execution and semantic command identities.
- Produces: explicit ElementCreated/Updated/Removed, TopologyChanged, NetworkChanged, and project/study event semantics.

- [ ] Locate the current command classification tables and event publication sequence.
- [ ] Define NetworkChanged as either true network mutation or explicitly documented aggregate invalidation; implement only the selected meaning.
- [ ] Ensure element events remain authoritative for element mutation.
- [ ] Ensure TopologyChanged is restricted to commands whose semantics alter topology/state.
- [ ] Ensure semantic event publication is not duplicated by a second event bus.
- [ ] Commit the event semantic correction.

### Task 10: Reconcile breaker command event semantics

**Files:**
- Modify: Application command/event classification implementation
- Modify: breaker command definitions/handlers only if semantic metadata is missing

**Interfaces:**
- Consumes: breaker commands `create_breaker`, `update_breaker`, `delete_breaker`, `open_breaker`, `close_breaker`, `trip_breaker`, `put_breaker_in_service`, and `take_breaker_out_of_service`.
- Produces: correct ElementUpdated/Removed/Created and topology/state semantic events without string-only classification.

- [ ] Map each breaker command to its engineering semantic effect.
- [ ] Include breaker topology/state commands in the topology classification where appropriate.
- [ ] Include trip as a breaker mutation producing the correct element mutation event.
- [ ] Exclude unrelated commands from topology publication.
- [ ] Verify event publication remains Application-owned.
- [ ] Commit breaker event reconciliation.

### Task 11: Establish semantic-event to UI presentation contract

**Files:**
- Modify: `ui/events/*`
- Modify: `ui/sld/*` or current `SLDUpdateCoordinator`
- Modify: projection/update boundary files as required

**Interfaces:**
- Consumes: Application semantic events.
- Produces: deterministic UI presentation invalidation/update behavior for element, topology, project, and study events.

- [ ] Trace current SLDUpdateCoordinator subscription and NetworkChanged dependency.
- [ ] Add explicit handlers for authoritative semantic events where required.
- [ ] Keep aggregate invalidation as an optimization only when its meaning is explicit.
- [ ] Ensure no unrelated event is used as an accidental proxy for element mutation.
- [ ] Commit the presentation event contract.

### Task 12: Define canonical Application Study request/result boundary

**Files:**
- Create: canonical immutable study request/result contract under existing `core/application` structure
- Modify: `core/application/application.py`
- Modify: `core/application/command.py` / command registration where study commands belong

**Interfaces:**
- Consumes: immutable UI-originated study requests.
- Produces: Application-owned study identity, request lifecycle, result access, and read-model boundary.

- [ ] Inspect existing StudyStarted/Completed event types and study-related application abstractions.
- [ ] Define one immutable StudyRequest contract and one immutable Application study result/read contract without duplicating Power Flow configuration.
- [ ] Register study commands through the existing CommandManager.
- [ ] Ensure returned results contain no Core/Qt object references.
- [ ] Commit the study boundary contract.

### Task 13: Implement Application Study orchestration

**Files:**
- Create: existing-pattern Application StudyService/StudyOrchestrator module
- Modify: `core/application/application.py`
- Modify: command handlers/registration as required
- Modify: application events for StudyStarted/Completed/Failed/Cancelled

**Interfaces:**
- Consumes: immutable study requests and existing Core Analysis facades.
- Produces: lifecycle-controlled analysis execution and immutable registered results.

- [ ] Implement one Application-owned orchestration service.
- [ ] Start lifecycle before Core analysis execution.
- [ ] Invoke Core Analysis facade rather than solver internals.
- [ ] Register immutable engineering results after successful execution.
- [ ] Publish StudyCompleted only after result registration succeeds.
- [ ] Publish StudyFailed for defined execution failures.
- [ ] Preserve cancellation semantics only where an existing cancellation mechanism is actually supported; do not invent asynchronous infrastructure.
- [ ] Commit the study orchestration.

### Task 14: Wire UI study invocation exclusively through Application

**Files:**
- Modify: study UI/controller modules
- Modify: study panels/results projection modules
- Modify: application study read-model/event boundary where needed

**Interfaces:**
- Consumes: engineer study configuration from UI presentation state.
- Produces: immutable StudyRequest → Application.execute() and StudyStarted/Completed/Failed → result projection.

- [ ] Search UI/controllers for direct `PowerFlowAnalysis`, `ShortCircuitAnalysis`, `TransientStabilitySolver`, or `DAESolver` calls.
- [ ] Replace direct calls with immutable Application study commands.
- [ ] Ensure UI receives immutable result/read data only.
- [ ] Commit the UI study boundary correction.

### Task 15: Reconcile Short Circuit configuration and preparation

**Files:**
- Modify: `core/analysis/short_circuit.py`
- Modify: `core/analysis/short_circuit_preparation.py`
- Create or modify: canonical immutable Short Circuit study configuration file following the existing Power Flow pattern
- Modify: application study adapter only as required

**Interfaces:**
- Consumes: immutable Short Circuit study configuration.
- Produces: detached ShortCircuitInput for numerical analysis and immutable engineering result.

- [ ] Compare Short Circuit with PowerFlowStudyConfiguration/PowerFlowPreparation.
- [ ] Introduce only one Short Circuit configuration contract.
- [ ] Keep live Network/equipment context inside Core preparation, not the public Application-facing request.
- [ ] Ensure solver input is detached and immutable.
- [ ] Preserve existing numerical implementation.
- [ ] Commit Short Circuit boundary reconciliation.

### Task 16: Establish public Transient Stability study facade

**Files:**
- Create/modify: `core/analysis/transient_stability.py`
- Modify: `core/analysis/__init__.py`
- Modify: current dynamic preparation modules as required

**Interfaces:**
- Consumes: immutable transient-stability study configuration plus prepared operating-point/dynamic model inputs.
- Produces: immutable engineering transient-stability result.

- [ ] Inspect current Dynamics solver classes and any existing transient-study implementation.
- [ ] Define the public analysis-level facade under `core.analysis`.
- [ ] Keep dynamic solver classes low-level.
- [ ] Have the facade prepare the simulation and invoke solver-level Dynamics.
- [ ] Ensure returned results contain no live Core objects.
- [ ] Commit the public study facade.

### Task 17: Reconcile Dynamics package exports

**Files:**
- Modify: `core/solver/dynamics/__init__.py`
- Modify: `core/solver/dynamics/transient_stability.py` only if implementation naming must be reconciled

**Interfaces:**
- Consumes: actual implemented solver-level symbols.
- Produces: package exports containing only real current implementations.

- [ ] Enumerate all exports from `core.solver.dynamics.__init__`.
- [ ] Verify each symbol exists in its implementation module.
- [ ] Remove fictitious study-level exports from solver package.
- [ ] Export only actual solver-level public symbols.
- [ ] Commit export reconciliation.

### Task 18: Correct transient-stability result sample invariant

**Files:**
- Modify: current transient-stability result/recording implementation

**Interfaces:**
- Consumes: simulation time/state/output at one simulation instant.
- Produces: equal-length coherent time/state/output samples.

- [ ] Trace initial-recording behavior.
- [ ] Make `record_initial=True` append time and corresponding state/output as one atomic sample.
- [ ] Ensure subsequent samples append all associated arrays together.
- [ ] Validate dimensions before producing final immutable result.
- [ ] Commit result invariant correction.

### Task 19: Establish dynamic machine model association boundary

**Files:**
- Modify: existing dynamic model definition module if present
- Create: association/value-object module in the existing Core/domain location indicated by current architecture
- Modify: `SynchronousMachine` only if the current frozen model requires a minimal identity/reference field; do not add generic dynamic parameters without evidence
- Modify: analysis preparation to consume the association

**Interfaces:**
- Consumes: authoritative `SynchronousMachine` identity and persisted dynamic model association.
- Produces: resolved dynamic model type and immutable `ClassicalMachineParameters` or equivalent solver input.

- [ ] Inspect current SynchronousMachine model and dynamic parameter classes.
- [ ] Determine the existing architectural owner for persisted study-side/dynamic model associations.
- [ ] Introduce one association contract rather than embedding solver parameters into generic equipment unless current architecture explicitly requires it.
- [ ] Ensure dynamic model identity is explicit and not inferred from UI state.
- [ ] Commit the association boundary.

### Task 20: Persist and reconstruct dynamic model associations

**Files:**
- Modify: current project serialization/deserialization modules
- Modify: current project schema/DTO modules where dynamic associations belong
- Modify: dynamic association module from Task 19

**Interfaces:**
- Consumes: dynamic model association attached to a SynchronousMachine identity.
- Produces: stable serialized representation and reconstructed association after reopen.

- [ ] Trace the current R3 project persistence pipeline.
- [ ] Add dynamic model association to the existing authoritative project serialization structure.
- [ ] Restore the association before study preparation after project load.
- [ ] Do not persist Qt/Canvas objects.
- [ ] Verify source-level save/load/reconstruction path.
- [ ] Commit dynamic-model persistence.

### Task 21: Implement Power Flow → Dynamic initial-state preparation

**Files:**
- Create/modify: `core/analysis` dynamic initial-state preparation module
- Modify: Power Flow result conversion only if the existing immutable solved-operating-point result lacks a required value and can expose it without redesign
- Modify: transient-stability facade to consume the prepared initial state

**Interfaces:**
- Consumes: immutable solved Power Flow operating point + SynchronousMachine identity + dynamic model parameters.
- Produces: immutable dynamic initial state containing terminal voltage, electrical/mechanical power, rotor angle, speed deviation, internal EMF, and solver state vector as required by the existing model.

- [ ] Identify the exact immutable Power Flow result values required by the existing Dynamics machine model.
- [ ] Build the conversion in Core Analysis, not UI or solver code.
- [ ] Calculate/prepare rotor angle and other initial-state values through the existing engineering model.
- [ ] Ensure no live Network/equipment objects cross into the numerical solver.
- [ ] Commit the initial-state preparation boundary.

### Task 22: Integrate dynamic initial state through the public study facade

**Files:**
- Modify: `core/analysis/transient_stability.py`
- Modify: dynamic preparation module
- Modify: Application StudyService integration from Tasks 12–13

**Interfaces:**
- Consumes: immutable study request, persisted dynamic model association, solved Power Flow result.
- Produces: immutable transient-stability result through Core Analysis → solver → Application result boundary.

- [ ] Make the public transient study facade obtain/receive the solved operating point through the established Core/Application boundary.
- [ ] Resolve the persisted dynamic model association.
- [ ] Prepare immutable dynamic initial state.
- [ ] Invoke the existing Dynamics solver.
- [ ] Convert solver output to immutable engineering result.
- [ ] Commit public study integration.

### Task 23: Source-level forbidden-boundary verification

**Files:**
- Modify only if verification reveals an implementation defect.

**Interfaces:**
- Consumes: completed remediation source.
- Produces: source verification report.

- [ ] Search for Core imports of Qt/PySide6/QGraphics/UI.
- [ ] Search for UI/controller/tool/canvas direct Core mutation.
- [ ] Search for UI/controller direct solver/analysis calls.
- [ ] Search for legacy Workspace construction/imports.
- [ ] Search for multiple CommandManager/event-bus implementations.
- [ ] Search for direct solver exposure through UI.
- [ ] Verify every Dynamics export exists.
- [ ] Verify study lifecycle event producers and consumers.
- [ ] Verify dynamic-model persistence path source-level.
- [ ] Commit only corrective changes discovered by verification.

### Task 24: Import verification and remediation report

**Files:**
- Create: `docs/superpowers/verification/2026-09-12-consolidated-root-cause-remediation.md`
- Modify: repository source only if verification finds a defect

**Interfaces:**
- Consumes: completed implementation and source-level verification evidence.
- Produces: explicit verification report separating source verified, import verified, static boundary verified, and tests not executed.

- [ ] Perform targeted import verification for modified Core/Application/UI modules.
- [ ] Do not execute the full test campaign.
- [ ] Record any unresolved architectural ambiguity explicitly.
- [ ] List all changed/created/deleted files.
- [ ] Map GF-AUD-WS-001 through GF-AUD-025 to root cause, corrected architecture, files, and status.
- [ ] Document final Core/Application/UI/SLD/Canvas/Workspace/Studies/Dynamics/Persistence relationships.
- [ ] Explicitly state that the full test campaign was not executed.
- [ ] Commit the verification report.

## Acceptance Criteria

- Canvas input reaches the active Tool only through InteractionManager → ToolManager.
- Tool mutations become immutable Commands executed by Application.
- Project lifecycle activates the canonical engineering Workspace without caller-supplied workspace IDs for normal new/open.
- No runtime construction/import of legacy `ui.workspace.workspace.Workspace` remains.
- MainWindow remains a mechanical Qt host and installs canonical CanvasComposition centrally.
- Semantic element and topology events have explicit Application-owned meanings.
- Breaker create/update/delete/open/close/trip/in-service/out-of-service commands are classified according to engineering semantics.
- NetworkChanged is not an ambiguous universal command-success event.
- UI presentation consumes semantic Application events through the canonical update boundary.
- Studies execute through Application orchestration and Core Analysis facades.
- UI does not instantiate or call numerical solvers directly.
- Short Circuit public configuration is immutable/detached and follows the existing Power Flow separation.
- Transient Stability public facade is under `core.analysis` and solver exports contain only actual solver symbols.
- Transient result samples preserve time/state/output dimensional consistency.
- Dynamic initial state is prepared from immutable solved Power Flow operating point plus persisted dynamic model association.
- Dynamic model association survives save → close → reopen → reconstruct → study preparation.
- No Core/UI/solver boundary violations remain in the verified source.
- Full test campaign is explicitly deferred to the later verification phase.
