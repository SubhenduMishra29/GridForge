"""Regression source for bidirectional instrumentation wiring navigation."""

from types import SimpleNamespace

from ui.instrumentation_wiring_navigation import InstrumentationWiringNavigator


class _Application:
    def __init__(self, resolutions):
        self.resolutions = tuple(resolutions)
        self.project_lifecycle = SimpleNamespace(
            state="ACTIVE",
            has_project=True,
            context=SimpleNamespace(project_id="project-1"),
            activation_generation=7,
        )

    def resolve_instrumentation_signal_endpoints(self):
        return self.resolutions


class _Surface:
    document_id = "sld-1"

    def highlight_instrumentation_routes(self, **_kwargs):
        return ("segment-1",)


def _resolution(
    *,
    endpoint_kind="CONTROL_INPUT",
    endpoint_id="component-1",
    owner_id="control-1",
    port="IN",
    status="RESOLVED",
    generation=7,
    binding_id="binding-1",
    signal_id="signal-1",
    carrier_ids=("core-1",),
):
    return SimpleNamespace(
        project_id="project-1",
        activation_generation=generation,
        endpoint_kind=endpoint_kind,
        endpoint_id=endpoint_id,
        owner_id=owner_id,
        port=port,
        status=status,
        binding_id=binding_id,
        signal_id=signal_id,
        carrier_ids=carrier_ids,
        physical_sink_terminal={"terminal_point_id": "terminal-point-1"},
    )


def test_provenance_targets_exposes_only_current_resolved_consumers():
    application = _Application((
        _resolution(),
        _resolution(
            endpoint_kind="PROTECTION_INPUT",
            endpoint_id="measurement-binding-2",
            owner_id="protection-element-2",
            port="phase_a",
            binding_id="binding-2",
        ),
        _resolution(endpoint_id="unresolved-component", status="UNRESOLVED", binding_id="binding-3"),
        _resolution(endpoint_id="stale-component", generation=6, binding_id="binding-4"),
        _resolution(endpoint_id="ambiguous-component", status="AMBIGUOUS", binding_id="binding-5"),
    ))
    navigator = InstrumentationWiringNavigator(
        application=application,
        activate_sld=lambda: None,
        refresh_sld=lambda: None,
        surface=_Surface(),
    )

    targets = navigator.provenance_targets()

    assert {item["target_editor"] for item in targets["signal-1"]} == {"control", "protection"}
    assert {item["target_object_id"] for item in targets["signal-1"]} == {
        "component-1", "protection-element-2",
    }
    assert len(targets["signal-1"]) == 2


def test_sld_consumer_navigation_revalidates_then_activates_refreshes_and_selects():
    application = _Application((_resolution(),))
    calls = []
    navigator = InstrumentationWiringNavigator(
        application=application,
        activate_sld=lambda: None,
        refresh_sld=lambda: None,
        surface=_Surface(),
        activate_editor=lambda editor: calls.append(("activate", editor)),
        refresh_editor=lambda editor: calls.append(("refresh", editor)),
        select_object=lambda object_id: calls.append(("select", object_id)),
    )
    target = navigator.provenance_targets()["signal-1"][0]

    result = navigator.navigate_to_consumer(target)

    assert result.success is True
    assert calls == [
        ("activate", "control"),
        ("refresh", "control"),
        ("select", "component-1"),
    ]


def test_sld_consumer_navigation_fails_closed_after_endpoint_becomes_unresolved():
    application = _Application((_resolution(),))
    calls = []
    navigator = InstrumentationWiringNavigator(
        application=application,
        activate_sld=lambda: None,
        refresh_sld=lambda: None,
        surface=_Surface(),
        activate_editor=lambda editor: calls.append(("activate", editor)),
        select_object=lambda object_id: calls.append(("select", object_id)),
    )
    target = navigator.provenance_targets()["signal-1"][0]
    application.resolutions = (_resolution(status="UNRESOLVED"),)

    result = navigator.navigate_to_consumer(target)

    assert result.success is False
    assert calls == []


def test_sld_protection_consumer_navigation_selects_protection_element_owner():
    application = _Application((
        _resolution(
            endpoint_kind="PROTECTION_INPUT",
            endpoint_id="measurement-binding-2",
            owner_id="protection-element-2",
            port="phase_a",
            binding_id="binding-2",
        ),
    ))
    calls = []
    navigator = InstrumentationWiringNavigator(
        application=application,
        activate_sld=lambda: None,
        refresh_sld=lambda: None,
        surface=_Surface(),
        activate_editor=lambda editor: calls.append(("activate", editor)),
        refresh_editor=lambda editor: calls.append(("refresh", editor)),
        select_object=lambda object_id: calls.append(("select", object_id)),
    )
    target = navigator.provenance_targets()["signal-1"][0]

    result = navigator.navigate_to_consumer(target)

    assert result.success is True
    assert calls == [
        ("activate", "protection"),
        ("refresh", "protection"),
        ("select", "protection-element-2"),
    ]
