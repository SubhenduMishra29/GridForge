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
- The contract is UI/framework-facing only.
- It does not import concrete plugins.
- It does not contain application/domain logic.
- It does not create widgets or services.
- PluginLoader performs concrete implementation resolution.
- PluginRegistry stores plugin instances.
- PluginManager coordinates lifecycle.
- MainWindow remains thin and plugin-driven.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


# ============================================================
# PLUGIN METADATA
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """
    Descriptive metadata for a UI plugin.

    Metadata is declarative and does not represent runtime state.
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
        if not isinstance(
            self.plugin_id,
            str,
        ) or not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if not isinstance(
            self.name,
            str,
        ) or not self.name.strip():
            raise ValueError(
                "name must be a non-empty string."
            )

        if not isinstance(
            self.version,
            str,
        ) or not self.version.strip():
            raise ValueError(
                "version must be a non-empty string."
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
# PLUGIN CONTEXT PROTOCOL
# ============================================================


@runtime_checkable
class PluginContextProtocol(Protocol):
    """
    Structural protocol for plugin dependency contexts.

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
    Structural runtime contract for GridForge UI plugins.

    Plugins do not need to inherit from a common base class to satisfy
    this protocol. This permits composition with existing concrete
    implementations while keeping the registry generic.
    """

    plugin_id: str

    plugin_name: str

    plugin_version: str

    def initialize(
        self,
        context: Any = None,
    ) -> Any:
        """
        Initialize the plugin and compose its UI contribution.
        """
        ...

    def shutdown(self) -> None:
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
    Optional protocol for plugins that expose a primary widget.
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
    Optional extended lifecycle contract.

    The basic PluginProtocol remains sufficient for plugins that do
    not require explicit lifecycle phases.
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

    Concrete plugins may inherit from this class, but the architecture
    does not require inheritance because PluginProtocol is structural.
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
        """Return the current plugin context."""

        return self._context

    @property
    def initialized(self) -> bool:
        """Return whether the plugin is initialized."""

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
        Execute the standard initialization lifecycle.

        Initialization is idempotent.
        """

        if self._initialized:
            return self.widget

        self._context = context

        self.before_initialize(
            context
        )

        result = self._initialize(
            context
        )

        self._initialized = True

        self.after_initialize()

        return (
            result
            if result is not None
            else self.widget
        )

    def shutdown(self) -> None:
        """
        Execute the standard shutdown lifecycle.

        Shutdown is idempotent.
        """

        if not self._initialized:
            return

        self.before_shutdown()

        self._shutdown()

        self._initialized = False
        self._context = None

        self.after_shutdown()

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
        """Hook executed after plugin-specific initialization."""

    def before_shutdown(
        self,
    ) -> None:
        """Hook executed before plugin-specific shutdown."""

    def after_shutdown(
        self,
    ) -> None:
        """Hook executed after plugin-specific shutdown."""

    @abstractmethod
    def _initialize(
        self,
        context: Any,
    ) -> Any:
        """
        Implement plugin-specific initialization.
        """

    @abstractmethod
    def _shutdown(self) -> None:
        """
        Implement plugin-specific shutdown.
        """


# ============================================================
# CONTRACT VALIDATION
# ============================================================


class PluginContractError(
    TypeError
):
    """Raised when an object does not satisfy the plugin contract."""


def validate_plugin(
    plugin: Any,
    *,
    plugin_id: Optional[str] = None,
) -> None:
    """
    Validate the minimum runtime plugin contract.

    This function performs structural validation only. It does not
    initialize the plugin.
    """

    if plugin is None:
        raise PluginContractError(
            "Plugin cannot be None."
        )

    if not isinstance(
        getattr(
            plugin,
            "plugin_id",
            None,
        ),
        str,
    ):
        raise PluginContractError(
            "Plugin must expose a string plugin_id."
        )

    if not getattr(
        plugin,
        "plugin_id",
    ).strip():
        raise PluginContractError(
            "Plugin plugin_id cannot be empty."
        )

    if plugin_id is not None:
        if plugin.plugin_id != plugin_id:
            raise PluginContractError(
                (
                    f"Plugin ID mismatch: expected "
                    f"{plugin_id!r}, received "
                    f"{plugin.plugin_id!r}."
                )
            )

    plugin_name = getattr(
        plugin,
        "plugin_name",
        None,
    )

    if not isinstance(
        plugin_name,
        str,
    ) or not plugin_name.strip():
        raise PluginContractError(
            "Plugin must expose a non-empty plugin_name."
        )

    plugin_version = getattr(
        plugin,
        "plugin_version",
        None,
    )

    if not isinstance(
        plugin_version,
        str,
    ) or not plugin_version.strip():
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
    Return whether an object satisfies the runtime plugin contract.
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
# METADATA EXTRACTION
# ============================================================


def plugin_metadata(
    plugin: Any,
) -> PluginMetadata:
    """
    Extract PluginMetadata from a concrete plugin object.

    Concrete plugins may optionally expose ``plugin_description``,
    ``plugin_dependencies``, and ``plugin_optional`` attributes.
    """

    validate_plugin(
        plugin
    )

    dependencies = getattr(
        plugin,
        "plugin_dependencies",
        (),
    )

    if dependencies is None:
        dependencies = ()

    return PluginMetadata(
        plugin_id=plugin.plugin_id,
        name=plugin.plugin_name,
        version=plugin.plugin_version,
        description=str(
            getattr(
                plugin,
                "plugin_description",
                "",
            )
        ),
        dependencies=tuple(
            dependencies
        ),
        optional=bool(
            getattr(
                plugin,
                "plugin_optional",
                False,
            )
        ),
    )


# ============================================================
# WIDGET EXTRACTION
# ============================================================


def plugin_widget(
    plugin: Any,
) -> Optional[QWidget]:
    """
    Return the primary widget exposed by a plugin, if any.

    A plugin may expose ``widget`` either as a property or as a
    zero-argument method.
    """

    if plugin is None:
        return None

    widget = getattr(
        plugin,
        "widget",
        None,
    )

    if callable(
        widget
    ):
        widget = widget()

    if widget is None:
        return None

    if not isinstance(
        widget,
        QWidget,
    ):
        raise PluginContractError(
            (
                f"Plugin {getattr(plugin, 'plugin_id', '<unknown>')!r} "
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
    """Return declared plugin dependencies."""

    validate_plugin(
        plugin
    )

    dependencies = getattr(
        plugin,
        "plugin_dependencies",
        (),
    )

    if dependencies is None:
        return ()

    return tuple(
        dependencies
    )


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
