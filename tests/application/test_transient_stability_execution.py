import json
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
from scipy.sparse import csr_matrix

from core.application.read_models import StudyResultReadModel
from core.application.read_service import StudyReadService
from core.application.revision import ProjectRevision
from core.solver.dynamics.transient_stability import TransientStabilityResult

from core.analysis.dynamic_model_association import DynamicMachineModelAssociation
from core.analysis.power_flow_preparation import PreparedBranch, PreparedPowerFlow
from core.analysis.transient_stability import TransientStabilityStudyConfiguration
from core.application.bootstrap import create_application
from core.application.study import StudyRequest
from core.network import Network
from core.model.bus import Bus
from core.model.synchronous_machine import SynchronousMachine
from core.numerical.ybus import YBus, YBusBuilder
from core.solver.dynamics.machine_models import ClassicalMachineParameters
from core.solver.power_flow.input import PowerFlowBusType, PowerFlowInput
from core.solver.power_flow.result import PowerFlowResult


def test_application_executes_transient_stability_from_detached_pf_snapshot():
    network = Network()
    network.add_bus(Bus("B1", name="Bus 1", nominal_voltage_kv=11.0))
    network.add_bus(Bus("B2", name="Bus 2", nominal_voltage_kv=11.0))
    network.add_synchronous_machine(SynchronousMachine("G1", name="G1", endpoint=network.get_by_id("bus", "B1")))
    application = create_application(network)

    bus_ids = ("B1", "B2")
    power_flow_input = PowerFlowInput(
        bus_ids=bus_ids,
        bus_types=(PowerFlowBusType.SLACK, PowerFlowBusType.PQ),
        p_spec=(0.8, -0.3),
        q_spec=(0.1, -0.1),
        q_min=(None, None),
        q_max=(None, None),
        initial_vm=(1.0, 1.0),
        initial_va=(0.0, 0.0),
    )
    branch = PreparedBranch("L1", "B1", "B2", 0.0, 0.2, 0.0)
    empty_ybus = YBus(csr_matrix((2, 2), dtype=np.complex128), bus_ids)
    snapshot = PreparedPowerFlow(
        input=power_flow_input,
        ybus=empty_ybus,
        base_mva=100.0,
        bus_voltage_bases={"B1": 11.0, "B2": 11.0},
        branches=(branch,),
        project_id=application.project_lifecycle.context.project_id,
        activation_generation=application.project_lifecycle.activation_generation,
        topology_revision=application.revision.topology_revision,
        source_revision=(
            application.revision.model_revision,
            application.revision.topology_revision,
            application.revision.presentation_revision,
            application.revision.persisted_revision,
        ),
    )
    snapshot = PreparedPowerFlow(
        input=snapshot.input,
        ybus=YBusBuilder().build(snapshot),
        base_mva=snapshot.base_mva,
        bus_voltage_bases=snapshot.bus_voltage_bases,
        branches=snapshot.branches,
        project_id=snapshot.project_id,
        activation_generation=snapshot.activation_generation,
        topology_revision=snapshot.topology_revision,
        source_revision=snapshot.source_revision,
    )
    power_flow_result = PowerFlowResult(
        success=True,
        iterations=2,
        error=1e-10,
        pv_to_pq=(),
        history=(1.0, 1e-10),
        message="converged",
        voltage_magnitudes=(1.0, 0.98),
        voltage_angles=(0.1, -0.02),
        bus_ids=power_flow_input.bus_ids,
        snapshot_id=power_flow_input.snapshot_id,
    )

    application.dynamic_models.bind(DynamicMachineModelAssociation(
        machine_id="G1",
        bus_id="B1",
        model_type="classical",
        parameters=ClassicalMachineParameters(H=3.0, Xd_prime=0.3, Efd=1.1),
        mechanical_power=0.0,
        project_id=application.project_lifecycle.context.project_id,
        activation_generation=application.project_lifecycle.activation_generation,
    ))
    request = StudyRequest(
        project_id=application.project_lifecycle.context.project_id,
        activation_generation=application.project_lifecycle.activation_generation,
        source_revision=application.revision,
        study_type="transient_stability",
        configuration={
            "configuration": TransientStabilityStudyConfiguration(end_time=0.02, dt=0.01),
            "prepared_power_flow": snapshot,
            "power_flow_result": power_flow_result,
        },
    )

    result = application.execute_study(request)

    assert result.status == "completed"
    assert result.value.number_of_steps >= 1


