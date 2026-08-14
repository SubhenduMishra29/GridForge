# ============================================================
# File: ui/renderers/renderer_loader.py
# GridForge V2 — Renderer Loader
# ============================================================
"""
Explicit renderer loading for GridForge V2.

Architecture
------------

    Application Bootstrap
            │
            ▼
      RendererLoader
            │
            ▼
      RendererRegistry
            │
            ▼
      Concrete Renderers
            │
            ▼
        GridScene

Purpose
-------
RendererLoader provides the explicit import/registration
boundary for concrete renderer implementations.

The renderer registry intentionally does not discover or import
concrete renderer modules automatically.

Therefore application bootstrap must explicitly invoke this
loader.

Current concrete renderers
--------------------------

    BusRenderer
    LineRenderer

The loader registers those renderers with the supplied
RendererRegistry.

Important architectural rule
----------------------------
This module performs registration only.

It does NOT:

    - create a QGraphicsScene;
    - create graphics items;
    - render model objects;
    - modify Core state;
    - implement tool behavior;
    - implement selection;
    - perform snapping;
    - perform navigation;
    - perform electrical calculations.

Renderer lifecycle remains owned by the application/UI
composition layer.

Qt Architecture
---------------
This module does not import Qt directly.

Concrete renderer modules are responsible for importing Qt
through:

    ui.core.qt
"""

from __future__ import annotations

from typing import Any

from ui.renderers.bus_renderer import BusRenderer
from ui.renderers.line_renderer import LineRenderer


class RendererLoader:
    """
    Explicit loader for GridForge concrete renderers.

    The loader does not own the registry.

    It simply registers the known renderer implementations with
    the registry supplied by application bootstrap.
    """

    # ========================================================
    # CONCRETE RENDERERS
    # ========================================================

    RENDERERS = (
        BusRenderer,
        LineRenderer,
    )

    # ========================================================
    # LOAD
    # ========================================================

    @classmethod
    def load(
        cls,
        registry: Any,
    ) -> Any:
        """
        Register all concrete GridForge renderers.

        Parameters
        ----------
        registry:
            GridForge RendererRegistry instance.

        Returns
        -------
        registry
            The same registry supplied by the caller.

        Notes
        -----
        The registry remains responsible for validating the
        registration contract.
        """

        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        register = getattr(
            registry,
            "register",
            None,
        )

        if not callable(register):
            raise TypeError(
                "registry must provide register()."
            )

        for renderer_class in cls.RENDERERS:
            cls._register(
                registry,
                renderer_class,
            )

        return registry

    # ========================================================
    # REGISTER ONE
    # ========================================================

    @classmethod
    def _register(
        cls,
        registry: Any,
        renderer_class: type,
    ) -> None:
        """
        Register one renderer class.

        RendererRegistry owns the exact registration semantics.
        """

        register = registry.register

        renderer_name = cls._renderer_name(
            renderer_class
        )

        # ----------------------------------------------------
        # Preferred registration contract:
        #
        #     registry.register(name, renderer_class)
        #
        # This keeps renderer identity explicit and avoids
        # relying on Python class names inside the registry.
        # ----------------------------------------------------

        try:
            register(
                renderer_name,
                renderer_class,
            )
            return

        except TypeError:
            # ------------------------------------------------
            # Compatibility with a registry whose canonical
            # contract accepts only the renderer class.
            #
            # This fallback does not change ownership or
            # discovery semantics.
            # ------------------------------------------------

            register(
                renderer_class
            )

    # ========================================================
    # NAME
    # ========================================================

    @staticmethod
    def _renderer_name(
        renderer_class: type,
    ) -> str:
        """
        Return the stable registry name for a renderer class.

        The explicit names are intentionally lower-case and
        domain-oriented.
        """

        if renderer_class is BusRenderer:
            return "bus"

        if renderer_class is LineRenderer:
            return "line"

        raise ValueError(
            "Unknown GridForge renderer class: "
            f"{renderer_class!r}"
        )

    # ========================================================
    # INDIVIDUAL LOADERS
    # ========================================================

    @classmethod
    def load_bus_renderer(
        cls,
        registry: Any,
    ) -> Any:
        """
        Explicitly register BusRenderer.
        """

        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        cls._register(
            registry,
            BusRenderer,
        )

        return registry

    # --------------------------------------------------------

    @classmethod
    def load_line_renderer(
        cls,
        registry: Any,
    ) -> Any:
        """
        Explicitly register LineRenderer.
        """

        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        cls._register(
            registry,
            LineRenderer,
        )

        return registry

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    @classmethod
    def renderer_classes(
        cls,
    ) -> tuple[type, ...]:
        """
        Return the concrete renderer classes known to the
        explicit loader.

        The returned tuple is immutable.
        """

        return tuple(
            cls.RENDERERS
        )


# ============================================================
# MODULE-LEVEL EXPLICIT LOAD FUNCTION
# ============================================================

def load_renderers(
    registry: Any,
) -> Any:
    """
    Explicitly load all GridForge concrete renderers.

    This convenience function is the preferred bootstrap entry
    point when the application does not need direct access to
    RendererLoader.
    """

    return RendererLoader.load(
        registry
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererLoader",
    "load_renderers",
]
