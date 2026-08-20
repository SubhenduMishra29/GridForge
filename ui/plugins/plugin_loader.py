"""
GridForge V2
============

File:
    ui/plugins/plugin_loader.py

Author:
    Subhendu Mishra

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
- import explicitly declared plugin modules;
- resolve explicitly declared plugin classes or factories;
- construct plugin instances;
- validate constructed plugin instances.

Non-responsibilities
--------------------
- plugin discovery;
- package scanning;
- dependency resolution;
- dependency ordering;
- plugin registration;
- lifecycle orchestration;
- PluginContext creation;
- Core/domain ownership;
- application business logic;
- UI composition.

Lifecycle boundary
------------------
    PluginLoader
        |
        +--> load()
        |       import + resolve implementation
        |
        +--> create()
                construct + contract validation
                         |
                         v
                  PluginRegistry
                         |
                         +--> register()
                         +--> initialize(context)
                         +--> shutdown()

PluginContext
-------------
PluginContext is NEVER a constructor dependency.

It is supplied only during:

    PluginRegistry.initialize(..., context=...)

Concrete plugin resolution is explicit.

No class-name inference, factory-name inference, package scanning,
entry-point discovery, reflection-based plugin discovery, or naming
convention discovery is performed.

Canonical composition plugins
-----------------------------
    canvas
    panels
    toolbar
    status
    shell

The shell is itself an explicit composition plugin.

Qt construction remains inside concrete plugin implementations.
PluginLoader does not construct Qt widgets directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import MappingProxyType, ModuleType
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

    Names are explicitly supplied by the application architecture.
    They are never derived from plugin_id.
    """

    plugin_id: str
    module_name: str

    class_name: Optional[str] = None
    factory_name: Optional[str] = None

    def __post_init__(self) -> None:
        # ----------------------------------------------------
        # plugin_id
        # ----------------------------------------------------

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
        # Exactly one construction mechanism
        # ----------------------------------------------------

        has_class = (
            self.class_name is not None
        )

        has_factory = (
            self.factory_name is not None
        )

        if not has_class and not has_factory:
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} "
                    "must declare either class_name "
                    "or factory_name."
                )
            )

        if has_class and has_factory:
            raise ValueError(
                (
                    f"Plugin {self.plugin_id!r} "
                    "cannot declare both class_name "
                    "and factory_name."
                )
            )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_module_name(
        module_name: str,
    ) -> None:
        """
        Validate a Python dotted module name.
        """

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
    Immutable descriptor for one explicitly resolved plugin.

    Loading resolves implementation metadata only.

    It does NOT:

        - construct the plugin;
        - initialize the plugin;
        - register the plugin;
        - create PluginContext;
        - create application state.
    """

    plugin_id: str
    module_name: str

    plugin_class: Optional[type[Any]] = None

    factory: Optional[
        Callable[..., Any]
    ] = None

    module: Optional[ModuleType] = None

    def __post_init__(self) -> None:
        # ----------------------------------------------------
        # plugin_id
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # module_name
        # ----------------------------------------------------

        PluginImplementation._validate_module_name(
            self.module_name
        )

        # ----------------------------------------------------
        # class
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # factory
        # ----------------------------------------------------

        if (
            self.factory is not None
            and not callable(
                self.factory
            )
        ):
            raise TypeError(
                "factory must be callable or None."
            )

        # ----------------------------------------------------
        # Exactly one construction mechanism
        # ----------------------------------------------------

        has_class = (
            self.plugin_class is not None
        )

        has_factory = (
            self.factory is not None
        )

        if not has_class and not has_factory:
            raise ValueError(
                (
                    f"Loaded plugin "
                    f"{self.plugin_id!r} must expose "
                    "either a plugin class or factory."
                )
            )

        if has_class and has_factory:
            raise ValueError(
                (
                    f"Loaded plugin "
                    f"{self.plugin_id!r} cannot expose "
                    "both a plugin class and factory."
                )
            )


# ============================================================
# CANONICAL EXPLICIT IMPLEMENTATIONS
# ============================================================


_DEFAULT_PLUGIN_IMPLEMENTATIONS: dict[
    str,
    PluginImplementation,
] = {
    # --------------------------------------------------------
    # Central canvas / SLD visual capability
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


# ------------------------------------------------------------
# Public immutable snapshot
# ------------------------------------------------------------

DEFAULT_PLUGIN_IMPLEMENTATIONS: Mapping[
    str,
    PluginImplementation,
] = MappingProxyType(
    _DEFAULT_PLUGIN_IMPLEMENTATIONS
)


DEFAULT_PLUGIN_MODULES: Mapping[
    str,
    str,
] = MappingProxyType(
    {
        plugin_id: definition.module_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
    }
)


DEFAULT_PLUGIN_CLASSES: Mapping[
    str,
    str,
] = MappingProxyType(
    {
        plugin_id: definition.class_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
        if definition.class_name is not None
    }
)


DEFAULT_PLUGIN_FACTORIES: Mapping[
    str,
    str,
] = MappingProxyType(
    {
        plugin_id: definition.factory_name
        for plugin_id, definition
        in DEFAULT_PLUGIN_IMPLEMENTATIONS.items()
        if definition.factory_name is not None
    }
)


# ============================================================
# LOADER
# ============================================================


class PluginLoader:
    """
    Explicit GridForge V2 UI plugin loader.

    PluginLoader knows only explicitly supplied implementation
    definitions.

    It performs no discovery and no lifecycle orchestration.
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
        Return an immutable snapshot of explicit definitions.
        """

        return MappingProxyType(
            dict(
                self._definitions
            )
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
        Define one explicit implementation.

        Import does not occur until load().
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
        Remove an explicit implementation definition.

        A loaded implementation cannot be removed until it is forgotten.
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
        Import and resolve one explicitly defined implementation.

        Performs only:

            1. definition lookup;
            2. module import;
            3. explicit class/factory resolution;
            4. descriptor creation.

        No instance is constructed.

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
        Load multiple explicitly defined implementations.

        Input order is preserved.

        No dependency ordering occurs here.
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
        """Load all explicitly defined implementations."""

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
        Construct one plugin instance.

        Construction and initialization are separate lifecycle phases.

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

        Constructor arguments are explicitly separate from
        initialization context.
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
        Construct through the explicitly resolved mechanism.
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
    # QUERIES
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
    # FORGET
    # ========================================================

    def forget(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """
        Forget one loaded descriptor.

        This does not unload Python modules or affect plugin instances.
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
# FACTORIES
# ============================================================


def create_default_plugin_loader() -> PluginLoader:
    """
    Create the canonical GridForge V2 PluginLoader.

    Exactly five concrete composition plugins are explicitly defined:

        canvas
        panels
        toolbar
        status
        shell

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
    Explicitly import all canonical composition plugins.

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
