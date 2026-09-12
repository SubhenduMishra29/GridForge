import pytest

from core.analysis.dynamic_initial_state import DynamicInitialStatePreparation
from core.analysis.dynamic_model_association import DynamicMachineModelAssociation, DynamicMachineModelRegistry
from core.solver.dynamics.machine_models import ClassicalMachineParameters
from core.solver.power_flow.result import PowerFlowResult


def test_power_flow_result_prepares_dynamic_initial_state():
    result = PowerFlowResult(
        success=True,
        iterations=3,
        error=1e-10,
        pv_to_pq=(),
        history=(1.0, 1e-4, 1e-10),
        message="converged",
        voltage_magnitudes=(1.0, 0.98),
        voltage_angles=(0.1, -0.02),
    )
    registry = DynamicMachineModelRegistry((
        DynamicMachineModelAssociation(
            machine_id="G1",
            bus_id="B1",
            model_type="classical",
            parameters=ClassicalMachineParameters(H=3.0, Xd_prime=0.3, Efd=1.1),
            mechanical_power=0.8,
        ),
    ))

    prepared = DynamicInitialStatePreparation.prepare(
        bus_ids=("B1", "B2"),
        power_flow_result=result,
        dynamic_models=registry,
    )

    assert prepared.state.shape == (2,)
    assert prepared.bus_voltages["B1"] == pytest.approx(1.0 * complex(__import__('math').cos(0.1), __import__('math').sin(0.1)))
    assert prepared.machine_ids == ("G1",)
