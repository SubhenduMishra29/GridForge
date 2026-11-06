# GridForge V2 Master Architectural Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the remaining obsolete UI/Core mutation paths and reconcile the current repository with the frozen GridForge V2 Application boundary, in the mandated C1→C10 order.

**Architecture:** Core remains authoritative and headless. All UI-originated mutation crosses `core.application.Application.execute()`; UI controllers coordinate interaction only; tools depend on `application`; Application owns command, transaction/history, endpoint resolution, events, and read models; SLD/Canvas remain presentation projections.

**Tech Stack:** Python, PySide6 UI, GridForge Core/Application services, pytest, GitHub repository APIs.

**Spec:** Master Architectural Correction & Closure Prompt supplied by the user on 2026-09-11.

## Global Constraints

- Core must remain headless and independent of Qt/UI/controllers/canvas/SLD/plugins.
- Application is the sole UI↔Core orchestration and mutation boundary.
- No UI/Core command-manager path, duplicate Application namespace, duplicate history, transaction, endpoint resolver, or compatibility architecture.
- Tool dependency contract is `application=`, never `command_manager=`.
- Every created/materially modified GridForge file must contain `Author: Subhendu Mishra`.
- Do not weaken type contracts, add `Any` to hide defects, fabricate commands, or bypass Application.
- No unrelated refactoring.
- Findings are CLOSED only with architectural removal, canonical path, old-path removal, passing relevant verification, and downstream integration evidence.

---

### Task 1: C1 Controller boundary

**Files:**
- Modify: `ui/core/controller.py`
- Modify: controller/canvas consumers discovered during tracing
- Test: existing `tests/ui/core/test_controller.py` plus a focused regression test if required

**Interfaces:**
- Controller retains UI coordination state and Application reference.
- Undo/redo, when exposed, delegate only to `Application.undo()` / `Application.redo()`.
- Controller exposes no Core accessor and no Core command-manager accessor.

- [ ] Write/extend failing architectural tests proving Controller cannot retain Core or Core command-manager authority.
- [ ] Run the focused tests and verify RED.
- [ ] Trace all current Controller callers before production edits.
- [ ] Remove `_core`, `core`, `get_core`, `set_core`, and direct Core command-manager access.
- [ ] Preserve valid tool/project/UI coordination behavior.
- [ ] Run focused controller tests and verify GREEN.
- [ ] Search repository for obsolete Controller Core access and update downstream consumers.

### Task 2: C2 canonical Application namespace

**Files:**
- Modify any stale import sites discovered by repository-wide search.
- Remove only genuinely obsolete duplicate namespace files if present.
- Test: Application namespace regression coverage.

**Interfaces:**
- Canonical Application package remains `core.application`.

- [ ] Search for `application.commands`, `application.services`, and `application.command`.
- [ ] Classify every result before changing it.
- [ ] Add/extend a regression assertion that only `core.application` is used.
- [ ] Correct obsolete imports and remove obsolete duplicate package paths without compatibility re-exports.
- [ ] Verify imports and targeted tests.

### Task 3: C3 unified Tool dependency contract

**Files:**
- Modify: `ui/tools/tool_base.py`
- Modify: `ui/tools/default_tool_registry.py`
- Modify: `ui/tools/tool_manager.py`
- Modify: concrete tools/constructors found to violate the contract
- Test: `tests/test_tool_dependency_contract.py` and focused tool tests

**Interfaces:**
- Tool construction contract uses `application`, `controller`, `selection_manager`, and `snap_system` as applicable.
- Tool execution calls `self.application.execute(command)`.
- ToolManager owns runtime tool instances/lifecycle; registry provides definitions/factories only.

- [ ] Extend tests to reject `command_manager=` construction and direct Core dependencies.
- [ ] Run RED.
- [ ] Trace ToolBase, ToolManager, registry, factory, and representative tools.
- [ ] Implement one canonical dependency path.
- [ ] Run targeted tests and verify GREEN.

