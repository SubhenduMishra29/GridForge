# ============================================================
# File: ui/tools/tool_session.py
# GridForge V2 — Tool Session
# ============================================================
"""
Tool-session lifecycle management for the GridForge V2 UI.

A ToolSession represents the lifetime of the currently active tool
interaction context. It sits above an individual ToolInteraction
and provides the ToolController / ToolManager with a stable
boundary for:

    - starting an interaction;
    - tracking the active interaction;
    - updating interaction input;
    - entering/leaving preview;
    - committing;
    - cancelling;
    - resetting a completed interaction.

Architectural boundaries
------------------------
ToolSession does NOT:

    - mutate Core;
    - execute Commands;
    - validate electrical topology;
    - perform hit testing;
    - perform snapping;
    - render graphics;
    - own tool registration;
    - depend on Qt.

ToolSession is intentionally a UI-state coordinator.

Relationship
------------

    ToolManager
         |
         v
    ToolController
         |
         v
    ToolSession
         |
         v
    ToolInteraction
         |
         v
    ToolResult / ToolEvent

A session may be reused for multiple sequential interactions by
resetting the completed interaction and beginning again.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from ui.tools.tool_event import ToolEvent
from ui.tools.tool_input import ToolInput
from ui.tools.tool_interaction import (
    ToolInteraction,
    ToolInteractionResult,
    ToolInteractionState,
)


# ============================================================
# SESSION STATE
# ============================================================


class ToolSessionState(str, Enum):
    """
    Lifecycle state of a tool session.
    """

    INACTIVE = "inactive"
    READY = "ready"
    ACTIVE = "active"
    PREVIEW = "preview"
    COMMITTED = "committed"
    CANCELLED = "cancelled"


# ============================================================
# SESSION RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolSessionResult:
    """
    Immutable result of a ToolSession lifecycle operation.
    """

    state: ToolSessionState

    changed: bool = False

    message: Optional[str] = None

    interaction_result: Optional[
        ToolInteractionResult
    ] = None

    session_id: Optional[str] = None

    tool_id: Optional[str] = None

    data: Mapping[str, Any] = ()

    @property
    def active(self) -> bool:
        """Return whether the session is actively interacting."""

        return self.state in {
            ToolSessionState.ACTIVE,
            ToolSessionState.PREVIEW,
        }

    @property
    def terminal(self) -> bool:
        """Return whether the current interaction is terminal."""

        return self.state in {
            ToolSessionState.COMMITTED,
            ToolSessionState.CANCELLED,
        }

    @property
    def previewing(self) -> bool:
        """Return whether the session is in preview."""

        return self.state == ToolSessionState.PREVIEW

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        interaction_result = self.interaction_result

        return {
            "state": self.state.value,
            "changed": self.changed,
            "message": self.message,
            "session_id": self.session_id,
            "tool_id": self.tool_id,
            "interaction_result": (
                interaction_result.to_dict()
                if interaction_result is not None
                else None
            ),
            "data": dict(self.data),
        }


# ============================================================
# TOOL SESSION
# ============================================================


class ToolSession:
    """
    Lifecycle owner for the active interaction of one tool.

    The session does not itself interpret ToolInput. It forwards
    normalized input to ToolInteraction and mirrors its lifecycle
    state at the session boundary.

    A session normally has the following lifecycle:

        INACTIVE
            |
          activate()
            |
            v
          READY
            |
          begin()
            |
            v
          ACTIVE
            |
       start_preview()
            |
            v
         PREVIEW
            |
        commit/cancel
            |
            v
        COMMITTED/CANCELLED
            |
          reset()
            |
            v
          READY
            |
        deactivate()
            |
            v
        INACTIVE
    """

    def __init__(
        self,
        *,
        session_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Create an inactive tool session.

        ``session_id`` is supplied by the owning UI layer when a
        stable identifier is required. This class does not generate
        application IDs.
        """

        self._session_id = self._validate_optional_id(
            session_id,
            "session_id",
        )

        self._tool_id = self._validate_optional_id(
            tool_id,
            "tool_id",
        )

        self._metadata: dict[str, Any] = dict(
            metadata or {}
        )

        self._state = ToolSessionState.INACTIVE

        self._interaction: Optional[
            ToolInteraction
        ] = None

        self._interaction_sequence = 0

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def session_id(self) -> Optional[str]:
        """Return the session identifier."""

        return self._session_id

    @property
    def tool_id(self) -> Optional[str]:
        """Return the owning tool identifier."""

        return self._tool_id

    @property
    def state(self) -> ToolSessionState:
        """Return the current session state."""

        return self._state

    @property
    def active(self) -> bool:
        """Return whether an interaction is active."""

        return self._state in {
            ToolSessionState.ACTIVE,
            ToolSessionState.PREVIEW,
        }

    @property
    def ready(self) -> bool:
        """Return whether the session is ready to begin."""

        return self._state == ToolSessionState.READY

    @property
    def previewing(self) -> bool:
        """Return whether the session is in preview."""

        return self._state == ToolSessionState.PREVIEW

    @property
    def terminal(self) -> bool:
        """Return whether the current interaction is terminal."""

        return self._state in {
            ToolSessionState.COMMITTED,
            ToolSessionState.CANCELLED,
        }

    @property
    def interaction(
        self,
    ) -> Optional[ToolInteraction]:
        """Return the current interaction."""

        return self._interaction

    @property
    def metadata(
        self,
    ) -> Mapping[str, Any]:
        """Return session metadata."""

        return self._metadata

    @property
    def interaction_sequence(self) -> int:
        """Return the number of interactions started by this session."""

        return self._interaction_sequence

    # ========================================================
    # SESSION ACTIVATION
    # ========================================================

    def activate(
        self,
    ) -> ToolSessionResult:
        """
        Activate the session.

        Activation prepares the session to receive a new
        interaction. It does not start an interaction.
        """

        if self._state != ToolSessionState.INACTIVE:
            return self._result(
                changed=False,
                message="Tool session is already active.",
            )

        self._state = ToolSessionState.READY

        return self._result(
            changed=True,
            message="Tool session activated.",
        )

    # --------------------------------------------------------

    def deactivate(
        self,
    ) -> ToolSessionResult:
        """
        Deactivate the session.

        An active interaction must first be committed or cancelled.
        """

        if self.active:
            raise RuntimeError(
                (
                    "Cannot deactivate a session while an "
                    "interaction is active."
                )
            )

        if self._state == ToolSessionState.INACTIVE:
            return self._result(
                changed=False,
                message="Tool session is already inactive.",
            )

        self._state = ToolSessionState.INACTIVE
        self._interaction = None

        return self._result(
            changed=True,
            message="Tool session deactivated.",
        )

    # ========================================================
    # INTERACTION LIFECYCLE
    # ========================================================

    def begin(
        self,
        tool_input: ToolInput,
        *,
        interaction_id: Optional[str] = None,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolSessionResult:
        """
        Begin a new interaction.

        A session must be READY before beginning an interaction.
        """

        self._require_input(
            tool_input
        )

        if self._state != ToolSessionState.READY:
            raise RuntimeError(
                (
                    "Tool session must be READY before begin(); "
                    f"current state is {self._state.value!r}."
                )
            )

        if interaction_id is None:
            interaction_id = self._build_interaction_id()

        interaction = ToolInteraction(
            interaction_id=interaction_id,
            tool_id=self._tool_id,
            metadata=self._metadata,
        )

        interaction_result = interaction.begin(
            tool_input,
            event=event,
            data=data,
        )

        self._interaction = interaction
        self._state = ToolSessionState.ACTIVE
        self._interaction_sequence += 1

        return self._result(
            changed=True,
            message="Tool interaction started.",
            interaction_result=interaction_result,
        )

    # --------------------------------------------------------

    def update(
        self,
        tool_input: ToolInput,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolSessionResult:
        """
        Update the current interaction.
        """

        self._require_input(
            tool_input
        )

        interaction = self._require_interaction()

        if not self.active:
            raise RuntimeError(
                (
                    "Cannot update an interaction while the "
                    f"session is {self._state.value!r}."
                )
            )

        interaction_result = interaction.update(
            tool_input,
            event=event,
            data=data,
        )

        self._sync_state_from_interaction()

        return self._result(
            changed=True,
            message="Tool interaction updated.",
            interaction_result=interaction_result,
        )

    # --------------------------------------------------------

    def start_preview(
        self,
        tool_input: Optional[ToolInput] = None,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolSessionResult:
        """
        Enter preview state for the current interaction.
        """

        interaction = self._require_interaction()

        if not self.active:
            raise RuntimeError(
                (
                    "Cannot start preview while the session is "
                    f"{self._state.value!r}."
                )
            )

        interaction_result = interaction.start_preview(
            tool_input,
            event=event,
            data=data,
        )

        self._state = ToolSessionState.PREVIEW

        return self._result(
            changed=True,
            message="Tool interaction entered preview.",
            interaction_result=interaction_result,
        )

    # --------------------------------------------------------

    def stop_preview(
        self,
    ) -> ToolSessionResult:
        """
        Return a previewing interaction to ACTIVE state.
        """

        interaction = self._require_interaction()

        if self._state != ToolSessionState.PREVIEW:
            raise RuntimeError(
                (
                    "Cannot stop preview while the session is "
                    f"{self._state.value!r}."
                )
            )

        interaction_result = interaction.stop_preview()

        self._state = ToolSessionState.ACTIVE

        return self._result(
            changed=True,
            message="Tool interaction left preview.",
            interaction_result=interaction_result,
        )

    # --------------------------------------------------------

    def commit(
        self,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolSessionResult:
        """
        Commit the current interaction.
        """

        interaction = self._require_interaction()

        if not self.active:
            raise RuntimeError(
                (
                    "Cannot commit while the session is "
                    f"{self._state.value!r}."
                )
            )

        interaction_result = interaction.commit(
            event=event,
            data=data,
        )

        self._state = ToolSessionState.COMMITTED

        return self._result(
            changed=True,
            message="Tool interaction committed.",
            interaction_result=interaction_result,
        )

    # --------------------------------------------------------

    def cancel(
        self,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolSessionResult:
        """
        Cancel the current interaction.
        """

        interaction = self._require_interaction()

        if not self.active:
            raise RuntimeError(
                (
                    "Cannot cancel while the session is "
                    f"{self._state.value!r}."
                )
            )

        interaction_result = interaction.cancel(
            event=event,
            data=data,
        )

        self._state = ToolSessionState.CANCELLED

        return self._result(
            changed=True,
            message="Tool interaction cancelled.",
            interaction_result=interaction_result,
        )

    # ========================================================
    # RESET / REUSE
    # ========================================================

    def reset(
        self,
    ) -> ToolSessionResult:
        """
        Reset a completed interaction and return to READY.

        Reset cannot discard an active interaction.
        """

        if self.active:
            raise RuntimeError(
                "Cannot reset an active tool session."
            )

        if self._state == ToolSessionState.INACTIVE:
            raise RuntimeError(
                "Cannot reset an inactive tool session."
            )

        if self._interaction is not None:
            if not self._interaction.terminal:
                raise RuntimeError(
                    (
                        "Cannot reset a non-terminal "
                        "interaction."
                    )
                )

            self._interaction.reset()

        self._interaction = None
        self._state = ToolSessionState.READY

        return self._result(
            changed=True,
            message="Tool session reset and ready for reuse.",
        )

    # ========================================================
    # DATA ACCESS
    # ========================================================

    def set_data(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store data on the current interaction.

        Session-level data is intentionally not maintained
        separately from ToolInteraction data.
        """

        interaction = self._require_interaction()

        interaction.set_data(
            key,
            value,
        )

    # --------------------------------------------------------

    def update_data(
        self,
        values: Mapping[str, Any],
    ) -> None:
        """Update current interaction data."""

        interaction = self._require_interaction()

        interaction.update_data(
            values
        )

    # --------------------------------------------------------

    def get_data(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return current interaction data."""

        interaction = self._require_interaction()

        return interaction.get_data(
            key,
            default,
        )

    # --------------------------------------------------------

    def has_data(
        self,
        key: str,
    ) -> bool:
        """Return whether current interaction has a data key."""

        interaction = self._require_interaction()

        return interaction.has_data(
            key
        )

    # ========================================================
    # INPUT / EVENT ACCESS
    # ========================================================

    @property
    def input(
        self,
    ) -> Optional[ToolInput]:
        """Return the latest interaction input."""

        if self._interaction is None:
            return None

        return self._interaction.input

    @property
    def previous_input(
        self,
    ) -> Optional[ToolInput]:
        """Return the previous interaction input."""

        if self._interaction is None:
            return None

        return self._interaction.previous_input

    @property
    def event(
        self,
    ) -> Optional[ToolEvent]:
        """Return the most recent interaction event."""

        if self._interaction is None:
            return None

        return self._interaction.event

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a detached diagnostic snapshot.
        """

        return {
            "session_id": self._session_id,
            "tool_id": self._tool_id,
            "state": self._state.value,
            "active": self.active,
            "ready": self.ready,
            "previewing": self.previewing,
            "terminal": self.terminal,
            "interaction_sequence": self._interaction_sequence,
            "metadata": dict(self._metadata),
            "interaction": (
                self._interaction.snapshot()
                if self._interaction is not None
                else None
            ),
        }

    # ========================================================
    # INTERNAL HELPERS
    # ========================================================

    def _require_interaction(
        self,
    ) -> ToolInteraction:
        """Return the current interaction or raise."""

        if self._interaction is None:
            raise RuntimeError(
                "No active tool interaction exists."
            )

        return self._interaction

    def _sync_state_from_interaction(
        self,
    ) -> None:
        """Synchronize session state with interaction state."""

        if self._interaction is None:
            return

        interaction_state = self._interaction.state

        mapping = {
            ToolInteractionState.IDLE:
                ToolSessionState.READY,
            ToolInteractionState.ACTIVE:
                ToolSessionState.ACTIVE,
            ToolInteractionState.PREVIEW:
                ToolSessionState.PREVIEW,
            ToolInteractionState.COMMITTED:
                ToolSessionState.COMMITTED,
            ToolInteractionState.CANCELLED:
                ToolSessionState.CANCELLED,
        }

        self._state = mapping[
            interaction_state
        ]

    def _build_interaction_id(
        self,
    ) -> str:
        """
        Build a deterministic session-local interaction ID.

        This identifier is local to the session. It is not a
        domain/entity identifier.
        """

        prefix = (
            self._session_id
            or self._tool_id
            or "tool"
        )

        return (
            f"{prefix}:interaction:"
            f"{self._interaction_sequence + 1}"
        )

    def _result(
        self,
        *,
        changed: bool,
        message: str,
        interaction_result: Optional[
            ToolInteractionResult
        ] = None,
    ) -> ToolSessionResult:
        """Construct a ToolSessionResult."""

        data: Mapping[str, Any] = {}

        if self._interaction is not None:
            data = dict(
                self._interaction.data
            )

        return ToolSessionResult(
            state=self._state,
            changed=changed,
            message=message,
            interaction_result=interaction_result,
            session_id=self._session_id,
            tool_id=self._tool_id,
            data=data,
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _require_input(
        tool_input: ToolInput,
    ) -> None:
        """Validate normalized tool input."""

        if not isinstance(
            tool_input,
            ToolInput,
        ):
            raise TypeError(
                "tool_input must be a ToolInput."
            )

    @staticmethod
    def _validate_optional_id(
        value: Optional[str],
        field_name: str,
    ) -> Optional[str]:
        """Validate an optional identifier."""

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string or None."
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
            f"session_id={self._session_id!r}, "
            f"tool_id={self._tool_id!r}, "
            f"state={self._state.value!r}, "
            f"interaction_sequence="
            f"{self._interaction_sequence}"
            ")"
        )


__all__ = [
    "ToolSessionState",
    "ToolSessionResult",
    "ToolSession",
]
