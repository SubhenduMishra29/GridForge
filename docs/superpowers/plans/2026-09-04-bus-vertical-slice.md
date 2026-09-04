# Phase 7.1 Bus Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Bus placement a truthful, testable `UI → UI-Core → Application → Core` vertical slice while correcting only the stale seams encountered on that path.

**Architecture:** The UI-facing command facade is backed directly by the canonical headless `Application`; Controller remains UI coordination state and no longer exposes Core command infrastructure. `BusTool` submits the existing authoritative `CreateBusCommand` through the injected facade. Application handlers/services remain the mutation boundary into `Network`, while the existing Application event → UI update → SLD read/projection path is verified end-to-end.

**Tech Stack:** Python, existing Qt abstraction under `ui.core.qt`, existing Application command/transaction infrastructure, pytest, GitHub repository APIs.

**Spec:** `docs/superpowers/specs/2026-09-04-bus-vertical-slice-design.md`

## Global Constraints

- Mutation remains `UI → UI Core → Application Command → Application.execute() → CommandManager → Handler → Service → Core Network`.
- Read/event flow remains `Core → Application event/result → UI-Core adapter → UI/update bus → SLD/read-model synchronization → canvas projection`.
- SLD remains presentation/document state and never owns electrical truth.
- Do not introduce a second command-history implementation.
- Do not restore `Core.command_manager` as a UI integration boundary.
- Do not activate the other equipment tools.
- Do not invent a domain position field for Bus merely to retain canvas coordinates.
- Do not redesign Network topology or perform unrelated cleanup.
- Every implementation step follows TDD: failing test, minimal change, focused verification, then commit.

## File Map

### Modify

- `ui/core/command_manager.py` — replace the obsolete Controller/Core command delegation with a UI-facing facade over the injected canonical `Application`, preserving the public UI command/history API where it is still required by the Bus slice.
- `ui/core/controller.py` — remove the Bus-path dependency on `Core.command_manager`; retain UI coordination state and only the minimal command-state compatibility surface needed by current callers.
- `ui/canvas/canvas_composition.py` — accept the canonical Application-backed UI command facade and inject the same instance into registered tools; correct the selected `ui.core.tool_manager.ToolManager` registration seam without reviving the parallel manager.
- `main.py` — construct the UI command facade once from the canonical Application and pass that same instance through Controller/Canvas composition; eliminate the dynamic `controller.gridforge_application` mutation used as a hidden dependency.
- `ui/tools/bus_tool.py` — construct `CreateBusCommand` using the authoritative payload fields; keep snapped position transient/presentation-side and submit through `ToolBase.execute_command()`.
- `ui/tools/default_tool_registry.py` — only if required by the selected runtime ToolManager registration contract; ensure Bus receives the already-composed command facade rather than `None`.
- `ui/core/tool_manager.py` — only if required to reconcile `register_tools` with the selected `register_tool` contract; keep one selected ToolManager architecture.

### Tests

- Add focused tests under the repository's existing test layout after locating the established conventions. Tests cover the UI command facade, BusTool command construction/dispatch, Application Bus execution, and composition/event propagation.

## Task 1: Establish the UI Command Facade Contract

**Files:**
- Modify: `ui/core/command_manager.py`
- Modify: `ui/core/controller.py`
- Test: existing/new focused UI command-manager tests in the repository's established test directory

**Interfaces:**
- Consumes: canonical `core.application.application.Application` methods for `execute`, undo/redo, command-state queries, and history operations where exposed.
- Produces: `ui.core.command_manager.CommandManager(application=...)` with `execute(command)` forwarding unchanged to `Application.execute(command)` and no Core dependency.

- [ ] **Step 1: Write the failing test**

```python
def test_ui_command_manager_forwards_to_application_without_core_access():
    application = FakeApplication()
    manager = CommandManager(application=application)
    command = object()

    assert manager.execute(command) == application.result
    assert application.executed == [command]
```

Also assert that constructing the facade does not require `controller.command_manager` or `controller._core`.

- [ ] **Step 2: Run the focused test and verify it fails**

Run the repository's focused pytest target for the new command-manager test.
Expected: FAIL because the current constructor requires `controller` and `execute()` delegates to `Controller`.

