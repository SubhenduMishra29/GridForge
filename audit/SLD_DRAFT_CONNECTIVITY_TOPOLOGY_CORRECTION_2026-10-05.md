# GridForge V2 — SLD Draft / Connectivity / Topology / Study Correction Audit

**Author:** Subhendu Mishra  
**Implementation Repository:** `madhuri196mishra-cpu/GridForge`  
**Branch:** `main`  
**Audit mode:** Static source inspection only  
**Runtime status:** DEFERRED — pytest/GUI/startup/CI execution was not performed in this correction pass.

## Correction summary

The frozen architecture is preserved:

`UI/Tool -> immutable Command -> Application.execute() -> CommandManager -> Transaction -> Core -> semantic event -> ReadModel/Projection -> UI`.

The correction establishes:

- canonical `DraftEndpointReference` with terminal and Bus forms;
- one canonical endpoint pair per `DraftConnection`;
- draft-first placement through `DraftNetwork`;
- draft-aware SnapSystem and WireTool paths;
- deterministic draft-to-Core identity translation;
- Simple Wire component -> unique Bus boundary resolution;
- explicit contradiction/ambiguity rejection;
- TopologySnapshot population from active Buses only;
- topology invalidation for endpoint-bearing membership/state mutations;
- Application revision transitions inside the transaction boundary;
- Application topology revision reconciliation against the committed Core topology revision;
- movement snap through the centralized SnapSystem;
- SLD connection render invalidation when endpoint node geometry changes;
- Power Flow multi-island policy and Bus-ID keyed numerical results.

## Finding audit

