# ============================================================
# File: core/application/project_lifecycle.py
# GridForge V2 — Application Project Lifecycle Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned project lifecycle coordination."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from core.persistence.project_package import normalize_package_path
from core.persistence.project_persistence import LoadedProject

from .project import ProjectContext


ProjectLoader = Callable[[Path], LoadedProject]
ProjectSaver = Callable[[ProjectContext, Any, Mapping[str, Any] | None, Path], None]
NetworkFactory = Callable[[], Any]
NetworkActivator = Callable[[Any], None]
PresentationSerializer = Callable[[Any], Mapping[str, Any]]
PresentationDeserializer = Callable[[Mapping[str, Any]], Any]


class ProjectLifecycleService:
    """Own the active project's lifecycle at the Application boundary.

    Persistence is injected as one canonical capability. The lifecycle service
    coordinates Core and optional presentation state without importing or
    depending on any concrete UI/SLD implementation.
    """

    def __init__(
        self,
        *,
        network: Any,
        network_factory: NetworkFactory,
        activate_network: NetworkActivator,
        context: ProjectContext | None = None,
        loader: ProjectLoader | None = None,
        saver: ProjectSaver | None = None,
        presentation: Any = None,
        serialize_presentation: PresentationSerializer | None = None,
        deserialize_presentation: PresentationDeserializer | None = None,
    ) -> None:
        if network is None:
            raise ValueError("network is required.")
        if not callable(network_factory):
            raise TypeError("network_factory must be callable.")
        if not callable(activate_network):
            raise TypeError("activate_network must be callable.")
        if (serialize_presentation is None) != (deserialize_presentation is None):
            raise ValueError(
                "serialize_presentation and deserialize_presentation must be configured together."
            )

        self._network = network
        self._network_factory = network_factory
        self._activate_network = activate_network
        self._context = context
        self._loader = loader
        self._saver = saver
        self._presentation = presentation
        self._serialize_presentation = serialize_presentation
        self._deserialize_presentation = deserialize_presentation

    @property
    def context(self) -> ProjectContext | None:
        return self._context

    @property
    def network(self) -> Any:
        return self._network

    @property
    def presentation(self) -> Any:
        """Return the active persistent presentation document/state."""
        return self._presentation

    @property
    def has_project(self) -> bool:
        return self._context is not None

    def configure_persistence(
        self,
        *,
        loader: ProjectLoader,
        saver: ProjectSaver,
    ) -> None:
        """Attach the canonical persistence capability without owning it."""
        if not callable(loader) or not callable(saver):
            raise TypeError("loader and saver must be callable.")
        self._loader = loader
        self._saver = saver

    def configure_presentation(
        self,
        *,
        presentation: Any,
        serializer: PresentationSerializer,
        deserializer: PresentationDeserializer,
    ) -> None:
        """Attach the concrete persistent presentation codec at the UI boundary."""
        if presentation is None:
            raise ValueError("presentation is required.")
        if not callable(serializer) or not callable(deserializer):
            raise TypeError("serializer and deserializer must be callable.")
        self._presentation = presentation
        self._serialize_presentation = serializer
        self._deserialize_presentation = deserializer

    def new_project(
        self,
        name: str = "Untitled Project",
        *,
        project_id: str | None = None,
    ) -> ProjectContext:
        """Create and activate a new clean in-memory project."""
        context = ProjectContext(
            project_id=project_id or str(uuid4()),
            name=name,
            path=None,
        )
        network = self._network_factory()
        self._activate(network)
        self._network = network
        self._context = context
        return context

    def open_project(self, path: str | Path) -> ProjectContext:
        """Load and activate Core plus optional persistent presentation state."""
        target = self._normalize_path(path)
        if self._loader is None:
            raise RuntimeError("Project persistence loader is not configured.")

        loaded = self._loader(target)
        if not isinstance(loaded, LoadedProject):
            raise TypeError("Project loader must return a LoadedProject.")
        context = loaded.context
        network = loaded.network
        if not isinstance(context, ProjectContext):
            raise TypeError("Project loader returned an invalid ProjectContext.")
        if network is None:
            raise ValueError("Project loader returned no Network.")

        presentation = None
        if loaded.presentation is not None:
            if self._deserialize_presentation is None:
                raise RuntimeError(
                    "Project contains persistent presentation state but no presentation deserializer is configured."
                )
            presentation = self._deserialize_presentation(loaded.presentation)

        self._activate(network)
        self._network = network
        self._context = context
        if presentation is not None:
            self._presentation = presentation
        return context

    def save_project(self, path: str | Path | None = None) -> ProjectContext:
        """Persist the active project without changing context on failure."""
        context = self._require_context()
        if self._saver is None:
            raise RuntimeError("Project persistence saver is not configured.")

        target = self._normalize_path(path) if path is not None else context.path
        if target is None:
            raise ValueError("A path is required to save an unnamed project.")

        presentation_data: Mapping[str, Any] | None = None
        if self._presentation is not None:
            if self._serialize_presentation is None:
                raise RuntimeError(
                    "A persistent presentation is active but no presentation serializer is configured."
                )
            presentation_data = self._serialize_presentation(self._presentation)
            if not isinstance(presentation_data, Mapping):
                raise TypeError("Presentation serializer must return a mapping.")

        self._saver(context, self._network, presentation_data, target)
        if context.path != target:
            context = ProjectContext(
                project_id=context.project_id,
                name=context.name,
                path=target,
            )
            self._context = context
        return context

    def save_project_as(self, path: str | Path) -> ProjectContext:
        """Persist the active project to a new package path."""
        return self.save_project(path)

    def close_project(self) -> ProjectContext | None:
        """Close the active project and release its lifecycle context."""
        previous = self._context
        self._context = None
        self._presentation = None
        return previous

    @staticmethod
    def _normalize_path(path: str | Path) -> Path:
        return normalize_package_path(path)

    def _require_context(self) -> ProjectContext:
        if self._context is None:
            raise RuntimeError("No active project.")
        return self._context


__all__ = [
    "PresentationDeserializer",
    "PresentationSerializer",
    "ProjectLifecycleService",
    "ProjectLoader",
    "ProjectSaver",
]
