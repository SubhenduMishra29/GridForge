"""Opt-in augmented-state integrator adapter for generator dynamics.

This adapter composes the existing Core MultiMachineSystem and Integrator
with the generator plugin's stage evaluator. It does not modify DAESolver's
legacy machine-only API or create another machine/solver authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import numpy as np

from core.solver.dynamics.component_assembly import DynamicComponentBinding
from core.solver.dynamics.component_contract import DynamicComponentInputs, DynamicStateComponent
from core.solver.dynamics.dynamic_state_layout import DynamicSystemStateLayout
from core.solver.dynamics.integrator import Integrator
from core.solver.dynamics.multimachine import MultiMachineSystem

from .avr_component import FirstOrderAVRStateComponent
from .network_stage import GeneratorNetworkSolver
from .stage_evaluation import (
    GeneratorDynamicStageResult,
    TerminalVoltageProjector,
    evaluate_generator_dynamic_stage,
)


class GeneratorAugmentedIntegratorError(ValueError):
    """Raised when the augmented generator integration boundary is invalid."""


MachineConnectionResolver = Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class GeneratorAugmentedStepResult:
    """Accepted augmented state and its final-time algebraic/derivative sample."""

    state: np.ndarray
    simulation_time_s: float
    final_stage: GeneratorDynamicStageResult

    def __post_init__(self) -> None:
        state = np.asarray(self.state, dtype=float).copy()
        if state.ndim != 1 or state.size == 0 or not np.all(np.isfinite(state)):
            raise GeneratorAugmentedIntegratorError("accepted state must be a finite non-empty vector")
        if not np.isfinite(float(self.simulation_time_s)):
            raise GeneratorAugmentedIntegratorError("accepted simulation time must be finite")
        if self.final_stage.component_inputs.simulation_time_s != float(self.simulation_time_s):
            raise GeneratorAugmentedIntegratorError("final stage time must match accepted simulation time")
        state.setflags(write=False)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "simulation_time_s", float(self.simulation_time_s))


class GeneratorAugmentedDAEAdapter:
    """Run augmented machine-plus-extension state through Core's Integrator.

    The caller constructs the global initial vector with
    DynamicSystemStateLayout.pack(). At every derivative callback (including
    RK4 intermediate states and trapezoidal Newton evaluations), this adapter
    performs a fresh AVR snapshot, network solve, terminal/electrical projection
    and composed derivative evaluation. It reuses the registered
    MultiMachineSystem and Integrator; DAESolver remains unchanged.
    """

    def __init__(
        self,
        *,
        machine_system: MultiMachineSystem,
        integrator: Integrator,
        layout: DynamicSystemStateLayout,
        components: Sequence[DynamicStateComponent],
        component_bindings: Sequence[DynamicComponentBinding],
        avr_components: Sequence[FirstOrderAVRStateComponent],
        network_solver: GeneratorNetworkSolver,
        terminal_voltage_projector: TerminalVoltageProjector,
        base_mechanical_powers_pu: Mapping[str, float],
        machine_connection_state: MachineConnectionResolver | None = None,
    ) -> None:
        if not isinstance(machine_system, MultiMachineSystem):
            raise TypeError("machine_system must be the canonical MultiMachineSystem")
        if not isinstance(integrator, Integrator):
            raise TypeError("integrator must be the canonical Core Integrator")
        if not isinstance(layout, DynamicSystemStateLayout):
            raise TypeError("layout must be DynamicSystemStateLayout")
        if not callable(network_solver) or not callable(terminal_voltage_projector):
            raise TypeError("network solver and terminal voltage projector must be callable")
        if machine_connection_state is not None and not callable(machine_connection_state):
            raise TypeError("machine_connection_state must be callable when supplied")

        canonical_slices = tuple(
            (item.machine_id, item.start, item.stop)
            for item in machine_system.state_layout
        )
        composed_slices = tuple(
            (item.owner_id, item.start, item.stop)
            for item in layout.machine_blocks
        )
        if layout.machine_state_size != machine_system.state_size or composed_slices != canonical_slices:
            raise GeneratorAugmentedIntegratorError(
                "composed machine prefix must exactly preserve MultiMachineSystem state ownership and offsets"
            )
        machine_ids = {machine.machine_id for machine in machine_system.machines}
        if set(base_mechanical_powers_pu) != machine_ids:
            raise GeneratorAugmentedIntegratorError(
                "base mechanical-power inputs must match the canonical machine set exactly"
            )
        self.machine_system = machine_system
        self.integrator = integrator
        self.layout = layout
        self.components = tuple(components)
        self.component_bindings = tuple(component_bindings)
        self.avr_components = tuple(avr_components)
        self.network_solver = network_solver
        self.terminal_voltage_projector = terminal_voltage_projector
        self.machine_bus_ids = {machine.machine_id: machine.bus_id for machine in machine_system.machines}
        self.base_mechanical_powers_pu = dict(base_mechanical_powers_pu)
        self.machine_connection_state = machine_connection_state

    def initialize_state(
        self,
        machine_state: Sequence[float] | np.ndarray,
        operating_point_inputs: DynamicComponentInputs,
    ) -> np.ndarray:
        """Build the augmented initial vector from a host-validated operating point.

        The host must first solve/validate the initial algebraic network state
        and supply terminal voltages and machine powers on the study base.
        Every registered continuous component contributes its own initial
        state; no controller state is guessed from nameplate defaults.
        """
        if not isinstance(operating_point_inputs, DynamicComponentInputs):
            raise TypeError("operating_point_inputs must be DynamicComponentInputs")
        machine = np.asarray(machine_state, dtype=float)
        if machine.ndim != 1 or machine.size != self.machine_system.state_size or not np.all(np.isfinite(machine)):
            raise GeneratorAugmentedIntegratorError(
                "machine_state must match the canonical finite machine state vector"
            )
        if dict(operating_point_inputs.mechanical_power_inputs_pu) != self.base_mechanical_powers_pu:
            raise GeneratorAugmentedIntegratorError(
                "operating-point mechanical powers must match the configured study inputs exactly"
            )
        if set(operating_point_inputs.electrical_active_power_pu) != set(self.machine_bus_ids):
            raise GeneratorAugmentedIntegratorError(
                "operating-point electrical powers must cover the canonical machine set exactly"
            )
        component_ids = {getattr(component, "component_id", None) for component in self.components}
        if component_ids != {block.owner_id for block in self.layout.component_blocks}:
            raise GeneratorAugmentedIntegratorError(
                "registered component identities must match the composed layout exactly"
            )
        states: dict[str, Sequence[float]] = {}
        for component in self.components:
            component_id = component.component_id
            try:
                initial = component.initial_state(operating_point_inputs)
            except Exception as exc:
                raise GeneratorAugmentedIntegratorError(
                    f"component {component_id!r} could not initialize from the supplied operating point"
                ) from exc
            states[component_id] = initial
        try:
            return self.layout.pack(machine, states)
        except Exception as exc:
            raise GeneratorAugmentedIntegratorError(
                "operating-point component states do not satisfy the composed layout"
            ) from exc

    def evaluate_stage(
        self,
        global_state: Sequence[float] | np.ndarray,
        simulation_time_s: float,
    ) -> GeneratorDynamicStageResult:
        """Evaluate the complete composed system at one integrator stage."""
        connection_states = None
        if self.machine_connection_state is not None:
            connection_states = {
                machine.machine_id: self.machine_connection_state(machine.machine_id)
                for machine in self.machine_system.machines
            }
            if any(type(value) is not bool for value in connection_states.values()):
                raise GeneratorAugmentedIntegratorError(
                    "machine connection resolver must return explicit bool values"
                )

        def electrical_power_evaluator(state, bus_voltages, field_voltages):
            return self.machine_system.electrical_powers(
                state,
                bus_voltages,
                field_voltages=field_voltages,
            )

        def machine_derivative_evaluator(
            *,
            state,
            terminal_voltages,
            mechanical_powers,
            machine_connection_states,
            time,
            field_voltages,
        ):
            return self.machine_system.derivatives(
                state=state,
                terminal_voltages=terminal_voltages,
                mechanical_powers=mechanical_powers,
                machine_connection_states=machine_connection_states,
                field_voltages=field_voltages,
                time=time,
            )

        try:
            return evaluate_generator_dynamic_stage(
                global_state=global_state,
                simulation_time_s=simulation_time_s,
                layout=self.layout,
                components=self.components,
                component_bindings=self.component_bindings,
                avr_components=self.avr_components,
                network_solver=self.network_solver,
                terminal_voltage_projector=self.terminal_voltage_projector,
                electrical_power_evaluator=electrical_power_evaluator,
                machine_bus_ids=self.machine_bus_ids,
                base_mechanical_powers_pu=self.base_mechanical_powers_pu,
                machine_derivative_evaluator=machine_derivative_evaluator,
                machine_connection_states=connection_states,
            )
        except Exception as exc:
            raise GeneratorAugmentedIntegratorError(
                f"augmented generator stage failed at t={float(simulation_time_s):.12g} s"
            ) from exc

    def derivatives(
        self,
        global_state: Sequence[float] | np.ndarray,
        simulation_time_s: float,
    ) -> np.ndarray:
        """Integrator-compatible derivative callback: (global_state, time)."""
        return self.evaluate_stage(global_state, simulation_time_s).derivative_assembly.state_derivatives.copy()

    def step(
        self,
        global_state: Sequence[float] | np.ndarray,
        simulation_time_s: float,
        dt: float,
    ) -> GeneratorAugmentedStepResult:
        """Advance the full augmented state using Core's configured integrator."""
        state = np.asarray(global_state, dtype=float)
        if state.ndim != 1 or state.size != self.layout.state_size or not np.all(np.isfinite(state)):
            raise GeneratorAugmentedIntegratorError("global_state must match the finite augmented state layout")
        try:
            start = float(simulation_time_s)
            interval = float(dt)
        except (TypeError, ValueError, OverflowError) as exc:
            raise GeneratorAugmentedIntegratorError("simulation time and dt must be numeric") from exc
        if not np.isfinite(start) or not np.isfinite(interval) or interval <= 0.0:
            raise GeneratorAugmentedIntegratorError("simulation time must be finite and dt must be positive")

        def derivative(stage_state: np.ndarray, stage_time: float) -> np.ndarray:
            return self.derivatives(stage_state, stage_time)

        try:
            accepted_state = self.integrator.step(
                x=state.copy(),
                derivative=derivative,
                t=start,
                dt=interval,
            )
        except Exception as exc:
            raise GeneratorAugmentedIntegratorError(
                f"augmented generator integration failed over [{start:.12g}, {start + interval:.12g}] s"
            ) from exc

        accepted_state = np.asarray(accepted_state, dtype=float)
        if accepted_state.shape != (self.layout.state_size,) or not np.all(np.isfinite(accepted_state)):
            raise GeneratorAugmentedIntegratorError("integrator returned an invalid augmented state")
        final_time = start + interval
        final_stage = self.evaluate_stage(accepted_state, final_time)
        return GeneratorAugmentedStepResult(
            state=accepted_state,
            simulation_time_s=final_time,
            final_stage=final_stage,
        )


__all__ = [
    "GeneratorAugmentedIntegratorError",
    "GeneratorAugmentedStepResult",
    "GeneratorAugmentedDAEAdapter",
]
