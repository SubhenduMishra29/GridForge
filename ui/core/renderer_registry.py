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

The registry stores renderer implementations as classes/factories
rather than scene-bound renderer instances.

This is important because renderers are Canvas/Scene specific:

    Renderer Class
          │
          ▼
    RenderSystem / Canvas Context
          │
          ▼
    Renderer Instance
          │
          ▼
      Graphics Scene

The registry therefore remains independent of any particular
QGraphicsScene or Canvas instance.

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
    - decide whether an object should be rendered;
    - manage renderer lifecycle.

Renderer Ownership
------------------
The registry stores renderer implementations only.

It does not create or destroy renderer instances.

Therefore:

    registry.register(
        "bus",
        BusRenderer,
        model_type=Bus,
    )

does NOT instantiate BusRenderer.

RenderSystem or the owning Canvas composition layer remains
responsible for creating a renderer instance with the appropriate
scene/context.

Model Dependency
----------------
RendererRegistry may store a model type as metadata.

It does not import Core model classes itself.

The caller supplies model_type explicitly.

This keeps the registry independent of the concrete Core model
hierarchy and prevents dependency inversion problems.

Renderer Resolution
-------------------
A renderer can be registered with:

    renderer_id
    renderer
    model_type

where renderer is normally a renderer class or factory.

The model_type association allows RenderSystem to resolve a
renderer implementation from an authoritative Core model
object without hard-coding concrete renderer imports.

Example:

    registry.register(
        "bus",
        BusRenderer,
        model_type=Bus,
    )

    renderer_class = registry.get_for_object(bus)

The registry performs only lookup.

Rendering policy and renderer instantiation remain outside the
registry.

Qt Architecture
---------------
This module intentionally does not import Qt.

Concrete renderers may use ui.core.qt.

No direct PySide6/PyQt imports are permitted in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional


# ============================================================
# RENDERER IMPLEMENTATION TYPE
# ============================================================

RendererImplementation = Any


# ============================================================
# RENDERER REGISTRATION
# ============================================================


