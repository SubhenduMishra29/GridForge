"""
GridForge V2
============

File:
    ui/plugins/plugin_loader.py

Purpose
-------
Explicitly loads the concrete GridForge UI composition plugins.

Architectural rules
-------------------
- Plugin discovery is explicit.
- This module is the composition-level loader responsible for importing
  concrete UI plugins.
- PluginRegistry does not import concrete plugins.
- MainWindow remains thin and plugin-driven.
- Loading a plugin does not initialize it.
- Plugin construction and plugin initialization are separate phases.
- PluginContext is supplied during initialize(context), not construction.
- No Core/domain state is created here.
- No plugin lifecycle methods are called here.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Optional

from .plugin_contract import (
    validate_plugin,
)


# ============================================================
# LOADED PLUGIN DESCRIPTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """
    Descriptor for an explicitly loaded plugin implementation.

    The descriptor records the concrete implementation that was
    imported. It does not contain runtime plugin state.

    Loading and construction remain separate:

        load()
            -> import + resolve

        create()
            -> instantiate

        initialize()
            -> handled by PluginRegistry / PluginManager
    """

    plugin_id: str

    module_name: str

    plugin_class: type[Any]

    factory: Optional[
        Callable[..., Any]
    ] = None

    module: Optional[ModuleType] = None


# ============================================================
# DEFAULT PLUGIN DEFINITIONS
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

    Responsibilities
    ----------------
    - Maintain explicit plugin module definitions.
    - Import concrete plugin modules.
    - Resolve the expected plugin class.
    - Resolve an optional explicit factory.
    - Construct plugin instances.
    - Validate constructed plugin instances.

    Non-responsibilities
    --------------------
    - Plugin discovery.
    - Package scanning.
    - Dependency ordering.
    - Plugin initialization.
    - Plugin shutdown.
    - Plugin registration.
    - MainWindow construction.
    - Core/domain state creation.
    - Tool registration.
    - Renderer registration.

    Lifecycle boundary
    ------------------
    The loader deliberately separates construction from initialization.

        loader.load(plugin_id)
            |
            v
        concrete implementation

        loader.create(plugin_id)
            |
            v
        plugin instance

        registry.initialize(
            plugin_id,
            context=context,
        )
            |
            v
        plugin.initialize(context)

    Therefore PluginContext is NOT a constructor dependency.
    """

    def __init__(
        self,
        definitions: Optional[
            Mapping[str, str]
        ] = None,
    ) -> None:
        self._definitions: dict[
            str,
            str,
        ] = dict(
            definitions
            or DEFAULT_PLUGIN_MODULES
        )

        self._loaded: dict[
            str,
            LoadedPlugin,
        ] = {}

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def definitions(
        self,
    ) -> Mapping[str, str]:
        """
        Return a copy of the explicit plugin definitions.
        """

        return dict(
            self._definitions
        )

    @property
    def loaded_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return IDs of successfully loaded plugins.
        """

        return tuple(
            self._loaded.keys()
        )

    @property
    def loaded_plugins(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """
        Return loaded plugin descriptors in load order.
        """

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
        Add or replace an explicit plugin definition.

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
        Remove an unloaded plugin definition.
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
        Explicitly import and resolve one plugin implementation.

        Loading performs:

            1. module import;
            2. expected class resolution;
            3. optional factory resolution;
            4. descriptor creation.

        Loading does NOT:

            - instantiate the plugin;
            - initialize the plugin;
            - provide PluginContext;
            - register the plugin;
            - modify application state.

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
                    f"No plugin definition "
                    f"exists for {plugin_id!r}."
                )
            )

        module = import_module(
            module_name
        )

        plugin_class = self._resolve_plugin_class(
            plugin_id,
            module,
        )

        factory = self._resolve_factory(
            plugin_id,
            module,
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

        The supplied order is preserved.

        Dependency ordering is NOT performed here. Dependency ordering
        belongs to PluginManager.
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
        Load all explicitly defined plugins.

        This loads only entries in the explicit definition mapping.
        No package scanning or discovery occurs.
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

        Construction does NOT initialize the plugin.

        ``args`` and ``kwargs`` are constructor arguments only.

        PluginContext must NOT be supplied here.

        The canonical lifecycle is:

            plugin = loader.create(plugin_id)

            registry.initialize(
                plugin_id,
                context=context,
            )

        A concrete plugin may still receive normal Qt ownership
        arguments such as ``parent=...`` if its constructor supports
        them. Application/UI context remains an initialization concern.
        """

        descriptor = self.load(
            plugin_id
        )

        if descriptor.factory is not None:
            plugin = descriptor.factory(
                *args,
                **kwargs,
            )
        else:
            plugin = descriptor.plugin_class(
                *args,
                **kwargs,
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

        Constructor arguments are explicitly separated from plugin
        initialization context.

        Parameters
        ----------
        plugin_ids:
            Plugin IDs to construct.

        constructor_args:
            Optional per-plugin positional constructor arguments.

        constructor_kwargs:
            Optional per-plugin keyword constructor arguments.

        No PluginContext is accepted here.
        """

        constructor_args = (
            constructor_args
            or {}
        )

        constructor_kwargs = (
            constructor_kwargs
            or {}
        )

        instances: list[Any] = []

        for plugin_id in plugin_ids:
            args = tuple(
                constructor_args.get(
                    plugin_id,
                    (),
                )
            )

            kwargs = dict(
                constructor_kwargs.get(
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
    # QUERY
    # ========================================================

    def is_loaded(
        self,
        plugin_id: str,
    ) -> bool:
        """
        Return whether a plugin has been loaded.
        """

        self._validate_plugin_id(
            plugin_id
        )

        return plugin_id in self._loaded

    def get(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """
        Return a loaded plugin descriptor.
        """

        self._validate_plugin_id(
            plugin_id
        )

        return self._loaded.get(
            plugin_id
        )

    # ========================================================
    # UNLOAD / FORGET
    # ========================================================

    def forget(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """
        Forget a loaded plugin descriptor.

        This does NOT:

            - unload Python modules;
            - destroy plugin instances;
            - call shutdown();
            - modify registry state.

        Runtime lifecycle remains the responsibility of
        PluginManager / PluginRegistry.
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

        This does not unload Python modules or destroy plugin instances.
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
        Resolve the expected concrete plugin class.

        The expected class name is explicit.

        The loader does not scan arbitrary module members looking for
        a possible plugin implementation.
        """

        class_name = DEFAULT_PLUGIN_CLASSES.get(
            plugin_id
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
        Resolve an optional explicit factory function.

        If the expected factory does not exist, direct class
        construction is used.

        The factory itself is never invoked during loading.
        """

        factory_name = DEFAULT_PLUGIN_FACTORIES.get(
            plugin_id
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
        """
        Validate a plugin identifier.
        """

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
        """
        Validate a Python module name.
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


# ============================================================
# DEFAULT LOADER
# ============================================================


def create_default_plugin_loader() -> PluginLoader:
    """
    Create the canonical GridForge UI plugin loader.

    Only the four explicitly defined composition plugins are
    configured.
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

    This function imports and resolves implementations only.

    It does NOT:

        - instantiate plugins;
        - initialize plugins;
        - create PluginContext;
        - register plugins.
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
    Convert a snake_case identifier to PascalCase.
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
    Normalize a simple plugin identifier to snake_case.
    """

    result: list[str] = []

    for index, char in enumerate(
        value
    ):
        if (
            char.isupper()
            and index > 0
        ):
            result.append("_")

        result.append(
            char.lower()
        )

    return "".join(
        result
    ).replace(
        "-",
        "_",
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
