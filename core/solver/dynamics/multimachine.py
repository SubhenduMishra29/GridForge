"""
GridForge Multi-Machine Dynamic System
======================================

Coordinates multiple dynamic machine models participating in a
time-domain simulation.

Responsibilities
----------------
- Register multiple dynamic machine models.
- Build the global dynamic-state layout.
- Map global state vectors to individual machine states.
- Evaluate all machine differential equations.
- Assemble machine electrical current injections.
- Provide machine/network coupling data.

This module is an orchestration layer.

It does NOT:
- perform numerical integration
- implement the swing equation
- implement AVR/GOV/PSS equations
- manage simulation events
- own persistent equipment state
- modify the GridForge network directly

The network/algebraic solver remains responsible for solving the
electrical network using the assembled machine injections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .machine_models import (
    DynamicMachineModel,
    MachineInputs,
    MachineModelCollection,
)
from .state_vector import (
    DynamicStateVector,
    StateLayout,
)


class MultiMachineError(RuntimeError):
    """Raised when multi-machine coordination fails."""


@dataclass(frozen=True)
class MachineStateSlice:
    """
    Location of one machine's states inside the global state vector.

    Parameters
    ----------
    machine_id:
        Dynamic machine identifier.

    start:
        First global state index.

    stop:
        Exclusive final global state index.
    """

    machine_id: str
    start: int
    stop: int

    @property
    def size(self) -> int:
        return self.stop - self.start


class MultiMachineSystem:
    """
    Global dynamic-machine coordinator.

    Example
    -------

        machines = MultiMachineSystem(
            [
                machine_1,
                machine_2,
            ]
        )

        state = machines.create_state_vector()

        dx = machines.derivatives(
            state=state.pack(),
            inputs=machine_inputs,
            time=0.0,
        )

    The global state vector remains owned by DynamicStateVector.
    """

    def __init__(
        self,
        models: list[
            DynamicMachineModel
        ] | None = None,
    ) -> None:

        self.models = MachineModelCollection(
            models
        )

        self._layout: StateLayout | None = None

        self._state_slices: dict[
            str,
            MachineStateSlice,
        ] = {}

        self._finalized = False

    # =========================================================
    # MACHINE REGISTRATION
    # =========================================================

    def add(
        self,
        model: DynamicMachineModel,
    ) -> None:
        """
        Add a dynamic machine model.

        Models cannot be added after the state layout has been
        finalized.
        """

        if self._finalized:
            raise RuntimeError(
                "Cannot add machine after "
                "state layout has been finalized."
            )

        self.models.add(
            model
        )

    # =========================================================
    # STATE LAYOUT
    # =========================================================

    def build_state_layout(
        self,
    ) -> StateLayout:
        """
        Build and finalize the global dynamic-state layout.

        Returns
        -------
        StateLayout
            Finalized state layout.
        """

        if self._finalized:
            if self._layout is None:
                raise MultiMachineError(
                    "Internal state-layout inconsistency."
                )

            return self._layout

        layout = StateLayout()

        self.models.register_states(
            layout
        )

        self._layout = layout
        self._finalized = True

        self._build_state_slices()

        return layout

    def create_state_vector(
        self,
    ) -> DynamicStateVector:
        """
        Create the global dynamic state vector.

        The state layout is finalized automatically if required.
        """

        layout = self.build_state_layout()

        return layout.finalize()

    @property
    def state_layout(
        self,
    ) -> StateLayout:
        """Return the finalized state layout."""

        if self._layout is None:
            raise RuntimeError(
                "State layout has not been built."
            )

        return self._layout

    # =========================================================
    # STATE MAPPING
    # =========================================================

    def state_slice(
        self,
        machine_id: str,
    ) -> MachineStateSlice:
        """
        Return the global state-vector slice belonging to a machine.
        """

        if not self._finalized:
            self.build_state_layout()

        try:
            return self._state_slices[
                machine_id
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown dynamic machine: "
                f"'{machine_id}'."
            ) from exc

    def machine_state(
        self,
        state: np.ndarray,
        machine_id: str,
    ) -> np.ndarray:
        """
        Extract one machine's local state from the global state vector.
        """

        state = self._validate_global_state(
            state
        )

        state_slice = self.state_slice(
            machine_id
        )

        return state[
            state_slice.start:
            state_slice.stop
        ].copy()

    # =========================================================
    # DIFFERENTIAL EQUATIONS
    # =========================================================

    def derivatives(
        self,
        state: np.ndarray,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        time: float,
    ) -> np.ndarray:
        """
        Evaluate all machine differential equations.

        Parameters
        ----------
        state:
            Global differential-state vector.

        inputs:
            Mapping:

                machine_id -> MachineInputs

        time:
            Simulation time [s].

        Returns
        -------
        numpy.ndarray
            Global derivative vector.
        """

        state = self._validate_global_state(
            state
        )

        if not np.isfinite(time):
            raise ValueError(
                "Simulation time must be finite."
            )

        derivative = np.zeros_like(
            state
        )

        for model in self.models.models:

            if model.machine_id not in inputs:
                raise MultiMachineError(
                    "Missing dynamic inputs for "
                    f"machine '{model.machine_id}'."
                )

            machine_slice = self.state_slice(
                model.machine_id
            )

            local_state = state[
                machine_slice.start:
                machine_slice.stop
            ]

            local_derivative = (
                model.derivatives(
                    state=local_state,
                    inputs=inputs[
                        model.machine_id
                    ],
                    time=time,
                )
            )

            local_derivative = np.asarray(
                local_derivative,
                dtype=float,
            )

            if local_derivative.shape != (
                local_state.shape
            ):
                raise MultiMachineError(
                    "Derivative shape mismatch for "
                    f"machine '{model.machine_id}': "
                    f"expected {local_state.shape}, "
                    f"received "
                    f"{local_derivative.shape}."
                )

            if not np.all(
                np.isfinite(
                    local_derivative
                )
            ):
                raise MultiMachineError(
                    "Non-finite derivative returned "
                    f"by machine '{model.machine_id}'."
                )

            derivative[
                machine_slice.start:
                machine_slice.stop
            ] = local_derivative

        return derivative

    # =========================================================
    # ELECTRICAL CURRENT INJECTIONS
    # =========================================================

    def electrical_injections(
        self,
        state: np.ndarray,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
    ) -> dict[str, complex]:
        """
        Assemble complex current injections from all dynamic machines.

        Returns
        -------
        dict[str, complex]
            Mapping:

                bus_id -> complex current injection

        If multiple dynamic machines are connected to the same bus,
        their currents are summed.
        """

        state = self._validate_global_state(
            state
        )

        injections: dict[
            str,
            complex,
        ] = {}

        for model in self.models.models:

            if model.machine_id not in inputs:
                raise MultiMachineError(
                    "Missing dynamic inputs for "
                    f"machine '{model.machine_id}'."
                )

            machine_slice = self.state_slice(
                model.machine_id
            )

            local_state = state[
                machine_slice.start:
                machine_slice.stop
            ]

            current = model.electrical_output(
                state=local_state,
                inputs=inputs[
                    model.machine_id
                ],
            )

            current = complex(
                current
            )

            if not (
                np.isfinite(
                    current.real
                )
                and np.isfinite(
                    current.imag
                )
            ):
                raise MultiMachineError(
                    "Machine "
                    f"'{model.machine_id}' "
                    "returned a non-finite "
                    "electrical current."
                )

            injections[
                model.bus_id
            ] = (
                injections.get(
                    model.bus_id,
                    0.0 + 0.0j,
                )
                + current
            )

        return injections

    # =========================================================
    # MACHINE ACCESS
    # =========================================================

    def machine(
        self,
        machine_id: str,
    ) -> DynamicMachineModel:
        """Return a registered machine model."""

        return self.models.get(
            machine_id
        )

    @property
    def machine_ids(
        self,
    ) -> tuple[str, ...]:
        """Return registered machine IDs."""

        return tuple(
            model.machine_id
            for model in self.models.models
        )

    @property
    def size(self) -> int:
        """Return the total number of dynamic states."""

        if not self._finalized:
            self.build_state_layout()

        return self.state_layout.size

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def initialize(
        self,
        state: DynamicStateVector,
        inputs: Mapping[
            str,
            MachineInputs,
        ],
    ) -> None:
        """
        Initialize all machine states from an operating point.

        The supplied DynamicStateVector is updated in-place.
        """

        global_state = state.pack()

        self._validate_global_state(
            global_state
        )

        for model in self.models.models:

            if model.machine_id not in inputs:
                raise MultiMachineError(
                    "Missing initialization inputs for "
                    f"machine '{model.machine_id}'."
                )

            machine_slice = self.state_slice(
                model.machine_id
            )

            local_state = global_state[
                machine_slice.start:
                machine_slice.stop
            ].copy()

            initialized = model.initialize(
                inputs[
                    model.machine_id
                ],
                local_state,
            )

            initialized = np.asarray(
                initialized,
                dtype=float,
            )

            if initialized.shape != (
                local_state.shape
            ):
                raise MultiMachineError(
                    "Initialization state shape mismatch "
                    f"for machine "
                    f"'{model.machine_id}'."
                )

            global_state[
                machine_slice.start:
                machine_slice.stop
            ] = initialized

        state.unpack(
            global_state
        )

    # =========================================================
    # INTERNAL
    # =========================================================

    def _build_state_slices(
        self,
    ) -> None:
        """
        Build deterministic global-state slices.

        State definitions are already registered in model order,
        therefore slices are deterministic.
        """

        if self._layout is None:
            raise MultiMachineError(
                "Cannot build state slices without "
                "a state layout."
            )

        definitions = (
            self._layout._definitions
        )

        for model in self.models.models:

            indices = [
                index
                for index, definition
                in enumerate(definitions)
                if definition.model_id
                == model.machine_id
            ]

            if not indices:
                raise MultiMachineError(
                    "Machine "
                    f"'{model.machine_id}' "
                    "registered no dynamic states."
                )

            expected = list(
                range(
                    min(indices),
                    max(indices) + 1,
                )
            )

            if indices != expected:
                raise MultiMachineError(
                    "States belonging to machine "
                    f"'{model.machine_id}' "
                    "are not contiguous in the "
                    "global state layout."
                )

            self._state_slices[
                model.machine_id
            ] = MachineStateSlice(
                machine_id=model.machine_id,
                start=min(indices),
                stop=max(indices) + 1,
            )

    def _validate_global_state(
        self,
        state: np.ndarray,
    ) -> np.ndarray:

        if not self._finalized:
            self.build_state_layout()

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.ndim != 1:
            raise MultiMachineError(
                "Global dynamic state must be "
                "one-dimensional."
            )

        if state.size != self.size:
            raise MultiMachineError(
                "Global dynamic-state size mismatch: "
                f"expected {self.size}, "
                f"received {state.size}."
            )

        if not np.all(
            np.isfinite(state)
        ):
            raise MultiMachineError(
                "Global dynamic state contains "
                "non-finite values."
            )

        return state
