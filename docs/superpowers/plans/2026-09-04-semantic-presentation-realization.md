# Semantic Presentation Realization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the missing semantic-to-presentation selection boundary to the live SLD canvas pipeline while preserving all existing Core, Application, SLD projection, Canvas, graphics-item, and locked-item contracts.

**Architecture:** `SLDCanvasNode` remains the complete semantic input. A dedicated semantic realization boundary interprets `properties["element_type"]` and returns only the minimum renderer-neutral presentation-selection information required by the concrete construction boundary. `SLDCanvasRenderSystem` remains orchestration/lifecycle owner and `SLDGraphicsItemFactory` remains construction-only.

**Tech Stack:** Python, PySide6/Qt graphics, pytest, existing GridForge SLD/Canvas architecture.

**Spec:** `docs/superpowers/specs/2026-09-04-semantic-presentation-realization-design.md`

## Global Constraints

- Core remains the sole owner of electrical truth.
- Application remains the mutation boundary.
- `SLDCanvasNode` is the complete semantic input to realization.
- Semantic source is `SLDCanvasNode.properties["element_type"]`.
- No duplicate `graphics_type`, `symbol_type`, or equivalent semantic field.
- Semantic realization does not access Core/Application services.
- Semantic realization does not create Qt graphics objects.
- Semantic realization does not own scene or SLD document state.
- Do not introduce `EquipmentRegistry`, `SymbolRegistry`, `EquipmentBase`, `SymbolBase`, or legacy generic renderer infrastructure as dependencies without new evidence.
- `SLDCanvasRenderSystem` remains synchronization/lifecycle/orchestration owner.
- `SLDGraphicsItemFactory` remains concrete construction boundary.
- `BusItem` and `LineItem` are locked and must not be modified.
- Unknown semantic types must fail explicitly; no fallback to `BusItem`.
- Connection realization remains `SLDCanvasConnection → SLDGraphicsItemFactory → LineItem`.

---

### Task 1: Establish the semantic realization test contract

**Files:**
- Create: `tests/test_semantic_presentation_realization.py`
- Reference: `ui/canvas/sld_canvas_projection.py`, `ui/canvas/sld_canvas_render_system.py`

**Interfaces:**
- Input: existing `SLDCanvasNode`.
- Required behavior: a supported semantic type produces a renderer-neutral presentation-selection result; unsupported types fail explicitly.

- [ ] **Step 1: Write the failing tests**

Create tests that construct `SLDCanvasNode` with `properties={"element_type": "bus"}` and assert the realization boundary returns a selection value that is distinct from the semantic input string. Add a second test with `element_type="unsupported-element"` and assert an explicit realization exception.

- [ ] **Step 2: Run the focused test file**

Run:
```bash
pytest tests/test_semantic_presentation_realization.py -v
```
Expected: FAIL because the realization module/contract does not yet exist.

- [ ] **Step 3: Inspect the failure before implementation**

Confirm the failure is caused by the missing realization contract rather than import/environment failure. If the environment cannot execute pytest, record that limitation and use repository-structural verification instead; do not claim the test passed.

- [ ] **Step 4: Commit the RED test**

```bash
git add tests/test_semantic_presentation_realization.py
git commit -m "test: define semantic presentation realization contract"
```

---

### Task 2: Introduce the minimum presentation-selection representation

**Files:**
- Create: `ui/canvas/semantic_presentation_realization.py`
- Test: `tests/test_semantic_presentation_realization.py`

**Interfaces:**
- Consumes: `SLDCanvasNode`.
- Produces: the smallest immutable renderer-neutral presentation-selection value required by the construction path.
- Does not expose Core/Application/Qt dependencies.

- [ ] **Step 1: Determine the smallest representation from the failing tests and current factory contract**

Use the existing construction vocabulary only where it is already proven. Do not introduce a descriptor hierarchy, registry, renderer instance, equipment instance, or symbol instance. If a minimal immutable value is required, keep it limited to presentation-selection identity and avoid carrying node identity, geometry, semantic type, properties, or electrical state.

- [ ] **Step 2: Implement only the realization boundary**

Implement a focused resolver/realizer that:
1. accepts `SLDCanvasNode`;
2. validates the node input using existing conventions;
3. reads `node.properties["element_type"]`;
4. maps only proven supported semantic types to presentation selections;
5. raises an explicit realization error for missing/unsupported semantic types;
6. performs no graphics construction.

- [ ] **Step 3: Run focused tests**

Run:
```bash
pytest tests/test_semantic_presentation_realization.py -v
```
Expected: PASS for the supported-selection and unsupported-type cases.

- [ ] **Step 4: Commit**

```bash
git add ui/canvas/semantic_presentation_realization.py tests/test_semantic_presentation_realization.py
git commit -m "feat: add semantic presentation realization boundary"
```

---

### Task 3: Integrate realization into the canonical SLD render path

**Files:**
- Modify: `ui/canvas/sld_canvas_render_system.py`
- Test: `tests/test_semantic_presentation_realization.py`
- Test: existing SLD render-system tests covering node synchronization

