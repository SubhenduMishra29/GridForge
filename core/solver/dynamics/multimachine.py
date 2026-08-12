"""
GridForge Multi-Machine Dynamic System
======================================

Coordinates multiple dynamic machine models and exposes a single global
dynamic-state interface to the DAE solver.

Responsibilities
----------------
- Manage an ordered collection of dynamic machines.
- Maintain deterministic machine ordering.
- Build and initialize the global dynamic state vector.
- Map the global state vector to individual machines.
- Collect machine current injections.
- Collect machine electrical outputs.
- Assemble machine derivatives into one global derivative vector.

Non-responsibilities
--------------------
This module does NOT:

- solve the network algebraic equations;
- construct Y-bus;
- implement swing equations;
- implement AVR/governor/PSS physics;
- perform numerical integration;
- process protection events;
- modify network topology.

Architecture
------------

    DAESolver
        |
        v
    MultiMachineSystem
        |
        +---- DynamicMachine 1
        |
        +---- DynamicMachine 2
        |
        +---- DynamicMachine N

The global state vector is the sole numerical state passed to the
integrator.

Machine-specific state ownership is handled through the machine-model
state interface rather than by maintaining a second independent global
copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

import numpy as np


# ======================================================================
# TYPES
# ======================================================================

State = np.ndarray

VoltageMap = Mapping[
    str,
    complex,
]

ElectricalOutputMap = Mapping[
    str,
    Any,
]


# ======================================================================
# MACHINE MODEL CONTRACT
# ======================================================================


class DynamicMachine(Protocol):
    """
    Protocol implemented by dynamic machine models.

    A machine must have a stable unique identifier and bus identifier.

    The machine state is represented as a vector so that different
    machine models can expose different dynamic orders without forcing
    the multi-machine system to know their internal physics.
    """

    @property
    def machine_id(self) -> str:
        """Unique machine identifier."""
        ...

    @property
    def bus_id(self) -> str:
        """Electrical bus identifier."""
        ...

    @property
    def state_size(self) -> int:
        """Number of dynamic states."""
        ...

    def initial_state(
        self,
        terminal_voltage: complex,
        electrical_power: Any,
        mechanical_power: float,
        *,
        time: float = 0.0,
    ) -> State:
        """
        Return the machine's initialized dynamic state.
        """
        ...

    def current_injection(
        self,
        state: State,
        terminal_voltage: complex,
        *,
        time: float = 0.0,
    ) -> complex:
        """
        Return the machine terminal current injection.
        """
        ...

    def electrical_output(
        self,
        state: State,
        terminal_voltage: complex,
        *,
        time: float = 0.0,
    ) -> Any:
        """
        Return the machine electrical output.
        """
        ...

    def derivatives(
        self,
        state: State,
        terminal_voltage: complex,
        electrical_output: Any,
        *,
        time: float = 0.0,
    ) -> State:
        """
        Return the machine dynamic derivatives.
        """
        ...


# ======================================================================
# STATE SLICE
# ======================================================================


@dataclass(frozen=True)
class MachineStateSlice:
    """
    Immutable mapping between a machine and its global state slice.
    """

    machine_id: str
    start: int
    stop: int

    @property
    def size(self) -> int:
        """Number of states belonging to the machine."""
        return self.stop - self.start

    def extract(
        self,
        state: State,
    ) -> State:
        """Extract this machine's state from a global state vector."""

        return state[
            self.start:self.stop
        ]

    def insert(
        self,
        target: State,
        values: State,
    ) -> None:
        """Insert machine states into a global state vector."""

        target[
            self.start:self.stop
        ] = values


# ======================================================================
# ERRORS
# ======================================================================


class MultiMachineError(
    RuntimeError
):
    """Base exception for multi-machine failures."""


class DuplicateMachineError(
    MultiMachineError
):
    """Raised when duplicate machine IDs are supplied."""


class MachineStateError(
    MultiMachineError
):
    """Raised when a machine returns an invalid state."""


# ======================================================================
# MULTI-MACHINE SYSTEM
# ======================================================================


