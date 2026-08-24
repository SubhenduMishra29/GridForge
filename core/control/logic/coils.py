"""
GridForge V2 - Logic Coils
===========================

Author:
    Subhendu Mishra

File:
    core/control/logic/coils.py

Purpose
-------
Headless industrial coil/output elements for the Logic Control domain.

A coil represents a discrete commanded output in a logic network.  The
coil owns only its discrete logic state.  It does not directly actuate
equipment in core/model.

The UI logic-layout/editing canvas is responsible for the graphical coil
symbol, placement, wiring and editing representation.

Domain boundary
---------------
    Logic input
        |
        v
      Coil
        |
        +----> Boolean output
        |
        +----> persistent coil state
        |
        +----> state-change event

The application/control layer is responsible for interpreting a coil
output and issuing the appropriate domain command to the controlled
system.
"""

from __future__ import annotations

from typing import Sequence

from ..base import (
    LogicControlComponent,
    LogicControlResult,
)
from ...base import (
    ControlSignal,
    Inputs,
    SignalRole,
    SignalValue,
    State,
)


class LogicCoil(LogicControlComponent):
    """
    Base headless logic coil.

    Inputs:
        IN
            Boolean command signal.

    Outputs:
        OUT
            Current coil state.

    Persistent state:
        energized
            Current Boolean coil state.

    The coil does not directly modify an electrical, mechanical, or
    simulation model.
    """

    _STATE_ENERGIZED = "energized"

    def __init__(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicCoil component_id cannot be empty."
            )

        self._component_id = component_id

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

        return "coil"

    # ========================================================================
    # SIGNAL CONTRACT
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Define the coil command input.
        """

        return (
            ControlSignal(
                name="IN",
                role=SignalRole.INPUT,
                description="Boolean coil command.",
                value_type=bool,
            ),
        )

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Define the current coil output.
        """

        return (
            ControlSignal(
                name="OUT",
                role=SignalRole.OUTPUT,
                description="Current Boolean coil state.",
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
        """
        Return persistent logic-state names.
        """

        return (
            self._STATE_ENERGIZED,
        )

    def logic_state_definition(
        self,
    ):
        """
        Define the persistent coil state.

        Import is kept local so this module remains aligned with the
        existing LogicControlComponent state-definition contract.
        """

        from ..base import LogicStateDefinition

        return (
            LogicStateDefinition(
                name=self._STATE_ENERGIZED,
                description="Current energized state of the coil.",
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
        Evaluate the coil.

        The input command becomes the new persistent coil state.

            energized(t+) = IN
            OUT(t+)       = energized(t+)
        """

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        normalized_state = self.validate_state(
            state
        )

        energized = bool(
            normalized_inputs["IN"]
        )

        previous_energized = bool(
            normalized_state[
                self._STATE_ENERGIZED
            ]
        )

        return LogicControlResult(
            outputs={
                "OUT": energized,
            },
            state={
                self._STATE_ENERGIZED:
                    energized,
            },
            time=time,
        )

    # ========================================================================
    # STATE HELPERS
    # ========================================================================

    def is_energized(
        self,
        state: State,
    ) -> bool:
        """
        Return the current coil state from a supplied state mapping.
        """

        normalized_state = self.validate_state(
            state
        )

        return bool(
            normalized_state[
                self._STATE_ENERGIZED
            ]
        )

    def is_deenergized(
        self,
        state: State,
    ) -> bool:
        """
        Return True when the coil is de-energized.
        """

        return not self.is_energized(
            state
        )

    def transition(
        self,
        previous: State,
        current: State,
    ):
        """
        Return the coil state transition.

        The generic LogicControlComponent transition contract is used;
        this helper additionally exposes the semantic coil transition.
        """

        previous_state = self.validate_state(
            previous
        )

        current_state = self.validate_state(
            current
        )

        previous_value = bool(
            previous_state[
                self._STATE_ENERGIZED
            ]
        )

        current_value = bool(
            current_state[
                self._STATE_ENERGIZED
            ]
        )

        if previous_value == current_value:
            return {}

        return {
            self._STATE_ENERGIZED: (
                previous_value,
                current_value,
            )
        }


class StandardCoil(LogicCoil):
    """
    Standard Boolean output coil.

    This class provides an explicit engineering-facing name while
    retaining the generic LogicCoil behavior.
    """

    @property
    def component_type(self) -> str:
        return "standard_coil"


# Conventional engineering alias.
Coil = StandardCoil


__all__ = [
    "LogicCoil",
    "StandardCoil",
    "Coil",
]
