# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/plugins/plugin_state.py
#
# Purpose
# -------
# Defines the runtime state representation for GridForge UI
# composition plugins.
#
# Architectural role
# ------------------
# PluginStateStore is a state-recording subsystem.
#
# It owns:
#     - observable plugin runtime facts;
#     - registration state;
#     - enablement state;
#     - initialization state;
#     - initialization generation;
#     - last recorded error;
#     - state metadata.
#
# It does NOT own:
#     - plugin instances;
#     - plugin lifecycle execution;
#     - dependency ordering;
#     - plugin registration decisions;
#     - PluginContext;
#     - Qt widgets;
#     - application/domain state.
#
# Lifecycle ownership
# -------------------
# PluginRegistry / PluginManager remain authoritative for lifecycle
# operations.
#
#     PluginLoader
#         -> constructs plugin
#
#     PluginRegistry
#         -> owns registration
#
#     PluginManager
#         -> owns dependency ordering and lifecycle orchestration
#
#     PluginStateStore
#         -> records resulting runtime state
#
# The store must never become a second lifecycle manager.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Mapping, Optional


# ============================================================
# PLUGIN STATE
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginState:
    """
    Immutable runtime state record for one plugin.

    PluginState deliberately contains facts rather than lifecycle
    commands.

    The concrete plugin instance remains owned by PluginRegistry.

    Lifecycle execution remains owned by PluginRegistry /
    PluginManager.
    """

    plugin_id: str

    registered: bool = False

    enabled: bool = False

    initialized: bool = False

    generation: int = 0

    last_error: Optional[str] = None

    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        """
        Validate and normalize the immutable state record.
        """

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

        if not isinstance(
            self.registered,
            bool,
        ):
            raise TypeError(
                "registered must be bool."
            )

        if not isinstance(
            self.enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be bool."
            )

        if not isinstance(
            self.initialized,
            bool,
        ):
            raise TypeError(
                "initialized must be bool."
            )

        if (
            not isinstance(
                self.generation,
                int,
            )
            or isinstance(
                self.generation,
                bool,
            )
        ):
            raise TypeError(
                "generation must be an integer."
            )

        if self.generation < 0:
            raise ValueError(
                "generation cannot be negative."
            )

        if (
            self.last_error is not None
            and not isinstance(
                self.last_error,
                str,
            )
        ):
            raise TypeError(
                "last_error must be a string or None."
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a Mapping."
            )

        # ----------------------------------------------------
        # Architectural invariants
        # ----------------------------------------------------

        if self.initialized and not self.registered:
            raise ValueError(
                (
                    "A plugin cannot be initialized "
                    "unless it is registered."
                )
            )

        if self.initialized and not self.enabled:
            raise ValueError(
                (
                    "A plugin cannot be initialized "
                    "while disabled."
                )
            )

        # ----------------------------------------------------
        # Immutable metadata snapshot
        # ----------------------------------------------------

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


# ============================================================
# STATE STORE
# ============================================================


