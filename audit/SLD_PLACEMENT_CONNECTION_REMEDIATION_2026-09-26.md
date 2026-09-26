# GridForge V2 — SLD Placement / Connection Root-Cause Remediation

**Date:** 2026-09-26  
**Branch:** `main`  
**Author:** Subhendu Mishra  
**Verification:** Static source re-audit only

## Result

The recorded placement/connection remediation scope **GF-SLD-WF-031 through GF-SLD-WF-087** has been corrected at the identified root-cause level. No pytest, CI, startup, GUI, or runtime verification was performed.

## Files modified

- `ui/tools/model_placement_tool.py` — existing position-first placement path was retained as the canonical implementation; static re-audit confirms no endpoint-first acquisition and no `ENDPOINT_FIELDS`.
- `ui/tools/transformer_tool.py` — converted from two-endpoint interaction to position-first Transformer placement with explicit engineering-basis validation.
- `ui/tools/default_tool_registry.py` — injects the canonical Presentation SymbolRegistry into placement tools.
- `main.py` — passes `PresentationBootstrap.symbol_registry` into the default tool registry.
- `core/application/application.py` — completes model-ID extraction used by position-first SLD projection.
- `core/application/services/transformer_model_service.py` — removes the obsolete endpoint-voltage helper and documents/retains explicit impedance reference voltage semantics.

## Recorded finding mapping

### GF-SLD-WF-031–GF-SLD-WF-042 — Position-first placement contract

`ui/tools/model_placement_tool.py` now captures a canvas position and builds the immutable Create<Model>Command without endpoint acquisition or `ENDPOINT_FIELDS`. All concrete placement tools use this path.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

### GF-SLD-WF-043–GF-SLD-WF-051 — SymbolDefinition-driven preview

`ModelPlacementTool._show_preview()` uses the canonical `SymbolRegistry` and transient `SymbolPreviewItem`; `show_segment()` is no longer used for equipment placement. `main.py` and `ui/tools/default_tool_registry.py` now inject the one PresentationBootstrap-owned registry.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

### GF-SLD-WF-052–GF-SLD-WF-062 — Optional external connectivity

Create commands for Grid/Generator/Load/Motor/Shunt/Reactor/Solar/SynchronousMachine/Battery and switching equipment retain optional endpoint references. `core/application/command_handlers.py` resolves endpoints only when present, so `None` remains a valid unconnected placement state.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

### GF-SLD-WF-063–GF-SLD-WF-070 — Authoritative terminal preservation

Core equipment models retain their authoritative Terminal/terminal-pair construction independently of external endpoint attachment. Placement therefore creates equipment terminals without manufacturing a Bus or electrical connection.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

### GF-SLD-WF-071–GF-SLD-WF-079 — Application position-first SLD projection

`Application._coordinate_pre_commit()` remains the single pre-commit projection hook and now extracts all placeable model identity fields, including generator/load/motor/grid/shunt/reactor/solar/synchronous-machine/battery/capacitor IDs. It then performs the existing transactional `AddSLDNodeCommand` projection.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

### GF-SLD-WF-080–GF-SLD-WF-087 — Transformer and connection separation

`TransformerTool` is now position-first and uses the real transformer SymbolDefinition preview. Its command explicitly carries `endpoint_from=None`/`endpoint_to=None` while requiring explicit impedance basis, base voltage, and base MVA/rating input. Wire/Line/Cable remain dedicated endpoint-to-endpoint connection tools; Application connection pre-commit remains separate from equipment placement.

**Static status:** CORRECTED — STATIC VERIFICATION COMPLETE

## Required lifecycle evidence

### Equipment placement

```
Palette
  -> concrete equipment tool
  -> SymbolDefinition preview
  -> click position
  -> immutable Create<Model>Command
  -> Application.execute()
  -> CommandManager
  -> Application model service
  -> Core equipment
  -> authoritative terminals
  -> _coordinate_pre_commit()
  -> transactional AddSLDNodeCommand
  -> SLD node
  -> existing SLD graphics/equipment factory
```

The command contracts statically accept optional external endpoints while carrying `presentation_x`/`presentation_y`. Core model-service create paths accept `None` endpoints for the placeable equipment in scope.

### Connection

```
existing terminal / bus
  -> SnapResult / EndpointReference
  -> Wire / Line / Cable connection command
  -> Application connection pre-commit
  -> SLD connection projection
  -> Core topology
```

Placement does not create an electrical connection.

### Transformer

```
Transformer tool
  -> transformer SymbolDefinition preview
  -> click position
  -> CreateTransformerCommand
       endpoint_from=None
       endpoint_to=None
       presentation_x/y
       explicit impedance_base_voltage_kv
       explicit impedance_base_mva or rate_mva
  -> Application
  -> TransformerModelService
  -> Core Transformer
  -> authoritative Branch terminals
  -> SLD projection
```

The service rejects a missing `impedance_base_voltage_kv`; it does not infer a voltage from an absent endpoint or invent a nominal voltage.

## Preserve / intentionally retained

- CommandManager remains the single execution/history/undo-redo gateway.
- Application remains the UI↔Core orchestration boundary.
- `_coordinate_pre_commit()` remains the existing position-first SLD projection mechanism.
- SLD nodes remain presentation state, not electrical truth.
- Core Terminal ownership and topology canonicalization remain unchanged.
- Wire/Line/Cable remain separate connection workflows.
- Existing SymbolDefinition, SymbolFactory, EquipmentFactory, SLDGraphicsItemFactory, and EquipmentItem architecture was not replaced.

## Remaining OPEN findings

**None identified within the recorded GF-SLD-WF-031–087 placement/connection scope from the supplied remediation contract.**

This statement is limited to the recorded scope above. It does not open or close CT/PT/CVT or other later audit batches.

## Scope control

No new audit scope was opened. The correction is limited to the recorded SLD placement/connection root causes and the minimum Application/projection wiring required to make the existing position-first architecture coherent.

## Commit sequence

- `99a194aed3c9ca341e8f20fe697d1ffd5169f8a0` — canonical SymbolRegistry injection into placement tools.
- `77aa054a226f81e0cbfbd133ed63223f35d79e64` — composition-root SymbolRegistry wiring.
- `d933099e5feab84206b899e160c56e02f8bbdbc9` — position-first Transformer placement.
- `d4231a37068579877941569b57ba3314572f6078` — complete Application placement identity extraction.
- `998b7e6ecb222b31bb53e784bfa6bdd8c70ffac0` — explicit Transformer impedance-basis service correction.

**Final engineering principle:** Place first. Connect separately. Preserve electrical semantics.
