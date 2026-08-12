"""
GridForge Dynamic State Vector
==============================

Generic state container and layout manager for dynamic simulation.

Responsibilities
----------------
- Define the global ordering of dynamic states.
- Provide deterministic named-state indexing.
- Store differential state values as a NumPy vector.
- Pack/unpack state values safely.
- Support arbitrary dynamic models and arbitrary numbers of states.

The state vector is deliberately domain-neutral.

It does NOT:
- implement machine equations
- implement control equations
- perform numerical integration
- solve network algebraic equations
- own persistent equipment state

Dynamic equations are evaluated by dynamic models and integrated by
the dynamics integrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class StateDefinition:
    """
    Definition of one differential state.

    Parameters
    ----------
    name:
        Globally unique state name within the simulation.

    initial_value:
        Initial numerical value.

    model_id:
        Identifier of the dynamic model that owns the state.
    """

    name: str
    initial_value: float = 0.0
    model_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("State name must not be empty.")

        if not isinstance(self.initial_value, (int, float, np.number)):
            raise TypeError(
                f"Initial value for state '{self.name}' must be numeric."
            )


class DynamicStateVector:
    """
    Global differential-state vector for GridForge dynamic simulation.

    The class separates:

        state definition
            from
        numerical state values.

    Example
    -------
    >>> state = DynamicStateVector(
    ...     [
    ...         StateDefinition("G1.delta", 0.0, "G1"),
    ...         StateDefinition("G1.omega", 0.0, "G1"),
    ...         StateDefinition("G2.delta", 0.0, "G2"),
    ...         StateDefinition("G2.omega", 0.0, "G2"),
    ...     ]
    ... )

    >>> x = state.pack()
    >>> x.shape
    (4,)

    >>> state["G1.delta"]
    0.0

    The ordering established during construction is immutable.
    """

    def __init__(
        self,
        definitions: Iterable[StateDefinition],
    ) -> None:

        definitions = list(definitions)

        names = [definition.name for definition in definitions]

        if len(names) != len(set(names)):
            duplicates = sorted(
                {
                    name
                    for name in names
                    if names.count(name) > 1
                }
            )

            raise ValueError(
                "Duplicate dynamic state names: "
                + ", ".join(duplicates)
            )

        self._definitions: tuple[
            StateDefinition, ...
        ] = tuple(definitions)

        self._index: dict[str, int] = {
            definition.name: index
            for index, definition in enumerate(
                self._definitions
            )
        }

        self._values = np.asarray(
            [
                float(definition.initial_value)
                for definition in self._definitions
            ],
            dtype=float,
        )

    # =========================================================
    # BASIC PROPERTIES
    # =========================================================

    @property
    def size(self) -> int:
        """Return the number of differential states."""
        return self._values.size

    @property
    def names(self) -> tuple[str, ...]:
        """Return the ordered state names."""
        return tuple(
            definition.name
            for definition in self._definitions
        )

    @property
    def definitions(
        self,
    ) -> tuple[StateDefinition, ...]:
        """Return the immutable state definitions."""
        return self._definitions

    @property
    def values(self) -> np.ndarray:
        """
        Return the current numerical state vector.

        A copy is returned so callers cannot accidentally mutate the
        internal state without going through the state-vector API.
        """
        return self._values.copy()

    # =========================================================
    # INDEXING
    # =========================================================

    def index(self, name: str) -> int:
        """
        Return the numerical index of a named state.
        """
        try:
            return self._index[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown dynamic state: '{name}'"
            ) from exc

    def __contains__(self, name: str) -> bool:
        return name in self._index

    def __getitem__(
        self,
        key: str | int,
    ) -> float:

        if isinstance(key, str):
            key = self.index(key)

        return float(self._values[key])

    def __setitem__(
        self,
        key: str | int,
        value: float,
    ) -> None:

        if isinstance(key, str):
            key = self.index(key)

        if not isinstance(
            value,
            (int, float, np.number),
        ):
            raise TypeError(
                "Dynamic state value must be numeric."
            )

        self._values[key] = float(value)

    # =========================================================
    # PACK / UNPACK
    # =========================================================

    def pack(self) -> np.ndarray:
        """
        Return a copy of the global numerical state vector.

        The ordering is the ordering established during construction.
        """
        return self._values.copy()

    def unpack(
        self,
        values: Sequence[float] | np.ndarray,
    ) -> None:
        """
        Replace the complete numerical state vector.
        """

        array = np.asarray(
            values,
            dtype=float,
        )

        if array.ndim != 1:
            raise ValueError(
                "Dynamic state vector must be one-dimensional."
            )

        if array.size != self.size:
            raise ValueError(
                "State vector size mismatch: "
                f"expected {self.size}, "
                f"received {array.size}."
            )

        self._values[:] = array

    # =========================================================
    # NAMED STATE ACCESS
    # =========================================================

    def get(
        self,
        name: str,
    ) -> float:
        """Return a state value by name."""
        return self[name]

    def set(
        self,
        name: str,
        value: float,
    ) -> None:
        """Set a state value by name."""
        self[name] = value

    def as_dict(self) -> dict[str, float]:
        """
        Return the complete state as a name/value dictionary.
        """
        return {
            definition.name: float(
                self._values[index]
            )
            for index, definition in enumerate(
                self._definitions
            )
        }

    # =========================================================
    # MODEL-SPECIFIC ACCESS
    # =========================================================

    def model_state(
        self,
        model_id: str,
    ) -> np.ndarray:
        """
        Return all states belonging to a particular dynamic model.

        The returned array is a copy.
        """

        indices = [
            index
            for index, definition in enumerate(
                self._definitions
            )
            if definition.model_id == model_id
        ]

        return self._values[indices].copy()

    # =========================================================
    # NUMERICAL OPERATIONS
    # =========================================================

    def copy(self) -> "DynamicStateVector":
        """
        Return an independent copy of the state vector.
        """

        result = DynamicStateVector(
            self._definitions
        )

        result._values[:] = self._values

        return result

    def zeros_like(self) -> np.ndarray:
        """
        Return a zero derivative/state vector with the same shape.
        """
        return np.zeros_like(self._values)

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return (
            f"DynamicStateVector("
            f"size={self.size}, "
            f"states={self.names!r})"
        )


class StateLayout:
    """
    Builder for deterministic dynamic-state layouts.

    Dynamic models can register arbitrary states without requiring the
    global solver to know their physical meaning.

    The layout is finalized explicitly before simulation.
    """

    def __init__(self) -> None:
        self._definitions: list[
            StateDefinition
        ] = []

        self._finalized = False

    def add_state(
        self,
        name: str,
        initial_value: float = 0.0,
        model_id: str | None = None,
    ) -> int:
        """
        Add one dynamic state.

        Returns
        -------
        int
            Index assigned to the state.
        """

        if self._finalized:
            raise RuntimeError(
                "State layout is already finalized."
            )

        if any(
            definition.name == name
            for definition in self._definitions
        ):
            raise ValueError(
                f"Dynamic state already exists: '{name}'"
            )

        definition = StateDefinition(
            name=name,
            initial_value=initial_value,
            model_id=model_id,
        )

        self._definitions.append(
            definition
        )

        return len(self._definitions) - 1

    def add_states(
        self,
        definitions: Iterable[StateDefinition],
    ) -> None:
        """Add multiple dynamic states."""

        for definition in definitions:
            self.add_state(
                name=definition.name,
                initial_value=definition.initial_value,
                model_id=definition.model_id,
            )

    def finalize(self) -> DynamicStateVector:
        """
        Finalize the layout and create its state vector.

        Once finalized, no additional states may be registered.
        """

        self._finalized = True

        return DynamicStateVector(
            self._definitions
        )

    @property
    def size(self) -> int:
        """Return the number of registered states."""
        return len(self._definitions)

    @property
    def finalized(self) -> bool:
        return self._finalized
