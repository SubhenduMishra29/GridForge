# GridForge V2 — Full SLD Creation Workflow Endpoint-Role Correction
# Author: Subhendu Mishra
# Date: 2026-09-28

## Scope

Target implementation repository: `madhuri196mishra-cpu/GridForge`
Branch: `main`

Architectural authority: `SubhenduMishra29/GridForge`

Mode: static source correction only. No tests, pytest, CI, application startup, GUI execution, or runtime verification were performed.

## Files changed

1. `ui/tools/model_placement_tool.py`
2. `ui/core/snap_system.py`

No Core, Application, CommandManager, CreationCommandFactory, CreationCommandPreparer, EndpointResolver, BusTool, SLD renderer/projection, Element List, SelectionManager, or Property Panel implementation was rewritten.

## Exact functions changed

### ui/tools/model_placement_tool.py

- `ModelPlacementTool.__init__`
  - retains the accepted endpoint candidate for the current interaction.
- `ModelPlacementTool.on_mouse_press`
  - keeps grid + object snapping for initial placement;
  - switches to endpoint-only snapping after placement;
  - refuses endpoint acquisition when required engineering configuration is incomplete.
- `ModelPlacementTool._pending_creation_role`
  - derives the next NEW-object CreationRole from canonical `CreationDefinition.terminal_requirements` and already acquired draft endpoints.
- `ModelPlacementTool._acquire_terminal`
  - no longer derives the NEW CreationRole from `SnapResult.terminal_name`;
  - adapts the accepted target through the existing `EndpointIdentityAdapter`;
  - stores the target endpoint under the pending NEW-object role via `CreationDraft.set_endpoint()`.
- `ModelPlacementTool._report_feedback`
  - uses an existing controller feedback hook when the composition provides one; no second feedback state authority was introduced.
- `ModelPlacementTool.on_mouse_release`
  - treats an accepted endpoint from press as authoritative;
  - does not re-snap the endpoint on release;
  - does not call final commit validation while another required terminal role remains.
- `ModelPlacementTool._snap_endpoint_result`
  - delegates electrical endpoint acquisition to the canonical SnapSystem endpoint-only operation.
- `ModelPlacementTool._clear_state`
  - clears the retained interaction candidate.

### ui/core/snap_system.py

- `SnapSystem.snap_endpoint`
  - added as the smallest explicit endpoint-only capability;
  - considers object/electrical candidates only;
  - never considers grid candidates.
- `SnapSystem._normalize_candidate`
  - corrected the return annotation to match the six-value normalized candidate actually returned by the implementation.

## CreationRole / TargetTerminal correction

The target terminal is no longer reused as the new object's creation role.

For example:

`Transformer.from <- Generator.terminal`

now follows:

`CreationDefinition -> pending role "from" -> SnapResult(Generator.terminal) -> EndpointIdentityAdapter -> EndpointReference.terminal(Generator, G1, "terminal") -> draft.set_endpoint("from", endpoint)`

The target terminal role remains `"terminal"`; the new Transformer role remains `"from"`.

The same rule applies to:

- single-terminal equipment: `terminal`;
- two-terminal equipment: `from`, then `to`;
- CT: `P1`, `P2`, `S1`, `S2`;
- PT: `primary_a`, `primary_b`, `secondary_a`, `secondary_b`;
- CVT: `H1`, `H2`, `X1`, `X2`.

Relay remains outside this generic endpoint acquisition path.

## Endpoint-only snapping

Initial placement continues to use:

`SnapSystem.snap(..., allow_grid=True, allow_object=True)`

After placement, endpoint acquisition uses:

`SnapSystem.snap_endpoint(scene_position)`

which resolves only the existing object/electrical snap candidates. A grid result therefore cannot satisfy a required electrical endpoint.

Bus and equipment presentation identity remain supplied by the existing SnapSystem candidate contract.

## Press/release consistency

An accepted endpoint candidate is retained between mouse press and mouse release.

Release does not perform a second endpoint snap. For multi-terminal equipment, release only advances the workflow when the accepted candidate exists; it does not replace that candidate with grid or another terminal.

## Multi-terminal progression

After the first endpoint:

- the endpoint remains in `CreationDraft.endpoints`;
- `_pending_creation_role()` derives the next missing required role;
- final commit is not attempted;
- feedback reports the next required role when a presentation feedback hook exists.

Only when no required terminal role remains does the canonical `validate_for_commit()` / command path become eligible.

## Canonical command path preserved

The corrected source still routes creation through:

`CreationDraft -> CreationCommandFactory -> CreationCommitIntent -> Application.prepare_creation_command() -> Application.execute() -> CommandManager -> Core`

The command factory and command preparer do not infer CreationRole.

## Bus and presentation preservation

`BusTool` was inspected and intentionally left unchanged.

Preview remains presentation-only. No Core object or permanent QGraphicsItem is created by the placement correction.

## Static coverage

The target repository's `EquipmentRegistry.create_default()` was reconciled against the canonical creation-role catalogue and exposes:

- Grid, Generator, Load, Shunt, Capacitor, Reactor, Solar, Battery, Motor, Synchronous Machine: `terminal`
- Line, Cable, Transformer, Switch, Breaker, Disconnector, Fuse: `from/to`
- Current Transformer: `P1/P2/S1/S2`
- Potential Transformer: `primary_a/primary_b/secondary_a/secondary_b`
- CVT: `H1/H2/X1/X2`
- Bus: dedicated placement path
- Relay: separate protection path

## Feedback limitation

The target repository contains `StatusPlugin.set_message()`, but the current ToolManager/Controller composition does not expose that presentation service to ModelPlacementTool. The correction therefore does not invent a second status/message authority.

The placement tool now reports through existing optional controller hooks (`show_status_message`, `set_status_message`, or `notify_user`) if a composition provides one. Wiring the canonical StatusPlugin into the existing tool composition remains an OPEN integration item if those hooks are absent.

## Audit register reconciliation

The target repository's `audit/MASTER_AUDIT_REGISTER.csv` and `audit/MASTER_AUDIT_REGISTER.md` were inspected. The literal IDs `SLD-F53` through `SLD-F73` are not present as current register rows.

No fabricated register rows or false closure statuses were added.

Required next action:

- reconcile/map `SLD-F53` through `SLD-F73` to the current target-repository register identifiers during the fresh static re-audit;
- evaluate each mapped item against the corrected source evidence;
- do not mark any item closed solely because these two files changed.

## Remaining OPEN items

1. Canonical status/message presentation is not directly exposed to ModelPlacementTool; existing optional hooks are used without creating a second feedback authority.
2. `SLD-F53` through `SLD-F73` are not literal rows in the target repository's current master register, so individual status reconciliation requires ID mapping during the next audit.
3. Full downstream SLD/Event/Element List/Selection/Property Panel closure remains subject to fresh static re-audit of the complete target tree.
4. Runtime verification remains deferred.

## Status

REMEDIATED — VERIFICATION REQUIRED

STATIC SOURCE CORRECTION COMPLETE

RUNTIME VERIFICATION — DEFERRED

Target main HEAD after correction: `d2fbff7f28a6b23f8bae99e0fdc131d39288d099`
