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

    def is_machine_connected(self, machine_id: str) -> bool:
        """Expose the same detached path state used by Norton-source assembly."""
        return self.event_state.is_machine_connected(machine_id)

    @property
    def provenance(self) -> dict[str, object]:
        snapshot = self.event_state.snapshot
        return {
            "project_id": snapshot.project_id,
            "activation_generation": snapshot.activation_generation,
            "source_revision": snapshot.source_revision,
            "topology_revision_at_start": snapshot.topology_revision,
            "machine_connections": {
                machine_id: {
                    "switching_path": path,
                    "disconnected_rotor_policy": snapshot.machine_rotor_policies[machine_id],
                }
                for machine_id, path in sorted(snapshot.machine_connection_paths.items())
            },
        }


__all__ = ["TransientNetworkRuntime"]
