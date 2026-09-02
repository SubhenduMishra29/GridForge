# Canvas Composition Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish an application-owned Canvas composition boundary using existing services.

**Architecture:** Compose existing services without changing their responsibilities, introducing a second renderer framework, or moving electrical truth into presentation.

**Tech Stack:** Python, Qt abstraction, existing GridForge UI services, pytest.

**Spec:** Approved GridForge V2 Canvas Composition Boundary design.

## Global Constraints
- Core owns authoritative electrical truth.
- Application controls meaningful mutation.
- UI expresses intent/results.
- Existing renderer contracts remain authoritative.
- BusItem and LineItem are not modified.
- PluginManager remains plugin lifecycle orchestration.
- PluginContext remains a dependency carrier.
- MainWindow remains a Qt host.
- Author generated GridForge source/docs as Subhendu Mishra.

### Task 1: Verify constructors and implement composer
- [ ] Verify constructors of every composed service.
- [ ] Add focused tests.
- [ ] Implement minimal composer.
- [ ] Run tests.

### Task 2: Integrate CanvasPlugin
- [ ] Test the plugin receives the composition.
- [ ] Rewire only the construction seam.
- [ ] Run tests.

### Task 3: Integrate application bootstrap
- [ ] Compose Canvas from the application root.
- [ ] Preserve plugin lifecycle and workspace ordering.
- [ ] Run tests.

### Task 4: Verify boundaries
- [ ] Verify scene/service identity.
- [ ] Verify selection/rendering ownership.
- [ ] Verify BusItem/LineItem unchanged.
- [ ] Run full available tests.
