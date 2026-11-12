"""Read-only resolution of canonical signal endpoint bindings.

This Application adapter correlates wiring metadata with the existing
MeasurementChannel, ControlSignalMapping and Protection configuration owners.
It never mutates those owners or invents missing relationships.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.application.read_models import SignalEndpointResolutionReadModel
from core.model.instrument_wiring import (
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
                        else:
                            channel = channels[source_channel]
                            if getattr(source, "signal", None) not in {
                                "value", "engineering_value", str(getattr(channel, "signal_type", "")).lower()
                            }:
                                status = "UNRESOLVED"
                                diagnostics.append("Control source signal selector is incompatible with its MeasurementChannel.")
                    elif source_domain == "core":
                        if read_service is None or not callable(getattr(read_service, "element", None)):
                            status = "UNRESOLVED"
                            diagnostics.append("Active Core read service is unavailable for the Control signal source.")
                        else:
                            try:
                                source_model = read_service.element(source.element_type, source.object_id)
                                attributes = getattr(source_model, "attributes", {})
                                if source.signal not in attributes:
                                    raise KeyError(source.signal)
                            except Exception as exc:
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
                    if (
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
                    if status == "RESOLVED" and protection_binding.channel_id not in channels:
                        status = "UNRESOLVED"
                        diagnostics.append(
                            f"Protection MeasurementChannel {protection_binding.channel_id!r} is not active."
                        )

        results.append(SignalEndpointResolutionReadModel(
            binding_id=binding.id,
            signal_id=binding.signal_id,
            endpoint_kind=endpoint.kind.value,
            endpoint_id=endpoint.endpoint_id,
            owner_id=endpoint.owner_id,
            port=endpoint.port,
            status=status,
            diagnostics=tuple(diagnostics),
        ))

    return tuple(results)


__all__ = ["resolve_signal_endpoint_bindings"]
