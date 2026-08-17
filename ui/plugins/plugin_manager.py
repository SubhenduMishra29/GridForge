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
- PluginContext is supplied during plugin initialization, never during
  plugin construction.
- MainWindow remains thin and plugin-driven.
- Plugin dependencies are explicit and deterministic.
- Dependencies are initialized before dependants.
- Dependants are shut down before dependencies.
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
    Declarative runtime definition of one UI composition plugin.

    PluginDefinition contains orchestration metadata only.

    It does not:

        - import a plugin;
        - construct a plugin;
        - initialize a plugin;
        - own plugin state;
        - contain PluginContext.
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

        if any(
            (
                not isinstance(
                    dependency,
                    str,
                )
                or not dependency.strip()
            )
            for dependency in self.dependencies
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
    4. Ask PluginLoader to import concrete implementations.
    5. Ask PluginLoader to construct plugin instances.
    6. Validate plugin contracts.
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

    Lifecycle
    ---------
        define()
            |
            v
        load()
            |
            +--> PluginLoader.load()
            +--> PluginLoader.create()
            +--> validate_plugin()
            +--> PluginRegistry.register()
            |
            v
        initialize()
            |
            +--> PluginRegistry.initialize(context)
            |
            v
        shutdown()
            |
            +--> PluginRegistry.shutdown()
            |
            v
        unload()
            |
            +--> PluginRegistry.unregister()

    Important
    ---------
    PluginContext is an initialization dependency.

    It is deliberately NOT passed to PluginLoader.create().
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

        Defining performs no import, construction, registration,
        or initialization.
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
        Remove an unloaded plugin definition.

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

        Dependencies are orchestration relationships only.
        Concrete implementations remain owned by PluginLoader.
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
        Assign the initialization context for a plugin.

        The context is stored without modification.

        It is consumed only when the plugin is initialized.
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
        """Assign initialization contexts to multiple plugins."""

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

        This method does NOT initialize any plugin.

        IMPORTANT
        ---------
        PluginContext is never passed to PluginLoader.create().
        Context belongs exclusively to the initialization phase.
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
            existing_entry = (
                self._registry.get_entry(
                    current_id
                )
            )

            if existing_entry is not None:
                continue

            definition = self._definitions[
                current_id
            ]

            # Concrete import is exclusively owned by PluginLoader.
            self._loader.load(
                current_id
            )

            # Construction is deliberately context-free.
            plugin = self._loader.create(
                current_id
            )

            # Validate before registration.
            try:
                validate_plugin(
                    plugin,
                    plugin_id=current_id,
                )
            except (
                PluginContractError,
                TypeError,
                ValueError,
            ):
                raise

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
        """
        Load plugins in deterministic dependency order.

        Dependencies are loaded before dependants.
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
        Load and initialize one plugin and all dependencies.

        Initialization occurs in topological dependency order.

        A plugin cannot initialize when one of its dependencies is
        disabled.
        """

        self._require_definition(
            plugin_id
        )

        order = self.resolve_order(
            (plugin_id,)
        )

        result: Any = None

        for current_id in order:
            definition = self._definitions[
                current_id
            ]

            entry = self.load(
                current_id
            )

            if not definition.enabled:
                continue

            self._require_enabled_dependencies(
                current_id
            )

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
        Initialize explicitly requested plugins in dependency order.

        Disabled plugins are skipped.

        A dependent plugin is not initialized if one of its
        dependencies is disabled.
        """

        order = self.resolve_order(
            plugin_ids
        )

        results: list[Any] = []

        for plugin_id in order:
            definition = self._definitions[
                plugin_id
            ]

            entry = self.load(
                plugin_id
            )

            if not definition.enabled:
                continue

            self._require_enabled_dependencies(
                plugin_id
            )

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
        Shut down all initialized plugins.

        Dependants are shut down before dependencies.
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

        A plugin cannot be unloaded while any registered dependant
        remains, including transitive dependants.
        """

        self._require_definition(
            plugin_id
        )

        dependants = self._dependent_closure(
            plugin_id
        )

        registered_dependants = tuple(
            current_id
            for current_id in dependants
            if current_id != plugin_id
            and self._registry.contains(
                current_id
            )
        )

        if registered_dependants:
            raise RuntimeError(
                (
                    f"Cannot unload plugin "
                    f"{plugin_id!r}; registered "
                    f"dependants remain: "
                    f"{', '.join(registered_dependants)}."
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
        Shut down and unregister all registered plugins.

        Definitions remain available for another lifecycle cycle.
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

        Example:

            status
              -> panels
                  -> canvas

        resolves as:

            canvas, panels, status
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
        """Return direct dependants in definition order."""

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

        The result follows definition/dependency traversal order.
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

    def _require_enabled_dependencies(
        self,
        plugin_id: str,
    ) -> None:
        """
        Ensure all direct dependencies are enabled.

        Initialization of a dependant is invalid when a required
        dependency is disabled.
        """

        definition = self._require_definition(
            plugin_id
        )

        disabled = tuple(
            dependency
            for dependency in definition.dependencies
            if not self._definitions[
                dependency
            ].enabled
        )

        if disabled:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} cannot "
                    "be initialized because required "
                    f"dependencies are disabled: "
                    f"{', '.join(disabled)}."
                )
            )

    # ========================================================
    # STATE
    # ========================================================

    def is_registered(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is registered."""

        self._validate_plugin_id(
            plugin_id
        )

        return self._registry.contains(
            plugin_id
        )

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is initialized."""

        self._validate_plugin_id(
            plugin_id
        )

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

        self._validate_plugin_id(
            plugin_id
        )

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
        """Return a registered plugin instance, if present."""

        self._validate_plugin_id(
            plugin_id
        )

        return self._registry.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> Any:
        """Return a registered plugin or raise KeyError."""

        self._validate_plugin_id(
            plugin_id
        )

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

        Enabling does not load or initialize the plugin.
        """

        definition = self._require_definition(
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

        if self._registry.contains(
            plugin_id
        ):
            self._registry.enable(
                plugin_id
            )

    def disable(
        self,
        plugin_id: str,
    ) -> None:
        """
        Disable a plugin.

        A registered plugin is shut down before being disabled.

        Dependants are not automatically disabled; attempting to
        initialize them while this dependency remains disabled will
        fail explicitly.
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

    The four canonical composition plugins are explicitly defined.

    No concrete plugin is imported, constructed, registered, or
    initialized by this factory.
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
