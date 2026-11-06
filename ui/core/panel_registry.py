# ============================================================
# File: ui/core/panel_registry.py
# GridForge V2 — Panel Registry
# ============================================================
"""
Central registry for GridForge UI panels.

Architecture
------------

    MainWindow / Plugins
             │
             ▼
       PanelRegistry
             │
       ┌─────┴─────┐
       ▼           ▼
    Panel ID    Panel Instance
                    │
                    ▼
              MainWindow / UI

Purpose
-------
PanelRegistry provides the central registration and lookup
boundary for application panels.

The registry stores panel metadata and panel instances, but
does not own the panel implementation or decide application
layout.

Responsibilities
----------------
PanelRegistry:

    - register panel definitions;
    - unregister panels;
    - resolve panels by ID;
    - expose registered panel IDs;
    - store panel metadata;
    - associate panel instances with panel IDs;
    - detect duplicate registrations;
    - provide diagnostics.

PanelRegistry does NOT:

    - create concrete panel classes;
    - instantiate Qt widgets;
    - arrange panels;
    - manage docking;
    - show or hide panels;
    - own MainWindow;
    - implement panel behavior;
    - subscribe to application events;
    - modify Core state;
    - perform model operations;
    - manage plugins;
    - decide which panels should exist.

Panel ownership
---------------
Concrete panel ownership belongs to the component that creates
and manages the panel.

PanelRegistry is a registry, not a lifecycle manager.

Therefore:

    registry.register(...)
        ≠
    registry creates panel

and:

    registry.unregister(...)
        ≠
    registry destroys panel

Panel IDs
---------
Panel IDs are stable application-level identifiers.

Examples:

    "properties"
    "project"
    "inspector"
    "toolbox"
    "results"
    "log"

The registry does not impose a fixed panel list. Concrete
plugins may register panels during application composition.

Metadata
--------
A panel registration may contain:

    panel_id
    panel
    title
    area
    visible
    closable
    metadata

The registry treats metadata as UI composition information and
does not interpret layout policy.

Qt Architecture
---------------
This module intentionally does not import Qt classes.

Panels themselves may use ui.core.qt.

No direct PySide6/PyQt imports are permitted anywhere in the
GridForge UI architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


# ============================================================
# PANEL REGISTRATION
# ============================================================


@dataclass(frozen=True)
class PanelRegistration:
    """
    Immutable registration record for one UI panel.

    Parameters
    ----------
    panel_id:
        Stable application-level panel identifier.

    panel:
        Concrete panel instance.

    title:
        Optional human-readable panel title.

    area:
        Optional layout-area metadata.

        The registry does not interpret this value.

    visible:
        Initial visibility metadata.

    closable:
        Whether the panel is intended to be closable.

    metadata:
        Additional application-specific panel metadata.

    Notes
    -----
    PanelRegistration contains references to an existing panel
    instance. It does not create or destroy the panel.
    """

    panel_id: str
    panel: Any

    title: str = ""

    area: Optional[Any] = None

    visible: bool = True

    closable: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate registration data.
        """

        if not isinstance(
            self.panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        panel_id = self.panel_id.strip()

        if not panel_id:
            raise ValueError(
                "panel_id must not be empty."
            )

        if self.panel is None:
            raise ValueError(
                "panel must not be None."
            )

        if not isinstance(
            self.title,
            str,
        ):
            raise TypeError(
                "title must be a string."
            )

        if not isinstance(
            self.visible,
            bool,
        ):
            raise TypeError(
                "visible must be a bool."
            )

        if not isinstance(
            self.closable,
            bool,
        ):
            raise TypeError(
                "closable must be a bool."
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
# PANEL REGISTRY
# ============================================================


class PanelRegistry:
    """
    Central registry for GridForge UI panels.

    The registry is intentionally independent of Qt and
    MainWindow.

    It stores registrations and provides deterministic lookup.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty panel registry.
        """

        self._registrations: dict[
            str,
            PanelRegistration,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        panel_id: str,
        panel: Any,
        *,
        title: str = "",
        area: Optional[Any] = None,
        visible: bool = True,
        closable: bool = True,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
        replace: bool = False,
    ) -> PanelRegistration:
        """
        Register a panel.

        Parameters
        ----------
        panel_id:
            Stable panel identifier.

        panel:
            Existing concrete panel instance.

        title:
            Optional display title.

        area:
            Optional layout-area metadata.

        visible:
            Initial visibility metadata.

        closable:
            Closability metadata.

        metadata:
            Optional additional metadata.

        replace:
            When False, duplicate registration raises
            ValueError.

            When True, the existing registration is replaced.

        Returns
        -------
        PanelRegistration
            The resulting registration.

        Notes
        -----
        The registry never creates the panel instance.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        if panel is None:
            raise ValueError(
                "panel must not be None."
            )

        if normalized_id in self._registrations:
            if not replace:
                raise ValueError(
                    f"Panel already registered: "
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

        registration = PanelRegistration(
            panel_id=normalized_id,
            panel=panel,
            title=title,
            area=area,
            visible=visible,
            closable=closable,
            metadata=dict(metadata),
        )

        self._registrations[
            normalized_id
        ] = registration

        return registration

    # --------------------------------------------------------

    def register_panel(
        self,
        registration: PanelRegistration,
        *,
        replace: bool = False,
    ) -> PanelRegistration:
        """
        Register an existing PanelRegistration.

        This is the explicit registration-record API.
        """

        if not isinstance(
            registration,
            PanelRegistration,
        ):
            raise TypeError(
                "registration must be a "
                "PanelRegistration."
            )

        return self.register(
            registration.panel_id,
            registration.panel,
            title=registration.title,
            area=registration.area,
            visible=registration.visible,
            closable=registration.closable,
            metadata=registration.metadata,
            replace=replace,
        )

    # ========================================================
    # UNREGISTRATION
    # ========================================================

    def unregister(
        self,
        panel_id: str,
    ) -> Optional[PanelRegistration]:
        """
        Remove a panel registration.

        Returns the removed registration, or None when the panel
        was not registered.

        The panel instance itself is not destroyed.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        return self._registrations.pop(
            normalized_id,
            None,
        )

    # --------------------------------------------------------

    def unregister_panel(
        self,
        panel_id: str,
    ) -> Optional[PanelRegistration]:
        """
        Alias for unregister().
        """

        return self.unregister(
            panel_id
        )

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        panel_id: str,
    ) -> Optional[PanelRegistration]:
        """
        Return a panel registration by ID.

        Returns None when the panel is not registered.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        return self._registrations.get(
            normalized_id
        )

    # --------------------------------------------------------

    def get_panel(
        self,
        panel_id: str,
    ) -> Optional[Any]:
        """
        Return the concrete panel instance by ID.

        Returns None when the panel is not registered.
        """

        registration = self.get(
            panel_id
        )

        if registration is None:
            return None

        return registration.panel

    # --------------------------------------------------------

    def require(
        self,
        panel_id: str,
    ) -> PanelRegistration:
        """
        Return a registration or raise KeyError.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        try:
            return self._registrations[
                normalized_id
            ]

        except KeyError as exc:
            raise KeyError(
                f"Panel is not registered: "
                f"{normalized_id!r}"
            ) from exc

    # --------------------------------------------------------

    def require_panel(
        self,
        panel_id: str,
    ) -> Any:
        """
        Return a concrete panel or raise KeyError.
        """

        return self.require(
            panel_id
        ).panel

    # ========================================================
    # QUERIES
    # ========================================================

    def contains(
        self,
        panel_id: str,
    ) -> bool:
        """
        Return True when panel_id is registered.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        return (
            normalized_id
            in self._registrations
        )

    # --------------------------------------------------------

    def has(
        self,
        panel_id: str,
    ) -> bool:
        """
        Alias for contains().
        """

        return self.contains(
            panel_id
        )

    # --------------------------------------------------------

    def __contains__(
        self,
        panel_id: str,
    ) -> bool:
        """
        Support:

            "properties" in registry
        """

        return self.contains(
            panel_id
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered panels.
        """

        return len(
            self._registrations
        )

    # ========================================================
    # PANEL IDS
    # ========================================================

    def get_panel_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered panel IDs in registration order.
        """

        return tuple(
            self._registrations.keys()
        )

    # --------------------------------------------------------

    @property
    def panel_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Read-only convenience property for registered IDs.
        """

        return self.get_panel_ids()

    # ========================================================
    # REGISTRATIONS
    # ========================================================

    def get_registrations(
        self,
    ) -> tuple[PanelRegistration, ...]:
        """
        Return all registrations in registration order.
        """

        return tuple(
            self._registrations.values()
        )

    # --------------------------------------------------------

    def values(
        self,
    ) -> tuple[PanelRegistration, ...]:
        """
        Return registered panel records.

        Equivalent to get_registrations().
        """

        return self.get_registrations()

    # --------------------------------------------------------

    def items(
        self,
    ) -> tuple[
        tuple[str, PanelRegistration],
        ...,
    ]:
        """
        Return panel ID/registration pairs in registration order.
        """

        return tuple(
            self._registrations.items()
        )

    # ========================================================
    # FILTERING
    # ========================================================

    def get_by_area(
        self,
        area: Any,
    ) -> tuple[PanelRegistration, ...]:
        """
        Return panels whose registration area matches area.

        Area values are opaque metadata to the registry.
        """

        return tuple(
            registration
            for registration
            in self._registrations.values()
            if registration.area == area
        )

    # --------------------------------------------------------

    def get_visible(
        self,
    ) -> tuple[PanelRegistration, ...]:
        """
        Return registrations marked visible.

        This reads registration metadata only.

        It does not call widget visibility methods.
        """

        return tuple(
            registration
            for registration
            in self._registrations.values()
            if registration.visible
        )

    # --------------------------------------------------------

    def get_closable(
        self,
    ) -> tuple[PanelRegistration, ...]:
        """
        Return registrations marked closable.
        """

        return tuple(
            registration
            for registration
            in self._registrations.values()
            if registration.closable
        )

    # ========================================================
    # REPLACEMENT
    # ========================================================

    def replace(
        self,
        panel_id: str,
        panel: Any,
        *,
        title: str = "",
        area: Optional[Any] = None,
        visible: bool = True,
        closable: bool = True,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> PanelRegistration:
        """
        Replace an existing panel registration.

        Raises
        ------
        KeyError
            If panel_id is not currently registered.

        Notes
        -----
        The old panel instance is not destroyed.
        """

        normalized_id = self._normalize_id(
            panel_id
        )

        if normalized_id not in self._registrations:
            raise KeyError(
                f"Panel is not registered: "
                f"{normalized_id!r}"
            )

        return self.register(
            normalized_id,
            panel,
            title=title,
            area=area,
            visible=visible,
            closable=closable,
            metadata=metadata,
            replace=True,
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> tuple[PanelRegistration, ...]:
        """
        Remove all panel registrations.

        Returns
        -------
        tuple[PanelRegistration, ...]
            Registrations that were removed.

        The concrete panel instances are not destroyed.
        """

        registrations = self.get_registrations()

        self._registrations.clear()

        return registrations

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[str, PanelRegistration]:
        """
        Return a shallow snapshot of the registry.

        The returned dictionary can be inspected without exposing
        the registry's internal dictionary.
        """

        return dict(
            self._registrations
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _normalize_id(
        panel_id: str,
    ) -> str:
        """
        Validate and normalize a panel identifier.
        """

        if not isinstance(
            panel_id,
            str,
        ):
            raise TypeError(
                "panel_id must be a string."
            )

        normalized = panel_id.strip()

        if not normalized:
            raise ValueError(
                "panel_id must not be empty."
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

        return {
            "count": len(
                self._registrations
            ),
            "panel_ids": self.get_panel_ids(),
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
            "PanelRegistry("
            f"count={len(self)}, "
            f"panels={self.get_panel_ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PanelRegistration",
    "PanelRegistry",
]
