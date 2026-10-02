# GridForge V2 — Tool / Editor Context Static Reconciliation
Author: Subhendu Mishra
Date: 2026-10-02
Repository: pandaraseswari03-collab/GridForge
Branch: main
Verification: static implementation only

## Canonical path
Workspace → Area → Editor → Region → EditorContext → discipline Tool System → Concrete Tool → Application Command → Application → CommandManager → Core.

## VERIFIED
- ToolDefinition remains the immutable metadata contract.
- ToolSettings remains contextual tool behavior state, distinct from Inspector properties.
- ToolManager remains the SLD runtime lifecycle authority.
- ToolSession, ToolInteraction, and InteractionSession are not inserted into the SLD runtime chain.
- SelectionManager remains the canonical SLD selection owner; SLDState remains a read-through compatibility view.
- EditorContext remains immutable presentation state and does not own runtime services.
- ToolPolicy no longer documents a frozen select/bus/line catalogue.
- Contextual keymaps now use semantic actions and explicit editor contexts.
- Tool Shelf realization is metadata-driven through ToolDefinition and editor applicability.
- Control and Protection expose common ToolDefinition metadata while retaining discipline-specific runtime boundaries.

## PARTIAL
- Study ToolDefinitions are currently contextual presentation metadata; a future dedicated Study runtime may supply richer factories.
- Tool icon realization accepts an icon provider but the composition root has not yet supplied a single canonical icon provider to every Tool Shelf.
- Existing Control/Protection internal toolbars/palettes remain inside their discipline workspaces as compatibility presentation surfaces while the common Tool Shelf becomes the editor-region contract.

## LEGACY / COMPATIBILITY
- ui/tools/tool_registry.py is a retired compatibility shell.
- ui/tools/default_tool_registry.py provides concrete factories; ToolManager owns lifecycle.
- ui/workspace/workspace_legacy.py contains WorkspacePlacement only for external migration callers.
- PanelArea, DockBinding, and MainWindow dock methods are legacy utility-panel mechanics, not workspace policy.
- InteractionSession remains a Protection-specific transient structure.

## OPEN
- Exhaustive repository-wide code search through the connected GitHub index remains unavailable; targeted workspace/editor/main inspection was used instead.
- Runtime verification remains intentionally outstanding.

No Master Register IDs are closed by this pass.