| Finding | Status | Files inspected | Corrected mechanism | Remaining risk |
|---|---|---|---|---|
| GF-AUD-SLD-001 | STATICALLY VERIFIED | `ui/creation/creation_context.py`, `ui/creation/creation_definition.py`, `ui/tools/model_placement_tool.py`, `core/application/draft/network.py` | Placement no longer requires resolved Core topology; placement creates DraftEquipment. | Runtime GUI flow not executed. |
| GF-AUD-SLD-002 | STATICALLY VERIFIED | `ui/tools/model_placement_tool.py`, `ui/canvas/symbol_preview_item.py`, `ui/core/snap_system.py` | Draft presentation receives stable draft identity and terminal snap points. | Runtime snapping not executed. |
| GF-AUD-SLD-003 | STATICALLY VERIFIED | `core/application/draft/network.py`, `core/application/draft/__init__.py` | Canonical immutable `DraftEndpointReference` separates terminal and Bus identity. | None identified statically. |
| GF-AUD-SLD-004 | STATICALLY VERIFIED | `core/application/commands/draft_commands.py`, `core/application/draft/handlers.py`, `ui/tools/wire_tool.py` | Draft wire authoring uses immutable `CreateDraftConnectionCommand`; committed objects retain Core command path. | Runtime command registration not executed. |
| GF-AUD-DRAFT-001 | STATICALLY VERIFIED | `core/application/draft/network.py` | DraftConnection has one source/target identity pair and validates DraftEquipment endpoint mappings. | None identified statically. |
| GF-AUD-DRAFT-002 | STATICALLY VERIFIED | `core/application/draft/network.py`, `ui/tools/wire_tool.py` | Bus is a first-class DraftEndpointReference; it is never represented as fake equipment. | Runtime mixed draft/Bus wiring not executed. |
| GF-AUD-CONN-001 | STATICALLY VERIFIED | `core/network/connectivity.py`, `core/network/electrical_boundary.py` | Simple Wire is authoritative connectivity; physical Terminal.endpoint is reconciled against its unique derived Bus when present. | Runtime contradiction cases not executed. |
| GF-AUD-CONN-002 | STATICALLY VERIFIED | `core/network/network.py`, `core/network/connectivity.py` | Network.validate() rejects multi-Bus Simple Wire components and physical/Simple-Wire Bus contradictions. | Runtime validation not executed. |
| GF-AUD-TOPO-003 | STATICALLY VERIFIED | `core/network/network.py`, endpoint-bearing Application services | Membership and topology-relevant in-service/switching changes invalidate topology; Application revision follows the resulting Core revision. | A full mutation matrix was not runtime-executed. |
| GF-AUD-TOPO-004 | STATICALLY VERIFIED | `core/network/connectivity.py`, `core/network/electrical_boundary.py`, `core/network/topology.py` | Committed SLD Simple Wire relationships resolve through ConnectivityResolver; physical terminal attachment is not required as a duplicate authoring operation. | Runtime end-to-end case not executed. |
| GF-AUD-TOPO-005 | STATICALLY VERIFIED | `core/network/electrical_boundary.py` | ElectricalBoundaryResolver consumes ConnectivityResolver.bus_for_terminal(). | None identified statically. |
| GF-AUD-TOPO-006 | STATICALLY VERIFIED | `core/network/connectivity.py` | Canonical `bus_ids_for_terminal()` / `bus_for_terminal()` API added on the existing ConnectivityResolver. | None identified statically. |
| GF-AUD-TOPO-007 | STATICALLY VERIFIED | `core/network/topology.py` | EquipmentBusAttachment construction consumes the canonical electrical boundary, including Simple Wire-derived Bus identity. | Runtime snapshot verification deferred. |
| GF-AUD-STUDY-002 | STATICALLY VERIFIED | `core/analysis/power_flow_preparation.py`, `core/analysis/sequence_network_preparation.py`, `core/analysis/short_circuit_preparation.py` | Studies continue consuming TopologySnapshot; no study-specific SLD connectivity graph was introduced. | Numerical runtime verification deferred. |
| GF-AUD-RENDER-002 | STATICALLY VERIFIED | `ui/canvas/sld_canvas_render_system.py` | Connection render signature now includes source/target node geometry, forcing endpoint/route refresh after movement. | GUI movement not executed. |
| GF-AUD-SEL-001 | STATICALLY VERIFIED | `ui/tools/select_tool.py` | Drag movement passes through centralized SnapSystem grid policy before SetSLDNodePositionCommand. | GUI drag execution deferred. |
| GF-AUD-SNAP-002 | STATICALLY VERIFIED | `ui/core/snap_system.py`, `ui/tools/wire_tool.py`, `ui/tools/select_tool.py`, `ui/tools/model_placement_tool.py` | Snap contexts remain separated by allow_grid/allow_object and electrical endpoint handling; draft candidates use a dedicated presentation identity path. | Runtime interaction matrix deferred. |
| GF-AUD-REV-001 | STATICALLY VERIFIED | `core/network/network.py`, `core/application/revision_service.py`, `core/application/application.py` | Bus and endpoint-bearing mutations invalidate Core topology; Application revision adopts the actual committed Core topology revision. | Runtime revision assertions deferred. |
| GF-AUD-REV-002 | STATICALLY VERIFIED | `core/application/application.py`, `core/application/transaction.py`, `core/application/command_manager.py` | Revision transition is prepared in the transaction pre-commit phase; rollback restores it, while committed history does not attempt rollback. | Runtime history-failure injection deferred. |
| GF-AUD-REV-003 | STATICALLY VERIFIED | `core/application/application.py`, `core/application/revision_service.py` | Undo adopts the actual post-undo Core topology revision; redo uses the normal pre-commit revision transition. | Runtime undo/redo matrix deferred. |
| GF-AUD-TOPO-001 | STATICALLY VERIFIED | `core/network/topology.py`, `core/network/network.py` | Active operational topology now populates adjacency/snapshot from active Buses only. | Runtime inactive-Bus case deferred. |
| GF-AUD-PF-002 | STATICALLY VERIFIED | `core/analysis/power_flow_preparation.py`, `core/solver/power_flow/input.py` | Power Flow explicitly rejects multiple TopologySnapshot islands because the solver contract requires exactly one slack bus. | Runtime study case deferred. |
| GF-AUD-PF-003 | STATICALLY VERIFIED | `core/analysis/power_flow_preparation.py`, `core/solver/power_flow/result.py`, `core/solver/power_flow/nr_solver.py` | Prepared/solved Power Flow retains canonical Bus-ID ordering and PowerFlowResult now carries immutable bus_ids. | Numerical execution deferred. |
| GF-AUD-YBUS-002 | STATICALLY VERIFIED | `core/analysis/power_flow_preparation.py`, `core/numerical/ybus.py`, `core/solver/power_flow/nr_solver.py` | YBus continues to receive the corrected TopologySnapshot/PowerFlowInput Bus ordering; no second connectivity authority was introduced. | Runtime numerical verification deferred. |

## Acceptance coverage

### Draft-first
Transformer placement now enters `DraftNetwork` without requiring a Core Bus endpoint.

### Draft wiring
WireTool can author:
- draft terminal -> draft terminal;
- draft terminal -> existing Bus;
- existing Bus -> draft terminal;
- mixed draft terminal -> committed terminal.

### Commit
`CommitNetworkCommand` validates the complete draft, creates Core equipment, translates endpoints deterministically, creates authoritative Simple Wire relationships, and restores the draft through the same transaction on rollback/undo.

### Ambiguity / contradiction
A terminal connected through Simple Wire to multiple Bus endpoints is rejected. A physical Terminal.endpoint that disagrees with a unique Simple Wire-derived Bus is rejected.

### Topology / studies
TopologySnapshot consumes the corrected electrical boundary and active-Bus policy. Power Flow, Sequence Network and Short Circuit remain downstream consumers rather than rebuilding SLD connectivity.

### Presentation
SLD connection signatures now account for node geometry, and movement uses centralized snapping.

## Verification limitation

This is a **static repository correction/audit**. No pytest suite, GUI startup, interactive SLD workflow, numerical study, or CI run was executed in this pass. Therefore the statuses above mean **source-verified structural closure**, not runtime closure.

Any future runtime failure must be recorded separately rather than being inferred as closed from application launch behavior.
