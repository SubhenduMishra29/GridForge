"""
GridForge V2 - Logic Interlocks
================================

Author:
    Subhendu Mishra

File:
    core/control/logic/interlocks.py

Purpose
-------
Headless interlock logic for the GridForge Control domain.

An interlock permits an action only when every required condition is
satisfied.

The authoritative persistent state is Boolean:

    blocked = True / False

The semantic InterlockState enum is retained as a public interpretation
of that Boolean state. String values are deliberately not stored in the
generic LogicStateDefinition because the frozen Logic state contract
accepts Boolean, integer, and floating-point state values.

UI logic-layout/editing remains outside Core Control.
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
# INTERLOCK STATE
# ============================================================================


class InterlockState(str, Enum):
    """Semantic interpretation of the interlock state."""

    CLEAR = "clear"
    BLOCKED = "blocked"


# ============================================================================
# INTERLOCK
# ============================================================================


class LogicInterlock(
    LogicControlComponent,
):
    """
    Boolean interlock component.

    Inputs
    ------
    ENABLE
        Master permission condition.

    CONDITIONS
        Sequence of Boolean permissive conditions.

    Output
    ------
    ALLOW
        True only when ENABLE and every condition are true.

    State
    -----
    blocked
        Persistent Boolean indication of the interlock state.

        True  -> BLOCKED
        False -> CLEAR

    The component intentionally uses one explicit Boolean output instead
    of exposing the semantic enum as a Core state value.
    """

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "interlock"

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(
        self,
        component_id: str,
        *,
        condition_count: int = 1,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicInterlock component_id cannot be empty."
            )

        condition_count = int(
            condition_count
        )

        if condition_count <= 0:
            raise ValueError(
                "LogicInterlock condition_count "
                "must be greater than zero."
            )

        self._component_id = component_id
        self._condition_count = condition_count

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    @property
    def condition_count(self) -> int:
        """Number of permissive conditions."""

        return self._condition_count

    @property
    def condition_names(self) -> tuple[str, ...]:
        """Ordered condition input names."""

        return tuple(
            f"CONDITION_{index}"
            for index in range(
                1,
                self._condition_count + 1,
            )
        )

    # ========================================================================
    # INPUTS
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        signals: list[ControlSignal] = [
            ControlSignal(
                name="ENABLE",
                role=SignalRole.INPUT,
                description=(
                    "Master interlock enable condition."
                ),
                value_type=bool,
            )
        ]

        signals.extend(
            ControlSignal(
                name=name,
                role=SignalRole.INPUT,
                description=(
                    "Required Boolean permissive condition."
                ),
                value_type=bool,
            )
            for name in self.condition_names
        )

        return tuple(
            signals
        )

    # ========================================================================
    # OUTPUTS
    # ========================================================================

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name="ALLOW",
                role=SignalRole.OUTPUT,
                description=(
                    "Interlock permission."
                ),
                value_type=bool,
            ),
        )

    # ========================================================================
    # STATE
    # ========================================================================

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name="blocked",
                value_type=bool,
                default=True,
                description=(
                    "Persistent Boolean interlock status. "
                    "True means blocked."
                ),
            ),
        )

    @property
    def blocked(self) -> bool:
        """
        Semantic convenience property.

        This property does not own state; the engine remains authoritative.
        """

        return bool(
            self._last_blocked
        )

    @property
    def interlock_state(self) -> InterlockState:
        """Return the semantic interpretation of the latest state."""

        return (
            InterlockState.BLOCKED
            if self.blocked
            else InterlockState.CLEAR
        )

    # ========================================================================
    # RESET
    # ========================================================================

    def reset_logic(
        self,
    ) -> State:
        """
        Return the safe initial interlock state.

        An interlock starts blocked until all permissive conditions are
        explicitly satisfied.
        """

        self._last_blocked = True

        return {
            "blocked": True,
        }

    def reset(
        self,
        inputs: Inputs | None = None,
    ) -> State:
        del inputs

        self._last_blocked = True

        return {
            "blocked": True,
        }

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate_logic(
        self,
        state: State,
        inputs: Inputs,
        time: float,
    ) -> LogicControlResult:
        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        normalized_state = (
            self.validate_logic_state(
                state
            )
        )

        enable = normalized_inputs[
            "ENABLE"
        ]

        conditions_ok = all(
            bool(
                normalized_inputs[
                    name
                ]
            )
            for name in self.condition_names
        )

        allowed = (
            bool(enable)
            and conditions_ok
        )

        blocked = not allowed

        previous_blocked = bool(
            normalized_state[
                "blocked"
            ]
        )

        events: list[
            LogicEvent
        ] = []

        if previous_blocked != blocked:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.STATE_CHANGED
                    ),
                    component_id=(
                        self.component_id
                    ),
                    signal_name="blocked",
                    previous_value=(
                        previous_blocked
                    ),
                    current_value=blocked,
                    time=time,
                    data={
                        "interlock_state": (
                            InterlockState.BLOCKED.value
                            if blocked
                            else InterlockState.CLEAR.value
                        ),
                    },
                )
            )

        if previous_blocked and not blocked:
            events.append(
                LogicEvent(
                    event_type=(
                        LogicEventType.TRIGGERED
                    ),
                    component_id=(
                        self.component_id
                    ),
                    signal_name="ALLOW",
                    previous_value=False,
                    current_value=True,
                    time=time,
                    data={
                        "interlock_state": (
                            InterlockState.CLEAR.value
                        ),
                    },
                )
            )

        self._last_blocked = blocked

        return LogicControlResult(
            outputs={
                "ALLOW": allowed,
            },
            state={
                "blocked": blocked,
            },
            time=time,
            events=tuple(
                events
            ),
            diagnostics={
                "interlock_state": (
                    InterlockState.BLOCKED.value
                    if blocked
                    else InterlockState.CLEAR.value
                ),
                "conditions_satisfied": (
                    conditions_ok
                ),
                "enable": bool(
                    enable
                ),
            },
        )


__all__ = [
    "InterlockState",
    "LogicInterlock",
]