**Interfaces:**
- RenderSystem consumes `SLDCanvasSnapshot`.
- For each node it invokes semantic realization before concrete graphics construction.
- Factory remains responsible for concrete construction.

- [ ] **Step 1: Add a failing integration test**

Construct a snapshot containing a known semantic node and verify synchronization invokes the realization boundary and passes the resulting presentation selection into the construction path without giving the resolver access to scene/Core/Application state.

- [ ] **Step 2: Run the focused integration test**

Run the exact new test with pytest and confirm RED for the missing integration.

- [ ] **Step 3: Implement orchestration-only integration**

Modify `SLDCanvasRenderSystem` so its synchronization flow is conceptually:
```text
snapshot node
    ↓
semantic realization
    ↓
presentation selection
    ↓
concrete factory construction
    ↓
scene insertion
```
Keep snapshot validation, connection endpoint resolution, styling, scene ownership, clearing, and disposal in the RenderSystem.

- [ ] **Step 4: Run focused integration tests**

Run the relevant render-system tests and the semantic realization tests. Expected: PASS where the environment supports Qt/test execution.

- [ ] **Step 5: Commit**

```bash
git add ui/canvas/sld_canvas_render_system.py tests/
git commit -m "feat: integrate semantic realization into SLD rendering"
```

---

### Task 4: Preserve the construction boundary and remove silent semantic fallback

**Files:**
- Modify: `ui/canvas/sld_graphics_item_factory.py`
- Modify: `tests/test_sld_graphics_item_factory.py`
- Test: `tests/test_sld_typed_graphics_contract.py`

**Interfaces:**
- Factory receives already-selected presentation information rather than becoming a semantic resolver.
- Existing connection construction remains unchanged in responsibility.

- [ ] **Step 1: Add failing tests for the new construction contract**

Add tests proving that an unsupported semantic node cannot silently become `BusItem`, while preserving tests for concrete Bus and Line construction through their valid presentation selections.

- [ ] **Step 2: Run the focused factory tests**

Run:
```bash
pytest tests/test_sld_graphics_item_factory.py tests/test_sld_typed_graphics_contract.py -v
```
Expected: RED until the factory contract is aligned with the realization result.

- [ ] **Step 3: Make the minimum factory change**

Keep the factory construction-only. Do not add semantic mapping tables or registry lookups. Adapt its node construction input only as required to consume the presentation-selection result produced upstream. Preserve `BusItem` and `LineItem` signatures and implementations exactly.

- [ ] **Step 4: Run focused tests**

Expected: PASS for valid construction, explicit rejection of unsupported realization, and locked graphics-item contract.

- [ ] **Step 5: Commit**

```bash
git add ui/canvas/sld_graphics_item_factory.py tests/test_sld_graphics_item_factory.py tests/test_sld_typed_graphics_contract.py
git commit -m "fix: enforce explicit SLD presentation realization"
```

---

### Task 5: Regression verification across the SLD pipeline

**Files:**
- Test: all affected SLD/Canvas tests
- Reference: `docs/superpowers/specs/2026-09-04-semantic-presentation-realization-design.md`

**Interfaces:**
- Verify complete flow from Application read model through SLD projection, Canvas projection, realization, factory, and graphics scene.

- [ ] **Step 1: Run targeted regression suite**

Run the semantic realization, graphics factory, typed graphics, SLD projection, Canvas projection, and RenderSystem tests.

- [ ] **Step 2: Run the full test suite**

Run:
```bash
pytest -v
```
Expected: all available tests pass. If Qt/display or dependency setup prevents execution, capture the exact failure and do not classify it as a code regression without evidence.

- [ ] **Step 3: Perform structural architecture checks**

Verify:
- no Core imports in realization;
- no Application service dependency in realization;
- no `EquipmentRegistry`/`SymbolRegistry` dependency introduced;
- no generic renderer registry introduced;
- `BusItem` and `LineItem` unchanged;
- no duplicate semantic field introduced;
- unknown semantic types have explicit failure;
- RenderSystem remains lifecycle/orchestration owner;
- factory remains construction-only.

- [ ] **Step 4: Review the final diff**

Confirm only files justified by the design and plan changed. Reject unrelated refactors, abstractions, cleanup, or architectural expansion.

- [ ] **Step 5: Commit verification/documentation if needed**

Only if verification requires a documentation update:
```bash
git add docs/ tests/
git commit -m "test: verify semantic presentation realization pipeline"
```
Otherwise leave the implementation commits as the complete code history.

## Completion Criteria

The implementation is complete only when the repository demonstrates:

```text
SLDCanvasNode
      ↓
semantic presentation realization
      ↓
presentation selection
      ↓
SLDGraphicsItemFactory
      ↓
concrete presentation graphics
```

and all architecture invariants in the spec remain true. Runtime tests must be reported accurately; structural GitHub verification is not a substitute for passing runtime tests.
