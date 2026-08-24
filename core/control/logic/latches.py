"""
GridForge V2 - Logic Latches
=============================

Author:
    Subhendu Mishra

File:
    core/control/logic/latches.py

Purpose
-------
Headless stateful latch elements for the Logic Control domain.

Supported latch types:

    SR - Set-dominant latch
    RS - Reset-dominant latch

A latch retains its Boolean output until an explicit set/reset command
changes it.

The latch is a Core Control component. Its graphical representation,
placement, wiring and editing behavior belong exclusively to the UI
logic-layout/editing canvas.

Domain boundary
---------------
    Set / Reset inputs
            |
            v
          Latch
            |
            +----> Boolean output
            |
            +----> persistent state

The latch does not directly mutate core/model or simulation state.
"""

from __future__ import annotations

from enum import Enum
from typing import Sequence

from ...base import (
    ControlSignal,
    Inputs,
    SignalRole,
    State,
)
from ..base import (
    LogicControlComponent,
    LogicControlResult,
    LogicStateDefinition,
)


class LatchType(str, Enum):
    """Supported industrial latch precedence modes."""

    SR = "sr"
    RS = "rs"


class LogicLatch(LogicControlComponent):
    """
    Base deterministic Boolean latch.

    Inputs:
        SET
            Set command.

        RESET
            Reset command.

    Output:
        Q
            Current retained latch state.

    Persistent state:
        Q
            Current Boolean latch state.

    Precedence:
        SR -> SET dominates when SET and RESET are simultaneously active.
        RS -> RESET dominates when SET and RESET are simultaneously active.

    When neither input is active, the previous state is retained.
    """

    _STATE_Q = "Q"

    def __init__(
        self,
        component_id: str,
        latch_type: LatchType,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicLatch component_id cannot be empty."
            )

        if not isinstance(
            latch_type,
            LatchType,
        ):
            try:
                latch_type = LatchType(
                    latch_type
                )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid latch type: "
                    f"{latch_type!r}."
                ) from exc

        self._component_id = component_id
        self._latch_type = latch_type

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        """Return the unique logic-component identifier."""

        return self._component_id

    @property
    def component_type(self) -> str:
        """Return the domain component type."""

        return f"{self._latch_type.value}_latch"

    @property
    def latch_type(self) -> LatchType:
        """Return the latch precedence mode."""

        return self._latch_type

    @property
    def set_dominant(self) -> bool:
        """Return True for an SR latch."""

        return self._latch_type is LatchType.SR

    @property
    def reset_dominant(self) -> bool:
        """Return True for an RS latch."""

        return self._latch_type is LatchType.RS

    # ========================================================================
    # SIGNAL CONTRACT
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Define SET and RESET Boolean inputs.
        """

        return (
            ControlSignal(
                name="SET",
                role=SignalRole.INPUT,
                description="Boolean set command.",
                value_type=bool,
            ),
            ControlSignal(
                name="RESET",
                role=SignalRole.INPUT,
                description="Boolean reset command.",
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Define the retained Boolean output.
        """

        return (
            ControlSignal(
                name="Q",
                role=SignalRole.OUTPUT,
                description="Current retained latch state.",
                value_type=bool,
            ),
        )

    # ========================================================================
    # STATE CONTRACT
    # ========================================================================

    @property
    def logic_state_names(
        self,
    ) -> Sequence[str]:
        return (
            self._STATE_Q,
        )

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name=self._STATE_Q,
                description="Current retained latch state.",
                value_type=bool,
                default=False,
            ),
        )

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        """
        Evaluate the latch.

        SR semantics:

            SET=1, RESET=0 -> Q=1
            SET=0, RESET=1 -> Q=0
            SET=0, RESET=0 -> retain
            SET=1, RESET=1 -> Q=1

        RS semantics:

            SET=1, RESET=0 -> Q=1
            SET=0, RESET=1 -> Q=0
            SET=0, RESET=0 -> retain
            SET=1, RESET=1 -> Q=0
        """

        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        current_q = bool(
            normalized_state[
                self._STATE_Q
            ]
        )

        set_active = bool(
            normalized_inputs["SET"]
        )

        reset_active = bool(
            normalized_inputs["RESET"]
        )

        if set_active and reset_active:
            if self._latch_type is LatchType.SR:
                current_q = True
            else:
                current_q = False

        elif set_active:
            current_q = True

        elif reset_active:
            current_q = False

        return LogicControlResult(
            outputs={
                "Q": current_q,
            },
            state={
                self._STATE_Q: current_q,
            },
            time=time,
        )

    # ========================================================================
    # STATE HELPERS
    # ========================================================================

    def output(
        self,
        state: State,
    ) -> bool:
        """
        Return the current latch output from a supplied state.
        """

        normalized_state = self.validate_state(
            state
        )

        return bool(
            normalized_state[
                self._STATE_Q
            ]
        )

    def is_set(
        self,
        state: State,
    ) -> bool:
        """Return True when the latch output is set."""

        return self.output(state)

    def is_reset(
        self,
        state: State,
    ) -> bool:
        """Return True when the latch output is reset."""

        return not self.output(state)

    def reset_logic(
        self,
    ) -> State:
        """
        Return the deterministic reset state.
        """

        return {
            self._STATE_Q: False,
        }


class SRLatch(LogicLatch):
    """
    Set-dominant SR latch.

    If SET and RESET are simultaneously active, SET wins.
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id=component_id,
            latch_type=LatchType.SR,
        )


class RSLatch(LogicLatch):
    """
    Reset-dominant RS latch.

    If SET and RESET are simultaneously active, RESET wins.
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id=component_id,
            latch_type=LatchType.RS,
        )


# Engineering-friendly aliases.
SetResetLatch = SRLatch
ResetSetLatch = RSLatch


__all__ = [
    "LatchType",
    "LogicLatch",
    "SRLatch",
    "RSLatch",
    "SetResetLatch",
    "ResetSetLatch",
]
