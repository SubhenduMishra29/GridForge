# ============================================================
# File: ui/canvas/render_system.py
# GridForge Render System
# ============================================================
#
# PURPOSE
# -------
# Synchronizes the GridForge domain model with the
# QGraphicsScene.
#
#
# ARCHITECTURE
# ------------
#
#                 DOMAIN MODEL
#                       │
#                       │
#                       ▼
#                RenderSystem
#                       │
#                       │ asks for renderer
#                       ▼
#              RendererRegistry
#                       │
#          ┌────────────┼────────────┐
#          ▼            ▼            ▼
#      BusRenderer  LineRenderer  FutureRenderer
#          │            │            │
#          ▼            ▼            ▼
#       BusItem      LineItem    GraphicsItem
#
#
# IMPORTANT
# ---------
#
# RenderSystem does NOT import:
#
#     BusItem
#     LineItem
#     TransformerItem
#     GeneratorItem
#     LoadItem
#     etc.
#
# All renderer knowledge belongs to RendererRegistry.
#
#
# RESPONSIBILITIES
# ----------------
#
# RenderSystem:
#
#     1. Reads the domain model
#     2. Obtains appropriate renderers
#     3. Creates graphics items through renderers
#     4. Adds those items to the scene
#     5. Restores persistent selection
#     6. Keeps the scene synchronized with the model
#
#
# IT DOES NOT:
# ------------
#
#     - modify the domain model
#     - calculate electrical quantities
#     - handle mouse events
#     - implement tool behavior
#     - create model objects
#     - know individual QGraphicsItem classes
#
#
# GOLDEN RULE
# -----------
#
# MODEL → VIEW only.
#
# The RenderSystem must never modify the model.
#
#
# FULL REBUILD STRATEGY
# ---------------------
#
# Current GridForge UI uses a deterministic full-rebuild strategy:
#
#     scene.clear()
#     model → renderer → graphics items
#
# This is intentionally simple and reliable during the initial
# UI architecture phase.
#
# Later, an incremental rendering/cache system can be introduced
# without changing the Controller, tools, or model architecture.
#
# ============================================================

from __future__ import annotations

from typing import Any, Iterable, Optional