class MultiMachineSystem:
    """
    Global dynamic system containing multiple machine models.

    Parameters
    ----------
    machines:
        Ordered iterable of dynamic machine models.

    Notes
    -----
    Machine ordering is deterministic and becomes part of the numerical
    state-vector contract.

    Once constructed, the machine collection is treated as immutable for
    the lifetime of the simulation. This prevents state-vector indexing
    from changing during numerical integration.
    """

    def __init__(
        self,
        machines: Iterable[
            DynamicMachine
        ],
    ) -> None:

        machine_list = list(
            machines
        )

        if not machine_list:

            raise ValueError(
                "MultiMachineSystem "
                "requires at least "
                "one machine."
            )

        self._machines = tuple(
            machine_list
        )

        self._validate_machines()

        self._state_slices = (
            self._build_state_slices()
        )

        self._state_size = (
            sum(
                item.size
                for item in
                self._state_slices.values()
            )
        )

        self._state = np.empty(
            self._state_size,
            dtype=float,
        )

        self._initialized = False

    # ==================================================================
    # MACHINE COLLECTION
    # ==================================================================

    @property
    def machines(
        self,
    ) -> tuple[
        DynamicMachine,
        ...,
    ]:
        """
        Ordered machine collection.

        The returned tuple prevents accidental mutation of machine
        ordering during simulation.
        """

        return self._machines

    @property
    def machine_count(
        self,
    ) -> int:
        """Number of dynamic machines."""

        return len(
            self._machines
        )

    @property
    def state_size(
        self,
    ) -> int:
        """Total number of dynamic states."""

        return self._state_size

    @property
    def state(
        self,
    ) -> State:
        """
        Current global dynamic state.

        A copy is returned to prevent external mutation.
        """

        return self._state.copy()

    # ==================================================================
    # STATE MAPPING
    # ==================================================================

    @property
    def state_slices(
        self,
    ) -> Mapping[
        str,
        MachineStateSlice,
    ]:
        """
        Mapping of machine ID to global state slice.
        """

        return dict(
            self._state_slices
        )

    def machine_state(
        self,
        machine_id: str,
        state: State | None = None,
    ) -> State:
        """
        Return the state belonging to one machine.
        """

        machine_slice = (
            self._state_slices.get(
                str(machine_id)
            )
        )

        if machine_slice is None:

            raise KeyError(
                f"Unknown machine "
                f"'{machine_id}'."
            )

        source = (
            self._state
            if state is None
            else np.asarray(
                state,
                dtype=float,
            )
        )

        self._validate_global_state(
            source
        )

        return machine_slice.extract(
            source
        ).copy()

    def set_state(
        self,
        state: State,
    ) -> None:
        """
        Replace the complete global dynamic state.
        """

        state = np.asarray(
            state,
            dtype=float,
        )

        self._validate_global_state(
            state
        )

        self._state = state.copy()

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initialize(
        self,
        terminal_voltages: VoltageMap,
        electrical_powers: Mapping[
            str,
            Any,
        ],
        mechanical_powers: Mapping[
            str,
            float,
        ],
        *,
        time: float = 0.0,
    ) -> State:
        """
        Initialize every machine and assemble the global state vector.
        """

        if time < 0.0:

            raise ValueError(
                "Initial time cannot "
                "be negative."
            )

        state = np.empty(
            self._state_size,
            dtype=float,
        )

        for machine in (
            self._machines
        ):

            machine_id = (
                str(
                    machine.machine_id
                )
            )

            bus_id = (
                str(
                    machine.bus_id
                )
            )

            if bus_id not in (
                terminal_voltages
            ):

                raise MachineStateError(
                    f"No terminal voltage "
                    f"provided for machine "
                    f"'{machine_id}' at "
                    f"bus '{bus_id}'."
                )

            if machine_id not in (
                electrical_powers
            ):

                raise MachineStateError(
                    f"No electrical power "
                    f"provided for machine "
                    f"'{machine_id}'."
                )

            if machine_id not in (
                mechanical_powers
            ):

                raise MachineStateError(
                    f"No mechanical power "
                    f"provided for machine "
                    f"'{machine_id}'."
                )

            voltage = complex(
                terminal_voltages[
                    bus_id
                ]
            )

            electrical_power = (
                electrical_powers[
                    machine_id
                ]
            )

            mechanical_power = float(
                mechanical_powers[
                    machine_id
                ]
            )

            try:

                machine_state = (
                    machine.initial_state(
                        terminal_voltage=(
                            voltage
                        ),
                        electrical_power=(
                            electrical_power
                        ),
                        mechanical_power=(
                            mechanical_power
                        ),
                        time=time,
                    )
                )

            except Exception as exc:

                raise MachineStateError(
                    "Failed to initialize "
                    f"machine "
                    f"'{machine_id}'."
                ) from exc

            machine_state = (
                self._validate_machine_state(
                    machine,
                    machine_state,
                )
            )

            self._state_slices[
                machine_id
            ].insert(
                state,
                machine_state,
            )

        self._state = state

        self._initialized = True

        return self.state

    # ==================================================================
    # CURRENT INJECTIONS
    # ==================================================================

    def current_injections(
        self,
        state: State,
        *,
        time: float = 0.0,
        terminal_voltages: VoltageMap | None = None,
    ) -> dict[
        str,
        complex,
    ]:
        """
        Calculate current injections from all machines.

        Returns
        -------
        dict
            Mapping:

                bus_id -> complex current

        If multiple dynamic machines are connected to the same bus,
        their injections are accumulated.
        """

        state = self._validate_global_state(
            state
        )

        voltages = (
            self._require_terminal_voltages(
                terminal_voltages
            )
        )

        injections: dict[
            str,
            complex,
        ] = {}

        for machine in (
            self._machines
        ):

            machine_id = (
                str(
                    machine.machine_id
                )
            )

            bus_id = (
                str(
                    machine.bus_id
                )
            )

            if bus_id not in voltages:

                raise MachineStateError(
                    f"No terminal voltage "
                    f"available for machine "
                    f"'{machine_id}' at "
                    f"bus '{bus_id}'."
                )

            machine_state = (
                self.machine_state(
                    machine_id,
                    state,
                )
            )

            try:

                current = complex(
                    machine.current_injection(
                        state=machine_state,
                        terminal_voltage=(
                            complex(
                                voltages[
                                    bus_id
                                ]
                            )
                        ),
                        time=time,
                    )
                )

            except Exception as exc:

                raise MultiMachineError(
                    "Failed to calculate "
                    f"current injection "
                    f"for machine "
                    f"'{machine_id}'."
                ) from exc

            injections[
                bus_id
            ] = (
                injections.get(
                    bus_id,
                    0.0 + 0.0j,
                )
                + current
            )

        return injections

    # ==================================================================
    # ELECTRICAL OUTPUTS
    # ==================================================================

    def electrical_outputs(
        self,
        state: State,
        terminal_voltages: VoltageMap,
        *,
        time: float = 0.0,
    ) -> dict[
        str,
        Any,
    ]:
        """
        Calculate electrical outputs for all machines.
        """

        state = self._validate_global_state(
            state
        )

        voltages = (
            self._require_terminal_voltages(
                terminal_voltages
            )
        )

        outputs: dict[
            str,
            Any,
        ] = {}

        for machine in (
            self._machines
        ):

            machine_id = (
                str(
                    machine.machine_id
                )
            )

            bus_id = (
                str(
                    machine.bus_id
                )
            )

            if bus_id not in voltages:

                raise MachineStateError(
                    f"No terminal voltage "
                    f"available for machine "
                    f"'{machine_id}'."
                )

            machine_state = (
                self.machine_state(
                    machine_id,
                    state,
                )
            )

            try:

                outputs[
                    machine_id
                ] = (
                    machine.electrical_output(
                        state=machine_state,
                        terminal_voltage=(
                            complex(
                                voltages[
                                    bus_id
                                ]
                            )
                        ),
                        time=time,
                    )
                )

            except Exception as exc:

                raise MultiMachineError(
                    "Failed to calculate "
                    f"electrical output "
                    f"for machine "
                    f"'{machine_id}'."
                ) from exc

        return outputs

    # ==================================================================
    # DERIVATIVES
    # ==================================================================

    def derivatives(
        self,
        state: State,
        terminal_voltages: VoltageMap,
        electrical_outputs: ElectricalOutputMap,
        *,
        time: float = 0.0,
    ) -> State:
        """
        Assemble the global dynamic derivative vector.
        """

        state = self._validate_global_state(
            state
        )

        voltages = (
            self._require_terminal_voltages(
                terminal_voltages
            )
        )

        derivatives = np.empty(
            self._state_size,
            dtype=float,
        )

        for machine in (
            self._machines
        ):

            machine_id = (
                str(
                    machine.machine_id
                )
            )

            bus_id = (
                str(
                    machine.bus_id
                )
            )

            if bus_id not in voltages:

                raise MachineStateError(
                    f"No terminal voltage "
                    f"available for machine "
                    f"'{machine_id}'."
                )

            if machine_id not in (
                electrical_outputs
            ):

                raise MultiMachineError(
                    f"No electrical output "
                    f"available for machine "
                    f"'{machine_id}'."
                )

            machine_state = (
                self.machine_state(
                    machine_id,
                    state,
                )
            )

            try:

                machine_derivative = (
                    machine.derivatives(
                        state=machine_state,
                        terminal_voltage=(
                            complex(
                                voltages[
                                    bus_id
                                ]
                            )
                        ),
                        electrical_output=(
                            electrical_outputs[
                                machine_id
                            ]
                        ),
                        time=time,
                    )
                )

            except Exception as exc:

                raise MultiMachineError(
                    "Failed to calculate "
                    f"derivatives for "
                    f"machine "
                    f"'{machine_id}'."
                ) from exc

            machine_derivative = (
                self._validate_machine_state(
                    machine,
                    machine_derivative,
                    name="derivative",
                )
            )

            self._state_slices[
                machine_id
            ].insert(
                derivatives,
                machine_derivative,
            )

        return derivatives

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def _validate_machines(
        self,
    ) -> None:
        """
        Validate machine collection and IDs.
        """

        identifiers: set[
            str
        ] = set()

        for machine in (
            self._machines
        ):

            if not hasattr(
                machine,
                "machine_id",
            ):

                raise TypeError(
                    "Every dynamic machine "
                    "must provide "
                    "'machine_id'."
                )

            if not hasattr(
                machine,
                "bus_id",
            ):

                raise TypeError(
                    "Every dynamic machine "
                    "must provide "
                    "'bus_id'."
                )

            machine_id = str(
                machine.machine_id
            )

            if not machine_id:

                raise ValueError(
                    "Machine ID cannot "
                    "be empty."
                )

            if machine_id in identifiers:

                raise DuplicateMachineError(
                    "Duplicate machine ID "
                    f"'{machine_id}'."
                )

            identifiers.add(
                machine_id
            )

            try:

                state_size = int(
                    machine.state_size
                )

            except Exception as exc:

                raise TypeError(
                    f"Machine "
                    f"'{machine_id}' has "
                    "an invalid "
                    "'state_size'."
                ) from exc

            if state_size <= 0:

                raise ValueError(
                    f"Machine "
                    f"'{machine_id}' must "
                    "have at least one "
                    "dynamic state."
                )

    def _build_state_slices(
        self,
    ) -> dict[
        str,
        MachineStateSlice,
    ]:
        """
        Build deterministic machine-to-state mappings.
        """

        slices: dict[
            str,
            MachineStateSlice,
        ] = {}

        offset = 0

        for machine in (
            self._machines
        ):

            machine_id = str(
                machine.machine_id
            )

            size = int(
                machine.state_size
            )

            slices[
                machine_id
            ] = MachineStateSlice(
                machine_id=machine_id,
                start=offset,
                stop=offset + size,
            )

            offset += size

        return slices

    def _validate_global_state(
        self,
        state: State,
    ) -> np.ndarray:
        """
        Validate the global state vector.
        """

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.ndim != 1:

            raise MachineStateError(
                "Global dynamic state "
                "must be one-dimensional."
            )

        if state.size != (
            self._state_size
        ):

            raise MachineStateError(
                "Global dynamic state "
                f"has {state.size} values; "
                f"expected {self._state_size}."
            )

        if not np.all(
            np.isfinite(state)
        ):

            raise MachineStateError(
                "Global dynamic state "
                "contains non-finite "
                "values."
            )

        return state

    @staticmethod
    def _validate_machine_state(
        machine: DynamicMachine,
        values: State,
        *,
        name: str = "state",
    ) -> np.ndarray:
        """
        Validate a machine-local state vector.
        """

        values = np.asarray(
            values,
            dtype=float,
        )

        expected = int(
            machine.state_size
        )

        if values.ndim != 1:

            raise MachineStateError(
                f"Machine "
                f"'{machine.machine_id}' "
                f"{name} must be "
                "one-dimensional."
            )

        if values.size != expected:

            raise MachineStateError(
                f"Machine "
                f"'{machine.machine_id}' "
                f"{name} has "
                f"{values.size} values; "
                f"expected {expected}."
            )

        if not np.all(
            np.isfinite(values)
        ):

            raise MachineStateError(
                f"Machine "
                f"'{machine.machine_id}' "
                f"{name} contains "
                "non-finite values."
            )

        return values

    @staticmethod
    def _require_terminal_voltages(
        terminal_voltages: VoltageMap | None,
    ) -> dict[
        str,
        complex,
    ]:
        """
        Validate and normalize terminal-voltage data.
        """

        if terminal_voltages is None:

            raise MachineStateError(
                "Terminal voltages "
                "are required."
            )

        return {
            str(bus_id): complex(
                voltage
            )
            for bus_id, voltage
            in terminal_voltages.items()
        }


__all__ = [
    "DynamicMachine",
    "MachineStateSlice",
    "MultiMachineError",
    "DuplicateMachineError",
    "MachineStateError",
    "MultiMachineSystem",
]
```
