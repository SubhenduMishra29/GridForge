```python id="7m4q2p"
"""
GridForge Multi-Machine Dynamic System
======================================

Coordinates multiple dynamic machine models and maps their local
dynamic equations into the global GridForge dynamic state vector.

Responsibilities
----------------
- Register dynamic machine models.
- Maintain deterministic machine ordering.
- Own the DynamicStateVector layout.
- Pack/unpack local machine states.
- Evaluate machine electrical outputs.
- Evaluate machine differential equations.
- Assemble a global derivative vector.

This module does NOT:

- solve the electrical network;
- construct Y-bus;
- perform numerical integration;
- process simulation events;
- modify network topology;
- implement AVR/Governor/PSS equations;
- own authoritative network state.

Architecture
------------
The intended coupling is:

    global x
       |
       v
    DynamicStateVector
       |
       v
    local machine states
       |
       +-----------------------+
       |                       |
       v                       v
    machine equations     electrical output
       |                       |
       v                       v
      dx/dt                 I / P / Q
                               |
                               v
                         Algebraic network
                               |
                               v
                              Vt

The DAE solver is responsible for coordinating this coupling.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from .machine_models import (
    DynamicMachineModel,
    ElectricalOutput,
    MachineInputs,
)
from .state_vector import (
    DynamicStateVector,
)


# ======================================================================
# ERRORS
# ======================================================================


class MultiMachineError(RuntimeError):
    """Raised when the multi-machine system is invalid."""


# ======================================================================
# MULTI-MACHINE SYSTEM
# ======================================================================


class MultiMachineSystem:
    """
    Collection and evaluator for dynamic machine models.

    Parameters
    ----------
    models:
        Dynamic machine models.

    Notes
    -----
    Machine ordering is fixed at construction time. This guarantees
    deterministic state-vector layout and derivative-vector ordering.
    """

    def __init__(
        self,
        models: Sequence[
            DynamicMachineModel
        ] = (),
    ) -> None:

        self._models: list[
            DynamicMachineModel
        ] = []

        self._model_by_id: dict[
            str,
            DynamicMachineModel,
        ] = {}

        self._model_by_bus: dict[
            str,
            DynamicMachineModel,
        ] = {}

        for model in models:
            self.add_model(
                model
            )

        self.state_vector = (
            DynamicStateVector(
                self._models
            )
        )

    # ==================================================================
    # MODEL REGISTRATION
    # ==================================================================

    def add_model(
        self,
        model: DynamicMachineModel,
    ) -> None:
        """
        Register one dynamic machine model.

        Registration is rejected after the state vector has been
        created. Construct a new MultiMachineSystem when changing the
        model set during a simulation.
        """

        if not isinstance(
            model,
            DynamicMachineModel,
        ):
            raise TypeError(
                "model must be a "
                "DynamicMachineModel."
            )

        machine_id = (
            model.machine_id
        )

        bus_id = (
            model.bus_id
        )

        if machine_id in (
            self._model_by_id
        ):
            raise MultiMachineError(
                "Duplicate dynamic machine "
                f"id '{machine_id}'."
            )

        if bus_id in (
            self._model_by_bus
        ):
            raise MultiMachineError(
                "Multiple dynamic machines "
                f"are registered on bus "
                f"'{bus_id}'."
            )

        if self._models:
            raise MultiMachineError(
                "Models cannot be added after "
                "the state vector has been "
                "initialized. Construct a new "
                "MultiMachineSystem."
            )

        self._models.append(
            model
        )

        self._model_by_id[
            machine_id
        ] = model

        self._model_by_bus[
            bus_id
        ] = model

    # ==================================================================
    # PROPERTIES
    # ==================================================================

    @property
    def models(
        self,
    ) -> tuple[
        DynamicMachineModel,
        ...
    ]:
        """Return registered dynamic models."""

        return tuple(
            self._models
        )

    @property
    def machine_ids(
        self,
    ) -> tuple[str, ...]:
        """Return dynamic machine identifiers."""

        return tuple(
            model.machine_id
            for model in self._models
        )

    @property
    def bus_ids(
        self,
    ) -> tuple[str, ...]:
        """Return buses associated with dynamic machines."""

        return tuple(
            model.bus_id
            for model in self._models
        )

    @property
    def size(
        self,
    ) -> int:
        """Return the total number of dynamic states."""

        return self.state_vector.size

    # ==================================================================
    # MODEL LOOKUP
    # ==================================================================

    def get_model(
        self,
        machine_id: str,
    ) -> DynamicMachineModel:
        """
        Return a model by machine identifier.
        """

        try:
            return self._model_by_id[
                machine_id
            ]

        except KeyError as exc:

            raise MultiMachineError(
                f"Unknown dynamic machine "
                f"'{machine_id}'."
            ) from exc

    def get_model_at_bus(
        self,
        bus_id: str,
    ) -> DynamicMachineModel:
        """
        Return the dynamic machine connected to a bus.
        """

        try:
            return self._model_by_bus[
                bus_id
            ]

        except KeyError as exc:

            raise MultiMachineError(
                f"No dynamic machine is "
                f"registered at bus '{bus_id}'."
            ) from exc

    # ==================================================================
    # STATE ACCESS
    # ==================================================================

    def state(
        self,
        vector: Sequence[float] | None = None,
    ) -> dict[
        str,
        dict[str, float],
    ]:
        """
        Return all machine-local states.

        Parameters
        ----------
        vector:
            Optional numerical state vector. If omitted, the current
            global state vector is used.
        """

        if vector is None:

            vector_array = (
                self.state_vector.values
            )

        else:

            vector_array = (
                self.state_vector._validate_vector(
                    vector
                )
            )

        return {
            model.machine_id:
                self.state_vector.model_state(
                    model.machine_id,
                    vector_array,
                )
            for model in self._models
        }

    def pack_states(
        self,
        states: Mapping[
            str,
            Mapping[str, float],
        ],
    ) -> np.ndarray:
        """
        Pack model-local states into the global vector.
        """

        return self.state_vector.pack(
            states
        )

    def unpack_states(
        self,
        vector: Sequence[float],
    ) -> dict[
        str,
        dict[str, float],
    ]:
        """
        Unpack a global vector into model-local states.
        """

        return self.state_vector.unpack(
            vector
        )

    # ==================================================================
    # ELECTRICAL OUTPUT
    # ==================================================================

    def electrical_outputs(
        self,
        vector: Sequence[float],
        terminal_voltages: Mapping[
            str,
            complex,
        ],
    ) -> dict[
        str,
        ElectricalOutput,
    ]:
        """
        Evaluate electrical output for every machine.

        Parameters
        ----------
        vector:
            Global dynamic-state vector.

        terminal_voltages:
            Mapping:

                bus_id -> complex terminal voltage

        Returns
        -------
        dict
            Mapping:

                machine_id -> ElectricalOutput

        Notes
        -----
        The terminal voltages are supplied by the algebraic network
        solver. This class does not calculate them.
        """

        state_map = (
            self.state_vector.unpack(
                vector
            )
        )

        outputs: dict[
            str,
            ElectricalOutput,
        ] = {}

        for model in self._models:

            bus_id = (
                model.bus_id
            )

            if bus_id not in (
                terminal_voltages
            ):
                raise MultiMachineError(
                    "Missing terminal voltage "
                    f"for machine "
                    f"'{model.machine_id}' "
                    f"at bus '{bus_id}'."
                )

            voltage = complex(
                terminal_voltages[
                    bus_id
                ]
            )

            outputs[
                model.machine_id
            ] = model.electrical_output(
                state=state_map[
                    model.machine_id
                ],
                terminal_voltage=voltage,
            )

        return outputs

    # ==================================================================
    # NETWORK CURRENT INJECTIONS
    # ==================================================================

    def current_injections(
        self,
        vector: Sequence[float],
        terminal_voltages: Mapping[
            str,
            complex,
        ],
    ) -> dict[
        str,
        complex,
    ]:
        """
        Return machine current injections indexed by network bus.

        The returned current is positive from the machine into the
        electrical network.
        """

        outputs = (
            self.electrical_outputs(
                vector,
                terminal_voltages,
            )
        )

        injections: dict[
            str,
            complex,
        ] = {}

        for model in self._models:

            output = outputs[
                model.machine_id
            ]

            bus_id = (
                model.bus_id
            )

            if bus_id in injections:
                raise MultiMachineError(
                    "Multiple current injections "
                    f"detected at bus '{bus_id}'."
                )

            injections[
                bus_id
            ] = complex(
                output.current
            )

        return injections

    # ==================================================================
    # DIFFERENTIAL EQUATIONS
    # ==================================================================

    def derivatives(
        self,
        vector: Sequence[float],
        inputs: Mapping[
            str,
            MachineInputs,
        ],
        time: float,
    ) -> np.ndarray:
        """
        Evaluate the complete global dynamic derivative vector.

        Parameters
        ----------
        vector:
            Global dynamic state vector.

        inputs:
            Mapping:

                machine_id -> MachineInputs

        time:
            Current simulation time.

        Returns
        -------
        numpy.ndarray
            Global derivative vector.

        Notes
        -----
        This method evaluates equations only. It does not integrate
        the state.
        """

        vector_array = (
            self.state_vector._validate_vector(
                vector
            )
        )

        state_map = (
            self.state_vector.unpack(
                vector_array
            )
        )

        derivatives: dict[
            str,
            Mapping[str, float],
        ] = {}

        for model in self._models:

            machine_id = (
                model.machine_id
            )

            if machine_id not in inputs:
                raise MultiMachineError(
                    "Missing MachineInputs for "
                    f"machine '{machine_id}'."
                )

            local_derivatives = (
                model.derivatives(
                    state=state_map[
                        machine_id
                    ],
                    inputs=inputs[
                        machine_id
                    ],
                    time=time,
                )
            )

            model.validate_derivatives(
                local_derivatives
            )

            derivatives[
                machine_id
            ] = local_derivatives

        return (
            self.state_vector.derivative_vector(
                derivatives
            )
        )

    # ==================================================================
    # ELECTRICAL POWER
    # ==================================================================

    def electrical_powers(
        self,
        vector: Sequence[float],
        terminal_voltages: Mapping[
            str,
            complex,
        ],
    ) -> dict[
        str,
        tuple[float, float],
    ]:
        """
        Return active and reactive electrical powers for all machines.

        Returns
        -------
        dict
            machine_id -> (P, Q)
        """

        outputs = (
            self.electrical_outputs(
                vector,
                terminal_voltages,
            )
        )

        return {
            machine_id: (
                float(
                    output.active_power
                ),
                float(
                    output.reactive_power
                ),
            )
            for machine_id, output
            in outputs.items()
        }

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initialize(
        self,
        terminal_voltages: Mapping[
            str,
            complex,
        ],
        electrical_powers: Mapping[
            str,
            float,
        ],
        mechanical_powers: Mapping[
            str,
            float,
        ],
    ) -> np.ndarray:
        """
        Initialize all dynamic machine models.

        Parameters
        ----------
        terminal_voltages:
            bus_id -> terminal voltage.

        electrical_powers:
            machine_id -> electrical active power.

        mechanical_powers:
            machine_id -> mechanical active power.

        Returns
        -------
        numpy.ndarray
            Initialized global state vector.

        Notes
        -----
        This performs model initialization only. It does not solve
        the network or perform numerical integration.
        """

        states: dict[
            str,
            dict[str, float],
        ] = {}

        for model in self._models:

            machine_id = (
                model.machine_id
            )

            bus_id = (
                model.bus_id
            )

            if bus_id not in (
                terminal_voltages
            ):
                raise MultiMachineError(
                    "Missing terminal voltage "
                    f"for machine "
                    f"'{machine_id}'."
                )

            if machine_id not in (
                electrical_powers
            ):
                raise MultiMachineError(
                    "Missing electrical power "
                    f"for machine "
                    f"'{machine_id}'."
                )

            if machine_id not in (
                mechanical_powers
            ):
                raise MultiMachineError(
                    "Missing mechanical power "
                    f"for machine "
                    f"'{machine_id}'."
                )

            states[
                machine_id
            ] = model.initialize(
                terminal_voltage=complex(
                    terminal_voltages[
                        bus_id
                    ]
                ),
                electrical_power=float(
                    electrical_powers[
                        machine_id
                    ]
                ),
                mechanical_power=float(
                    mechanical_powers[
                        machine_id
                    ]
                ),
            )

        return self.state_vector.pack(
            states
        )

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the multi-machine configuration and state vector.
        """

        if not self._models:
            raise MultiMachineError(
                "MultiMachineSystem contains "
                "no dynamic machine models."
            )

        self.state_vector.validate()

        for model in self._models:

            definitions = (
                model.state_definitions()
            )

            if not definitions:
                raise MultiMachineError(
                    f"Dynamic machine "
                    f"'{model.machine_id}' "
                    "declares no dynamic states."
                )

            names = [
                definition.name
                for definition
                in definitions
            ]

            if len(names) != len(
                set(names)
            ):
                raise MultiMachineError(
                    f"Dynamic machine "
                    f"'{model.machine_id}' "
                    "contains duplicate state names."
                )

    # ==================================================================
    # ITERATION
    # ==================================================================

    def __iter__(
        self,
    ):
        """
        Iterate through registered dynamic models.
        """

        return iter(
            self._models
        )


__all__ = [
    "MultiMachineError",
    "MultiMachineSystem",
]
```
