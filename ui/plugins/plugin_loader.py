```python
"""
GridForge V2
============

File:
    ui/plugins/plugin_loader.py

Purpose
-------
Explicitly loads and constructs the concrete GridForge UI
composition plugins.

Architectural role
------------------
PluginLoader is the explicit concrete-plugin import and construction
boundary.

Responsibilities
----------------
- maintain explicit plugin implementation definitions;
- import concrete plugin modules;
- resolve the explicitly declared plugin class or factory;
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

Construction boundary
---------------------
Plugin construction is deliberately restricted.

The loader may provide only the Qt ownership parent:

    PluginLoader.create(plugin_id, parent=...)

Application and UI dependencies MUST NOT be constructor arguments.

They are supplied later through:

    plugin.initialize(context)

Therefore:

    PluginLoader
        |
        +--> load()
        |       import + resolve implementation
        |
        +--> create()
                construct instance with optional Qt parent

    PluginRegistry / PluginManager
        |
        +--> register()
        |
        +--> initialize(context)
        |
        +--> shutdown()

PluginContext is therefore NEVER a constructor dependency.

Concrete plugin resolution is explicit. No class-name or factory-name
discovery by convention is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Optional

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
        if (
            not isinstance(self.plugin_id, str)
            or not self.plugin_id.strip()
        ):
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if (
            not isinstance(self.module_name, str)
            or not self.module_name.strip()
        ):
            raise ValueError(
                "module_name must be a non-empty string."
            )

        if (
            not isinstance(self.class_name, str)
            and self.class_name is not None
        ):
            raise TypeError(
                "class_name must be a string or None."
            )

        if (
            not isinstance(self.factory_name, str)
            and self.factory_name is not None
        ):
            raise TypeError(
                "factory_name must be a string or None."
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
                    "and factory_name."
                )
            )

        PluginLoader._validate_module_name(
            self.module_name
        )


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

    plugin_class: Optional[type[Any]] = None

    factory: Optional[Callable[..., Any]] = None

    module: Optional[ModuleType] = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.plugin_id, str)
            or not self.plugin_id.strip()
        ):
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if (
            not isinstance(self.module_name, str)
            or not self.module_name.strip()
        ):
            raise ValueError(
                "module_name must be a non-empty string."
            )

        if (
            self.plugin_class is not None
            and not isinstance(self.plugin_class, type)
        ):
            raise TypeError(
                "plugin_class must be a class or None."
            )

        if (
            self.factory is not None
            and not callable(self.factory)
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
# EXPLICIT PLUGIN DEFINITIONS
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
}


# Compatibility-facing explicit mappings.

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
    Initialization belongs to PluginRegistry / PluginManager.

    Construction is restricted to the optional Qt parent argument.
    """

    def __init__(
        self,
        definitions: Optional[
            Mapping[str, PluginImplementation]
        ] = None,
    ) -> None:
        definitions = (
            definitions
            if definitions is not None
            else DEFAULT_PLUGIN_IMPLEMENTATIONS
        )

        if not isinstance(definitions, Mapping):
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

        for plugin_id, definition in definitions.items():
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

            self.define(definition)

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def definitions(
        self,
    ) -> Mapping[str, PluginImplementation]:
        """
        Return a snapshot of the explicit definitions.
        """

        return dict(self._definitions)

    @property
    def loaded_ids(
        self,
    ) -> tuple[str, ...]:
        """Return successfully loaded plugin IDs."""

        return tuple(self._loaded.keys())

    @property
    def loaded_plugins(
        self,
    ) -> tuple[LoadedPlugin, ...]:
        """Return loaded descriptors in load order."""

        return tuple(self._loaded.values())

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

        Duplicate plugin IDs are rejected.
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

        if plugin_id in self._loaded:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is already loaded."
                )
            )

        self._definitions[plugin_id] = definition

    def remove_definition(
        self,
        plugin_id: str,
    ) -> None:
        """
        Remove an explicit plugin definition.

        A loaded plugin definition cannot be removed.
        """

        self._validate_plugin_id(plugin_id)

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
            2. explicitly declared implementation resolution;
            3. descriptor creation.

        It does NOT construct or initialize the plugin.

        Repeated loads are idempotent.
        """

        self._validate_plugin_id(plugin_id)

        existing = self._loaded.get(plugin_id)

        if existing is not None:
            return existing

        definition = self._definitions.get(plugin_id)

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

        plugin_class: Optional[type[Any]] = None
        factory: Optional[Callable[..., Any]] = None

        if definition.class_name is not None:
            plugin_class = self._resolve_plugin_class(
                definition,
                module,
            )
        else:
            factory = self._resolve_factory(
                definition,
                module,
            )

        descriptor = LoadedPlugin(
            plugin_id=definition.plugin_id,
            module_name=definition.module_name,
            plugin_class=plugin_class,
            factory=factory,
            module=module,
        )

        self._loaded[plugin_id] = descriptor

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

        result: list[LoadedPlugin] = []

        for plugin_id in plugin_ids:
            result.append(
                self.load(plugin_id)
            )

        return tuple(result)

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
        *,
        parent: Any = None,
    ) -> Any:
        """
        Construct one loaded plugin.

        The construction boundary is intentionally strict.

        The ONLY constructor dependency accepted by the loader is:

            parent

        ``parent`` is the Qt ownership reference.

        Application services, controllers, managers, project state,
        tools, renderers, PluginContext, and arbitrary constructor
        arguments are forbidden here.

        Construction and initialization remain separate:

            create()
                ->
            initialize(context)

        Parameters
        ----------
        plugin_id:
            Explicit plugin identifier.

        parent:
            Optional Qt ownership parent.

        Returns
        -------
        Any
            A validated plugin instance.

        Raises
        ------
        TypeError
            If construction violates the loader boundary or produces
            an object that does not satisfy the plugin contract.
        """

        descriptor = self.load(plugin_id)

        plugin = self._construct(
            descriptor,
            parent=parent,
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
        parents: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Construct multiple plugins.

        The only per-plugin constructor dependency permitted is the
        optional Qt parent.

        No arbitrary constructor arguments are accepted.

        Initialization context remains outside this method.
        """

        if parents is not None and not isinstance(
            parents,
            Mapping,
        ):
            raise TypeError(
                "parents must be a Mapping or None."
            )

        parent_map = (
            parents
            if parents is not None
            else {}
        )

        instances: list[Any] = []

        for plugin_id in plugin_ids:
            if plugin_id in parent_map:
                instance = self.create(
                    plugin_id,
                    parent=parent_map[plugin_id],
                )
            else:
                instance = self.create(
                    plugin_id,
                )

            instances.append(instance)

        return tuple(instances)

    # ========================================================
    # CONSTRUCTION
    # ========================================================

    @staticmethod
    def _construct(
        descriptor: LoadedPlugin,
        *,
        parent: Any = None,
    ) -> Any:
        """
        Construct a plugin through its explicitly resolved
        construction mechanism.

        Only the Qt ownership parent is forwarded.

        Factories are therefore also subject to the same construction
        boundary as classes.
        """

        construction_kwargs: dict[str, Any] = {}

        if parent is not None:
            construction_kwargs["parent"] = parent

        if descriptor.factory is not None:
            return descriptor.factory(
                **construction_kwargs,
            )

        if descriptor.plugin_class is not None:
            return descriptor.plugin_class(
                **construction_kwargs,
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

        self._validate_plugin_id(plugin_id)

        return plugin_id in self._loaded

    def get(
        self,
        plugin_id: str,
    ) -> Optional[LoadedPlugin]:
        """Return a loaded descriptor, if present."""

        self._validate_plugin_id(plugin_id)

        return self._loaded.get(plugin_id)

    def require(
        self,
        plugin_id: str,
    ) -> LoadedPlugin:
        """Return a loaded descriptor or raise KeyError."""

        self._validate_plugin_id(plugin_id)

        descriptor = self._loaded.get(plugin_id)

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

        self._validate_plugin_id(plugin_id)

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
    Create the canonical GridForge V2 UI plugin loader.

    Exactly four concrete composition plugins are explicitly defined:

        canvas
        panels
        toolbar
        status
    """

    return PluginLoader(
        definitions=DEFAULT_PLUGIN_IMPLEMENTATIONS
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
```
