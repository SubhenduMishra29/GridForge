# Core Completion — SynchronousMachine, Motor, Reactor and Solar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Application CRUD mutation lifecycle for SynchronousMachine, Motor, Reactor, and Solar while preserving the existing GridForge Application → Core architecture and Network/Registry ownership.

**Architecture:** Add one dedicated Application domain service per equipment family. Commands carry only immutable intent/value data; handlers resolve EndpointReference values through EndpointResolver and delegate to the correct service; services perform Core mutation through the existing Network add/remove lifecycle and transaction boundary. ModelService remains a delegation-only compatibility facade.

**Tech Stack:** Python, existing GridForge Application/Command/Transaction/Network layers, pytest static/source inspection only for this remediation.

**Spec:** User-provided Core Completion Remediation specification for baseline `a17fc7d9e10d86122dfd74b943ba9b935492d09d`.

## Global Constraints

- UI/Controller → Command → CommandManager → CommandHandler → Domain Model Service → Network → Registry / Topology.
- Do not redesign the architecture.
- Create only `SynchronousMachineModelService`, `MotorModelService`, `ReactorModelService`, and `SolarModelService`.
- `ModelService` remains a thin compatibility facade and contains no domain mutation logic.
- Commands contain Application intent/value data only; they never carry Core model objects or resolve endpoints.
- Endpoint-bearing commands use `EndpointReference`; handlers use the canonical `EndpointResolver`.
- Network and Registry remain the authoritative ownership boundary for equipment membership and lifecycle.
- Do not add generic Branch commands, generic Branch services, duplicate registries, GUI state, or service-local collections.
- PT, CT, and CVT remain distinct equipment types.
- Runtime execution is deferred; do not claim pytest or runtime verification passed.

---

### Task 1: Add the four dedicated domain services

**Files:**
- Create: `core/application/services/synchronous_machine_model_service.py`
- Create: `core/application/services/motor_model_service.py`
- Create: `core/application/services/reactor_model_service.py`
- Create: `core/application/services/solar_model_service.py`

**Interfaces:**
- Each service consumes `Network`, resolved `Bus | Terminal | None` endpoints where supported, model value fields, and an active `Transaction`.
- Each service produces `ApplicationResult` values and records transaction undo operations through the existing Network add/remove lifecycle.

- [ ] **Step 1: Add SynchronousMachineModelService**
  - Implement `create_synchronous_machine`, `update_synchronous_machine`, and `delete_synchronous_machine`.
  - Create validates `synchronous_machine_id`, validates the resolved endpoint, constructs `SynchronousMachine`, calls `network.add_synchronous_machine`, and records the inverse removal.
  - Update retrieves `synchronous_machine` through `Network.get_by_id`, checks the Core type, applies only supplied mutable fields, calls the model's existing validation API, and records a complete restore closure.
  - Delete retrieves the model, calls `network.remove_synchronous_machine`, and records the inverse add.

- [ ] **Step 2: Add MotorModelService**
  - Implement `create_motor`, `update_motor`, and `delete_motor` using the existing `Network.add_motor` / `remove_motor` boundary.
  - Preserve Motor-local validation by using its existing setters or validation API; do not create a second Motor model or local collection.
  - Preserve transaction undo behavior for create, update, and delete.

- [ ] **Step 3: Add ReactorModelService**
  - Implement `create_reactor`, `update_reactor`, and `delete_reactor`.
  - The Application endpoint parameter resolves to `Bus | Terminal | None` and is passed to the existing Reactor constructor through its `bus` compatibility parameter.
  - Use `network.add_reactor` / `network.remove_reactor` only for global membership.

- [ ] **Step 4: Add SolarModelService**
  - Implement `create_solar`, `update_solar`, and `delete_solar`.
  - Preserve Solar active/reactive power limits and local validation by using its existing public mutation/validation API.
  - Use `network.add_solar` / `network.remove_solar` only for global membership.

---

### Task 2: Add canonical CRUD commands

**Files:**
- Modify: `core/application/commands/model_commands.py`

**Interfaces:**
- Produce command constants and immutable `Command` subclasses for each CRUD operation:
  - `CREATE_SYNCHRONOUS_MACHINE`, `UPDATE_SYNCHRONOUS_MACHINE`, `DELETE_SYNCHRONOUS_MACHINE`
  - `CREATE_MOTOR`, `UPDATE_MOTOR`, `DELETE_MOTOR`
  - `CREATE_REACTOR`, `UPDATE_REACTOR`, `DELETE_REACTOR`
  - `CREATE_SOLAR`, `UPDATE_SOLAR`, `DELETE_SOLAR`
- Endpoint fields, when present, are typed as `EndpointReference | None` and are validated by the existing `_endpoint` helper.

- [ ] **Step 1: Add SynchronousMachine constants and commands**
  - Keep endpoint data as `EndpointReference`, never a Core `Bus` or `Terminal`.
  - Include only stable command intent/value fields from the existing Core model API.

- [ ] **Step 2: Add Motor constants and commands**
  - Carry Motor nameplate and operating value fields only.
  - Do not carry a Core Motor object or resolved endpoint.

- [ ] **Step 3: Add Reactor constants and commands**
  - Carry reactor identity, name, reactive-power injection, service state, and optional endpoint reference for creation.

