import numpy as np

from core.analysis.power_flow_preparation import PreparedBranch, PreparedShunt
from core.analysis.transient_event_state import TransientEventState
from core.analysis.transient_events import schedule_breaker_open, schedule_fault_apply, schedule_fault_clear
from core.analysis.transient_fault import TransientFault
from core.analysis.transient_network import DetachedTransientNetworkState
from core.analysis.transient_runtime import TransientNetworkRuntime
from core.solver.dynamics import EventManager, EventTransition, MultiMachineSystem
from core.solver.dynamics.machine_models import ClassicalSynchronousMachine
from core.solver.short_circuit.fault_types import FaultType


def _runtime():
    snapshot = DetachedTransientNetworkState(
        bus_ids=("B1", "B2"),
        branches=(PreparedBranch("L1", "B1", "B2", 0.0, 0.2, 0.0),),
        transformers=(),
        shunts=(PreparedShunt("S1", "B2", 1.0, 0.0),),
        equipment_states={"L1": True, "S1": True},
        topology_revision=1,
    )
    event_state = TransientEventState.from_snapshot(snapshot)
    machine = ClassicalSynchronousMachine("G1", "B1", H=3.0, Xd_prime=0.3, Efd=1.1)
    return event_state, TransientNetworkRuntime(event_state, MultiMachineSystem((machine,)))


def test_fault_event_changes_detached_network_solution_and_clear_restores():
    event_state, runtime = _runtime()
    state = np.array([0.0, 0.0])
    baseline = runtime.solve(state, 0.0)
    manager = EventManager()
    fault = TransientFault(FaultType.THREE_PHASE, "B2", 0.1j)
    schedule_fault_apply(manager, event_state, 0.1, fault, event_id="fault-on")
    schedule_fault_clear(manager, event_state, 0.2, event_id="fault-off")

    manager.process_interval(0.0, 0.1)
    fault_transition = manager.history[0].transition
    assert isinstance(fault_transition, EventTransition)
    assert fault_transition.transition_type == "fault_apply"
    assert fault_transition.target_kind == "fault"
    assert fault_transition.target_id == "TRANSIENT-FAULT" or fault_transition.target_id == str(getattr(fault, "fault_id", ""))
    assert fault_transition.previous_state is False
    assert fault_transition.new_state is True
    faulted = runtime.solve(state, 0.1)
    manager.process_interval(0.1, 0.2)
    restored = runtime.solve(state, 0.2)

    assert faulted != baseline
    assert restored == baseline
    assert event_state.snapshot.active_fault is None


def test_breaker_event_changes_only_detached_passive_equipment_state():
    event_state, runtime = _runtime()
    manager = EventManager()
    schedule_breaker_open(
        manager,
        event_state,
        0.1,
        "CB1",
        affected_equipment_ids=("L1",),
        event_id="breaker-open",
    )
    baseline = runtime.solve(np.array([0.0, 0.0]), 0.0)
    manager.process_interval(0.0, 0.1)
    switch_transition = manager.history[0].transition
    assert isinstance(switch_transition, EventTransition)
    assert switch_transition.target_kind == "switch"
    assert switch_transition.target_id == "CB1"
    assert switch_transition.previous_state is None
    assert switch_transition.new_state is False
    opened = runtime.solve(np.array([0.0, 0.0]), 0.1)

    assert event_state.breaker_states["CB1"] is False
    assert event_state.is_conducting("L1") is False
    assert event_state.snapshot.is_element_conducting("L1") is True
    assert opened != baseline
