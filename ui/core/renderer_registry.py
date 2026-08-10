```python
# ============================================================
# File: ui/core/renderer_registry.py
# GridForge Renderer Registry
# ============================================================
#
# PURPOSE
# -------
# Maintains the runtime mapping between GridForge model
# element types and their renderer implementations.
#
#
# ARCHITECTURE
# ------------
#
#     Core Model
#         │
#         │ model element
#         ▼
#     RendererRegistry
#         │
#         │ renderer class
#         ▼
#     Renderer
#         │
#         │ graphics representation
#         ▼
#     QGraphicsItem
#
#
# Example
# -------
#
#     Bus
#       ↓
#     BusRenderer
#       ↓
#     BusItem
#
#     Line
#       ↓
#     LineRenderer
#       ↓
#     LineItem
#
#
# IMPORTANT ARCHITECTURAL RULES
# -----------------------------
#
# 1. This registry must NOT import individual renderers.
#
# 2. This registry must NOT import Qt.
#
# 3. This registry must NOT modify the core model.
#
# 4. This registry stores renderer IMPLEMENTATIONS, not
#    graphics items.
#
# 5. RenderSystem is responsible for obtaining the renderer
#    and invoking it.
#
# 6. A renderer registration must not silently replace another
#    renderer. Duplicate registration is considered an
#    architectural/configuration error.
#
#
# FUTURE PLUGIN ARCHITECTURE
# --------------------------
#
# The central plugin system lives in:
#
#     ui/core/plugin_registry.py
#
# Renderer plugins can eventually self-register there:
#
#     @register_plugin("renderer", "bus")
#     class BusRenderer:
#         ...
#
# A loader can then populate this runtime registry.
#
# This means RenderSystem does not need to know which renderer
# classes exist.
#
# ============================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type


class RendererRegistry:
    """
    Runtime registry mapping model element classes to renderer
    implementations.

    Example
    -------

        registry.register(Bus, BusRenderer)

        renderer = registry.get_renderer(Bus)

    The registry stores renderer CLASSES.

    Renderer instances are created by the rendering layer when
    required. This prevents renderer lifetime and registration
    concerns from being mixed together.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Create an empty renderer registry.

        Internal mapping:

            ModelClass -> RendererClass
        """

        self._renderers: Dict[
            Type[Any],
            Type[Any],
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        model_type: Type[Any],
        renderer: Type[Any],
    ) -> Type[Any]:
        """
        Register a renderer for a model element type.

        Parameters
        ----------
        model_type:
            Model class handled by the renderer.

            Example:
                Bus

        renderer:
            Renderer class responsible for visualizing the
            model element.

            Example:
                BusRenderer

        Returns
        -------
        Type
            The registered renderer class.

        Raises
        ------
        TypeError
            If model_type or renderer is not a class.

        ValueError
            If a different renderer is already registered for
            the same model type.

        Notes
        -----
        Duplicate registration of the SAME renderer is harmless.

        Duplicate registration of a DIFFERENT renderer is rejected
        because silently replacing a renderer can create difficult
        rendering bugs.
        """

        # ----------------------------------------------------
        # Validate model type
        # ----------------------------------------------------

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a class"
            )

        # ----------------------------------------------------
        # Validate renderer
        # ----------------------------------------------------

        if not isinstance(renderer, type):
            raise TypeError(
                "renderer must be a class"
            )

        # ----------------------------------------------------
        # Check existing registration
        # ----------------------------------------------------

        existing = self._renderers.get(model_type)

        if existing is not None:

            # Registering the exact same renderer again is safe.
            if existing is renderer:
                return renderer

            raise ValueError(
                "Renderer already registered for "
                f"{model_type.__name__}: "
                f"{existing.__name__}"
            )

        # ----------------------------------------------------
        # Register renderer
        # ----------------------------------------------------

        self._renderers[model_type] = renderer

        return renderer

    # ========================================================
    # UNREGISTER
    # ========================================================

    def unregister(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Remove the renderer registered for a model type.

        Returns
        -------
        bool
            True if a renderer was removed.
            False if no renderer was registered.
        """

        if model_type not in self._renderers:
            return False

        del self._renderers[model_type]

        return True

    # ========================================================
    # RENDERER LOOKUP
    # ========================================================

    def get_renderer(
        self,
        model_type: Type[Any],
    ) -> Optional[Type[Any]]:
        """
        Retrieve the renderer class for a model type.

        Lookup order
        ------------
        1. Exact model-type match
        2. Registered base-class match

        Example
        -------

        If:

            ElectricalElement
                ↑
              Bus

        and only ElectricalElement has a renderer, Bus will use
        the ElectricalElement renderer unless Bus has its own
        renderer.

        Returns
        -------
        Type | None
            Renderer class, or None when no renderer exists.
        """

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        renderer = self._renderers.get(model_type)

        if renderer is not None:
            return renderer

        # ----------------------------------------------------
        # Inheritance fallback
        # ----------------------------------------------------
        #
        # Iterate through the Python method-resolution order
        # rather than checking every registered type manually.
        #
        # This gives deterministic base-class lookup.
        # ----------------------------------------------------

        for base_type in getattr(
            model_type,
            "__mro__",
            (),
        ):

            if base_type is model_type:
                continue

            renderer = self._renderers.get(base_type)

            if renderer is not None:
                return renderer

        return None

    # ========================================================
    # REQUIRED LOOKUP
    # ========================================================

    def require_renderer(
        self,
        model_type: Type[Any],
    ) -> Type[Any]:
        """
        Retrieve a renderer and raise an explicit error if none
        is registered.

        This should be used by RenderSystem when absence of a
        renderer represents an invalid UI configuration.
        """

        renderer = self.get_renderer(model_type)

        if renderer is None:
            raise KeyError(
                "No renderer registered for model type "
                f"'{model_type.__name__}'"
            )

        return renderer

    # ========================================================
    # EXISTENCE CHECK
    # ========================================================

    def contains(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Return True when an exact renderer registration exists.

        Note:
        This checks direct registration only. It does not perform
        inheritance fallback.
        """

        return model_type in self._renderers

    # ========================================================
    # LIST REGISTERED MODEL TYPES
    # ========================================================

    def list_model_types(self) -> List[Type[Any]]:
        """
        Return all model classes with directly registered
        renderers.
        """

        return list(self._renderers.keys())

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def list_renderers(self) -> Dict[str, str]:
        """
        Return a human-readable representation of the current
        renderer registry.

        Example result:

            {
                "Bus": "BusRenderer",
                "Line": "LineRenderer"
            }

        This method is intended for diagnostics, logging, and
        development tools.
        """

        return {
            model_type.__name__: renderer.__name__
            for model_type, renderer
            in self._renderers.items()
        }

    # ========================================================
    # ITERATION
    # ========================================================

    def items(self):
        """
        Iterate over registered:

            (model_type, renderer_class)

        pairs.
        """

        return self._renderers.items()

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all renderer registrations.

        Primarily intended for:

            - automated tests
            - development reload
            - controlled application reset

        Normal application execution should generally not call
        this method.
        """

        self._renderers.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(self) -> int:
        """
        Return the number of directly registered renderers.
        """

        return len(self._renderers)

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        renderer_names = ", ".join(
            renderer.__name__
            for renderer in self._renderers.values()
        )

        return (
            "RendererRegistry("
            f"renderers=[{renderer_names}]"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererRegistry",
]
```