- [ ] **Step 3: Implement the minimal Application-backed facade**

Use an explicit constructor dependency:

```python
class CommandManager:
    def __init__(self, application: Any) -> None:
        if application is None:
            raise ValueError("application must not be None.")
        execute = getattr(application, "execute", None)
        if not callable(execute):
            raise TypeError("application must provide execute().")
        self.application = application

    def execute(self, command: Any) -> Any:
        if command is None:
            raise ValueError("command must not be None.")
        return self.application.execute(command)
```

Preserve only history/state methods actually required by existing UI callers, forwarding to explicit Application APIs where those APIs exist. Do not reach through Application into Core.

- [ ] **Step 4: Run the focused test and repository command-boundary tests**

Run the focused pytest target, then the existing Application/UI command tests discovered before implementation.
Expected: PASS, with no imports or references from the UI facade to `core.command_manager`.

- [ ] **Step 5: Commit**

```bash
git add ui/core/command_manager.py ui/core/controller.py tests/
git commit -m "refactor: route UI command dispatch through Application"
```

## Task 2: Correct BusTool Against the Frozen Command Contract

**Files:**
- Modify: `ui/tools/bus_tool.py`
- Test: focused BusTool tests

**Interfaces:**
- Consumes: `ToolBase.execute_command()` and the existing `CreateBusCommand` constructor.
- Produces: mouse release creates exactly one `CreateBusCommand` with `bus_id`, `name`, `nominal_voltage_kv`, `voltage_pu`, `angle_deg`, `frequency_hz`, and `in_service`.

- [ ] **Step 1: Write the failing test**

```python
def test_bus_tool_mouse_release_submits_authoritative_create_bus_command():
    command_manager = RecordingCommandManager()
    snap_system = FixedSnapSystem((10.0, 20.0))
    tool = BusTool(
        controller=object(),
        command_manager=command_manager,
        selection_manager=object(),
        snap_system=snap_system,
    )
    tool.activate()

    assert tool.mouse_release({"position": (10.0, 20.0)}) is True

    command = command_manager.commands[0]
    assert command.command_type == "model.create_bus"
    assert command.payload["name"] == "Bus"
    assert command.payload["nominal_voltage_kv"] == 0.0
    assert command.payload["voltage_pu"] == 1.0
    assert command.payload["angle_deg"] == 0.0
    assert command.payload["frequency_hz"] == 50.0
    assert command.payload["in_service"] is True
    assert "voltage" not in command.payload
    assert "angle" not in command.payload
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run the BusTool test.
Expected: FAIL because the current implementation passes obsolete `voltage` and `angle` keywords to `CreateBusCommand`.

- [ ] **Step 3: Implement the minimal command correction**

Replace the obsolete construction with:

```python
command = CreateBusCommand(
    bus_id=f"bus-{uuid4()}",
    name="Bus",
    nominal_voltage_kv=0.0,
    voltage_pu=1.0,
    angle_deg=0.0,
    frequency_hz=50.0,
    in_service=True,
)
self.execute_command(command)
```

Do not add position fields to the command. Keep `_position` only as transient tool state.

- [ ] **Step 4: Run focused BusTool tests**

Expected: PASS, including the existing snap/cancel behavior.

- [ ] **Step 5: Commit**

```bash
git add ui/tools/bus_tool.py tests/
git commit -m "fix: align BusTool with CreateBusCommand"
```

## Task 3: Wire One Application-Backed Command Facade Through Composition

**Files:**
- Modify: `main.py`
- Modify: `ui/canvas/canvas_composition.py`
- Modify: `ui/tools/default_tool_registry.py` only if necessary
- Modify: `ui/core/tool_manager.py` only if necessary
- Test: composition-focused tests

**Interfaces:**
- Consumes: `Application`, `ui.core.command_manager.CommandManager`, `CanvasComposer`, selected `ui.core.tool_manager.ToolManager`.
- Produces: one command facade instance shared by CanvasComposition and BusTool.

- [ ] **Step 1: Write the failing composition test**

```python
def test_canvas_composition_injects_same_command_manager_into_bus_tool():
    application = FakeApplication()
    command_manager = CommandManager(application=application)
    controller = Controller()
    tool_manager = ToolManager(controller=controller)

    composition = CanvasComposer().compose(
        controller=controller,
        tool_manager=tool_manager,
        command_manager=command_manager,
    )

    bus_tool = tool_manager.get_tool("bus")
    assert bus_tool.command_manager is command_manager
