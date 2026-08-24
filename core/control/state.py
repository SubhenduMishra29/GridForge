"""
GridForge V2 - Control State Contract
=====================================

Author:
    Subhendu Mishra

File:
    core/control/state.py

Purpose
-------
Defines the local state representation used by Control-domain
components.

ControlState is deliberately NOT a solver state vector.

The ownership boundary is:

    core/solver/dynamics
        owns global numerical state and integration

    core/control
        owns controller-local state semantics

    plugins
        implement concrete control behavior

ControlState supports both:

    Dynamic Control
        numeric states such as Efd, Pm, Xw

    Logic Control
        persistent states such as timer, latch, counter, etc.

Architectural Rules
-------------------
1. No numerical integration is performed here.
2. No network or equipment state is accessed here.
3. No plugin is imported here.
4. State ordering is deterministic.
5. State names are authoritative within the component.
6. Vector conversion is a representation operation only.
7. Boolean state is preserved as Boolean when using mapping access.
8. Numeric vector conversion is intended for numerical solver
   integration and therefore requires numeric state values.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Sequence

import math

import numpy as np


# ============================================================================
# TYPE ALIASES
# ============================================================================

StateValue = float | int | bool


# ============================================================================
# ERRORS
# ============================================================================


class StateError(ValueError):
    """Base error for ControlState validation failures."""


class StateNameError(StateError):
    """Raised when state names are invalid."""


class StateValueError(StateError):
    """Raised when state values are invalid."""


class StateVectorError(StateError):
    """Raised when vector conversion is invalid."""


# ============================================================================
# STATE DEFINITION
# ============================================================================


@dataclass(frozen=True)
class StateVariable:
    """
    Definition of one local Control state variable.

    Parameters
    ----------
    name:
        Stable state name.

    unit:
        Engineering unit.

    description:
        Human-readable description.

    value_type:
        Expected Python value type.

    default:
        Optional default initial value.

    Notes
    -----
    ``value_type`` supports:

        float
        int
        bool

    The definition contains metadata only. Runtime state values are
    stored by ControlState.
    """

    name: str
    unit: str = ""
    description: str = ""
    value_type: type = float
    default: StateValue | None = None

    def __post_init__(self) -> None:
        name = str(self.name).strip()

        if not name:
            raise StateNameError(
                "StateVariable name cannot be empty."
            )

        if self.value_type not in (
            float,
            int,
            bool,
        ):
            raise StateValueError(
                "StateVariable value_type must be "
                "float, int, or bool."
            )

        if self.default is not None:
            _validate_value(
                self.name,
                self.default,
                self.value_type,
            )

        object.__setattr__(
            self,
            "name",
            name,
        )


# ============================================================================
# CONTROL STATE
# ============================================================================


class ControlState(Mapping[str, StateValue]):
    """
    Deterministic local state container for a Control component.

    The object behaves like a read-only mapping from state name to
    state value.

    Example
    -------
    Dynamic controller:

        state = ControlState(
            definitions=[
                StateVariable("Efd", unit="pu"),
            ],
            values={
                "Efd": 1.05,
            },
        )

    Logic controller:

        state = ControlState(
            definitions=[
                StateVariable(
                    "latched",
                    value_type=bool,
                ),
            ],
            values={
                "latched": True,
            },
        )

    The object does not perform integration or execute control laws.
    """

    __slots__ = (
        "_definitions",
        "_values",
        "_index",
    )

    def __init__(
        self,
        definitions: Sequence[StateVariable] = (),
        values: Mapping[str, StateValue] | None = None,
    ) -> None:
        definitions = tuple(definitions)

        self._validate_definitions(
            definitions
        )

        self._definitions = definitions

        self._index = {
            variable.name: index
            for index, variable
            in enumerate(definitions)
        }

        supplied = dict(values or {})

        expected = set(
            self._index
        )

        actual = {
            str(name)
            for name in supplied
        }

        missing = expected - actual

        if missing:
            raise StateValueError(
                "Missing state values: "
                f"{sorted(missing)}"
            )

        unknown = actual - expected

        if unknown:
            raise StateValueError(
                "Unknown state values: "
                f"{sorted(unknown)}"
            )

        normalized: dict[str, StateValue] = {}

        for variable in definitions:
            value = supplied[
                variable.name
            ]

            _validate_value(
                variable.name,
                value,
                variable.value_type,
            )

            normalized[
                variable.name
            ] = value

        self._values = normalized

    # ========================================================================
    # MAPPING INTERFACE
    # ========================================================================

    def __getitem__(
        self,
        name: str,
    ) -> StateValue:
        try:
            return self._values[name]
        except KeyError as exc:
            raise StateNameError(
                f"Unknown state '{name}'."
            ) from exc

    def __iter__(self) -> Iterator[str]:
        return iter(
            variable.name
            for variable in self._definitions
        )

    def __len__(self) -> int:
        return len(
            self._definitions
        )

    # ========================================================================
    # DEFINITIONS
    # ========================================================================

    @property
    def definitions(
        self,
    ) -> tuple[StateVariable, ...]:
        """
        Return state definitions in authoritative order.
        """

        return self._definitions

    @property
    def names(
        self,
    ) -> tuple[str, ...]:
        """
        Return state names in authoritative order.
        """

        return tuple(
            variable.name
            for variable in self._definitions
        )

    @property
    def size(
        self,
    ) -> int:
        """
        Number of local state variables.
        """

        return len(
            self._definitions
        )

    # ========================================================================
    # VALUES
    # ========================================================================

    @property
    def values(
        self,
    ) -> dict[str, StateValue]:
        """
        Return a detached mapping containing the state values.
        """

        return dict(
            self._values
        )

    def copy(
        self,
    ) -> "ControlState":
        """
        Return an independent ControlState with identical values.
        """

        return ControlState(
            definitions=self._definitions,
            values=self._values,
        )

    def with_values(
        self,
        values: Mapping[str, StateValue],
    ) -> "ControlState":
        """
        Return a new state with the supplied values replaced.

        The existing object is not mutated.
        """

        merged = self.values()
        merged.update(values)

        return ControlState(
            definitions=self._definitions,
            values=merged,
        )

    # ========================================================================
    # VECTOR CONVERSION
    # ========================================================================

    def to_vector(
        self,
        *,
        dtype: type | np.dtype = float,
    ) -> np.ndarray:
        """
        Convert numeric state values to an ordered NumPy vector.

        Boolean states are converted to numeric values only for this
        representation:

            False → 0.0
            True  → 1.0

        This operation does NOT change the logical state type.

        The returned vector is detached from the ControlState.
        """

        result = np.empty(
            self.size,
            dtype=dtype,
        )

        for index, variable in enumerate(
            self._definitions
        ):
            value = self._values[
                variable.name
            ]

            if isinstance(value, bool):
                result[index] = (
                    1.0
                    if value
                    else 0.0
                )
            else:
                try:
                    numeric = float(value)
                except (
                    TypeError,
                    ValueError,
                ) as exc:
                    raise StateVectorError(
                        f"State '{variable.name}' "
                        "cannot be converted to a numeric vector."
                    ) from exc

                if not math.isfinite(numeric):
                    raise StateVectorError(
                        f"State '{variable.name}' "
                        "must be finite."
                    )

                result[index] = numeric

        return result

    @classmethod
    def from_vector(
        cls,
        definitions: Sequence[StateVariable],
        vector: Sequence[float] | np.ndarray,
        *,
        boolean_threshold: float = 0.5,
    ) -> "ControlState":
        """
        Construct ControlState from an ordered numeric vector.

        Boolean state variables are reconstructed using
        ``boolean_threshold``.

        This method is intended for representation conversion around
        numerical execution. It does not integrate or modify the vector.
        """

        definitions = tuple(
            definitions
        )

        cls._validate_definitions(
            definitions
        )

        array = np.asarray(
            vector,
            dtype=float,
        ).reshape(-1)

        if array.size != len(
            definitions
        ):
            raise StateVectorError(
                "Vector size mismatch: "
                f"expected {len(definitions)}, "
                f"got {array.size}."
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise StateVectorError(
                "State vector must contain "
                "only finite values."
            )

        threshold = float(
            boolean_threshold
        )

        if not math.isfinite(
            threshold
        ):
            raise StateVectorError(
                "Boolean threshold must be finite."
            )

        values: dict[str, StateValue] = {}

        for index, variable in enumerate(
            definitions
        ):
            numeric = float(
                array[index]
            )

            if variable.value_type is bool:
                values[
                    variable.name
                ] = numeric >= threshold

            elif variable.value_type is int:
                values[
                    variable.name
                ] = int(
                    round(numeric)
                )

            else:
                values[
                    variable.name
                ] = numeric

        return cls(
            definitions=definitions,
            values=values,
        )

    # ========================================================================
    # INDEXING
    # ========================================================================

    def index_of(
        self,
        name: str,
    ) -> int:
        """
        Return the deterministic vector index of a state.
        """

        try:
            return self._index[name]
        except KeyError as exc:
            raise StateNameError(
                f"Unknown state '{name}'."
            ) from exc

    def variable(
        self,
        name: str,
    ) -> StateVariable:
        """
        Return the definition of a named state.
        """

        index = self.index_of(
            name
        )

        return self._definitions[
            index
        ]

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_definitions(
        definitions: Sequence[StateVariable],
    ) -> None:
        names: list[str] = []

        for variable in definitions:
            if not isinstance(
                variable,
                StateVariable,
            ):
                raise StateValueError(
                    "All state definitions must "
                    "be StateVariable instances."
                )

            if variable.name in names:
                raise StateNameError(
                    "Duplicate state name: "
                    f"'{variable.name}'."
                )

            names.append(
                variable.name
            )

    def validate(self) -> None:
        """
        Validate the complete current state.

        Raises
        ------
        StateError
            If any state value violates its definition.
        """

        for variable in self._definitions:
            _validate_value(
                variable.name,
                self._values[
                    variable.name
                ],
                variable.value_type,
            )

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(
        self,
    ) -> dict[str, StateValue]:
        """
        Return an ordered, detached state mapping.
        """

        return {
            variable.name: self._values[
                variable.name
            ]
            for variable
            in self._definitions
        }

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __repr__(self) -> str:
        values = ", ".join(
            f"{name}={value!r}"
            for name, value
            in self._values.items()
        )

        return (
            f"ControlState("
            f"{values})"
        )


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def _validate_value(
    name: str,
    value: StateValue,
    expected_type: type,
) -> None:
    """
    Validate one state value against its definition.
    """

    if expected_type is bool:
        if not isinstance(
            value,
            bool,
        ):
            raise StateValueError(
                f"State '{name}' must be Boolean."
            )

        return

    if expected_type is int:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise StateValueError(
                f"State '{name}' must be an integer."
            )

        return

    if expected_type is float:
        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise StateValueError(
                f"State '{name}' must be numeric."
            )

        if not math.isfinite(
            float(value)
        ):
            raise StateValueError(
                f"State '{name}' must be finite."
            )

        return

    raise StateValueError(
        f"Unsupported state type for '{name}'."
    )


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "StateValue",
    "StateVariable",
    "StateError",
    "StateNameError",
    "StateValueError",
    "StateVectorError",
    "ControlState",
]
