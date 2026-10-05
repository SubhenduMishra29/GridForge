# GridForge V2 — SLD Terminal, Wire and Connection Lifecycle Final Static Reconciliation
**Project:** GridForge V2  
**Author:** Subhendu Mishra  
**Implementation Repository:** `madhuri196mishra-cpu/GridForge`  
**Branch:** `main`  
**Audit mode:** Static repository inspection only; runtime/GUI/pytest/CI execution not performed.

## Scope
Final source reconciliation of:
`Snap → Endpoint → WireTool → Command → Core → Event → Projection → Connection Item → Selection → Route → Undo/Redo → Reconciliation`.

## Corrections applied
1. `ui/tools/wire_tool.py`
   - Hardened failed/no-snap preview handling so a transient preview remains retryable and invalid target state is explicit.
   - Removed unsafe unpacking of an optional endpoint pair before command execution.
2. `ui/tools/endpoint_identity_adapter.py`
   - Replaced obsolete “Line connection” vocabulary with “Simple Wire connection”.
   - Preserved canonical equipment_id + terminal_role and Bus bus_id + attachment_id identity.
3. `ui/sld/items/sld_connection_item.py`
   - Enabled `ItemIsSelectable` so committed Simple Wire graphics can participate in canonical SelectionManager projection.
4. `ui/sld/sld_read_adapter.py`
   - Preserved `NetworkReadModel.simple_wires` through the SLD read adapter instead of silently dropping the authoritative Simple Wire read collection.
5. `ui/tools/default_tool_registry.py`
   - Retired the obsolete primary `line` interaction tool from the default active tool catalog. Line/Cable remain domain equipment concepts; Simple Wire is the connection interaction.

## Acceptance matrix

| ID | Requirement | Status | Static evidence |
|---|---|---|---|
| GF-AUD-WIRE-001 | WIRE_START identity | CLOSED | WireTool uses WIRE_START with object-only snapping; adapter preserves terminal role / Bus attachment. |
| GF-AUD-WIRE-002 | WIRE_TARGET identity | CLOSED | WireTool switches to WIRE_TARGET after source acquisition; grid is disabled. |
| GF-AUD-WIRE-003 | Multi-terminal snap identity | CLOSED | EquipmentItem emits one candidate per Core terminal with terminal_id + terminal_name; adapter requires an exact presentation-terminal match. |
| GF-AUD-WIRE-004 | Bus attachment identity | CLOSED | BusItem emits canonical attachment-N candidates with bus_id + attachment_id; Bus center is not emitted as an electrical endpoint. |
| GF-AUD-WIRE-005 | EndpointIdentityAdapter | CLOSED | Identity-only translation; no Core mutation/topology ownership; deterministic terminal/Bus validation. |
| GF-AUD-WIRE-006 | Draft endpoint path | CLOSED | WireTool creates DraftEndpointReference and CreateDraftConnectionCommand for draft snaps; DraftNetwork remains Application-owned. |
| GF-AUD-WIRE-007 | Core endpoint path | CLOSED | WireTool creates CreateSimpleWireConnectionCommand from EndpointReference; Application/Core validates it. |
| GF-AUD-WIRE-008 | Wire preview ownership | CLOSED | ConnectionPreview is transient; WireTool clears it on commit/cancel/deactivation and never registers it with SnapSystem. |
| GF-AUD-WIRE-009 | Simple Wire validation | CLOSED | EndpointCompatibility validates identity, self-links, same-equipment terminals, registration and electrical-domain rules; service validates before Core insertion. |
| GF-AUD-WIRE-010 | Permanent connection projection | CLOSED | Application pre-commit creates the SLDConnection companion transactionally; render system realizes permanent SLDConnectionItem from SLD snapshot. |
| GF-AUD-WIRE-011 | Connection canonical identity | CLOSED | SLD connection companion uses the command/Core connection_id; renderer keys realized presentation by that same ID. |
| GF-AUD-WIRE-012 | Connection selection | CLOSED | SLDConnectionItem is selectable and exposes canonical object_id; SelectionManager projects selection by object identity; inspector/deletion uses Application boundary. |
| GF-AUD-WIRE-013 | Route editing | CLOSED | SLDConnectionItem emits route-edit requests; SLDRouteEditController routes them to SLDController/Application. |
| GF-AUD-WIRE-014 | Engineer-owned route preservation | CLOSED | SLDRoute ownership distinguishes auto/engineer; auto routes may regenerate, engineer routes retain persisted interior points until explicitly edited. |
| GF-AUD-WIRE-015 | Connection deletion | CLOSED | Simple Wire deletion is an Application RemoveSimpleWireConnectionCommand; pre-commit removes its SLD companion in the same transaction. |
| GF-AUD-WIRE-016 | Connection undo | CLOSED | Reversible Simple Wire command plus transaction undo and semantic remove event reconcile Core and SLD presentation. |
| GF-AUD-WIRE-017 | Connection redo | CLOSED | Reversible command restores the original connection_id/endpoints; semantic create event and projection reconciliation recreate presentation. |
| GF-AUD-WIRE-018 | Refresh/reconciliation | PARTIAL | The persistent SLD companion is authoritative for authored presentation/route state and renderer refresh reconciles from the SLD snapshot. Application NetworkReadModel now preserves simple_wires, but the generic SLDReadSynchronizer does not itself materialize missing Simple Wire companions from that read collection because doing so outside an Application transaction would create a second presentation mutation path. |
| GF-AUD-WIRE-019 | No duplicate connection presentation | CLOSED | SLDCanvasRenderSystem maintains one realized item tuple per connection_id and removes/replaces stale realization before recreation. |
| GF-AUD-WIRE-020 | No obsolete primary Line Tool | CLOSED | Default tool catalog no longer registers/imports the obsolete primary `line` interaction tool; Simple Wire is the canonical wiring interaction. |
| GF-AUD-WIRE-021 | No direct UI/Core mutation | CLOSED | WireTool calls Application command execution; renderer/items/preview/adapter contain no Core mutation path. |

## Multi-terminal equipment contract
Static inspection confirms the canonical chain is present for Transformer, Breaker, Switch/Disconnector and Fuse through the shared EquipmentItem terminal enumeration and SymbolDefinition terminal anchors. Relay remains protection-domain equipment and does not acquire a second electrical endpoint authority.

## Frozen-architecture check
No new Core/UI boundary, topology authority, SnapSystem, renderer, connection authority, Line Tool, 3D layer, or draft-to-Core implicit promotion was introduced.

## Final conclusion
The requested correction is implemented on `main`. **20/21 acceptance items are CLOSED; GF-AUD-WIRE-018 is PARTIAL with the concrete architectural reason documented above.** Runtime/GUI behavior remains unverified in this static audit.
