"""
GridForge Dynamic Machine Models
================================

Dynamic-machine model interfaces and classical synchronous-machine
equations for GridForge time-domain simulation.

Responsibilities
----------------
- Define the contract for dynamic machine models.
- Define machine-specific dynamic state registration.
- Provide terminal/electrical inputs to machine models.
- Provide differential equations for registered states.
- Provide machine electrical outputs required by the network solver.

The module is deliberately separated from the persistent GridForge
equipment model.

A GridForge generator in ``core/model`` represents the engineering /
Digital-Twin entity.

A dynamic machine model represents the mathematical time-domain model
used during a simulation.

This module does NOT:
- own the global simulation state
- perform numerical integration
- solve the network
- implement AVR/GOV/PSS controllers
- implement protection
- modify persistent network state
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .state_vector import StateLayout


class DynamicModelError(RuntimeError):
    """Raised when a dynamic-machine model cannot be evaluated."""


@dataclass(frozen=True)
class MachineInputs:
    """
    Algebraic/electrical inputs supplied to a dynamic machine model.

    Parameters
    ----------
    terminal_voltage:
        Complex terminal voltage in per-unit.

    electrical_power:
        Electrical active power output in per-unit.

    mechanical_power:
        Mechanical input power in per-unit.

    terminal_current:
        Optional complex terminal current in per-unit.

    electrical_reactive_power:
        Optional reactive power output in per-unit.
    """

    terminal_voltage: complex
    electrical_power: float
    mechanical_power: float
    terminal_current: complex | None = None
    electrical_reactive_power: float | None = None

    def __post_init__(self) -> None:
        if not np.isfinite(
            self.terminal_voltage.real
        ) or not np.isfinite(
            self.terminal_voltage.imag
        ):
            raise ValueError(
                "Terminal voltage must be finite."
            )

        if not np.isfinite(
            self.electrical_power
        ):
            raise ValueError(
                "Electrical power must be finite."
            )

        if not np.isfinite(
            self.mechanical_power
        ):
            raise ValueError(
                "Mechanical power must be finite."
            )

        if self.terminal_current is not None:
            if not np.isfinite(
                self.terminal_current.real
            ) or not np.isfinite(
                self.terminal_current.imag
            ):
                raise ValueError(
                    "Terminal current must be finite."
                )

        if self.electrical_reactive_power is not None:
            if not np.isfinite(
                self.electrical_reactive_power
            ):
                raise ValueError(
                    "Reactive power must be finite."
                )


class DynamicMachineModel(ABC):
    """
    Abstract interface for synchronous-machine dynamic models.

    A dynamic model is stateless with respect to the global simulation
    trajectory. Its state is held by ``DynamicStateVector``.

    Subclasses define:
        - required dynamic states
        - initialization
        - differential equations
        - electrical outputs
    """

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
    ) -> None:

        if not machine_id:
            raise ValueError(
                "machine_id must not be empty."
            )

        if not bus_id:
            raise ValueError(
                "bus_id must not be empty."
            )

        self.machine_id = machine_id
        self.bus_id = bus_id

    # =========================================================
    # STATE REGISTRATION
    # =========================================================

    @abstractmethod
    def register_states(
        self,
        layout: StateLayout,
    ) -> None:
        """
        Register all differential states required by the model.
        """
        raise NotImplementedError

    # =========================================================
    # INITIALIZATION
    # =========================================================

    @abstractmethod
    def initialize(
        self,
        inputs: MachineInputs,
        state: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the model's initial state.

        Parameters
        ----------
        inputs:
            Initial algebraic/electrical operating point.

        state:
            Model-specific state vector.

        Returns
        -------
        numpy.ndarray
            Initialized model state.
        """
        raise NotImplementedError

    # =========================================================
    # DIFFERENTIAL EQUATIONS
    # =========================================================

    @abstractmethod
    def derivatives(
        self,
        state: np.ndarray,
        inputs: MachineInputs,
        time: float,
    ) -> np.ndarray:
        """
        Evaluate differential equations.

        Returns
        -------
        numpy.ndarray
            ``dx/dt`` for this model's states.
        """
        raise NotImplementedError

    # =========================================================
    # ELECTRICAL OUTPUT
    # =========================================================

    @abstractmethod
    def electrical_output(
        self,
        state: np.ndarray,
        inputs: MachineInputs,
    ) -> complex:
        """
        Return the machine's complex current injection/output.

        The result is in per-unit.
        """
        raise NotImplementedError

    # =========================================================
    # METADATA
    # =========================================================

    @property
    @abstractmethod
    def model_type(self) -> str:
        """Return the dynamic model identifier."""
        raise NotImplementedError