class PluginStateStore:
    """
    Thread-safe runtime state store for GridForge UI plugins.

    The store is deliberately passive.

    It records state supplied by PluginRegistry / PluginManager but
    does not decide whether a lifecycle transition is valid.

    In particular, this class never:

        - constructs plugins;
        - initializes plugins;
        - shuts down plugins;
        - resolves dependencies;
        - orders plugins;
        - accesses PluginContext;
        - owns plugin instances;
        - creates Qt objects.
    """

    def __init__(self) -> None:
        self._states: dict[
            str,
            PluginState,
        ] = {}

        self._lock = RLock()

    # ========================================================
    # QUERY
    # ========================================================

    @property
    def plugin_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all known plugin IDs in insertion order.
        """

        with self._lock:
            return tuple(
                self._states.keys()
            )

    @property
    def snapshots(
        self,
    ) -> tuple[PluginState, ...]:
        """
        Return immutable state snapshots in insertion order.
        """

        with self._lock:
            return tuple(
                self._states.values()
            )

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether state exists for the plugin."""

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            return plugin_id in self._states

    def get(
        self,
        plugin_id: str,
    ) -> Optional[PluginState]:
        """
        Return plugin state if known.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            return self._states.get(
                plugin_id
            )

    def require(
        self,
        plugin_id: str,
    ) -> PluginState:
        """
        Return plugin state or raise KeyError.
        """

        state = self.get(
            plugin_id
        )

        if state is None:
            raise KeyError(
                (
                    f"No state exists for "
                    f"plugin {plugin_id!r}."
                )
            )

        return state

    def is_registered(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether the plugin is registered."""

        return self.require(
            plugin_id
        ).registered

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether the plugin is enabled."""

        return self.require(
            plugin_id
        ).enabled

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether the plugin is initialized."""

        return self.require(
            plugin_id
        ).initialized

    def generation(
        self,
        plugin_id: str,
    ) -> int:
        """Return the initialization generation."""

        return self.require(
            plugin_id
        ).generation

    def last_error(
        self,
        plugin_id: str,
    ) -> Optional[str]:
        """Return the last recorded error."""

        return self.require(
            plugin_id
        ).last_error

    # ========================================================
    # REGISTRATION STATE
    # ========================================================

    def define(
        self,
        plugin_id: str,
        *,
        enabled: bool = False,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> PluginState:
        """
        Create initial state for a plugin.

        Existing state is never overwritten.

        Registration is represented by ``registered=True``.

        This method records the registration result; the decision to
        register the plugin belongs to PluginRegistry.
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

        with self._lock:
            existing = self._states.get(
                plugin_id
            )

            if existing is not None:
                return existing

            state = PluginState(
                plugin_id=plugin_id,
                registered=True,
                enabled=enabled,
                initialized=False,
                generation=0,
                last_error=None,
                metadata=dict(
                    metadata or {}
                ),
            )

            self._states[
                plugin_id
            ] = state

            return state

    def set_registered(
        self,
        plugin_id: str,
        registered: bool,
    ) -> PluginState:
        """
        Record registration state.

        This does not register or unregister the actual plugin.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if not isinstance(
            registered,
            bool,
        ):
            raise TypeError(
                "registered must be bool."
            )

        with self._lock:
            current = self.require(
                plugin_id
            )

            if (
                not registered
                and current.initialized
            ):
                raise RuntimeError(
                    (
                        f"Cannot mark initialized plugin "
                        f"{plugin_id!r} as unregistered."
                    )
                )

            return self._replace(
                current,
                registered=registered,
            )

    # ========================================================
    # ENABLEMENT
    # ========================================================

    def set_enabled(
        self,
        plugin_id: str,
        enabled: bool,
    ) -> PluginState:
        """
        Record plugin enablement.

        This method does not initialize or shut down the plugin.

        Lifecycle orchestration remains external.
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

        with self._lock:
            current = self.require(
                plugin_id
            )

            if enabled and not current.registered:
                raise RuntimeError(
                    (
                        f"Cannot enable unregistered "
                        f"plugin {plugin_id!r}."
                    )
                )

            if not enabled and current.initialized:
                raise RuntimeError(
                    (
                        f"Cannot disable initialized "
                        f"plugin {plugin_id!r}."
                    )
                )

            return self._replace(
                current,
                enabled=enabled,
            )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def set_initialized(
        self,
        plugin_id: str,
        initialized: bool,
    ) -> PluginState:
        """
        Record initialization state.

        When initialization changes from False to True, the generation
        counter is incremented.

        The store does not call plugin initialization itself.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if not isinstance(
            initialized,
            bool,
        ):
            raise TypeError(
                "initialized must be bool."
            )

        with self._lock:
            current = self.require(
                plugin_id
            )

            if initialized:
                if not current.registered:
                    raise RuntimeError(
                        (
                            f"Cannot initialize unregistered "
                            f"plugin {plugin_id!r}."
                        )
                    )

                if not current.enabled:
                    raise RuntimeError(
                        (
                            f"Cannot initialize disabled "
                            f"plugin {plugin_id!r}."
                        )
                    )

                if current.initialized:
                    return current

                return self._replace(
                    current,
                    initialized=True,
                    generation=(
                        current.generation + 1
                    ),
                    last_error=None,
                )

            if not current.initialized:
                return current

            return self._replace(
                current,
                initialized=False,
            )

    # ========================================================
    # ERROR MANAGEMENT
    # ========================================================

    def record_error(
        self,
        plugin_id: str,
        error: BaseException | str,
    ) -> PluginState:
        """
        Record a lifecycle error.

        Recording an error does not itself decide the lifecycle state.
        The manager/registry remains responsible for the lifecycle
        response to that error.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if isinstance(
            error,
            BaseException,
        ):
            message = str(
                error
            )
        else:
            message = error

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "error must be an exception or string."
            )

        message = message.strip()

        if not message:
            message = "Unknown plugin failure."

        with self._lock:
            current = self.require(
                plugin_id
            )

            return self._replace(
                current,
                last_error=message,
            )

    def clear_error(
        self,
        plugin_id: str,
    ) -> PluginState:
        """
        Clear the recorded error without changing lifecycle state.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            current = self.require(
                plugin_id
            )

            return self._replace(
                current,
                last_error=None,
            )

    # ========================================================
    # METADATA
    # ========================================================

    def set_metadata(
        self,
        plugin_id: str,
        key: str,
        value: Any,
    ) -> PluginState:
        """
        Record one state metadata value.
        """

        self._validate_name(
            key,
            "key",
        )

        with self._lock:
            current = self.require(
                plugin_id
            )

            metadata = dict(
                current.metadata
            )

            metadata[
                key
            ] = value

            return self._replace(
                current,
                metadata=metadata,
            )

    def metadata(
        self,
        plugin_id: str,
    ) -> dict[str, Any]:
        """
        Return a mutable copy of plugin state metadata.
        """

        with self._lock:
            return dict(
                self.require(
                    plugin_id
                ).metadata
            )

    # ========================================================
    # REMOVAL
    # ========================================================

    def remove(
        self,
        plugin_id: str,
    ) -> Optional[PluginState]:
        """
        Remove state for an inactive plugin.

        This does not unregister or destroy a plugin instance.

        PluginRegistry must perform the actual unregister operation
        before this state is removed.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            current = self._states.get(
                plugin_id
            )

            if current is None:
                return None

            if current.initialized:
                raise RuntimeError(
                    (
                        f"Cannot remove state for "
                        f"initialized plugin {plugin_id!r}."
                    )
                )

            return self._states.pop(
                plugin_id
            )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        plugin_id: str,
        *,
        enabled: Optional[bool] = None,
    ) -> PluginState:
        """
        Reset runtime state without removing registration.

        The plugin must already be uninitialized.

        Generation is intentionally preserved because it represents
        the number of successful initialization generations.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            current = self.require(
                plugin_id
            )

            if current.initialized:
                raise RuntimeError(
                    (
                        f"Cannot reset initialized "
                        f"plugin {plugin_id!r}."
                    )
                )

            next_enabled = (
                current.enabled
                if enabled is None
                else enabled
            )

            if not isinstance(
                next_enabled,
                bool,
            ):
                raise TypeError(
                    "enabled must be bool."
                )

            if (
                next_enabled
                and not current.registered
            ):
                raise RuntimeError(
                    (
                        f"Cannot enable unregistered "
                        f"plugin {plugin_id!r}."
                    )
                )

            return self._replace(
                current,
                enabled=next_enabled,
                initialized=False,
                last_error=None,
            )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _replace(
        self,
        current: PluginState,
        **changes: Any,
    ) -> PluginState:
        """
        Create and store a new immutable state snapshot.
        """

        updated = PluginState(
            plugin_id=current.plugin_id,
            registered=changes.get(
                "registered",
                current.registered,
            ),
            enabled=changes.get(
                "enabled",
                current.enabled,
            ),
            initialized=changes.get(
                "initialized",
                current.initialized,
            ),
            generation=changes.get(
                "generation",
                current.generation,
            ),
            last_error=changes.get(
                "last_error",
                current.last_error,
            ),
            metadata=changes.get(
                "metadata",
                current.metadata,
            ),
        )

        self._states[
            current.plugin_id
        ] = updated

        return updated

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
    def _validate_name(
        value: Any,
        parameter_name: str,
    ) -> None:
        """Validate a metadata identifier."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{parameter_name} must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"{parameter_name} must be a non-empty string."
            )


# ============================================================
# STATE HELPERS
# ============================================================


def is_registered(
    state: PluginState,
) -> bool:
    """Return whether the state represents a registered plugin."""

    if not isinstance(
        state,
        PluginState,
    ):
        raise TypeError(
            "state must be a PluginState."
        )

    return state.registered


def is_enabled(
    state: PluginState,
) -> bool:
    """Return whether the plugin is enabled."""

    if not isinstance(
        state,
        PluginState,
    ):
        raise TypeError(
            "state must be a PluginState."
        )

    return state.enabled


def is_initialized(
    state: PluginState,
) -> bool:
    """Return whether the plugin is initialized."""

    if not isinstance(
        state,
        PluginState,
    ):
        raise TypeError(
            "state must be a PluginState."
        )

    return state.initialized


def is_active(
    state: PluginState,
) -> bool:
    """
    Return whether the plugin is currently initialized and enabled.
    """

    if not isinstance(
        state,
        PluginState,
    ):
        raise TypeError(
            "state must be a PluginState."
        )

    return (
        state.registered
        and state.enabled
        and state.initialized
    )


# ============================================================
# PUBLIC API
# ============================================================


__all__ = [
    "PluginState",
    "PluginStateStore",
    "is_registered",
    "is_enabled",
    "is_initialized",
    "is_active",
]