- [ ] **Step 4: Add Solar constants and commands**
  - Carry Solar identity, operating point, power limits, service state, and optional endpoint reference for creation.
  - Do not expose `dynamic_model` as a command payload object.

- [ ] **Step 5: Export the new constants/classes in `__all__`**
  - Ensure the canonical command module exposes all twelve CRUD command types and constants.

---

### Task 3: Register handlers and enforce endpoint resolution

**Files:**
- Modify: `core/application/command_handlers.py`

**Interfaces:**
- `ModelCommandHandlers.handlers()` produces mappings for all twelve new command types.
- Each create handler resolves the command's `EndpointReference` through `EndpointResolver` and delegates to the matching service method.
- Update/delete handlers delegate by the model ID and value fields without direct Network mutation.

- [ ] **Step 1: Import the twelve command constants**
  - Keep imports in the canonical model command module.

- [ ] **Step 2: Register all twelve handlers**
  - Map every command constant to its dedicated handler method.

- [ ] **Step 3: Implement handler methods**
  - Add `create_synchronous_machine`, `update_synchronous_machine`, `delete_synchronous_machine`.
  - Add `create_motor`, `update_motor`, `delete_motor`.
  - Add `create_reactor`, `update_reactor`, `delete_reactor`.
  - Add `create_solar`, `update_solar`, `delete_solar`.
  - For each endpoint-bearing create handler, call `_resolve(..., "endpoint")` before invoking the service.
  - Do not inspect endpoint IDs or call Network directly inside handlers.

---

### Task 4: Extend ModelService only as a compatibility facade

**Files:**
- Modify: `core/application/services/model_service.py`

**Interfaces:**
- Add four private service instances and four public service properties.
- Add CRUD facade methods that delegate directly to the corresponding dedicated service.

- [ ] **Step 1: Import and construct the four dedicated services**
  - Instantiate each with the same canonical `Network` passed to `ModelService`.

- [ ] **Step 2: Add service properties**
  - `synchronous_machine_service`, `motor_service`, `reactor_service`, `solar_service`.

- [ ] **Step 3: Add delegation methods**
  - `create/update/delete_synchronous_machine`
  - `create/update/delete_motor`
  - `create/update/delete_reactor`
  - `create/update/delete_solar`
  - No mutation logic, endpoint resolution, or Network calls are added to the facade.

---

### Task 5: Remove stale generic Branch command references from Application topology classification

**Files:**
- Modify: `core/application/application.py`

**Interfaces:**
- `_TOPOLOGY_COMMANDS` remains a classification set for concrete topology commands only.
- `model.create_branch`, `model.update_branch`, and `model.delete_branch` must not appear as supported command lifecycle entries.

- [ ] **Step 1: Remove the three generic Branch command strings**
  - Keep concrete Line, Cable, Transformer, Switch, Disconnector, and Fuse topology commands unchanged.

---

### Task 6: Add static regression coverage

**Files:**
- Create: `tests/application/test_core_equipment_crud_static.py`

**Interfaces:**
- Tests inspect source files with `ast` and text matching; they do not instantiate the application or execute runtime behavior.

- [ ] **Step 1: Verify dedicated services exist**
  - Parse each service file and assert the expected class exists.
  - Assert each class defines `create_*`, `update_*`, and `delete_*` methods.

- [ ] **Step 2: Verify commands exist and are immutable**
  - Parse `model_commands.py` and assert the twelve constants and twelve `Command` subclasses exist.
  - Assert command constructors use `EndpointReference` for endpoint parameters where present.
  - Assert command payload construction does not reference Core model classes.

- [ ] **Step 3: Verify command and handler registration**
  - Parse `command_handlers.py` and assert every new command constant appears in `handlers()` and every handler method exists.
  - Assert endpoint-bearing create handlers invoke `EndpointResolver`.

- [ ] **Step 4: Verify service delegation and Network lifecycle**
  - Parse each dedicated service and assert create calls the matching `network.add_*`, delete calls the matching `network.remove_*`, and update retrieves the matching equipment family through `Network.get_by_id`.
  - Assert the ModelService facade delegates each CRUD method to the matching dedicated service.

- [ ] **Step 5: Verify architectural regressions are absent**
  - Assert no `CREATE_BRANCH`, `UPDATE_BRANCH`, or `DELETE_BRANCH` lifecycle constants/classes are present in `model_commands.py`.
  - Assert no generic Branch handler methods are present in `command_handlers.py`.
  - Assert no additional `ModelService` class exists under `core/application/services`.
  - Assert no new generic equipment service or generic Branch service file exists.

---

### Task 7: Static/source-level completion audit

**Files:**
- Inspect: all files changed by Tasks 1–6.

- [ ] **Step 1: Re-read the four equipment paths**
  - Confirm each path is `model → registry → network → service → command → handler → EndpointResolver where applicable`.

- [ ] **Step 2: Inspect diffs for ownership regressions**
  - Confirm handlers do not mutate Network directly.
  - Confirm services do not maintain equipment collections.
  - Confirm ModelService contains delegation only for the four new equipment families.

- [ ] **Step 3: Record verification status**
  - Static/source inspection: performed.
  - Runtime tests: deferred by scope.
  - Never report pytest passed or runtime verification completed.

---
