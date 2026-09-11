# C9 Application Read Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the immutable Application read projection for the frozen 22-type SLD vocabulary and protection read boundary without bypassing Core/Application architecture.

**Architecture:** Keep `ElementReadModel` as the canonical immutable envelope. Replace the generic attribute whitelist with explicit per-equipment projection rules, preserve authoritative terminal/connectivity identities, and extend protection read models/facade for Relay state and bindings. Keep `SLDReadAdapter` consuming Application DTOs only.

**Tech Stack:** Python, dataclasses, immutable mappings/tuples, pytest, existing GridForge Core/Application/SLD architecture.

**Spec:** C9 Application Read Contract Remediation supplied by the user in this conversation.

## Global Constraints

- Core remains sole authority for domain/electrical/protection truth.
- Application remains the sole UI ↔ Core read/orchestration boundary.
- `ElementReadModel`, `NetworkReadModel`, `RelayReadModel`, and `ProtectionReadModel` remain immutable transport models.
- No `model.__dict__`, Core object references, mutable Core dictionaries, or direct UI/SLD/renderer/controller/tool/plugin → Core access.
- Preserve the frozen 22-type SLD vocabulary; Relay remains protection-owned.
- Every materially modified/new source file retains `Author: Subhendu Mishra` in the established header format.
- No unrelated refactoring or command/history/event architecture changes.

### Task 1: Inventory authoritative Core properties and existing test fixtures

**Files:**
- Inspect: `core/model/*`, `core/network/*`, `core/protection/*`, existing Application read tests.
- Test: existing read-service/read-model/SLD tests.

- [ ] **Step 1: Identify actual Core attribute names and terminal shapes for all 22 semantic types.**
- [ ] **Step 2: Identify existing read-service, protection, and SLD adapter test fixtures.**
- [ ] **Step 3: Record any requested C9 fields whose Core property names differ, preserving Core authority and explicit read-key mapping.**

### Task 2: Add failing tests for the 22-type projection contract

**Files:**
- Create/Modify: existing Application read-service test module following repository test layout.
- Test: all 22 semantic types.

- [ ] **Step 1: Add one focused test per semantic type asserting element type, ID, labels, required canonical attributes, authoritative values, and connectivity.**
- [ ] **Step 2: Add immutability/Core-leak tests for mappings, nested connectivity data, and DTO object exposure.**
- [ ] **Step 3: Add derived-state tests for explicitly derived fields such as fuse/disconnector conducts where supported by the contract.**
- [ ] **Step 4: Run the focused tests and verify they fail because the projection contract is incomplete.**

### Task 3: Implement explicit network projection rules

**Files:**
- Modify: `core/application/read_service.py`
- Modify: `core/application/read_models.py` only where immutable nested protection/read data requires it.

- [ ] **Step 1: Replace the generic hard-coded property whitelist with explicit per-type projection functions/registry.**
- [ ] **Step 2: Implement required Bus, Line, Cable, Transformer, Switch, Breaker, Disconnector, Fuse, Load, Generator, Synchronous Machine, Motor, Shunt, Capacitor, Reactor, Solar, Battery, Grid fields using authoritative Core properties.**
- [ ] **Step 3: Implement explicit CT/PT/CVT field mappings and preserve semantic terminal roles in immutable connectivity/terminal references.**
- [ ] **Step 4: Keep connectivity references as stable identifiers and never expose Core terminal objects.**
- [ ] **Step 5: Run focused projection tests and make them pass.**

### Task 4: Complete Relay and Protection read contract

**Files:**
- Modify: `core/application/read_models.py`
- Modify: `core/application/read_service.py`
- Modify: `core/application/application.py`
- Modify: `core/application/__init__.py` if exports require adjustment.

- [ ] **Step 1: Add failing tests for `plugin_id`, settings, picked-up/tripped state, and immutable input-channel bindings.**
- [ ] **Step 2: Add immutable Relay fields and immutable binding representation without exposing protection-domain objects.**
- [ ] **Step 3: Project authoritative Relay state and bindings from `ProtectionSystem`.**
- [ ] **Step 4: Add `Application.read_protection()` and `Application.read_relay(relay_id)` using the configured protection read service without changing command architecture.**
- [ ] **Step 5: Run protection tests and make them pass.**

### Task 5: Remediate SLDReadAdapter

**Files:**
- Modify: `ui/sld/sld_read_adapter.py`
- Test: existing/new SLD read adapter tests.

- [ ] **Step 1: Add failing tests proving network DTOs remain consumable without Core imports/access.**
- [ ] **Step 2: Add Relay semantic projection from `ProtectionReadModel`, including protection-domain association/binding references rather than forced empty connectivity.**
- [ ] **Step 3: Preserve the explicit 22-type SLD vocabulary through the existing `semantic_type` mapping.**
- [ ] **Step 4: Run adapter tests and make them pass.**

### Task 6: Full verification and boundary audit

**Files:**
- Inspect: modified Application/SLD files and repository boundary references.
- Test: relevant existing suite plus new C9 tests.

- [ ] **Step 1: Run all focused C9 tests.**
- [ ] **Step 2: Run the relevant existing Application, Core, protection, and SLD test suites.**
- [ ] **Step 3: Search modified code for prohibited direct UI/SLD/renderer/controller/tool/plugin → Core access.**
- [ ] **Step 4: Produce a 22-type projection matrix covering required fields, connectivity, immutability, and SLD consumption.**
- [ ] **Step 5: Verify no unrelated command, transaction, history, undo/redo, event, lifecycle, registry, topology, or plugin-boundary regressions.**
- [ ] **Step 6: Commit the completed C9 remediation to the working branch.**
