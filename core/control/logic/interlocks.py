"""
GridForge V2 - Logic Interlocks
================================

Author:
    Subhendu Mishra

File:
    core/control/logic/interlocks.py

Purpose
-------
Headless industrial interlock and permissive logic for the GridForge
Control domain.

An interlock determines whether an operation is permitted based on
Boolean permissive and blocking conditions.

The component is deliberately independent of:

    - UI
    - logic-layout graphics
    - equipment graphics
    - core/model mutation
    - wall-clock time

The UI logic-layout canvas may represent the interlock graphically, but
the authoritative interlock semantics live here.

Domain semantics
----------------

A command is permitted when:

    command
    AND
    all permissive conditions
    AND
    NOT any blocking condition

Trip conditions force the interlock into a blocked state.

Fail-safe behavior is supported by treating missing/invalid required
conditions as non-permissive rather than silently allowing operation.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping, Sequence

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


class InterlockState(str, Enum):
    """Authoritative interlock evaluation state."""

    PERMISSIVE = "permissive"
    BLOCKED = "blocked"
    TRIPPED = "tripped"


class LogicInterlock(LogicControlComponent):
    """
    Headless industrial interlock.

    Inputs
    ------
    COMMAND:
        Requested operation.

    PERMISSIVE_*:
        Required permissive conditions.

    BLOCK_*:
        Blocking conditions.

    TRIP_*:
        Trip conditions.

    Output
    ------
    PERMIT:
        True only when the command is permitted.

    BLOCKED:
        True when operation is blocked.

    TRIPPED:
        True when a trip condition is active.

    State
    -----
    status:
        Current InterlockState.

    The component does not execute the commanded operation. It only
    determines whether the operation is permitted.
    """

    _STATE_STATUS = "status"

    COMMAND = "COMMAND"
    PERMIT = "PERMIT"
    BLOCKED = "BLOCKED"
    TRIPPED = "TRIPPED"

    def __init__(
        self,
        component_id: str,
        *,
        permissive_inputs: Sequence[str] = (),
        blocking_inputs: Sequence[str] = (),
        trip_inputs: Sequence[str] = (),
        fail_safe: bool = True,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if not component_id:
            raise ValueError(
                "LogicInterlock component_id cannot be empty."
            )

        self._component_id = component_id
        self._fail_safe = bool(fail_safe)

        self._permissive_inputs = (
            self._normalize_names(
                permissive_inputs,
                "permissive",
            )
        )

        self._blocking_inputs = (
            self._normalize_names(
                blocking_inputs,
                "blocking",
            )
        )

        self._trip_inputs = (
            self._normalize_names(
                trip_inputs,
                "trip",
            )
        )

        self._validate_unique_names()

    # ========================================================================
    # IDENTITY
    # ========================================================================

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def component_type(self) -> str:
        return "interlock"

    @property
    def fail_safe(self) -> bool:
        return self._fail_safe

    @property
    def permissive_inputs(self) -> tuple[str, ...]:
        return self._permissive_inputs

    @property
    def blocking_inputs(self) -> tuple[str, ...]:
        return self._blocking_inputs

    @property
    def trip_inputs(self) -> tuple[str, ...]:
        return self._trip_inputs

    # ========================================================================
    # SIGNAL CONTRACT
    # ========================================================================

    def input_definition(
        self,
    ) -> Sequence[ControlSignal]:
        """
        Define the complete interlock input interface.

        ``COMMAND`` is always present.

        Additional inputs are dynamically defined by the interlock
        configuration.
        """

        signals: list[ControlSignal] = [
            ControlSignal(
                name=self.COMMAND,
                role=SignalRole.INPUT,
                description="Requested controlled operation.",
                value_type=bool,
            )
        ]

        for name in self._permissive_inputs:
            signals.append(
                ControlSignal(
                    name=name,
                    role=SignalRole.INPUT,
                    description="Required permissive condition.",
                    value_type=bool,
                )
            )

        for name in self._blocking_inputs:
            signals.append(
                ControlSignal(
                    name=name,
                    role=SignalRole.INPUT,
                    description="Blocking condition.",
                    value_type=bool,
                )
            )

        for name in self._trip_inputs:
            signals.append(
                ControlSignal(
                    name=name,
                    role=SignalRole.INPUT,
                    description="Trip condition.",
                    value_type=bool,
                )
            )

        return tuple(signals)

    def output_definition(
        self,
    ) -> Sequence[ControlSignal]:
        return (
            ControlSignal(
                name=self.PERMIT,
                role=SignalRole.OUTPUT,
                description="Interlock permit output.",
                value_type=bool,
            ),
            ControlSignal(
                name=self.BLOCKED,
                role=SignalRole.OUTPUT,
                description="Interlock blocked indication.",
                value_type=bool,
            ),
            ControlSignal(
                name=self.TRIPPED,
                role=SignalRole.OUTPUT,
                description="Interlock trip indication.",
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
            self._STATE_STATUS,
        )

    def logic_state_definition(
        self,
    ) -> Sequence[LogicStateDefinition]:
        return (
            LogicStateDefinition(
                name=self._STATE_STATUS,
                description="Current interlock evaluation state.",
                value_type=str,
                default=InterlockState.BLOCKED.value,
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
        Evaluate the interlock.

        Evaluation precedence:

            1. Trip
            2. Blocking condition
            3. Missing required permissive
            4. False permissive
            5. Command inactive
            6. Permit

        Trip always has precedence over ordinary blocking.
        """

        normalized_state = self.validate_state(
            state
        )

        normalized_inputs = (
            self.validate_logic_inputs(
                inputs
            )
        )

        del normalized_state

        trip_active = self._any_active(
            normalized_inputs,
            self._trip_inputs,
        )

        block_active = self._any_active(
            normalized_inputs,
            self._blocking_inputs,
        )

        missing_permissive = (
            self._missing_inputs(
                normalized_inputs,
                self._permissive_inputs,
            )
        )

        false_permissive = (
            self._any_false(
                normalized_inputs,
                self._permissive_inputs,
            )
        )

        command_active = bool(
            normalized_inputs[self.COMMAND]
        )

        if trip_active:
            status = InterlockState.TRIPPED
            permit = False

        elif block_active:
            status = InterlockState.BLOCKED
            permit = False

        elif (
            self._fail_safe
            and missing_permissive
        ):
            status = InterlockState.BLOCKED
            permit = False

        elif false_permissive:
            status = InterlockState.BLOCKED
            permit = False

        elif not command_active:
            status = InterlockState.BLOCKED
            permit = False

        else:
            status = InterlockState.PERMISSIVE
            permit = True

        return LogicControlResult(
            outputs={
                self.PERMIT: permit,
                self.BLOCKED: (
                    status is InterlockState.BLOCKED
                ),
                self.TRIPPED: (
                    status is InterlockState.TRIPPED
                ),
            },
            state={
                self._STATE_STATUS:
                    status.value,
            },
            time=time,
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    def status(
        self,
        state: State,
    ) -> InterlockState:
        """
        Return the current interlock state.
        """

        normalized = self.validate_state(
            state
        )

        raw_status = normalized[
            self._STATE_STATUS
        ]

        try:
            return InterlockState(
                raw_status
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid interlock state: "
                f"{raw_status!r}."
            ) from exc

    def is_permissive(
        self,
        state: State,
    ) -> bool:
        return (
            self.status(state)
            is InterlockState.PERMISSIVE
        )

    def is_blocked(
        self,
        state: State,
    ) -> bool:
        return (
            self.status(state)
            is InterlockState.BLOCKED
        )

    def is_tripped(
        self,
        state: State,
    ) -> bool:
        return (
            self.status(state)
            is InterlockState.TRIPPED
        )

    def reset_logic(
        self,
    ) -> State:
        """
        Return the deterministic safe/reset state.
        """

        return {
            self._STATE_STATUS:
                InterlockState.BLOCKED.value,
        }

    # ========================================================================
    # CONFIGURATION VALIDATION
    # ========================================================================

    @staticmethod
    def _normalize_names(
        names: Sequence[str],
        category: str,
    ) -> tuple[str, ...]:
        normalized: list[str] = []

        for name in names:
            value = str(name).strip()

            if not value:
                raise ValueError(
                    f"{category.capitalize()} input "
                    "names cannot be empty."
                )

            normalized.append(value)

        return tuple(normalized)

    def _validate_unique_names(
        self,
    ) -> None:
        groups = {
            "permissive": self._permissive_inputs,
            "blocking": self._blocking_inputs,
            "trip": self._trip_inputs,
        }

        seen: dict[str, str] = {}

        reserved = {
            self.COMMAND,
        }

        for category, names in groups.items():
            for name in names:
                if name in reserved:
                    raise ValueError(
                        f"Input name {name!r} is reserved."
                    )

                previous = seen.get(name)

                if previous is not None:
                    raise ValueError(
                        f"Input {name!r} is defined as both "
                        f"{previous} and {category}."
                    )

                seen[name] = category

    # ========================================================================
    # BOOLEAN EVALUATION HELPERS
    # ========================================================================

    @staticmethod
    def _any_active(
        inputs: Mapping[str, object],
        names: Sequence[str],
    ) -> bool:
        return any(
            bool(inputs[name])
            for name in names
            if name in inputs
        )

    @staticmethod
    def _any_false(
        inputs: Mapping[str, object],
        names: Sequence[str],
    ) -> bool:
        return any(
            not bool(inputs[name])
            for name in names
            if name in inputs
        )

    @staticmethod
    def _missing_inputs(
        inputs: Mapping[str, object],
        names: Sequence[str],
    ) -> bool:
        return any(
            name not in inputs
            for name in names
        )


class PermissiveInterlock(LogicInterlock):
    """
    Convenience interlock emphasizing required permissive conditions.

    Blocking and trip conditions remain supported.
    """

    @property
    def component_type(self) -> str:
        return "permissive_interlock"


class SafetyInterlock(LogicInterlock):
    """
    Fail-safe interlock intended for safety/permissive logic.

    Missing required inputs are treated as blocking.
    """

    def __init__(
        self,
        component_id: str,
        *,
        permissive_inputs: Sequence[str] = (),
        blocking_inputs: Sequence[str] = (),
        trip_inputs: Sequence[str] = (),
    ) -> None:
        super().__init__(
            component_id=component_id,
            permissive_inputs=permissive_inputs,
            blocking_inputs=blocking_inputs,
            trip_inputs=trip_inputs,
            fail_safe=True,
        )

    @property
    def component_type(self) -> str:
        return "safety_interlock"


__all__ = [
    "InterlockState",
    "LogicInterlock",
    "PermissiveInterlock",
    "SafetyInterlock",
]
