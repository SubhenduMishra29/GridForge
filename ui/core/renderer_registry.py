# ============================================================
# File: ui/core/renderer_registry.py
# GridForge V2 — Renderer Registry
# ============================================================
"""
Central registry for GridForge canvas renderers.

Architecture
------------

    RenderSystem
         │
         ▼
    RendererRegistry
         │
    ┌────┼────────────┐
    ▼    ▼            ▼
   Bus  Line       Future Renderer
 Renderer Renderer

Purpose
-------
RendererRegistry provides the stable lookup boundary between
the canvas rendering system and concrete renderer
implementations.

The registry stores renderer implementations as classes or
factories. It never creates renderer instances.

Responsibilities
----------------
RendererRegistry:

    - register renderer implementations;
    - unregister renderers;
    - resolve renderers by stable ID;
    - resolve renderers by model type;
    - expose renderer registrations;
    - detect duplicate renderer IDs;
    - optionally replace registrations;
    - validate required registrations;
    - provide deterministic diagnostics.

RendererRegistry does NOT:

    - instantiate renderers;
    - create graphics items;
    - create model objects;
    - render objects;
    - own RenderSystem;
    - own QGraphicsScene;
    - perform selection;
    - perform snapping;
    - perform navigation;
    - modify Core state;
    - calculate electrical quantities;
    - decide rendering order;
    - manage renderer lifecycle.

Qt Architecture
---------------
This module intentionally does not import Qt.

Concrete renderers may use ui.core.qt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


# ============================================================
# TYPES
# ============================================================

RendererImplementation = Any


# ============================================================
# RENDERER REGISTRATION
# ============================================================

@dataclass(frozen=True)
class RendererRegistration:
    """
    Immutable registration record for one renderer.
    """

    renderer_id: str
    renderer: RendererImplementation
    model_type: Optional[type] = None
    priority: int = 0
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.renderer_id, str):
            raise TypeError(
                "renderer_id must be a string."
            )

        normalized_id = self.renderer_id.strip()

        if not normalized_id:
            raise ValueError(
                "renderer_id must not be empty."
            )

        if self.renderer is None:
            raise ValueError(
                "renderer must not be None."
            )

        if self.model_type is not None and not isinstance(
            self.model_type,
            type,
        ):
            raise TypeError(
                "model_type must be a type or None."
            )

        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
        ):
            raise TypeError(
                "priority must be an integer."
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError(
                "metadata must be a mapping."
            )


# ============================================================
# RENDERER REGISTRY
# ============================================================

class RendererRegistry:
    """
    Central registry for GridForge renderer implementations.

    Canonical RenderSystem lookup contract:

        registry.get_renderer(type(element))

    ID-based lookup remains available through:

        registry.get(renderer_id)
        registry.require(renderer_id)

    The registry never instantiates renderer implementations.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        self._registrations: dict[
            str,
            RendererRegistration,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        renderer_id: str,
        renderer: RendererImplementation,
        *,
        model_type: Optional[type] = None,
        priority: int = 0,
        metadata: Optional[Mapping[str, Any]] = None,
        replace: bool = False,
    ) -> RendererRegistration:
        """
        Register a renderer implementation.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        if (
            normalized_id in self._registrations
            and not replace
        ):
            raise ValueError(
                "Renderer already registered: "
                f"{normalized_id!r}"
            )

        if metadata is None:
            metadata = {}

        registration = RendererRegistration(
            renderer_id=normalized_id,
            renderer=renderer,
            model_type=model_type,
            priority=priority,
            metadata=dict(metadata),
        )

        self._registrations[
            normalized_id
        ] = registration

        return registration

    # --------------------------------------------------------

    def register_renderer(
        self,
        registration: RendererRegistration,
        *,
        replace: bool = False,
    ) -> RendererRegistration:
        """
        Register an explicit RendererRegistration.
        """

        if not isinstance(
            registration,
            RendererRegistration,
        ):
            raise TypeError(
                "registration must be a RendererRegistration."
            )

        return self.register(
            registration.renderer_id,
            registration.renderer,
            model_type=registration.model_type,
            priority=registration.priority,
            metadata=registration.metadata,
            replace=replace,
        )

    # ========================================================
    # UNREGISTRATION
    # ========================================================

    def unregister(
        self,
        renderer_id: str,
    ) -> Optional[RendererRegistration]:
        """
        Remove a renderer registration.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        return self._registrations.pop(
            normalized_id,
            None,
        )

    # --------------------------------------------------------

    def unregister_renderer(
        self,
        renderer_id: str,
    ) -> Optional[RendererRegistration]:
        """
        Alias for unregister().
        """

        return self.unregister(
            renderer_id
        )

    # ========================================================
    # ID LOOKUP
    # ========================================================

    def get(
        self,
        renderer_id: str,
    ) -> Optional[RendererRegistration]:
        """
        Return a registration by renderer ID.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        return self._registrations.get(
            normalized_id
        )

    # --------------------------------------------------------

    def get_by_id(
        self,
        renderer_id: str,
    ) -> Optional[RendererRegistration]:
        """
        Explicit alias for ID-based registration lookup.
        """

        return self.get(
            renderer_id
        )

    # --------------------------------------------------------

    def require(
        self,
        renderer_id: str,
    ) -> RendererRegistration:
        """
        Return a registration or raise KeyError.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        try:
            return self._registrations[
                normalized_id
            ]
        except KeyError as exc:
            raise KeyError(
                "Renderer is not registered: "
                f"{normalized_id!r}"
            ) from exc

    # --------------------------------------------------------

    def require_renderer_by_id(
        self,
        renderer_id: str,
    ) -> RendererImplementation:
        """
        Return a renderer implementation by ID.
        """

        return self.require(
            renderer_id
        ).renderer

    # ========================================================
    # CANONICAL RENDERER RESOLUTION
    # ========================================================

    def get_renderer(
        self,
        model_type: type,
    ) -> Optional[RendererImplementation]:
        """
        Resolve the renderer implementation for a model type.

        This is the canonical RenderSystem contract:

            registry.get_renderer(type(element))

        Resolution order:

            1. exact model-type match;
            2. compatible base-class match;
            3. highest priority;
            4. registration order.
        """

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a type."
            )

        exact_matches = [
            registration
            for registration in self._registrations.values()
            if registration.model_type is model_type
        ]

        if exact_matches:
            return self._select_best(
                exact_matches
            ).renderer

        compatible_matches = [
            registration
            for registration in self._registrations.values()
            if (
                registration.model_type is not None
                and issubclass(
                    model_type,
                    registration.model_type,
                )
            )
        ]

        if not compatible_matches:
            return None

        return self._select_best(
            compatible_matches
        ).renderer

    # --------------------------------------------------------

    def get_for_type(
        self,
        model_type: type,
    ) -> Optional[RendererImplementation]:
        """
        Compatibility alias for model-type resolution.
        """

        return self.get_renderer(
            model_type
        )

    # --------------------------------------------------------

    def get_for_object(
        self,
        model_object: Any,
    ) -> Optional[RendererImplementation]:
        """
        Resolve a renderer for a concrete model object.
        """

        if model_object is None:
            return None

        return self.get_renderer(
            type(model_object)
        )

    # --------------------------------------------------------

    def require_for_type(
        self,
        model_type: type,
    ) -> RendererImplementation:
        """
        Resolve a renderer or raise KeyError.
        """

        renderer = self.get_renderer(
            model_type
        )

        if renderer is None:
            raise KeyError(
                "No renderer registered for model type "
                f"{model_type!r}."
            )

        return renderer

    # --------------------------------------------------------

    def require_for_object(
        self,
        model_object: Any,
    ) -> RendererImplementation:
        """
        Resolve a renderer for an object or raise KeyError.
        """

        if model_object is None:
            raise ValueError(
                "model_object must not be None."
            )

        return self.require_for_type(
            type(model_object)
        )

    # ========================================================
    # REQUIRED REGISTRATIONS
    # ========================================================

    def require_renderers(
        self,
        renderer_ids: Any,
    ) -> tuple[RendererRegistration, ...]:
        """
        Require all supplied renderer IDs to exist.

        Returns registrations in the requested order.
        """

        if renderer_ids is None:
            raise ValueError(
                "renderer_ids must not be None."
            )

        registrations = []

        for renderer_id in renderer_ids:
            registrations.append(
                self.require(
                    renderer_id
                )
            )

        return tuple(
            registrations
        )

    # ========================================================
    # REGISTRATION QUERIES
    # ========================================================

    def get_registrations_for_type(
        self,
        model_type: type,
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Return all compatible registrations.

        Results are ordered by descending priority and then
        original registration order.
        """

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a type."
            )

        matches = [
            registration
            for registration in self._registrations.values()
            if (
                registration.model_type is not None
                and (
                    registration.model_type is model_type
                    or issubclass(
                        model_type,
                        registration.model_type,
                    )
                )
            )
        ]

        return self._sort_registrations(
            matches
        )

    # ========================================================
    # REGISTRATION ACCESS
    # ========================================================

    def get_renderer_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return renderer IDs in registration order.
        """

        return tuple(
            self._registrations.keys()
        )

    @property
    def renderer_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Read-only renderer ID collection.
        """

        return self.get_renderer_ids()

    # --------------------------------------------------------

    def get_registrations(
        self,
    ) -> tuple[RendererRegistration, ...]:
        """
        Return all registrations in registration order.
        """

        return tuple(
            self._registrations.values()
        )

    # --------------------------------------------------------

    def values(
        self,
    ) -> tuple[RendererRegistration, ...]:
        """
        Return all registrations.
        """

        return self.get_registrations()

    # --------------------------------------------------------

    def items(
        self,
    ) -> tuple[
        tuple[str, RendererRegistration],
        ...,
    ]:
        """
        Return renderer ID/registration pairs.
        """

        return tuple(
            self._registrations.items()
        )

    # ========================================================
    # CONTAINS
    # ========================================================

    def contains(
        self,
        renderer_id: str,
    ) -> bool:
        """
        Return True when renderer_id is registered.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        return normalized_id in self._registrations

    def has(
        self,
        renderer_id: str,
    ) -> bool:
        """
        Alias for contains().
        """

        return self.contains(
            renderer_id
        )

    def __contains__(
        self,
        renderer_id: str,
    ) -> bool:
        return self.contains(
            renderer_id
        )

    def __len__(
        self,
    ) -> int:
        return len(
            self._registrations
        )

    # ========================================================
    # PRIORITY
    # ========================================================

    def get_by_priority(
        self,
        priority: int,
    ) -> tuple[RendererRegistration, ...]:
        """
        Return registrations having the specified priority.
        """

        if (
            isinstance(priority, bool)
            or not isinstance(priority, int)
        ):
            raise TypeError(
                "priority must be an integer."
            )

        return tuple(
            registration
            for registration in self._registrations.values()
            if registration.priority == priority
        )

    # ========================================================
    # REPLACEMENT
    # ========================================================

    def replace(
        self,
        renderer_id: str,
        renderer: RendererImplementation,
        *,
        model_type: Optional[type] = None,
        priority: int = 0,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> RendererRegistration:
        """
        Replace an existing renderer registration.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        if normalized_id not in self._registrations:
            raise KeyError(
                "Renderer is not registered: "
                f"{normalized_id!r}"
            )

        return self.register(
            normalized_id,
            renderer,
            model_type=model_type,
            priority=priority,
            metadata=metadata,
            replace=True,
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> tuple[RendererRegistration, ...]:
        """
        Remove all registrations.
        """

        registrations = self.get_registrations()

        self._registrations.clear()

        return registrations

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[str, RendererRegistration]:
        """
        Return a shallow registry snapshot.
        """

        return dict(
            self._registrations
        )

    # ========================================================
    # INTERNAL RESOLUTION
    # ========================================================

    @staticmethod
    def _sort_registrations(
        registrations: list[RendererRegistration],
    ) -> tuple[RendererRegistration, ...]:
        """
        Sort registrations by descending priority.

        Python's stable sorting preserves registration order
        for equal priorities.
        """

        return tuple(
            sorted(
                registrations,
                key=lambda registration: (
                    -registration.priority,
                ),
            )
        )

    @classmethod
    def _select_best(
        cls,
        registrations: list[RendererRegistration],
    ) -> RendererRegistration:
        """
        Select the highest-priority registration.
        """

        if not registrations:
            raise ValueError(
                "registrations must not be empty."
            )

        return cls._sort_registrations(
            registrations
        )[0]

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _normalize_id(
        renderer_id: str,
    ) -> str:
        """
        Validate and normalize a renderer ID.
        """

        if not isinstance(renderer_id, str):
            raise TypeError(
                "renderer_id must be a string."
            )

        normalized = renderer_id.strip()

        if not normalized:
            raise ValueError(
                "renderer_id must not be empty."
            )

        return normalized

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic registry state.
        """

        model_type_count = sum(
            registration.model_type is not None
            for registration in self._registrations.values()
        )

        return {
            "count": len(self._registrations),
            "renderer_ids": self.renderer_ids,
            "model_type_registrations": model_type_count,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return (
            "RendererRegistry("
            f"count={len(self)}, "
            f"renderers={self.renderer_ids!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererRegistration",
    "RendererRegistry",
]
