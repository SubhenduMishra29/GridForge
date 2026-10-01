# ============================================================
# GridForge V2 — Batch 27 SLD Presentation Activation Static Re-audit
# Author: Subhendu Mishra
# ============================================================

## Authority

- Repository: `pandaraseswari03-collab/GridForge`
- Branch: `main`
- Verification mode: static source inspection only.
- Runtime GUI, pytest, CI, and startup execution were not performed.

## Finding

The previous Batch 27 implementation routed `EngineeringWorkspaceTabs.set_sld_document()`
only to `MapWorkspaceView`. The canonical `SLDCanvasSurface` therefore did not
receive the Application-authoritative `SLDDocument` during project activation.

## Correction

The canonical `SLDCanvasSurface` now owns the presentation binding capability while
continuing to reuse the existing:

- `CanvasCompositionPreparation.scene`
- `SLDCanvasProjection`
- `SLDCanvasRenderSystem`
- `GraphicsView`

`EngineeringWorkspaceTabs.set_sld_document()` forwards the document to that same
surface and retains MapWorkspaceView only as a secondary geometry projection.

`ProjectWorkspaceApplicationAdapter` now exposes a UI-level presentation activation
bridge. The bridge is invoked inside the Application presentation activation phase,
so new/open/close presentation changes are coordinated with lifecycle rollback.

The composition root binds that bridge to
`workspace_surface_host.set_sld_document`. The former `main.py`
`create_sld_document()` side effect and duplicate lifecycle factory configuration
were removed. SLD document creation/deserialization remains owned by the
Application presentation contract configured by `ProjectWorkspaceApplicationAdapter`.

`CanvasPlugin.synchronize_sld()` now delegates to the canonical SLD surface rather
than independently projecting and rendering the document.

`ui/sld/sld_surface.py` is reconciled as a compatibility adapter around the
canonical `SLDCanvasSurface`; it no longer owns a projection or render system.

## Static lifecycle evidence

### No project

`Application.presentation is None` causes the activation bridge to call
`set_sld_document(None)`, which clears the canonical renderer/scene.

### New project

Application creates the authoritative `SLDDocument`; the activation bridge calls
the canonical SLD surface; the surface projects the document model and synchronizes
the existing renderer against the existing scene.

### Open project

Application deserializes the authoritative `SLDDocument`; the same activation
bridge presents that document through the canonical surface, preserving persisted
SLD presentation geometry.

### Close project

Application transitions to no presentation; the activation bridge calls
`set_sld_document(None)`; the same canonical renderer clears the graphical state.

### Rollback

If graphical presentation activation fails, the adapter restores the previous
workspace state and re-presents the previous document. The Application lifecycle
therefore retains its existing transactional rollback boundary.

## Duplication audit

The production composition root still creates exactly one Application-owned
`SLDCanvasProjection` and one `SLDCanvasRenderSystem`, both targeting the
single `CanvasCompositionPreparation.scene`. `CanvasComposer` creates one
`SLDCanvasSurface` around the existing `GraphicsView`.

No second SLD GraphicsView, GraphicsScene, renderer, projection, CanvasComposition,
SymbolRegistry, or Application SLDDocument authority was introduced by this correction.

## Static disposition

**B27-FINAL-011 — STATICALLY VERIFIED**

Runtime GUI verification remains deferred.
