```python
"""
GridForge Dynamic Machine Models
================================

Dynamic-model contracts used by the GridForge time-domain solver.

Architectural responsibilities
-------------------------------
A dynamic machine model:

- identifies the machine and its network bus;
- declares its local dynamic states;
- initializes those states;
- evaluates differential equations;
- evaluates the electrical terminal/network interface;
- consumes algebraic terminal quantities;
- exposes model parameters.

A dynamic machine model does NOT:

- integrate its own states;
- own the global dynamic state vector;
- construct or solve Y-bus;
- modify network topology;
- implement simulation events;
- implement the numerical integration algorithm;
- hard-code AVR/Governor/PSS implementations.

Controller models such as AVR, governor and PSS are intended to be
composable dynamic-model components/plugins. Their states, when present,
are registered into the common dynamic state vector.

State convention
----------------
The machine model works with a local mapping of named state variables.

The global state-vector implementation is responsible for converting
between the global numerical vector and these local mappings.

Electrical convention
---------------------
Complex electrical quantities use GridForge per-unit conventions.

Terminal voltage:

    Vt = V.real + j * V.imag

Terminal current:

    It = Ir + j * Ii

Complex power:

    S = Vt * conj(It)

Therefore:

    P = real(S)
    Q = imag(S)

The machine model is responsible for determining the current injection
corresponding to its internal dynamic state and terminal voltage.

This file intentionally contains interfaces and a classical machine
implementation suitable as the initial reference model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np


# ======================================================================
# DATA CONTRACTS
# ======================================================================


@dataclass(frozen=True)
class MachineInputs:
    """
    Algebraic and external inputs supplied to a dynamic machine model.

    Parameters
    ----------
    terminal_voltage:
        Complex terminal voltage [pu].

    electrical_power:
        Electrical active power extracted from the network [pu].

        This value should normally be calculated from the network
        algebraic solution rather than supplied independently.

    mechanical_power:
        External mechanical-power reference [pu].

    terminal_current:
        Complex terminal current [pu], when available.

    electrical_reactive_power:
        Electrical reactive power [pu], when available.
    """

    terminal_voltage: complex

    electrical_power: float = 0.0

    mechanical_power: float = 0.0

    terminal_current: complex | None = None

    electrical_reactive_power: float | None = None

    def __post_init__(self) -> None:

        voltage = complex(
            self.terminal_voltage
        )

        if not (
            np.isfinite(voltage.real)
            and np.isfinite(voltage.imag)
        ):
            raise ValueError(
                "terminal_voltage must be finite."
            )

        if not np.isfinite(
            self.electrical_power
        ):
            raise ValueError(
                "electrical_power must be finite."
            )

        if not np.isfinite(
            self.mechanical_power
        ):
            raise ValueError(
                "mechanical_power must be finite."
            )

        if self.terminal_current is not None:

            current = complex(
                self.terminal_current
            )

            if not (
                np.isfinite(current.real)
                and np.isfinite(current.imag)
            ):
                raise ValueError(
                    "terminal_current must be finite."
                )

        if (
            self.electrical_reactive_power
            is not None
            and not np.isfinite(
                self.electrical_reactive_power
            )
        ):
            raise ValueError(
                "electrical_reactive_power must be finite."
            )


@dataclass(frozen=True)
class ElectricalOutput:
    """
    Electrical interface exposed by a dynamic machine.

    Parameters
    ----------
    current:
        Complex current injected into the network [pu].

    active_power:
        Active electrical power [pu].

    reactive_power:
        Reactive electrical power [pu].
    """

    current: complex

    active_power: float

    reactive_power: float

    def __post_init__(self) -> None:

        current = complex(
            self.current
        )

        if not (
            np.isfinite(current.real)
            and np.isfinite(current.imag)
        ):
            raise ValueError(
                "current must be finite."
            )

        if not np.isfinite(
            self.active_power
        ):
            raise ValueError(
                "active_power must be finite."
            )

        if not np.isfinite(
            self.reactive_power
        ):
            raise ValueError(
                "reactive_power must be finite."
            )


@dataclass(frozen=True)
class StateDefinition:
    """
    Definition of one dynamic state.

    Parameters
    ----------
    name:
        Unique state name within the model.

    initial_value:
        Default initial value.

    description:
        Human-readable description.

    units:
        Engineering units.
    """

    name: str

    initial_value: float = 0.0

    description: str = ""

    units: str = "pu"

    def __post_init__(self) -> None:

        if not self.name:
            raise ValueError(
                "Dynamic state name cannot be empty."
            )

        if not np.isfinite(
            self.initial_value
        ):
            raise ValueError(
                f"Initial value for state "
                f"'{self.name}' must be finite."
            )


@dataclass(frozen=True)
class DynamicModelMetadata:
    """
    Descriptive metadata for a dynamic model.
    """

    model_type: str

    model_name: str

    model_version: str = "1.0"

    description: str = ""


# ======================================================================
# BASE DYNAMIC MODEL
# ======================================================================


class DynamicMachineModel(ABC):
    """
    Abstract base contract for GridForge dynamic machine models.

    The model owns physical/dynamic equations.

    The global solver owns:
        - state storage;
        - state packing/unpacking;
        - integration;
        - simulation time;
        - events;
        - network solution.

    Parameters
    ----------
    machine_id:
        Unique dynamic-model identifier.

    bus_id:
        Network bus to which the dynamic machine is connected.
    """

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
    ) -> None:

        if not machine_id:
            raise ValueError(
                "machine_id cannot be empty."
            )

        if not bus_id:
            raise ValueError(
                "bus_id cannot be empty."
            )

        self.machine_id = machine_id
        self.bus_id = bus_id

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def metadata(
        self,
    ) -> DynamicModelMetadata:
        """
        Return model metadata.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # STATE DEFINITION
    # ------------------------------------------------------------------

    @abstractmethod
    def state_definitions(
        self,
    ) -> Sequence[StateDefinition]:
        """
        Return the model's local dynamic-state definitions.

        The order returned here is the canonical local state order.
        """
        raise NotImplementedError

    def state_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return the model's local state names.
        """

        return tuple(
            definition.name
            for definition
            in self.state_definitions()
        )

    def initial_state(
        self,
    ) -> dict[str, float]:
        """
        Return the initial local state.

        Subclasses may override this when the operating point requires
        a calculated initialization.
        """

        return {
            definition.name:
                float(
                    definition.initial_value
                )
            for definition
            in self.state_definitions()
        }

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------

    def initialize(
        self,
        terminal_voltage: complex,
        electrical_power: float,
        mechanical_power: float,
    ) -> dict[str, float]:
        """
        Initialize the dynamic model from an operating point.

        The default implementation returns the declared initial state.

        More sophisticated machine models should override this method
        to calculate internally consistent states.
        """

        del terminal_voltage
        del electrical_power
        del mechanical_power

        return self.initial_state()

    # ------------------------------------------------------------------
    # DIFFERENTIAL EQUATIONS
    # ------------------------------------------------------------------

    @abstractmethod
    def derivatives(
        self,
        state: Mapping[str, float],
        inputs: MachineInputs,
        time: float,
    ) -> Mapping[str, float]:
        """
        Evaluate local differential equations.

        Returns
        -------
        Mapping[str, float]
            State-name -> time derivative.

        Important
        ---------
        This method must NOT modify ``state`` and must NOT perform
        numerical integration.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # ELECTRICAL INTERFACE
    # ------------------------------------------------------------------

    @abstractmethod
    def electrical_output(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> ElectricalOutput:
        """
        Calculate the machine's electrical network interface.

        The returned current is the current injected by the machine
        into the electrical network.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate_state(
        self,
        state: Mapping[str, float],
    ) -> None:
        """
        Validate that all declared states are present and finite.
        """

        expected = set(
            self.state_names()
        )

        received = set(
            state.keys()
        )

        missing = expected - received

        if missing:
            raise ValueError(
                f"Machine '{self.machine_id}' is "
                f"missing dynamic states: "
                f"{sorted(missing)}"
            )

        for name in expected:

            value = state[name]

            if not np.isfinite(
                value
            ):
                raise ValueError(
                    f"Dynamic state '{name}' "
                    f"of machine "
                    f"'{self.machine_id}' "
                    f"is not finite."
                )

    def validate_derivatives(
        self,
        derivatives: Mapping[str, float],
    ) -> None:
        """
        Validate a derivative mapping.
        """

        expected = set(
            self.state_names()
        )

        received = set(
            derivatives.keys()
        )

        missing = expected - received

        if missing:
            raise ValueError(
                f"Machine '{self.machine_id}' "
                f"did not return derivatives for "
                f"{sorted(missing)}"
            )

        for name in expected:

            value = derivatives[name]

            if not np.isfinite(
                value
            ):
                raise ValueError(
                    f"Derivative of state "
                    f"'{name}' in machine "
                    f"'{self.machine_id}' "
                    f"is not finite."
                )


# ======================================================================
# CLASSICAL SYNCHRONOUS MACHINE
# ======================================================================


class ClassicalSynchronousMachine(
    DynamicMachineModel
):
    """
    Classical synchronous-machine transient-stability model.

    The internal emf is represented as a constant-magnitude voltage
    behind transient reactance.

    Dynamic states
    --------------
    delta:
        Rotor electrical angle [rad].

    omega:
        Rotor speed deviation [pu].

    Equations
    ---------
    d(delta)/dt = omega_base * omega

    d(omega)/dt =
        (Pm - Pe - D*omega) / (2H)

    Electrical interface
    --------------------
    E = E' * exp(j*delta)

    I = (E - Vt) / (j*Xd_prime)

    where the current is positive from the machine into the network.

    Notes
    -----
    This is deliberately a reference transient-stability model.
    Detailed subtransient machine equations belong in separate
    specialized models/plugins.
    """

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
        H: float,
        Xd_prime: float,
        E_prime: float = 1.0,
        damping: float = 0.0,
        frequency: float = 50.0,
        initial_delta: float = 0.0,
        initial_omega: float = 0.0,
    ) -> None:

        super().__init__(
            machine_id=machine_id,
            bus_id=bus_id,
        )

        if H <= 0.0:
            raise ValueError(
                "H must be greater than zero."
            )

        if Xd_prime <= 0.0:
            raise ValueError(
                "Xd_prime must be greater than zero."
            )

        if E_prime <= 0.0:
            raise ValueError(
                "E_prime must be greater than zero."
            )

        if frequency <= 0.0:
            raise ValueError(
                "frequency must be greater than zero."
            )

        if not np.isfinite(
            damping
        ):
            raise ValueError(
                "damping must be finite."
            )

        self.H = float(H)

        self.Xd_prime = float(
            Xd_prime
        )

        self.E_prime = float(
            E_prime
        )

        self.damping = float(
            damping
        )

        self.frequency = float(
            frequency
        )

        self.initial_delta = float(
            initial_delta
        )

        self.initial_omega = float(
            initial_omega
        )

    # ------------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------------

    @property
    def metadata(
        self,
    ) -> DynamicModelMetadata:

        return DynamicModelMetadata(
            model_type="synchronous_machine",
            model_name="ClassicalSynchronousMachine",
            model_version="1.0",
            description=(
                "Classical transient-stability "
                "synchronous-machine model."
            ),
        )

    # ------------------------------------------------------------------
    # STATE DEFINITION
    # ------------------------------------------------------------------

    def state_definitions(
        self,
    ) -> Sequence[StateDefinition]:

        return (
            StateDefinition(
                name="delta",
                initial_value=self.initial_delta,
                description="Rotor electrical angle",
                units="rad",
            ),
            StateDefinition(
                name="omega",
                initial_value=self.initial_omega,
                description="Rotor speed deviation",
                units="pu",
            ),
        )

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------

    def initialize(
        self,
        terminal_voltage: complex,
        electrical_power: float,
        mechanical_power: float,
    ) -> dict[str, float]:

        del mechanical_power

        Vt = complex(
            terminal_voltage
        )

        if abs(Vt) <= 0.0:
            raise ValueError(
                "Cannot initialize machine "
                "from zero terminal voltage."
            )

        # For the classical model, determine the rotor angle from
        # the internal emf relation when possible.
        #
        # The initial state remains deterministic even if the supplied
        # operating point does not permit an exact reconstruction.
        #
        # E = V + jXd'I
        #
        # If no current is available at this layer, retain the
        # configured initial rotor angle.
        del electrical_power

        return {
            "delta": self.initial_delta,
            "omega": self.initial_omega,
        }

    # ------------------------------------------------------------------
    # DIFFERENTIAL EQUATIONS
    # ------------------------------------------------------------------

    def derivatives(
        self,
        state: Mapping[str, float],
        inputs: MachineInputs,
        time: float,
    ) -> Mapping[str, float]:

        del time

        self.validate_state(
            state
        )

        omega = float(
            state["omega"]
        )

        Pe = float(
            inputs.electrical_power
        )

        Pm = float(
            inputs.mechanical_power
        )

        omega_base = (
            2.0
            * np.pi
            * self.frequency
        )

        ddelta_dt = (
            omega_base
            * omega
        )

        domega_dt = (
            Pm
            - Pe
            - self.damping * omega
        ) / (
            2.0 * self.H
        )

        derivatives = {
            "delta": ddelta_dt,
            "omega": domega_dt,
        }

        self.validate_derivatives(
            derivatives
        )

        return derivatives

    # ------------------------------------------------------------------
    # ELECTRICAL OUTPUT
    # ------------------------------------------------------------------

    def electrical_output(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> ElectricalOutput:

        self.validate_state(
            state
        )

        delta = float(
            state["delta"]
        )

        Vt = complex(
            terminal_voltage
        )

        internal_voltage = (
            self.E_prime
            * np.exp(
                1j * delta
            )
        )

        denominator = (
            1j
            * self.Xd_prime
        )

        current = (
            internal_voltage
            - Vt
        ) / denominator

        S = (
            Vt
            * np.conj(current)
        )

        return ElectricalOutput(
            current=current,
            active_power=float(
                S.real
            ),
            reactive_power=float(
                S.imag
            ),
        )


# ======================================================================
# PUBLIC EXPORTS
# ======================================================================


__all__ = [
    "MachineInputs",
    "ElectricalOutput",
    "StateDefinition",
    "DynamicModelMetadata",
    "DynamicMachineModel",
    "ClassicalSynchronousMachine",
]
```
