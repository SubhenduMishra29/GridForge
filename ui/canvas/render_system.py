"""
Render System

Location:
---------
ui/canvas/render_system.py

Purpose:
--------
Responsible for translating the data model into visual QGraphicsItems.

This system:
-------------
- Clears and rebuilds the scene
- Delegates rendering to registered renderers
- Does NOT know about specific item types (bus, line, etc.)

Architecture:
-------------
Model → RenderSystem → Renderer Plugins → QGraphicsItems → Scene

Extensibility:
--------------
To support new element types:
1. Create a renderer plugin
2. Register it in the renderer registry
3. NO changes required here
"""

class RenderSystem:
    """
    Rebuilds the scene using registered renderers.
    """

    def __init__(self, scene, controller, renderer_registry):
        """
        Parameters:
        -----------
        scene : QGraphicsScene
            The scene where items are rendered

        controller : Controller
            Provides access to the model

        renderer_registry : RendererRegistry
            Maps model types → renderer classes
        """
        self.scene = scene
        self.controller = controller
        self.renderer_registry = renderer_registry

    # ==========================================================
    # MAIN ENTRY POINT
    # ==========================================================

    def rebuild(self):
        """
        Clears and rebuilds the entire scene from the model.
        """

        # ------------------------------------------------------
        # Clear existing visuals
        # ------------------------------------------------------
        self.scene.clear()

        model = self.controller.model

        # ------------------------------------------------------
        # Iterate over all model elements generically
        # ------------------------------------------------------
        for element in self._iterate_model(model):
            self._render_element(element)

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    def _iterate_model(self, model):
        """
        Yields all drawable elements from the model.

        This isolates knowledge of model structure.
        """

        # Example structure — extend ONLY here if model changes
        yield from model.graph.buses.values()
        yield from model.graph.lines.values()

    # ----------------------------------------------------------

    def _render_element(self, element):
        """
        Uses the renderer registry to create a visual item.
        """

        renderer = self.renderer_registry.get_renderer(type(element))

        if not renderer:
            print(f"[RenderSystem] No renderer for {type(element).__name__}")
            return

        item = renderer.create_item(element, self.controller)

        if item:
            self.scene.addItem(item)
