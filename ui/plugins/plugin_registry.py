"""
GridForge V2
============

File:
    ui/plugins/plugin_registry.py

Purpose
-------
Low-level runtime registry for explicitly constructed UI plugins.

Architectural rules
-------------------
- PluginRegistry does not discover plugins.
- PluginRegistry does not import concrete plugin implementations.
- PluginRegistry does not construct plugins.
- PluginRegistry does not resolve dependencies.
- PluginRegistry does not assign dependency ordering.
- PluginRegistry does not own PluginContext.
- PluginRegistry does not own Core/domain state.
- PluginRegistry does not construct Qt widgets.
- PluginManager owns orchestration and dependency ordering.
- PluginLoader owns concrete-plugin loading and construction.
- PluginStateStore owns observable runtime lifecycle state.

Lifecycle ownership
-------------------
PluginManager decides:

    WHAT should happen
    WHEN it should happen
    IN WHICH dependency order it should happen

PluginRegistry performs:

    register
    initialize
    shutdown
    unregister
    enable
    disable

PluginStateStore records:

    registered
    enabled
    initialized
    generation
    last_error
    metadata

PluginEntry is only a runtime handle to a registered plugin instance.
It is NOT the runtime lifecycle-state authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .plugin_contract import validate_plugin
from .plugin_state import PluginStateStore


# ============================================================
# PLUGIN ENTRY
# ============================================================


@dataclass(slots=True)
class PluginEntry:
    """
    Runtime handle for one registered plugin.

    PluginEntry deliberately contains only:

        plugin_id
        plugin instance
        metadata

    Runtime lifecycle state belongs exclusively to
    PluginStateStore.
    """

    plugin_id: str

    plugin: Any

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Validate and normalize the runtime entry."""

        if not isinstance(
            self.plugin_id,
            str,
        ):
            raise TypeError(
                "plugin_id must be a string."
            )

        if not self.plugin_id.strip():
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
    Low-level runtime registry and lifecycle execution boundary.

    Responsibilities
    ----------------
    1. Register already-constructed plugin instances.
    2. Validate plugin contracts.
    3. Initialize registered plugins.
    4. Shut down initialized plugins.
    5. Unregister plugins.
    6. Enable and disable plugins.
    7. Synchronize lifecycle state with PluginStateStore.
    8. Expose registered plugin instances.

    Non-responsibilities
    --------------------
    - Plugin discovery.
    - Concrete plugin imports.
    - Plugin construction.
    - Dependency resolution.
    - Dependency ordering.
    - Plugin definitions.
    - Plugin context ownership.
    - Core/domain state.
    - Qt application ownership.
    - UI composition.
    """

    def __init__(
        self,
        *,
        state_store: PluginStateStore | None = None,
    ) -> None:
        self._state_store = (
            state_store
            if state_store is not None
            else PluginStateStore()
        )

        self._entries: dict[
            str,
            PluginEntry,
        ] = {}

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def state_store(self) -> PluginStateStore:
        """
        Return the canonical runtime state store.

        PluginRegistry does not maintain a second lifecycle-state model.
        """

        return self._state_store

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        """Return registered plugin IDs in registration order."""

        return tuple(
            self._entries.keys()
        )

    @property
    def entries(self) -> tuple[PluginEntry, ...]:
        """
        Return registered runtime entries in registration order.

        Lifecycle state is not stored in PluginEntry. Consumers requiring
        lifecycle state must query PluginStateStore.
        """

        return tuple(
            self._entries.values()
        )

    @property
    def count(self) -> int:
        """Return the number of registered plugins."""

        return len(
            self._entries
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
        metadata: Mapping[str, Any] | None = None,
    ) -> PluginEntry:
        """
        Register an already-constructed plugin.

        Registration performs:

            validate plugin ID
            reject duplicate registration
            validate plugin contract
            create runtime entry
            record registration state

        Registration does NOT initialize the plugin.

        Dependency handling is outside this class.

        Raises
        ------
        KeyError
            If the plugin ID is already registered.

        TypeError / ValueError
            If the plugin ID, plugin, or enabled flag is invalid.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id in self._entries:
            raise KeyError(
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

        validate_plugin(
            plugin,
            plugin_id=plugin_id,
        )

        entry = PluginEntry(
            plugin_id=plugin_id,
            plugin=plugin,
            metadata=(
                {}
                if metadata is None
                else dict(metadata)
            ),
        )

        self._entries[
            plugin_id
        ] = entry

        try:
            self._state_store.register(
                plugin_id,
                enabled=enabled,
                metadata=entry.metadata,
            )
        except Exception:
            self._entries.pop(
                plugin_id,
                None,
            )
            raise

        return entry

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(
        self,
        plugin_id: str,
        *,
        context: Any = None,
    ) -> Any:
        """
        Initialize one registered plugin.

        Dependency ordering is deliberately not handled here.

        PluginManager must establish dependency ordering before invoking
        this method.

        Parameters
        ----------
        plugin_id:
            Registered plugin identifier.

        context:
            PluginContext supplied by the lifecycle owner.

        Returns
        -------
        Any
            Value returned by the plugin's initialize() method.

        Notes
        -----
        Successful initialization is recorded only after the plugin
        lifecycle call returns successfully.
        """

        entry = self._require_entry(
            plugin_id
        )

        if not self.is_enabled(
            plugin_id
        ):
            raise RuntimeError(
                (
                    f"Plugin {plugin_id!r} "
                    "is disabled."
                )
            )

        if self.is_initialized(
            plugin_id
        ):
            return None

        try:
            result = entry.plugin.initialize(
                context
            )
        except Exception as exc:
            self._state_store.set_last_error(
                plugin_id,
                exc,
            )
            raise

        try:
            self._state_store.mark_initialized(
                plugin_id
            )

            self._state_store.clear_last_error(
                plugin_id
            )
        except Exception:
            # The plugin has already initialized successfully, but
            # the canonical state transition failed. Do not silently
            # hide the registry/state inconsistency.
            raise

        return result

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def shutdown(
        self,
        plugin_id: str,
    ) -> None:
        """
        Shut down one initialized plugin.

        Dependency ordering is deliberately not handled here.

        PluginManager is responsible for invoking shutdown in the
        appropriate reverse dependency order.
        """

        entry = self._require_entry(
            plugin_id
        )

        if not self.is_initialized(
            plugin_id
        ):
            return

        try:
            entry.plugin.shutdown()
        except Exception as exc:
            self._state_store.set_last_error(
                plugin_id,
                exc,
            )
            raise

        self._state_store.mark_uninitialized(
            plugin_id
        )

        self._state_store.clear_last_error(
            plugin_id
        )

    # ========================================================
    # UNREGISTRATION
    # ========================================================

    def unregister(
        self,
        plugin_id: str,
        *,
        shutdown: bool = True,
    ) -> PluginEntry | None:
        """
        Unregister one plugin.

        If ``shutdown`` is True, an initialized plugin is shut down
        before the runtime entry and state are removed.

        The registry does not inspect dependencies.

        PluginManager is responsible for ensuring that dependent
        plugins have already been shut down/unregistered as required.
        """

        if not self.contains(
            plugin_id
        ):
            return None

        if shutdown and self.is_initialized(
            plugin_id
        ):
            self.shutdown(
                plugin_id
            )

        # PluginStateStore requires an inactive and disabled plugin
        # before unregistration.
        if self.is_enabled(
            plugin_id
        ):
            raise RuntimeError(
                (
                    f"Cannot unregister enabled plugin "
                    f"{plugin_id!r}. Disable it first."
                )
            )

        entry = self._entries[
            plugin_id
        ]

        try:
            self._state_store.unregister(
                plugin_id
            )
        except Exception:
            # State remains authoritative. The registry entry has not
            # been detached because state removal failed.
            raise

        self._entries.pop(
            plugin_id,
            None,
        )

        return entry

    # ========================================================
    # ENABLE
    # ========================================================

    def enable(
        self,
        plugin_id: str,
    ) -> None:
        """
        Enable a registered plugin.

        Enabling does not initialize the plugin.
        """

        self._require_entry(
            plugin_id
        )

        if self.is_enabled(
            plugin_id
        ):
            return

        self._state_store.set_enabled(
            plugin_id,
            True,
        )

        self._state_store.clear_last_error(
            plugin_id
        )

    # ========================================================
    # DISABLE
    # ========================================================

    def disable(
        self,
        plugin_id: str,
        *,
        shutdown: bool = True,
    ) -> None:
        """
        Disable a registered plugin.

        If initialized and ``shutdown`` is True, shutdown is performed
        before recording the disabled state.

        If an initialized plugin is disabled with ``shutdown=False``,
        PluginStateStore will reject the transition. This is deliberate:
        an initialized plugin cannot be represented as disabled.
        """

        self._require_entry(
            plugin_id
        )

        if shutdown and self.is_initialized(
            plugin_id
        ):
            self.shutdown(
                plugin_id
            )

        if not self.is_enabled(
            plugin_id
        ):
            return

        self._state_store.set_enabled(
            plugin_id,
            False,
        )

    # ========================================================
    # QUERIES
    # ========================================================

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is registered."""

        self._validate_plugin_id(
            plugin_id
        )

        return plugin_id in self._entries

    def get(
        self,
        plugin_id: str,
    ) -> Any | None:
        """Return a registered plugin instance or None."""

        self._validate_plugin_id(
            plugin_id
        )

        entry = self._entries.get(
            plugin_id
        )

        if entry is None:
            return None

        return entry.plugin

    def get_entry(
        self,
        plugin_id: str,
    ) -> PluginEntry | None:
        """Return a registered PluginEntry or None."""

        self._validate_plugin_id(
            plugin_id
        )

        return self._entries.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> Any:
        """Return a registered plugin or raise KeyError."""

        return self._require_entry(
            plugin_id
        ).plugin

    def require_entry(
        self,
        plugin_id: str,
    ) -> PluginEntry:
        """Return a registered PluginEntry or raise KeyError."""

        return self._require_entry(
            plugin_id
        )

    # ========================================================
    # STATE QUERIES
    # ========================================================

    def is_registered(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical registration state."""

        return self.contains(
            plugin_id
        )

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical initialization state."""

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id not in self._entries:
            return False

        return self._state_store.is_initialized(
            plugin_id
        )

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return canonical enablement state."""

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id not in self._entries:
            return False

        return self._state_store.is_enabled(
            plugin_id
        )

    # ========================================================
    # INTERNALS
    # ========================================================

    def _require_entry(
        self,
        plugin_id: str,
    ) -> PluginEntry:
        """Return a registered entry or raise KeyError."""

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
    state_store: PluginStateStore | None = None,
) -> PluginRegistry:
    """
    Create a PluginRegistry.

    The factory performs no plugin discovery, loading, construction,
    registration, initialization, or dependency resolution.
    """

    return PluginRegistry(
        state_store=state_store
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginEntry",
    "PluginRegistry",
    "create_plugin_registry",
]
