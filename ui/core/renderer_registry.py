"""
Renderer Registry

Location:
---------
ui/core/renderer_registry.py

Purpose:
--------
Central registry that maps model element types to their corresponding
renderer implementations.

This enables a fully decoupled rendering pipeline where:
- The RenderSystem does NOT know about specific UI items
- New model elements can be introduced without modifying core files

Architecture:
-------------
Model Element Type → Renderer → QGraphicsItem

Example:
--------
Bus → BusRenderer → BusItem
Line → LineRenderer → LineItem

Usage:
------
registry.register(Bus, BusRenderer)
renderer = registry.get_renderer(Bus)

Extensibility:
--------------
To add support for a new model element:
1. Create a renderer class
2. Register it using registry.register(...)
3. Done — no changes required elsewhere
"""


class RendererRegistry:
    """
    Maintains mapping between model types and renderer classes.
    """

    def __init__(self):
        # ------------------------------------------------------
        # Internal mapping:
        # { ModelClass: RendererClass }
        # ------------------------------------------------------
        self._renderers = {}

    # ==========================================================
    # REGISTRATION API
    # ==========================================================

    def register(self, model_type, renderer):
        """
        Register a renderer for a specific model type.

        Parameters:
        -----------
        model_type : type
            The class of the model element (e.g., Bus, Line)

        renderer : class
            Renderer class implementing:
                create_item(element, controller)

        Behavior:
        ---------
        - Overwrites existing renderer if already registered
        - Logs registration for debugging
        """

        self._renderers[model_type] = renderer
        print(f"[RendererRegistry] Registered renderer for {model_type.__name__}")

    # ==========================================================
    # LOOKUP API
    # ==========================================================

    def get_renderer(self, model_type):
        """
        Retrieve renderer for a given model type.

        Parameters:
        -----------
        model_type : type

        Returns:
        --------
        renderer class OR None if not found

        Behavior:
        ---------
        - Direct lookup
        - Falls back to parent class if exact match not found
        """

        # Direct match
        if model_type in self._renderers:
            return self._renderers[model_type]

        # Fallback: check inheritance chain
        for registered_type in self._renderers:
            if issubclass(model_type, registered_type):
                return self._renderers[registered_type]

        return None

    # ==========================================================
    # DEBUG / INTROSPECTION
    # ==========================================================

    def list_renderers(self):
        """
        Returns a dictionary of registered renderers.

        Useful for debugging and validation.
        """
        return {
            model.__name__: renderer.__name__
            for model, renderer in self._renderers.items()
        }
