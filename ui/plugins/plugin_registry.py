"""
GridForge V2
============

File:
    ui/plugins/plugin_registry.py

Author:
    Subhendu Mishra

Purpose
-------
Low-level runtime registry for explicitly constructed UI plugins.

Architectural role
------------------
PluginRegistry is the runtime registration and lifecycle execution
boundary.

Responsibilities
----------------
- register already-constructed plugin instances;
- validate plugin contracts;
- execute plugin initialization;
- execute plugin shutdown;
- enable and disable registered plugins;
- unregister runtime plugin instances;
- expose registered plugin instances;
- synchronize lifecycle state with PluginStateStore.

Non-responsibilities
--------------------
- plugin discovery;
- concrete plugin imports;
- plugin construction;
- dependency resolution;
- dependency ordering;
- plugin definitions;
- PluginContext ownership;
- Core/domain state;
- Qt application ownership;
- UI composition;
- lifecycle orchestration policy.

Architectural ownership
-----------------------
PluginLoader
    Explicit concrete-plugin loading and construction.

PluginManager
    Composition definitions, dependency resolution, ordering,
    lifecycle orchestration, and context assignment.

PluginRegistry
    Runtime registration and low-level lifecycle execution.

PluginStateStore
    Canonical observable runtime lifecycle state.

PluginContext
    Dependency carrier supplied during initialization.

Lifecycle state is NEVER duplicated inside PluginEntry or
PluginRegistry.

PluginEntry is only a runtime handle to a registered plugin instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType
from typing import Any, Mapping

from .plugin_contract import validate_plugin
from .plugin_state import PluginStateStore


# ============================================================
# PLUGIN ENTRY
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginEntry:
    """
    Immutable runtime handle for one registered plugin.

    PluginEntry contains only:

        plugin_id
        plugin instance
        immutable metadata

    Runtime lifecycle state belongs exclusively to
    PluginStateStore.

    PluginEntry deliberately does not contain:

        enabled
        initialized
        generation
        last_error
        dependency state
    """

    plugin_id: str

    plugin: Any

    metadata: Mapping[str, Any] = MappingProxyType({})

    def __post_init__(self) -> None:
        """Validate and freeze the runtime entry."""

        # ----------------------------------------------------
        # Plugin ID
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Plugin instance
        # ----------------------------------------------------

        if self.plugin is None:
            raise ValueError(
                "plugin cannot be None."
            )

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

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
# PLUGIN REGISTRY
# ============================================================


class PluginRegistry:
    """
    Low-level runtime registry and lifecycle execution boundary.

    PluginRegistry is intentionally dependency-blind.

    It does not:

        - discover plugins;
        - import concrete plugins;
        - construct plugins;
        - resolve dependencies;
        - determine lifecycle ordering;
        - own PluginContext;
        - own Core/domain state;
        - construct Qt objects;
        - compose the UI.

    PluginManager establishes dependency ordering and invokes this
    registry accordingly.

    PluginStateStore is the sole authority for runtime lifecycle state.

    Threading
    ---------
    Registry membership and lifecycle transitions are serialized by an
    RLock. The lock is re-entrant so lifecycle callbacks may safely
    perform registry queries without deadlocking the registry.
    """

    def __init__(
        self,
        *,
        state_store: PluginStateStore | None = None,
    ) -> None:
        if state_store is not None and not isinstance(
            state_store,
            PluginStateStore,
        ):
            raise TypeError(
                "state_store must be a PluginStateStore or None."
            )

        self._state_store = (
            state_store
            if state_store is not None
            else PluginStateStore()
        )

        self._entries: dict[
            str,
            PluginEntry,
        ] = {}

        self._lock = RLock()

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def state_store(self) -> PluginStateStore:
        """
        Return the canonical runtime lifecycle state store.
        """

        return self._state_store

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        """
        Return registered plugin IDs in registration order.
        """

        with self._lock:
            return tuple(
                self._entries.keys()
            )

    @property
    def entries(self) -> tuple[PluginEntry, ...]:
        """
        Return immutable runtime handles in registration order.

        Lifecycle state is intentionally absent from PluginEntry.
        """

        with self._lock:
            return tuple(
                self._entries.values()
            )

    @property
    def count(self) -> int:
        """Return the number of registered plugins."""

        with self._lock:
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

        Registration does not initialize the plugin.

        Dependency handling and lifecycle ordering are outside this
        class.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        if (
            metadata is not None
            and not isinstance(
                metadata,
                Mapping,
            )
        ):
            raise TypeError(
                "metadata must be a Mapping or None."
            )

        # ----------------------------------------------------
        # Validate before changing runtime state.
        # ----------------------------------------------------

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
                else metadata
            ),
        )

        with self._lock:
            if plugin_id in self._entries:
                raise KeyError(
                    (
                        f"Plugin {plugin_id!r} "
                        "is already registered."
                    )
                )

            # ------------------------------------------------
            # Commit canonical state first.
            # ------------------------------------------------

            self._state_store.register(
                plugin_id,
                enabled=enabled,
                metadata=dict(
                    entry.metadata
                ),
            )

            try:
                self._entries[
                    plugin_id
                ] = entry
            except Exception:
                # Registry insertion failure must not leave a
                # canonical state entry behind.
                try:
                    self._state_store.unregister(
                        plugin_id
                    )
                except Exception:
                    pass

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

        Dependency ordering is NOT performed here.

        PluginManager must establish dependency ordering before calling
        this method.

        Successful initialization is recorded in PluginStateStore only
        after the plugin's initialize() method succeeds.
        """

        with self._lock:
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
                self._record_error(
                    plugin_id,
                    exc,
                )
                raise

            # ------------------------------------------------
            # Commit lifecycle state only after successful
            # plugin initialization.
            # ------------------------------------------------

            try:
                self._state_store.mark_initialized(
                    plugin_id
                )

                self._state_store.clear_last_error(
                    plugin_id
                )

            except Exception as exc:
                # The plugin callback succeeded, but the canonical
                # state transition failed. Record the failure if
                # possible and propagate it rather than pretending
                # initialization was fully committed.
                try:
                    self._record_error(
                        plugin_id,
                        exc,
                    )
                except Exception:
                    pass

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

        Dependency ordering is NOT performed here.

        PluginManager is responsible for reverse dependency ordering.
        """

        with self._lock:
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
                self._record_error(
                    plugin_id,
                    exc,
                )
                raise

            try:
                self._state_store.mark_uninitialized(
                    plugin_id
                )

                self._state_store.clear_last_error(
                    plugin_id
                )

            except Exception as exc:
                try:
                    self._record_error(
                        plugin_id,
                        exc,
                    )
                except Exception:
                    pass

                raise

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
        Unregister one runtime plugin.

        If shutdown=True, an initialized plugin is shut down first.

        The registry requires the plugin to be disabled before
        unregistering it.

        Dependency safety is the responsibility of PluginManager.

        If state removal fails, the runtime entry remains registered,
        preventing registry/state divergence.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if not isinstance(
            shutdown,
            bool,
        ):
            raise TypeError(
                "shutdown must be bool."
            )

        with self._lock:
            entry = self._entries.get(
                plugin_id
            )

            if entry is None:
                return None

            if (
                shutdown
                and self.is_initialized(
                    plugin_id
                )
            ):
                self.shutdown(
                    plugin_id
                )

            if self.is_initialized(
                plugin_id
            ):
                raise RuntimeError(
                    (
                        f"Cannot unregister initialized "
                        f"plugin {plugin_id!r}."
                    )
                )

            if self.is_enabled(
                plugin_id
            ):
                raise RuntimeError(
                    (
                        f"Cannot unregister enabled plugin "
                        f"{plugin_id!r}. Disable it first."
                    )
                )

            # State is removed before registry membership.
            # If state removal fails, registry membership remains.
            self._state_store.unregister(
                plugin_id
            )

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

        with self._lock:
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

        If initialized and shutdown=True, the plugin is shut down
        before the disabled state is recorded.

        If shutdown=False is supplied while the plugin is initialized,
        PluginStateStore rejects the invalid transition.
        """

        if not isinstance(
            shutdown,
            bool,
        ):
            raise TypeError(
                "shutdown must be bool."
            )

        with self._lock:
            self._require_entry(
                plugin_id
            )

            if (
                shutdown
                and self.is_initialized(
                    plugin_id
                )
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

        with self._lock:
            return plugin_id in self._entries

    def get(
        self,
        plugin_id: str,
    ) -> Any | None:
        """
        Return a registered plugin instance.

        Returns None if the plugin is not registered.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
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
        """
        Return a registered PluginEntry.

        Returns None if the plugin is not registered.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
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
        """
        Return whether the plugin is structurally registered.

        Registry membership is authoritative for this question.
        """

        return self.contains(
            plugin_id
        )

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """
        Return canonical initialization state.

        PluginStateStore is authoritative for lifecycle state.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            if plugin_id not in self._entries:
                return False

            return self._state_store.is_initialized(
                plugin_id
            )

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """
        Return canonical runtime enablement state.

        PluginStateStore is authoritative for registered plugins.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            if plugin_id not in self._entries:
                return False

            return self._state_store.is_enabled(
                plugin_id
            )

    # ========================================================
    # INTERNAL ERROR HANDLING
    # ========================================================

    def _record_error(
        self,
        plugin_id: str,
        error: BaseException,
    ) -> None:
        """
        Record a plugin lifecycle failure.

        State-store failures are intentionally allowed to propagate.
        """

        self._state_store.set_last_error(
            plugin_id,
            error,
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
    Create an empty PluginRegistry.

    The factory performs no:

        - plugin discovery;
        - plugin loading;
        - plugin construction;
        - plugin registration;
        - plugin initialization;
        - dependency resolution;
        - UI composition.
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
