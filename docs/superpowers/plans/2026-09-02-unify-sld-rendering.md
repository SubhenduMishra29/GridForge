# GridForge V2 — Unified SLD Rendering Migration

**Author:** Subhendu Mishra

## Objective
Migrate GridForge V2 from the legacy `RenderSystem → RendererRegistry → typed renderers` path to the single authoritative SLD projection/rendering path, then remove the legacy renderer infrastructure.

## Target architecture

`Core/Application → SLD projection/read model → SLDDocument/Layout → SLDCanvasProjection → SLDCanvasSnapshot → SLDCanvasRenderSystem → QGraphicsScene`

## Work sequence

1. Trace remaining legacy renderer dependencies and classify each as migrate, adapt, or retire.
2. Remove legacy renderer dependencies from Canvas composition and tool contracts where they are not required by the new architecture.
3. Reconcile `BusItem` and `LineItem` against the unified SLD projection boundary before modifying or retiring either.
4. Complete SLD graphical geometry ownership so persistent position has one canonical presentation owner and projection snapshots contain sufficient connection geometry.
5. Migrate any surviving typed graphics behavior into the unified SLD projection path; no second renderer/state architecture.
6. Remove duplicate `RendererLoader` implementations and legacy renderer registrations after references are gone.
7. Remove legacy `RenderSystem`, `RendererRegistry`, `BusRenderer`, and `LineRenderer` only after repository-wide reference checks confirm they are unreachable.
8. Run import, unit, architecture-boundary, and application startup verification.
9. Re-scan repository references and freeze one SLD rendering ownership path.

## Safety rules

- Never restore or activate the legacy renderer path merely to make existing code executable.
- `BusItem` and `LineItem` remain untouched until their compatibility is established.
- QGraphics items remain projections; they never own electrical truth.
- Graphical position remains SLD/document presentation state.
- Core mutation continues through Application commands.
- Each production change requires a corresponding test-first verification where behavior changes.
