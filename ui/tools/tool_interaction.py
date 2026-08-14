# ============================================================
# File: ui/tools/tool_interaction.py
# GridForge V2 — Tool Interaction
# ============================================================
"""
Interaction-session state for the GridForge V2 tool system.

ToolInteraction represents one continuous interaction owned by a
tool, for example:

    SelectTool
        pointer press -> selection update -> pointer release

    BusTool
        pointer press -> preview -> commit/cancel

    LineTool
        first endpoint -> preview -> second endpoint -> commit

The class is intentionally a UI interaction abstraction.

It does NOT:

    - mutate Core;
    - execute commands;
    - validate electrical topology;
    - perform hit testing;
    - calculate snapping;
    - render graphics;
    - depend on Qt.

ToolInteraction is stateful, but the state is limited to the
current interaction session. Persistent application state belongs
elsewhere.

Architectural flow:

    ToolEvent / ToolInput
            |
            v
      active Tool
            |
            v
     ToolInteraction
            |
            +--> ToolResult
            |
            +--> ToolEvent
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional

from ui.tools.tool_event import ToolEvent
from ui.tools.tool_input import ToolInput


# ============================================================
# INTERACTION STATE
# ============================================================


class ToolInteractionState(str, Enum):
    """Lifecycle state of a tool interaction."""

    IDLE = "idle"
    ACTIVE = "active"
    PREVIEW = "preview"
    COMMITTED = "committed"
    CANCELLED = "cancelled"


# ============================================================
# INTERACTION RESULT
# ============================================================


@dataclass(frozen=True, slots=True)
class ToolInteractionResult:
    """
    Immutable result of an interaction lifecycle operation.

    The result reports what happened to the interaction. It does
    not execute any command or mutate the Core.
    """

    state: ToolInteractionState

    changed: bool = False

    message: Optional[str] = None

    event: Optional[ToolEvent] = None

    data: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def active(self) -> bool:
        """Return whether the interaction remains active."""

        return self.state in {
            ToolInteractionState.ACTIVE,
            ToolInteractionState.PREVIEW,
        }

    @property
    def terminal(self) -> bool:
        """Return whether the interaction has reached a terminal state."""

        return self.state in {
            ToolInteractionState.COMMITTED,
            ToolInteractionState.CANCELLED,
        }

    @property
    def previewing(self) -> bool:
        """Return whether the interaction is currently previewing."""

        return self.state == ToolInteractionState.PREVIEW

    def to_dict(self) -> dict[str, Any]:
        """Return a diagnostic representation."""

        return {
            "state": self.state.value,
            "changed": self.changed,
            "message": self.message,
            "event": self.event,
            "data": dict(self.data),
        }


# ============================================================
# INTERACTION
# ============================================================


class ToolInteraction:
    """
    Mutable state container for one tool interaction.

    The object is deliberately generic. Concrete tools decide what
    their semantic interaction data means.

    Typical lifecycle:

        begin()
          |
          v
        update()
          |
          v
        preview()
          |
          +------> update()
          |
          v
        commit()

    or:

        begin()
          |
          v
        cancel()
    """

    def __init__(
        self,
        *,
        interaction_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """
        Create an idle interaction.

        Parameters
        ----------
        interaction_id:
            Optional stable identifier supplied by the owning tool.
            The interaction class does not generate application IDs.

        tool_id:
            Identifier of the owning tool.

        metadata:
            Static interaction metadata.
        """

        self._interaction_id = self._validate_optional_id(
            interaction_id,
            "interaction_id",
        )

        self._tool_id = self._validate_optional_id(
            tool_id,
            "tool_id",
        )

        self._state = ToolInteractionState.IDLE

        self._metadata: dict[str, Any] = dict(
            metadata or {}
        )

        self._data: dict[str, Any] = {}

        self._input: Optional[ToolInput] = None

        self._previous_input: Optional[ToolInput] = None

        self._event: Optional[ToolEvent] = None

        self._update_count = 0

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def interaction_id(self) -> Optional[str]:
        """Return the interaction identifier."""

        return self._interaction_id

    @property
    def tool_id(self) -> Optional[str]:
        """Return the owning tool identifier."""

        return self._tool_id

    @property
    def state(self) -> ToolInteractionState:
        """Return the current lifecycle state."""

        return self._state

    @property
    def active(self) -> bool:
        """Return whether the interaction is active."""

        return self._state in {
            ToolInteractionState.ACTIVE,
            ToolInteractionState.PREVIEW,
        }

    @property
    def previewing(self) -> bool:
        """Return whether the interaction is previewing."""

        return (
            self._state
            == ToolInteractionState.PREVIEW
        )

    @property
    def terminal(self) -> bool:
        """Return whether the interaction is terminal."""

        return self._state in {
            ToolInteractionState.COMMITTED,
            ToolInteractionState.CANCELLED,
        }

    @property
    def input(self) -> Optional[ToolInput]:
        """Return the latest normalized input."""

        return self._input

    @property
    def previous_input(self) -> Optional[ToolInput]:
        """Return the previous normalized input."""

        return self._previous_input

    @property
    def event(self) -> Optional[ToolEvent]:
        """Return the most recent associated event."""

        return self._event

    @property
    def update_count(self) -> int:
        """Return the number of input updates."""

        return self._update_count

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return interaction metadata as a read-only view."""

        return self._metadata

    @property
    def data(self) -> Mapping[str, Any]:
        """Return interaction data as a read-only mapping view."""

        return self._data

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def begin(
        self,
        tool_input: ToolInput,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolInteractionResult:
        """
        Begin the interaction.

        An interaction must be idle before it can be started.
        """

        self._require_input(
            tool_input
        )

        if self._state != ToolInteractionState.IDLE:
            raise RuntimeError(
                (
                    "Interaction can only begin from IDLE; "
                    f"current state is {self._state.value!r}."
                )
            )

        self._input = tool_input
        self._previous_input = None
        self._event = event
        self._update_count = 0

        self._data.clear()

        if data is not None:
            self._data.update(
                data
            )

        self._state = ToolInteractionState.ACTIVE

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction started.",
            event=event,
            data=dict(self._data),
        )

    # --------------------------------------------------------

    def update(
        self,
        tool_input: ToolInput,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolInteractionResult:
        """
        Update the active interaction with normalized input.
        """

        self._require_input(
            tool_input
        )

        if not self.active:
            raise RuntimeError(
                (
                    "Interaction can only be updated while "
                    "ACTIVE or PREVIEW; current state is "
                    f"{self._state.value!r}."
                )
            )

        self._previous_input = self._input
        self._input = tool_input

        if event is not None:
            self._event = event

        if data is not None:
            self._data.update(
                data
            )

        self._update_count += 1

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction updated.",
            event=self._event,
            data=dict(self._data),
        )

    # --------------------------------------------------------

    def start_preview(
        self,
        tool_input: Optional[ToolInput] = None,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolInteractionResult:
        """
        Enter preview state.

        Preview is still part of the same interaction and can later
        return to ACTIVE or terminate through commit/cancel.
        """

        if self._state not in {
            ToolInteractionState.ACTIVE,
            ToolInteractionState.PREVIEW,
        }:
            raise RuntimeError(
                (
                    "Preview can only start from ACTIVE or PREVIEW; "
                    f"current state is {self._state.value!r}."
                )
            )

        if tool_input is not None:
            self.update(
                tool_input,
                event=event,
                data=data,
            )
        else:
            if event is not None:
                self._event = event

            if data is not None:
                self._data.update(
                    data
                )

        self._state = ToolInteractionState.PREVIEW

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction entered preview state.",
            event=self._event,
            data=dict(self._data),
        )

    # --------------------------------------------------------

    def stop_preview(
        self,
    ) -> ToolInteractionResult:
        """
        Leave preview state and return to ACTIVE.
        """

        if self._state != ToolInteractionState.PREVIEW:
            raise RuntimeError(
                (
                    "Preview can only stop from PREVIEW; "
                    f"current state is {self._state.value!r}."
                )
            )

        self._state = ToolInteractionState.ACTIVE

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction left preview state.",
            event=self._event,
            data=dict(self._data),
        )

    # --------------------------------------------------------

    def commit(
        self,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolInteractionResult:
        """
        Commit the interaction.

        Commit marks the interaction complete. It does not execute a
        command and does not mutate Core.
        """

        if not self.active:
            raise RuntimeError(
                (
                    "Interaction can only commit while ACTIVE or "
                    "PREVIEW; current state is "
                    f"{self._state.value!r}."
                )
            )

        if event is not None:
            self._event = event

        if data is not None:
            self._data.update(
                data
            )

        self._state = ToolInteractionState.COMMITTED

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction committed.",
            event=self._event,
            data=dict(self._data),
        )

    # --------------------------------------------------------

    def cancel(
        self,
        *,
        event: Optional[ToolEvent] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ToolInteractionResult:
        """
        Cancel the interaction.

        Cancellation clears neither historical metadata nor the
        interaction data. The terminal state remains inspectable
        until the interaction object is discarded/reset.
        """

        if not self.active:
            raise RuntimeError(
                (
                    "Interaction can only cancel while ACTIVE or "
                    "PREVIEW; current state is "
                    f"{self._state.value!r}."
                )
            )

        if event is not None:
            self._event = event

        if data is not None:
            self._data.update(
                data
            )

        self._state = ToolInteractionState.CANCELLED

        return ToolInteractionResult(
            state=self._state,
            changed=True,
            message="Interaction cancelled.",
            event=self._event,
            data=dict(self._data),
        )

    # ========================================================
    # DATA MANAGEMENT
    # ========================================================

    def set_data(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set one interaction data value."""

        key = self._validate_data_key(
            key
        )

        self._data[key] = value

    # --------------------------------------------------------

    def update_data(
        self,
        values: Mapping[str, Any],
    ) -> None:
        """Update interaction data from a mapping."""

        if not isinstance(
            values,
            Mapping,
        ):
            raise TypeError(
                "values must implement Mapping."
            )

        self._data.update(
            values
        )

    # --------------------------------------------------------

    def get_data(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return one interaction data value."""

        key = self._validate_data_key(
            key
        )

        return self._data.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def has_data(
        self,
        key: str,
    ) -> bool:
        """Return whether a data value exists."""

        key = self._validate_data_key(
            key
        )

        return key in self._data

    # --------------------------------------------------------

    def remove_data(
        self,
        key: str,
    ) -> Any:
        """Remove and return one data value."""

        key = self._validate_data_key(
            key
        )

        return self._data.pop(
            key
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset the interaction to IDLE.

        Reset is intended for reuse by a tool after a terminal
        interaction has been consumed.
        """

        if self.active:
            raise RuntimeError(
                "Cannot reset an active interaction."
            )

        self._state = ToolInteractionState.IDLE

        self._input = None
        self._previous_input = None
        self._event = None

        self._data.clear()

        self._update_count = 0

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a detached diagnostic snapshot.

        The returned mapping can safely be modified by callers.
        """

        return {
            "interaction_id": self._interaction_id,
            "tool_id": self._tool_id,
            "state": self._state.value,
            "active": self.active,
            "previewing": self.previewing,
            "terminal": self.terminal,
            "input": self._input,
            "previous_input": self._previous_input,
            "event": self._event,
            "update_count": self._update_count,
            "metadata": dict(self._metadata),
            "data": dict(self._data),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _require_input(
        tool_input: ToolInput,
    ) -> None:
        """Validate normalized input."""

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

    @staticmethod
    def _validate_data_key(
        key: str,
    ) -> str:
        """Validate an interaction-data key."""

        if not isinstance(
            key,
            str,
        ):
            raise TypeError(
                "key must be a string."
            )

        key = key.strip()

        if not key:
            raise ValueError(
                "key must not be empty."
            )

        return key

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """Return a concise diagnostic representation."""

        return (
            f"{type(self).__name__}("
            f"interaction_id={self._interaction_id!r}, "
            f"tool_id={self._tool_id!r}, "
            f"state={self._state.value!r}, "
            f"update_count={self._update_count}"
            ")"
        )


__all__ = [
    "ToolInteractionState",
    "ToolInteractionResult",
    "ToolInteraction",
]
