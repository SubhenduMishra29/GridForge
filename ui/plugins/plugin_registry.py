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
- The registry owns registered plugin instances.
- PluginStateStore owns observable runtime lifecycle state.
- Registration does not initialize a plugin.
- The registry does not perform plugin discovery.
- The registry does not resolve dependencies.
- The registry does not own application/domain state.
- PluginManager owns lifecycle orchestration and dependency ordering.
- MainWindow remains thin and plugin-driven.

Lifecycle boundary
------------------
PluginRegistry is the low-level lifecycle execution boundary.

It may execute:

    initialize()
    shutdown()

when instructed by PluginManager or another composition owner.

It does NOT decide:

    dependency ordering
    dependency satisfaction
    global lifecycle policy
    composition order

PluginStateStore is updated only with lifecycle results. It is not a
lifecycle manager.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from .plugin_state import (
    PluginStateStore,
)


# ============================================================
# REGISTRY ENTRY
# ============================================================


@dataclass(slots=True)
class PluginEntry:
    """
    Runtime registry entry for one UI plugin.

    PluginEntry owns the association between a plugin ID and its
    concrete plugin instance.

    Runtime lifecycle state is deliberately NOT stored here.

    In particular, PluginEntry does not contain:

        - enabled
        - initialized
        - generation
        - last_error

    Those facts belong to PluginStateStore.
    """

    plugin_id: str

    plugin: Any

    metadata: dict[str, Any] = field(
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

        if self.plugin is None:
            raise ValueError(
                "plugin cannot be None."
            )

        self.metadata = dict(
            self.metadata
        )


# ============================================================
# PLUGIN REGISTRY
# ============================================================


class PluginRegistry:
    """
    Registry for UI composition plugin instances.

    Ownership
    ---------
    PluginRegistry owns:

        - plugin instance registration;
        - plugin instance lookup;
        - registration metadata;
        - low-level lifecycle execution.

    PluginRegistry does NOT own:

        - dependency resolution;
        - lifecycle ordering;
        - composition definitions;
        - application/domain state;
        - concrete plugin imports.

    Runtime state
    -------------
    PluginStateStore is the canonical source for:

        - registered;
        - enabled;
        - initialized;
        - generation;
        - last_error.

    Therefore this registry never maintains a second copy of those
    runtime facts inside PluginEntry.
    """

    def __init__(
        self,
        *,
        state_store: Optional[
            PluginStateStore
        ] = None,
    ) -> None:
        self._entries: dict[
            str,
            PluginEntry,
        ] = {}

        self._state_store = (
            state_store
            if state_store is not None
            else PluginStateStore()
        )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def state_store(self) -> PluginStateStore:
        """
        Return the canonical runtime-state store.

        PluginManager and PluginRegistry should share the same store
        when they participate in the same composition.
        """

        return self._state_store

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
            Mapping[str, Any]
        ] = None,
    ) -> PluginEntry:
        """
        Register a plugin instance.

        Registration does not initialize the plugin.

        The resulting registration and enablement facts are recorded
        in PluginStateStore.
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
            metadata=dict(
                metadata or {}
            ),
        )

        self._entries[
            plugin_id
        ] = entry

        try:
            self._state_store.define(
                plugin_id,
                enabled=enabled,
                metadata=entry.metadata,
            )
        except Exception:
            # Registration must remain atomic from the registry's
            # perspective if state recording fails.
            self._entries.pop(
                plugin_id,
                None,
            )
            raise

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

        If registration of a later plugin fails, previously registered
        plugins remain registered. No implicit rollback policy is
        introduced here.
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

        The registry entry is removed only after successful shutdown.
        Runtime state is removed only after the registry no longer owns
        the plugin instance.
        """

        self._validate_plugin_id(
            plugin_id
        )

        entry = self._entries.get(
            plugin_id
        )

        if entry is None:
            return None

        if (
            shutdown
            and self._state_store.is_initialized(
                plugin_id
            )
        ):
            self._shutdown_entry(
                entry
            )

        elif (
            not shutdown
            and self._state_store.is_initialized(
                plugin_id
            )
        ):
            raise RuntimeError(
                (
                    f"Cannot unregister initialized "
                    f"plugin {plugin_id!r} without shutdown."
                )
            )

        removed = self._entries.pop(
            plugin_id
        )

        # The state record is removed only after the actual registry
        # ownership has been removed successfully.
        self._state_store.remove(
            plugin_id
        )

        return removed

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
        """
        Record the enabled result for a registered plugin.

        Enabling does not initialize the plugin.
        """

        self._require_entry(
            plugin_id
        )

        self._state_store.set_enabled(
            plugin_id,
            True,
        )

    def disable(
        self,
        plugin_id: str,
        *,
        shutdown: bool = True,
    ) -> None:
        """
        Disable a registered plugin.

        If the plugin is initialized, it must be shut down first unless
        the requested operation is rejected by the state store.
        """

        entry = self._require_entry(
            plugin_id
        )

        if (
            shutdown
            and self._state_store.is_initialized(
                plugin_id
            )
        ):
            self._shutdown_entry(
                entry
            )

        self._state_store.set_enabled(
            plugin_id,
            False,
        )

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical enablement state."""

        self._require_entry(
            plugin_id
        )

        return self._state_store.is_enabled(
            plugin_id
        )

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

        This method performs low-level lifecycle execution.

        Dependency ordering and lifecycle policy remain outside the
        registry.
        """

        entry = self._require_entry(
            plugin_id
        )

        state = self._state_store.require(
            plugin_id
        )

        if not state.enabled:
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is disabled."
                )
            )

        if state.initialized:
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
            error = TypeError(
                (
                    f"Plugin {plugin_id!r} "
                    "does not provide initialize()."
                )
            )

            self._state_store.record_error(
                plugin_id,
                error,
            )

            raise error

        try:
            if context is None:
                result = initialize()
            else:
                result = initialize(
                    context
                )

        except Exception as error:
            self._state_store.record_error(
                plugin_id,
                error,
            )
            raise

        self._state_store.set_initialized(
            plugin_id,
            True,
        )

        return result

    def initialize_many(
        self,
        plugin_ids: Optional[
            Iterable[str]
        ] = None,
        *,
        contexts: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> tuple[Any, ...]:
        """
        Initialize multiple registered plugins in explicit caller order.

        Dependency ordering is intentionally not performed here.
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
        """
        Shut down one registered plugin.

        Dependency ordering remains the responsibility of
        PluginManager.
        """

        entry = self._require_entry(
            plugin_id
        )

        if not self._state_store.is_initialized(
            plugin_id
        ):
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
        Shut down registered plugins in the caller-supplied order.

        When no order is supplied, reverse registration order is used.

        Dependency-aware ordering remains the responsibility of
        PluginManager.
        """

        ids = (
            tuple(
                plugin_ids
            )
            if plugin_ids is not None
            else tuple(
                reversed(
                    self.plugin_ids
                )
            )
        )

        for plugin_id in ids:
            self._require_entry(
                plugin_id
            )

            if self._state_store.is_initialized(
                plugin_id
            ):
                self.shutdown(
                    plugin_id
                )

    # ========================================================
    # STATE
    # ========================================================

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical initialization state."""

        self._require_entry(
            plugin_id
        )

        return self._state_store.is_initialized(
            plugin_id
        )

    def initialized_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered IDs whose canonical state is initialized."""

        return tuple(
            plugin_id
            for plugin_id in self.plugin_ids
            if self._state_store.is_initialized(
                plugin_id
            )
        )

    def enabled_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered IDs whose canonical state is enabled."""

        return tuple(
            plugin_id
            for plugin_id in self.plugin_ids
            if self._state_store.is_enabled(
                plugin_id
            )
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
        """Set registry metadata and mirror it in canonical state."""

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

        entry.metadata[key] = value

        self._state_store.set_metadata(
            plugin_id,
            key,
            value,
        )

    def metadata(
        self,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Return a copy of plugin metadata."""

        entry = self._require_entry(
            plugin_id
        )

        return dict(
            entry.metadata
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

        # Registry and state store must remain synchronized at the
        # registration boundary.
        if not self._state_store.contains(
            plugin_id
        ):
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} is registered "
                    "but has no corresponding runtime state."
                )
            )

        return entry

    def _shutdown_entry(
        self,
        entry: PluginEntry,
    ) -> None:
        """
        Execute the plugin shutdown lifecycle operation.

        State is changed only after successful shutdown.

        On failure, the plugin remains initialized and the error is
        recorded in PluginStateStore.
        """

        shutdown = getattr(
            entry.plugin,
            "shutdown",
            None,
        )

        if not callable(
            shutdown
        ):
            error = TypeError(
                (
                    f"Plugin {entry.plugin_id!r} "
                    "does not provide shutdown()."
                )
            )

            self._state_store.record_error(
                entry.plugin_id,
                error,
            )

            raise error

        try:
            shutdown()

        except Exception as error:
            self._state_store.record_error(
                entry.plugin_id,
                error,
            )
            raise

        self._state_store.set_initialized(
            entry.plugin_id,
            False,
        )

    @staticmethod
    def _plugin_widget(
        plugin: Any,
    ) -> Any:
        """
        Return an optional plugin widget after initialization.

        This helper does not impose a widget interface on plugins.
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


def create_plugin_registry(
    *,
    state_store: Optional[
        PluginStateStore
    ] = None,
) -> PluginRegistry:
    """
    Create an empty plugin registry.

    Concrete plugin imports intentionally do not occur here.

    A state store may be supplied so the registry participates in a
    larger composition with a shared canonical runtime-state store.
    """

    return PluginRegistry(
        state_store=state_store,
    )


__all__ = [
    "PluginEntry",
    "PluginRegistry",
    "create_plugin_registry",
]
