import numpy as np
import pytest

from core.solver.dynamics import DAESolver, Integrator, MultiMachineSystem, TransientStabilityError, TransientStabilitySolver
from core.solver.dynamics.machine_models import ClassicalSynchronousMachine


def test_event_inside_step_is_applied_at_exact_boundary_before_recording_voltage():
    machine = ClassicalSynchronousMachine("G1", "B1", H=3.0, Xd_prime=0.3, Efd=1.1)
    system = MultiMachineSystem((machine,))
    applied = {"fault": False}
    observed_times = []

    def network_solver(state, time):
        del state
        observed_times.append(time)
        return {"B1": 0.5 + 0.0j if applied["fault"] else 1.0 + 0.0j}

    dae = DAESolver(
        system,
        network_solver,
        {"G1": 0.0},
        integrator=Integrator("RK4"),
    )
    solver = TransientStabilitySolver(dae, start_time=0.0, end_time=0.25, dt=0.1)
    solver.event_manager.add(
        0.15,
        lambda: applied.__setitem__("fault", True),
        event_id="fault-on",
        event_type="fault_apply",
    )
    solver.initialize(np.array([0.0, 0.0]), time=0.0)

    result = solver.run()

    assert np.any(np.isclose(result.time, 0.15))
    boundary_index = int(np.where(np.isclose(result.time, 0.15))[0][0])
    assert result.terminal_voltages[boundary_index]["B1"] == 0.5 + 0.0j
    assert any(np.isclose(time, 0.15) for time in observed_times)
    assert result.events[0].event_id == "fault-on"
    assert np.all(np.diff(result.time) > 0.0)
    assert len(result.discontinuities) == 1
    boundary = result.discontinuities[0]
    assert boundary.time == 0.15
    assert boundary.event_ids == ("fault-on",)
    assert boundary.pre_terminal_voltages["B1"] == 1.0 + 0.0j
    assert boundary.post_terminal_voltages["B1"] == 0.5 + 0.0j
    assert boundary.post_status == "succeeded"


def test_failed_event_batch_returns_partial_trajectory_without_post_state():
    machine = ClassicalSynchronousMachine("G1", "B1", H=3.0, Xd_prime=0.3, Efd=1.1)
    system = MultiMachineSystem((machine,))
    applied = {"fault": False}
    def network_solver(state, time):
        del state, time
        return {"B1": 0.5 + 0.0j if applied["fault"] else 1.0 + 0.0j}
    dae = DAESolver(system, network_solver, {"G1": 0.0}, integrator=Integrator("RK4"))
    solver = TransientStabilitySolver(dae, start_time=0.0, end_time=0.25, dt=0.1)
    solver.event_manager.add(0.15, lambda: applied.__setitem__("fault", True), event_id="a-fault-on", event_type="fault_apply")
    def fail_dispatch():
        raise RuntimeError("dispatch failure after first event")
    solver.event_manager.add(0.15, fail_dispatch, event_id="b-fail", event_type="test_failure")
    solver.initialize(np.array([0.0, 0.0]))
    with pytest.raises(TransientStabilityError) as captured:
        solver.run()
    partial = captured.value.partial_result
    assert partial is not None
    assert np.all(np.diff(partial.time) > 0.0)
    assert np.isclose(partial.time[-1], 0.15)
    assert len(partial.discontinuities) == 1
    boundary = partial.discontinuities[0]
    assert boundary.event_ids == ("a-fault-on", "b-fail")
    assert boundary.pre_terminal_voltages["B1"] == 1.0 + 0.0j
    assert boundary.post_status == "dispatch_failed"
    assert boundary.post_state is None
    assert boundary.post_terminal_voltages is None
    assert tuple(item.status for item in boundary.event_executions) == ("succeeded", "failed")


def test_incremental_step_exposes_event_boundary_sides():
    machine = ClassicalSynchronousMachine("G1", "B1", H=3.0, Xd_prime=0.3, Efd=1.1)
    system = MultiMachineSystem((machine,))
    applied = {"fault": False}
    def network_solver(state, time):
        del state, time
        return {"B1": 0.5 + 0.0j if applied["fault"] else 1.0 + 0.0j}
    dae = DAESolver(system, network_solver, {"G1": 0.0}, integrator=Integrator("RK4"))
    solver = TransientStabilitySolver(dae, start_time=0.0, end_time=0.2, dt=0.1)
    solver.event_manager.add(0.1, lambda: applied.__setitem__("fault", True), event_id="step-fault", event_type="fault_apply")
    solver.initialize(np.array([0.0, 0.0]))
    solution = solver.step()
    assert solution.time == 0.1
    assert solver.last_step_discontinuity is not None
    assert solver.last_step_discontinuity.event_ids == ("step-fault",)
    assert solver.last_step_discontinuity.pre_terminal_voltages["B1"] == 1.0 + 0.0j
    assert solver.last_step_discontinuity.post_terminal_voltages["B1"] == 0.5 + 0.0j
