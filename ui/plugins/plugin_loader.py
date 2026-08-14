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
- Plugin discovery/registration is explicit.
- This module is the only composition-level loader responsible for
  importing concrete UI plugins.
- The plugin registry must not import concrete plugins implicitly.
- MainWindow remains thin and plugin-driven.
- Loading a plugin does not initialize it.
- Plugin lifecycle remains explicit.
- No Core/domain state is created here.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Optional


# ============================================================
# LOADED PLUGIN DESCRIPTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """
    Descriptor for an explicitly loaded plugin implementation.

    The loader records what was imported. It does not instantiate or
    initialize the plugin automatically.
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
    Explicit UI plugin loader.

    PluginLoader performs import and class/factory resolution only.

    It deliberately does not:
        - initialize plugins
        - create MainWindow
        - create Core services
        - mutate project state
        - register tools
        - register renderers
        - silently scan packages
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
        """Return the configured plugin definitions."""

        return dict(
            self._definitions
        )

    @property
    def loaded_ids(
        self,
    ) -> tuple[str, ...]:
        """Return IDs of successfully loaded plugins."""

        return tuple(
            self._loaded.keys()
        )

    @property
    def loaded_plugins(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """Return all loaded plugin descriptors."""

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
        """Remove an unloaded plugin definition."""

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
        Explicitly import and resolve one plugin.

        Repeated loads are idempotent and return the existing
        descriptor.
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
        Explicitly load multiple plugins in the supplied order.

        Order is preserved and no package scanning is performed.
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

        This means all entries in the loader's definition mapping;
        it does not discover arbitrary modules from the package.
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
        Instantiate a loaded plugin.

        If a plugin exposes its explicit factory, that factory is used.
        Otherwise its plugin class is instantiated directly.

        Creation does not call initialize().
        """

        descriptor = self.load(
            plugin_id
        )

        if descriptor.factory is not None:
            return descriptor.factory(
                *args,
                **kwargs,
            )

        return descriptor.plugin_class(
            *args,
            **kwargs,
        )

    def create_many(
        self,
        plugin_ids: Iterable[str],
        *,
        contexts: Optional[
            Mapping[str, Any]
        ] = None,
        **kwargs: Any,
    ) -> tuple[Any, ...]:
        """
        Instantiate multiple plugins.

        Optional per-plugin contexts are passed as the ``context``
        keyword argument.
        """

        contexts = contexts or {}

        instances: list[Any] = []

        for plugin_id in plugin_ids:
            context = contexts.get(
                plugin_id
            )

            instance_kwargs = dict(
                kwargs
            )

            if context is not None:
                instance_kwargs[
                    "context"
                ] = context

            instances.append(
                self.create(
                    plugin_id,
                    **instance_kwargs,
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
        """Return whether a plugin has been loaded."""

        return plugin_id in self._loaded

    def get(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """Return a loaded plugin descriptor."""

        return self._loaded.get(
            plugin_id
        )

    # ========================================================
    # UNLOAD
    # ========================================================

    def forget(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """
        Forget a loaded plugin descriptor.

        This does not unload Python modules from sys.modules and does
        not destroy plugin instances.
        """

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

        The loader requires the class to be explicitly exposed by the
        module. It does not search arbitrary module members.
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
        Resolve the explicit factory function if provided.

        A factory is optional because plugin construction may be
        performed directly through the concrete plugin class.
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

        if not callable(factory):
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

    The returned loader contains only the four explicitly defined
    composition plugins.
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

    No plugin is instantiated or initialized by this function.
    """

    loader = create_default_plugin_loader()

    return loader.load_all()


# ============================================================
# NAMING HELPERS
# ============================================================


def _pascal_case(value: str) -> str:
    """Convert a snake_case identifier to PascalCase."""

    return "".join(
        part[:1].upper() + part[1:]
        for part in value.split("_")
        if part
    )


def _snake_case(value: str) -> str:
    """Normalize a simple plugin identifier to snake_case."""

    result: list[str] = []

    for index, char in enumerate(value):
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


__all__ = [
    "LoadedPlugin",
    "DEFAULT_PLUGIN_MODULES",
    "DEFAULT_PLUGIN_CLASSES",
    "DEFAULT_PLUGIN_FACTORIES",
    "PluginLoader",
    "create_default_plugin_loader",
    "load_default_plugins",
]
