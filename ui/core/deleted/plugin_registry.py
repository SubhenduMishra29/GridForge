# ============================================================
# File: ui/core/plugin_registry.py
# GridForge V2 — UI Plugin Registry
# ============================================================
"""
Central registry for GridForge UI composition plugins.

Purpose
-------
PluginRegistry provides the stable registration and lookup
boundary for UI plugins.

Architecture
------------

    MainWindow
        │
        ▼
    PluginRegistry
        │
        ├── CanvasPlugin
        ├── PanelsPlugin
        ├── ToolbarPlugin
        └── StatusPlugin

The registry stores plugin instances and exposes deterministic
lookup/order information.

IMPORTANT
---------
PluginRegistry intentionally does NOT import concrete plugins.

Concrete plugin loading is an explicit application/bootstrap
responsibility.

For example:

    from ui.plugins.canvas_plugin import CanvasPlugin

    registry.register(
        CanvasPlugin(...)
    )

This prevents the registry from becoming an implicit dependency
loader and avoids circular imports.

Responsibilities
----------------
PluginRegistry:

    - register plugin instances;
    - reject duplicate plugin identifiers;
    - retrieve plugins by identifier;
    - preserve deterministic registration order;
    - unregister plugins;
    - expose registered plugin IDs;
    - provide lifecycle delegation;
    - provide diagnostics.

PluginRegistry does NOT:

    - discover plugin modules;
    - import concrete plugins;
    - instantiate plugins automatically;
    - decide application composition;
    - own MainWindow;
    - own Controller;
    - implement plugin-specific behavior;
    - contain canvas logic;
    - contain toolbar logic;
    - contain panel logic;
    - contain status-bar logic.

Plugin Contract
---------------
A plugin must provide:

    plugin_id

and should provide lifecycle methods as required by the
application composition contract.

The registry accepts plugin objects rather than concrete classes.

This keeps construction and dependency injection outside the
registry.

Lifecycle
---------
The registry supports the following optional lifecycle methods:

    initialize()
    activate()
    deactivate()
    dispose()

Not every plugin is required to implement every lifecycle
operation.

When a lifecycle method is absent, that operation is skipped.

Lifecycle order
---------------
Initialization and activation follow registration order.

Deactivation and disposal follow reverse registration order.

This gives later-registered plugins an opportunity to release
dependencies before earlier infrastructure plugins are removed.

Failure semantics
-----------------
A lifecycle exception is propagated.

The registry does not silently swallow plugin failures.

Registration itself is atomic: a plugin is added only after its
identifier has passed validation and duplicate checks.

Qt Architecture
---------------
This module is intentionally Qt-independent.

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional


class PluginRegistry:
    """
    Registry and lifecycle coordinator for UI plugins.

    The registry owns the registered plugin references but does
    not create plugin instances.

    Concrete plugin imports remain outside this class.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        plugins: Optional[Iterable[Any]] = None,
    ) -> None:
        """
        Initialize the plugin registry.

        Parameters
        ----------
        plugins:
            Optional iterable of already-created plugin instances.

        Notes
        -----
        Plugins are registered in the supplied iteration order.
        """

        self._plugins: dict[str, Any] = {}
        self._order: list[str] = []

        self._initialized = False
        self._active = False
        self._disposed = False

        if plugins is not None:
            for plugin in plugins:
                self.register(plugin)

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _get_plugin_id(
        plugin: Any,
    ) -> str:
        """
        Resolve and validate a plugin identifier.

        The canonical plugin contract is an instance attribute:

            plugin_id

        A callable plugin_id is also accepted for compatibility
        with plugin implementations exposing plugin_id().
        """

        if plugin is None:
            raise ValueError(
                "plugin must not be None."
            )

        plugin_id = getattr(
            plugin,
            "plugin_id",
            None,
        )

        if callable(plugin_id):
            plugin_id = plugin_id()

        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin must provide a string plugin_id."
            )

        plugin_id = plugin_id.strip()

        if not plugin_id:
            raise ValueError(
                "plugin_id must not be empty."
            )

        return plugin_id

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        plugin: Any,
    ) -> str:
        """
        Register an already-created plugin instance.

        Parameters
        ----------
        plugin:
            Concrete plugin instance.

        Returns
        -------
        str
            Registered plugin identifier.

        Raises
        ------
        ValueError
            If the plugin ID is empty or already registered.

        TypeError
            If the plugin does not provide a valid plugin ID.

        Notes
        -----
        The registry does not instantiate the plugin.

        A plugin cannot be registered after the registry has
        entered its disposed state.
        """

        if self._disposed:
            raise RuntimeError(
                "Cannot register a plugin after "
                "PluginRegistry has been disposed."
            )

        plugin_id = self._get_plugin_id(
            plugin
        )

        if plugin_id in self._plugins:
            raise ValueError(
                f"Plugin already registered: "
                f"{plugin_id!r}"
            )

        self._plugins[
            plugin_id
        ] = plugin

        self._order.append(
            plugin_id
        )

        return plugin_id

    # ========================================================
    # UNREGISTRATION
    # ========================================================

    def unregister(
        self,
        plugin_id: str,
    ) -> Any:
        """
        Remove and return a registered plugin.

        This method does not automatically call dispose().

        Lifecycle ownership remains explicit so callers can
        control shutdown ordering.
        """

        plugin_id = self._validate_plugin_id(
            plugin_id
        )

        if plugin_id not in self._plugins:
            raise KeyError(
                f"Plugin is not registered: "
                f"{plugin_id!r}"
            )

        plugin = self._plugins.pop(
            plugin_id
        )

        self._order.remove(
            plugin_id
        )

        return plugin

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        plugin_id: str,
    ) -> Any:
        """
        Return a registered plugin.

        Raises
        ------
        KeyError
            If the plugin is not registered.
        """

        plugin_id = self._validate_plugin_id(
            plugin_id
        )

        try:
            return self._plugins[
                plugin_id
            ]

        except KeyError:
            raise KeyError(
                f"Plugin is not registered: "
                f"{plugin_id!r}"
            ) from None

    # --------------------------------------------------------

    def get_optional(
        self,
        plugin_id: str,
    ) -> Optional[Any]:
        """
        Return a registered plugin or None.
        """

        plugin_id = self._validate_plugin_id(
            plugin_id
        )

        return self._plugins.get(
            plugin_id
        )

    # --------------------------------------------------------

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """
        Return True when plugin_id is registered.
        """

        plugin_id = self._validate_plugin_id(
            plugin_id
        )

        return plugin_id in self._plugins

    # --------------------------------------------------------

    def __contains__(
        self,
        plugin_id: object,
    ) -> bool:
        """
        Support:

            plugin_id in registry
        """

        if not isinstance(
            plugin_id,
            str,
        ):
            return False

        return plugin_id in self._plugins

    # --------------------------------------------------------

    def __getitem__(
        self,
        plugin_id: str,
    ) -> Any:
        """
        Support:

            registry["canvas"]
        """

        return self.get(
            plugin_id
        )

    # ========================================================
    # ORDER / ITERATION
    # ========================================================

    def plugin_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return registered plugin IDs in registration order.
        """

        return tuple(
            self._order
        )

    # --------------------------------------------------------

    def plugins(
        self,
    ) -> tuple[Any, ...]:
        """
        Return registered plugin instances in registration order.
        """

        return tuple(
            self._plugins[
                plugin_id
            ]
            for plugin_id in self._order
        )

    # --------------------------------------------------------

    def __iter__(
        self,
    ):
        """
        Iterate over registered plugin instances in registration
        order.
        """

        return iter(
            self.plugins()
        )

    # --------------------------------------------------------

    def __len__(
        self,
    ) -> int:
        """
        Return the number of registered plugins.
        """

        return len(
            self._plugins
        )

    # ========================================================
    # LIFECYCLE HELPERS
    # ========================================================

    @staticmethod
    def _call_optional(
        plugin: Any,
        method_name: str,
    ) -> Any:
        """
        Invoke an optional plugin lifecycle method.

        Missing lifecycle methods are intentionally ignored.
        """

        method = getattr(
            plugin,
            method_name,
            None,
        )

        if method is None:
            return None

        if not callable(method):
            raise TypeError(
                f"Plugin "
                f"{type(plugin).__name__!r} "
                f"defines non-callable "
                f"{method_name}."
            )

        return method()

    # ========================================================
    # INITIALIZE
    # ========================================================

    def initialize(
        self,
    ) -> None:
        """
        Initialize all registered plugins.

        Plugins are initialized in registration order.

        Calling initialize() more than once is idempotent.
        """

        if self._disposed:
            raise RuntimeError(
                "Cannot initialize a disposed PluginRegistry."
            )

        if self._initialized:
            return

        for plugin_id in self._order:
            self._call_optional(
                self._plugins[
                    plugin_id
                ],
                "initialize",
            )

        self._initialized = True

    # ========================================================
    # ACTIVATE
    # ========================================================

    def activate(
        self,
    ) -> None:
        """
        Activate all registered plugins.

        Initialization is performed automatically if necessary.

        Plugins are activated in registration order.

        Calling activate() more than once is idempotent.
        """

        if self._disposed:
            raise RuntimeError(
                "Cannot activate a disposed PluginRegistry."
            )

        if self._active:
            return

        if not self._initialized:
            self.initialize()

        for plugin_id in self._order:
            self._call_optional(
                self._plugins[
                    plugin_id
                ],
                "activate",
            )

        self._active = True

    # ========================================================
    # DEACTIVATE
    # ========================================================

    def deactivate(
        self,
    ) -> None:
        """
        Deactivate all registered plugins.

        Plugins are deactivated in reverse registration order.

        Calling deactivate() while inactive is idempotent.
        """

        if not self._active:
            return

        for plugin_id in reversed(
            self._order
        ):
            self._call_optional(
                self._plugins[
                    plugin_id
                ],
                "deactivate",
            )

        self._active = False

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose all registered plugins.

        If active, plugins are first deactivated.

        Disposal occurs in reverse registration order.

        The registry itself remains allocated but cannot accept
        new plugins after disposal.
        """

        if self._disposed:
            return

        if self._active:
            self.deactivate()

        for plugin_id in reversed(
            self._order
        ):
            self._call_optional(
                self._plugins[
                    plugin_id
                ],
                "dispose",
            )

        self._disposed = True

    # ========================================================
    # STATE
    # ========================================================

    @property
    def initialized(
        self,
    ) -> bool:
        """
        Return True when plugin initialization has completed.
        """

        return self._initialized

    # --------------------------------------------------------

    @property
    def active(
        self,
    ) -> bool:
        """
        Return True when plugins are currently active.
        """

        return self._active

    # --------------------------------------------------------

    @property
    def disposed(
        self,
    ) -> bool:
        """
        Return True when the registry has been disposed.
        """

        return self._disposed

    # ========================================================
    # STATE / DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of registry state.
        """

        return {
            "plugin_count": len(
                self._plugins
            ),
            "plugin_ids": self.plugin_ids(),
            "initialized": self._initialized,
            "active": self._active,
            "disposed": self._disposed,
        }

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> str:
        """
        Validate a plugin identifier supplied by callers.
        """

        if not isinstance(
            plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        plugin_id = plugin_id.strip()

        if not plugin_id:
            raise ValueError(
                "plugin_id must not be empty."
            )

        return plugin_id

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "PluginRegistry("
            f"plugins={self.plugin_ids()}, "
            f"initialized={self._initialized}, "
            f"active={self._active}, "
            f"disposed={self._disposed}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PluginRegistry",
]