@dataclass(frozen=True)
class RendererRegistration:
    """
    Immutable registration record for one renderer.

    Parameters
    ----------
    renderer_id:
        Stable renderer identifier.

    renderer:
        Renderer implementation.

        Normally this is a renderer class. A callable factory
        may also be supplied when explicitly required by the
        rendering infrastructure.

        The registry never invokes this implementation.

    model_type:
        Optional model class/type handled by this renderer.

        The registry treats this as an opaque lookup key.

    priority:
        Resolution priority.

        Higher values are preferred when multiple registrations
        match the same model type.

    metadata:
        Additional renderer metadata.

    Notes
    -----
    The registration stores an implementation, not a
    scene-bound renderer instance.

    This keeps the registry reusable across multiple Canvas
    instances.
    """

    renderer_id: str
    renderer: RendererImplementation

    model_type: Optional[type] = None

    priority: int = 0

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate registration data.
        """

        if not isinstance(
            self.renderer_id,
            str,
        ):
            raise TypeError(
                "renderer_id must be a string."
            )

        renderer_id = self.renderer_id.strip()

        if not renderer_id:
            raise ValueError(
                "renderer_id must not be empty."
            )

        if self.renderer is None:
            raise ValueError(
                "renderer must not be None."
            )

        if self.model_type is not None:
            if not isinstance(
                self.model_type,
                type,
            ):
                raise TypeError(
                    "model_type must be a type or None."
                )

        if isinstance(
            self.priority,
            bool,
        ) or not isinstance(
            self.priority,
            int,
        ):
            raise TypeError(
                "priority must be an integer."
            )

        if self.metadata is None:
            raise ValueError(
                "metadata must not be None."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping."
            )


# ============================================================
# RENDERER REGISTRY
# ============================================================


class RendererRegistry:
    """
    Central registry for GridForge renderer implementations.

    RendererRegistry is deliberately independent of:

        - Qt;
        - QGraphicsScene;
        - RenderSystem;
        - concrete Core models;
        - renderer instances.

    It is a registration and resolution service only.

    The registry stores renderer implementations and never
    creates scene-bound renderer instances.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty renderer registry.
        """

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
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
        replace: bool = False,
    ) -> RendererRegistration:
        """
        Register a renderer implementation.

        Parameters
        ----------
        renderer_id:
            Stable renderer identifier.

        renderer:
            Renderer implementation.

            Normally a renderer class. A callable factory is
            also accepted.

            The registry stores this implementation and never
            invokes it.

        model_type:
            Optional model type handled by the renderer.

        priority:
            Resolution priority for model-type lookup.

        metadata:
            Optional additional renderer metadata.

        replace:
            Replace an existing registration when True.

        Returns
        -------
        RendererRegistration
            The resulting registration.

        Raises
        ------
        ValueError
            If renderer_id is already registered and
            replace=False.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        if renderer is None:
            raise ValueError(
                "renderer must not be None."
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

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping."
            )

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
                "registration must be a "
                "RendererRegistration."
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

        No renderer instance is created or destroyed.
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
        Return a renderer registration by ID.

        Returns None when no registration exists.
        """

        normalized_id = self._normalize_id(
            renderer_id
        )

        return self._registrations.get(
            normalized_id
        )

    # --------------------------------------------------------

    def get_renderer(
        self,
        renderer_id: str,
    ) -> Optional[RendererImplementation]:
        """
        Return a renderer implementation by ID.

        No renderer instance is created.
        """

        registration = self.get(
            renderer_id
        )

        if registration is None:
            return None

        return registration.renderer

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

    def require_renderer(
        self,
        renderer_id: str,
    ) -> RendererImplementation:
        """
        Return a renderer implementation or raise KeyError.

        No renderer instance is created.
        """

        return self.require(
            renderer_id
        ).renderer

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

        return (
            normalized_id
            in self._registrations
        )

    # --------------------------------------------------------

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

    # --------------------------------------------------------

    def __contains__(
        self,
        renderer_id: str,
    ) -> bool:
        """
        Support:

            "bus" in registry
        """

        return self.contains(
            renderer_id
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return number of registered renderers.
        """

        return len(
            self._registrations
        )

    # ========================================================
    # MODEL-TYPE RESOLUTION
    # ========================================================

    def get_for_type(
        self,
        model_type: type,
    ) -> Optional[RendererImplementation]:
        """
        Resolve the highest-priority renderer implementation
        for model_type.

        Exact type matches are preferred over base-class matches.

        Resolution order:

            1. exact model_type match;
            2. compatible base-class match;
            3. highest priority;
            4. registration order as deterministic tie-breaker.

        Returns
        -------
        object | None
            Registered renderer implementation.
        """

        if not isinstance(
            model_type,
            type,
        ):
            raise TypeError(
                "model_type must be a type."
            )

        exact_matches = [
            registration
            for registration
            in self._registrations.values()
            if registration.model_type
            is model_type
        ]

        if exact_matches:
            return self._select_best(
                exact_matches
            ).renderer

        compatible_matches = [
            registration
            for registration
            in self._registrations.values()
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

    def get_for_object(
        self,
        model_object: Any,
    ) -> Optional[RendererImplementation]:
        """
        Resolve a renderer implementation for a concrete
        model object.

        The object's concrete Python type is used for lookup.

        Returns None when no compatible renderer is registered.
        """

        if model_object is None:
            return None

        return self.get_for_type(
            type(model_object)
        )

    # --------------------------------------------------------

    def require_for_type(
        self,
        model_type: type,
    ) -> RendererImplementation:
        """
        Resolve a renderer implementation for a model type or
        raise KeyError.
        """

        renderer = self.get_for_type(
            model_type
        )

        if renderer is None:
            raise KeyError(
                "No renderer registered for "
                f"model type {model_type!r}."
            )

        return renderer

    # --------------------------------------------------------

    def require_for_object(
        self,
        model_object: Any,
    ) -> RendererImplementation:
        """
        Resolve a renderer implementation for a model object
        or raise KeyError.
        """

        if model_object is None:
            raise ValueError(
                "model_object must not be None."
            )

        return self.require_for_type(
            type(model_object)
        )

    # ========================================================
    # MODEL-TYPE REGISTRATION QUERIES
    # ========================================================

    def get_registrations_for_type(
        self,
        model_type: type,
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Return all registrations compatible with model_type.

        Results are ordered by descending priority and then
        registration order.
        """

        if not isinstance(
            model_type,
            type,
        ):
            raise TypeError(
                "model_type must be a type."
            )

        matches = [
            registration
            for registration
            in self._registrations.values()
            if (
                registration.model_type is not None
                and (
                    registration.model_type
                    is model_type
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

    # --------------------------------------------------------

    @property
    def renderer_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Read-only convenience property.
        """

        return self.get_renderer_ids()

    # --------------------------------------------------------

    def get_registrations(
        self,
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Return all registrations in registration order.
        """

        return tuple(
            self._registrations.values()
        )

    # --------------------------------------------------------

    def values(
        self,
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Return all renderer registrations.
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
    # FILTERING
    # ========================================================

    def get_by_priority(
        self,
        priority: int,
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Return renderers having the specified priority.
        """

        if isinstance(
            priority,
            bool,
        ) or not isinstance(
            priority,
            int,
        ):
            raise TypeError(
                "priority must be an integer."
            )

        return tuple(
            registration
            for registration
            in self._registrations.values()
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
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> RendererRegistration:
        """
        Replace an existing renderer registration.

        No renderer instance is created or destroyed.
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
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Remove all renderer registrations.

        No renderer instances are created or destroyed.
        """

        registrations = self.get_registrations()

        self._registrations.clear()

        return registrations

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[
        str,
        RendererRegistration,
    ]:
        """
        Return a shallow registry snapshot.

        The returned dictionary does not permit mutation of the
        registry itself.
        """

        return dict(
            self._registrations
        )

    # ========================================================
    # INTERNAL RESOLUTION
    # ========================================================

    @staticmethod
    def _sort_registrations(
        registrations: list[
            RendererRegistration
        ],
    ) -> tuple[
        RendererRegistration,
        ...,
    ]:
        """
        Sort registrations deterministically.

        Higher priority is preferred.

        Python's stable sorting preserves original registration
        order for equal priorities.
        """

        return tuple(
            sorted(
                registrations,
                key=lambda registration: (
                    -registration.priority,
                ),
            )
        )

    # --------------------------------------------------------

    @classmethod
    def _select_best(
        cls,
        registrations: list[
            RendererRegistration
        ],
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
        Validate and normalize renderer identifier.
        """

        if not isinstance(
            renderer_id,
            str,
        ):
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
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic registry snapshot.
        """

        model_type_count = sum(
            registration.model_type is not None
            for registration
            in self._registrations.values()
        )

        return {
            "count": len(
                self._registrations
            ),
            "renderer_ids": (
                self.get_renderer_ids()
            ),
            "model_type_registrations": (
                model_type_count
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
            "RendererRegistry("
            f"count={len(self)}, "
            f"renderers="
            f"{self.get_renderer_ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererRegistration",
    "RendererRegistry",
]
