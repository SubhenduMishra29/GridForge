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
canonical GridForge renderer set.

Current renderer set:

    - BusRenderer
    - LineRenderer

The loader explicitly imports concrete renderer
implementations and authoritative Core model types.

No dynamic discovery is performed.

No filesystem scanning is performed.

No package introspection is performed.

No renderer instances are created here.

RendererLoader only performs deterministic registration.

Responsibilities
----------------

RendererLoader:

    - explicitly imports concrete renderers;
    - explicitly imports authoritative model types;
    - registers renderer/model-type associations;
    - validates the canonical renderer set;
    - provides deterministic bootstrap state.

RendererLoader does NOT:

    - instantiate renderers;
    - render graphics;
    - create QGraphicsItems;
    - own RenderSystem;
    - own QGraphicsScene;
    - manage renderer lifecycle;
    - modify Core state;
    - perform electrical calculations;
    - perform selection;
    - perform snapping;
    - perform navigation;
    - discover renderers dynamically.

Registration ownership
----------------------

RendererLoader
    = explicit composition / registration

RendererRegistry
    = registration storage / renderer resolution

RenderSystem
    = rendering lifecycle / graphical projection

Qt architecture
---------------

This module contains no Qt imports.
"""

from __future__ import annotations

from typing import Any

from ui.core.renderer_registry import RendererRegistry


class RendererLoader:
    """
    Explicit loader for the canonical GridForge V2 renderer set.

    RendererLoader owns knowledge of the concrete renderer set,
    but does not own renderer instances.
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
        """
        Initialize the renderer loader.
        """

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
    # EXPLICIT CANONICAL DEFINITION
    # ========================================================

    @staticmethod
    def _load_canonical_definitions() -> tuple[
        tuple[
            str,
            Any,
            type,
        ],
        ...,
    ]:
        """
        Import and return the canonical renderer definitions.

        Each entry contains:

            (renderer_id, renderer_implementation, model_type)

        Imports are deliberately local so importing this loader
        does not eagerly import concrete renderers.
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

        return (
            (
                RendererLoader.BUS_RENDERER_ID,
                BusRenderer,
                Bus,
            ),
            (
                RendererLoader.LINE_RENDERER_ID,
                LineRenderer,
                Line,
            ),
        )

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

        Registration is performed only after every canonical
        renderer definition has been successfully imported.
        """

        if not isinstance(
            replace,
            bool,
        ):
            raise TypeError(
                "replace must be a bool."
            )

        definitions = (
            self._load_canonical_definitions()
        )

        # ----------------------------------------------------
        # Preflight validation.
        #
        # All imports and canonical definitions must succeed
        # before registry mutation begins.
        # ----------------------------------------------------

        for (
            renderer_id,
            renderer,
            model_type,
        ) in definitions:

            if not isinstance(
                renderer_id,
                str,
            ):
                raise TypeError(
                    "Canonical renderer ID must be a string."
                )

            if renderer is None:
                raise ValueError(
                    "Canonical renderer implementation "
                    "must not be None."
                )

            if not isinstance(
                model_type,
                type,
            ):
                raise TypeError(
                    "Canonical renderer model_type "
                    "must be a type."
                )

            if (
                not replace
                and self.registry.contains(
                    renderer_id
                )
            ):
                raise ValueError(
                    "Renderer already registered: "
                    f"{renderer_id!r}"
                )

        # ----------------------------------------------------
        # Registration.
        #
        # At this point all imports and canonical definitions
        # have passed validation.
        # ----------------------------------------------------

        for (
            renderer_id,
            renderer,
            model_type,
        ) in definitions:

            self.registry.register(
                renderer_id,
                renderer,
                model_type=model_type,
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
        Validate the complete canonical renderer set.

        Validation checks:

            1. required renderer IDs exist;
            2. renderer implementation is canonical;
            3. model type is canonical.
        """

        definitions = (
            self._load_canonical_definitions()
        )

        registrations = self.registry.require_renderers(
            self.REQUIRED_RENDERER_IDS
        )

        expected = {
            renderer_id: (
                renderer,
                model_type,
            )
            for (
                renderer_id,
                renderer,
                model_type,
            ) in definitions
        }

        for registration in registrations:

            expected_renderer, expected_model_type = (
                expected[
                    registration.renderer_id
                ]
            )

            if registration.renderer is not expected_renderer:
                raise TypeError(
                    "Renderer registration "
                    f"{registration.renderer_id!r} does not "
                    "match the canonical renderer."
                )

            if registration.model_type is not expected_model_type:
                raise TypeError(
                    "Renderer registration "
                    f"{registration.renderer_id!r} has an "
                    "incorrect model_type."
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
        Load and validate the complete canonical renderer set.
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
        Return True after successful registration.
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
        Return the target RendererRegistry.
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
        Return the canonical renderer IDs expected by V2.
        """

        return cls.REQUIRED_RENDERER_IDS

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of loader state.
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
        """
        Return a concise diagnostic representation.
        """

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
