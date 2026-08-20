"""
GridForge V2
============

File:
    ui/plugins/plugin_loader.py

Purpose
-------
Explicitly loads the concrete GridForge UI composition plugins.

Architectural role
------------------
PluginLoader is the explicit concrete-plugin import and construction
boundary.

Responsibilities
----------------
- maintain explicit plugin implementation definitions;
- validate implementation definitions;
- import concrete plugin modules;
- resolve explicitly declared plugin classes or factories;
- construct plugin instances;
- validate constructed plugin instances.

Non-responsibilities
--------------------
- plugin discovery;
- package scanning;
- dependency ordering;
- plugin registration;
- plugin lifecycle orchestration;
- PluginContext creation;
- Core/domain state;
- application business logic;
- UI composition.

Lifecycle
---------
    PluginLoader
        |
        +--> load()
        |       import + resolve implementation
        |
        +--> create()
                construct + contract validation

    PluginManager
        |
        +--> dependency ordering
        |
        +--> PluginRegistry
                |
                +--> register()
                +--> initialize(context)
                +--> shutdown()

PluginContext is therefore NEVER a constructor dependency.

Concrete plugin resolution is explicit. No class-name or factory-name
discovery by convention is performed.

Canonical composition plugins
-----------------------------
    canvas
    panels
    toolbar
    status
    shell

The shell is itself an explicit composition plugin. It is loaded and
constructed by PluginLoader, ordered and initialized by PluginManager,
and performs only final UI composition.

Qt construction remains inside the concrete plugin implementations.
PluginLoader does not create widgets directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Optional,
)

from .plugin_contract import validate_plugin


# ============================================================
# PLUGIN IMPLEMENTATION DEFINITION
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginImplementation:
    """
    Explicit implementation definition for one UI plugin.

    Exactly one construction mechanism must be declared:

        class_name
            OR
        factory_name

    The loader never derives either name from plugin_id.
    """

    plugin_id: str
    module_name: str

    class_name: Optional[str] = None
    factory_name: Optional[str] = None

    def __post_init__(self) -> None:
        # ----------------------------------------------------
        # plugin_id
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # module_name
        # ----------------------------------------------------

        self._validate_module_name(
            self.module_name
        )

        # ----------------------------------------------------
        # class_name
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # factory_name
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # construction mechanism
        # ----------------------------------------------------

        if (
            self.class_name is None
            and self.factory_name is None
        ):
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} "
                    "must declare either class_name "
                    "or factory_name."
                )
            )

        if (
            self.class_name is not None
            and self.factory_name is not None
        ):
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} "
                    "cannot declare both class_name "
                    "or factory_name."
                )
            )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_module_name(
        module_name: str,
    ) -> None:
        """Validate a Python module name."""

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
            not part
            for part in parts
        ):
            raise ValueError(
                f"Invalid module name: {module_name!r}."
            )

        if any(
            not part.isidentifier()
            for part in parts
        ):
            raise ValueError(
                f"Invalid module name: {module_name!r}."
            )


# ============================================================
# LOADED PLUGIN DESCRIPTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """
    Immutable descriptor for one explicitly resolved plugin
    implementation.

    Loading resolves implementation metadata only.

    It does not:

        - construct the plugin;
        - initialize the plugin;
        - register the plugin;
        - create application state;
        - create PluginContext.
    """

    plugin_id: str
    module_name: str

    plugin_class: Optional[type[Any]] = None

    factory: Optional[
        Callable[..., Any]
    ] = None

    module: Optional[ModuleType] = None

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
                    f"Loaded plugin "
                    f"{self.plugin_id!r} must expose "
                    "either a plugin class or factory."
                )
            )

        if (
            self.plugin_class is not None
            and self.factory is not None
        ):
            raise ValueError(
                (
                    f"Loaded plugin "
                    f"{self.plugin_id!r} cannot expose "
                    "both a plugin class or factory."
                )
            )


# ============================================================
# EXPLICIT PLUGIN DEFINITIONS
# ============================================================


DEFAULT_PLUGIN_IMPLEMENTATIONS: Mapping[
    str,
    PluginImplementation,
] = {
    # --------------------------------------------------------
    # Central canvas
    # --------------------------------------------------------

    "canvas": PluginImplementation(
        plugin_id="canvas",
        module_name="ui.plugins.canvas_plugin",
        class_name="CanvasPlugin",
    ),

    # --------------------------------------------------------
    # Dock / panel composition
    # --------------------------------------------------------

    "panels": PluginImplementation(
        plugin_id="panels",
        module_name="ui.plugins.panels_plugin",
        class_name="PanelsPlugin",
    ),

    # --------------------------------------------------------
    # Toolbar composition
    # --------------------------------------------------------

    "toolbar": PluginImplementation(
        plugin_id="toolbar",
        module_name="ui.plugins.toolbar_plugin",
        class_name="ToolbarPlugin",
    ),

    # --------------------------------------------------------
    # Status composition
    # --------------------------------------------------------

    "status": PluginImplementation(
        plugin_id="status",
        module_name="ui.plugins.status_plugin",
        class_name="StatusPlugin",
    ),

    # --------------------------------------------------------
    # Final application shell
    # --------------------------------------------------------

    "shell": PluginImplementation(
        plugin_id="shell",
        module_name="ui.plugins.shell_plugin",
        class_name="ShellPlugin",
    ),
}


# ============================================================
# COMPATIBILITY-FACING EXPLICIT MAPPINGS
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
# LOADER
# ============================================================


class PluginLoader:
    """
    Explicit GridForge V2 UI plugin loader.

    This class intentionally performs no plugin discovery.

    A plugin becomes known to the loader only because an explicit
    PluginImplementation definition was supplied.

    Dependency ordering belongs to PluginManager.

    Registration belongs to PluginRegistry.

    Initialization and shutdown belong to PluginRegistry /
    PluginManager.
    """

    def __init__(
        self,
        definitions: Optional[
            Mapping[str, PluginImplementation]
        ] = None,
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
    ) -> Mapping[str, PluginImplementation]:
        """
        Return a snapshot of the explicit definitions.

        Mutating the returned dictionary cannot mutate loader state.
        """

        return dict(
            self._definitions
        )

    @property
    def loaded_ids(
        self,
    ) -> tuple[str, ...]:
        """Return successfully loaded plugin IDs."""

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
    # CONFIGURATION
    # ========================================================

    def define(
        self,
        definition: PluginImplementation,
    ) -> None:
        """
        Define one explicit plugin implementation.

        The module is not imported until load() is called.
        """

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
                    f"Plugin definition "
                    f"{plugin_id!r} already exists."
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
        Remove an explicit plugin definition.

        A loaded plugin definition cannot be removed.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id in self._loaded:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is already loaded."
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

        This performs only:

            1. explicit definition lookup;
            2. module import;
            3. explicit implementation resolution;
            4. descriptor creation.

        It does NOT construct or initialize the plugin.

        Repeated loads are idempotent.
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

        plugin_class: Optional[
            type[Any]
        ] = None

        factory: Optional[
            Callable[..., Any]
        ] = None

        if definition.class_name is not None:
            plugin_class = (
                self._resolve_plugin_class(
                    definition,
                    module,
                )
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
            plugin_class=plugin_class,
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
        """
        Explicitly load multiple plugins.

        Input order is preserved.

        No dependency ordering is performed.
        """

        result: list[
            LoadedPlugin
        ] = []

        for plugin_id in plugin_ids:
            result.append(
                self.load(
                    plugin_id
                )
            )

        return tuple(
            result
        )

    def load_all(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """
        Load every explicitly defined plugin.

        Definition insertion order is preserved.
        """

        return self.load_many(
            self._definitions.keys()
        )

    # ========================================================
    # INSTANCE CREATION
    # ========================================================

    def create(
        self,
        plugin_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Construct one loaded plugin.

        Construction and initialization remain strictly separate.

        PluginContext MUST NOT be supplied here.
        """

        if "context" in kwargs:
            raise TypeError(
                (
                    "PluginContext must not be supplied to "
                    "PluginLoader.create(). "
                    "Pass context to plugin initialization."
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
        constructor_args: Optional[
            Mapping[str, tuple[Any, ...]]
        ] = None,
        constructor_kwargs: Optional[
            Mapping[str, Mapping[str, Any]]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Construct multiple plugins.

        Constructor arguments are explicitly separated from
        initialization context.

        No PluginContext is created or supplied here.
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
                        "arguments, not a string."
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
                        "must be an iterable."
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
    # CONSTRUCTION
    # ========================================================

    @staticmethod
    def _construct(
        descriptor: LoadedPlugin,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> Any:
        """
        Construct a plugin through its explicitly resolved
        construction mechanism.

        No lifecycle operation is performed.
        """

        if descriptor.factory is not None:
            return descriptor.factory(
                *args,
                **dict(kwargs),
            )

        if descriptor.plugin_class is not None:
            return descriptor.plugin_class(
                *args,
                **dict(kwargs),
            )

        raise RuntimeError(
            (
                f"Loaded plugin "
                f"{descriptor.plugin_id!r} has no "
                "construction mechanism."
            )
        )

    # ========================================================
    # QUERY
    # ========================================================

    def is_loaded(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin has been loaded."""

        self._validate_plugin_id(
            plugin_id
        )

        return plugin_id in self._loaded

    def get(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
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
                    f"Plugin {plugin_id!r} "
                    "has not been loaded."
                )
            )

        return descriptor

    # ========================================================
    # UNLOAD / FORGET
    # ========================================================

    def forget(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """
        Forget one loaded descriptor.

        This does NOT:

            - unload the Python module;
            - destroy plugin instances;
            - call shutdown();
            - unregister plugins;
            - modify registry state.
        """

        self._validate_plugin_id(
            plugin_id
        )

        return self._loaded.pop(
            plugin_id,
            None,
        )

    def clear(self) -> None:
        """
        Forget all loaded descriptors.

        Python modules remain imported.

        Existing plugin instances remain owned by their caller.
        """

        self._loaded.clear()

    # ========================================================
    # RESOLUTION
    # ========================================================

    @staticmethod
    def _resolve_plugin_class(
        definition: PluginImplementation,
        module: ModuleType,
    ) -> type[Any]:
        """
        Resolve the explicitly declared plugin class.

        No class-name inference is performed.
        """

        class_name = definition.class_name

        if class_name is None:
            raise RuntimeError(
                (
                    f"Plugin {definition.plugin_id!r} "
                    "does not declare a class_name."
                )
            )

        plugin_class = getattr(
            module,
            class_name,
            None,
        )

        if plugin_class is None:
            raise ImportError(
                (
                    f"Plugin module "
                    f"{module.__name__!r} does not "
                    f"export explicitly declared class "
                    f"{class_name!r}."
                )
            )

        if not isinstance(
            plugin_class,
            type,
        ):
            raise TypeError(
                (
                    f"{module.__name__!r}."
                    f"{class_name} is not a class."
                )
            )

        return plugin_class

    @staticmethod
    def _resolve_factory(
        definition: PluginImplementation,
        module: ModuleType,
    ) -> Callable[..., Any]:
        """
        Resolve the explicitly declared factory.

        No factory-name inference is performed.
        """

        factory_name = definition.factory_name

        if factory_name is None:
            raise RuntimeError(
                (
                    f"Plugin {definition.plugin_id!r} "
                    "does not declare a factory_name."
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
                    f"Plugin module "
                    f"{module.__name__!r} does not "
                    f"export explicitly declared factory "
                    f"{factory_name!r}."
                )
            )

        if not callable(
            factory
        ):
            raise TypeError(
                (
                    f"{module.__name__!r}."
                    f"{factory_name} is not callable."
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
# DEFAULT LOADER
# ============================================================


def create_default_plugin_loader() -> PluginLoader:
    """
    Create the canonical GridForge V2 UI plugin loader.

    Exactly five concrete composition plugins are explicitly defined:

        canvas
        panels
        toolbar
        status
        shell

    The shell is the final UI composition boundary.

    No plugin is imported or constructed by this factory.
    """

    return PluginLoader(
        definitions=DEFAULT_PLUGIN_IMPLEMENTATIONS
    )


def load_default_plugins() -> tuple[
    LoadedPlugin,
    ...,
]:
    """
    Explicitly import all canonical UI composition plugins.

    This performs import and implementation resolution only.

    It does NOT:

        - instantiate plugins;
        - initialize plugins;
        - create PluginContext;
        - register plugins;
        - modify MainWindow.
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
