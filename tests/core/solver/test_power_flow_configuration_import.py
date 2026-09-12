def test_application_import_can_reach_authoritative_power_flow_configuration():
    from core.application.application import Application
    from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
    from core.solver.power_flow import PowerFlowStudyConfiguration as SolverStudyConfiguration

    assert Application is not None
    assert SolverStudyConfiguration is PowerFlowStudyConfiguration
