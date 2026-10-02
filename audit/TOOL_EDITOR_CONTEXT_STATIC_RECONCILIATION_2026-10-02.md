# GridForge V2 — Tool System and Editor Context Static Reconciliation
Author: Subhendu Mishra
Date: 2026-10-02
Implementation repository: pandaraseswari03-collab/GridForge
Branch: main
Verification mode: static inspection only

## Scope
Reconciled the common editor/tool contracts around the existing SLD runtime path:

Workspace -> Area -> Editor -> Region -> EditorContext -> Tool System -> Concrete Tool -> Application -> Core.

No pytest, CI, application startup, GUI/runtime verification, or Core electrical changes were performed.

## Implemented

- Added `ui/tools/tool_definition.py` as the immutable Qt-independent ToolDefinition metadata contract.
- Added `ui/tools/tool_settings.py` as the immutable contextual ToolSettings model.
- Preserved EquipmentDefinition separately; its existing `tool_id` remains the relationship to interaction tooling.
- Preserved `ui/core/tool_manager.py` as the SLD runtime authority and did not insert ToolSession/ToolInteraction between ToolManager and ToolBase.
- Demoted ToolState to a diagnostic/read snapshot and added ToolStateSnapshot compatibility alias.
- Reconciled InteractionManager so it no longer inspects `WireTool._preview`; WireTool now exposes the semantic `has_source_endpoint` contract.
- Added immutable EditorContext to `ui/workspace/engineering_context.py` without owning runtime services.
- Reconciled SLDState so selection and active-tool state are read-through compatibility views backed by SelectionManager/ToolManager rather than locally stored authorities.
- Reconciled ToolPolicy so it no longer contains the obsolete select/bus/line catalogue; contextual ToolDefinition capabilities/mode are accepted by policy evaluation.
- Added structural ToolDefinition validation to ToolValidator.
- Reconciled ToolShortcutRegistry into contextual keymaps with no embedded default tool catalogue.
- Added common ToolDefinition bridges for Control descriptors and Protection tool metadata while retaining discipline-specific runtime behavior.
- Demoted ToolSession, ToolInteraction, and InteractionSession to supporting state structures; they are not mandatory global runtime layers.

## Ownership reconciliation

| Concern | Canonical owner | Static result |
|---|---|---|
| Tool metadata | ToolDefinition | IMPLEMENTED |
| Equipment metadata | EquipmentDefinition | PRESERVED SEPARATELY |
| SLD tool runtime | ui.core.tool_manager.ToolManager | PRESERVED |
| Tool lifecycle | ToolManager + ToolBase | PRESERVED |
| Concrete interaction state | Concrete Tool | PRESERVED |
| Creation session | CreationContext | PRESERVED |
| Selection | SelectionManager | SLDState demoted to read-through |
| Editor context | EditorContext | IMPLEMENTED |
| Tool mode | ToolMode | PRESERVED |
| Tool policy | ToolPolicy + ToolDefinition/context | RECONCILED |
| Structural tool validation | ToolValidator | RECONCILED |
| Tool settings | ToolSettings | IMPLEMENTED |
| Keymaps | Contextual ToolShortcutRegistry | RECONCILED |
| Preview | Preview layer / concrete tool | PRESERVED |
| Domain validity | Application/Core | UNCHANGED |
| Command execution | Application | UNCHANGED |
| Persistence | Existing persistence boundary | UNCHANGED |
| Rendering | Presentation layer | UNCHANGED |

## Compatibility / remaining paths

1. `ui/tools/tool_registry.py` remains a retired compatibility shell and is not a runtime authority.
2. `ui/tools/default_tool_registry.py` remains a factory mapping consumed by ToolManager; it does not own tool instances/lifecycle.
3. `ToolSession` and `ToolInteraction` remain available as supporting data structures. They are not inserted into the SLD runtime chain.
4. `InteractionSession` remains used by Protection as a discipline-specific transient container.
5. Control retains `ControlToolDescriptor/ControlToolRegistry` for presentation compatibility, but descriptors now expose the common ToolDefinition contract.
6. Protection retains its own controller/runtime boundary and now declares its contextual tools using ToolDefinition.
7. Repository-wide code search through the connected GitHub code-search index was unavailable/incomplete; therefore this report does not claim exhaustive reference elimination. Direct inspection covered the canonical affected modules and current known compatibility paths.
8. Existing Master Register IDs are not closed by this pass. Runtime verification remains outstanding.

## Static conclusion

The canonical SLD runtime remains:

ToolManager -> ToolBase -> Concrete Tool -> CreationContext/SelectionManager -> Application -> Core.

No second mandatory ToolManager/ToolSession/ToolInteraction runtime layer was introduced. The principal duplicate authorities identified in the affected modules were demoted or redirected to their canonical owners.

Status: REMEDIATED — STATIC VERIFICATION REQUIRED
