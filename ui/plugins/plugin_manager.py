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
- PluginLoader is responsible for explicit concrete-plugin imports.
- PluginRegistry is responsible for registration and lookup.
- PluginManager coordinates loading, construction, initialization,
  shutdown, and lifecycle ordering.
- PluginManager does not discover plugins dynamically.
- PluginManager does not import concrete plugin implementations.
- PluginManager does not own Core/domain state.
- MainWindow remains thin and delegates UI composition to plugins.
- Plugin dependencies are explicit and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

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

    The definition describes orchestration metadata only. It does not
    import or instantiate the concrete plugin.
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


# ============================================================
# PLUGIN MANAGER
# ============================================================


class PluginManager:
    """
    Coordinates the complete lifecycle of UI composition plugins.

    Responsibilities
    ----------------
    1. Maintain explicit plugin definitions.
    2. Resolve dependency ordering.
    3. Ask PluginLoader to import concrete implementations.
    4. Instantiate plugins.
    5. Register them in PluginRegistry.
    6. Initialize them in dependency order.
    7. Shut them down in reverse dependency order.

    Non-responsibilities
    --------------------
    - Plugin discovery.
    - Package scanning.
    - Concrete plugin imports.
    - Core/domain mutation.
    - Tool registration.
    - Renderer registration.
    - Application business logic.
    """

    def __init__(
        self,
        *,
        loader: Optional[
            PluginLoader
        ] = None,
        registry: Optional[
            PluginRegistry
        ] = None,
        definitions: Optional[
            Iterable[PluginDefinition]
        ] = None,
    ) -> None:
        self._loader = (
            loader
            or create_default_plugin_loader()
        )

        self._registry = (
            registry
            or create_plugin_registry()
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
            for definition in definitions:
                self.define(
                    definition
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
        """Return defined plugin IDs."""

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
        Add an explicit plugin definition.

        Defining a plugin does not import, construct, or initialize it.
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

        A definition cannot be removed while the plugin remains
        registered.
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
                    "is already registered."
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
        Define the canonical GridForge UI composition plugins.

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
            if (
                definition.plugin_id
                not in self._definitions
            ):
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
        Set the construction/initialization context for one plugin.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id not in self._definitions:
            raise KeyError(
                (
                    f"Plugin {plugin_id!r} "
                    "has no definition."
                )
            )

        self._contexts[
            plugin_id
        ] = context

    def set_contexts(
        self,
        contexts: Mapping[str, Any],
    ) -> None:
        """Set contexts for multiple plugins."""

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

        self._validate_plugin_id(
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
        Load, construct, and register one plugin.

        The plugin is not initialized by this method.
        """

        definition = self._require_definition(
            plugin_id
        )

        existing = self._registry.get_entry(
            plugin_id
        )

        if existing is not None:
            return existing

        # Explicit dependency validation occurs before construction.
        for dependency in definition.dependencies:
            if dependency not in self._definitions:
                raise KeyError(
                    (
                        f"Plugin {plugin_id!r} "
                        f"depends on undefined plugin "
                        f"{dependency!r}."
                    )
                )

        # Importing concrete implementations is delegated entirely to
        # PluginLoader.
        self._loader.load(
            plugin_id
        )

        context = self._contexts.get(
            plugin_id
        )

        if context is None:
            plugin = self._loader.create(
                plugin_id
            )
        else:
            plugin = self._loader.create(
                plugin_id,
                context=context,
            )

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
        Load multiple plugins in dependency order.
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
        Load and initialize one plugin.

        Dependencies are initialized first.
        """

        order = self.resolve_order(
            (plugin_id,)
        )

        result = None

        for current_id in order:
            entry = self.load(
                current_id
            )

            if not entry.enabled:
                continue

            if not entry.initialized:
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

        Already initialized plugins are left untouched.
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
        Shut down one plugin and its initialized dependants.

        A dependent plugin must not remain active after the plugin it
        depends on has been shut down.
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
        Shut down every initialized plugin in reverse dependency order.
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

        Dependants must be unloaded first.
        """

        self._require_definition(
            plugin_id
        )

        dependants = self._direct_dependants(
            plugin_id
        )

        active_dependants = [
            dependency
            for dependency in dependants
            if self._registry.contains(
                dependency
            )
        ]

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

        Definitions remain available for a subsequent load cycle.
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
        Resolve a deterministic topological initialization order.

        Raises RuntimeError if a dependency cycle is detected.
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
        visiting: set[str] = set()
        result: list[str] = []

        def visit(
            plugin_id: str,
        ) -> None:
            if plugin_id in visited:
                return

            if plugin_id in visiting:
                cycle = " -> ".join(
                    list(
                        visiting
                    )
                    + [plugin_id]
                )

                raise RuntimeError(
                    (
                        "Plugin dependency cycle "
                        f"detected: {cycle}"
                    )
                )

            visiting.add(
                plugin_id
            )

            definition = self._definitions[
                plugin_id
            ]

            for dependency in (
                definition.dependencies
            ):
                if dependency not in self._definitions:
                    raise KeyError(
                        (
                            f"Plugin "
                            f"{plugin_id!r} depends on "
                            f"undefined plugin "
                            f"{dependency!r}."
                        )
                    )

                visit(
                    dependency
                )

            visiting.remove(
                plugin_id
            )

            visited.add(
                plugin_id
            )

            result.append(
                plugin_id
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
        """Return direct dependencies of a plugin."""

        return self._require_definition(
            plugin_id
        ).dependencies

    def dependants(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        """Return direct dependants of a plugin."""

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
            if plugin_id
            in definition.dependencies
        )

    def _dependent_closure(
        self,
        plugin_id: str,
    ) -> tuple[str, ...]:
        """
        Return the requested plugin plus all of its dependants.
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

            for dependant in (
                self._direct_dependants(
                    current_id
                )
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
        """Enable a defined plugin."""

        self._require_definition(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            self._registry.enable(
                plugin_id
            )
            return

        definition = self._definitions[
            plugin_id
        ]

        if not definition.enabled:
            self._definitions[
                plugin_id
            ] = PluginDefinition(
                plugin_id=definition.plugin_id,
                dependencies=definition.dependencies,
                enabled=True,
                metadata=definition.metadata,
            )

    def disable(
        self,
        plugin_id: str,
    ) -> None:
        """
        Disable a plugin.

        If registered and initialized, it is shut down first.
        """

        self._require_definition(
            plugin_id
        )

        if self._registry.contains(
            plugin_id
        ):
            self._registry.disable(
                plugin_id,
                shutdown=True,
            )

        definition = self._definitions[
            plugin_id
        ]

        if definition.enabled:
            self._definitions[
                plugin_id
            ] = PluginDefinition(
                plugin_id=definition.plugin_id,
                dependencies=definition.dependencies,
                enabled=False,
                metadata=definition.metadata,
            )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

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
# DEFAULT MANAGER
# ============================================================


def create_default_plugin_manager(
    *,
    loader: Optional[
        PluginLoader
    ] = None,
    registry: Optional[
        PluginRegistry
    ] = None,
) -> PluginManager:
    """
    Create the canonical GridForge UI plugin manager.

    The manager receives explicit definitions for the four composition
    plugins but does not import or initialize them until requested.
    """

    manager = PluginManager(
        loader=(
            loader
            or create_default_plugin_loader()
        ),
        registry=(
            registry
            or create_plugin_registry()
        ),
    )

    manager.define_defaults()

    return manager


__all__ = [
    "PluginDefinition",
    "PluginManager",
    "create_default_plugin_manager",
]
