# GridForge V2 — Reference SLD Workspace UI Static Correction
# Date: 2026-09-29
# Author: Subhendu Mishra

## Target

Implementation repository:

- `madhuri196mishra-cpu/GridForge`
- branch: `main`

The supplied reference image is treated as the target presentation shape for the SLD engineering workspace:

- dark application/menu/toolbar shell;
- project/system explorer;
- searchable equipment library;
- central SLD document surface with document tab and canvas controls;
- right-side engineering properties inspector;
- bottom element list, messages/events, and study cases;
- engineering status/grid/snap presentation.

## Corrective implementation

The correction remains presentation/composition work and does not introduce a second SLD authority.

### Changed files

- `ui/core/qt.py`
  - extended the single Qt import boundary with tree/table/tab presentation widgets.

- `ui/canvas/canvas_composition.py`
  - added `SLDCanvasSurface` around the existing canonical `GraphicsView`;
  - added SLD document/tab chrome;
  - added presentation-only Normal/Placement/Connection mode selector;
  - added zoom/fit controls wired to the existing `NavigationController`;
  - added project-aware SLD document title presentation;
  - retained the existing `SLDCanvasProjection` and `SLDCanvasRenderSystem` unchanged as the SLD projection/render authority.

- `ui/panels/default_panels.py`
  - realized the Project Explorer as a presentation tree;
  - expanded the Equipment Browser with search/filter and catalogue category presentation;
  - preserved equipment selection -> existing ToolManager activation path;
  - added presentation sizing metadata to the canonical panel specifications.

- `ui/panels/element_list_panel.py`
  - changed the read-only element presentation to a structured engineering table:
    ID / Name / Type / Nominal Voltage / Status.

- `ui/projection/element_list_projection.py`
  - exposes nominal-voltage and status presentation fields from the Application read model.

- `ui/plugins/panels_plugin.py`
  - honors presentation-only minimum dock dimensions from `PanelSpec.metadata`.

- `ui/styling/stylesheet.qss`
  - added SLD document chrome, project-tree, engineering-table, equipment-search, and panel presentation rules.

- `main.py`
  - synchronizes the MainWindow title and SLD document presentation title from the existing Application project lifecycle context.

## Architecture preservation

The implementation continues to use the frozen path:

```
Engineer
  -> Equipment Palette
  -> Tool activation
  -> Canvas interaction / live preview
  -> Placement command
  -> Application.execute()
  -> CommandManager
  -> Transaction
  -> Core engineering object
  -> Semantic event
  -> Application read model
  -> SLD projection
  -> SLD document
  -> SLD canvas projection
  -> SLD canvas snapshot
  -> SLDCanvasRenderSystem.synchronize()
```

No UI panel or canvas presentation object was made a Core mutation authority.

No second SLD synchronizer, topology authority, endpoint identity authority, or parallel SLD document architecture was introduced.

The new `SLDCanvasSurface` is presentation chrome only; the existing `GraphicsView`, SLD projection, snapshot, and render system remain canonical.

## Static re-audit disposition

**STATICALLY VERIFIED**

Source inspection confirms:

1. the new canvas surface wraps the existing GraphicsView rather than replacing it;
2. Equipment Browser activation still delegates through the existing ToolManager;
3. element-list data still originates from the Application read model projection;
4. panel sizing is presentation metadata consumed by PanelsPlugin;
5. project/title presentation reads Application project lifecycle state;
6. no direct UI -> Core mutation path was added;
7. no runtime/test/CI/app-start verification was performed.

**RUNTIME VERIFICATION — DEFERRED**

Visual rendering, Qt event delivery, actual palette placement, application startup, and runtime interaction remain deferred under the project audit rules.
