"""
GridForge V2 - Logic Latches
============================

Author:
    Subhendu Mishra

File:
    core/control/logic/latches.py

Purpose
-------
Headless latch components for the Logic Control branch.

Supported latch forms:

    SR
        SET has priority over RESET.

    RS
        RESET has priority over SET.

The latch stores only Boolean persistent state:

    Q

The UI logic-layout/editing canvas represents the latch and its
connections but does not own the latch state or semantics.
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
from .base import (
    LogicControlComponent,
    LogicControlResult,
    LogicEvent,
    LogicEventType,
    LogicStateDefinition,
)


# ============================================================================
# LATCH MODE
# ============================================================================


class LatchMode(str, Enum):
    """Priority rule used when SET and RESET are asserted together."""

    SR = "sr"
    RS = "rs"


# ============================================================================
# BASE LATCH
# ============================================================================


class LogicLatch(
    LogicControlComponent,
):
    """
    Generic Boolean set/reset latch.

    Inputs:
        SET
        RESET

    Output:
        Q

    State:
        q

    Priority:
        SR -> SET dominates simultaneous SET + RESET.
        RS -> RESET dominates simultaneous SET + RESET.
    """

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "latch"

    def __init__(
        self,
        component_id: str,
        *,
        mode: LatchMode = LatchMode.SR,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicLatch component_id cannot be empty."
            )

        try:
            normalized_mode = (
                mode
                if isinstance(
                    mode,
                    LatchMode,
                )
                else LatchMode(
                    mode
                )
            )
        except ValueError as exc:
            raise ValueError(
                f"Unsupported latch mode: {mode!r}."
            ) from exc

        self._component_id = component_id
        self._mode = normalized_mode

    @property
    def mode(self) -> LatchMode:
        """Latch priority mode."""

        return self._mode

    # ========================================================================
    # SIGNAL CONTRACT
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="SET",
                role=SignalRole.INPUT,
                description=(
                    "Boolean set command."
                ),
                value_type=bool,
            ),
            ControlSignal(
                name="RESET",
                role=SignalRole.INPUT,
                description=(
                    "Boolean reset command."
                ),
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="Q",
                role=SignalRole.OUTPUT,
                description=(
                    "Latched Boolean output."
                ),
                value_type=bool,
            ),
        )

    # ========================================================================
    # STATE CONTRACT
    # ========================================================================

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name="q",
                value_type=bool,
                default=False,
                description=(
                    "Persistent Boolean latch state."
                ),
            ),
        )

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
    ) -> State:
        return {
            "q": False,
        }

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> State:
        del inputs
        return self.reset_logic()

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        previous_q = bool(
            normalized_state[
                "q"
            ]
        )

        set_active = bool(
            normalized_inputs[
                "SET"
            ]
        )

        reset_active = bool(
            normalized_inputs[
                "RESET"
            ]
        )

        # --------------------------------------------------------------------
        # PRIORITY LOGIC
        # --------------------------------------------------------------------

        if self.mode is LatchMode.SR:
            if set_active:
                q = True
            elif reset_active:
                q = False
            else:
                q = previous_q

        else:
            # RS mode: RESET dominates simultaneous commands.
            if reset_active:
                q = False
            elif set_active:
                q = True
            else:
                q = previous_q

        # --------------------------------------------------------------------
        # EVENTS
        # --------------------------------------------------------------------

        events: list[
            LogicEvent
        ] = []

        if q != previous_q:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.OUTPUT_CHANGED
                    ),
                    component_id=self.component_id,
                    signal_name="Q",
                    previous_value=previous_q,
                    current_value=q,
                    time=time,
                    data={
                        "mode": self.mode.value,
                        "set": set_active,
                        "reset": reset_active,
                    },
                )
            )

        return LogicControlResult(
            outputs={
                "Q": q,
            },
            state={
                "q": q,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "mode": self.mode.value,
                "set": set_active,
                "reset": reset_active,
                "latched": q,
            },
        )


# ============================================================================
# SPECIALIZED LATCHES
# ============================================================================


class LogicSRLatch(
    LogicLatch,
):
    """
    SR latch.

    SET has priority when SET and RESET are simultaneously asserted.
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id,
            mode=LatchMode.SR,
        )


class LogicRSLatch(
    LogicLatch,
):
    """
    RS latch.

    RESET has priority when SET and RESET are simultaneously asserted.
    """

    def __init__(
        self,
        component_id: str,
    ) -> None:
        super().__init__(
            component_id,
            mode=LatchMode.RS,
        )


# ============================================================================
# COMPATIBILITY ALIASES
# ============================================================================

# Preserve concise public names for existing consumers without introducing
# another implementation hierarchy.

SRLatch = LogicSRLatch
RSLatch = LogicRSLatch


__all__ = [
    "LatchMode",
    "LogicLatch",
    "LogicSRLatch",
    "LogicRSLatch",
    "SRLatch",
    "RSLatch",
]
