# ============================================================
# File: core/application/project_lifecycle.py
# GridForge V2 — Application Project Lifecycle Service
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
PresentationFactory = Callable[[ProjectContext], Any]
PresentationSerializer = Callable[[Any], Mapping[str, Any]]
PresentationDeserializer = Callable[[Mapping[str, Any]], Any]
ProjectStateActivator = Callable[[ProjectContext | None, LoadedProject | None], None]
ProjectStateValidator = Callable[[ProjectContext, LoadedProject | None, Any, Any], None]


class ProjectLifecycleService:
    """Own the active project's lifecycle at the Application boundary."""

    def __init__(self, *, network: Any, network_factory: NetworkFactory,
                 activate_network: NetworkActivator, context: ProjectContext | None = None,
                 loader: ProjectLoader | None = None, saver: ProjectSaver | None = None,
                 presentation: Any = None, presentation_factory: PresentationFactory | None = None,
                 serialize_presentation: PresentationSerializer | None = None,
                 deserialize_presentation: PresentationDeserializer | None = None,
                 project_state_activator: ProjectStateActivator | None = None,
                 project_state_validator: ProjectStateValidator | None = None) -> None:
        if network is None:
            raise ValueError("network is required.")
        if not callable(network_factory):
            raise TypeError("network_factory must be callable.")
        if not callable(activate_network):
            raise TypeError("activate_network must be callable.")
        if (serialize_presentation is None) != (deserialize_presentation is None):
            raise ValueError("serialize_presentation and deserialize_presentation must be configured together.")
        if project_state_activator is not None and not callable(project_state_activator):
            raise TypeError("project_state_activator must be callable.")
        if project_state_validator is not None and not callable(project_state_validator):
            raise TypeError("project_state_validator must be callable.")
        self._network = network
        self._network_factory = network_factory
        self._activate_network = activate_network
        self._context = context
        self._loader = loader
        self._saver = saver
        self._presentation = presentation
        self._presentation_factory = presentation_factory
        self._serialize_presentation = serialize_presentation
        self._deserialize_presentation = deserialize_presentation
        self._project_state_activator = project_state_activator
        self._project_state_validator = project_state_validator
        self._activation_generation = 1 if context is not None else 0

    @property
    def context(self) -> ProjectContext | None:
        return self._context

    @property
    def network(self) -> Any:
        return self._network

    @property
    def presentation(self) -> Any:
        return self._presentation

    @property
    def has_project(self) -> bool:
        return self._context is not None

    @property
    def activation_generation(self) -> int:
        return self._activation_generation

    def configure_persistence(self, *, loader: ProjectLoader, saver: ProjectSaver) -> None:
        if not callable(loader) or not callable(saver):
            raise TypeError("loader and saver must be callable.")
        self._loader = loader
        self._saver = saver

    def configure_project_state_validator(self, validator: ProjectStateValidator) -> None:
        if not callable(validator):
            raise TypeError("validator must be callable.")
        self._project_state_validator = validator

    def configure_project_state_activator(self, activator: ProjectStateActivator) -> None:
        if not callable(activator):
            raise TypeError("activator must be callable.")
        self._project_state_activator = activator

    def configure_presentation_factory(self, factory: PresentationFactory) -> None:
        if not callable(factory):
            raise TypeError("factory must be callable.")
        self._presentation_factory = factory

    def configure_presentation(self, *, presentation: Any, serializer: PresentationSerializer,
                               deserializer: PresentationDeserializer) -> None:
        if presentation is None:
            raise ValueError("presentation is required.")
        if not callable(serializer) or not callable(deserializer):
            raise TypeError("serializer and deserializer must be callable.")
        self._presentation = presentation
        self._serialize_presentation = serializer
        self._deserialize_presentation = deserializer

    def new_project(self, name: str = "Untitled Project", *, project_id: str | None = None) -> ProjectContext:
        context = ProjectContext(project_id=project_id or str(uuid4()), name=name, path=None)
        network = self._network_factory()
        presentation = self._create_presentation(context)
        self._validate_candidate(context, None, network, presentation)
        self._activate_network(network)
        self._network = network
        self._context = context
        self._presentation = presentation
        self._activate_project_state(context, None)
        self._activation_generation += 1
        return context

    def open_project(self, path: str | Path) -> ProjectContext:
        target = self._normalize_path(path)
        if self._loader is None:
            raise RuntimeError("Project persistence loader is not configured.")
        loaded = self._loader(target)
        if not isinstance(loaded, LoadedProject):
            raise TypeError("Project loader must return a LoadedProject.")
        if not isinstance(loaded.context, ProjectContext):
            raise TypeError("Project loader returned an invalid ProjectContext.")
        if loaded.network is None:
            raise ValueError("Project loader returned no Network.")

        presentation = None
        if loaded.presentation is not None:
            if self._deserialize_presentation is None:
                raise RuntimeError("Project contains persistent presentation state but no presentation deserializer is configured.")
            presentation = self._deserialize_presentation(loaded.presentation)
        else:
            presentation = self._create_presentation(loaded.context)

        self._validate_candidate(loaded.context, loaded, loaded.network, presentation)
        self._activate_network(loaded.network)
        self._network = loaded.network
        self._context = loaded.context
        self._presentation = presentation
        self._activate_project_state(loaded.context, loaded)
        self._activation_generation += 1
        return self._context

    def save_project(self, path: str | Path | None = None) -> ProjectContext:
        context = self._require_context()
        if self._saver is None:
            raise RuntimeError("Project persistence saver is not configured.")
        target = self._normalize_path(path) if path is not None else context.path
        if target is None:
            raise ValueError("A path is required to save an unnamed project.")

        presentation_data: Mapping[str, Any] | None = None
        if self._presentation is not None:
            if self._serialize_presentation is None:
                raise RuntimeError("A persistent presentation is active but no presentation serializer is configured.")
            presentation_data = self._serialize_presentation(self._presentation)
            if not isinstance(presentation_data, Mapping):
                raise TypeError("Presentation serializer must return a mapping.")

        self._saver(context, self._network, presentation_data, target)
        mark_clean = getattr(self._presentation, "mark_clean", None)
        if callable(mark_clean):
            mark_clean()
        if context.path != target:
            context = ProjectContext(project_id=context.project_id, name=context.name, path=target)
            self._context = context
        return context

    def save_project_as(self, path: str | Path) -> ProjectContext:
        return self.save_project(path)

    def close_project(self) -> ProjectContext | None:
        previous = self._context
        self._context = None
        self._presentation = None

        # Closing a project must also detach every Application read/mutation
        # service from the closed project's authoritative Network. Keep a
        # fresh empty Network as the inactive shell rather than leaving the
        # previous project graph reachable through the Application boundary.
        network = self._network_factory()
        self._activate_network(network)
        self._network = network
        self._activate_project_state(None, None)
        self._activation_generation += 1
        return previous

    def _validate_candidate(self, context: ProjectContext, loaded: LoadedProject | None, network: Any, presentation: Any) -> None:
        if self._project_state_validator is not None:
            self._project_state_validator(context, loaded, network, presentation)

    def _validate_candidate(self, context: ProjectContext, loaded: LoadedProject | None, network: Any, presentation: Any) -> None:
        if self._project_state_validator is not None:
            self._project_state_validator(context, loaded, network, presentation)

    def _validate_candidate(self, context: ProjectContext, loaded: LoadedProject | None, network: Any, presentation: Any) -> None:
        if self._project_state_validator is not None:
            self._project_state_validator(context, loaded, network, presentation)

    def _activate_project_state(self, context: ProjectContext | None, loaded: LoadedProject | None) -> None:
        if self._project_state_activator is not None:
            self._project_state_activator(context, loaded)

    def _create_presentation(self, context: ProjectContext) -> Any:
        if self._presentation_factory is None:
            return None
        presentation = self._presentation_factory(context)
        if presentation is None:
            raise RuntimeError("Presentation factory returned no presentation.")
        return presentation

    @staticmethod
    def _normalize_path(path: str | Path) -> Path:
        return normalize_package_path(path)

    def _require_context(self) -> ProjectContext:
        if self._context is None:
            raise RuntimeError("No active project.")
        return self._context


__all__ = [
    "PresentationDeserializer", "PresentationFactory", "PresentationSerializer", "ProjectLifecycleService",
    "ProjectLoader", "ProjectSaver", "ProjectStateActivator", "ProjectStateValidator",
]
