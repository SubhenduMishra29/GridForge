"""
GridForge V2 — deterministic UI plugin lifecycle orchestration.

Author: Subhendu Mishra

Plugin construction is context-free. PluginContext is supplied during
initialization and is the single dependency carrier for plugin composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Optional

from .plugin_context import PluginContext
from .plugin_events import (PluginEvent, PluginEventSource, plugin_defined, plugin_disabled, plugin_enabled, plugin_failed, plugin_initialize_requested, plugin_initialized, plugin_initializing, plugin_load_requested, plugin_loaded, plugin_shutdown, plugin_shutdown_requested, plugin_shutting_down, plugin_unload_requested, plugin_unloaded)
from .plugin_contract import validate_plugin
from .plugin_loader import PluginLoader, create_default_plugin_loader
from .plugin_registry import PluginEntry, PluginRegistry, create_plugin_registry
from .plugin_state import PluginStateStore


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    """Declarative composition definition for one UI plugin."""

    plugin_id: str
    dependencies: tuple[str, ...] = ()
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.plugin_id, str) or not self.plugin_id.strip():
            raise ValueError("plugin_id must be a non-empty string.")
        if not isinstance(self.dependencies, tuple):
            raise TypeError("dependencies must be a tuple.")
        if any(not isinstance(item, str) or not item.strip() for item in self.dependencies):
            raise ValueError("dependencies must contain non-empty strings.")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("dependencies cannot contain duplicates.")
        if self.plugin_id in self.dependencies:
            raise ValueError(f"Plugin {self.plugin_id!r} cannot depend on itself.")
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a Mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class PluginManager:
    """Coordinates explicitly defined GridForge V2 UI plugins."""

    def __init__(self, *, loader: Optional[PluginLoader] = None, registry: Optional[PluginRegistry] = None,
                 state_store: Optional[PluginStateStore] = None, definitions: Optional[Iterable[PluginDefinition]] = None,
                 event_sink: Optional[Callable[[PluginEvent], None]] = None) -> None:
        if event_sink is not None and not callable(event_sink):
            raise TypeError("event_sink must be callable or None.")
        self._event_sink = event_sink
        self._events: list[PluginEvent] = []
        self._loader = loader if loader is not None else create_default_plugin_loader()
        if not isinstance(self._loader, PluginLoader):
            raise TypeError("loader must be a PluginLoader.")
        if registry is not None:
            if not isinstance(registry, PluginRegistry):
                raise TypeError("registry must be a PluginRegistry.")
            self._registry = registry
            registry_state_store = registry.state_store
            if state_store is not None and state_store is not registry_state_store:
                raise ValueError("state_store must be the same PluginStateStore instance owned by the supplied registry.")
            self._state_store = registry_state_store
        else:
            self._state_store = state_store if state_store is not None else PluginStateStore()
            if not isinstance(self._state_store, PluginStateStore):
                raise TypeError("state_store must be a PluginStateStore.")
            self._registry = create_plugin_registry(state_store=self._state_store, event_sink=self._emit)
        self._definitions: dict[str, PluginDefinition] = {}
        self._contexts: dict[str, PluginContext] = {}
        if definitions is not None:
            self.define_many(definitions)

    @property
    def loader(self) -> PluginLoader:
        return self._loader

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    @property
    def state_store(self) -> PluginStateStore:
        return self._state_store

    @property
    def events(self) -> tuple[PluginEvent, ...]:
        """Return the immutable observational lifecycle event history."""
        return tuple(self._events)

    @property
    def definitions(self) -> tuple[PluginDefinition, ...]:
        return tuple(self._definitions.values())

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        return tuple(self._definitions.keys())

    def get(self, plugin_id: str) -> Any:
        """Return a loaded plugin instance through the canonical registry."""
        self._require_definition(plugin_id)
        entry = self._registry.get_entry(plugin_id)
        if entry is None:
            raise KeyError(f"Plugin {plugin_id!r} is not loaded.")
        return entry.plugin

    def define(self, definition: PluginDefinition) -> None:
        if not isinstance(definition, PluginDefinition):
            raise TypeError("definition must be PluginDefinition.")
        if definition.plugin_id in self._definitions:
            raise ValueError(f"Plugin definition {definition.plugin_id!r} already exists.")
        self._definitions[definition.plugin_id] = definition
        self._emit(plugin_defined(definition.plugin_id, source=PluginEventSource.MANAGER))

    def define_many(self, definitions: Iterable[PluginDefinition]) -> None:
        for definition in definitions:
            self.define(definition)

    def remove_definition(self, plugin_id: str) -> None:
        self._validate_plugin_id(plugin_id)
        if self._registry.contains(plugin_id):
            raise RuntimeError(f"Plugin {plugin_id!r} is currently registered.")
        dependants = self._direct_dependants(plugin_id)
        if dependants:
            raise RuntimeError(f"Cannot remove plugin {plugin_id!r}; dependent definitions remain: {', '.join(dependants)}.")
        self._definitions.pop(plugin_id, None)
        self._contexts.pop(plugin_id, None)

    def define_defaults(self) -> None:
        defaults = (
            PluginDefinition("canvas"),
            PluginDefinition("menu"),
            PluginDefinition("panels", dependencies=("canvas",)),
            PluginDefinition("toolbar", dependencies=("canvas",)),
            PluginDefinition("status", dependencies=("canvas", "panels", "toolbar")),
            PluginDefinition("shell", dependencies=("canvas", "panels", "toolbar", "status")),
        )
        for definition in defaults:
            if definition.plugin_id not in self._definitions:
                self.define(definition)

    def set_context(self, plugin_id: str, context: PluginContext) -> None:
        self._require_definition(plugin_id)
        if not isinstance(context, PluginContext):
            raise TypeError("context must be PluginContext.")
        self._contexts[plugin_id] = context

    def set_contexts(self, contexts: Mapping[str, PluginContext]) -> None:
        if not isinstance(contexts, Mapping):
            raise TypeError("contexts must be a Mapping.")
        for plugin_id, context in contexts.items():
            self.set_context(plugin_id, context)

    def context(self, plugin_id: str) -> Optional[PluginContext]:
        self._require_definition(plugin_id)
        return self._contexts.get(plugin_id)

    def load(self, plugin_id: str) -> PluginEntry:
        self._require_definition(plugin_id)
        order = self.resolve_order((plugin_id,))
        self._load_plugins(order)
        entry = self._registry.get_entry(plugin_id)
        if entry is None:
            raise RuntimeError(f"Plugin {plugin_id!r} was not registered after loading.")
        return entry

    def load_many(self, plugin_ids: Optional[Iterable[str]] = None) -> tuple[PluginEntry, ...]:
        order = self.resolve_order(plugin_ids)
        self._load_plugins(order)
        return tuple(
            self._registry.get_entry(plugin_id)
            for plugin_id in order
            if self._registry.get_entry(plugin_id) is not None
        )

    def load_all(self) -> tuple[PluginEntry, ...]:
        return self.load_many()

    def _load_plugins(self, order: Iterable[str]) -> list[str]:
        """Load one ordered lifecycle transaction and compensate new registrations on failure."""
        loaded_here: list[str] = []
        try:
            for current_id in order:
                if self._registry.contains(current_id):
                    continue
                self._emit(
                    plugin_load_requested(
                        current_id,
                        source=PluginEventSource.MANAGER,
                    )
                )
                definition = self._definitions[current_id]
                try:
                    plugin = self._loader.create(current_id)
                    validate_plugin(plugin, plugin_id=current_id)
                    self._registry.register(
                        current_id,
                        plugin,
                        enabled=definition.enabled,
                        metadata=dict(definition.metadata),
                    )
                except Exception as exc:
                    self._emit(
                        plugin_failed(
                            current_id,
                            exc,
                            operation="load",
                            recoverable=True,
                            source=PluginEventSource.MANAGER,
                        )
                    )
                    raise
                loaded_here.append(current_id)
                self._emit(
                    plugin_loaded(
                        current_id,
                        source=PluginEventSource.MANAGER,
                    )
                )
        except Exception as exc:
            rollback_errors = self._rollback_loaded(loaded_here)
            if rollback_errors:
                raise ExceptionGroup(
                    "Plugin load transaction and compensation failed.",
                    [exc, *rollback_errors],
                ) from exc
            raise
        return loaded_here

    def _rollback_loaded(
        self,
        loaded_here: Iterable[str],
        *,
        protected: Iterable[str] = (),
    ) -> list[BaseException]:
        """Restore transaction-created registrations unless safe compensation failed."""
        failures: list[BaseException] = []
        protected_ids = set(protected)
        for plugin_id in reversed(tuple(loaded_here)):
            if plugin_id in protected_ids:
                continue
            if not self._registry.contains(plugin_id):
                continue
            metadata = {"rollback": True}
            self._emit(
                plugin_unload_requested(
                    plugin_id,
                    source=PluginEventSource.MANAGER,
                    metadata=metadata,
                )
            )
            try:
                if self._registry.is_initialized(plugin_id):
                    self._shutdown_one(
                        plugin_id,
                        metadata=metadata,
                    )
                if self._registry.is_enabled(plugin_id):
                    self._registry.disable(plugin_id)
                    self._emit(
                        plugin_disabled(
                            plugin_id,
                            source=PluginEventSource.MANAGER,
                            metadata=metadata,
                        )
                    )
                self._registry.unregister(plugin_id, shutdown=False)
                self._emit(
                    plugin_unloaded(
                        plugin_id,
                        source=PluginEventSource.MANAGER,
                        metadata=metadata,
                    )
                )
            except Exception as exc:
                failures.append(exc)
                self._emit(
                    plugin_failed(
                        plugin_id,
                        exc,
                        operation="unload",
                        recoverable=True,
                        source=PluginEventSource.MANAGER,
                        metadata=metadata,
                    )
                )
        return failures

    def initialize(self, plugin_id: str) -> Any:
        self._require_definition(plugin_id)
        results = self._initialize_transaction(self.resolve_order((plugin_id,)))
        return results[-1] if results else None

    def initialize_many(self, plugin_ids: Optional[Iterable[str]] = None) -> tuple[Any, ...]:
        return tuple(
            self._initialize_transaction(self.resolve_order(plugin_ids))
        )

    def initialize_all(self) -> tuple[Any, ...]:
        return self.initialize_many()

    def _initialize_transaction(self, order: Iterable[str]) -> list[Any]:
        """Initialize an ordered dependency closure as one load/initialization transaction."""
        loaded_here = self._load_plugins(order)
        initialized_here: list[str] = []
        results: list[Any] = []
        initialization_started = False
        current_initializing: Optional[str] = None
        try:
            for current_id in order:
                definition = self._definitions[current_id]
                if not definition.enabled:
                    continue
                self._require_enabled_dependencies(current_id)
                if not self._registry.is_enabled(current_id):
                    raise RuntimeError(f"Plugin {current_id!r} is runtime-disabled.")
                if self._registry.is_initialized(current_id):
                    continue
                context = self._contexts.get(current_id)
                if context is None:
                    raise RuntimeError(
                        f"Plugin {current_id!r} requires an explicit PluginContext before initialization."
                    )
                if current_id == "shell":
                    self._prepare_shell_composition()
                self._emit(
                    plugin_initialize_requested(
                        current_id,
                        source=PluginEventSource.MANAGER,
                    )
                )
                self._emit(
                    plugin_initializing(
                        current_id,
                        source=PluginEventSource.MANAGER,
                    )
                )
                initialization_started = True
                current_initializing = current_id
                try:
                    result = self._registry.initialize(
                        current_id,
                        context=context,
                    )
                except Exception as exc:
                    self._emit(
                        plugin_failed(
                            current_id,
                            exc,
                            operation="initialize",
                            recoverable=True,
                            source=PluginEventSource.MANAGER,
                        )
                    )
                    raise

                # PluginRegistry returns only after canonical initialization
                # state has been committed. From this point onward, this is
                # a normal initialized plugin, never a failed pre-initialization
                # attempt. Clear the compensation guard before emitting the
                # observational INITIALIZED event.
                initialized_here.append(current_id)
                results.append(result)
                initialization_started = False
                current_initializing = None

                self._emit(
                    plugin_initialized(
                        current_id,
                        source=PluginEventSource.MANAGER,
                    )
                )
        except Exception as exc:
            rollback_errors: list[BaseException] = []
            protected_loaded: set[str] = set()
            if initialization_started and current_initializing is not None:
                metadata = {"rollback": True}
                failed_id = current_initializing
                self._emit(
                    plugin_shutdown_requested(
                        failed_id,
                        source=PluginEventSource.MANAGER,
                        metadata=metadata,
                    )
                )
                self._emit(
                    plugin_shutting_down(
                        failed_id,
                        source=PluginEventSource.MANAGER,
                        metadata=metadata,
                    )
                )
                try:
                    self._registry.compensate_failed_initialization(failed_id)
                except Exception as compensation_error:
                    rollback_errors.append(compensation_error)
                    protected_loaded.add(failed_id)
                    self._emit(
                        plugin_failed(
                            failed_id,
                            compensation_error,
                            operation="rollback_shutdown",
                            recoverable=True,
                            source=PluginEventSource.MANAGER,
                            metadata=metadata,
                        )
                    )
                else:
                    self._emit(
                        plugin_shutdown(
                            failed_id,
                            source=PluginEventSource.MANAGER,
                            metadata=metadata,
                        )
                    )
            rollback_errors.extend(self._rollback_initialization(initialized_here))
            rollback_errors.extend(
                self._rollback_loaded(
                    loaded_here,
                    protected=protected_loaded,
                )
            )
            if rollback_errors:
                raise ExceptionGroup(
                    "Plugin initialization transaction and compensation failed.",
                    [exc, *rollback_errors],
                ) from exc
            raise
        return results

    def _prepare_shell_composition(self) -> None:
        shell_entry = self._registry.get_entry("shell")
        if shell_entry is None:
            raise RuntimeError("Shell plugin is not registered.")
        shell_plugin = shell_entry.plugin
        entries = {plugin_id: self._registry.get_entry(plugin_id) for plugin_id in ("canvas", "toolbar", "status")}
        for plugin_id, entry in entries.items():
            if entry is None:
                raise RuntimeError(f"Shell composition requires registered {plugin_id} plugin.")
            if not self._registry.is_initialized(plugin_id):
                raise RuntimeError(f"{plugin_id.title()} plugin must be initialized before shell composition.")
        widgets = {plugin_id: getattr(entry.plugin, "widget", None) for plugin_id, entry in entries.items()}
        for plugin_id, widget in widgets.items():
            if widget is None:
                raise RuntimeError(f"{plugin_id.title()}Plugin did not expose an initialized widget.")
        setter = getattr(shell_plugin, "set_composition", None)
        if not callable(setter):
            raise RuntimeError("ShellPlugin does not implement the required set_composition() contract.")
        setter(canvas_widget=widgets["canvas"], toolbar_widget=widgets["toolbar"], status_widget=widgets["status"])

    def enable(self, plugin_id: str) -> None:
        self._require_definition(plugin_id)
        if not self._registry.contains(plugin_id):
            raise KeyError(f"Plugin {plugin_id!r} is not registered.")
        if self._registry.is_enabled(plugin_id):
            return
        try:
            self._registry.enable(plugin_id)
        except Exception as exc:
            self._emit(
                plugin_failed(
                    plugin_id,
                    exc,
                    operation="enable",
                    recoverable=True,
                    source=PluginEventSource.MANAGER,
                )
            )
            raise
        self._emit(plugin_enabled(plugin_id, source=PluginEventSource.MANAGER))

    def disable(self, plugin_id: str) -> None:
        self._require_definition(plugin_id)
        if not self._registry.contains(plugin_id):
            raise KeyError(f"Plugin {plugin_id!r} is not registered.")
        if self._registry.is_initialized(plugin_id):
            self.shutdown(plugin_id)
        if not self._registry.is_enabled(plugin_id):
            return
        try:
            self._registry.disable(plugin_id, shutdown=False)
        except Exception as exc:
            self._emit(
                plugin_failed(
                    plugin_id,
                    exc,
                    operation="disable",
                    recoverable=True,
                    source=PluginEventSource.MANAGER,
                )
            )
            raise
        self._emit(plugin_disabled(plugin_id, source=PluginEventSource.MANAGER))

    def _shutdown_one(
        self,
        plugin_id: str,
        *,
        metadata: Optional[Mapping[str, Any]] = None,
        failure_operation: str = "shutdown",
    ) -> None:
        self._emit(
            plugin_shutdown_requested(
                plugin_id,
                source=PluginEventSource.MANAGER,
                metadata=metadata,
            )
        )
        self._emit(
            plugin_shutting_down(
                plugin_id,
                source=PluginEventSource.MANAGER,
                metadata=metadata,
            )
        )
        try:
            self._registry.shutdown(plugin_id)
        except Exception as exc:
            self._emit(
                plugin_failed(
                    plugin_id,
                    exc,
                    operation=failure_operation,
                    recoverable=True,
                    source=PluginEventSource.MANAGER,
                    metadata=metadata,
                )
            )
            raise
        self._emit(
            plugin_shutdown(
                plugin_id,
                source=PluginEventSource.MANAGER,
                metadata=metadata,
            )
        )

    def shutdown(self, plugin_id: str) -> None:
        self._require_definition(plugin_id)
        affected = set(self._dependent_closure(plugin_id))
        failures: list[BaseException] = []
        failed_plugins: set[str] = set()
        for current_id in reversed(
            tuple(item for item in self.resolve_order() if item in affected)
        ):
            if not (
                self._registry.contains(current_id)
                and self._registry.is_initialized(current_id)
            ):
                continue
            if any(
                dependant in failed_plugins
                for dependant in self._dependent_closure(current_id)
                if dependant != current_id
            ):
                continue
            try:
                self._shutdown_one(current_id)
            except Exception as exc:
                failures.append(exc)
                failed_plugins.add(current_id)
        if failures:
            raise ExceptionGroup(
                f"One or more plugin shutdown operations failed for {plugin_id!r}.",
                failures,
            )

    def shutdown_all(self) -> None:
        failures: list[BaseException] = []
        failed_plugins: set[str] = set()
        for plugin_id in reversed(self.resolve_order()):
            if not (
                self._registry.contains(plugin_id)
                and self._registry.is_initialized(plugin_id)
            ):
                continue
            if any(
                dependant in failed_plugins
                for dependant in self._dependent_closure(plugin_id)
                if dependant != plugin_id
            ):
                continue
            try:
                self._shutdown_one(plugin_id)
            except Exception as exc:
                failures.append(exc)
                failed_plugins.add(plugin_id)
                continue
        if failures:
            raise ExceptionGroup(
                "One or more plugin shutdown operations failed.",
                failures,
            )

    def unload(self, plugin_id: str) -> Optional[PluginEntry]:
        """Unload one plugin using explicit stage-specific failure operations.

        Unload failure operations are deterministic:
            unload.shutdown
            unload.disable
            unload.unregister

        A failed stage does not emit a later successful lifecycle event.
        The PluginStateStore remains the canonical source of resulting state.
        """
        self._require_definition(plugin_id)
        registered_dependants = tuple(
            dependant
            for dependant in self._dependent_closure(plugin_id)
            if dependant != plugin_id and self._registry.contains(dependant)
        )
        if registered_dependants:
            raise RuntimeError(
                f"Cannot unload plugin {plugin_id!r}; registered dependants remain: "
                f"{', '.join(registered_dependants)}."
            )
        if not self._registry.contains(plugin_id):
            return None

        self._emit(
            plugin_unload_requested(
                plugin_id,
                source=PluginEventSource.MANAGER,
            )
        )
        if self._registry.is_initialized(plugin_id):
            self._shutdown_one(
                plugin_id,
                failure_operation="unload.shutdown",
            )

        if self._registry.is_enabled(plugin_id):
            try:
                self._registry.disable(plugin_id, shutdown=False)
            except Exception as exc:
                self._emit(
                    plugin_failed(
                        plugin_id,
                        exc,
                        operation="unload.disable",
                        recoverable=True,
                        source=PluginEventSource.MANAGER,
                    )
                )
                raise
            self._emit(
                plugin_disabled(
                    plugin_id,
                    source=PluginEventSource.MANAGER,
                )
            )

        entry = self._registry.get_entry(plugin_id)
        try:
            self._registry.unregister(plugin_id, shutdown=False)
        except Exception as exc:
            self._emit(
                plugin_failed(
                    plugin_id,
                    exc,
                    operation="unload.unregister",
                    recoverable=True,
                    source=PluginEventSource.MANAGER,
                )
            )
            raise
        self._emit(plugin_unloaded(plugin_id, source=PluginEventSource.MANAGER))
        return entry

    def resolve_order(self, plugin_ids: Optional[Iterable[str]] = None) -> tuple[str, ...]:
        requested = tuple(self.plugin_ids if plugin_ids is None else plugin_ids)
        for plugin_id in requested:
            self._require_definition(plugin_id)
        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []
        def visit(current_id: str) -> None:
            if current_id in visited:
                return
            if current_id in visiting:
                raise RuntimeError(f"Plugin dependency cycle detected at {current_id!r}.")
            visiting.add(current_id)
            for dependency in self._definitions[current_id].dependencies:
                self._require_definition(dependency)
                visit(dependency)
            visiting.remove(current_id)
            visited.add(current_id)
            order.append(current_id)
        for plugin_id in requested:
            visit(plugin_id)
        return tuple(order)

    def _require_enabled_dependencies(self, plugin_id: str) -> None:
        for dependency in self._definitions[plugin_id].dependencies:
            definition = self._definitions[dependency]
            if not definition.enabled:
                raise RuntimeError(f"Plugin {plugin_id!r} requires disabled dependency {dependency!r}.")
            if not self._registry.is_initialized(dependency):
                raise RuntimeError(f"Plugin dependency {dependency!r} is not initialized.")

    def _dependent_closure(self, plugin_id: str) -> tuple[str, ...]:
        affected: list[str] = [plugin_id]
        changed = True
        while changed:
            changed = False
            for candidate, definition in self._definitions.items():
                if candidate not in affected and any(dep in affected for dep in definition.dependencies):
                    affected.append(candidate)
                    changed = True
        return tuple(affected)

    def _direct_dependants(self, plugin_id: str) -> tuple[str, ...]:
        return tuple(candidate for candidate, definition in self._definitions.items() if plugin_id in definition.dependencies)

    def _rollback_initialization(self, initialized_here: Iterable[str]) -> list[BaseException]:
        failures: list[BaseException] = []
        for plugin_id in reversed(tuple(initialized_here)):
            if not (
                self._registry.contains(plugin_id)
                and self._registry.is_initialized(plugin_id)
            ):
                continue
            metadata = {"rollback": True}
            try:
                self._shutdown_one(plugin_id, metadata=metadata)
            except Exception as exc:
                failures.append(exc)
        return failures

    def _emit(self, event: PluginEvent) -> None:
        self._events.append(event)
        if self._event_sink is not None:
            self._event_sink(event)

    def _require_definition(self, plugin_id: str) -> PluginDefinition:
        self._validate_plugin_id(plugin_id)
        try:
            return self._definitions[plugin_id]
        except KeyError as exc:
            raise KeyError(f"Unknown plugin id: {plugin_id!r}.") from exc

    @staticmethod
    def _validate_plugin_id(plugin_id: str) -> None:
        if not isinstance(plugin_id, str) or not plugin_id.strip():
            raise ValueError("plugin_id must be a non-empty string.")


__all__ = ["PluginDefinition", "PluginManager"]
