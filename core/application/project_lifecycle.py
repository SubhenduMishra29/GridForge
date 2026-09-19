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
PresentationFactory = Callable[[ProjectContext], Any]
PresentationSerializer = Callable[[Any], Mapping[str, Any]]
PresentationDeserializer = Callable[[Mapping[str, Any]], Any]
ProjectStateActivator = Callable[[ProjectContext | None, LoadedProject | None], None]
ProjectStateValidator = Callable[[ProjectContext, LoadedProject | None, Any, Any], None]
PresentationActivator = Callable[[Any | None], None]
ActivationRollback = Callable[[], None]
ActivationTransaction = Callable[[ProjectContext | None, LoadedProject | None, Any, Any, int], ActivationRollback | None]


class ProjectLifecycleService:
    """Own the active project's lifecycle at the Application boundary."""

    def __init__(self, *, network: Any, network_factory: NetworkFactory,
                 activate_network: NetworkActivator, context: ProjectContext | None = None,
                 loader: ProjectLoader | None = None, saver: ProjectSaver | None = None,
                 presentation: Any = None, presentation_factory: PresentationFactory | None = None,
                 serialize_presentation: PresentationSerializer | None = None,
                 deserialize_presentation: PresentationDeserializer | None = None,
                 project_state_activator: ProjectStateActivator | None = None,
                 project_state_validator: ProjectStateValidator | None = None,
                 presentation_activator: PresentationActivator | None = None,
                 activation_transaction: ActivationTransaction | None = None) -> None:
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
        if presentation_activator is not None and not callable(presentation_activator):
            raise TypeError("presentation_activator must be callable.")
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
        self._presentation_activator = presentation_activator
        if activation_transaction is not None and not callable(activation_transaction):
            raise TypeError("activation_transaction must be callable.")
        self._activation_transaction = activation_transaction

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

    def configure_presentation_activator(self, activator: PresentationActivator) -> None:
        if not callable(activator):
            raise TypeError("activator must be callable.")
        self._presentation_activator = activator

    def configure_activation_transaction(self, transaction: ActivationTransaction) -> None:
        if not callable(transaction):
            raise TypeError("transaction must be callable.")
        self._activation_transaction = transaction

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
        next_generation = self._activation_generation + 1
        self._validate_candidate(context, None, network, presentation)
        self._commit_candidate(context, None, network, presentation, next_generation)
        self._network = network
        self._context = context
        self._presentation = presentation
        self._activation_generation = next_generation
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

        next_generation = self._activation_generation + 1
        self._validate_candidate(loaded.context, loaded, loaded.network, presentation)
        self._commit_candidate(loaded.context, loaded, loaded.network, presentation, next_generation)
        self._network = loaded.network
        self._context = loaded.context
        self._presentation = presentation
        self._activation_generation = next_generation
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

        # Closing is the same atomic activation boundary as opening/new-project:
        # stage the inactive runtime, commit once, then publish ProjectClosed.
        network = self._network_factory()
        next_generation = self._activation_generation + 1
        self._commit_candidate(None, None, network, None, next_generation)
        self._network = network
        self._context = None
        self._presentation = None
        self._activation_generation = next_generation
        return previous

    def _commit_candidate(
        self,
        context: ProjectContext | None,
        loaded: LoadedProject | None,
        network: Any,
        presentation: Any | None,
        generation: int,
    ) -> None:
        """Commit one fully validated candidate through the single activation boundary."""
        if self._activation_transaction is not None:
            rollback = self._activation_transaction(context, loaded, network, presentation, generation)
            if rollback is not None and not callable(rollback):
                raise TypeError("activation_transaction must return a callable rollback or None.")
            return

        # Compatibility path for legacy composition callers.
        previous_network = self._network
        previous_context = self._context
        previous_presentation = self._presentation
        try:
            self._activate_presentation(presentation)
            self._activate_network(network)
            self._activate_project_state(context, loaded)
        except Exception:
            try:
                self._activate_presentation(previous_presentation)
                self._activate_network(previous_network)
                self._activate_project_state(previous_context, None)
            except Exception as rollback_exc:
                raise RuntimeError("Project activation failed and rollback also failed.") from rollback_exc
            raise

    def _activate_presentation(self, presentation: Any | None) -> None:
        if self._presentation_activator is not None:
            self._presentation_activator(presentation)

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
    "ProjectLoader", "ProjectSaver", "ProjectStateActivator", "ProjectStateValidator", "PresentationActivator",
]
