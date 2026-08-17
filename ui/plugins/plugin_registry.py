"""
GridForge V2
============

File:
    ui/plugins/plugin_registry.py

Purpose
-------
Generic registry for GridForge UI composition plugins.

Architectural rules
-------------------
- The registry does NOT import concrete plugin implementations.
- Concrete plugin imports are handled explicitly by plugin_loader.py.
- The registry stores plugin descriptors/instances only.
- Registration does not initialize a plugin.
- The registry does not perform plugin discovery.
- The registry does not create Core/domain state.
- MainWindow remains thin and plugin-driven.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional


# ============================================================
# REGISTRY ENTRY
# ============================================================


@dataclass(slots=True)
class PluginEntry:
    """
    Runtime registry entry for one UI plugin.

    The registry is intentionally implementation-agnostic. A plugin
    object is supplied by the explicit loader or application
    composition layer.
    """

    plugin_id: str

    plugin: Any

    enabled: bool = True

    initialized: bool = False

    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.plugin_id,
            str,
        ) or not self.plugin_id.strip():
            raise ValueError(
                "plugin_id must be a non-empty string."
            )

        if self.metadata is None:
            self.metadata = {}


# ============================================================
# PLUGIN REGISTRY
# ============================================================


class PluginRegistry:
    """
    Registry for UI composition plugins.

    PluginRegistry deliberately contains no concrete imports.

    Typical flow::

        loader = create_default_plugin_loader()

        descriptor = loader.load("canvas")

        plugin = loader.create("canvas")

        registry.register(
            descriptor.plugin_id,
            plugin,
        )

        registry.initialize("canvas")

    The loader is responsible for resolving concrete implementations;
    this registry is responsible only for lifecycle registration and
    lookup.
    """

    def __init__(self) -> None:
        self._entries: dict[
            str,
            PluginEntry,
        ] = {}

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def plugin_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered plugin IDs in registration order."""

        return tuple(
            self._entries.keys()
        )

    @property
    def plugins(
        self,
    ) -> tuple[Any, ...]:
        """Return registered plugin instances."""

        return tuple(
            entry.plugin
            for entry in self._entries.values()
        )

    @property
    def entries(
        self,
    ) -> tuple[PluginEntry, ...]:
        """Return registered plugin entries."""

        return tuple(
            self._entries.values()
        )

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        plugin_id: str,
        plugin: Any,
        *,
        enabled: bool = True,
        metadata: Optional[
            dict[str, Any]
        ] = None,
    ) -> PluginEntry:
        """
        Register a plugin instance.

        Duplicate IDs are rejected. Registration does not initialize
        the plugin.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin is None:
            raise ValueError(
                "plugin cannot be None."
            )

        if plugin_id in self._entries:
            raise ValueError(
                (
                    f"Plugin {plugin_id!r} "
                    "is already registered."
                )
            )

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        entry = PluginEntry(
            plugin_id=plugin_id,
            plugin=plugin,
            enabled=enabled,
            initialized=False,
            metadata=dict(
                metadata or {}
            ),
        )

        self._entries[
            plugin_id
        ] = entry

        return entry

    def register_many(
        self,
        plugins: Iterable[
            tuple[str, Any]
        ],
    ) -> tuple[PluginEntry, ...]:
        """
        Register multiple plugin instances.

        Registration order is preserved.
        """

        registered: list[
            PluginEntry
        ] = []

        for plugin_id, plugin in plugins:
            registered.append(
                self.register(
                    plugin_id,
                    plugin,
                )
            )

        return tuple(
            registered
        )

    def unregister(
        self,
        plugin_id: str,
        *,
        shutdown: bool = True,
    ) -> Optional[PluginEntry]:
        """
        Remove a plugin from the registry.

        By default, an initialized plugin is shut down before removal.
        The registry does not destroy arbitrary plugin objects.
        """

        self._validate_plugin_id(
            plugin_id
        )

        entry = self._entries.get(
            plugin_id
        )

        if entry is None:
            return None

        # Preserve registry state until shutdown succeeds. If plugin
        # shutdown raises, the initialized entry remains registered and
        # accurately reflects the live runtime object.
        if (
            shutdown
            and entry.initialized
        ):
            self._shutdown_entry(
                entry
            )

        self._entries.pop(
            plugin_id,
            None,
        )

        return entry

    def clear(
        self,
        *,
        shutdown: bool = True,
    ) -> None:
        """Remove all registered plugins."""

        plugin_ids = tuple(
            self._entries.keys()
        )

        for plugin_id in plugin_ids:
            self.unregister(
                plugin_id,
                shutdown=shutdown,
            )

    # ========================================================
    # LOOKUP
    # ========================================================

    def get(
        self,
        plugin_id: str,
    ) -> Optional[Any]:
        """Return a registered plugin instance."""

        entry = self._entries.get(
            plugin_id
        )

        if entry is None:
            return None

        return entry.plugin

    def get_entry(
        self,
        plugin_id: str,
    ) -> Optional[PluginEntry]:
        """Return a registered plugin entry."""

        return self._entries.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> Any:
        """
        Return a registered plugin or raise KeyError.
        """

        plugin = self.get(
            plugin_id
        )

        if plugin is None:
            raise KeyError(
                (
                    f"Plugin {plugin_id!r} "
                    "is not registered."
                )
            )

        return plugin

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is registered."""

        return plugin_id in self._entries

    def __contains__(
        self,
        plugin_id: object,
    ) -> bool:
        """Support ``plugin_id in registry``."""

        return (
            isinstance(
                plugin_id,
                str,
            )
            and plugin_id in self._entries
        )

    def __len__(self) -> int:
        """Return the number of registered plugins."""

        return len(
            self._entries
        )

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(
        self,
        plugin_id: str,
    ) -> None:
        """Enable a registered plugin."""

        entry = self._require_entry(
            plugin_id
        )

        entry.enabled = True

    def disable(
        self,
        plugin_id: str,
        *,
        shutdown: bool = True,
    ) -> None:
        """
        Disable a registered plugin.

        If the plugin is initialized, it is shut down by default.
        """

        entry = self._require_entry(
            plugin_id
        )

        if shutdown and entry.initialized:
            self._shutdown_entry(
                entry
            )

        entry.enabled = False

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is enabled."""

        return self._require_entry(
            plugin_id
        ).enabled

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def initialize(
        self,
        plugin_id: str,
        *,
        context: Any = None,
    ) -> Any:
        """
        Initialize one registered plugin.

        The registry supports the conventional ``initialize(context)``
        contract but does not impose a concrete plugin base class.
        """

        entry = self._require_entry(
            plugin_id
        )

        if not entry.enabled:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is disabled."
                )
            )

        if entry.initialized:
            return self._plugin_widget(
                entry.plugin
            )

        initialize = getattr(
            entry.plugin,
            "initialize",
            None,
        )

        if not callable(
            initialize
        ):
            raise TypeError(
                (
                    f"Plugin {plugin_id!r} "
                    "does not provide initialize()."
                )
            )

        if context is None:
            result = initialize()
        else:
            result = initialize(
                context
            )

        entry.initialized = True

        return result

    def initialize_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
        *,
        contexts: Optional[
            dict[str, Any]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Initialize multiple registered plugins in explicit order.
        """

        ids = (
            tuple(
                plugin_ids
            )
            if plugin_ids is not None
            else self.plugin_ids
        )

        contexts = contexts or {}

        results: list[Any] = []

        for plugin_id in ids:
            results.append(
                self.initialize(
                    plugin_id,
                    context=contexts.get(
                        plugin_id
                    ),
                )
            )

        return tuple(
            results
        )

    def shutdown(
        self,
        plugin_id: str,
    ) -> None:
        """Shut down one registered plugin."""

        entry = self._require_entry(
            plugin_id
        )

        if not entry.initialized:
            return

        self._shutdown_entry(
            entry
        )

    def shutdown_all(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
    ) -> None:
        """
        Shut down registered plugins.

        Shutdown occurs in reverse registration order to provide a
        predictable composition teardown sequence.
        """

        ids = (
            tuple(
                plugin_ids
            )
            if plugin_ids is not None
            else self.plugin_ids
        )

        for plugin_id in reversed(
            ids
        ):
            entry = self._require_entry(
                plugin_id
            )

            if entry.initialized:
                self._shutdown_entry(
                    entry
                )

    # ========================================================
    # STATE
    # ========================================================

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin has been initialized."""

        return self._require_entry(
            plugin_id
        ).initialized

    def initialized_ids(
        self,
    ) -> tuple[str, ...]:
        """Return initialized plugin IDs."""

        return tuple(
            entry.plugin_id
            for entry in self._entries.values()
            if entry.initialized
        )

    def enabled_ids(
        self,
    ) -> tuple[str, ...]:
        """Return enabled plugin IDs."""

        return tuple(
            entry.plugin_id
            for entry in self._entries.values()
            if entry.enabled
        )

    # ========================================================
    # METADATA
    # ========================================================

    def set_metadata(
        self,
        plugin_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set registry metadata for a plugin."""

        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "metadata key must be a non-empty string."
            )

        entry = self._require_entry(
            plugin_id
        )

        assert entry.metadata is not None

        entry.metadata[
            key
        ] = value

    def metadata(
        self,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Return a copy of plugin metadata."""

        entry = self._require_entry(
            plugin_id
        )

        return dict(
            entry.metadata or {}
        )

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _require_entry(
        self,
        plugin_id: str,
    ) -> PluginEntry:
        """Return an entry or raise KeyError."""

        self._validate_plugin_id(
            plugin_id
        )

        entry = self._entries.get(
            plugin_id
        )

        if entry is None:
            raise KeyError(
                (
                    f"Plugin {plugin_id!r} "
                    "is not registered."
                )
            )

        return entry

    @staticmethod
    def _shutdown_entry(
        entry: PluginEntry,
    ) -> None:
        """
        Shut down a plugin through its explicit lifecycle contract.
        """

        shutdown = getattr(
            entry.plugin,
            "shutdown",
            None,
        )

        if not callable(
            shutdown
        ):
            raise TypeError(
                (
                    f"Plugin {entry.plugin_id!r} "
                    "does not provide shutdown()."
                )
            )

        shutdown()

        entry.initialized = False

    @staticmethod
    def _plugin_widget(
        plugin: Any,
    ) -> Any:
        """
        Return an optional plugin widget after initialization.

        This helper avoids imposing a widget interface on every plugin.
        """

        widget = getattr(
            plugin,
            "widget",
            None,
        )

        if callable(
            widget
        ):
            widget = widget()

        return widget

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
# FACTORY
# ============================================================


def create_plugin_registry() -> PluginRegistry:
    """
    Create an empty plugin registry.

    Concrete plugin imports intentionally do not occur here.
    """

    return PluginRegistry()


__all__ = [
    "PluginEntry",
    "PluginRegistry",
    "create_plugin_registry",
]
