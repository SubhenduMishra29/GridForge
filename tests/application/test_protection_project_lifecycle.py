from core.application.bootstrap import create_application
from core.network import Network
from ui.sld.sld_document import SLDDocument


def test_close_project_deactivates_protection_runtime_and_configuration():
    application = create_application(Network())

    assert application.protection_runtime is not None
    assert application.protection_configuration_service.configuration.project_id == application.project_lifecycle.context.project_id

    application.close_project()

    assert application.project_lifecycle.context is None
    assert application.protection_runtime is None
    assert application.protection_configuration_service.configuration is None


def test_new_project_recreates_protection_state_after_close():
    application = create_application(Network())
    application.configure_project_presentation_contract(
        factory=lambda context: SLDDocument(f"{context.project_id}:sld", project_id=context.project_id),
        serializer=lambda value: value.to_dict(),
        deserializer=lambda data: SLDDocument.from_dict(data),
    )
    first = application.project_lifecycle.context

    application.close_project()
    second = application.new_project("Second")

    assert first is not None
    assert second.project_id != first.project_id
    assert application.protection_runtime is not None
    assert application.protection_configuration_service.configuration.project_id == second.project_id
    assert application.protection_runtime.network is application.project_lifecycle.network
