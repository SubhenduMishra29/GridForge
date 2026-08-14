"""
GridForge V2
============

File:
    ui/plugins/plugin_state.py

Purpose
-------
Defines runtime state representations for GridForge UI composition
plugins.

Architectural rules
-------------------
- Plugin state describes lifecycle and availability; it does not own
  application/domain state.
- State transitions are explicit and deterministic.
- Plugin implementations remain responsible for their own resources.
- PluginRegistry and PluginManager may use this state model but do not
  need to expose their internal storage.
- No concrete plugin imports are performed here.
- No Qt widgets are created here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


# ============================================================
# PLUGIN LIFECYCLE STATE
# ============================================================


class PluginState(str, Enum):
    """
    Canonical runtime lifecycle state of a UI plugin.
    """

    DEFINED = "defined"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    DISABLED = "disabled"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"
    FAILED = "failed"


# ============================================================
# STATE TRANSITION ERROR
# ============================================================


class PluginStateError(
    RuntimeError
):
    """Raised when an invalid plugin state transition is requested."""


# ============================================================
# VALID TRANSITIONS
# ============================================================


_VALID_TRANSITIONS: dict[
    PluginState,
    frozenset[PluginState],
] = {
    PluginState.DEFINED: frozenset(
        {
            PluginState.LOADING,
            PluginState.DISABLED,
            PluginState.FAILED,
        }
    ),
    PluginState.LOADING: frozenset(
        {
            PluginState.LOADED,
            PluginState.FAILED,
        }
    ),
    PluginState.LOADED: frozenset(
        {
            PluginState.INITIALIZING,
            PluginState.DISABLED,
            PluginState.SHUTTING_DOWN,
            PluginState.FAILED,
        }
    ),
    PluginState.INITIALIZING: frozenset(
        {
            PluginState.INITIALIZED,
            PluginState.FAILED,
        }
    ),
    PluginState.INITIALIZED: frozenset(
        {
            PluginState.SHUTTING_DOWN,
            PluginState.DISABLED,
            PluginState.FAILED,
        }
    ),
    PluginState.DISABLED: frozenset(
        {
            PluginState.LOADING,
            PluginState.LOADED,
            PluginState.INITIALIZING,
            PluginState.SHUTTING_DOWN,
            PluginState.FAILED,
        }
    ),
    PluginState.SHUTTING_DOWN: frozenset(
        {
            PluginState.SHUTDOWN,
            PluginState.FAILED,
        }
    ),
    PluginState.SHUTDOWN: frozenset(
        {
            PluginState.LOADING,
            PluginState.DISABLED,
            PluginState.FAILED,
        }
    ),
    PluginState.FAILED: frozenset(
        {
            PluginState.LOADING,
            PluginState.SHUTDOWN,
            PluginState.DISABLED,
        }
    ),
}


# ============================================================
# STATE SNAPSHOT
# ============================================================


@dataclass(frozen=True, slots=True)
class PluginStateSnapshot:
    """
    Immutable snapshot of plugin runtime state.
    """

    plugin_id: str

    state: PluginState = PluginState.DEFINED

    enabled: bool = True

    initialized: bool = False

    error: Optional[str] = None

    generation: int = 0

    metadata: Mapping[
        str,
        Any,
    ] = field(
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

        if self.generation < 0:
            raise ValueError(
                "generation cannot be negative."
            )

        if (
            self.state
            == PluginState.INITIALIZED
            and not self.initialized
        ):
            raise ValueError(
                (
                    "INITIALIZED state requires "
                    "initialized=True."
                )
            )

        if (
            self.state
            != PluginState.INITIALIZED
            and self.initialized
        ):
            raise ValueError(
                (
                    "initialized=True is only valid "
                    "for INITIALIZED state."
                )
            )

        if (
            self.state
            == PluginState.DISABLED
            and self.enabled
        ):
            raise ValueError(
                (
                    "DISABLED state requires "
                    "enabled=False."
                )
            )

        if (
            self.state
            != PluginState.DISABLED
            and not self.enabled
            and self.state
            not in {
                PluginState.DEFINED,
                PluginState.LOADED,
                PluginState.SHUTDOWN,
                PluginState.FAILED,
            }
        ):
            raise ValueError(
                (
                    "Disabled plugins cannot be in "
                    "an active lifecycle state."
                )
            )


# ============================================================
# MUTABLE STATE HOLDER
# ============================================================


class PluginStateStore:
    """
    Explicit runtime state store for UI plugins.

    This class stores lifecycle state only. It does not store plugin
    instances, widgets, project data, or domain state.
    """

    def __init__(self) -> None:
        self._states: dict[
            str,
            PluginStateSnapshot,
        ] = {}

    # ========================================================
    # QUERY
    # ========================================================

    @property
    def plugin_ids(
        self,
    ) -> tuple[str, ...]:
        """Return known plugin IDs."""

        return tuple(
            self._states.keys()
        )

    @property
    def snapshots(
        self,
    ) -> tuple[PluginStateSnapshot, ...]:
        """Return all state snapshots."""

        return tuple(
            self._states.values()
        )

    def contains(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether state exists for a plugin."""

        return plugin_id in self._states

    def get(
        self,
        plugin_id: str,
    ) -> Optional[PluginStateSnapshot]:
        """Return plugin state, if known."""

        return self._states.get(
            plugin_id
        )

    def require(
        self,
        plugin_id: str,
    ) -> PluginStateSnapshot:
        """Return plugin state or raise KeyError."""

        snapshot = self.get(
            plugin_id
        )

        if snapshot is None:
            raise KeyError(
                (
                    f"No state exists for "
                    f"plugin {plugin_id!r}."
                )
            )

        return snapshot

    def state(
        self,
        plugin_id: str,
    ) -> PluginState:
        """Return the current lifecycle state."""

        return self.require(
            plugin_id
        ).state

    def is_enabled(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is enabled."""

        return self.require(
            plugin_id
        ).enabled

    def is_initialized(
        self,
        plugin_id: str,
    ) -> bool:
        """Return whether a plugin is initialized."""

        return self.require(
            plugin_id
        ).initialized

    def error(
        self,
        plugin_id: str,
    ) -> Optional[str]:
        """Return the last recorded error."""

        return self.require(
            plugin_id
        ).error

    # ========================================================
    # REGISTRATION
    # ========================================================

    def define(
        self,
        plugin_id: str,
        *,
        enabled: bool = True,
        metadata: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> PluginStateSnapshot:
        """
        Create initial state for a plugin.

        Existing state is not overwritten.
        """

        self._validate_plugin_id(
            plugin_id
        )

        if plugin_id in self._states:
            return self._states[
                plugin_id
            ]

        state = (
            PluginState.DEFINED
            if enabled
            else PluginState.DISABLED
        )

        snapshot = PluginStateSnapshot(
            plugin_id=plugin_id,
            state=state,
            enabled=enabled,
            initialized=False,
            error=None,
            generation=0,
            metadata=dict(
                metadata or {}
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    def remove(
        self,
        plugin_id: str,
    ) -> Optional[PluginStateSnapshot]:
        """
        Remove plugin state.

        Active plugins cannot be silently removed.
        """

        snapshot = self._states.get(
            plugin_id
        )

        if snapshot is None:
            return None

        if snapshot.state in {
            PluginState.LOADING,
            PluginState.INITIALIZING,
            PluginState.INITIALIZED,
            PluginState.SHUTTING_DOWN,
        }:
            raise PluginStateError(
                (
                    f"Cannot remove active plugin "
                    f"state for {plugin_id!r}."
                )
            )

        return self._states.pop(
            plugin_id
        )

    # ========================================================
    # TRANSITIONS
    # ========================================================

    def transition(
        self,
        plugin_id: str,
        target: PluginState,
    ) -> PluginStateSnapshot:
        """
        Perform one validated lifecycle transition.
        """

        current = self.require(
            plugin_id
        )

        if current.state == target:
            return current

        allowed = _VALID_TRANSITIONS.get(
            current.state,
            frozenset(),
        )

        if target not in allowed:
            raise PluginStateError(
                (
                    f"Invalid plugin state transition "
                    f"for {plugin_id!r}: "
                    f"{current.state.value} -> "
                    f"{target.value}."
                )
            )

        enabled = current.enabled
        initialized = current.initialized
        error = current.error
        generation = current.generation

        if target == PluginState.DISABLED:
            enabled = False
            initialized = False

        elif target == PluginState.INITIALIZED:
            enabled = True
            initialized = True
            error = None
            generation += 1

        elif target == PluginState.FAILED:
            initialized = False

        elif target in {
            PluginState.DEFINED,
            PluginState.LOADED,
            PluginState.LOADING,
            PluginState.INITIALIZING,
            PluginState.SHUTTING_DOWN,
            PluginState.SHUTDOWN,
        }:
            if target != PluginState.DISABLED:
                initialized = (
                    target
                    == PluginState.INITIALIZED
                )

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=target,
            enabled=enabled,
            initialized=initialized,
            error=error,
            generation=generation,
            metadata=dict(
                current.metadata
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    # ========================================================
    # ENABLE / DISABLE
    # ========================================================

    def enable(
        self,
        plugin_id: str,
    ) -> PluginStateSnapshot:
        """
        Enable a plugin without initializing it.
        """

        current = self.require(
            plugin_id
        )

        if current.enabled:
            return current

        if current.state in {
            PluginState.DISABLED,
            PluginState.SHUTDOWN,
            PluginState.FAILED,
        }:
            target = (
                PluginState.LOADED
                if current.state
                == PluginState.DISABLED
                else PluginState.DEFINED
            )

            snapshot = PluginStateSnapshot(
                plugin_id=current.plugin_id,
                state=target,
                enabled=True,
                initialized=False,
                error=None,
                generation=current.generation,
                metadata=dict(
                    current.metadata
                ),
            )

            self._states[
                plugin_id
            ] = snapshot

            return snapshot

        raise PluginStateError(
            (
                f"Cannot enable plugin "
                f"{plugin_id!r} from state "
                f"{current.state.value}."
            )
        )

    def disable(
        self,
        plugin_id: str,
    ) -> PluginStateSnapshot:
        """
        Disable a plugin.

        Initialized plugins must be shut down first.
        """

        current = self.require(
            plugin_id
        )

        if current.state == PluginState.DISABLED:
            return current

        if current.initialized:
            raise PluginStateError(
                (
                    f"Plugin {plugin_id!r} must be "
                    "shut down before it can be disabled."
                )
            )

        if current.state not in {
            PluginState.DEFINED,
            PluginState.LOADED,
            PluginState.SHUTDOWN,
            PluginState.FAILED,
        }:
            raise PluginStateError(
                (
                    f"Cannot disable plugin "
                    f"{plugin_id!r} from state "
                    f"{current.state.value}."
                )
            )

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=PluginState.DISABLED,
            enabled=False,
            initialized=False,
            error=current.error,
            generation=current.generation,
            metadata=dict(
                current.metadata
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    # ========================================================
    # ERROR MANAGEMENT
    # ========================================================

    def record_error(
        self,
        plugin_id: str,
        error: BaseException | str,
    ) -> PluginStateSnapshot:
        """
        Record a plugin failure and transition to FAILED.
        """

        current = self.require(
            plugin_id
        )

        message = (
            str(error)
            if isinstance(
                error,
                BaseException,
            )
            else error
        )

        if not isinstance(
            message,
            str,
        ) or not message.strip():
            message = "Unknown plugin failure."

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=PluginState.FAILED,
            enabled=current.enabled,
            initialized=False,
            error=message,
            generation=current.generation,
            metadata=dict(
                current.metadata
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    def clear_error(
        self,
        plugin_id: str,
    ) -> PluginStateSnapshot:
        """Clear a recorded error without changing lifecycle state."""

        current = self.require(
            plugin_id
        )

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=current.state,
            enabled=current.enabled,
            initialized=current.initialized,
            error=None,
            generation=current.generation,
            metadata=dict(
                current.metadata
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    # ========================================================
    # METADATA
    # ========================================================

    def set_metadata(
        self,
        plugin_id: str,
        key: str,
        value: Any,
    ) -> PluginStateSnapshot:
        """Set one state metadata value."""

        if not isinstance(
            key,
            str,
        ) or not key.strip():
            raise ValueError(
                "key must be a non-empty string."
            )

        current = self.require(
            plugin_id
        )

        metadata = dict(
            current.metadata
        )

        metadata[
            key
        ] = value

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=current.state,
            enabled=current.enabled,
            initialized=current.initialized,
            error=current.error,
            generation=current.generation,
            metadata=metadata,
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    def metadata(
        self,
        plugin_id: str,
    ) -> dict[str, Any]:
        """Return a copy of state metadata."""

        return dict(
            self.require(
                plugin_id
            ).metadata
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        plugin_id: str,
        *,
        enabled: bool = True,
    ) -> PluginStateSnapshot:
        """
        Reset a non-active plugin to its initial lifecycle state.
        """

        current = self.require(
            plugin_id
        )

        if current.state in {
            PluginState.LOADING,
            PluginState.INITIALIZING,
            PluginState.INITIALIZED,
            PluginState.SHUTTING_DOWN,
        }:
            raise PluginStateError(
                (
                    f"Cannot reset active plugin "
                    f"{plugin_id!r}."
                )
            )

        snapshot = PluginStateSnapshot(
            plugin_id=current.plugin_id,
            state=(
                PluginState.DEFINED
                if enabled
                else PluginState.DISABLED
            ),
            enabled=enabled,
            initialized=False,
            error=None,
            generation=current.generation,
            metadata=dict(
                current.metadata
            ),
        )

        self._states[
            plugin_id
        ] = snapshot

        return snapshot

    # ========================================================
    # INTERNAL
    # ========================================================

    @staticmethod
    def _validate_plugin_id(
        plugin_id: str,
    ) -> None:
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
# STATE HELPERS
# ============================================================


def can_transition(
    current: PluginState,
    target: PluginState,
) -> bool:
    """
    Return whether a lifecycle transition is valid.
    """

    if current == target:
        return True

    return target in _VALID_TRANSITIONS.get(
        current,
        frozenset(),
    )


def valid_transitions(
    state: PluginState,
) -> tuple[PluginState, ...]:
    """
    Return valid target states for a lifecycle state.
    """

    return tuple(
        _VALID_TRANSITIONS.get(
            state,
            frozenset(),
        )
    )


def is_active_state(
    state: PluginState,
) -> bool:
    """Return whether the plugin is in an active lifecycle phase."""

    return state in {
        PluginState.LOADING,
        PluginState.LOADED,
        PluginState.INITIALIZING,
        PluginState.INITIALIZED,
        PluginState.SHUTTING_DOWN,
    }


def is_terminal_state(
    state: PluginState,
) -> bool:
    """
    Return whether the state represents a stopped/failed endpoint
    requiring an explicit new lifecycle operation.
    """

    return state in {
        PluginState.SHUTDOWN,
        PluginState.FAILED,
    }


__all__ = [
    "PluginState",
    "PluginStateError",
    "PluginStateSnapshot",
    "PluginStateStore",
    "can_transition",
    "valid_transitions",
    "is_active_state",
    "is_terminal_state",
]
