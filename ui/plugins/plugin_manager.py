"""
GridForge V2
============

File:
    ui/plugins/plugin_manager.py

Purpose
-------
Application-level lifecycle manager for explicitly registered UI
composition plugins.

Architectural role
------------------
PluginManager is the orchestration layer for the UI composition plugin
system.

Responsibilities
----------------
    PluginLoader
        Explicit concrete-plugin imports and construction.

    PluginRegistry
        Runtime plugin registration and lifecycle execution.

    PluginStateStore
        Canonical observable runtime lifecycle state.

    PluginManager
        Composition definitions, dependency resolution, context
        assignment, and lifecycle ordering.

    PluginContext
        Dependency carrier supplied during plugin initialization.

Architectural rules
-------------------
- no dynamic plugin discovery;
- no concrete plugin imports;
- no Qt construction;
- no Core/domain ownership;
- no duplicated runtime lifecycle state;
- explicit deterministic dependencies;
- dependencies initialize before dependants;
- dependants shut down before dependencies;
- plugin construction is context-free;
- PluginContext is supplied only during initialization;
- MainWindow remains a thin composition boundary.

Canonical composition
---------------------
    canvas
        ↓
    panels
        ↓
    toolbar
        ↓
    status
        ↓
    shell

Actual dependency graph:

    panels  ──→ canvas
    toolbar ──→ canvas

    status  ──→ canvas
               panels
               toolbar

    shell   ──→ canvas
               panels
               toolbar
               status

The canvas remains the central visual capability and the SLD workflow
remains a first-class current UI capability.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from types import MappingProxyType
from typing import (
    Any,
    Iterable,
    Mapping,
    Optional,
)

from .plugin_contract import validate_plugin
from .plugin_loader import (
    PluginLoader,
    create_default_plugin_loader,
)
from .plugin_registry import (
    PluginEntry,
    PluginRegistry,
    create_plugin_registry,
)
from .plugin_state import PluginStateStore


# ============================================================
# PLUGIN DEFINITION
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    """
    Declarative composition definition for one UI plugin.

    This object contains configuration only.

    Runtime lifecycle state belongs exclusively to PluginStateStore.
    """

    plugin_id: str

    dependencies: tuple[str, ...] = ()

    enabled: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(
                self.plugin_id,
                str,
            )
            or not self.plugin_id.strip()
        ):
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if not isinstance(
            self.dependencies,
            tuple,
        ):
            raise TypeError(
                "dependencies must be a tuple."
            )

        for dependency in self.dependencies:
            if (
                not isinstance(
                    dependency,
                    str,
                )
                or not dependency.strip()
            ):
                raise ValueError(
                    "dependencies must contain non-empty strings."
                )

        if len(
            set(self.dependencies)
        ) != len(
            self.dependencies
        ):
            raise ValueError(
                "dependencies cannot contain duplicates."
            )

        if self.plugin_id in self.dependencies:
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} "
                    "cannot depend on itself."
                )
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


# ============================================================
# PLUGIN MANAGER
# ============================================================


class PluginManager:
    """
    Coordinates explicitly defined GridForge V2 UI plugins.

    PluginManager owns orchestration only.

    It does not maintain runtime lifecycle state.

    Canonical runtime state is obtained from PluginRegistry /
    PluginStateStore.
    """

    def __init__(
        self,
        *,
        loader: Optional[PluginLoader] = None,
        registry: Optional[PluginRegistry] = None,
        state_store: Optional[PluginStateStore] = None,
        definitions: Optional[
            Iterable[PluginDefinition]
        ] = None,
    ) -> None:
        self._loader = (
            loader
            if loader is not None
            else create_default_plugin_loader()
        )

        if not isinstance(
            self._loader,
            PluginLoader,
        ):
            raise TypeError(
                "loader must be a PluginLoader."
            )

        # ----------------------------------------------------
        # Registry owns the canonical state store.
        # ----------------------------------------------------

        if registry is not None:
            if not isinstance(
                registry,
                PluginRegistry,
            ):
                raise TypeError(
                    "registry must be a PluginRegistry."
                )

            self._registry = registry

            registry_state_store = (
                registry.state_store
            )

            if (
                state_store is not None
                and state_store is not registry_state_store
            ):
                raise ValueError(
                    (
                        "state_store must be the same "
                        "PluginStateStore instance owned by "
                        "the supplied registry."
                    )
                )

            self._state_store = (
                registry_state_store
            )

        else:
            self._state_store = (
                state_store
                if state_store is not None
                else PluginStateStore()
            )

            if not isinstance(
                self._state_store,
                PluginStateStore,
            ):
                raise TypeError(
                    "state_store must be a PluginStateStore."
                )

            self._registry = (
                create_plugin_registry(
                    state_store=self._state_store
                )
            )

        self._definitions: dict[
            str,
            PluginDefinition,
        ] = {}

        self._contexts: dict[
            str,
            Any,
        ] = {}

        if definitions is not None:
            self.define_many(
                definitions
            )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def loader(self) -> PluginLoader:
        """Return the explicit plugin loader."""

        return self._loader

    @property
    def registry(self) -> PluginRegistry:
        """Return the runtime plugin registry."""

        return self._registry

    @property
    def state_store(self) -> PluginStateStore:
        """
        Return the canonical runtime state store.
        """

        return self._state_store

    @property
    def definitions(
        self,
    ) -> tuple[PluginDefinition, ...]:
        """Return definitions in declaration order."""

        return tuple(
            self._definitions.values()
        )

    @property
    def plugin_ids(
        self,
    ) -> tuple[str, ...]:
        """Return explicitly defined plugin IDs."""

        return tuple(
            self._definitions.keys()
        )

    # ========================================================
    # DEFINITION
    # ========================================================

    def define(
        self,
        definition: PluginDefinition,
    ) -> None:
        """
        Add one explicit plugin definition.

        No runtime lifecycle operation occurs.
        """

        if not isinstance(
            definition,
            PluginDefinition,
        ):
            raise TypeError(
                "definition must be PluginDefinition."
            )

        plugin_id = definition.plugin_id

        if plugin_id in self._definitions:
            raise ValueError(
                (
                    f"Plugin definition "
                    f"{plugin_id!r} already exists."
                )
            )

        self._definitions[
            plugin_id
        ] = definition

    def define_many(
        self,
        definitions: Iterable[
            PluginDefinition
        ],
    ) -> None:
        """Add multiple explicit definitions."""

        for definition in definitions:
            self.define(
                definition
            )

    def remove_definition(
        self,
        plugin_id: str,
    ) -> None:
        """
        Remove an unused plugin definition.

        A definition cannot be removed while:

        - the plugin is registered; or
        - another definition depends on it.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is currently registered."
                )
            )

        dependants = self._direct_dependants(
            plugin_id
        )

        if dependants:
            raise RuntimeError(
                (
                    f"Cannot remove plugin "
                    f"{plugin_id!r}; dependent "
                    "definitions remain: "
                    f"{', '.join(dependants)}."
                )
            )

        self._definitions.pop(
            plugin_id,
            None,
        )

        self._contexts.pop(
            plugin_id,
            None,
        )

    # ========================================================
    # DEFAULT DEFINITIONS
    # ========================================================

    def define_defaults(self) -> None:
        """
        Define the canonical GridForge V2 composition.
        """

        defaults = (
            PluginDefinition(
                plugin_id="canvas",
            ),
            PluginDefinition(
                plugin_id="panels",
                dependencies=("canvas",),
            ),
            PluginDefinition(
                plugin_id="toolbar",
                dependencies=("canvas",),
            ),
            PluginDefinition(
                plugin_id="status",
                dependencies=(
                    "canvas",
                    "panels",
                    "toolbar",
                ),
            ),
            PluginDefinition(
                plugin_id="shell",
                dependencies=(
                    "canvas",
                    "panels",
                    "toolbar",
                    "status",
                ),
            ),
        )

        for definition in defaults:
            if definition.plugin_id not in self._definitions:
                self.define(
                    definition
                )

    # ========================================================
    # CONTEXT
    # ========================================================

    def set_context(
        self,
        plugin_id: str,
        context: Any,
    ) -> None:
        """
        Assign initialization context for one plugin.

        The manager stores the supplied reference only.
        """

        self._require_definition(
            plugin_id
        )

        self._contexts[
            plugin_id
        ] = context

    def set_contexts(
        self,
        contexts: Mapping[str, Any],
    ) -> None:
        """Assign contexts to multiple plugins."""

        if not isinstance(
            contexts,
            Mapping,
        ):
            raise TypeError(
                "contexts must be a Mapping."
            )

        for plugin_id, context in contexts.items():
            self.set_context(
                plugin_id,
                context,
            )

    def context(
        self,
        plugin_id: str,
    ) -> Any:
        """Return the configured initialization context."""

        self._require_definition(
            plugin_id
        )

        return self._contexts.get(
            plugin_id
        )

    # ========================================================
    # LOAD
    # ========================================================

    def load(
        self,
        plugin_id: str,
    ) -> PluginEntry:
        """
        Load, construct, validate, and register one plugin.

        Dependencies are loaded first.

        No plugin is initialized.
        """

        self._require_definition(
            plugin_id
        )

        existing = self._registry.get_entry(
            plugin_id
        )

        if existing is not None:
            return existing

        order = self.resolve_order(
            (plugin_id,)
        )

        for current_id in order:
            if self._registry.contains(
                current_id
            ):
                continue

            definition = self._definitions[
                current_id
            ]

            plugin = self._loader.create(
                current_id
            )

            validate_plugin(
                plugin,
                plugin_id=current_id,
            )

            self._registry.register(
                current_id,
                plugin,
                enabled=definition.enabled,
                metadata=dict(
                    definition.metadata
                ),
            )

        entry = self._registry.get_entry(
            plugin_id
        )

        if entry is None:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "was not registered after loading."
                )
            )

        return entry

    def load_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> tuple[PluginEntry, ...]:
        """Load plugins in deterministic dependency order."""

        order = self.resolve_order(
            plugin_ids
        )

        entries: list[
            PluginEntry
        ] = []

        for current_id in order:
            entries.append(
                self.load(
                    current_id
                )
            )

        return tuple(
            entries
        )

    def load_all(
        self,
    ) -> tuple[PluginEntry, ...]:
        """Load all explicitly defined plugins."""

        return self.load_many()

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        plugin_id: str,
    ) -> Any:
        """
        Initialize one plugin and its dependencies.

        Dependencies initialize before dependants.

        Initialization is transactional for this operation:

        - already-initialized plugins are untouched;
        - plugins initialized by this call are tracked;
        - if a later initialization fails, those newly initialized
          plugins are shut down in reverse order.
        """

        self._require_definition(
            plugin_id
        )

        order = self.resolve_order(
            (plugin_id,)
        )

        initialized_here: list[str] = []
        result: Any = None

        try:
            for current_id in order:
                definition = self._definitions[
                    current_id
                ]

                self.load(
                    current_id
                )

                if not definition.enabled:
                    continue

                self._require_enabled_dependencies(
                    current_id
                )

                if not self._registry.is_enabled(
                    current_id
                ):
                    raise RuntimeError(
                        (
                            f"Plugin {current_id!r} "
                            "is runtime-disabled."
                        )
                    )

                if self._registry.is_initialized(
                    current_id
                ):
                    continue

                result = self._registry.initialize(
                    current_id,
                    context=self._contexts.get(
                        current_id
                    ),
                )

                initialized_here.append(
                    current_id
                )

        except Exception:
            self._rollback_initialization(
                initialized_here
            )
            raise

        return result

    def initialize_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Initialize plugins in deterministic dependency order.

        If initialization fails, plugins initialized by this operation
        are shut down in reverse order.
        """

        order = self.resolve_order(
            plugin_ids
        )

        results: list[Any] = []
        initialized_here: list[str] = []

        try:
            for current_id in order:
                definition = self._definitions[
                    current_id
                ]

                self.load(
                    current_id
                )

                if not definition.enabled:
                    continue

                self._require_enabled_dependencies(
                    current_id
                )

                if not self._registry.is_enabled(
                    current_id
                ):
                    raise RuntimeError(
                        (
                            f"Plugin {current_id!r} "
                            "is runtime-disabled."
                        )
                    )

                if self._registry.is_initialized(
                    current_id
                ):
                    continue

                results.append(
                    self._registry.initialize(
                        current_id,
                        context=self._contexts.get(
                            current_id
                        ),
                    )
                )

                initialized_here.append(
                    current_id
                )

        except Exception:
            self._rollback_initialization(
                initialized_here
            )
            raise

        return tuple(
            results
        )

    def initialize_all(
        self,
    ) -> tuple[Any, ...]:
        """Initialize all explicitly defined plugins."""

        return self.initialize_many()

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def shutdown(
        self,
        plugin_id: str,
    ) -> None:
        """
        Shut down one plugin and all initialized dependants.

        Dependants are shut down before dependencies.

        A shutdown failure is propagated and remaining lifecycle state
        is preserved in PluginStateStore.
        """

        self._require_definition(
            plugin_id
        )

        affected = set(
            self._dependent_closure(
                plugin_id
            )
        )

        order = tuple(
            current_id
            for current_id in self.resolve_order()
            if current_id in affected
        )

        for current_id in reversed(
            order
        ):
            if (
                self._registry.contains(
                    current_id
                )
                and self._registry.is_initialized(
                    current_id
                )
            ):
                self._registry.shutdown(
                    current_id
                )

    def shutdown_all(self) -> None:
        """
        Shut down all initialized plugins in reverse dependency order.
        """

        for plugin_id in reversed(
            self.resolve_order()
        ):
            if (
                self._registry.contains(
                    plugin_id
                )
                and self._registry.is_initialized(
                    plugin_id
                )
            ):
                self._registry.shutdown(
                    plugin_id
                )

    # ========================================================
    # UNLOAD
    # ========================================================

    def unload(
        self,
        plugin_id: str,
    ) -> Optional[PluginEntry]:
        """
        Shut down, disable, and unregister one plugin.

        Registered dependants must be removed first.

        The declarative definition remains intact.
        """

        self._require_definition(
            plugin_id
        )

        registered_dependants = tuple(
            dependant
            for dependant in self._dependent_closure(
                plugin_id
            )
            if (
                dependant != plugin_id
                and self._registry.contains(
                    dependant
                )
            )
        )

        if registered_dependants:
            raise RuntimeError(
                (
                    f"Cannot unload plugin "
                    f"{plugin_id!r}; registered "
                    "dependants remain: "
                    f"{', '.join(registered_dependants)}."
                )
            )

        if not self._registry.contains(
            plugin_id
        ):
            return None

        if self._registry.is_initialized(
            plugin_id
        ):
            self._registry.shutdown(
                plugin_id
            )

        if self._registry.is_enabled(
            plugin_id
        ):
            self._registry.disable(
                plugin_id,
                shutdown=False,
            )

        return self._registry.unregister(
            plugin_id,
            shutdown=False,
        )

    def unload_all(self) -> None:
        """
        Shut down, disable, and unregister all registered plugins.

        Reverse dependency order is enforced.
        """

        for plugin_id in reversed(
            self.resolve_order()
        ):
            if not self._registry.contains(
                plugin_id
            ):
                continue

            if self._registry.is_initialized(
                plugin_id
            ):
                self._registry.shutdown(
                    plugin_id
                )

            if self._registry.is_enabled(
                plugin_id
            ):
                self._registry.disable(
                    plugin_id,
                    shutdown=False,
                )

            self._registry.unregister(
                plugin_id,
                shutdown=False,
            )

    # ========================================================
    # DEPENDENCY RESOLUTION
    # ========================================================

    def resolve_order(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> tuple[str, ...]:
        """
        Resolve deterministic topological dependency order.

        Dependencies always precede dependants.
        """

        requested = (
            tuple(
                self._definitions.keys()
            )
            if plugin_ids is None
            else tuple(
                plugin_ids
            )
        )

        for plugin_id in requested:
            self._require_definition(
                plugin_id
            )

        visited: set[str] = set()
        visiting: list[str] = []
        result: list[str] = []

        def visit(
            current_id: str,
        ) -> None:
            if current_id in visited:
                return

            if current_id in visiting:
                cycle_start = visiting.index(
                    current_id
                )

                cycle = (
                    visiting[
                        cycle_start:
                    ]
                    + [current_id]
                )

                raise RuntimeError(
                    (
                        "Plugin dependency cycle "
                        "detected: "
                        + " -> ".join(
                            cycle
                        )
                    )
                )

            visiting.append(
                current_id
            )

            definition = self._definitions[
                current_id
            ]

            for dependency in definition.dependencies:
                if dependency not in self._definitions:
                    raise KeyError(
                        (
                            f"Plugin "
                            f"{current_id!r} depends on "
                            "undefined plugin "
                            f"{dependency!r}."
                        )
                    )

                visit(
                    dependency
                )

            visiting.pop()

            visited.add(
                current_id
            )

            result.append(
                current_id
            )

        for plugin_id in requested:
            visit(
                plugin_id
            )

        return tuple(
            result
        )

    # ========================================================
    # DEPENDENCY QUERIES
    # ========================================================

    def dependencies(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        """Return direct dependencies."""

        return self._require_definition(
            plugin_id
        ).dependencies

    def dependants(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        """Return direct dependants."""

        self._require_definition(
            plugin_id
        )

        return self._direct_dependants(
            plugin_id
        )

    def _direct_dependants(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        return tuple(
            definition.plugin_id
            for definition in self._definitions.values()
            if plugin_id in definition.dependencies
        )

    def _dependent_closure(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        """
        Return the plugin and all transitive dependants.

        Definition order is preserved.
        """

        result: list[str] = []
        visited: set[str] = set()

        def visit(
            current_id: str,
        ) -> None:
            if current_id in visited:
                return

            visited.add(
                current_id
            )

            result.append(
                current_id
            )

            for dependant in self._direct_dependants(
                current_id
            ):
                visit(
                    dependant
                )

        visit(
            plugin_id
        )

        return tuple(
            result
        )

    # ========================================================
    # STATE
    # ========================================================

    def is_registered(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is registered."""

        return self._registry.contains(
            plugin_id
        )

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical runtime initialization state."""

        if not self._registry.contains(
            plugin_id
        ):
            self._require_definition(
                plugin_id
            )
            return False

        return self._registry.is_initialized(
            plugin_id
        )

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """
        Return effective enablement.

        For an unloaded plugin, the declarative definition determines
        the desired enablement.

        For a registered plugin, PluginStateStore determines the actual
        runtime enablement.
        """

        if not self._registry.contains(
            plugin_id
        ):
            return self._require_definition(
                plugin_id
            ).enabled

        return self._registry.is_enabled(
            plugin_id
        )

    def get(
        self,
        plugin_id: str,
    ) -> Optional[Any]:
        """Return a registered plugin instance."""

        return self._registry.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> Any:
        """Return a registered plugin or raise KeyError."""

        return self._registry.require(
            plugin_id
        )

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(
        self,
        plugin_id: str,
    ) -> None:
        """
        Enable a plugin.

        Enabling does not initialize it.

        The declarative definition is updated so that a future load
        cycle uses the same enablement policy.
        """

        definition = self._require_definition(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            self._registry.enable(
                plugin_id
            )

        if not definition.enabled:
            self._definitions[
                plugin_id
            ] = PluginDefinition(
                plugin_id=definition.plugin_id,
                dependencies=definition.dependencies,
                enabled=True,
                metadata=dict(
                    definition.metadata
                ),
            )

    def disable(
        self,
        plugin_id: str,
    ) -> None:
        """
        Disable a plugin.

        Initialized registered dependants are shut down first.

        The target plugin is then shut down, if necessary, and disabled
        through the registry exactly once.
        """

        definition = self._require_definition(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            self.shutdown(
                plugin_id
            )

            if self._registry.is_enabled(
                plugin_id
            ):
                self._registry.disable(
                    plugin_id,
                    shutdown=False,
                )

        if definition.enabled:
            self._definitions[
                plugin_id
            ] = PluginDefinition(
                plugin_id=definition.plugin_id,
                dependencies=definition.dependencies,
                enabled=False,
                metadata=dict(
                    definition.metadata
                ),
            )

    # ========================================================
    # INTERNAL INITIALIZATION ROLLBACK
    # ========================================================

    def _rollback_initialization(
        self,
        initialized_plugin_ids: Iterable[str],
    ) -> None:
        """
        Roll back plugins initialized by the current operation.

        Shutdown occurs in reverse initialization order.

        If rollback itself fails, the original initialization exception
        remains the exception propagated by the caller. PluginRegistry
        records the rollback failure in canonical state.
        """

        for plugin_id in reversed(
            tuple(initialized_plugin_ids)
        ):
            if not self._registry.contains(
                plugin_id
            ):
                continue

            if not self._registry.is_initialized(
                plugin_id
            ):
                continue

            try:
                self._registry.shutdown(
                    plugin_id
                )
            except Exception:
                # Preserve the original initialization failure.
                # PluginStateStore remains authoritative regarding the
                # resulting runtime state.
                continue

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    def _validate_dependencies(
        self,
        plugin_id: str,
    ) -> None:
        """Validate that all direct dependencies are defined."""

        definition = self._require_definition(
            plugin_id
        )

        for dependency in definition.dependencies:
            if dependency not in self._definitions:
                raise KeyError(
                    (
                        f"Plugin "
                        f"{plugin_id!r} depends on "
                        "undefined plugin "
                        f"{dependency!r}."
                    )
                )

    def _require_enabled_dependencies(
        self,
        plugin_id: str,
    ) -> None:
        """
        Ensure all required dependencies are definition-enabled and
        runtime-enabled when registered.
        """

        definition = self._require_definition(
            plugin_id
        )

        disabled: list[str] = []

        for dependency in definition.dependencies:
            dependency_definition = self._definitions[
                dependency
            ]

            if not dependency_definition.enabled:
                disabled.append(
                    dependency
                )
                continue

            if (
                self._registry.contains(
                    dependency
                )
                and not self._registry.is_enabled(
                    dependency
                )
            ):
                disabled.append(
                    dependency
                )

        if disabled:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} cannot "
                    "be initialized because required "
                    "dependencies are disabled: "
                    f"{', '.join(disabled)}."
                )
            )

    def _require_definition(
        self,
        plugin_id: str,
    ) -> PluginDefinition:
        """Return a definition or raise KeyError."""

        self._validate_plugin_id(
            plugin_id
        )

        definition = self._definitions.get(
            plugin_id
        )

        if definition is None:
            raise KeyError(
                (
                    f"Plugin definition "
                    f"{plugin_id!r} does not exist."
                )
            )

        return definition

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> None:
        """Validate a plugin identifier."""

        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not plugin_id.strip():
            raise ValueError(
                "plugin_id cannot be empty."
            )


# ============================================================
# FACTORY
# ============================================================


def create_default_plugin_manager(
    *,
    loader: Optional[PluginLoader] = None,
    registry: Optional[PluginRegistry] = None,
    state_store: Optional[PluginStateStore] = None,
) -> PluginManager:
    """
    Create the canonical GridForge V2 PluginManager.

    Exactly five composition plugins are defined:

        canvas
        panels
        toolbar
        status
        shell

    No plugin is loaded or constructed by this factory.
    """

    manager = PluginManager(
        loader=(
            loader
            if loader is not None
            else create_default_plugin_loader()
        ),
        registry=registry,
        state_store=state_store,
    )

    manager.define_defaults()

    return manager


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginDefinition",
    "PluginManager",
    "create_default_plugin_manager",
]
