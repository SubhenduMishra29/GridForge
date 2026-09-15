"""Study-owned transient runtime adapters."""

from __future__ import annotations

import numpy as np

from core.solver.dynamics.multimachine import MultiMachineSystem

from .transient_event_state import TransientEventState
from .transient_network import TransientNetworkSolver


class TransientNetworkRuntime:
    """Expose the current detached event-state network through the DAE callback."""

    def __init__(self, event_state: TransientEventState, machine_system: MultiMachineSystem) -> None:
        if not isinstance(event_state, TransientEventState):
            raise TypeError("event_state must be TransientEventState.")
        if not isinstance(machine_system, MultiMachineSystem):
            raise TypeError("machine_system must be MultiMachineSystem.")
        self.event_state = event_state
        self.machine_system = machine_system

    def solve(self, state: np.ndarray, time: float) -> dict[str, complex]:
        detached = self.event_state.detached_view()
        return TransientNetworkSolver(detached, self.machine_system).solve(state, time)


__all__ = ["TransientNetworkRuntime"]
