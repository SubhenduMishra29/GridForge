"""
GridForge V2
============

File:
    ui/plugins/plugin_loader.py

Purpose
-------
Explicit loader and constructor for GridForge UI composition plugins.

Architectural role
------------------
PluginLoader is the concrete implementation boundary.

It is responsible only for:

    1. holding explicit plugin implementation definitions;
    2. importing explicitly named plugin modules;
    3. resolving explicitly named classes/factories;
    4. constructing plugin instances;
    5. validating constructed plugin instances.

It does NOT:

    - discover plugins;
    - scan packages;
    - infer implementations;
    - resolve dependencies;
    - determine lifecycle ordering;
    - register plugins;
    - initialize plugins;
    - shut down plugins;
    - create PluginContext;
    - own PluginStateStore;
    - own PluginRegistry;
    - compose the UI;
    - create Qt application objects.

Lifecycle boundary
------------------

    PluginLoader
        │
        ├── load()
        │      import + resolve implementation
        │
        └── create()
               construct + validate instance
                         │
                         ▼
                  PluginRegistry
                         │
                         ├── register()
                         ├── initialize(context)
                         └── shutdown()

PluginContext
-------------
PluginContext is NEVER a constructor dependency.

It is supplied by PluginManager through PluginRegistry during
plugin initialization.

Construction must therefore remain context-free.

Canonical GridForge V2 composition plugins
------------------------------------------
    canvas
    panels
    toolbar
    status
    shell

The shell is the final UI composition plugin.

The SLD/canvas subsystem remains a first-class current capability.
The loader does not special-case it; it explicitly loads the canvas
composition plugin like every other composition plugin.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping

from .plugin_contract import validate_plugin


# ============================================================
# PLUGIN IMPLEMENTATION
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginImplementation:
    """
    Explicit definition of one concrete plugin implementation.

    Exactly one construction mechanism must be specified:

        class_name
            OR
        factory_name

    No implementation name is inferred from plugin_id.
    """

    plugin_id: str
    module_name: str

    class_name: str | None = None
    factory_name: str | None = None

    def __post_init__(self) -> None:
        self._validate_plugin_id(
            self.plugin_id
        )

        self._validate_module_name(
            self.module_name
        )

        if (
            self.class_name is not None
            and not isinstance(
                self.class_name,
                str,
            )
        ):
            raise TypeError(
                "class_name must be a string or None."
            )

        if (
            self.class_name is not None
            and not self.class_name.strip()
        ):
            raise ValueError(
                "class_name cannot be empty."
            )

        if (
            self.factory_name is not None
            and not isinstance(
                self.factory_name,
                str,
            )
        ):
            raise TypeError(
                "factory_name must be a string or None."
            )

        if (
            self.factory_name is not None
            and not self.factory_name.strip()
        ):
            raise ValueError(
                "factory_name cannot be empty."
            )

        if (
            self.class_name is None
            and self.factory_name is None
        ):
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} must "
                    "declare either class_name or "
                    "factory_name."
                )
            )

        if (
            self.class_name is not None
            and self.factory_name is not None
        ):
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} cannot "
                    "declare both class_name and "
                    "factory_name."
                )
            )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> None:
        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

    @staticmethod
    def _validate_module_name(
        module_name: str,
    ) -> None:
        if not isinstance(
            module_name,
            str,
        ):
            raise TypeError(
                "module_name must be a string."
            )

        if not module_name.strip():
            raise ValueError(
                "module_name cannot be empty."
            )

        parts = module_name.split(".")

        if any(
            not part or not part.isidentifier()
            for part in parts
        ):
            raise ValueError(
                f"Invalid module name: {module_name!r}."
            )


# ============================================================
# LOADED PLUGIN
# ============================================================


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """
    Immutable descriptor for a resolved implementation.

    This is implementation metadata only.

    It does NOT contain:

        - plugin instance;
        - lifecycle state;
        - PluginContext;
        - dependency state.
    """

    plugin_id: str
    module_name: str

    plugin_class: type[Any] | None = None

    factory: Callable[..., Any] | None = None

    module: ModuleType | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        PluginImplementation._validate_module_name(
            self.module_name
        )

        if (
            self.plugin_class is not None
            and not isinstance(
                self.plugin_class,
                type,
            )
        ):
            raise TypeError(
                "plugin_class must be a class or None."
            )

        if (
            self.factory is not None
            and not callable(
                self.factory
            )
        ):
            raise TypeError(
                "factory must be callable or None."
            )

        if (
            self.plugin_class is None
            and self.factory is None
        ):
            raise ValueError(
                (
                    f"Loaded plugin {self.plugin_id!r} "
                    "must expose either a plugin class "
                    "or factory."
                )
            )

        if (
            self.plugin_class is not None
            and self.factory is not None
        ):
            raise ValueError(
                (
                    f"Loaded plugin {self.plugin_id!r} "
                    "cannot expose both a plugin class "
                    "and factory."
                )
            )


# ============================================================
# CANONICAL IMPLEMENTATIONS
# ============================================================


DEFAULT_PLUGIN_IMPLEMENTATIONS: Mapping[
    str,
    PluginImplementation,
] = {
    "canvas": PluginImplementation(
        plugin_id="canvas",
        module_name="ui.plugins.canvas_plugin",
        class_name="CanvasPlugin",
    ),

    "panels": PluginImplementation(
        plugin_id="panels",
        module_name="ui.plugins.panels_plugin",
        class_name="PanelsPlugin",
    ),

    "toolbar": PluginImplementation(
        plugin_id="toolbar",
        module_name="ui.plugins.toolbar_plugin",
        class_name="ToolbarPlugin",
    ),

    "status": PluginImplementation(
        plugin_id="status",
        module_name="ui.plugins.status_plugin",
        class_name="StatusPlugin",
    ),

    "shell": PluginImplementation(
        plugin_id="shell",
        module_name="ui.plugins.shell_plugin",
        class_name="ShellPlugin",
    ),
}


# ============================================================
# EXPLICIT COMPATIBILITY MAPS
# ============================================================


DEFAULT_PLUGIN_MODULES: Mapping[
    str,
    str,
] = {
    plugin_id: definition.module_name
    for plugin_id, definition
    in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
}


DEFAULT_PLUGIN_CLASSES: Mapping[
    str,
    str,
] = {
    plugin_id: definition.class_name
    for plugin_id, definition
    in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
    if definition.class_name is not None
}


DEFAULT_PLUGIN_FACTORIES: Mapping[
    str,
    str,
] = {
    plugin_id: definition.factory_name
    for plugin_id, definition
    in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
    if definition.factory_name is not None
}


# ============================================================
# PLUGIN LOADER
# ============================================================


class PluginLoader:
    """
    Explicit GridForge V2 plugin implementation loader.

    The loader knows only about explicit definitions.

    It does not discover plugins and does not perform lifecycle
    orchestration.
    """

    def __init__(
        self,
        definitions: Mapping[
            str,
            PluginImplementation,
        ] | None = None,
    ) -> None:

        source = (
            DEFAULT_PLUGIN_IMPLEMENTATIONS
            if definitions is None
            else definitions
        )

        if not isinstance(
            source,
            Mapping,
        ):
            raise TypeError(
                "definitions must be a Mapping."
            )

        self._definitions: dict[
            str,
            PluginImplementation,
        ] = {}

        self._loaded: dict[
            str,
            LoadedPlugin,
        ] = {}

        for plugin_id, definition in source.items():

            if not isinstance(
                plugin_id,
                str,
            ):
                raise TypeError(
                    "Plugin definition keys must be strings."
                )

            if not isinstance(
                definition,
                PluginImplementation,
            ):
                raise TypeError(
                    (
                        f"Definition for plugin "
                        f"{plugin_id!r} must be "
                        "PluginImplementation."
                    )
                )

            if definition.plugin_id != plugin_id:
                raise ValueError(
                    (
                        f"Plugin definition key "
                        f"{plugin_id!r} does not match "
                        f"definition.plugin_id="
                        f"{definition.plugin_id!r}."
                    )
                )

            self.define(
                definition
            )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def definitions(
        self,
    ) -> Mapping[
        str,
        PluginImplementation,
    ]:
        """Return a defensive snapshot of definitions."""

        return dict(
            self._definitions
        )

    @property
    def loaded_ids(
        self,
    ) -> tuple[str, ...]:
        """Return loaded plugin IDs in load order."""

        return tuple(
            self._loaded.keys()
        )

    @property
    def loaded_plugins(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """Return loaded descriptors in load order."""

        return tuple(
            self._loaded.values()
        )

    # ========================================================
    # DEFINITIONS
    # ========================================================

    def define(
        self,
        definition: PluginImplementation,
    ) -> None:
        """Add one explicit implementation definition."""

        if not isinstance(
            definition,
            PluginImplementation,
        ):
            raise TypeError(
                "definition must be PluginImplementation."
            )

        plugin_id = definition.plugin_id

        if plugin_id in self._definitions:
            raise ValueError(
                (
                    f"Plugin definition {plugin_id!r} "
                    "already exists."
                )
            )

        self._definitions[
            plugin_id
        ] = definition

    def remove_definition(
        self,
        plugin_id: str,
    ) -> None:
        """
        Remove an unloaded implementation definition.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id in self._loaded:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} is already "
                    "loaded."
                )
            )

        self._definitions.pop(
            plugin_id,
            None,
        )

    # ========================================================
    # LOAD
    # ========================================================

    def load(
        self,
        plugin_id: str,
    ) -> LoadedPlugin:
        """
        Import and resolve one explicitly defined plugin.

        No construction or lifecycle operation occurs here.
        """

        self._validate_plugin_id(
            plugin_id
        )

        existing = self._loaded.get(
            plugin_id
        )

        if existing is not None:
            return existing

        definition = self._definitions.get(
            plugin_id
        )

        if definition is None:
            raise KeyError(
                (
                    f"No explicit plugin definition "
                    f"exists for {plugin_id!r}."
                )
            )

        module = import_module(
            definition.module_name
        )

        if definition.class_name is not None:
            plugin_class = (
                self._resolve_plugin_class(
                    definition,
                    module,
                )
            )

            descriptor = LoadedPlugin(
                plugin_id=definition.plugin_id,
                module_name=definition.module_name,
                plugin_class=plugin_class,
                module=module,
            )

        else:
            factory = (
                self._resolve_factory(
                    definition,
                    module,
                )
            )

            descriptor = LoadedPlugin(
                plugin_id=definition.plugin_id,
                module_name=definition.module_name,
                factory=factory,
                module=module,
            )

        self._loaded[
            plugin_id
        ] = descriptor

        return descriptor

    def load_many(
        self,
        plugin_ids: Iterable[str],
    ) -> tuple[LoadedPlugin, ...]:
        """Load explicit plugins in caller-supplied order."""

        return tuple(
            self.load(plugin_id)
            for plugin_id in plugin_ids
        )

    def load_all(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """Load all explicitly defined plugins in definition order."""

        return self.load_many(
            self._definitions.keys()
        )

    # ========================================================
    # CONSTRUCTION
    # ========================================================

    def create(
        self,
        plugin_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Construct and validate one plugin instance.

        PluginContext is forbidden at this boundary.

        Initialization occurs later through PluginRegistry.
        """

        if "context" in kwargs:
            raise TypeError(
                (
                    "PluginContext must not be supplied to "
                    "PluginLoader.create(). "
                    "Context belongs to initialize()."
                )
            )

        descriptor = self.load(
            plugin_id
        )

        plugin = self._construct(
            descriptor,
            args,
            kwargs,
        )

        validate_plugin(
            plugin,
            plugin_id=plugin_id,
        )

        return plugin

    def create_many(
        self,
        plugin_ids: Iterable[str],
        *,
        constructor_args: Mapping[
            str,
            Iterable[Any],
        ] | None = None,
        constructor_kwargs: Mapping[
            str,
            Mapping[str, Any],
        ] | None = None,
    ) -> tuple[Any, ...]:
        """
        Construct multiple plugins.

        Constructor arguments are explicit.

        PluginContext is never created or supplied.
        """

        positional = (
            {}
            if constructor_args is None
            else constructor_args
        )

        keyword = (
            {}
            if constructor_kwargs is None
            else constructor_kwargs
        )

        if not isinstance(
            positional,
            Mapping,
        ):
            raise TypeError(
                "constructor_args must be a Mapping."
            )

        if not isinstance(
            keyword,
            Mapping,
        ):
            raise TypeError(
                "constructor_kwargs must be a Mapping."
            )

        instances: list[Any] = []

        for plugin_id in plugin_ids:

            raw_args = positional.get(
                plugin_id,
                (),
            )

            if isinstance(
                raw_args,
                (str, bytes),
            ):
                raise TypeError(
                    (
                        f"constructor_args[{plugin_id!r}] "
                        "must be an iterable of positional "
                        "arguments."
                    )
                )

            try:
                args = tuple(
                    raw_args
                )
            except TypeError as exc:
                raise TypeError(
                    (
                        f"constructor_args[{plugin_id!r}] "
                        "must be iterable."
                    )
                ) from exc

            raw_kwargs = keyword.get(
                plugin_id,
                {},
            )

            if not isinstance(
                raw_kwargs,
                Mapping,
            ):
                raise TypeError(
                    (
                        f"constructor_kwargs[{plugin_id!r}] "
                        "must be a Mapping."
                    )
                )

            instances.append(
                self.create(
                    plugin_id,
                    *args,
                    **dict(raw_kwargs),
                )
            )

        return tuple(
            instances
        )

    # ========================================================
    # INTERNAL CONSTRUCTION
    # ========================================================

    @staticmethod
    def _construct(
        descriptor: LoadedPlugin,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """Construct through the explicitly resolved mechanism."""

        if descriptor.plugin_class is not None:
            return descriptor.plugin_class(
                *args,
                **dict(kwargs),
            )

        if descriptor.factory is not None:
            return descriptor.factory(
                *args,
                **dict(kwargs),
            )

        raise RuntimeError(
            (
                f"Loaded plugin {descriptor.plugin_id!r} "
                "has no construction mechanism."
            )
        )

    # ========================================================
    # QUERY
    # ========================================================

    def is_loaded(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether an implementation is loaded."""

        self._validate_plugin_id(
            plugin_id
        )

        return plugin_id in self._loaded

    def get(
        self,
        plugin_id: str,
    ) -> LoadedPlugin | None:
        """Return a loaded descriptor, if present."""

        self._validate_plugin_id(
            plugin_id
        )

        return self._loaded.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> LoadedPlugin:
        """Return a loaded descriptor or raise KeyError."""

        self._validate_plugin_id(
            plugin_id
        )

        descriptor = self._loaded.get(
            plugin_id
        )

        if descriptor is None:
            raise KeyError(
                (
                    f"Plugin {plugin_id!r} has not "
                    "been loaded."
                )
            )

        return descriptor

    # ========================================================
    # FORGET
    # ========================================================

    def forget(
        self,
        plugin_id: str,
    ) -> LoadedPlugin | None:
        """
        Forget a loaded implementation descriptor.

        This does not unload Python modules or affect instances.
        """

        self._validate_plugin_id(
            plugin_id
        )

        return self._loaded.pop(
            plugin_id,
            None,
        )

    def clear(self) -> None:
        """Forget all loaded implementation descriptors."""

        self._loaded.clear()

    # ========================================================
    # RESOLUTION
    # ========================================================

    @staticmethod
    def _resolve_plugin_class(
        definition: PluginImplementation,
        module: ModuleType,
    ) -> type[Any]:

        class_name = definition.class_name

        if class_name is None:
            raise RuntimeError(
                (
                    f"Plugin {definition.plugin_id!r} "
                    "does not declare class_name."
                )
            )

        implementation = getattr(
            module,
            class_name,
            None,
        )

        if implementation is None:
            raise ImportError(
                (
                    f"Module {module.__name__!r} does not "
                    f"export class {class_name!r}."
                )
            )

        if not isinstance(
            implementation,
            type,
        ):
            raise TypeError(
                (
                    f"{module.__name__!r}.{class_name} "
                    "is not a class."
                )
            )

        return implementation

    @staticmethod
    def _resolve_factory(
        definition: PluginImplementation,
        module: ModuleType,
    ) -> Callable[..., Any]:

        factory_name = definition.factory_name

        if factory_name is None:
            raise RuntimeError(
                (
                    f"Plugin {definition.plugin_id!r} "
                    "does not declare factory_name."
                )
            )

        factory = getattr(
            module,
            factory_name,
            None,
        )

        if factory is None:
            raise ImportError(
                (
                    f"Module {module.__name__!r} does not "
                    f"export factory {factory_name!r}."
                )
            )

        if not callable(
            factory
        ):
            raise TypeError(
                (
                    f"{module.__name__!r}.{factory_name} "
                    "is not callable."
                )
            )

        return factory

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> None:

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
# FACTORIES
# ============================================================


def create_default_plugin_loader() -> PluginLoader:
    """
    Create the canonical GridForge V2 plugin loader.

    This creates definitions only.

    No plugin module is imported and no plugin is constructed.
    """

    return PluginLoader(
        definitions=DEFAULT_PLUGIN_IMPLEMENTATIONS
    )


def load_default_plugins() -> tuple[LoadedPlugin, ...]:
    """
    Explicitly resolve all canonical plugin implementations.

    This imports modules but does not construct or initialize them.
    """

    loader = create_default_plugin_loader()

    return loader.load_all()


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginImplementation",
    "LoadedPlugin",
    "DEFAULT_PLUGIN_IMPLEMENTATIONS",
    "DEFAULT_PLUGIN_MODULES",
    "DEFAULT_PLUGIN_CLASSES",
    "DEFAULT_PLUGIN_FACTORIES",
    "PluginLoader",
    "create_default_plugin_loader",
    "load_default_plugins",
]