```

Adapt the lookup only to the selected ToolManager's existing public API; do not introduce a second registry.

- [ ] **Step 2: Run the focused composition test and verify it fails**

Expected: FAIL because `CanvasComposer` currently has no command-manager parameter and registers factories with `command_manager=None`.

- [ ] **Step 3: Implement the minimal injection change**

Extend the composition signature with the existing UI command facade:

```python
def compose(
    self,
    *,
    controller: Controller,
    tool_manager: ToolManager,
    command_manager: Any,
    parent: Optional[QWidget] = None,
) -> CanvasComposition:
```

Pass that exact instance into `create_default_tool_factories(...)`. Correct `register_tools`/`register_tool` only to the extent required by the selected runtime `ui.core.tool_manager.ToolManager` contract.

- [ ] **Step 4: Update main composition**

Create the facade immediately after `gridforge_application = create_application(network)`:

```python
command_manager = UICommandManager(application=gridforge_application)
```

Pass it into `CanvasComposer.compose(...)` and the ToolManager construction path. Do not attach `gridforge_application` dynamically to Controller merely for Bus dispatch.

- [ ] **Step 5: Run composition and BusTool tests**

Expected: PASS. Verify the Bus tool has the same Application-backed facade instance that composition created.

- [ ] **Step 6: Commit**

```bash
git add main.py ui/canvas/canvas_composition.py ui/tools/default_tool_registry.py ui/core/tool_manager.py tests/
git commit -m "refactor: inject Application command boundary into Canvas tools"
```

## Task 4: Verify the Application Bus Mutation Path With Transaction Semantics

**Files:**
- Modify: none unless a test exposes a genuine Bus-path defect
- Test: focused Application Bus integration tests

**Interfaces:**
- Consumes: `create_application(network)`, `CreateBusCommand`, Application `execute()`, existing Bus handler/service, `Network`.
- Produces: verified successful Bus creation, result, Network membership, undo registration, and `NetworkChanged` publication.

- [ ] **Step 1: Write the failing integration assertions**

```python
def test_application_create_bus_mutates_network_and_publishes_event():
    network = Network()
    application = create_application(network)
    events = []
    application.event_bus.subscribe(events.append)

    result = application.execute(
        CreateBusCommand(
            bus_id="bus-test",
            name="Bus",
            nominal_voltage_kv=132.0,
            voltage_pu=1.0,
            angle_deg=0.0,
            frequency_hz=50.0,
            in_service=True,
        )
    )

    assert result.success is True
    assert network.get_bus("bus-test") is not None
    assert events
```

Add a rollback/duplicate-ID assertion using the existing transaction/validation behavior rather than implementing new semantics.

- [ ] **Step 2: Run the focused integration test**

Expected: PASS if the previously audited Application Bus path is intact. If it fails, stop and correct only the defect required by this slice.

- [ ] **Step 3: Verify no UI/Core boundary regression**

Search changed UI files for `core.command_manager`, `Core.command_manager`, `Network`, and direct Core model imports. Expected: none in the Bus dispatch path.

- [ ] **Step 4: Commit only if a test-driven correction was required**

Use a specific commit message describing the verified Bus-path defect; otherwise do not create a no-op commit.

## Task 5: Verify Application Event → UI Update → SLD Read/Canvas Projection

**Files:**
- Modify: existing UI event adapter file only if the Bus test proves a missing bridge
- Test: focused event/composition integration tests

**Interfaces:**
- Consumes: `Application.event_bus`, `SLDUpdateCoordinator`, `UIUpdateBoundary`, `SLDReadSynchronizer`, existing Canvas synchronization callback.
- Produces: a successful Bus mutation causes the existing SLD/read-model path to refresh without passing Core objects into projection.

- [ ] **Step 1: Write the failing end-to-end event assertion**

```python
def test_network_changed_reaches_sld_refresh_path():
    refresh_calls = []
    coordinator = SLDUpdateCoordinator(
        application=application,
        document=sld_document,
        synchronizer=synchronizer,
        canvas_refresh=lambda: refresh_calls.append(True),
    )
    boundary = UIUpdateBoundary(
        event_bus=application.event_bus,
        refresh=coordinator.refresh,
    )
    boundary.subscribe()

    application.execute(create_bus_command)

    assert refresh_calls == [True]