### Task 4: C4 registry/lifecycle and tool coverage

**Files:**
- Modify: `ui/tools/default_tool_registry.py`, `ui/tools/tool_registry.py`, `ui/tools/tool_manager.py`, concrete tool definitions as required.
- Test: tool registry/manager coverage tests.

- [ ] Enumerate supported equipment vocabulary against Application command/handler capability.
- [ ] Remove duplicate construction modes.
- [ ] Ensure registered tools construct through `application=`.
- [ ] Ensure ToolManager is the runtime lifecycle authority.
- [ ] Add regression coverage for all supported tool definitions.
- [ ] Verify.

### Task 5: C5 equipment tool paths

**Files:**
- Modify representative and deficient tools: Bus, Line, Cable, Transformer, Breaker, plus other supported tools as required.
- Test: focused tool command-path tests.

- [ ] Verify each tool builds an immutable command.
- [ ] Verify each command reaches the canonical Application handler/service.
- [ ] Remove stale capability guards.
- [ ] Correct CableTool without TransformerTool inheritance coupling.
- [ ] Correct TransformerTool/ModelPlacementTool constructor and execution path.
- [ ] Verify representative Bus/Line/Cable/Transformer/Breaker vertical slices.

### Task 6: C6 engineering configuration

**Files:**
- Modify: `ui/tools/line_tool.py` and only required command/application payload/service contracts.
- Test: line engineering parameter boundary tests.

- [ ] Separate UI placement state from engineering parameters.
- [ ] Ensure R/X/rating/nominal voltage/thermal limits enter Application command payloads.
- [ ] Prevent Controller from becoming electrical authority.
- [ ] Verify through command→handler→service→Core path.

### Task 7: C7 endpoint authority

**Files:**
- Modify deficient tools/resolvers only after tracing `core/application/endpoint_resolver.py`, `core/application/endpoint_reference.py`, and UI connection helpers.
- Test: endpoint identity valid/invalid resolution coverage.

- [ ] Verify tools emit endpoint identities only.
- [ ] Route resolution/validation through Application endpoint resolver.
- [ ] Remove duplicate UI/Core endpoint interpretation where it is authoritative rather than merely presentational.
- [ ] Verify valid and invalid endpoint cases.

### Task 8: C8 contingency semantics

**Files:**
- Modify only if current code still violates isolation/bus-outage semantics.
- Test: contingency isolation and bus-outage tests.

- [ ] Inspect current contingency implementation; do not trust the historical closure register.
- [ ] Verify isolated study state and bus outage semantics.
- [ ] Confirm authoritative project Network is unchanged.
- [ ] If already correct, record evidence and do not edit.

### Task 9: C9 SLD coverage and UI event path

**Files:**
- Modify only deficient SLD/UI event/projection files.
- Test: SLD supported-type, event-to-refresh, and renderer-boundary tests.

- [ ] Verify read-model→SLD synchronizer→document→projection→graphics pipeline.
- [ ] Ensure graphics factories do not resolve Core domain objects.
- [ ] Verify semantic equipment vocabulary and supported-type realization.
- [ ] Verify Application events reach UIUpdateBoundary without direct Core callbacks.

### Task 10: C10 documentation, repository-wide regression, and closure

**Files:**
- Modify audit/correction register and current documentation only after implementation evidence exists.
- Add regression tests where practical.

- [ ] Search repository for `command_manager=`, `_core`, `get_core`, `set_core`, `application.commands`, `application.services`, `network =`, `self.network`, `core.command_manager`, and UI Core mutation imports.
- [ ] Classify every occurrence as valid/obsolete/violation/test-only/documentation-only.
- [ ] Correct every architectural violation.
- [ ] Run targeted and broad tests available in the repository environment.
- [ ] Perform end-to-end acceptance path including undo/redo and SLD refresh.
- [ ] Update the correction register without renumbering or erasing historical findings.
- [ ] Report remaining OPEN and deferred verification explicitly.
