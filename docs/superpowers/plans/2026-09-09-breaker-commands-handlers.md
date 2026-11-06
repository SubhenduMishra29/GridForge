# Breaker Application Commands and Handlers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Breaker command and handler coverage so Breaker intent follows the canonical `Command → Handler → SwitchingModelService → Core` path.

**Architecture:** Extend the existing switching command family rather than introducing a Breaker-specific service. Commands contain immutable intent/value data; handlers resolve endpoint references at the Application boundary and delegate all mutation to `SwitchingModelService`.

**Tech Stack:** Python, existing GridForge Application command/handler framework, pytest-style tests already present in `tests/`.

**Spec:** Bounded Batch B.1 design approved by the user on 2026-09-09; repository architecture baseline governs all implementation choices.

## Global Constraints

- Core owns electrical truth; no Core mutation logic may be duplicated in commands or handlers.
- Application is the mandatory mutation boundary.
- Use the existing canonical `EndpointResolver`; do not introduce a second resolver.
- Preserve public signatures and compatibility APIs.
- `ModelService` remains a compatibility facade.
- Breaker remains owned by `SwitchingModelService`.
- No Network or Core changes are required for this batch.
- Each remediation action remains isolated on its own Git branch.

---

### Task 1: Add failing Breaker command/handler contract tests

**Files:**
- Create: `tests/test_breaker_commands_handlers.py`

**Interfaces:**
- Consumes: existing command and handler APIs.
- Produces: regression coverage for Breaker command constants, payloads, handler registration, endpoint resolution, and service delegation.

- [ ] **Step 1: Write tests for all seven Breaker command types.**
- [ ] **Step 2: Write tests asserting Breaker commands are exported by `core.application.commands`.**
- [ ] **Step 3: Write tests asserting `ModelCommandHandlers.handlers()` registers every Breaker command.**
- [ ] **Step 4: Write tests for create/update handler endpoint resolution and delegation.**
- [ ] **Step 5: Verify the tests fail against the current implementation.**

### Task 2: Add Breaker command contracts

**Files:**
- Modify: `core/application/commands/model_commands.py`
- Modify: `core/application/commands/__init__.py`

**Interfaces:**
- Consumes: `Command`, `EndpointReference`.
- Produces: `CreateBreakerCommand`, `UpdateBreakerCommand`, `DeleteBreakerCommand`, `OpenBreakerCommand`, `CloseBreakerCommand`, `PutBreakerInServiceCommand`, `TakeBreakerOutOfServiceCommand` and their command-type constants.

- [ ] **Step 1: Add Breaker command constants.**
- [ ] **Step 2: Add immutable create/update/delete command payloads using endpoint references where applicable.**
- [ ] **Step 3: Add operational-state commands with only Breaker identifiers.**
- [ ] **Step 4: Export all Breaker command symbols from the commands package.**
- [ ] **Step 5: Re-run the contract tests.**

### Task 3: Add Breaker handler registration and delegation

**Files:**
- Modify: `core/application/command_handlers.py`

**Interfaces:**
- Consumes: Breaker command constants/payloads and `EndpointResolver`.
- Produces: registered handler methods that delegate to the compatibility facade without mutating Core directly.

- [ ] **Step 1: Import Breaker command constants.**
- [ ] **Step 2: Register all seven Breaker command handlers.**
- [ ] **Step 3: Resolve `endpoint_from` and `endpoint_to` through `EndpointResolver` for create/update when present.**
- [ ] **Step 4: Delegate to Breaker methods exposed through `ModelService`.**
- [ ] **Step 5: Re-run focused tests.**

### Task 4: Verify and commit the isolated action

**Files:**
- No additional production files unless verification exposes a necessary compatibility defect.

- [ ] **Step 1: Run focused Breaker tests if an execution environment is available.**
- [ ] **Step 2: Run static import/source verification.**
- [ ] **Step 3: Confirm no Core/Network files changed.**
- [ ] **Step 4: Commit the completed Batch B.1 action on `remediation/b1-breaker-commands-handlers`.**
- [ ] **Step 5: Record exact commit SHA and verification status.**
