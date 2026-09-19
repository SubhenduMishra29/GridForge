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
NetworkActivator = Callable[[Any], Callable[[], None] | None]
PresentationFactory = Callable[[ProjectContext], Any]
PresentationSerializer = Callable[[Any], Mapping[str, Any]]
PresentationDeserializer = Callable[[Mapping[str, Any]], Any]
ProjectStateActivator = Callable[
    [ProjectContext | None, LoadedProject | None, Any, int],
    Callable[[], None] | None,
]
ProjectStateValidator = Callable[[ProjectContext, LoadedProject | None, Any, Any], None]
PresentationActivator = Callable[[Any | None], Callable[[], None] | None]


class ProjectLifecycleService:
    """Own the single Application project activation transaction boundary."""

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
        presentation_factory: PresentationFactory | None = None,
        serialize_presentation: PresentationSerializer | None = None,
        deserialize_presentation: PresentationDeserializer | None = None,
        project_state_activator: ProjectStateActivator | None = None,
        project_state_validator: ProjectStateValidator | None = None,
        presentation_activator: PresentationActivator | None = None,
    ) -> None:
        if network is None:
            raise ValueError("network is required.")
        if not callable(network_factory):
            raise TypeError("network_factory must be callable.")
        if not callable(activate_network):
            raise TypeError("activate_network must be callable.")
        if (serialize_presentation is None) != (deserialize_presentation is None):
            raise ValueError("serialize_presentation and deserialize_presentation must be configured together.")
        for name, callback in (
            ("project_state_activator", project_state_activator),
            ("project_state_validator", project_state_validator),
            ("presentation_activator", presentation_activator),
        ):
            if callback is not None and not callable(callback):
                raise TypeError(f"{name} must be callable.")

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
        self._presentation_activator = presentation_activator
        self._activation_generation = 1 if context is not None else 0
        self._state = "ACTIVE" if context is not None else "NO_PROJECT"
        self._rollback_error: Exception | None = None

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

    @property
    def state(self) -> str:
        """Return the lifecycle integrity state."""
        return self._state

    @property
    def rollback_error(self) -> Exception | None:
        """Return the rollback failure that put lifecycle into ROLLBACK_FAILED."""
        return self._rollback_error

    def configure_persistence(self, *, loader: ProjectLoader, saver: ProjectSaver) -> None:
        if not callable(loader) or not callable(saver):
            raise TypeError("loader and saver must be callable.")
        self._loader = loader
        self._saver = saver

    def configure_project_state_validator(self, validator: ProjectStateValidator) -> None:
        if not callable(validator):
            raise TypeError("validator must be callable.")
        self._project_state_validator = validator

    def configure_presentation_factory(self, factory: PresentationFactory) -> None:
        if not callable(factory):
            raise TypeError("factory must be callable.")
        self._presentation_factory = factory

    def configure_presentation_activator(self, activator: PresentationActivator) -> None:
        if not callable(activator):
            raise TypeError("activator must be callable.")
        self._presentation_activator = activator

    def configure_presentation(
        self,
        *,
        presentation: Any,
        serializer: PresentationSerializer,
        deserializer: PresentationDeserializer,
    ) -> None:
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
        context = ProjectContext(
            project_id=project_id or str(uuid4()),
            name=name,
            path=None,
        )
        network = self._network_factory()
        presentation = self._create_presentation(context)
        return self._activate_candidate(context, None, network, presentation)

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

        if loaded.presentation is not None:
            if self._deserialize_presentation is None:
                raise RuntimeError(
                    "Project contains persistent presentation state but no presentation "
                    "deserializer is configured."
                )
            presentation = self._deserialize_presentation(loaded.presentation)
        else:
            presentation = self._create_presentation(loaded.context)

        return self._activate_candidate(
            loaded.context,
            loaded,
            loaded.network,
            presentation,
        )

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
                raise RuntimeError(
                    "A persistent presentation is active but no presentation serializer is configured."
                )
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
        network = self._network_factory()
        return self._activate_candidate(None, None, network, None, previous_context=previous)

    def _activate_candidate(
        self,
        context: ProjectContext | None,
        loaded: LoadedProject | None,
        network: Any,
        presentation: Any | None,
        *,
        previous_context: ProjectContext | None = None,
    ) -> ProjectContext | None:
        if self._state == "ROLLBACK_FAILED":
            raise RuntimeError(
                "Project lifecycle is in ROLLBACK_FAILED state and requires recovery before another transition."
            ) from self._rollback_error
        if context is not None:
            self._validate_candidate(context, loaded, network, presentation)
        elif loaded is not None:
            raise ValueError("An empty activation cannot carry loaded project data.")

        old_context = self._context
        old_network = self._network
        old_presentation = self._presentation
        old_generation = self._activation_generation
        old_state = self._state
        old_rollback_error = self._rollback_error
        next_generation = old_generation + 1

        rollback_stack: list[Callable[[], None]] = []
        try:
            rollback = self._activate_presentation(presentation)
            if rollback is not None:
                rollback_stack.append(rollback)

            rollback = self._activate_network(network)
            if rollback is not None:
                rollback_stack.append(rollback)

            rollback = self._activate_project_state(context, loaded, network, next_generation)
            if rollback is not None:
                rollback_stack.append(rollback)

            self._network = network
            self._context = context
            self._presentation = presentation
            self._activation_generation = next_generation
            self._state = "ACTIVE" if context is not None else "NO_PROJECT"
            self._rollback_error = None
            return context if context is not None else previous_context
        except Exception as activation_error:
            rollback_errors: list[Exception] = []
            for rollback in reversed(rollback_stack):
                try:
                    rollback()
                except Exception as rollback_error:
                    rollback_errors.append(rollback_error)

            self._network = old_network
            self._context = old_context
            self._presentation = old_presentation
            self._activation_generation = old_generation

            if rollback_errors:
                self._state = "ROLLBACK_FAILED"
                self._rollback_error = RuntimeError(
                    "One or more project activation rollback callbacks failed."
                )
                self._rollback_error.__cause__ = activation_error
                raise RuntimeError(
                    "Project activation failed and rollback is incomplete; lifecycle is ROLLBACK_FAILED."
                ) from activation_error

            self._state = old_state
            self._rollback_error = old_rollback_error
            raise

    def _activate_presentation(self, presentation: Any | None) -> Callable[[], None] | None:
        if self._presentation_activator is None:
            return None
        return self._presentation_activator(presentation)

    def _validate_candidate(
        self,
        context: ProjectContext,
        loaded: LoadedProject | None,
        network: Any,
        presentation: Any | None,
    ) -> None:
        if not isinstance(context, ProjectContext):
            raise TypeError("Candidate project context must be a ProjectContext.")
        if network is None:
            raise ValueError("Candidate project must provide a Network.")
        if presentation is None:
            raise RuntimeError("Candidate project requires an Application-owned presentation.")

        for candidate, label in ((network, "network"), (presentation, "presentation")):
            candidate_project_id = getattr(candidate, "project_id", None)
            if candidate_project_id is not None and candidate_project_id != context.project_id:
                raise ValueError(f"Candidate {label} project_id does not match the candidate project.")

        if loaded is not None and loaded.context.project_id != context.project_id:
            raise ValueError("Loaded project context does not match the candidate context.")

        if self._project_state_validator is None:
            raise RuntimeError("Application-owned candidate validator is not configured.")
        self._project_state_validator(context, loaded, network, presentation)

    def _activate_project_state(
        self,
        context: ProjectContext | None,
        loaded: LoadedProject | None,
        network: Any,
        generation: int,
    ) -> Callable[[], None] | None:
        if self._project_state_activator is None:
            return None
        return self._project_state_activator(context, loaded, network, generation)

    def _create_presentation(self, context: ProjectContext) -> Any:
        if not isinstance(context, ProjectContext):
            raise TypeError("Presentation creation requires a ProjectContext.")
        if self._presentation_factory is None:
            raise RuntimeError("Application-owned presentation factory is not configured.")
        presentation = self._presentation_factory(context)
        if presentation is None:
            raise RuntimeError("Presentation factory returned no presentation.")
        candidate_project_id = getattr(presentation, "project_id", None)
        if candidate_project_id is not None and candidate_project_id != context.project_id:
            raise ValueError("Presentation factory returned a presentation for a different project.")
        return presentation

    def _normalize_path(self, path: str | Path) -> Path:
        return normalize_package_path(path)

    def _require_context(self) -> ProjectContext:
        if self._context is None:
            raise RuntimeError("No active project.")
        return self._context


__all__ = [
    "PresentationDeserializer",
    "PresentationFactory",
    "PresentationSerializer",
    "ProjectLifecycleService",
    "ProjectLoader",
    "ProjectSaver",
    "ProjectStateActivator",
    "ProjectStateValidator",
    "PresentationActivator",
]