class RenderSystem:
    """
    Synchronizes the GridForge model with the graphics scene.

    Renderer implementations are resolved exclusively through
    RendererRegistry.

    Parameters
    ----------
    scene:
        QGraphicsScene used by the GridForge canvas.

    controller:
        GridForge Controller.

    renderer_registry:
        Runtime RendererRegistry containing mappings such as:

            Bus  → BusRenderer
            Line → LineRenderer
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
        controller: Any,
        renderer_registry: Any,
    ) -> None:
        """
        Initialize the RenderSystem.

        The registry is injected rather than imported.

        This is important because RenderSystem must remain
        independent of concrete renderer implementations.
        """

        self.scene = scene
        self.controller = controller
        self.renderer_registry = renderer_registry

        # ----------------------------------------------------
        # Automatically respond to relevant controller events.
        #
        # This makes RenderSystem a self-contained UI system.
        #
        # The Controller remains unaware of rendering details.
        # ----------------------------------------------------

        self.controller.subscribe(
            "model_changed",
            self._on_model_changed,
        )

        self.controller.subscribe(
            "selection_changed",
            self._on_selection_changed,
        )

    # ========================================================
    # EVENT HANDLERS
    # ========================================================

    def _on_model_changed(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> None:
        """
        React to a model-changed event.

        A model modification invalidates the current visual
        representation, therefore the scene is rebuilt.
        """

        self.rebuild()

    # --------------------------------------------------------

    def _on_selection_changed(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> None:
        """
        React to a selection change.

        For the current full-rebuild architecture, selection
        changes also rebuild the scene.

        This keeps selection visuals deterministic.

        Later this can be optimized to update only affected
        graphics items without changing the public architecture.
        """

        self.rebuild()

    # ========================================================
    # MAIN RENDER ENTRY POINT
    # ========================================================

    def rebuild(self) -> None:
        """
        Rebuild the entire graphics scene from the model.

        Processing order:

            1. Clear scene
            2. Obtain model
            3. Render model elements
            4. Restore selection

        The model is read only.

        No model object is created, deleted, or modified here.
        """

        # ----------------------------------------------------
        # 1. Clear existing graphics
        # ----------------------------------------------------
        #
        # QGraphicsScene owns the visual representation.
        #
        # Clearing the scene does NOT clear Controller selection
        # because selection is stored independently using model IDs.
        # ----------------------------------------------------

        self.scene.clear()

        # ----------------------------------------------------
        # 2. Obtain the domain model
        # ----------------------------------------------------

        model = self.controller.model

        # ----------------------------------------------------
        # 3. Render all model elements
        # ----------------------------------------------------
        #
        # We deliberately do not write:
        #
        #     BusItem(...)
        #     LineItem(...)
        #
        # here.
        #
        # RendererRegistry decides which renderer handles each
        # model element.
        # ----------------------------------------------------

        for element in self._iter_model_elements(model):

            self._render_element(
                element,
                model,
            )

    # ========================================================
    # MODEL ELEMENT ITERATION
    # ========================================================

    def _iter_model_elements(
        self,
        model: Any,
    ) -> Iterable[Any]:
        """
        Yield model elements that should be displayed.

        Current GridForge model structure:

            model.graph.buses
            model.graph.lines

        This method intentionally isolates knowledge of the
        current Graph storage structure.

        When Graph later exposes a generic iterable of network
        elements, only this method needs to change.

        IMPORTANT
        ---------
        This method does not import Bus or Line classes.
        """

        graph = model.graph

        # ----------------------------------------------------
        # Buses
        # ----------------------------------------------------

        for bus in graph.buses.values():
            yield bus

        # ----------------------------------------------------
        # Lines
        # ----------------------------------------------------

        for line in graph.lines.values():
            yield line

    # ========================================================
    # ELEMENT RENDERING
    # ========================================================

    def _render_element(
        self,
        element: Any,
        model: Any,
    ) -> Optional[Any]:
        """
        Render one model element.

        Parameters
        ----------
        element:
            Model object to render.

        model:
            Complete GridForge model.

        Returns
        -------
        QGraphicsItem | None
            Created graphics item.

        Renderer contract
        -----------------
        A renderer should provide:

            create_item(element, controller)

        The renderer is responsible for constructing the
        appropriate QGraphicsItem.
        """

        # ----------------------------------------------------
        # Resolve renderer based on the actual model class.
        # ----------------------------------------------------

        renderer_class = (
            self.renderer_registry.get_renderer(
                type(element)
            )
        )

        # ----------------------------------------------------
        # No renderer registered.
        # ----------------------------------------------------
        #
        # We intentionally skip unsupported model elements
        # rather than crashing the entire canvas.
        #
        # This allows the model to contain future elements that
        # have not yet received a UI renderer.
        # ----------------------------------------------------

        if renderer_class is None:
            return None

        # ----------------------------------------------------
        # Create the graphics item.
        # ----------------------------------------------------
        #
        # Renderer classes are responsible for their own
        # construction details.
        #
        # RenderSystem only knows the renderer contract.
        # ----------------------------------------------------

        item = renderer_class.create_item(
            element,
            self.controller,
        )

        if item is None:
            return None

        # ----------------------------------------------------
        # Restore persistent selection.
        #
        # Selection is stored by MODEL ID in Controller.
        #
        # Graphics items are disposable and therefore must
        # never be the source of truth for selection.
        # ----------------------------------------------------

        element_id = getattr(
            element,
            "id",
            None,
        )

        if (
            element_id is not None
            and element_id
            in self.controller.selected_ids
        ):

            if hasattr(item, "setSelected"):
                item.setSelected(True)

        # ----------------------------------------------------
        # Add visual item to scene.
        # ----------------------------------------------------

        self.scene.addItem(item)

        return item

    # ========================================================
    # SELECTION UPDATE
    # ========================================================

    def refresh_selection(self) -> None:
        """
        Refresh selection visuals without changing model state.

        This method is currently implemented using a full rebuild
        because the GridForge renderer architecture is still in
        the deterministic full-render phase.

        It exists as a separate API so that a future incremental
        selection renderer can replace the implementation without
        changing Controller or tool code.
        """

        self.rebuild()

    # ========================================================
    # MANUAL REFRESH
    # ========================================================

    def refresh(self) -> None:
        """
        Explicitly request a complete visual refresh.

        Useful during:

            - application startup
            - canvas reset
            - model import
            - project loading
            - debugging
        """

        self.rebuild()

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def renderer_for(
        self,
        element: Any,
    ) -> Optional[type]:
        """
        Return the renderer class responsible for a model element.

        This is primarily a diagnostic/helper API.
        """

        return self.renderer_registry.get_renderer(
            type(element)
        )

    # --------------------------------------------------------

    def renderer_status(self) -> dict[str, str]:
        """
        Return the current renderer registry state.

        Useful for diagnostics and startup validation.
        """

        return self.renderer_registry.list_renderers()

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "RenderSystem("
            f"scene={type(self.scene).__name__}, "
            f"renderers={len(self.renderer_registry)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RenderSystem",
]
```
