"""
GridForge V2
============

File:
    ui/plugins/plugin_manager.py

Purpose
-------
Application-level lifecycle manager for explicitly registered UI
composition plugins.

Architectural rules
-------------------
- PluginLoader owns explicit concrete-plugin imports and construction.
- PluginRegistry owns registered plugin instances and lifecycle state.
- PluginManager owns composition definitions, dependency resolution,
  context assignment, and lifecycle ordering.
- PluginManager does not discover plugins dynamically.
- PluginManager does not import concrete plugin implementations.
- PluginManager does not own Core/domain state.
- PluginManager does not construct Qt widgets directly.
- MainWindow remains thin and delegates UI composition to plugins.
- Plugin dependencies are explicit and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from .plugin_contract import (
    PluginContractError,
    validate_plugin,
)
from .plugin_loader import (
    PluginLoader,
    create_default_plugin_loader,
)
from .plugin_registry import (
    PluginEntry,
    PluginRegistry,
    create_plugin_registry,
)


# ============================================================
# PLUGIN DEFINITION
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    """
    Runtime composition definition for one UI plugin.

    This is orchestration metadata only.

    It does not:
        - import the plugin;
        - instantiate the plugin;
        - initialize the plugin;
        - own plugin state.
    """

    plugin_id: str

    dependencies: tuple[str, ...] = ()

    enabled: bool = True

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.plugin_id,
            str,
        ) or not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if any(
            not isinstance(
                dependency,
                str,
            )
            or not dependency.strip()
            for dependency in self.dependencies
        ):
            raise ValueError(
                "dependencies must contain non-empty strings."
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


# ============================================================
# PLUGIN MANAGER
# ============================================================


class PluginManager:
    """
    Coordinates the lifecycle of explicitly defined UI plugins.

    Responsibilities
    ----------------
    1. Maintain explicit plugin definitions.
    2. Store plugin contexts.
    3. Resolve dependency ordering.
    4. Ask PluginLoader to load concrete implementations.
    5. Ask PluginLoader to construct plugin instances.
    6. Validate the plugin contract.
    7. Register instances in PluginRegistry.
    8. Initialize plugins in dependency order.
    9. Shut down plugins in reverse dependency order.
    10. Unregister plugins safely.

    Non-responsibilities
    --------------------
    - Plugin discovery.
    - Package scanning.
    - Concrete plugin imports.
    - Core/domain state.
    - Tool registration.
    - Renderer registration.
    - MainWindow construction.
    - Qt application ownership.
    """

    def __init__(
        self,
        *,
        loader: Optional[PluginLoader] = None,
        registry: Optional[PluginRegistry] = None,
        definitions: Optional[
            Iterable[PluginDefinition]
        ] = None,
    ) -> None:
        self._loader = (
            loader
            if loader is not None
            else create_default_plugin_loader()
        )

        self._registry = (
            registry
            if registry is not None
            else create_plugin_registry()
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
        """Return the plugin registry."""

        return self._registry

    @property
    def definitions(
        self,
    ) -> tuple[PluginDefinition, ...]:
        """Return definitions in registration order."""

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

        Defining a plugin performs no loading or construction.
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
        """Add multiple explicit plugin definitions."""

        for definition in definitions:
            self.define(
                definition
            )

    def remove_definition(
        self,
        plugin_id: str,
    ) -> None:
        """
        Remove a plugin definition.

        The plugin must not be registered.

        Definitions with dependants cannot be removed because doing so
        would leave an invalid composition graph.
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
                    f"definitions remain: "
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
        Define the canonical GridForge V2 UI composition.

        Dependency graph:

            canvas
              ├── panels
              ├── toolbar
              └── status

            panels ─────┐
            toolbar ────┼──> status

        The concrete classes remain owned by PluginLoader.
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
        Assign the composition context for one plugin.

        The manager stores the reference only. It does not create,
        modify, or validate application services contained in it.
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
        """Assign contexts to multiple explicitly defined plugins."""

        for plugin_id, context in contexts.items():
            self.set_context(
                plugin_id,
                context,
            )

    def context(
        self,
        plugin_id: str,
    ) -> Any:
        """Return the configured context for a plugin."""

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

        Loading does not initialize the plugin.

        Dependencies are loaded first.
        """

        definition = self._require_definition(
            plugin_id
        )

        existing = self._registry.get_entry(
            plugin_id
        )

        if existing is not None:
            return existing

        self._validate_dependencies(
            plugin_id
        )

        # Explicit concrete import remains exclusively owned by loader.
        self._loader.load(
            plugin_id
        )

        context = self._contexts.get(
            plugin_id
        )

        # Construction remains exclusively owned by loader.
        if context is None:
            plugin = self._loader.create(
                plugin_id
            )
        else:
            plugin = self._loader.create(
                plugin_id,
                context=context,
            )

        # Contract validation occurs before registration.
        try:
            validate_plugin(
                plugin,
                plugin_id=plugin_id,
            )
        except (
            PluginContractError,
            TypeError,
            ValueError,
        ):
            raise

        return self._registry.register(
            plugin_id,
            plugin,
            enabled=definition.enabled,
            metadata=dict(
                definition.metadata
            ),
        )

    def load_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> tuple[PluginEntry, ...]:
        """
        Load plugins in deterministic dependency order.
        """

        order = self.resolve_order(
            plugin_ids
        )

        entries: list[
            PluginEntry
        ] = []

        for plugin_id in order:
            entries.append(
                self.load(
                    plugin_id
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
        Load and initialize one plugin and its dependencies.

        Dependencies are initialized before the requested plugin.
        """

        order = self.resolve_order(
            (plugin_id,)
        )

        result: Any = None

        for current_id in order:
            entry = self.load(
                current_id
            )

            if not entry.enabled:
                continue

            if entry.initialized:
                continue

            result = self._registry.initialize(
                current_id,
                context=self._contexts.get(
                    current_id
                ),
            )

        return result

    def initialize_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Initialize plugins in dependency order.

        Already initialized plugins are skipped.
        Disabled plugins are not initialized.
        """

        order = self.resolve_order(
            plugin_ids
        )

        results: list[Any] = []

        for plugin_id in order:
            entry = self.load(
                plugin_id
            )

            if not entry.enabled:
                continue

            if entry.initialized:
                continue

            results.append(
                self._registry.initialize(
                    plugin_id,
                    context=self._contexts.get(
                        plugin_id
                    ),
                )
            )

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
        Shut down a plugin and all initialized dependants.

        Shutdown occurs in reverse dependency order.
        """

        self._require_definition(
            plugin_id
        )

        affected = self._dependent_closure(
            plugin_id
        )

        order = self.resolve_order(
            affected
        )

        for current_id in reversed(
            order
        ):
            entry = self._registry.get_entry(
                current_id
            )

            if (
                entry is not None
                and entry.initialized
            ):
                self._registry.shutdown(
                    current_id
                )

    def shutdown_all(self) -> None:
        """
        Shut down all initialized plugins in reverse dependency order.
        """

        order = self.resolve_order()

        for plugin_id in reversed(
            order
        ):
            entry = self._registry.get_entry(
                plugin_id
            )

            if (
                entry is not None
                and entry.initialized
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
        Shut down and unregister one plugin.

        Registered dependants must be removed first.
        """

        self._require_definition(
            plugin_id
        )

        dependants = self._direct_dependants(
            plugin_id
        )

        active_dependants = tuple(
            dependant
            for dependant in dependants
            if self._registry.contains(
                dependant
            )
        )

        if active_dependants:
            raise RuntimeError(
                (
                    f"Cannot unload plugin "
                    f"{plugin_id!r}; registered "
                    f"dependants remain: "
                    f"{', '.join(active_dependants)}."
                )
            )

        entry = self._registry.get_entry(
            plugin_id
        )

        if entry is None:
            return None

        return self._registry.unregister(
            plugin_id,
            shutdown=True,
        )

    def unload_all(self) -> None:
        """
        Shut down and unregister all plugins in reverse dependency order.

        Definitions remain available for a later load cycle.
        """

        order = self.resolve_order()

        for plugin_id in reversed(
            order
        ):
            if self._registry.contains(
                plugin_id
            ):
                self._registry.unregister(
                    plugin_id,
                    shutdown=True,
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

        Raises
        ------
        KeyError
            If a requested plugin or dependency is undefined.

        RuntimeError
            If a dependency cycle exists.
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
                cycle_start = (
                    visiting.index(
                        current_id
                    )
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
                            f"undefined plugin "
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
        Return a plugin and all of its transitive dependants.
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
        """Return whether a plugin is initialized."""

        if not self._registry.contains(
            plugin_id
        ):
            return False

        return self._registry.is_initialized(
            plugin_id
        )

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is enabled."""

        if not self._registry.contains(
            plugin_id
        ):
            definition = self._require_definition(
                plugin_id
            )

            return definition.enabled

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
        Enable a plugin definition.

        If the plugin is already registered, its registry state is
        enabled as well.
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

        An initialized registered plugin is shut down first.
        """

        definition = self._require_definition(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            self._registry.disable(
                plugin_id,
                shutdown=True,
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
    # INTERNAL VALIDATION
    # ========================================================

    def _validate_dependencies(
        self,
        plugin_id: str,
    ) -> None:
        """
        Validate that all direct dependencies are defined.
        """

        definition = self._require_definition(
            plugin_id
        )

        for dependency in definition.dependencies:
            if dependency not in self._definitions:
                raise KeyError(
                    (
                        f"Plugin "
                        f"{plugin_id!r} depends on "
                        f"undefined plugin "
                        f"{dependency!r}."
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
) -> PluginManager:
    """
    Create the canonical GridForge V2 plugin manager.

    The four canonical composition plugins are explicitly defined,
    but none is imported, constructed, or initialized here.
    """

    manager = PluginManager(
        loader=(
            loader
            if loader is not None
            else create_default_plugin_loader()
        ),
        registry=(
            registry
            if registry is not None
            else create_plugin_registry()
        ),
    )

    manager.define_defaults()

    return manager


__all__ = [
    "PluginDefinition",
    "PluginManager",
    "create_default_plugin_manager",
]