```

Also assert the synchronizer receives `NetworkReadModel`/`ElementReadModel` rather than Core `Bus` objects.

- [ ] **Step 2: Run the focused event test and verify the current behavior**

Expected: either PASS, proving no event correction is needed, or FAIL at the missing adapter seam.

- [ ] **Step 3: Implement only the minimal adapter correction if required**

Preserve the existing chain:

```text
Application.event_bus
    → UIUpdateBoundary
    → SLDUpdateCoordinator.refresh
    → Application.read_network()
    → SLDReadSynchronizer
    → CanvasPlugin synchronization
```

Do not introduce a new event bus.

- [ ] **Step 4: Run focused event/SLD tests**

Expected: PASS, with no Core object retained by SLD projection.

- [ ] **Step 5: Commit**

```bash
git add ui/events/ tests/
git commit -m "test: verify Application event reaches SLD projection"
```

## Task 6: Full Bus Vertical-Slice Verification and Architectural Freeze

**Files:**
- Modify: only files proven necessary by prior tasks
- Test: complete relevant pytest suite and static repository checks

**Interfaces:**
- Consumes: corrected Bus slice from Tasks 1–5.
- Produces: verified frozen Bus integration seam.

- [ ] **Step 1: Run all focused Bus/Application/UI tests**

Run the exact focused targets created or discovered during Tasks 1–5.
Expected: PASS.

- [ ] **Step 2: Run the repository's full test suite**

Run the repository's documented test command, normally:

```bash
pytest -q
```

Expected: all available tests pass, or any pre-existing unrelated failure is explicitly recorded rather than hidden.

- [ ] **Step 3: Perform architecture-boundary searches**

Search the changed Bus path for forbidden dependencies:

```text
ui → core.command_manager
ui → Network
ui/sld → Core model objects
ui/sld → Network
SLD → Core
```

Expected: zero new violations introduced by Phase 7.1.

- [ ] **Step 4: Verify runtime composition identity**

Confirm there is exactly one canonical `Application` instance for the application graph and one UI command facade instance used by the Bus tool. Confirm the facade calls `Application.execute()` rather than reaching through Controller.

- [ ] **Step 5: Run final verification before claiming completion**

Use the verification-before-completion workflow. Record the actual commands and outputs. Do not claim the slice is complete without evidence.

- [ ] **Step 6: Freeze the corrected seam**

Document the final Bus path and any explicitly deferred findings in the Phase 7 audit record. The frozen path must be:

```text
BusTool
  → UI CommandManager
  → Application.execute(CreateBusCommand)
  → Application CommandManager
  → CREATE_BUS handler
  → Bus ModelService
  → Network.add_bus()
  → Application NetworkChanged
  → UIUpdateBoundary
  → SLDUpdateCoordinator
  → Application ReadModel
  → SLD projection/canvas
```

- [ ] **Step 7: Commit final verification/documentation**

```bash
git add docs/superpowers/
git commit -m "docs: freeze Phase 7.1 Bus integration seam"
```

## Review Checklist

Before declaring Phase 7.1 complete:

- `CreateBusCommand` is constructed with its real authoritative signature. fileciteturn33file0
- Bus creation remains `Application → handler → service → Network`. fileciteturn35file0 fileciteturn36file0
- `ToolBase` remains the UI interaction-to-command seam. fileciteturn36file0
- Canvas composition injects a real command facade instead of `None`. fileciteturn34file0
- `main.py` no longer needs dynamic Controller attachment for Bus dispatch. fileciteturn30file0
- No Core command manager is used by UI code.
- No Core model object is introduced into SLD projection.
- No second Application, command manager, event bus, or renderer architecture is introduced.
- Other equipment tools remain deferred.
- Every claim of passing behavior is backed by an actual verification result.
