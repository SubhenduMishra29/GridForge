# ============================================================
# File: ui/core/renderer_loader.py
# GridForge V2 — Renderer Loader
# ============================================================
"""
Explicit renderer registration loader for GridForge V2.

Architecture
------------

    UI Composition / Bootstrap
              │
              ▼
       RendererLoader
              │
              ▼
       RendererRegistry
              │
              ▼
       RenderSystem
              │
              ▼
      Concrete Renderers

Purpose
-------
RendererLoader is the explicit composition boundary for the
concrete GridForge renderer set.

Current renderer set:

    - BusRenderer
    - LineRenderer

No dynamic discovery is performed.

No filesystem scanning is performed.

No renderer instances are created here.

RendererLoader only imports concrete renderer classes and
registers them with RendererRegistry.
"""

from __future__ import annotations

from typing import Any

from ui.core.renderer_registry import RendererRegistry


class RendererLoader:
    """
    Explicit loader for the GridForge V2 renderer set.

    The loader owns renderer registration knowledge but does not
    own renderer instances.
    """

    # ========================================================
    # CANONICAL RENDERER IDS
    # ========================================================

    BUS_RENDERER_ID = "bus"
    LINE_RENDERER_ID = "line"

    REQUIRED_RENDERER_IDS = (
        BUS_RENDERER_ID,
        LINE_RENDERER_ID,
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        registry: RendererRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        if not isinstance(
            registry,
            RendererRegistry,
        ):
            raise TypeError(
                "registry must be a RendererRegistry."
            )

        self.registry = registry
        self._loaded = False

    # ========================================================
    # EXPLICIT LOADING
    # ========================================================

    def load(
        self,
        *,
        replace: bool = False,
    ) -> None:
        """
        Explicitly import and register the canonical renderers.

        Model classes are imported here as part of the explicit
        composition boundary so the registry can resolve renderers
        from authoritative model types.
        """

        from ui.renderers.bus_renderer import (
            BusRenderer,
        )

        from ui.renderers.line_renderer import (
            LineRenderer,
        )

        from core.model.bus import (
            Bus,
        )

        from core.model.line import (
            Line,
        )

        self.registry.register(
            self.BUS_RENDERER_ID,
            BusRenderer,
            model_type=Bus,
            replace=replace,
        )

        self.registry.register(
            self.LINE_RENDERER_ID,
            LineRenderer,
            model_type=Line,
            replace=replace,
        )

        self._loaded = True

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate that all canonical renderer registrations exist.
        """

        self.registry.require_renderers(
            self.REQUIRED_RENDERER_IDS
        )

    # ========================================================
    # LOAD + VALIDATE
    # ========================================================

    def load_and_validate(
        self,
        *,
        replace: bool = False,
    ) -> None:
        """
        Load and validate the complete renderer set.
        """

        self.load(
            replace=replace
        )

        self.validate()

    # ========================================================
    # STATUS
    # ========================================================

    @property
    def loaded(
        self,
    ) -> bool:
        """
        Return True after successful loading.
        """

        return self._loaded

    # --------------------------------------------------------

    def is_loaded(
        self,
    ) -> bool:
        """
        Semantic alias for loaded.
        """

        return self._loaded

    # ========================================================
    # REGISTRY ACCESS
    # ========================================================

    def get_registry(
        self,
    ) -> RendererRegistry:
        """
        Return the target registry.
        """

        return self.registry

    # ========================================================
    # REQUIRED IDS
    # ========================================================

    @classmethod
    def required_renderer_ids(
        cls,
    ) -> tuple[str, ...]:
        """
        Return canonical renderer IDs.
        """

        return cls.REQUIRED_RENDERER_IDS

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic loader state.
        """

        return {
            "loaded": self._loaded,
            "required_renderer_ids": (
                self.REQUIRED_RENDERER_IDS
            ),
            "registered_renderer_ids": (
                self.registry.renderer_ids
            ),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return (
            "RendererLoader("
            f"loaded={self._loaded}, "
            f"renderers={self.registry.renderer_ids!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererLoader",
]
