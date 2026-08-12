```python
"""
GridForge Dynamic Machine Models
================================

Dynamic machine-model interfaces and classical synchronous-machine
implementation used by the GridForge transient-stability solver.

Architectural role
------------------
This module defines the machine-side dynamic equations used by the
DAE solver.

A machine model contains:

- machine identity;
- network terminal identity;
- physical parameters;
- differential-equation evaluation;
- electrical current injection calculation;
- electrical-power calculation;
- mapping between machine physics and the global dynamic state.

The numerical state itself is owned by ``DynamicStateVector`` /
``MultiMachineSystem`` and is not stored as the authoritative state
inside the machine model.

Control systems
---------------
AVR, governor, PSS, turbine and other control systems are separate
dynamic components.

This module deliberately does NOT implement a governor because the
legacy GridForge ``governor.py`` implementation has been removed.

The machine model may accept control inputs supplied by an external
controller/domain implementation.

Network responsibility
----------------------
This module does not construct Y-bus, solve the network, or modify
topology.

The network solver consumes the current injections produced here and
returns bus voltages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


# ======================================================================
# ERRORS
# ======================================================================


class MachineModelError(RuntimeError):
    """Raised when a dynamic machine model is invalid."""


# ======================================================================
# PARAMETERS
# ======================================================================


@dataclass(frozen=True)
class ClassicalMachineParameters:
    """
    Parameters for a classical synchronous-machine representation.

    Parameters
    ----------
    H:
        Inertia constant [s].

    D:
        Damping coefficient.

    Xd:
        Direct-axis transient/steady reactance used by the selected
        classical representation.

    base_mva:
        Machine MVA base.

    Notes
    -----
    The exact electrical representation is intentionally explicit.
    More detailed subtransient models can be implemented as separate
    machine-model classes without changing the DAE architecture.
    """

    H: float

    D: float = 0.0

    Xd: float = 1.8

    base_mva: float = 100.0

    def __post_init__(
        self,
    ) -> None:

        if self.H <= 0.0:
            raise ValueError(
                "H must be greater than zero."
            )

        if self.Xd <= 0.0:
            raise ValueError(
                "Xd must be greater than zero."
            )

        if self.base_mva <= 0.0:
            raise ValueError(
                "base_mva must be greater "
                "than zero."
            )


# ======================================================================
# MACHINE INPUTS
# ======================================================================


@dataclass(frozen=True)
class MachineDynamicInputs:
    """
    External inputs supplied to a dynamic machine model.

    Parameters
    ----------
    mechanical_power:
        Mechanical input power Pm [pu].

    excitation:
        Excitation/internal EMF input.

    control_signal:
        Optional aggregate stabilizing/control signal.

    additional:
        Extension point for detailed machine/controller models.
    """

    mechanical_power: float = 1.0

    excitation: float = 1.0

    control_signal: float = 0.0

    additional: Mapping[
        str,
        float,
    ] | None = None


# ======================================================================
# MACHINE ELECTRICAL OUTPUT
# ======================================================================


@dataclass(frozen=True)
class MachineElectricalOutput:
    """
    Electrical output of a dynamic machine.

    Parameters
    ----------
    active_power:
        Electrical active power Pe [pu].

    reactive_power:
        Electrical reactive power Qe [pu].

    current:
        Complex terminal current [pu].

    internal_emf:
        Complex internal EMF [pu].
    """

    active_power: float

    reactive_power: float

    current: complex

    internal_emf: complex


# ======================================================================
# MACHINE DERIVATIVES
# ======================================================================


@dataclass(frozen=True)
class MachineDerivative:
    """
    Differential-equation output for one machine.

    The state ordering is defined by the machine/system state-vector
    implementation rather than by this object.
    """

    delta: float

    omega: float

    Efd: float = 0.0

    Pm: float = 0.0

    pss: float = 0.0


# ======================================================================
# BASE MACHINE MODEL
# ======================================================================


class DynamicMachineModel(ABC):
    """
    Abstract interface for a dynamic machine model.

    Concrete implementations provide machine equations without owning
    the global simulation state.
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

    # ==================================================================
    # STATE DEFINITION
    # ==================================================================

    @property
    @abstractmethod
    def state_names(
        self,
    ) -> tuple[str, ...]:
        """
        Names of dynamic states owned by this machine.
        """
        ...

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    @abstractmethod
    def initial_state(
        self,
        terminal_voltage: complex,
        electrical_power: float,
        mechanical_power: float,
    ) -> Mapping[
        str,
        float,
    ]:
        """
        Calculate the machine's initial dynamic state.
        """
        ...

    # ==================================================================
    # ELECTRICAL MODEL
    # ==================================================================

    @abstractmethod
    def current_injection(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> complex:
        """
        Calculate complex current injection into the network.
        """
        ...

    @abstractmethod
    def electrical_output(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> MachineElectricalOutput:
        """
        Calculate machine electrical output.
        """
        ...

    # ==================================================================
    # DYNAMIC EQUATIONS
    # ==================================================================

    @abstractmethod
    def derivatives(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
        electrical_output: MachineElectricalOutput,
        inputs: MachineDynamicInputs,
        time: float,
    ) -> MachineDerivative:
        """
        Evaluate machine differential equations.
        """
        ...

    # ==================================================================
    # INPUT CONSTRUCTION
    # ==================================================================

    def build_inputs(
        self,
        *,
        terminal_voltage: complex,
        electrical_output: MachineElectricalOutput,
        time: float,
    ) -> MachineDynamicInputs:
        """
        Build default dynamic inputs.

        Detailed controller-enabled machine implementations can override
        this method or receive controller outputs through a higher-level
        control system.
        """

        return MachineDynamicInputs(
            mechanical_power=(
                electrical_output.active_power
            ),
            excitation=1.0,
            control_signal=0.0,
        )


# ======================================================================
# CLASSICAL SYNCHRONOUS MACHINE
# ======================================================================


class ClassicalSynchronousMachine(
    DynamicMachineModel
):
    """
    Classical synchronous-machine model.

    Differential equations
    ----------------------

        dδ/dt = ω

        dω/dt =
            (Pm - Pe - Dω) / (2H)

    Electrical representation
    -------------------------

        E = Efd ∠δ

        I = (E - V) / jXd

    where:

        Efd
            internal EMF magnitude;

        δ
            rotor angle;

        V
            terminal voltage;

        Xd
            direct-axis reactance.

    Notes
    -----
    ``omega`` is represented as speed deviation from synchronous speed
    in the dynamic state.

    This is a transient-stability model, not a detailed electromagnetic
    transient machine model.
    """

    def __init__(
        self,
        machine_id: str,
        bus_id: str,
        parameters:
            ClassicalMachineParameters,
        *,
        initial_Efd: float = 1.0,
    ) -> None:

        super().__init__(
            machine_id=machine_id,
            bus_id=bus_id,
        )

        if initial_Efd <= 0.0:
            raise ValueError(
                "initial_Efd must be "
                "greater than zero."
            )

        self.parameters = parameters

        self.initial_Efd = float(
            initial_Efd
        )

    # ==================================================================
    # STATE
    # ==================================================================

    @property
    def state_names(
        self,
    ) -> tuple[str, ...]:

        return (
            "delta",
            "omega",
            "Efd",
            "Pm",
        )

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def initial_state(
        self,
        terminal_voltage: complex,
        electrical_power: float,
        mechanical_power: float,
    ) -> Mapping[
        str,
        float,
    ]:
        """
        Estimate a consistent classical-machine initial state.
        """

        if abs(
            terminal_voltage
        ) <= 0.0:

            raise MachineModelError(
                "Terminal voltage cannot "
                "be zero during machine "
                "initialization."
            )

        # Approximate rotor angle from terminal-voltage reference.
        delta = float(
            np.angle(
                terminal_voltage
            )
        )

        return {
            "delta": delta,
            "omega": 0.0,
            "Efd": self.initial_Efd,
            "Pm": float(
                mechanical_power
            ),
        }

    # ==================================================================
    # INTERNAL EMF
    # ==================================================================

    @staticmethod
    def internal_emf(
        state: Mapping[str, float],
    ) -> complex:
        """
        Return internal EMF Efd ∠delta.
        """

        return (
            float(state["Efd"])
            * np.exp(
                1j
                * float(
                    state["delta"]
                )
            )
        )

    # ==================================================================
    # CURRENT
    # ==================================================================

    def current_injection(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> complex:
        """
        Calculate generator current injection.

        Sign convention
        ----------------
        Positive current is injected from the machine into the
        electrical network.
        """

        E = self.internal_emf(
            state
        )

        Xd = (
            self.parameters.Xd
        )

        return (
            E - terminal_voltage
        ) / (
            1j * Xd
        )

    # ==================================================================
    # ELECTRICAL OUTPUT
    # ==================================================================

    def electrical_output(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
    ) -> MachineElectricalOutput:
        """
        Calculate terminal electrical power and current.
        """

        current = (
            self.current_injection(
                state,
                terminal_voltage,
            )
        )

        apparent_power = (
            terminal_voltage
            * np.conj(current)
        )

        E = self.internal_emf(
            state
        )

        return MachineElectricalOutput(
            active_power=float(
                apparent_power.real
            ),
            reactive_power=float(
                apparent_power.imag
            ),
            current=current,
            internal_emf=E,
        )

    # ==================================================================
    # DERIVATIVES
    # ==================================================================

    def derivatives(
        self,
        state: Mapping[str, float],
        terminal_voltage: complex,
        electrical_output:
            MachineElectricalOutput,
        inputs: MachineDynamicInputs,
        time: float,
    ) -> MachineDerivative:
        """
        Evaluate the classical swing-equation dynamics.

        The control-system dynamics for excitation and mechanical power
        are not invented here. They are supplied through ``inputs`` or
        implemented by separate control-domain components.
        """

        del terminal_voltage
        del time

        H = (
            self.parameters.H
        )

        D = (
            self.parameters.D
        )

        if H <= 0.0:
            raise MachineModelError(
                "Machine inertia H must "
                "be positive."
            )

        delta = float(
            state["delta"]
        )

        omega = float(
            state["omega"]
        )

        Pm = float(
            inputs.mechanical_power
        )

        Pe = float(
            electrical_output.active_power
        )

        ddelta = omega

        domega = (
            Pm
            - Pe
            - D * omega
        ) / (
            2.0 * H
        )

        return MachineDerivative(
            delta=ddelta,
            omega=domega,
            Efd=float(
                inputs.excitation
            ),
            Pm=0.0,
            pss=float(
                inputs.control_signal
            ),
        )


# ======================================================================
# PUBLIC EXPORTS
# ======================================================================


__all__ = [
    "MachineModelError",
    "ClassicalMachineParameters",
    "MachineDynamicInputs",
    "MachineElectricalOutput",
    "MachineDerivative",
    "DynamicMachineModel",
    "ClassicalSynchronousMachine",
]
```
