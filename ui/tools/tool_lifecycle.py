# ============================================================
# File: ui/tools/tool_lifecycle.py
# GridForge V2 — Tool Lifecycle
# ============================================================
"""
Lifecycle contract for GridForge V2 tools.

ToolLifecycle provides a small, explicit lifecycle abstraction
between ToolManager / ToolController and concrete tools.

It owns no application state and performs no Core mutation.

Lifecycle responsibilities
--------------------------
    - activation;
    - deactivation;
    - reset;
    - interaction-session notifications;
    - lifecycle state reporting.

Non-responsibilities
--------------------
    - tool registration;
    - input dispatch;
    - command execution;
    - domain mutation;
    - topology validation;
    - rendering;
    - snapping;
    - Qt event handling.

Concrete tools may subclass ToolLifecycle directly or use the
provided no-op implementation as a mixin/base contract.

The lifecycle is intentionally synchronous and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


# ============================================================
# LIFECYCLE STATE
# ============================================================


class ToolLifecycleState(str, Enum):
    """Lifecycle state of a tool."""

    INACTIVE = "inactive"
    ACTIVE = "active"


# ============================================================
# LIFECYCLE EVENT
# ============================================================


class ToolLifecycleEvent(str, Enum):
    """Lifecycle events emitted to observers."""

    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    RESET = "reset"
    SESSION_STARTED = "session_started"
    SESSION_COMMITTED = "session_committed"
    SESSION_CANCELLED = "session_cancelled"


# ============================================================
# LIFECYCLE RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolLifecycleResult:
    """
    Immutable result of a lifecycle transition.
    """

    state: ToolLifecycleState

    event: ToolLifecycleEvent

    changed: bool = False

    tool_id: Optional[str] = None

    session_id: Optional[str] = None

    data: Mapping[str, Any] = ()

    message: Optional[str] = None

    @property
    def active(self) -> bool:
        """Return whether the tool is active."""

        return self.state == ToolLifecycleState.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "state": self.state.value,
            "event": self.event.value,
            "changed": self.changed,
            "tool_id": self.tool_id,
            "session_id": self.session_id,
            "data": dict(self.data),
            "message": self.message,
        }


# ============================================================
# TOOL LIFECYCLE
# ============================================================


class ToolLifecycle:
    """
    Explicit lifecycle base class for GridForge tools.

    The class provides deterministic lifecycle transitions and
    overridable hooks.

    Concrete tools should override the protected hooks when they
    need lifecycle-specific behavior.

    Example:

        class BusTool(ToolBase, ToolLifecycle):
            ...

    The lifecycle object itself does not create or destroy the
    tool. Tool ownership remains with ToolManager / ToolRegistry.
    """

    def __init__(
        self,
        *,
        tool_id: Optional[str] = None,
    ) -> None:
        """
        Initialize an inactive lifecycle.

        Parameters
        ----------
        tool_id:
            Stable UI tool identifier.
        """

        self._tool_id = self._validate_optional_id(
            tool_id,
            "tool_id",
        )

        self._lifecycle_state = (
            ToolLifecycleState.INACTIVE
        )

        self._last_event: Optional[
            ToolLifecycleEvent
        ] = None

        self._session_id: Optional[str] = None

        self._activation_count = 0
        self._deactivation_count = 0
        self._reset_count = 0

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def tool_id(self) -> Optional[str]:
        """Return the tool identifier."""

        return self._tool_id

    @property
    def lifecycle_state(
        self,
    ) -> ToolLifecycleState:
        """Return the current lifecycle state."""

        return self._lifecycle_state

    @property
    def active(self) -> bool:
        """Return whether the tool is active."""

        return (
            self._lifecycle_state
            == ToolLifecycleState.ACTIVE
        )

    @property
    def inactive(self) -> bool:
        """Return whether the tool is inactive."""

        return not self.active

    @property
    def session_id(
        self,
    ) -> Optional[str]:
        """Return the current interaction session ID."""

        return self._session_id

    @property
    def last_event(
        self,
    ) -> Optional[ToolLifecycleEvent]:
        """Return the last lifecycle event."""

        return self._last_event

    @property
    def activation_count(self) -> int:
        """Return the number of activations."""

        return self._activation_count

    @property
    def deactivation_count(self) -> int:
        """Return the number of deactivations."""

        return self._deactivation_count

    @property
    def reset_count(self) -> int:
        """Return the number of resets."""

        return self._reset_count

    # ========================================================
    # ACTIVATION
    # ========================================================

    def activate(
        self,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Activate the tool.

        Activation is idempotent. Calling activate() on an already
        active tool returns an unchanged result and does not invoke
        the activation hook again.
        """

        if self.active:
            return self._result(
                event=ToolLifecycleEvent.ACTIVATED,
                changed=False,
                message="Tool is already active.",
                data=context,
            )

        self._before_activate(
            context
        )

        self._lifecycle_state = (
            ToolLifecycleState.ACTIVE
        )

        self._activation_count += 1

        self._after_activate(
            context
        )

        self._last_event = (
            ToolLifecycleEvent.ACTIVATED
        )

        return self._result(
            event=ToolLifecycleEvent.ACTIVATED,
            changed=True,
            message="Tool activated.",
            data=context,
        )

    # ========================================================
    # DEACTIVATION
    # ========================================================

    def deactivate(
        self,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Deactivate the tool.

        Deactivation is idempotent.

        A concrete tool may reject deactivation through its
        ``_before_deactivate`` hook if it has an active interaction
        that must first be resolved.
        """

        if not self.active:
            return self._result(
                event=ToolLifecycleEvent.DEACTIVATED,
                changed=False,
                message="Tool is already inactive.",
                data=context,
            )

        self._before_deactivate(
            context
        )

        self._lifecycle_state = (
            ToolLifecycleState.INACTIVE
        )

        self._session_id = None

        self._deactivation_count += 1

        self._after_deactivate(
            context
        )

        self._last_event = (
            ToolLifecycleEvent.DEACTIVATED
        )

        return self._result(
            event=ToolLifecycleEvent.DEACTIVATED,
            changed=True,
            message="Tool deactivated.",
            data=context,
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Reset tool-specific transient state.

        Reset does not implicitly activate or deactivate the tool.

        Therefore:

            inactive + reset -> inactive
            active + reset   -> active

        Concrete tools implement transient-state cleanup in
        ``_on_reset``.
        """

        self._on_reset(
            context
        )

        self._reset_count += 1

        self._last_event = (
            ToolLifecycleEvent.RESET
        )

        return self._result(
            event=ToolLifecycleEvent.RESET,
            changed=True,
            message="Tool reset.",
            data=context,
        )

    # ========================================================
    # INTERACTION SESSION NOTIFICATIONS
    # ========================================================

    def session_started(
        self,
        session_id: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Notify the tool that a new interaction session started.

        This method does not create a ToolSession. Session ownership
        belongs to the tool/session coordination layer.
        """

        self._require_active()

        session_id = self._validate_id(
            session_id,
            "session_id",
        )

        if self._session_id is not None:
            raise RuntimeError(
                (
                    "A tool interaction session is already "
                    f"active: {self._session_id!r}."
                )
            )

        self._before_session_started(
            session_id,
            context,
        )

        self._session_id = session_id

        self._after_session_started(
            session_id,
            context,
        )

        self._last_event = (
            ToolLifecycleEvent.SESSION_STARTED
        )

        return self._result(
            event=ToolLifecycleEvent.SESSION_STARTED,
            changed=True,
            session_id=session_id,
            message="Tool session started.",
            data=context,
        )

    # --------------------------------------------------------

    def session_committed(
        self,
        *,
        session_id: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Notify the tool that its current interaction committed.
        """

        resolved_session_id = self._resolve_session_id(
            session_id
        )

        self._before_session_committed(
            resolved_session_id,
            context,
        )

        self._session_id = None

        self._after_session_committed(
            resolved_session_id,
            context,
        )

        self._last_event = (
            ToolLifecycleEvent.SESSION_COMMITTED
        )

        return self._result(
            event=ToolLifecycleEvent.SESSION_COMMITTED,
            changed=True,
            session_id=resolved_session_id,
            message="Tool session committed.",
            data=context,
        )

    # --------------------------------------------------------

    def session_cancelled(
        self,
        *,
        session_id: Optional[str] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """
        Notify the tool that its current interaction was cancelled.
        """

        resolved_session_id = self._resolve_session_id(
            session_id
        )

        self._before_session_cancelled(
            resolved_session_id,
            context,
        )

        self._session_id = None

        self._after_session_cancelled(
            resolved_session_id,
            context,
        )

        self._last_event = (
            ToolLifecycleEvent.SESSION_CANCELLED
        )

        return self._result(
            event=ToolLifecycleEvent.SESSION_CANCELLED,
            changed=True,
            session_id=resolved_session_id,
            message="Tool session cancelled.",
            data=context,
        )

    # ========================================================
    # HOOKS
    # ========================================================

    def _before_activate(
        self,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """
        Hook invoked immediately before activation.

        Subclasses may override.
        """

    def _after_activate(
        self,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """
        Hook invoked immediately after activation.

        Subclasses may override.
        """

    def _before_deactivate(
        self,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """
        Hook invoked before deactivation.

        Subclasses may override to reject deactivation when their
        internal state requires explicit cleanup.
        """

    def _after_deactivate(
        self,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """
        Hook invoked after deactivation.

        Subclasses may override.
        """

    def _on_reset(
        self,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """
        Hook invoked during reset.

        Subclasses should clear transient tool state here.

        Core state must never be cleared through this hook.
        """

    def _before_session_started(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked before recording a session ID."""

    def _after_session_started(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked after recording a session ID."""

    def _before_session_committed(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked before clearing the session ID."""

    def _after_session_committed(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked after clearing the session ID."""

    def _before_session_cancelled(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked before clearing the session ID."""

    def _after_session_cancelled(
        self,
        session_id: str,
        context: Optional[Mapping[str, Any]],
    ) -> None:
        """Hook invoked after clearing the session ID."""

    # ========================================================
    # QUERIES
    # ========================================================

    def lifecycle_snapshot(
        self,
    ) -> dict[str, Any]:
        """Return a detached lifecycle snapshot."""

        return {
            "tool_id": self._tool_id,
            "state": self._lifecycle_state.value,
            "active": self.active,
            "session_id": self._session_id,
            "last_event": (
                self._last_event.value
                if self._last_event is not None
                else None
            ),
            "activation_count": self._activation_count,
            "deactivation_count": self._deactivation_count,
            "reset_count": self._reset_count,
        }

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _require_active(
        self,
    ) -> None:
        """Require the tool to be active."""

        if not self.active:
            raise RuntimeError(
                (
                    "Tool lifecycle operation requires an active "
                    "tool; current state is "
                    f"{self._lifecycle_state.value!r}."
                )
            )

    def _resolve_session_id(
        self,
        session_id: Optional[str],
    ) -> str:
        """Resolve an explicit or current session identifier."""

        if session_id is None:
            session_id = self._session_id

        if session_id is None:
            raise RuntimeError(
                "No active tool interaction session exists."
            )

        session_id = self._validate_id(
            session_id,
            "session_id",
        )

        if (
            self._session_id is not None
            and session_id != self._session_id
        ):
            raise ValueError(
                (
                    f"Session ID mismatch: expected "
                    f"{self._session_id!r}, received "
                    f"{session_id!r}."
                )
            )

        return session_id

    def _result(
        self,
        *,
        event: ToolLifecycleEvent,
        changed: bool,
        message: str,
        session_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolLifecycleResult:
        """Construct a lifecycle result."""

        return ToolLifecycleResult(
            state=self._lifecycle_state,
            event=event,
            changed=changed,
            tool_id=self._tool_id,
            session_id=session_id,
            data=dict(data or {}),
            message=message,
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_optional_id(
        value: Optional[str],
        field_name: str,
    ) -> Optional[str]:
        """Validate an optional identifier."""

        if value is None:
            return None

        return ToolLifecycle._validate_id(
            value,
            field_name,
        )

    @staticmethod
    def _validate_id(
        value: str,
        field_name: str,
    ) -> str:
        """Validate a required identifier."""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} must not be empty."
            )

        return value

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        return (
            f"{type(self).__name__}("
            f"tool_id={self._tool_id!r}, "
            f"state={self._lifecycle_state.value!r}, "
            f"session_id={self._session_id!r}"
            ")"
        )


__all__ = [
    "ToolLifecycleState",
    "ToolLifecycleEvent",
    "ToolLifecycleResult",
    "ToolLifecycle",
]
