# ============================================================
# File: core/application/project_lifecycle.py
# GridForge V2 — Application Project Lifecycle Service
# Author: Subhendu Mishra
# ============================================================

"""Application-owned project lifecycle coordination."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .project import ProjectContext


ProjectLoader = Callable[[Path], tuple[ProjectContext, Any]]
ProjectSaver = Callable[[ProjectContext, Any, Path], None]
NetworkFactory = Callable[[], Any]
NetworkActivator = Callable[[Any], None]


class ProjectLifecycleService:
    """Own the active project's lifecycle at the Application boundary.

    Persistence is deliberately injected as a capability. The service does not
    implement a second persistence system; the canonical persistence service
    will be supplied by the Application composition root in the persistence
    workstream.
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
    ) -> None:
        if network is None:
            raise ValueError("network is required.")
        if not callable(network_factory):
            raise TypeError("network_factory must be callable.")
        if not callable(activate_network):
            raise TypeError("activate_network must be callable.")

        self._network = network
        self._network_factory = network_factory
        self._activate_network = activate_network
        self._context = context
        self._loader = loader
        self._saver = saver

    @property
    def context(self) -> ProjectContext | None:
        return self._context

    @property
    def network(self) -> Any:
        return self._network

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
        """Load and activate a project through the configured persistence capability."""
        target = self._normalize_path(path)
        if self._loader is None:
            raise RuntimeError("Project persistence loader is not configured.")

        context, network = self._loader(target)
        if not isinstance(context, ProjectContext):
            raise TypeError("Project loader must return a ProjectContext.")
        if network is None:
            raise ValueError("Project loader returned no Network.")

        self._activate(network)
        self._network = network
        self._context = context
        return context

    def save_project(self, path: str | Path | None = None) -> ProjectContext:
        """Persist the active project without changing context on failure."""
        context = self._require_context()
        if self._saver is None:
            raise RuntimeError("Project persistence saver is not configured.")

        target = self._normalize_path(path) if path is not None else context.path
        if target is None:
            raise ValueError("A path is required to save an unnamed project.")

        self._saver(context, self._network, target)
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
        return previous

    @staticmethod
    def _normalize_path(path: str | Path) -> Path:
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be a string or Path.")
        target = Path(path)
        if not str(target):
            raise ValueError("path must not be empty.")
        return target

    def _require_context(self) -> ProjectContext:
        if self._context is None:
            raise RuntimeError("No active project.")
        return self._context


__all__ = [
    "ProjectLifecycleService",
    "ProjectLoader",
    "ProjectSaver",
]