@dataclass(frozen=True)
class ClassicalMachineParameters:
    """
    Parameters for the classical synchronous-machine model.

    The classical model represents the machine by a constant internal
    voltage behind transient/subtransient reactance for the purpose of
    electromechanical transient-stability studies.

    Parameters
    ----------
    H:
        Inertia constant [s].

    D:
        Damping coefficient [pu power / pu speed deviation].

    Xd_prime:
        d-axis transient reactance [pu].

    omega_s:
        Synchronous electrical angular frequency [rad/s].

    internal_voltage:
        Constant internal voltage magnitude [pu].
    """

    H: float
    D: float = 0.0
    Xd_prime: float = 0.3
    omega_s: float = 2.0 * np.pi * 50.0
    internal_voltage: float = 1.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.H) or self.H <= 0.0:
            raise ValueError(
                "H must be finite and greater than zero."
            )

        if not np.isfinite(self.D) or self.D < 0.0:
            raise ValueError(
                "D must be finite and non-negative."
            )

        if (
            not np.isfinite(self.Xd_prime)
            or self.Xd_prime <= 0.0
        ):
            raise ValueError(
                "Xd_prime must be finite and greater than zero."
            )

        if (
            not np.isfinite(self.omega_s)
            or self.omega_s <= 0.0
        ):
            raise ValueError(
                "omega_s must be finite and greater than zero."
            )

        if (
            not np.isfinite(self.internal_voltage)
            or self.internal_voltage <= 0.0
        ):
            raise ValueError(
                "internal_voltage must be finite and greater than zero."
            )


