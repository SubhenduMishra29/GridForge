# GridForge V2 — Engineering Workspace Architecture
Author: Subhendu Mishra

## Current canonical composition

GridForge uses a Blender-inspired composition model without importing Blender
implementation or domain semantics:

Application Window
    |
    v
Workspace
    |
    v
Areas
    |
    v
Editors
    |
    v
Regions
    |
    v
EditorContext
    |
    v
Discipline Tool System
    |
    v
Application Commands / Queries
    |
    v
Core

Areas, Editors and Regions are UI composition infrastructure only.

## Canonical logical contracts

- ui/workspace/area.py — immutable AreaDefinition.
- ui/workspace/editor.py — immutable EditorDefinition.
- ui/workspace/region.py — immutable RegionDefinition.
- WorkspaceDefinition and WorkspaceLayout carry only Area composition.
- ui/editors/common/editor_host.py is the shared Qt realization boundary.
- SLD, Control, Protection and Study editors compose explicit Regions.
- EditorContext carries contextual state without owning runtime services.

## Blender-to-GridForge mapping

| Blender | GridForge |
| --- | --- |
| Window | GridForge Application Window |
| Workspace | Engineering Workspace |
| Area | Engineering UI Area |
| Editor | Engineering Editor |
| 3D Viewport | 2D SLD / Control / Protection Canvas |
| Outliner | Engineering Explorer Region |
| Properties | Contextual Inspector Region |
| Toolbar | Engineering Tool Shelf Region |
| Sidebar | Editor Sidebar / Inspector Region |
| Timeline | Study / Dynamic Timeline Region |
| Overlays | Engineering Validation / Results Overlay |
| Mode | Engineering Editor Mode |

## Compatibility boundary

ui/workspace/workspace_legacy.py contains the retired WorkspacePlacement type
for external migration callers only. PanelArea, DockBinding and MainWindow
dock APIs are legacy utility-panel mechanics.

None of these compatibility types participates in WorkspaceDefinition,
WorkspaceLayout, WorkspaceManager policy, or canonical Area realization.

ControlSurfaceHost retains its historical name for compatibility but delegates
editor switching to EngineeringEditorHost.

## SLD invariants

The SLD editor continues to use the canonical CanvasComposition,
SLDCanvasProjection, SLDCanvasRenderSystem, SymbolRegistry, EquipmentRegistry
and ToolManager. Preview remains transient; committed changes continue through
Application commands.

## Persistence

Transient Qt widgets, QGraphicsItems, Tool runtime objects and SelectionManager
internals remain outside Core persistence.

Runtime verification is intentionally outside this architecture conversion.
