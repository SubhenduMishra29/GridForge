"""
GridForge V2
============

File:
    ui/plugins/plugin_state.py

Purpose
-------
Defines the canonical runtime state representation for GridForge UI
composition plugins.

Architectural role
------------------
PluginStateStore is the canonical observable runtime-state subsystem.

It owns:
    - registration state;
    - enablement state;
    - initialization state;
    - successful initialization generation;
    - last recorded lifecycle error;
    - state metadata.

It does NOT own:
    - plugin instances;
    - lifecycle execution;
    - dependency resolution;
    - lifecycle ordering;
    - registration decisions;
    - PluginContext;
    - Qt objects;
    - application/domain state.

Lifecycle ownership
-------------------
PluginManager owns lifecycle orchestration and dependency ordering.

PluginRegistry owns plugin instances and the low-level lifecycle
execution boundary.

PluginStateStore records the resulting runtime facts.

The store never initiates lifecycle operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from types import MappingProxyType
from typing import Any, Mapping


# ============================================================
# PLUGIN STATE
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginState:
    """
    Immutable runtime state snapshot for one plugin.

    PluginState contains facts only. It contains no plugin instance,
    lifecycle command, callback, or executable operation.
    """

    plugin_id: str

    registered: bool = False

    enabled: bool = False

    initialized: bool = False

    generation: int = 0

    last_error: str | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Validate and normalize the immutable state snapshot."""

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
        # Runtime invariants
        # ----------------------------------------------------

        if self.enabled and not self.registered:
            raise ValueError(
                "A plugin cannot be enabled unless it is registered."
            )

        if self.initialized and not self.registered:
            raise ValueError(
                "A plugin cannot be initialized unless it is registered."
            )

        if self.initialized and not self.enabled:
            raise ValueError(
                "A plugin cannot be initialized while disabled."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


# ============================================================
# STATE STORE
# ============================================================


class PluginStateStore:
    """
    Thread-safe canonical runtime-state store.

    This class records state supplied by the lifecycle owner.

    It deliberately does not:
        - construct plugins;
        - initialize plugins;
        - shut down plugins;
        - resolve dependencies;
        - order lifecycle operations;
        - own plugin instances;
        - create Qt objects;
        - emit lifecycle operations;
        - make lifecycle decisions.
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
    def plugin_ids(self) -> tuple[str, ...]:
        """Return known plugin IDs in insertion order."""

        with self._lock:
            return tuple(
                self._states.keys()
            )

    @property
    def snapshots(self) -> tuple[PluginState, ...]:
        """Return immutable state snapshots in insertion order."""

        with self._lock:
            return tuple(
                self._states.values()
            )

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether runtime state exists."""

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            return plugin_id in self._states

    def get(
        self,
        plugin_id: str,
    ) -> PluginState | None:
        """Return runtime state if known."""

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
        """Return runtime state or raise KeyError."""

        state = self.get(
            plugin_id
        )

        if state is None:
            raise KeyError(
                f"No state exists for plugin {plugin_id!r}."
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
        """Return successful initialization generation."""

        return self.require(
            plugin_id
        ).generation

    def last_error(
        self,
        plugin_id: str,
    ) -> str | None:
        """Return the last recorded lifecycle error."""

        return self.require(
            plugin_id
        ).last_error

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        plugin_id: str,
        *,
        enabled: bool = False,
        metadata: Mapping[str, Any] | None = None,
    ) -> PluginState:
        """
        Record successful registration.

        Registration itself is performed by PluginRegistry.

        Existing runtime state cannot be silently overwritten.
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

        with self._lock:
            if plugin_id in self._states:
                raise KeyError(
                    (
                        f"Runtime state for plugin "
                        f"{plugin_id!r} already exists."
                    )
                )

            state = PluginState(
                plugin_id=plugin_id,
                registered=True,
                enabled=enabled,
                initialized=False,
                generation=0,
                last_error=None,
                metadata=(
                    {}
                    if metadata is None
                    else dict(metadata)
                ),
            )

            self._states[
                plugin_id
            ] = state

            return state

    def unregister(
        self,
        plugin_id: str,
    ) -> PluginState:
        """
        Record successful unregistration.

        The caller must have already shut down the plugin and disabled
        it where required.

        The state store does not perform unregistration itself.
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
                        f"Cannot unregister initialized "
                        f"plugin {plugin_id!r}."
                    )
                )

            if current.enabled:
                raise RuntimeError(
                    (
                        f"Cannot unregister enabled "
                        f"plugin {plugin_id!r}."
                    )
                )

            return self._states.pop(
                plugin_id
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
        Record resulting enablement state.

        This method does not perform enable/disable operations.
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

    def mark_initialized(
        self,
        plugin_id: str,
    ) -> PluginState:
        """
        Record a successful initialization.

        A False -> True transition increments generation.

        Generation therefore counts successful initialization cycles.
        """

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            current = self.require(
                plugin_id
            )

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

    def mark_uninitialized(
        self,
        plugin_id: str,
    ) -> PluginState:
        """Record a successful shutdown."""

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            current = self.require(
                plugin_id
            )

            if not current.initialized:
                return current

            return self._replace(
                current,
                initialized=False,
            )

    # ========================================================
    # ERROR
    # ========================================================

    def set_last_error(
        self,
        plugin_id: str,
        error: BaseException | str,
    ) -> PluginState:
        """
        Record the latest lifecycle error.

        Recording an error does not alter lifecycle state.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if isinstance(
            error,
            BaseException,
        ):
            message = str(error)
        elif isinstance(
            error,
            str,
        ):
            message = error
        else:
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

    def clear_last_error(
        self,
        plugin_id: str,
    ) -> PluginState:
        """Clear the recorded lifecycle error."""

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
        """Record one metadata value."""

        self._validate_plugin_id(
            plugin_id
        )

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

            metadata[key] = value

            return self._replace(
                current,
                metadata=metadata,
            )

    def metadata(
        self,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Return a mutable copy of plugin metadata."""

        self._validate_plugin_id(
            plugin_id
        )

        with self._lock:
            return dict(
                self.require(
                    plugin_id
                ).metadata
            )

    # ========================================================
    # INTERNAL
    # ========================================================

    def _replace(
        self,
        current: PluginState,
        **changes: Any,
    ) -> PluginState:
        """Create and store a new immutable state snapshot."""

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
        """Validate a metadata key."""

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
    """Return whether the plugin is currently active."""

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