class ClassicalMachineModel(DynamicMachineModel):
    """
    Classical second-order synchronous-machine model.

    Differential states
    -------------------
        delta
            Rotor electrical angle [rad].

        omega
            Rotor-speed deviation [pu].

    Equations
    ---------
        d(delta)/dt = omega_s * omega

        d(omega)/dt =
            (Pm - Pe - D*omega) / (2H)

    Electrical representation
    --------------------------
    The internal emf is represented as:

        E = E_internal * exp(j*delta)

    and the current injection is:

        I = (E - V) / (j*Xd')

    This is a classical transient-stability representation.

    The model does not integrate its own states. The global dynamic
    solver owns the state vector and numerical integration.
    """

    DELTA_STATE = "delta"
    OMEGA_STATE = "omega"

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
        parameters: ClassicalMachineParameters,
    ) -> None:

        super().__init__(
            machine_id=machine_id,
            bus_id=bus_id,
        )

        self.parameters = parameters

    @property
    def model_type(self) -> str:
        return "classical"

    # =========================================================
    # STATE REGISTRATION
    # =========================================================

    def register_states(
        self,
        layout: StateLayout,
    ) -> None:

        layout.add_state(
            name=self.state_name(
                self.DELTA_STATE
            ),
            initial_value=0.0,
            model_id=self.machine_id,
        )

        layout.add_state(
            name=self.state_name(
                self.OMEGA_STATE
            ),
            initial_value=0.0,
            model_id=self.machine_id,
        )

    def state_name(
        self,
        name: str,
    ) -> str:
        """
        Return the globally unique state name for this machine.
        """

        return (
            f"{self.machine_id}.{name}"
        )

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def initialize(
        self,
        inputs: MachineInputs,
        state: np.ndarray,
    ) -> np.ndarray:

        state = self._validate_state(
            state
        )

        Vt = inputs.terminal_voltage

        if abs(Vt) <= 0.0:
            raise DynamicModelError(
                "Cannot initialize classical machine "
                "with zero terminal voltage."
            )

        # Initial electrical power-angle relation.
        #
        # For the classical model:
        #
        #     Pe ≈ E*V/X * sin(delta)
        #
        # Use the operating-point active power to estimate the
        # initial rotor angle.
        #
        # Clamp the argument to avoid invalid arcsin values caused
        # by numerical round-off or an incompatible initial point.

        magnitude = (
            self.parameters.internal_voltage
            * abs(Vt)
            / self.parameters.Xd_prime
        )

        if magnitude <= 0.0:
            raise DynamicModelError(
                "Invalid classical-machine "
                "initialization magnitude."
            )

        ratio = (
            inputs.electrical_power
            / magnitude
        )

        ratio = float(
            np.clip(
                ratio,
                -1.0,
                1.0,
            )
        )

        terminal_angle = np.angle(
            Vt
        )

        delta = (
            terminal_angle
            + np.arcsin(ratio)
        )

        state[0] = delta
        state[1] = 0.0

        return state

    # =========================================================
    # DIFFERENTIAL EQUATIONS
    # =========================================================

    def derivatives(
        self,
        state: np.ndarray,
        inputs: MachineInputs,
        time: float,
    ) -> np.ndarray:

        del time

        state = self._validate_state(
            state
        )

        delta = state[0]
        omega = state[1]

        d_delta = (
            self.parameters.omega_s
            * omega
        )

        d_omega = (
            inputs.mechanical_power
            - inputs.electrical_power
            - self.parameters.D * omega
        ) / (
            2.0 * self.parameters.H
        )

        return np.asarray(
            [
                d_delta,
                d_omega,
            ],
            dtype=float,
        )

    # =========================================================
    # ELECTRICAL OUTPUT
    # =========================================================

    def electrical_output(
        self,
        state: np.ndarray,
        inputs: MachineInputs,
    ) -> complex:

        state = self._validate_state(
            state
        )

        delta = state[0]

        internal_voltage = (
            self.parameters.internal_voltage
            * np.exp(1j * delta)
        )

        terminal_voltage = (
            inputs.terminal_voltage
        )

        impedance = (
            1j
            * self.parameters.Xd_prime
        )

        return (
            internal_voltage
            - terminal_voltage
        ) / impedance

    # =========================================================
    # STATE VALIDATION
    # =========================================================

    @staticmethod
    def _validate_state(
        state: np.ndarray,
    ) -> np.ndarray:

        state = np.asarray(
            state,
            dtype=float,
        )

        if state.ndim != 1:
            raise DynamicModelError(
                "Machine state must be one-dimensional."
            )

        if state.size != 2:
            raise DynamicModelError(
                "Classical machine requires "
                "exactly two states: delta and omega."
            )

        if not np.all(
            np.isfinite(state)
        ):
            raise DynamicModelError(
                "Machine state contains "
                "non-finite values."
            )

        return state


class MachineModelCollection:
    """
    Collection of dynamic machine models.

    This class performs model registration and state-layout assembly.

    It does not perform numerical integration or network solution.
    """

    def __init__(
        self,
        models: list[
            DynamicMachineModel
        ] | None = None,
    ) -> None:

        self._models: list[
            DynamicMachineModel
        ] = []

        self._ids: set[str] = set()

        if models is not None:
            for model in models:
                self.add(model)

    def add(
        self,
        model: DynamicMachineModel,
    ) -> None:
        """Register a dynamic machine model."""

        if model.machine_id in self._ids:
            raise ValueError(
                "Duplicate dynamic machine ID: "
                f"'{model.machine_id}'."
            )

        self._models.append(
            model
        )

        self._ids.add(
            model.machine_id
        )

    @property
    def models(
        self,
    ) -> tuple[
        DynamicMachineModel, ...
    ]:
        """Return registered machine models."""
        return tuple(
            self._models
        )

    def register_states(
        self,
        layout: StateLayout,
    ) -> None:
        """Register states for all machine models."""

        for model in self._models:
            model.register_states(
                layout
            )

    def get(
        self,
        machine_id: str,
    ) -> DynamicMachineModel:
        """Return a model by machine ID."""

        for model in self._models:
            if model.machine_id == machine_id:
                return model

        raise KeyError(
            f"Unknown dynamic machine: "
            f"'{machine_id}'."
        )

    def __len__(self) -> int:
        return len(
            self._models
        )
