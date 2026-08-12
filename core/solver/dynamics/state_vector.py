```python
"""
GridForge Dynamic State Vector
==============================

Global dynamic-state representation for GridForge time-domain
simulation.

Responsibilities
----------------
- Build a deterministic global state layout from dynamic models.
- Pack named model states into a numerical vector.
- Unpack a numerical vector into model-local state mappings.
- Provide model/state indexing.
- Validate state-vector dimensions and values.

The state vector is the authoritative numerical representation used
by the dynamic solver and numerical integrators.

Architectural rules
-------------------
- Dynamic models declare their states.
- This module owns the global numerical layout.
- Integrators operate on numerical vectors.
- Machine models do not own integration.
- No network equations are implemented here.
- No simulation events are implemented here.
- No AVR/GOV/PSS-specific state containers are hard-coded here.

The resulting global vector is:

    x = [model_1 states, model_2 states, ..., model_n states]

The order is deterministic and follows the order in which models are
registered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping, Sequence

import numpy as np

from .machine_models import (
    DynamicMachineModel,
)


# ======================================================================
# ERRORS
# ======================================================================


class StateVectorError(ValueError):
    """Raised when a dynamic-state vector operation is invalid."""


# ======================================================================
# STATE LOCATION
# ======================================================================


@dataclass(frozen=True)
class StateLocation:
    """
    Location of one dynamic state in the global vector.

    Parameters
    ----------
    machine_id:
        Dynamic-model identifier.

    state_name:
        Local state name.

    index:
        Global vector index.

    description:
        State description.

    units:
        Engineering units.
    """

    machine_id: str
    state_name: str
    index: int
    description: str = ""
    units: str = "pu"


# ======================================================================
# STATE VECTOR
# ======================================================================


class DynamicStateVector:
    """
    Global dynamic-state vector.

    Parameters
    ----------
    models:
        Dynamic machine models whose states form the global vector.

    Notes
    -----
    The vector layout is immutable after construction.

    Model-local state values are stored separately from the numerical
    vector only conceptually; ``pack`` and ``unpack`` provide the
    authoritative conversion between the two representations.

    Example
    -------
    For two classical machines:

        Machine G1:
            delta
            omega

        Machine G2:
            delta
            omega

    the global vector is:

        [G1.delta, G1.omega, G2.delta, G2.omega]
    """

    def __init__(
        self,
        models: Sequence[
            DynamicMachineModel
        ],
    ) -> None:

        self.models = tuple(
            models
        )

        self._locations: tuple[
            StateLocation,
            ...
        ] = ()

        self._machine_indices: dict[
            str,
            dict[str, int],
        ] = {}

        self._machine_states: dict[
            str,
            tuple[str, ...],
        ] = {}

        self._build_layout()

        self._values = np.zeros(
            self.size,
            dtype=float,
        )

        self._initialize_values()

    # ==================================================================
    # LAYOUT
    # ==================================================================

    def _build_layout(
        self,
    ) -> None:

        locations: list[
            StateLocation
        ] = []

        machine_indices: dict[
            str,
            dict[str, int],
        ] = {}

        machine_states: dict[
            str,
            tuple[str, ...],
        ] = {}

        seen_machine_ids: set[str] = set()

        index = 0

        for model in self.models:

            machine_id = (
                model.machine_id
            )

            if machine_id in seen_machine_ids:
                raise StateVectorError(
                    "Duplicate dynamic-model "
                    f"identifier '{machine_id}'."
                )

            seen_machine_ids.add(
                machine_id
            )

            definitions = tuple(
                model.state_definitions()
            )

            local_names: list[str] = []

            indices: dict[
                str,
                int,
            ] = {}

            for definition in definitions:

                name = definition.name

                if name in indices:
                    raise StateVectorError(
                        "Duplicate state "
                        f"'{name}' in model "
                        f"'{machine_id}'."
                    )

                indices[name] = index

                local_names.append(
                    name
                )

                locations.append(
                    StateLocation(
                        machine_id=machine_id,
                        state_name=name,
                        index=index,
                        description=(
                            definition.description
                        ),
                        units=(
                            definition.units
                        ),
                    )
                )

                index += 1

            machine_indices[
                machine_id
            ] = indices

            machine_states[
                machine_id
            ] = tuple(
                local_names
            )

        self._locations = tuple(
            locations
        )

        self._machine_indices = (
            machine_indices
        )

        self._machine_states = (
            machine_states
        )

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def _initialize_values(
        self,
    ) -> None:

        for model in self.models:

            machine_id = (
                model.machine_id
            )

            state = model.initial_state()

            self._set_model_state(
                machine_id,
                state,
            )

    # ==================================================================
    # BASIC PROPERTIES
    # ==================================================================

    @property
    def size(
        self,
    ) -> int:
        """Return the total number of dynamic states."""

        return len(
            self._locations
        )

    @property
    def locations(
        self,
    ) -> tuple[
        StateLocation,
        ...
    ]:
        """Return the immutable global state layout."""

        return self._locations

    @property
    def values(
        self,
    ) -> np.ndarray:
        """
        Return a copy of the current numerical state vector.
        """

        return self._values.copy()

    # ==================================================================
    # PACK / UNPACK
    # ==================================================================

    def pack(
        self,
        states: Mapping[
            str,
            Mapping[str, float],
        ] | None = None,
    ) -> np.ndarray:
        """
        Pack model-local states into a numerical vector.

        Parameters
        ----------
        states:
            Optional mapping:

                machine_id -> state_name -> value

            If omitted, the currently stored global state is returned.
        """

        if states is None:
            return self._values.copy()

        vector = np.zeros(
            self.size,
            dtype=float,
        )

        for model in self.models:

            machine_id = (
                model.machine_id
            )

            if machine_id not in states:
                raise StateVectorError(
                    "Missing state mapping for "
                    f"model '{machine_id}'."
                )

            local_state = states[
                machine_id
            ]

            self._validate_local_state(
                model,
                local_state,
            )

            for name, index in (
                self._machine_indices[
                    machine_id
                ].items()
            ):

                vector[index] = float(
                    local_state[name]
                )

        self._validate_vector(
            vector
        )

        return vector

    def unpack(
        self,
        vector: Sequence[float],
    ) -> dict[
        str,
        dict[str, float],
    ]:
        """
        Convert a numerical vector into model-local state mappings.

        The internal state is also updated to the supplied vector.
        """

        vector_array = (
            self._validate_vector(
                vector
            )
        )

        states: dict[
            str,
            dict[str, float],
        ] = {}

        for model in self.models:

            machine_id = (
                model.machine_id
            )

            states[
                machine_id
            ] = {}

            for name, index in (
                self._machine_indices[
                    machine_id
                ].items()
            ):

                states[
                    machine_id
                ][name] = float(
                    vector_array[index]
                )

        self._values = (
            vector_array.copy()
        )

        return states

    # ==================================================================
    # MODEL STATE ACCESS
    # ==================================================================

    def model_state(
        self,
        machine_id: str,
        vector: Sequence[float] | None = None,
    ) -> dict[str, float]:
        """
        Return the local state mapping for one dynamic model.

        Parameters
        ----------
        machine_id:
            Dynamic-model identifier.

        vector:
            Optional external numerical vector. If omitted, the current
            state vector is used.
        """

        self._require_machine(
            machine_id
        )

        if vector is None:
            vector_array = self._values
        else:
            vector_array = (
                self._validate_vector(
                    vector
                )
            )

        return {
            name: float(
                vector_array[index]
            )
            for name, index
            in self._machine_indices[
                machine_id
            ].items()
        }

    def set_model_state(
        self,
        machine_id: str,
        state: Mapping[str, float],
    ) -> None:
        """
        Replace the local state of one dynamic model.
        """

        self._require_machine(
            machine_id
        )

        model = self._model(
            machine_id
        )

        self._validate_local_state(
            model,
            state,
        )

        self._set_model_state(
            machine_id,
            state,
        )

    def _set_model_state(
        self,
        machine_id: str,
        state: Mapping[str, float],
    ) -> None:

        for name, index in (
            self._machine_indices[
                machine_id
            ].items()
        ):

            self._values[index] = (
                float(
                    state[name]
                )
            )

    # ==================================================================
    # INDIVIDUAL STATE ACCESS
    # ==================================================================

    def get(
        self,
        machine_id: str,
        state_name: str,
    ) -> float:
        """
        Return one state value.
        """

        index = self.index_of(
            machine_id,
            state_name,
        )

        return float(
            self._values[index]
        )

    def set(
        self,
        machine_id: str,
        state_name: str,
        value: float,
    ) -> None:
        """
        Set one state value.
        """

        if not np.isfinite(
            value
        ):
            raise StateVectorError(
                "State value must be finite."
            )

        index = self.index_of(
            machine_id,
            state_name,
        )

        self._values[index] = (
            float(value)
        )

    def index_of(
        self,
        machine_id: str,
        state_name: str,
    ) -> int:
        """
        Return the global index of a model-local state.
        """

        self._require_machine(
            machine_id
        )

        indices = (
            self._machine_indices[
                machine_id
            ]
        )

        if state_name not in indices:
            raise StateVectorError(
                f"Model '{machine_id}' "
                f"does not define state "
                f"'{state_name}'."
            )

        return indices[
            state_name
        ]

    # ==================================================================
    # DERIVATIVE VECTOR
    # ==================================================================

    def derivative_vector(
        self,
        derivatives: Mapping[
            str,
            Mapping[str, float],
        ],
    ) -> np.ndarray:
        """
        Pack model-local derivatives into a global vector.

        Parameters
        ----------
        derivatives:
            Mapping:

                machine_id -> state_name -> derivative
        """

        vector = np.zeros(
            self.size,
            dtype=float,
        )

        for model in self.models:

            machine_id = (
                model.machine_id
            )

            if machine_id not in derivatives:
                raise StateVectorError(
                    "Missing derivatives for "
                    f"model '{machine_id}'."
                )

            local = derivatives[
                machine_id
            ]

            expected = set(
                self._machine_states[
                    machine_id
                ]
            )

            received = set(
                local.keys()
            )

            missing = (
                expected
                - received
            )

            if missing:
                raise StateVectorError(
                    f"Missing derivatives for "
                    f"model '{machine_id}': "
                    f"{sorted(missing)}"
                )

            for name, index in (
                self._machine_indices[
                    machine_id
                ].items()
            ):

                value = float(
                    local[name]
                )

                if not np.isfinite(
                    value
                ):
                    raise StateVectorError(
                        f"Derivative "
                        f"'{machine_id}.{name}' "
                        "is not finite."
                    )

                vector[index] = (
                    value
                )

        return vector

    # ==================================================================
    # ITERATION / INTROSPECTION
    # ==================================================================

    def __iter__(
        self,
    ) -> Iterator[
        StateLocation
    ]:
        """Iterate through the global state layout."""

        return iter(
            self._locations
        )

    def model_ids(
        self,
    ) -> tuple[str, ...]:
        """Return dynamic-model identifiers."""

        return tuple(
            model.machine_id
            for model in self.models
        )

    def state_names(
        self,
        machine_id: str,
    ) -> tuple[str, ...]:
        """Return state names for one model."""

        self._require_machine(
            machine_id
        )

        return self._machine_states[
            machine_id
        ]

    # ==================================================================
    # COPY
    # ==================================================================

    def copy(
        self,
    ) -> "DynamicStateVector":
        """
        Return an independent state-vector copy.

        The model layout is reused, while numerical values are copied.
        """

        copied = DynamicStateVector(
            self.models
        )

        copied._values = (
            self._values.copy()
        )

        return copied

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def validate(
        self,
    ) -> None:
        """Validate the current state vector."""

        self._validate_vector(
            self._values
        )

    def _validate_vector(
        self,
        vector: Sequence[float],
    ) -> np.ndarray:

        array = np.asarray(
            vector,
            dtype=float,
        )

        if array.ndim != 1:
            raise StateVectorError(
                "Dynamic state vector must "
                "be one-dimensional."
            )

        if array.size != self.size:
            raise StateVectorError(
                "Dynamic state vector size "
                f"mismatch: expected "
                f"{self.size}, received "
                f"{array.size}."
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise StateVectorError(
                "Dynamic state vector contains "
                "non-finite values."
            )

        return array

    def _validate_local_state(
        self,
        model: DynamicMachineModel,
        state: Mapping[str, float],
    ) -> None:

        expected = set(
            model.state_names()
        )

        received = set(
            state.keys()
        )

        missing = (
            expected
            - received
        )

        if missing:
            raise StateVectorError(
                f"Model '{model.machine_id}' "
                f"is missing states: "
                f"{sorted(missing)}"
            )

        extra = (
            received
            - expected
        )

        if extra:
            raise StateVectorError(
                f"Model '{model.machine_id}' "
                f"contains unknown states: "
                f"{sorted(extra)}"
            )

        for name in expected:

            value = float(
                state[name]
            )

            if not np.isfinite(
                value
            ):
                raise StateVectorError(
                    f"State "
                    f"'{model.machine_id}.{name}' "
                    "must be finite."
                )

    # ==================================================================
    # INTERNAL LOOKUP
    # ==================================================================

    def _require_machine(
        self,
        machine_id: str,
    ) -> None:

        if machine_id not in (
            self._machine_indices
        ):
            raise StateVectorError(
                f"Unknown dynamic model "
                f"'{machine_id}'."
            )

    def _model(
        self,
        machine_id: str,
    ) -> DynamicMachineModel:

        for model in self.models:

            if (
                model.machine_id
                == machine_id
            ):
                return model

        raise StateVectorError(
            f"Unknown dynamic model "
            f"'{machine_id}'."
        )


__all__ = [
    "StateVectorError",
    "StateLocation",
    "DynamicStateVector",
]
```
