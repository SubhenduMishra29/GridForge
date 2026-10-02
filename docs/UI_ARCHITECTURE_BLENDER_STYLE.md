# GridForge V2 — Engineering Workspace Architecture

Author: Subhendu Mishra

## Composition model

GridForge uses a Blender-inspired composition model without importing Blender
implementation or domain semantics:

```text
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
Presentation / Interaction
        |
        v
Application Commands / Queries
        |
        v
       Core
        |
        v
Semantic Events
        |
        v
Read Models / Projections
```

The frozen GridForge Core/Application boundary remains authoritative. Areas,
Editors and Regions are UI composition infrastructure only.

## Canonical logical contracts

- `ui/workspace/area.py` — immutable `AreaDefinition`.
- `ui/workspace/editor.py` — immutable `EditorDefinition`.
- `ui/workspace/region.py` — immutable `RegionDefinition`.
- `WorkspaceDefinition` and `WorkspaceLayout` now carry Area/Editor state.
- Existing `WorkspacePlacement` / `PanelArea` data remains as a compatibility
  migration path for persisted/legacy workspace state.
- `ui/editors/common/editor_host.py` is the shared Qt realization boundary.
- `ui/editors/sld/sld_editor.py`, `control/control_editor.py`,
  `protection/protection_editor.py`, and `study/study_editor.py` are
  domain-editor composition adapters.

## Blender-to-GridForge mapping

| Blender | GridForge |
| --- | --- |
| Window | GridForge Application Window |
| Workspace | Engineering Workspace |
| Area | Engineering UI Area |
| Editor | Engineering Editor |
| 3D Viewport | SLD / Control / Protection Canvas |
| Outliner | Engineering Explorer |
| Properties | Contextual Inspector |
| Toolbar | Engineering Tool Shelf |
| Sidebar | Editor Inspector / Context Panel |
| Timeline | Study / Dynamic Timeline |
| Overlays | Engineering Validation / Results Overlay |
| Mode | Engineering Workspace / Editor Mode |

## Migration boundary

The historical `ControlSurfaceHost` name remains as a compatibility facade.
Its implementation now delegates surface switching to the shared
`EngineeringEditorHost`, so callers do not acquire a second workspace
manager, renderer, symbol registry, equipment registry, or command pipeline.

Legacy panel docks remain a compatibility realization boundary until the
existing panel composition is fully converted to Area-owned regions. They are
not allowed to become domain authorities.

## SLD invariants

The SLD editor continues to use the canonical `CanvasComposition`,
`SLDCanvasProjection`, `SLDCanvasRenderSystem`, symbol registry, equipment
registry and ToolManager. Preview state remains transient; committed changes
continue through Application commands.

## Persistence

Protection presentation is part of the canonical project package alongside
SLD, Control and Protection configuration. The persistence service save
signature now explicitly accepts `protection_presentation`, matching the
existing bootstrap save call and load model.

Runtime verification is intentionally outside this architecture conversion.
