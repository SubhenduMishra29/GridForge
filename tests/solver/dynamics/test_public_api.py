# ============================================================
# GridForge V2 — Dynamics Public API Test
# Author: Subhendu Mishra
# ============================================================

from core.solver.dynamics import (
    ClassicalSynchronousMachine,
    Integrator,
    MultiMachineSystem,
)


def test_dynamics_public_api_exposes_canonical_state_owner() -> None:
    assert ClassicalSynchronousMachine is not None
    assert Integrator is not None
    assert MultiMachineSystem is not None


def test_dynamics_public_api_has_no_obsolete_dynamic_state_export() -> None:
    import core.solver.dynamics as dynamics

    assert not hasattr(dynamics, "DynamicState")
    assert not hasattr(dynamics, "DynamicStateVector")
