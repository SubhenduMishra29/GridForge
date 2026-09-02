import dataclasses

import numpy as np

from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.runtime_state import PowerFlowRuntimeState
from core.solver.power_flow.result import PowerFlowResult
from core.solver.common.mismatch import PowerMismatch


def make_input():
    return PowerFlowInput(
        bus_ids=("B1", "B2"),
        bus_types=(PowerFlowBusType.SLACK, PowerFlowBusType.PQ),
        p_spec=(0.0, -1.0),
        q_spec=(0.0, -0.5),
        q_min=(None, None),
        q_max=(None, None),
        initial_vm=(1.0, 1.0),
        initial_va=(0.0, 0.0),
    )


def test_runtime_state_is_initialized_from_numerical_input_only():
    inp = make_input()
    state = PowerFlowRuntimeState.from_input(inp)
    assert np.allclose(state.vm, [1.0, 1.0])
    assert np.allclose(state.va, [0.0, 0.0])
    assert tuple(state.effective_bus_types) == inp.bus_types
    assert tuple(state.effective_q_spec) == inp.q_spec
    assert not any(value is inp for value in (state.vm, state.va, state.effective_q_spec))


def test_runtime_state_owns_pv_pq_transition_without_changing_input():
    inp = PowerFlowInput(
        bus_ids=("B1", "B2"),
        bus_types=(PowerFlowBusType.SLACK, PowerFlowBusType.PV),
        p_spec=(0.0, 1.0), q_spec=(0.0, 0.0),
        q_min=(None, -0.2), q_max=(None, 0.2),
        initial_vm=(1.0, 1.0), initial_va=(0.0, 0.0),
    )
    state = PowerFlowRuntimeState.from_input(inp)
    state.convert_pv_to_pq(1, -0.2, "Qmin")
    assert state.effective_bus_types[1] is PowerFlowBusType.PQ
    assert state.effective_q_spec[1] == -0.2
    assert inp.bus_types[1] is PowerFlowBusType.PV
    assert inp.q_spec[1] == 0.0


def test_result_is_immutable_and_standalone():
    result = PowerFlowResult(
        success=True,
        iterations=2,
        error=1e-9,
        pv_to_pq=(),
        history=(1.0, 1e-9),
        message="Converged.",
        voltage_magnitudes=(1.0, 0.99),
        voltage_angles=(0.0, -0.01),
    )
    assert dataclasses.is_dataclass(result)
    assert result.voltages == {"Vm": (1.0, 0.99), "Va": (0.0, -0.01)}
    try:
        result.success = False
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("PowerFlowResult must be immutable")


def test_mismatch_consumes_only_numerical_contracts():
    inp = make_input()
    state = PowerFlowRuntimeState.from_input(inp)
    ybus = np.array([[10j, -10j], [-10j, 10j]], dtype=complex)
    engine = PowerMismatch(inp, ybus, state)
    p, q = engine.compute_power()
    assert p.shape == (2,)
    assert q.shape == (2,)
    assert engine.compute().shape == (2,)
    assert not hasattr(engine, "network")
    assert not hasattr(engine, "buses")