def test_study_comparison_read_contract_accepts_live_and_archived_results():
    project_id = "project-live-archive"
    revision = ProjectRevision(model_revision=3, topology_revision=2)
    live_study_id = uuid4()
    archived_record_id = uuid4()
    provenance = {
        "nominal_frequency_hz": 50.0,
        "power_base_mva": 100.0,
        "bus_voltage_bases_kv": {"B1": 11.0},
        "canonical_topology_fingerprint": "topology-sha256",
        "prepared_network_topology_fingerprint": "prepared-sha256",
        "machine_model_manifest": (("G1", "classical"),),
        "state_signals": ({
            "signal_id": "machine:G1:rotor_angle",
            "global_index": 0,
            "label": "G1 rotor angle",
            "state_name": "rotor_angle",
            "unit": "rad",
            "machine_id": "G1",
        },),
    }
    def transient_result(offset):
        return TransientStabilityResult(
            time=np.asarray([0.0, 0.01]),
            states=np.asarray([[0.1 + offset], [0.2 + offset]]),
            terminal_voltages=({"B1": 1.0 + 0.0j}, {"B1": 0.99 + 0.01j}),
            electrical_powers=({"G1": (0.8, 0.1)}, {"G1": (0.79, 0.11)}),
            provenance=provenance,
        )
    archived_result = SimpleNamespace(
        study_id=uuid4(),
        project_id=project_id,
        activation_generation=3,
        source_revision=revision,
        study_type="transient_stability",
        status="completed",
        value=transient_result(0.0),
        message="archived run",
        metadata={},
    )
    live_result = StudyResultReadModel(
        study_id=live_study_id,
        project_id=project_id,
        activation_generation=4,
        source_revision=revision,
        study_type="transient_stability",
        status="completed",
        value=transient_result(0.05),
        current=True,
    )
    archive_record = SimpleNamespace(
        record_id=archived_record_id,
        saved_at="2026-11-05T10:00:00+00:00",
        result=archived_result,
    )
    studies = SimpleNamespace(
        get_result=lambda *args, **kwargs: None,
        results=lambda **kwargs: (),
    )
    archive = SimpleNamespace(
        load_all=lambda *args, **kwargs: (archive_record,),
        load_latest=lambda *args, **kwargs: None,
    )
    read_service = StudyReadService(studies, archive)

    comparison = read_service.compare_study_results(
        live_result,
        archived_record_id,
        project_id=project_id,
        activation_generation=4,
        current_revision=revision,
    )

    assert comparison.left is live_result
    assert comparison.right.record_id == archived_record_id
    assert comparison.left.study_id == live_study_id
    assert comparison.compatible
    assert comparison.numeric_comparison_status == "TRANSIENT_COMPARABLE"
    assert comparison.transient_signal_deltas
    assert comparison.transient_signal_deltas[0].deltas == (0.05, 0.05)
    payload = json.loads(read_service.export_study_comparison(
        live_result,
        archived_record_id,
        project_id=project_id,
        activation_generation=4,
        current_revision=revision,
    ))
    assert payload["format"] == "GridForgeTransientComparison"
    assert payload["left"]["source_kind"] == "live"
    assert payload["left"]["record_id"] is None
    assert payload["right"]["source_kind"] == "archive"
    assert payload["right"]["record_id"] == str(archived_record_id)
    stale_live = StudyResultReadModel(
        study_id=live_study_id,
        project_id=project_id,
        activation_generation=4,
        source_revision=revision,
        study_type="transient_stability",
        status="completed",
        value=transient_result(0.05),
        current=False,
    )
    stale_comparison = read_service.compare_study_results(
        stale_live,
        archived_record_id,
        project_id=project_id,
        activation_generation=4,
        current_revision=revision,
    )
    assert not stale_comparison.compatible
    assert "LEFT_LIVE_RESULT_NOT_CURRENT" in stale_comparison.transient_compatibility_diagnostics
    revision_drift_comparison = read_service.compare_study_results(
        live_result,
        archived_record_id,
        project_id=project_id,
        activation_generation=4,
        current_revision=ProjectRevision(model_revision=4, topology_revision=2),
    )
    assert not revision_drift_comparison.compatible
    assert "LEFT_LIVE_RESULT_NOT_CURRENT" in revision_drift_comparison.transient_compatibility_diagnostics
    assert read_service.compare_archived_results(
        live_result,
        archived_record_id,
        project_id=project_id,
        activation_generation=4,
        current_revision=revision,
    ) == comparison
