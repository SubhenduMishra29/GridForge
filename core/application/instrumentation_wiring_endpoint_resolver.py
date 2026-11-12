"""Read-only resolution of canonical signal endpoint bindings.

This Application adapter correlates wiring metadata with the existing
MeasurementChannel, ControlSignalMapping and Protection configuration owners.
It never mutates those owners or invents missing relationships.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.application.read_models import SignalEndpointResolutionReadModel
from core.model.instrument_wiring import (
    CarrierKind,
    InstrumentationWiringInventory,
    SignalEndpointKind,
)


def resolve_signal_endpoint_bindings(
    inventory: InstrumentationWiringInventory,
    *,
    measurement_channels: Iterable[Any] | None,
    control_signal_mapping: Any | None,
    protection_configuration: Any | None,
    read_service: Any | None = None,
) -> tuple[SignalEndpointResolutionReadModel, ...]:
    """Resolve every explicit endpoint against active Application-owned state.

    Missing providers and stale references produce unresolved diagnostics.
    No endpoint is resolved by tag, display name, or proximity.
    """
    if not isinstance(inventory, InstrumentationWiringInventory):
        raise TypeError("inventory must be an InstrumentationWiringInventory.")

    channels: dict[str, Any] = {}
    if measurement_channels is not None:
        for channel in measurement_channels:
            channel_id = getattr(channel, "channel_id", None)
            if not isinstance(channel_id, str) or not channel_id.strip():
                raise TypeError("MeasurementChannel read models must expose a stable channel_id.")
            if channel_id in channels:
                raise ValueError(f"Duplicate MeasurementChannel read identity {channel_id!r}.")
            channels[channel_id] = channel

    control_bindings = tuple(
        getattr(control_signal_mapping, "bindings", ())
        if control_signal_mapping is not None else ()
    )
    protection_get_binding = getattr(protection_configuration, "get_measurement_binding", None)
    protection_get_element = getattr(protection_configuration, "get", None)

    cores_by_id = {item.id: item for item in inventory.cores}
    panel_wires_by_id = {item.id: item for item in inventory.panel_wires}

    def physical_source_diagnostics(
        signal_id: str,
        channel_id: str,
        *,
        sink_terminal: Any | None = None,
        direction: str = "SOURCE_TO_SINK",
    ) -> tuple[str, ...]:
        """Validate source, sink and directed continuity of bound physical carriers."""
        channel = channels.get(channel_id)
        if channel is None:
            return (f"MeasurementChannel {channel_id!r} is not active.",)
        source_id = getattr(channel, "source_id", None)
        source_terminal = getattr(channel, "source_terminal", None)
        if not isinstance(source_id, str) or not source_id.strip():
            return ("MeasurementChannel has no explicit physical source identity.",)
        if not isinstance(source_terminal, Mapping) or source_terminal.get("kind") != "TERMINAL":
            return ("MeasurementChannel has no explicit physical source terminal reference.",)
        source_equipment_id = source_terminal.get("equipment_id")
        source_terminal_role = source_terminal.get("terminal_role")
        if source_equipment_id != source_id or not isinstance(source_terminal_role, str) or not source_terminal_role:
            return ("MeasurementChannel source equipment and source terminal owner identities disagree or are incomplete.",)

        if sink_terminal is not None and not hasattr(sink_terminal, "identity"):
            return ("Endpoint physical sink terminal reference is malformed.",)

        carriers: list[tuple[str, tuple[tuple[str, str], ...], str]] = []
        unsupported: list[str] = []
        unassigned_carriers: list[str] = []
        for carrier_binding in inventory.signal_bindings:
            if carrier_binding.signal_id != signal_id:
                continue
            if carrier_binding.carrier_kind not in {CarrierKind.CABLE_CORE, CarrierKind.PANEL_WIRE}:
                unsupported.append(
                    f"{carrier_binding.carrier_kind.value} carrier {carrier_binding.carrier_id!r} has no typed terminal-path resolver."
                )
                continue
            if carrier_binding.source_channel_id is None:
                unassigned_carriers.append(carrier_binding.carrier_id)
                continue
            if carrier_binding.source_channel_id not in channel_refs_by_signal.get(signal_id, set()):
                return (
                    f"Signal carrier {carrier_binding.carrier_id!r} references unbound MeasurementChannel "
                    f"{carrier_binding.source_channel_id!r}.",
                )
            if carrier_binding.source_channel_id != channel_id:
                continue
            if carrier_binding.carrier_kind is CarrierKind.CABLE_CORE:
                carrier = cores_by_id.get(carrier_binding.carrier_id)
            else:
                carrier = panel_wires_by_id.get(carrier_binding.carrier_id)
            if carrier is None:
                return (f"Signal carrier {carrier_binding.carrier_id!r} cannot be resolved.",)
            path = tuple(item.identity for item in carrier.terminal_path)
            if len(path) < 2:
                return (
                    f"Signal carrier {carrier.id!r} has no complete terminal-to-terminal path.",
                )
            carriers.append((carrier.id, path, carrier_binding.direction))
        if unassigned_carriers:
            return (
                "Signal contains carrier(s) without explicit MeasurementChannel ownership: "
                + ", ".join(sorted(unassigned_carriers)) + ".",
            )

        if unsupported:
            return tuple(unsupported)
        if not carriers:
            return ("Signal has no explicitly bound physical cable-core or panel-wire carriers.",)

        adjacency: dict[tuple[str, str], set[tuple[str, str]]] = {}
        directed_adjacency: dict[tuple[str, str], set[tuple[str, str]]] = {}
        for _carrier_id, path, carrier_direction in carriers:
            for first, second in zip(path, path[1:]):
                adjacency.setdefault(first, set()).add(second)
                adjacency.setdefault(second, set()).add(first)
                if carrier_direction in {"SOURCE_TO_SINK", "BIDIRECTIONAL"}:
                    directed_adjacency.setdefault(first, set()).add(second)
                if carrier_direction in {"SINK_TO_SOURCE", "BIDIRECTIONAL"}:
                    directed_adjacency.setdefault(second, set()).add(first)

        source = (source_equipment_id, source_terminal_role)
        if source not in adjacency:
            return ("No physical carrier path begins at the MeasurementChannel source terminal.",)

        reachable = {source}
        pending = [source]
        while pending:
            current = pending.pop()
            for neighbour in adjacency.get(current, ()):
                if neighbour not in reachable:
                    reachable.add(neighbour)
                    pending.append(neighbour)

        disconnected = [
            carrier_id
            for carrier_id, path, _direction in carriers
            if not any(terminal in reachable for terminal in path)
            or any(terminal not in reachable for terminal in path)
        ]
        if disconnected:
            return (
                "Signal physical carrier chain is discontinuous; disconnected carrier(s): "
                + ", ".join(sorted(disconnected)) + ".",
            )

        if sink_terminal is not None:
            sink = sink_terminal.identity
            if sink not in adjacency:
                return ("Declared logical input sink terminal is absent from the signal carrier graph.",)
            if sink not in reachable:
                return ("Declared logical input sink terminal is physically disconnected from the MeasurementChannel source.",)

            def directed_reachable(start: tuple[str, str], target: tuple[str, str]) -> bool:
                visited = {start}
                pending = [start]
                while pending:
                    current = pending.pop()
                    if current == target:
                        return True
                    for neighbour in directed_adjacency.get(current, ()):
                        if neighbour not in visited:
                            visited.add(neighbour)
                            pending.append(neighbour)
                return False

            forward = directed_reachable(source, sink)
            reverse = directed_reachable(sink, source)
            if direction == "SOURCE_TO_SINK" and not forward:
                return ("Physical carrier direction does not permit SOURCE_TO_SINK flow to the declared input terminal.",)
            if direction == "SINK_TO_SOURCE" and not reverse:
                return ("Physical carrier direction does not permit SINK_TO_SOURCE flow from the declared input terminal.",)
            if direction == "BIDIRECTIONAL" and not (forward and reverse):
                return ("Physical carrier path is not bidirectional between source and declared input terminal.",)
        return ()

    channel_refs_by_signal: dict[str, set[str]] = {}
    for reference in inventory.endpoint_bindings:
        endpoint = reference.endpoint
        if endpoint.kind is SignalEndpointKind.MEASUREMENT_CHANNEL:
            channel_refs_by_signal.setdefault(reference.signal_id, set()).add(endpoint.endpoint_id)

    results: list[SignalEndpointResolutionReadModel] = []
    for binding in inventory.endpoint_bindings:
        endpoint = binding.endpoint
        diagnostics: list[str] = []
        status = "RESOLVED"

        if endpoint.kind is SignalEndpointKind.MEASUREMENT_CHANNEL:
            if measurement_channels is None:
                status = "UNRESOLVED"
                diagnostics.append("Active MeasurementChannel read service is unavailable.")
            elif endpoint.endpoint_id not in channels:
                status = "UNRESOLVED"
                diagnostics.append(
                    f"MeasurementChannel {endpoint.endpoint_id!r} is not present in the active project."
                )
            else:
                physical_diagnostics = physical_source_diagnostics(
                    binding.signal_id, endpoint.endpoint_id
                )
                if physical_diagnostics:
                    status = "UNRESOLVED"
                    diagnostics.extend(physical_diagnostics)

        elif endpoint.kind is SignalEndpointKind.CONTROL_INPUT:
            if control_signal_mapping is None:
                status = "UNRESOLVED"
                diagnostics.append("Active ControlSignalMapping is unavailable.")
            else:
                matches = [
                    item for item in control_bindings
                    if (
                        getattr(getattr(item, "destination", None), "control_id", None) == endpoint.owner_id
                        and getattr(getattr(item, "destination", None), "component_id", None) == endpoint.endpoint_id
                        and getattr(getattr(item, "destination", None), "input_name", None) == endpoint.port
                    )
                ]
                if len(matches) == 0:
                    status = "UNRESOLVED"
                    diagnostics.append("Control input does not have an exact active ControlSignalMapping.")
                elif len(matches) > 1:
                    status = "AMBIGUOUS"
                    diagnostics.append("More than one active ControlSignalMapping targets this input.")
                else:
                    source = matches[0].source
                    source_domain = getattr(source, "domain", None)
                    if source_domain == "measurement":
                        source_channel = str(getattr(source, "object_id", ""))
                        if source_channel not in channel_refs_by_signal.get(binding.signal_id, set()):
                            status = "UNRESOLVED"
                            diagnostics.append(
                                "Control measurement source has no matching signal-to-MeasurementChannel binding."
                            )
                        elif source_channel not in channels:
                            status = "UNRESOLVED"
                            diagnostics.append(
                                f"Control source MeasurementChannel {source_channel!r} is not active."
                            )
                        elif endpoint.physical_terminal is None:
                            status = "UNRESOLVED"
                            diagnostics.append("Control input has no explicit physical sink terminal reference.")
                        else:
                            channel = channels[source_channel]
                            if getattr(source, "signal", None) not in {
                                "value", "engineering_value", str(getattr(channel, "signal_type", "")).lower()
                            }:
                                status = "UNRESOLVED"
                                diagnostics.append("Control source signal selector is incompatible with its MeasurementChannel.")
                            if status == "RESOLVED":
                                physical_diagnostics = physical_source_diagnostics(
                                    binding.signal_id,
                                    source_channel,
                                    sink_terminal=endpoint.physical_terminal,
                                    direction=binding.direction,
                                )
                                if physical_diagnostics:
                                    status = "UNRESOLVED"
                                    diagnostics.extend(physical_diagnostics)
                    elif source_domain == "core":
                        if endpoint.physical_terminal is None:
                            status = "UNRESOLVED"
                            diagnostics.append("Control input has no explicit physical sink terminal reference.")
                        elif read_service is None or not callable(getattr(read_service, "element", None)):
                            status = "UNRESOLVED"
                            diagnostics.append("Active Core read service is unavailable for the Control signal source.")
                        else:
                            try:
                                source_model = read_service.element(source.element_type, source.object_id)
                                attributes = getattr(source_model, "attributes", {})
                                if source.signal not in attributes:
                                    raise KeyError(source.signal)
                                status = "UNRESOLVED"
                                diagnostics.append(
                                    "Core-domain Control source has no explicit physical source-terminal contract; "
                                    "the physical signal route cannot be proven."
                                )
                            except (KeyError, TypeError, ValueError) as exc:
                                status = "UNRESOLVED"
                                diagnostics.append(
                                    f"Control Core source cannot be resolved: {type(exc).__name__}: {exc}."
                                )
                    else:
                        status = "UNRESOLVED"
                        diagnostics.append(f"Unsupported Control signal source domain {source_domain!r}.")

        elif endpoint.kind is SignalEndpointKind.PROTECTION_INPUT:
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
                    if endpoint.physical_terminal is None:
                        status = "UNRESOLVED"
                        diagnostics.append("Protection relay input has no explicit physical sink terminal reference.")
                    elif (
                        protection_binding.protection_element_id != endpoint.owner_id
                        or protection_binding.relay_input_id != endpoint.port
                    ):
                        status = "UNRESOLVED"
                        diagnostics.append(
                            "Protection binding owner/input identity does not match the declared endpoint."
                        )
                    elif endpoint.port == "residual_current":
                        if getattr(element_configuration, "function_code", None) not in {"50N", "51N"}:
                            status = "UNRESOLVED"
                            diagnostics.append("Residual-current endpoint is not valid for this Protection function.")
                        else:
                            residual = getattr(element_configuration, "residual_current_input", None)
                            if residual is None:
                                status = "UNRESOLVED"
                                diagnostics.append("Residual-current relay input has no explicit residual source configuration.")
                            else:
                                residual_ids = (
                                    set((getattr(residual, "phase_binding_ids", None) or {}).values())
                                    if getattr(residual, "mode", None) == "THREE_PHASE_SUM"
                                    else {getattr(residual, "direct_binding_id", None)}
                                )
                                if protection_binding.binding_id not in residual_ids:
                                    status = "UNRESOLVED"
                                    diagnostics.append("Protection binding is not declared by the residual-current input configuration.")
                    elif element_configuration.input_channel_ids.get(endpoint.port) != protection_binding.channel_id:
                        status = "UNRESOLVED"
                        diagnostics.append(
                            "Protection binding channel does not match the configured relay input channel."
                        )
                    if status == "RESOLVED" and protection_binding.channel_id not in channel_refs_by_signal.get(binding.signal_id, set()):
                        status = "UNRESOLVED"
                        diagnostics.append(
                            "Protection input has no matching signal-to-MeasurementChannel binding."
                        )
                    if status == "RESOLVED":
                        physical_diagnostics = physical_source_diagnostics(
                            binding.signal_id,
                            protection_binding.channel_id,
                            sink_terminal=endpoint.physical_terminal,
                            direction=binding.direction,
                        )
                        if physical_diagnostics:
                            status = "UNRESOLVED"
                            diagnostics.extend(physical_diagnostics)

        results.append(SignalEndpointResolutionReadModel(
            binding_id=binding.id,
            signal_id=binding.signal_id,
            endpoint_kind=endpoint.kind.value,
            endpoint_id=endpoint.endpoint_id,
            owner_id=endpoint.owner_id,
            port=endpoint.port,
            status=status,
            diagnostics=tuple(diagnostics),
            direction=binding.direction,
            physical_sink_terminal=(
                {
                    "equipment_id": endpoint.physical_terminal.equipment_id,
                    "terminal_role": endpoint.physical_terminal.terminal_role,
                    "designation": endpoint.physical_terminal.designation,
                }
                if endpoint.physical_terminal is not None else None
            ),
        ))

    return tuple(results)


__all__ = ["resolve_signal_endpoint_bindings"]
