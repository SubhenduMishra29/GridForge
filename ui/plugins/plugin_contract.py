"""
GridForge V2
============

File:
    ui/plugins/plugin_contract.py

Purpose
-------
Defines the structural contract shared by GridForge UI composition
plugins.

Architectural rules
-------------------
- This module defines the plugin contract only.
- It does not import concrete plugins.
- It does not contain application/domain logic.
- It does not create application services.
- Qt imports are obtained exclusively through ui.core.qt.
- PluginLoader resolves concrete implementations.
- PluginRegistry stores plugin instances and lifecycle state.
- PluginManager coordinates dependency ordering and lifecycle.
- MainWindow remains thin and plugin-driven.

Lifecycle
---------
Plugin construction and initialization are separate operations.

    PluginLoader
        |
        | create()
        v
    Plugin instance
        |
        | initialize(context)
        v
    Initialized plugin
        |
        | shutdown()
        v
    Uninitialized plugin

PluginContext is an initialization dependency, not a constructor
dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

from ui.core.qt import QObject, QWidget


# ============================================================
# PLUGIN METADATA
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """
    Declarative metadata describing a UI composition plugin.

    Runtime dependency ordering is owned by PluginManager through
    PluginDefinition.

    The dependencies field here is descriptive metadata only and
    must not be treated as a second dependency graph.
    """

    plugin_id: str

    name: str

    version: str = "1.0"

    description: str = ""

    dependencies: tuple[str, ...] = ()

    optional: bool = False

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

        if (
            not isinstance(
                self.name,
                str,
            )
            or not self.name.strip()
        ):
            raise ValueError(
                "name must be a non-empty string."
            )

        if (
            not isinstance(
                self.version,
                str,
            )
            or not self.version.strip()
        ):
            raise ValueError(
                "version must be a non-empty string."
            )

        if not isinstance(
            self.description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        if not isinstance(
            self.dependencies,
            tuple,
        ):
            raise TypeError(
                "dependencies must be a tuple."
            )

        for dependency in self.dependencies:
            if (
                not isinstance(
                    dependency,
                    str,
                )
                or not dependency.strip()
            ):
                raise ValueError(
                    (
                        "dependencies must contain "
                        "non-empty strings."
                    )
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
            self.optional,
            bool,
        ):
            raise TypeError(
                "optional must be bool."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )


# ============================================================
# PLUGIN CONTEXT PROTOCOL
# ============================================================


@runtime_checkable
class PluginContextProtocol(Protocol):
    """
    Structural protocol for the dependency context supplied to
    plugins during initialization.

    The concrete implementation is provided by plugin_context.py.
    """

    main_window: Optional[QWidget]

    parent: Optional[QWidget]

    def service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        ...


# ============================================================
# PLUGIN PROTOCOL
# ============================================================


@runtime_checkable
class PluginProtocol(Protocol):
    """
    Mandatory structural runtime contract for GridForge UI plugins.

    Plugins do not need to inherit from BasePlugin.

    Structural conformance is sufficient.
    """

    plugin_id: str

    plugin_name: str

    plugin_version: str

    def initialize(
        self,
        context: Any = None,
    ) -> Any:
        """
        Initialize the plugin using the supplied context.
        """
        ...

    def shutdown(
        self,
    ) -> None:
        """
        Release plugin-owned runtime resources.
        """
        ...


# ============================================================
# OPTIONAL WIDGET PROVIDER
# ============================================================


@runtime_checkable
class PluginWidgetProvider(Protocol):
    """
    Optional protocol for plugins exposing a primary QWidget.

    Composition plugins are not required to expose a single widget.
    """

    @property
    def widget(self) -> Optional[QWidget]:
        ...


# ============================================================
# OPTIONAL LIFECYCLE HOOKS
# ============================================================


@runtime_checkable
class PluginLifecycleProtocol(Protocol):
    """
    Optional extended lifecycle hooks.

    These hooks are deliberately outside the mandatory plugin
    contract.
    """

    def before_initialize(
        self,
        context: Any,
    ) -> None:
        ...

    def after_initialize(
        self,
    ) -> None:
        ...

    def before_shutdown(
        self,
    ) -> None:
        ...

    def after_shutdown(
        self,
    ) -> None:
        ...


# ============================================================
# BASE PLUGIN
# ============================================================


class BasePlugin(
    QObject,
    ABC,
):
    """
    Optional base implementation of the GridForge plugin contract.

    Construction accepts only Qt ownership information.

    Application/UI dependencies are supplied later through
    initialize(context).

    Lifecycle separation:

        construction
            ->
        initialize(context)
            ->
        shutdown()
    """

    plugin_id: str = ""

    plugin_name: str = ""

    plugin_version: str = "1.0"

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(
            parent
        )

        self._context: Any = None

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(self) -> Any:
        """
        Return the current initialization context.

        Returns None when the plugin is not initialized.
        """

        return self._context

    @property
    def initialized(self) -> bool:
        """Return whether the plugin is currently initialized."""

        return self._initialized

    @property
    def widget(self) -> Optional[QWidget]:
        """
        Return the plugin's primary widget.

        Plugins without a single primary widget return None.
        """

        return None

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        context: Any = None,
    ) -> Any:
        """
        Initialize the plugin.

        Initialization is idempotent.

        A failed initialization always leaves the plugin in the
        uninitialized state with its context cleared.
        """

        if self._initialized:
            return self.widget

        self._context = context

        try:
            self.before_initialize(
                context
            )

            result = self._initialize(
                context
            )

            self.after_initialize()

            self._initialized = True

            return (
                result
                if result is not None
                else self.widget
            )

        except Exception:
            self._initialized = False
            self._context = None
            raise

    def shutdown(self) -> None:
        """
        Shut down the plugin.

        Shutdown is idempotent.

        Runtime state is cleared even when plugin-specific shutdown
        logic raises.
        """

        if not self._initialized:
            return

        shutdown_error: Optional[
            BaseException
        ] = None

        try:
            self.before_shutdown()

            self._shutdown()

        except BaseException as exc:
            shutdown_error = exc

        finally:
            self._initialized = False
            self._context = None

        try:
            self.after_shutdown()

        except BaseException:
            if shutdown_error is None:
                raise

        if shutdown_error is not None:
            raise shutdown_error

    # ========================================================
    # EXTENSION POINTS
    # ========================================================

    def before_initialize(
        self,
        context: Any,
    ) -> None:
        """Hook executed before plugin-specific initialization."""

    def after_initialize(
        self,
    ) -> None:
        """Hook executed after successful plugin initialization."""

    def before_shutdown(
        self,
    ) -> None:
        """Hook executed before plugin-specific shutdown."""

    def after_shutdown(
        self,
    ) -> None:
        """Hook executed after shutdown state has been cleared."""

    @abstractmethod
    def _initialize(
        self,
        context: Any,
    ) -> Any:
        """
        Implement plugin-specific initialization.
        """

    @abstractmethod
    def _shutdown(
        self,
    ) -> None:
        """
        Implement plugin-specific shutdown.
        """


# ============================================================
# CONTRACT VALIDATION
# ============================================================


class PluginContractError(TypeError):
    """Raised when an object does not satisfy the plugin contract."""


def validate_plugin(
    plugin: Any,
    *,
    plugin_id: Optional[str] = None,
) -> None:
    """
    Validate the mandatory runtime plugin contract.

    Structural validation only.

    This function does not:

        - initialize the plugin;
        - create widgets;
        - access application services;
        - modify plugin state.
    """

    if plugin is None:
        raise PluginContractError(
            "Plugin cannot be None."
        )

    actual_plugin_id = getattr(
        plugin,
        "plugin_id",
        None,
    )

    if not isinstance(
        actual_plugin_id,
        str,
    ):
        raise PluginContractError(
            "Plugin must expose a string plugin_id."
        )

    if not actual_plugin_id.strip():
        raise PluginContractError(
            "Plugin plugin_id cannot be empty."
        )

    if plugin_id is not None:
        if (
            not isinstance(
                plugin_id,
                str,
            )
            or not plugin_id.strip()
        ):
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if actual_plugin_id != plugin_id:
            raise PluginContractError(
                (
                    f"Plugin ID mismatch: expected "
                    f"{plugin_id!r}, received "
                    f"{actual_plugin_id!r}."
                )
            )

    plugin_name = getattr(
        plugin,
        "plugin_name",
        None,
    )

    if (
        not isinstance(
            plugin_name,
            str,
        )
        or not plugin_name.strip()
    ):
        raise PluginContractError(
            "Plugin must expose a non-empty plugin_name."
        )

    plugin_version = getattr(
        plugin,
        "plugin_version",
        None,
    )

    if (
        not isinstance(
            plugin_version,
            str,
        )
        or not plugin_version.strip()
    ):
        raise PluginContractError(
            "Plugin must expose a non-empty plugin_version."
        )

    initialize = getattr(
        plugin,
        "initialize",
        None,
    )

    if not callable(
        initialize
    ):
        raise PluginContractError(
            "Plugin must provide callable initialize()."
        )

    shutdown = getattr(
        plugin,
        "shutdown",
        None,
    )

    if not callable(
        shutdown
    ):
        raise PluginContractError(
            "Plugin must provide callable shutdown()."
        )


def is_plugin(
    plugin: Any,
) -> bool:
    """
    Return whether an object satisfies the mandatory plugin contract.
    """

    try:
        validate_plugin(
            plugin
        )
    except (
        PluginContractError,
        TypeError,
        ValueError,
    ):
        return False

    return True


# ============================================================
# DEPENDENCY VALIDATION
# ============================================================


def _validate_dependency_sequence(
    dependencies: Any,
) -> tuple[str, ...]:
    """
    Validate and normalize a plugin dependency declaration.

    Dependency declarations must be explicit sequences of unique,
    non-empty string identifiers.

    Strings are rejected deliberately because a string is iterable
    but is not a valid dependency collection.
    """

    if dependencies is None:
        return ()

    if not isinstance(
        dependencies,
        tuple,
    ):
        raise PluginContractError(
            "plugin_dependencies must be a tuple."
        )

    for dependency in dependencies:
        if (
            not isinstance(
                dependency,
                str,
            )
            or not dependency.strip()
        ):
            raise PluginContractError(
                (
                    "plugin_dependencies must contain "
                    "non-empty strings."
                )
            )

    if len(
        set(dependencies)
    ) != len(
        dependencies
    ):
        raise PluginContractError(
            "plugin_dependencies cannot contain duplicates."
        )

    return dependencies


# ============================================================
# METADATA EXTRACTION
# ============================================================


def plugin_metadata(
    plugin: Any,
) -> PluginMetadata:
    """
    Extract descriptive metadata from a concrete plugin.

    Runtime dependency ordering is not performed here.
    """

    validate_plugin(
        plugin
    )

    dependencies = _validate_dependency_sequence(
        getattr(
            plugin,
            "plugin_dependencies",
            (),
        )
    )

    description = getattr(
        plugin,
        "plugin_description",
        "",
    )

    if not isinstance(
        description,
        str,
    ):
        raise PluginContractError(
            "plugin_description must be a string."
        )

    optional = getattr(
        plugin,
        "plugin_optional",
        False,
    )

    if not isinstance(
        optional,
        bool,
    ):
        raise PluginContractError(
            "plugin_optional must be bool."
        )

    return PluginMetadata(
        plugin_id=plugin.plugin_id,
        name=plugin.plugin_name,
        version=plugin.plugin_version,
        description=description,
        dependencies=dependencies,
        optional=optional,
    )


# ============================================================
# WIDGET EXTRACTION
# ============================================================


def plugin_widget(
    plugin: Any,
) -> Optional[QWidget]:
    """
    Return the primary QWidget exposed by a plugin, if any.

    ``widget`` may be:

        - a QWidget-valued property;
        - a zero-argument callable returning QWidget;
        - None.

    Invalid widget values raise PluginContractError.
    """

    if plugin is None:
        return None

    widget = getattr(
        plugin,
        "widget",
        None,
    )

    if widget is None:
        return None

    if callable(
        widget
    ):
        try:
            widget = widget()
        except TypeError as exc:
            raise PluginContractError(
                (
                    f"Plugin "
                    f"{getattr(plugin, 'plugin_id', '<unknown>')!r} "
                    "widget provider must be callable "
                    "without arguments."
                )
            ) from exc

    if widget is None:
        return None

    if not isinstance(
        widget,
        QWidget,
    ):
        raise PluginContractError(
            (
                f"Plugin "
                f"{getattr(plugin, 'plugin_id', '<unknown>')!r} "
                "exposes a widget that is not a QWidget."
            )
        )

    return widget


# ============================================================
# CONTRACT HELPERS
# ============================================================


def plugin_id(
    plugin: Any,
) -> str:
    """Return a validated plugin ID."""

    validate_plugin(
        plugin
    )

    return plugin.plugin_id


def plugin_dependencies(
    plugin: Any,
) -> tuple[str, ...]:
    """
    Return validated descriptive plugin dependencies.

    These dependencies are metadata only. PluginManager owns the
    authoritative runtime dependency graph.
    """

    validate_plugin(
        plugin
    )

    return _validate_dependency_sequence(
        getattr(
            plugin,
            "plugin_dependencies",
            (),
        )
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginMetadata",
    "PluginContextProtocol",
    "PluginProtocol",
    "PluginWidgetProvider",
    "PluginLifecycleProtocol",
    "BasePlugin",
    "PluginContractError",
    "validate_plugin",
    "is_plugin",
    "plugin_metadata",
    "plugin_widget",
    "plugin_id",
    "plugin_dependencies",
]
