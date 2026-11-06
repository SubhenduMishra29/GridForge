from core.analysis.transient_event_state import TransientEventState
from core.analysis.transient_network import DetachedTransientNetworkState


def test_breaker_event_changes_only_detached_state():
    live = DetachedTransientNetworkState(
        bus_ids=("B1", "B2"),
        equipment_states={"L1": True},
    )
    state = TransientEventState.from_snapshot(live)

    state.set_equipment("L1", False)

    assert state.is_conducting("L1") is False
    assert live.is_element_conducting("L1") is True
    assert state.topology_revision == 1


def test_fault_apply_and_clear_restore_detached_fault_state():
    snapshot = DetachedTransientNetworkState(bus_ids=("B1",))
    state = TransientEventState.from_snapshot(snapshot)
    fault = {"bus_id": "B1", "impedance": 0.0j}

    state.apply_fault(fault)
    assert state.active_fault == fault
    state.clear_fault()
    assert state.active_fault is None
    assert snapshot.active_fault is None
