# GridForge V2 — Engineering Workspace Architecture
Author: Subhendu Mishra

## Current canonical composition

GridForge uses a Blender-inspired composition model without importing Blender implementation or domain semantics:

```text
Application Window
  → Workspace
  → Areas
  → Editors
  → Regions
  → EditorContext
  → Discipline Tool System
  → Application Commands / Queries
  → Core
```

Areas, Editors and Regions are UI composition infrastructure only.

## Canonical logical contracts

- `ui/workspace/area.py` — immutable AreaDefinition.
- `ui/workspace/editor.py` — immutable EditorDefinition.
- `ui/workspace/region.py` — immutable RegionDefinition.
- WorkspaceDefinition and WorkspaceLayout carry only Area composition.
- `ui/editors/common/editor_host.py` is the shared Qt realization boundary.
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

`ui/workspace/workspace_legacy.py` contains the retired WorkspacePlacement type for external migration callers only. PanelArea, DockBinding and MainWindow dock APIs are legacy utility-panel mechanics.

None of these compatibility types participates in WorkspaceDefinition, WorkspaceLayout, WorkspaceManager policy, or canonical Area realization.

ControlSurfaceHost retains its historical name for compatibility but delegates editor switching to EngineeringEditorHost.

## SLD invariants

The SLD editor uses the canonical CanvasComposition, SLDCanvasProjection, SLDCanvasRenderSystem, SymbolRegistry, EquipmentRegistry and ToolManager.

- Preview is transient authoring state.
- Committed equipment/connectivity changes use Application commands.
- A symbol or QGraphicsItem is not an equipment object.
- Graphical snapping, crossing and route geometry do not establish electrical connectivity.
- Persistent SLD document/layout state is distinct from Core equipment and network relationships.
- Runtime graphics are reconstructed projections, not persistence authorities.

## Phase-domain conductor editor boundary

PR #908 and the subsequent mainline D15F increments provide Application-owned graph-edit commands and SLD-derived graph construction for supported Line/Cable conductors, Breaker/Switch/Disconnector/Fuse pole paths, and Transformer winding/neutral/earth paths. The graph builder resolves canonical equipment terminals and Bus attachment slots from committed topology and explicit Core construction; it does not infer physical paths from canvas coordinates.

The remaining UI gap is a complete engineer-facing configuration and inspection workflow for all supported physical-conductor construction data, plus a general-purpose graph editor for explicit nodes/segments not generated from equipment construction. Such tools must preview without mutation, validate through Application, commit transactionally, and expose unsupported paths. Ordinary Simple Wire route geometry must never synthesize phase-domain graph edges.

## Qt and persistence

Qt access remains centralized through `ui/core/qt.py`. Core must not import Qt, QGraphics, SLD or UI types.

Transient Qt widgets, QGraphicsItems, Tool runtime objects and SelectionManager internals remain outside Core persistence. Persistent presentation state is serialized semantically and reprojected after load/undo/redo.

## Verification boundary

This document records architecture contracts and source-level implementation boundaries. It does not claim that every editor, tool, panel, placement workflow, graph editor or runtime projection has been visually or end-to-end verified.
