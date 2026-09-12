# ============================================================
# File: core/analysis/dynamic_initial_state.py
# GridForge V2 — Power Flow to Dynamics Initial State
# Author: Subhendu Mishra
# ============================================================
"""Canonical immutable Power Flow -> Dynamics initialization boundary."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math

from core.solver.dynamics.machine_models import ClassicalMachineParameters
from core.solver.power_flow.input import PowerFlowInput
from core.solver.power_flow.result import PowerFlowResult


@dataclass(frozen=True, slots=True)
class DynamicMachineModelDefinition:
    """Immutable dynamic model definition associated with one machine identity."""

    machine_id: str
    bus_id: str
    parameters: ClassicalMachineParameters
    mechanical_power: float

    def __post_init__(self) -> None:
        if not isinstance(self.machine_id, str) or not self.machine_id.strip():
            raise ValueError("machine_id must be a non-empty string.")
        if not isinstance(self.bus_id, str) or not self.bus_id.strip():
            raise ValueError("bus_id must be a non-empty string.")
        if not isinstance(self.parameters, ClassicalMachineParameters):
            raise TypeError("parameters must be ClassicalMachineParameters.")
        value = float(self.mechanical_power)
        if not math.isfinite(value):
            raise ValueError("mechanical_power must be finite.")
        object.__setattr__(self, "machine_id", self.machine_id.strip())
        object.__setattr__(self, "bus_id", self.bus_id.strip())
        object.__setattr__(self, "mechanical_power", value)


@dataclass(frozen=True, slots=True)
class DynamicInitialState:
    """Immutable dynamic operating point derived from a solved Power Flow."""

    machine_id: str
    bus_id: str
    terminal_voltage: complex
    electrical_power: complex
    mechanical_power: float
    rotor_angle: float
    speed_deviation: float
    internal_emf: complex
    state_vector: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.state_vector) != 2:
            raise ValueError("Classical dynamic state vector must contain [delta, omega].")
        if not all(math.isfinite(float(value)) for value in self.state_vector):
            raise ValueError("Dynamic state vector must contain finite values.")
        numeric_values = (
            self.terminal_voltage.real,
            self.terminal_voltage.imag,
            self.electrical_power.real,
            self.electrical_power.imag,
            self.internal_emf.real,
            self.internal_emf.imag,
            self.mechanical_power,
            self.rotor_angle,
            self.speed_deviation,
        )
        if not all(math.isfinite(float(value)) for value in numeric_values):
            raise ValueError("Dynamic initial state contains non-finite values.")
        object.__setattr__(self, "state_vector", tuple(float(value) for value in self.state_vector))


class DynamicInitialStatePreparation:
    """Prepare detached dynamic initial states from immutable study inputs."""

    @staticmethod
    def prepare(
        power_flow_result: PowerFlowResult,
        power_flow_input: PowerFlowInput,
        machine: DynamicMachineModelDefinition,
    ) -> DynamicInitialState:
        if not isinstance(power_flow_result, PowerFlowResult):
            raise TypeError("power_flow_result must be PowerFlowResult.")
        if not isinstance(power_flow_input, PowerFlowInput):
            raise TypeError("power_flow_input must be PowerFlowInput.")
        if not isinstance(machine, DynamicMachineModelDefinition):
            raise TypeError("machine must be DynamicMachineModelDefinition.")
        if not power_flow_result.success:
            raise ValueError("Power Flow must be successfully solved before Dynamics initialization.")
        if len(power_flow_result.voltage_magnitudes) != len(power_flow_input.bus_ids):
            raise ValueError("Power Flow result and input bus dimensions do not match.")
        try:
            bus_index = power_flow_input.bus_ids.index(machine.bus_id)
        except ValueError as exc:
            raise ValueError(
                f"Dynamic machine bus '{machine.bus_id}' is absent from the Power Flow input."
            ) from exc

        magnitude = float(power_flow_result.voltage_magnitudes[bus_index])
        angle = float(power_flow_result.voltage_angles[bus_index])
        terminal_voltage = cmath.rect(magnitude, angle)
        electrical_power = complex(machine.mechanical_power, 0.0)

        params = machine.parameters
        current = (
            electrical_power.conjugate() / terminal_voltage
            if abs(terminal_voltage) > 1e-12
            else 0.0j
        )
        internal_emf = terminal_voltage + 1j * params.Xd_prime * current
        rotor_angle = (
            float(cmath.phase(internal_emf))
            if abs(internal_emf) > 1e-12
            else params.initial_delta
        )
        speed_deviation = float(params.initial_omega)

        return DynamicInitialState(
            machine_id=machine.machine_id,
            bus_id=machine.bus_id,
            terminal_voltage=terminal_voltage,
            electrical_power=electrical_power,
            mechanical_power=machine.mechanical_power,
            rotor_angle=rotor_angle,
            speed_deviation=speed_deviation,
            internal_emf=internal_emf,
            state_vector=(rotor_angle, speed_deviation),
        )


__all__ = [
    "DynamicMachineModelDefinition",
    "DynamicInitialState",
    "DynamicInitialStatePreparation",
]
