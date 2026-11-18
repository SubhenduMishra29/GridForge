"""Resolve canonical instrumentation signal endpoints against active project owners.

This is a read-only Application adapter. It correlates the persisted signal
and carrier identities with active MeasurementChannel, Control and Protection
configuration. It never mutates those owners or infers relationships from tags,
display names, canvas geometry or list order.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable, Mapping

from core.application.read_models import SignalEndpointResolutionReadModel
from core.model.instrument_wiring import (
    CarrierKind,
    InstrumentationWiringInventory,
    SignalEndpointKind,
    SignalKind,
    TerminalAccessoryKind,
    TerminalAccessoryState,
    WiringConductorRole,
)


_SIGNAL_TO_MEASUREMENT_TYPE = {
    SignalKind.CURRENT: "CURRENT",
    SignalKind.VOLTAGE: "VOLTAGE",
    SignalKind.DIGITAL: "DIGITAL",
    SignalKind.TEMPERATURE: "TEMPERATURE",
}

_SIGNAL_CONTINUITY_ACCESSORY_KINDS = frozenset({
    TerminalAccessoryKind.FIXED_LINK,
    TerminalAccessoryKind.TEST_DISCONNECT,
    TerminalAccessoryKind.SHORTING_LINK,
    TerminalAccessoryKind.FUSE_LINK,
    TerminalAccessoryKind.ISOLATING_LINK,
})


def _index_by_channel_id(values: Iterable[Any] | None, label: str) -> dict[str, Any] | None:
    if values is None:
        return None
    result: dict[str, Any] = {}
    for value in values:
        channel_id = getattr(value, "channel_id", None)
        if not isinstance(channel_id, str) or not channel_id.strip():
            raise TypeError(f"{label} entries must expose a non-empty channel_id.")
        if channel_id in result:
            raise ValueError(f"{label} contains duplicate channel identity {channel_id!r}.")
        result[channel_id] = value
    return result


def _source_terminal_identity(channel_configuration: Any) -> tuple[tuple[str, str, None] | None, tuple[str, ...]]:
    source_id = getattr(channel_configuration, "source_id", None)
    reference = getattr(channel_configuration, "source_terminal_reference", None)
    if not isinstance(source_id, str) or not source_id.strip():
        return None, ("MeasurementChannel has no explicit physical source equipment identity.",)
    if not isinstance(reference, Mapping):
        return None, ("MeasurementChannel has no explicit canonical source-terminal reference.",)
    if str(reference.get("kind", "")).casefold() != "terminal":
        return None, ("MeasurementChannel source reference is not a Core terminal endpoint.",)
    equipment_id = reference.get("object_id")
    terminal_role = reference.get("terminal_role")
    if (
        not isinstance(equipment_id, str) or not equipment_id.strip()
        or not isinstance(terminal_role, str) or not terminal_role.strip()
    ):
        return None, ("MeasurementChannel source-terminal identity is incomplete.",)
    if equipment_id != source_id:
        return None, ("MeasurementChannel source equipment and source-terminal owner identities disagree.",)
    declared_equipment_type = getattr(channel_configuration, "source_equipment_type", None)
    referenced_equipment_type = reference.get("equipment_type")
    if (
        declared_equipment_type is not None
        and referenced_equipment_type is not None
        and declared_equipment_type != referenced_equipment_type
    ):
        return None, ("MeasurementChannel source equipment type and terminal reference disagree.",)
    return (equipment_id, terminal_role, None), ()


def _channel_signal_diagnostics(signal: Any, channel: Any) -> tuple[str, ...]:
    diagnostics: list[str] = []
    expected_type = _SIGNAL_TO_MEASUREMENT_TYPE.get(signal.kind)
    actual_type = str(getattr(channel, "signal_type", "")).strip().upper()
    if expected_type is None:
        diagnostics.append(
            f"Signal kind {signal.kind.value!r} has no authoritative MeasurementSignalType mapping."
        )
    elif actual_type != expected_type:
        diagnostics.append(
            f"Signal kind {signal.kind.value!r} does not match MeasurementChannel type {actual_type!r}."
        )
    signal_phase = signal.phase
    channel_phase = str(getattr(channel, "phase", "")).strip()
    if signal_phase is None or not channel_phase or signal_phase.upper() != channel_phase.upper():
        diagnostics.append(
            f"Signal phase {signal_phase!r} does not match MeasurementChannel phase {channel_phase!r}."
        )
    signal_unit = signal.unit
    channel_unit = str(getattr(channel, "unit", "")).strip()
    if signal_unit is None or not channel_unit or signal_unit.casefold() != channel_unit.casefold():
        diagnostics.append(
            f"Signal unit {signal_unit!r} does not match MeasurementChannel unit {channel_unit!r}; no conversion is inferred."
        )
    return tuple(diagnostics)


def _reachable(graph: Mapping[tuple, set[tuple]], start: tuple) -> set[tuple]:
    visited = {start}
    pending = deque((start,))
    while pending:
        current = pending.popleft()
        for neighbour in graph.get(current, ()):
            if neighbour not in visited:
                visited.add(neighbour)
                pending.append(neighbour)
    return visited


def _count_simple_paths(
    graph: Mapping[tuple, set[tuple]], start: tuple, target: tuple, *, limit: int = 2
) -> int:
    """Count simple paths only up to limit; two paths are enough to prove ambiguity."""
    if start == target:
        return 1
    count = 0
    pending: list[tuple[tuple, frozenset[tuple]]] = [(start, frozenset((start,)))]
    while pending:
        current, visited = pending.pop()
        for neighbour in graph.get(current, ()):
            if neighbour in visited:
                continue
            if neighbour == target:
                count += 1
                if count >= limit:
                    return count
            else:
                pending.append((neighbour, visited | {neighbour}))
    return count


def _resolve_physical_path(
    inventory: InstrumentationWiringInventory,
    signal_id: str,
    channel_configuration: Any,
    sink_terminal: Any,
    direction: str,
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    source, source_diagnostics = _source_terminal_identity(channel_configuration)
    if source_diagnostics:
        return "UNRESOLVED", source_diagnostics, ()
    if sink_terminal is None or not hasattr(sink_terminal, "canonical_identity"):
        return "UNRESOLVED", ("Endpoint has no canonical physical sink-terminal identity.",), ()
    sink = sink_terminal.canonical_identity

    cores = {item.id: item for item in inventory.cores}
    wires = {item.id: item for item in inventory.panel_wires}
    carrier_bindings = tuple(
        item for item in inventory.signal_bindings if item.signal_id == signal_id
    )
    if not carrier_bindings:
        return "UNRESOLVED", ("Signal has no explicitly bound physical carriers.",), ()

    carrier_ids: list[str] = []
    carrier_keys: set[tuple[str, str]] = set()
    carrier_paths: list[tuple[str, tuple[tuple, ...]]] = []
    adjacency: dict[tuple, set[tuple]] = {}
    directed: dict[tuple, set[tuple]] = {}
    diagnostics: list[str] = []
    ambiguous = False

    for binding in carrier_bindings:
        key = (binding.carrier_kind.value, binding.carrier_id)
        if key in carrier_keys:
            ambiguous = True
            diagnostics.append(
                f"Physical carrier {binding.carrier_id!r} is bound to the same signal more than once."
            )
            continue
        carrier_keys.add(key)
        if binding.carrier_kind is CarrierKind.CABLE_CORE:
            carrier = cores.get(binding.carrier_id)
        elif binding.carrier_kind is CarrierKind.PANEL_WIRE:
            carrier = wires.get(binding.carrier_id)
        else:
            diagnostics.append(
                f"{binding.carrier_kind.value} carrier {binding.carrier_id!r} has no typed terminal-path resolver."
            )
            continue
        if carrier is None:
            diagnostics.append(f"Bound physical carrier {binding.carrier_id!r} is missing.")
            continue
        role = getattr(getattr(carrier, "role", None), "value", getattr(carrier, "role", None))
        if role not in {
            WiringConductorRole.SIGNAL.value,
            WiringConductorRole.RETURN.value,
            WiringConductorRole.COMMUNICATION.value,
        }:
            diagnostics.append(
                f"Bound carrier {carrier.id!r} has conductor role {role!r}, "
                "which is not permitted to carry a logical signal."
            )
            continue
        path = tuple(item.canonical_identity for item in carrier.terminal_path)
        if len(path) < 2:
            diagnostics.append(f"Physical carrier {carrier.id!r} has no complete terminal-to-terminal path.")
            continue
        carrier_ids.append(carrier.id)
        carrier_paths.append((carrier.id, path))
        for first, second in zip(path, path[1:]):
            adjacency.setdefault(first, set()).add(second)
            adjacency.setdefault(second, set()).add(first)
            if binding.direction in {"SOURCE_TO_SINK", "BIDIRECTIONAL"}:
                directed.setdefault(first, set()).add(second)
            if binding.direction in {"SINK_TO_SOURCE", "BIDIRECTIONAL"}:
                directed.setdefault(second, set()).add(first)

    if diagnostics:
        return ("AMBIGUOUS" if ambiguous else "UNRESOLVED"), tuple(diagnostics), tuple(sorted(carrier_ids))
    if not carrier_paths:
        return "UNRESOLVED", ("Signal has no supported physical cable-core or panel-wire route.",), ()

    terminal_points = {item.id: item for item in inventory.terminal_points}
    for accessory in inventory.terminal_accessories:
        if (
            accessory.state is not TerminalAccessoryState.CLOSED
            or accessory.kind not in _SIGNAL_CONTINUITY_ACCESSORY_KINDS
        ):
            # Earth links and unclassified accessories are not series signal
            # continuity. Only declared, closed, signal-path link types bridge.
            continue
        for first_id, second_id in accessory.active_conductive_pairs:
            first_point = terminal_points.get(first_id)
            second_point = terminal_points.get(second_id)
            if first_point is None or second_point is None:
                return "UNRESOLVED", (
                    f"Closed terminal accessory {accessory.id!r} references a missing terminal point.",
                ), tuple(sorted(carrier_ids))
            first = (first_point.terminal_block_id, first_point.terminal_number, first_point.id)
            second = (second_point.terminal_block_id, second_point.terminal_number, second_point.id)
            adjacency.setdefault(first, set()).add(second)
            adjacency.setdefault(second, set()).add(first)
            directed.setdefault(first, set()).add(second)
            directed.setdefault(second, set()).add(first)

    if source not in adjacency:
        return "UNRESOLVED", (
            "No bound physical carrier begins at the active MeasurementChannel source terminal.",
        ), tuple(sorted(carrier_ids))
    reachable = _reachable(adjacency, source)
    disconnected = tuple(
        carrier_id for carrier_id, path in carrier_paths
        if any(terminal not in reachable for terminal in path)
    )
    if disconnected:
        return "UNRESOLVED", (
            "Signal physical carrier chain is discontinuous; disconnected carrier(s): "
            + ", ".join(sorted(disconnected)) + ".",
        ), tuple(sorted(carrier_ids))
    if sink not in adjacency or sink not in reachable:
        return "UNRESOLVED", (
            "Declared logical input sink terminal is absent from or disconnected in the physical carrier graph.",
        ), tuple(sorted(carrier_ids))

    forward = _count_simple_paths(directed, source, sink)
    reverse = _count_simple_paths(directed, sink, source)
    requested = direction.upper()
    if requested == "SOURCE_TO_SINK":
        count = forward
    elif requested == "SINK_TO_SOURCE":
        count = reverse
    elif requested == "BIDIRECTIONAL":
        if forward > 1 or reverse > 1:
            return "AMBIGUOUS", (
                "More than one directed physical route exists between the source and declared input terminal.",
            ), tuple(sorted(carrier_ids))
        if forward == 0 or reverse == 0:
            return "UNRESOLVED", (
                "Physical carrier path does not support bidirectional flow between source and declared input terminal.",
            ), tuple(sorted(carrier_ids))
        count = 1
    else:
        return "UNRESOLVED", (f"Unsupported endpoint direction {direction!r}.",), tuple(sorted(carrier_ids))
    if count == 0:
        return "UNRESOLVED", (
            f"Physical carrier direction does not permit {requested} flow to the declared input terminal.",
        ), tuple(sorted(carrier_ids))
    if count > 1:
        return "AMBIGUOUS", (
            "More than one directed physical carrier path reaches the declared input terminal.",
        ), tuple(sorted(carrier_ids))
    return "RESOLVED", (), tuple(sorted(carrier_ids))


def resolve_signal_endpoint_bindings(
    inventory: InstrumentationWiringInventory,
    *,
    project_id: str,
    activation_generation: int,
    measurement_channel_configurations: Iterable[Any] | None,
    measurement_channels: Iterable[Any] | None,
    control_signal_mapping: Any | None,
    protection_configuration: Any | None,
) -> tuple[SignalEndpointResolutionReadModel, ...]:
    """Resolve each persisted Control/Protection endpoint against active owners.

    MeasurementChannel identity is sourced only from
    SignalDefinition.measurement_channel_id. Physical carriers are resolved
    separately from SignalCarrierBinding and exact ordered terminal paths.
    """
    if not isinstance(inventory, InstrumentationWiringInventory):
        raise TypeError("inventory must be an InstrumentationWiringInventory.")
    from core.application.services.instrumentation_receiver_compatibility import (
        validate_control_mapping_binding,
        validate_protection_receiver,
    )

    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("project_id must be a non-empty string.")
    if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
        raise ValueError("activation_generation must be a positive integer.")

    configurations = _index_by_channel_id(
        measurement_channel_configurations, "MeasurementChannel configurations"
    )
    live_channels = _index_by_channel_id(measurement_channels, "MeasurementChannel samples")
    signals = {item.id: item for item in inventory.signals}
    control_bindings = tuple(
        getattr(control_signal_mapping, "bindings", ())
        if control_signal_mapping is not None else ()
    )
    protection_get_binding = getattr(protection_configuration, "get_measurement_binding", None)
    protection_get_element = getattr(protection_configuration, "get", None)

    results: list[SignalEndpointResolutionReadModel] = []
    for binding in inventory.endpoint_bindings:
        endpoint = binding.endpoint
        signal = signals.get(binding.signal_id)
        diagnostics: list[str] = []
        status = "RESOLVED"
        channel_id = signal.measurement_channel_id if signal is not None else None
        channel_configuration = configurations.get(channel_id) if configurations is not None and channel_id else None
        channel_sample = live_channels.get(channel_id) if live_channels is not None and channel_id else None

        if signal is None:
            status = "UNRESOLVED"
            diagnostics.append("Signal definition is not present in the active wiring inventory.")
        elif channel_id is None:
            status = "UNRESOLVED"
            diagnostics.append("Signal definition has no persisted MeasurementChannel association.")
        elif configurations is None:
            status = "UNRESOLVED"
            diagnostics.append("Active MeasurementChannel configuration read service is unavailable.")
        elif channel_configuration is None:
            status = "UNRESOLVED"
            diagnostics.append(f"MeasurementChannel {channel_id!r} is not configured in the active project.")
        elif live_channels is None:
            status = "UNRESOLVED"
            diagnostics.append("Active MeasurementChannel read service is unavailable.")
        elif channel_sample is None:
            status = "UNRESOLVED"
            diagnostics.append(f"MeasurementChannel {channel_id!r} is not active in the project registry.")
        else:
            channel_diagnostics = _channel_signal_diagnostics(signal, channel_configuration)
            if channel_diagnostics:
                status = "UNRESOLVED"
                diagnostics.extend(channel_diagnostics)

        if status == "RESOLVED" and endpoint.kind is SignalEndpointKind.CONTROL_INPUT:
            if control_signal_mapping is None:
                status = "UNRESOLVED"
                diagnostics.append("Active ControlSignalMapping is unavailable.")
            else:
                matches = tuple(
                    item for item in control_bindings
                    if (
                        item.destination.control_id == endpoint.owner_id
                        and item.destination.component_id == endpoint.endpoint_id
                        and item.destination.input_name == endpoint.port
                    )
                )
                if not matches:
                    status = "UNRESOLVED"
                    diagnostics.append("Control input has no exact active ControlSignalMapping.")
                elif len(matches) > 1:
                    status = "AMBIGUOUS"
                    diagnostics.append("More than one active ControlSignalMapping targets this input.")
                else:
                    compatibility = validate_control_mapping_binding(
                        signal, control_signal_mapping, matches[0].destination
                    )
                    if not compatibility.compatible:
                        status = "UNRESOLVED"
                        diagnostics.extend(compatibility.diagnostics)

        elif status == "RESOLVED" and endpoint.kind is SignalEndpointKind.PROTECTION_INPUT:
            if not callable(protection_get_binding) or not callable(protection_get_element):
                status = "UNRESOLVED"
                diagnostics.append("Active ProtectionProjectConfiguration is unavailable.")
            else:
                try:
                    protection_binding = protection_get_binding(endpoint.endpoint_id)
                    element_configuration = protection_get_element(endpoint.owner_id)
                except (KeyError, TypeError, ValueError) as exc:
                    status = "UNRESOLVED"
                    diagnostics.append(f"Protection measurement binding or element is unavailable: {exc}.")
                else:
                    if (
                        protection_binding.protection_element_id != endpoint.owner_id
                        or protection_binding.relay_input_id != endpoint.port
                    ):
                        status = "UNRESOLVED"
                        diagnostics.append("Protection binding owner/input identity does not match the declared endpoint.")
                    elif protection_binding.channel_id != channel_id:
                        status = "UNRESOLVED"
                        diagnostics.append(
                            "Protection measurement binding channel does not match the signal's persisted MeasurementChannel association."
                        )
                    elif endpoint.port == "residual_current":
                        residual = getattr(element_configuration, "residual_current_input", None)
                        mode = getattr(residual, "mode", None) if residual is not None else None
                        mode = getattr(mode, "value", mode)
                        if element_configuration.function_code not in {"50N", "51N"} or residual is None:
                            status = "UNRESOLVED"
                            diagnostics.append("Residual-current endpoint lacks its canonical 50N/51N source configuration.")
                        elif mode == "THREE_PHASE_SUM":
                            status = "UNRESOLVED"
                            diagnostics.append(
                                "Three-phase residual-current input requires a composite multi-channel signal contract; one SignalDefinition cannot represent its phase bindings."
                            )
                        elif (
                            mode != "DIRECT"
                            or getattr(residual, "direct_binding_id", None) != protection_binding.binding_id
                        ):
                            status = "UNRESOLVED"
                            diagnostics.append("Direct residual-current endpoint does not match the configured direct binding.")
                    elif element_configuration.input_channel_ids.get(endpoint.port) != channel_id:
                        status = "UNRESOLVED"
                        diagnostics.append("Protection input channel does not match the declared endpoint channel.")
                    if status == "RESOLVED":
                        compatibility = validate_protection_receiver(
                            signal,
                            function_code=element_configuration.function_code,
                            input_name=endpoint.port,
                            element_id=endpoint.owner_id,
                        )
                        if not compatibility.compatible:
                            status = "UNRESOLVED"
                            diagnostics.extend(compatibility.diagnostics)

        elif status == "RESOLVED":
            status = "UNRESOLVED"
            diagnostics.append(f"Unsupported signal endpoint kind {endpoint.kind!r}.")

        carrier_ids: tuple[str, ...] = ()
        if status == "RESOLVED":
            physical_status, physical_diagnostics, carrier_ids = _resolve_physical_path(
                inventory,
                binding.signal_id,
                channel_configuration,
                endpoint.physical_terminal,
                binding.direction,
            )
            if physical_status != "RESOLVED":
                status = physical_status
                diagnostics.extend(physical_diagnostics)

        terminal = endpoint.physical_terminal
        sink_payload = {
            "equipment_id": terminal.equipment_id,
            "terminal_role": terminal.terminal_role,
            "designation": terminal.designation,
            "terminal_point_id": terminal.terminal_point_id,
        }
        results.append(SignalEndpointResolutionReadModel(
            project_id=project_id,
            activation_generation=activation_generation,
            binding_id=binding.id,
            signal_id=binding.signal_id,
            endpoint_kind=endpoint.kind.value,
            endpoint_id=endpoint.endpoint_id,
            owner_id=endpoint.owner_id,
            port=endpoint.port,
            channel_id=channel_id,
            status=status,
            diagnostics=tuple(diagnostics),
            direction=binding.direction,
            carrier_ids=carrier_ids,
            physical_sink_terminal=sink_payload,
        ))
    return tuple(results)


__all__ = ["resolve_signal_endpoint_bindings"]
