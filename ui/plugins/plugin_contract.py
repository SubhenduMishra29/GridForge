"""
GridForge V2
============

File:
    ui/plugins/plugin_contract.py

Purpose
-------
Defines the structural contract shared by GridForge UI composition
plugins.

Architectural role
------------------
This module defines plugin contracts and contract-level validation.

It does NOT:

    - import concrete plugins;
    - discover plugins;
    - create application services;
    - perform application/domain logic;
    - manage plugin registration;
    - manage plugin dependency ordering;
    - own the runtime dependency graph.

Runtime responsibilities are separated as follows:

    PluginLoader
        concrete plugin import and construction

    PluginRegistry
        plugin storage and registration

    PluginManager
        dependency ordering and lifecycle orchestration

    PluginContext
        dependency carrier supplied during initialization

    PluginContract
        structural contracts and contract validation

Lifecycle
---------
Plugin construction and initialization are separate operations.

    PluginLoader
        |
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

Qt
--
All Qt access is obtained exclusively through ``ui.core.qt``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import (
    Any,
    Mapping,
    Optional,
    Protocol,
    runtime_checkable,
)

from ui.core.qt import (
    QObject,
    QWidget,
)


# ============================================================
# PLUGIN METADATA
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """
    Immutable descriptive metadata for one UI composition plugin.

    Dependency information contained here is declarative metadata.
    Runtime dependency ordering remains the responsibility of
    PluginManager.
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
        """Validate and freeze plugin metadata."""

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

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


# ============================================================
# PLUGIN CONTEXT PROTOCOL
# ============================================================


