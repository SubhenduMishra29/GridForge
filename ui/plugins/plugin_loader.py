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
- maintain explicit plugin definitions;
- import concrete plugin modules;
- resolve the declared plugin class;
- resolve an optional declared factory;
- construct plugin instances;
- validate constructed plugin instances.

Non-responsibilities
--------------------
- plugin discovery;
- package scanning;
- dependency ordering;
- plugin registration;
- plugin initialization;
- plugin shutdown;
- PluginContext creation;
- Core/domain state;
- application business logic.

Lifecycle
---------
The lifecycle is deliberately split:

    PluginLoader
        |
        +--> load()
        |       import + resolve implementation
        |
        +--> create()
                construct instance

    PluginRegistry / PluginManager
        |
        +--> register()
        |
        +--> initialize(context)
        |
        +--> shutdown()

PluginContext is therefore NEVER a constructor dependency.

Concrete plugin imports remain explicit. PluginRegistry does not import
concrete implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Optional

from .plugin_contract import validate_plugin


# ============================================================
# LOADED PLUGIN DESCRIPTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """
    Immutable descriptor for one explicitly loaded plugin.

    Loading resolves implementation metadata only.

    It does not:
        - construct the plugin;
        - initialize the plugin;
        - register the plugin;
        - create application state.
    """

    plugin_id: str

    module_name: str

    plugin_class: type[Any]

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

        if (
            not isinstance(
                self.module_name,
                str,
            )
            or not self.module_name.strip()
        ):
            raise ValueError(
                "module_name must be a non-empty string."
            )

        if not isinstance(
            self.plugin_class,
            type,
        ):
            raise TypeError(
                "plugin_class must be a class."
            )

        if (
            self.factory is not None
            and not callable(self.factory)
        ):
            raise TypeError(
                "factory must be callable or None."
            )


# ============================================================
# EXPLICIT PLUGIN DEFINITIONS
# ============================================================


DEFAULT_PLUGIN_MODULES: Mapping[
    str,
    str,
] = {
    "canvas": "ui.plugins.canvas_plugin",
    "panels": "ui.plugins.panels_plugin",
    "toolbar": "ui.plugins.toolbar_plugin",
    "status": "ui.plugins.status_plugin",
}


DEFAULT_PLUGIN_CLASSES: Mapping[
    str,
    str,
] = {
    "canvas": "CanvasPlugin",
    "panels": "PanelsPlugin",
    "toolbar": "ToolbarPlugin",
    "status": "StatusPlugin",
}


DEFAULT_PLUGIN_FACTORIES: Mapping[
    str,
    str,
] = {
    "canvas": "create_canvas_plugin",
    "panels": "create_panels_plugin",
    "toolbar": "create_toolbar_plugin",
    "status": "create_status_plugin",
}


# ============================================================
# LOADER
# ============================================================


class PluginLoader:
    """
    Explicit GridForge UI plugin loader.

    This class intentionally performs no plugin discovery.

    A plugin becomes known to the loader only because it exists in
    the explicit definition mapping.

    Dependency ordering belongs to PluginManager.
    Registration belongs to PluginRegistry.
    Initialization belongs to PluginRegistry / PluginManager.
    """

    def __init__(
        self,
        definitions: Optional[
            Mapping[str, str]
        ] = None,
    ) -> None:
        definitions = (
            definitions
            if definitions is not None
            else DEFAULT_PLUGIN_MODULES
        )

        self._definitions: dict[
            str,
            str,
        ] = {}

        self._loaded: dict[
            str,
            LoadedPlugin,
        ] = {}

        for plugin_id, module_name in definitions.items():
            self.define(
                plugin_id,
                module_name,
            )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def definitions(
        self,
    ) -> Mapping[str, str]:
        """
        Return a snapshot of the explicit definitions.

        The caller cannot mutate loader configuration through the
        returned mapping.
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
        plugin_id: str,
        module_name: str,
    ) -> None:
        """
        Define one explicit plugin implementation.

        The module is not imported until load() is called.
        """

        self._validate_plugin_id(
            plugin_id
        )

        self._validate_module_name(
            module_name
        )

        if plugin_id in self._loaded:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is already loaded."
                )
            )

        self._definitions[
            plugin_id
        ] = module_name

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

        This method performs only:

            1. module import;
            2. concrete class resolution;
            3. optional factory resolution;
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

        module_name = self._definitions.get(
            plugin_id
        )

        if module_name is None:
            raise KeyError(
                (
                    f"No explicit plugin definition "
                    f"exists for {plugin_id!r}."
                )
            )

        module = import_module(
            module_name
        )

        plugin_class = (
            self._resolve_plugin_class(
                plugin_id,
                module,
            )
        )

        factory = (
            self._resolve_factory(
                plugin_id,
                module,
            )
        )

        descriptor = LoadedPlugin(
            plugin_id=plugin_id,
            module_name=module_name,
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

        No package scanning or dynamic discovery occurs.
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

        Construction and initialization are strictly separate.

        PluginContext MUST NOT be passed here.

        Correct lifecycle:

            descriptor = loader.load("canvas")
            plugin = loader.create("canvas")
            registry.register("canvas", plugin)
            registry.initialize(
                "canvas",
                context=context,
            )

        Normal constructor arguments such as a Qt ``parent`` are
        allowed where supported by the concrete plugin.
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

        try:
            validate_plugin(
                plugin,
                plugin_id=plugin_id,
            )
        except Exception as exc:
            raise TypeError(
                (
                    f"Constructed plugin "
                    f"{plugin_id!r} does not satisfy "
                    "the GridForge plugin contract."
                )
            ) from exc

        actual_plugin_id = getattr(
            plugin,
            "plugin_id",
            None,
        )

        if actual_plugin_id != plugin_id:
            raise TypeError(
                (
                    f"Plugin definition {plugin_id!r} "
                    f"constructed an object declaring "
                    f"plugin_id={actual_plugin_id!r}."
                )
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

        Constructor arguments are explicitly separated from the
        initialization context.

        ``context`` is rejected by ``create()`` and therefore cannot
        accidentally cross the construction boundary.
        """

        positional = (
            constructor_args
            if constructor_args is not None
            else {}
        )

        keyword = (
            constructor_kwargs
            if constructor_kwargs is not None
            else {}
        )

        instances: list[Any] = []

        for plugin_id in plugin_ids:
            args = tuple(
                positional.get(
                    plugin_id,
                    (),
                )
            )

            kwargs = dict(
                keyword.get(
                    plugin_id,
                    {},
                )
            )

            instances.append(
                self.create(
                    plugin_id,
                    *args,
                    **kwargs,
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
        Construct a plugin through its explicit factory or class.

        Factories are construction helpers only. They do not receive
        lifecycle context implicitly.
        """

        if descriptor.factory is not None:
            return descriptor.factory(
                *args,
                **dict(kwargs),
            )

        return descriptor.plugin_class(
            *args,
            **dict(kwargs),
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
        """
        Return a loaded descriptor.

        Raises KeyError when the plugin has not been loaded.
        """

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
        Plugin instances remain owned by their caller.
        """

        self._loaded.clear()

    # ========================================================
    # RESOLUTION
    # ========================================================

    @staticmethod
    def _resolve_plugin_class(
        plugin_id: str,
        module: ModuleType,
    ) -> type[Any]:
        """
        Resolve the explicitly declared concrete plugin class.

        The canonical GridForge composition plugins use explicit class
        mappings. For custom definitions, the conventional class name
        is ``<PascalCasePluginId>Plugin``.
        """

        class_name = (
            DEFAULT_PLUGIN_CLASSES.get(
                plugin_id
            )
        )

        if class_name is None:
            class_name = (
                f"{_pascal_case(plugin_id)}Plugin"
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
                    f"export {class_name!r}."
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
        plugin_id: str,
        module: ModuleType,
    ) -> Optional[
        Callable[..., Any]
    ]:
        """
        Resolve the explicitly declared factory.

        Absence of a factory is valid and causes direct class
        construction.

        The factory is never invoked during load().
        """

        factory_name = (
            DEFAULT_PLUGIN_FACTORIES.get(
                plugin_id
            )
        )

        if factory_name is None:
            factory_name = (
                f"create_"
                f"{_snake_case(plugin_id)}_plugin"
            )

        factory = getattr(
            module,
            factory_name,
            None,
        )

        if factory is None:
            return None

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
                (
                    f"Invalid module name: "
                    f"{module_name!r}."
                )
            )

        if any(
            not part.isidentifier()
            for part in parts
        ):
            raise ValueError(
                (
                    f"Invalid module name: "
                    f"{module_name!r}."
                )
            )


# ============================================================
# DEFAULT LOADER
# ============================================================


def create_default_plugin_loader() -> PluginLoader:
    """
    Create the canonical GridForge UI plugin loader.

    Exactly four concrete composition plugins are explicitly defined:

        canvas
        panels
        toolbar
        status
    """

    return PluginLoader(
        definitions=DEFAULT_PLUGIN_MODULES
    )


def load_default_plugins() -> tuple[
    LoadedPlugin,
    ...
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
# NAMING HELPERS
# ============================================================


def _pascal_case(
    value: str,
) -> str:
    """
    Convert a simple snake_case identifier to PascalCase.
    """

    return "".join(
        part[:1].upper() + part[1:]
        for part in value.split("_")
        if part
    )


def _snake_case(
    value: str,
) -> str:
    """
    Convert a simple plugin identifier to snake_case.

    This helper is used only for conventional fallback factory
    naming. Canonical plugins use explicit factory definitions.
    """

    normalized = value.replace(
        "-",
        "_",
    )

    result: list[str] = []

    for index, char in enumerate(
        normalized
    ):
        if (
            char.isupper()
            and index > 0
            and normalized[index - 1] != "_"
        ):
            result.append("_")

        result.append(
            char.lower()
        )

    return "".join(
        result
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "LoadedPlugin",
    "DEFAULT_PLUGIN_MODULES",
    "DEFAULT_PLUGIN_CLASSES",
    "DEFAULT_PLUGIN_FACTORIES",
    "PluginLoader",
    "create_default_plugin_loader",
    "load_default_plugins",
]
