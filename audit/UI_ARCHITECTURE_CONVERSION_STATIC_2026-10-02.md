# GridForge V2 — Blender-Inspired UI Architecture Static Reconciliation
Author: Subhendu Mishra
Date: 2026-10-02
Mode: static implementation only

## CURRENT CANONICAL
The canonical presentation model is now:

WorkspaceDefinition
→ WorkspaceManager
→ WorkspaceLayout
→ AreaDefinition
→ EditorDefinition
→ RegionDefinition
→ EngineeringEditorHost
→ EditorContext
→ discipline Tool System
→ Application command boundary.

WorkspaceDefinition and WorkspaceLayout no longer contain WorkspacePlacement or panel-placement state.

WorkspaceRealizer no longer consumes PanelArea, WorkspacePlacement, dock groups, or QDockWidget geometry to realize workspace policy. Its dock bindings are explicitly compatibility-only utility-panel mechanics.

WorkspaceController passes the active workspace identity into editor realization so an immutable EditorContext snapshot is propagated when the active editor changes.

EngineeringEditorHost now retains active editor, Area, Region and EditorContext presentation state and supports presentation-only Area maximize/restore.

SLD, Control, Protection and Study editor implementations now compose explicit Header/Tool Shelf/Tool Settings/Canvas/Inspector/Diagnostics/Status regions as applicable.

## VERIFIED
- Area → Editor → Region contracts are Qt-independent.
- WorkspaceManager is the logical workspace authority.
- MainWindow remains a mechanical window shell.
- Tool Shelf uses ToolDefinition metadata and editor applicability.
- Selection remains owned by SelectionManager.
- EquipmentDefinition and ToolDefinition remain separate.
- Core/Application ownership is unchanged.
- No UI persistence is introduced into Core.
- No QGraphicsItem or QWidget is part of workspace definition state.

## LEGACY / COMPATIBILITY
- ui/workspace/workspace_legacy.py contains the retired WorkspacePlacement type.
- PanelArea remains available only for legacy utility-panel callers.
- PanelsPlugin and MainWindow retain dock creation/hosting because existing utility panels have not yet been physically relocated into editor-owned Region widgets.
- ControlSurfaceHost retains its historical class name but internally delegates to EngineeringEditorHost.

## PARTIAL
- Existing utility panels are not yet physically re-homed into Sidebar/Diagnostics/Explorer Region widgets; they remain legacy presentation implementations outside canonical workspace policy.
- Control and Protection discipline surfaces still contain their historical internal palettes/toolbars in addition to the common editor Tool Shelf region.
- Study has a contextual ToolDefinition presentation set but not a separate Study runtime factory registry.

## OPEN
- Full repository-wide reference elimination cannot be claimed because the connected GitHub code-search index is unavailable/incomplete.
- Runtime verification is intentionally not performed in this correction.

## Register discipline
The requested GF-UI-STATE-001..005, GF-UI-INPUT-001..005 and GF-UI-TOOL-002..013 findings remain RE-AUDIT REQUIRED / PARTIAL as applicable. Compatibility presence alone is not closure evidence.