@runtime_checkable
class PluginContextProtocol(Protocol):
    """
    Structural dependency-context contract.

    The concrete implementation is provided by:

        ui.plugins.plugin_context.PluginContext

    The protocol intentionally exposes only the generic dependency
    surface required by contract-level plugin infrastructure.

    Concrete plugins may depend on the explicit fields provided by
    PluginContext when their architectural contract requires them.
    """

    main_window: Optional[QWidget]

    parent: Optional[QWidget]

    def service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return an optional extension service.
        """
        ...


# ============================================================
# PLUGIN PROTOCOL
# ============================================================


@runtime_checkable
class PluginProtocol(Protocol):
    """
    Mandatory structural runtime contract for GridForge plugins.

    Concrete plugins do not have to inherit from BasePlugin.

    Structural conformance is sufficient.

    Required metadata:

        plugin_id
        plugin_name
        plugin_version

    Required lifecycle:

        initialize()
        shutdown()
    """

    plugin_id: str

    plugin_name: str

    plugin_version: str

    def initialize(
        self,
        context: Optional[
            PluginContextProtocol
        ] = None,
    ) -> Any:
        """
        Initialize the plugin.

        Concrete plugins may expose a narrower initialization
        signature where required by their established lifecycle
        implementation.
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
    Optional contract for plugins exposing a primary QWidget.

    A composition plugin is not required to expose one widget.

    Plugins such as dock/panel composition plugins may legitimately
    return None because their presentation consists of multiple
    independently composed widgets.
    """

    @property
    def widget(
        self,
    ) -> Optional[QWidget]:
        """
        Return the primary plugin widget, if one exists.
        """
        ...


# ============================================================
# OPTIONAL LIFECYCLE HOOKS
# ============================================================


@runtime_checkable
class PluginLifecycleProtocol(Protocol):
    """
    Optional lifecycle-hook contract.

    Individual hooks are optional in practice.

    PluginManager must therefore inspect each hook independently
    instead of requiring a plugin to implement every hook.
    """

    def before_initialize(
        self,
        context: PluginContextProtocol,
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
    Optional abstract base implementation of PluginProtocol.

    Construction accepts only Qt ownership information.

    Application and UI dependencies are supplied during
    ``initialize(context)``.

    Lifecycle:

        construction
            ->
        initialize(context)
            ->
        initialized
            ->
        shutdown()
            ->
        uninitialized
    """

    plugin_id: str = ""

    plugin_name: str = ""

    plugin_version: str = "1.0"

    plugin_description: str = ""

    plugin_dependencies: tuple[str, ...] = ()

    plugin_optional: bool = False

    plugin_metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __init__(
        self,
        parent: Optional[QObject] = None,
    ) -> None:
        """
        Construct an uninitialized plugin.

        No application services or UI dependencies are resolved here.
        """

        super().__init__(
            parent
        )

        self._context: Optional[
            PluginContextProtocol
        ] = None

        self._initialized = False

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def context(
        self,
    ) -> Optional[PluginContextProtocol]:
        """
        Return the active initialization context.

        Returns None while the plugin is uninitialized.
        """

        return self._context

    @property
    def initialized(
        self,
    ) -> bool:
        """
        Return whether the plugin is currently initialized.
        """

        return self._initialized

    @property
    def widget(
        self,
    ) -> Optional[QWidget]:
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
        context: Optional[
            PluginContextProtocol
        ] = None,
    ) -> Any:
        """
        Initialize the plugin.

        Initialization is idempotent.

        A failed initialization leaves the plugin uninitialized and
        clears the stored context.
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

            if result is not None:
                return result

            return self.widget

        except Exception:
            self._initialized = False
            self._context = None
            raise

    def shutdown(
        self,
    ) -> None:
        """
        Shut down the plugin.

        Shutdown is idempotent.

        Plugin lifecycle state is cleared even if plugin-specific
        shutdown logic raises.
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
    # LIFECYCLE HOOKS
    # ========================================================

    def before_initialize(
        self,
        context: Optional[
            PluginContextProtocol
        ],
    ) -> None:
        """
        Hook executed before plugin-specific initialization.
        """

    def after_initialize(
        self,
    ) -> None:
        """
        Hook executed after successful plugin initialization.
        """

    def before_shutdown(
        self,
    ) -> None:
        """
        Hook executed before plugin-specific shutdown.
        """

    def after_shutdown(
        self,
    ) -> None:
        """
        Hook executed after plugin lifecycle state is cleared.
        """

    # ========================================================
    # ABSTRACT IMPLEMENTATION
    # ========================================================

    @abstractmethod
    def _initialize(
        self,
        context: Optional[
            PluginContextProtocol
        ],
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
# CONTRACT ERROR
# ============================================================


class PluginContractError(TypeError):
    """
    Raised when an object violates the GridForge plugin contract.
    """


# ============================================================
# CONTRACT VALIDATION
# ============================================================


def validate_plugin(
    plugin: Any,
    *,
    plugin_id: Optional[str] = None,
) -> None:
    """
    Validate the mandatory structural plugin contract.

    Validation is side-effect free.

    This function does not:

        - initialize the plugin;
        - construct widgets;
        - resolve dependencies;
        - access application services;
        - register the plugin;
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
    Validate a plugin dependency declaration.

    Dependency declarations must be explicit tuples containing
    unique, non-empty string identifiers.

    Strings and arbitrary iterables are deliberately rejected.
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
    Extract validated descriptive metadata from a plugin.

    Dependency information returned here remains descriptive.
    Runtime dependency ordering belongs to PluginManager.
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

    metadata = getattr(
        plugin,
        "plugin_metadata",
        {},
    )

    if not isinstance(
        metadata,
        Mapping,
    ):
        raise PluginContractError(
            "plugin_metadata must be a Mapping."
        )

    return PluginMetadata(
        plugin_id=plugin.plugin_id,
        name=plugin.plugin_name,
        version=plugin.plugin_version,
        description=description,
        dependencies=dependencies,
        optional=optional,
        metadata=metadata,
    )


# ============================================================
# WIDGET EXTRACTION
# ============================================================


def plugin_widget(
    plugin: Any,
) -> Optional[QWidget]:
    """
    Return the primary QWidget exposed by a plugin.

    Supported forms:

        - QWidget-valued property;
        - zero-argument callable returning QWidget;
        - None.

    Invalid widget providers raise PluginContractError.
    """

    if plugin is None:
        return None

    plugin_identifier = getattr(
        plugin,
        "plugin_id",
        "<unknown>",
    )

    try:
        widget = getattr(
            plugin,
            "widget",
            None,
        )

    except Exception as exc:
        raise PluginContractError(
            (
                f"Plugin {plugin_identifier!r} "
                "widget provider could not be accessed."
            )
        ) from exc

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
                    f"Plugin {plugin_identifier!r} "
                    "widget provider must be callable "
                    "without arguments."
                )
            ) from exc

        except Exception as exc:
            raise PluginContractError(
                (
                    f"Plugin {plugin_identifier!r} "
                    "widget provider failed."
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
                f"Plugin {plugin_identifier!r} "
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
    """
    Return the validated plugin identifier.
    """

    validate_plugin(
        plugin
    )

    return plugin.plugin_id


def plugin_dependencies(
    plugin: Any,
) -> tuple[str, ...]:
    """
    Return the validated descriptive dependency declaration.

    This function does not construct or resolve dependencies.

    PluginManager owns the authoritative runtime dependency graph.
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
