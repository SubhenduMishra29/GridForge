"""Read-only Control/Protection views of canonical physical wiring provenance.

The helper joins detached Application read models only. It does not own wiring,
create identities, mutate Core, or infer physical continuity from canvas geometry.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _terminal_label(reference: Any) -> str:
    if not isinstance(reference, Mapping):
        return str(reference)
    equipment_id = str(reference.get("equipment_id") or "?")
    role = str(reference.get("terminal_role") or "?")
    designation = str(reference.get("designation") or "?")
    point_id = reference.get("terminal_point_id")
    suffix = f" [terminal point {point_id}]" if point_id else ""
    return f"{equipment_id}.{role} ({designation}){suffix}"


def _normalized_ids(values: Iterable[Any] | str | None) -> frozenset[str]:
    if values is None:
        return frozenset()
    if isinstance(values, str):
        values = (values,)
    return frozenset(str(value).strip() for value in values if value is not None and str(value).strip())


def instrumentation_wiring_provenance_lines(
    application: Any,
    *,
    endpoint_kind: str,
    owner_ids: Iterable[Any] | str | None = None,
    endpoint_ids: Iterable[Any] | str | None = None,
) -> tuple[str, ...]:
    """Format exact consumer endpoint bindings and their declared physical paths.

    Resolution status and diagnostics come from the Application resolver. Carrier
    identities, terminal paths and hop IDs come from the canonical wiring read
    model. The two snapshots must belong to the same project activation.
    """
    owners = _normalized_ids(owner_ids)
    endpoints = _normalized_ids(endpoint_ids)
    if not owners and not endpoints:
        return ("No consumer endpoint is selected.",)

    read_wiring = getattr(application, "read_instrumentation_wiring", None)
    resolve_endpoints = getattr(application, "resolve_instrumentation_signal_endpoints", None)
    if not callable(read_wiring) or not callable(resolve_endpoints):
        return ("Application physical-wiring provenance read path is unavailable.",)

    try:
        wiring = read_wiring()
        resolutions = tuple(resolve_endpoints())
    except (RuntimeError, AttributeError, TypeError, ValueError) as exc:
        return (f"Physical-wiring provenance unavailable: {exc}",)

    project_id = str(getattr(wiring, "project_id", ""))
    generation = getattr(wiring, "activation_generation", None)
    if not project_id or isinstance(generation, bool) or not isinstance(generation, int):
        return ("Physical-wiring snapshot has no valid project activation identity.",)

    selected = tuple(
        item for item in resolutions
        if str(getattr(item, "endpoint_kind", "")).upper() == str(endpoint_kind).upper()
        and (not owners or str(getattr(item, "owner_id", "")) in owners)
        and (not endpoints or str(getattr(item, "endpoint_id", "")) in endpoints)
    )
    if any(
        str(getattr(item, "project_id", "")) != project_id
        or getattr(item, "activation_generation", None) != generation
        for item in selected
    ):
        return ("Endpoint and wiring snapshots belong to different project activations; refresh required.",)
    if not selected:
        return ("No canonical signal endpoint binding is declared for this selection.",)

    signals = {str(item.get("id")): item for item in wiring.signals}
    cables = {str(item.get("id")): item for item in wiring.cables}
    cores = {str(item.get("id")): item for item in wiring.cores}
    panel_wires = {str(item.get("id")): item for item in wiring.panel_wires}
    signal_bindings: dict[str, list[Mapping[str, Any]]] = {}
    for binding in wiring.signal_bindings:
        signal_bindings.setdefault(str(binding.get("signal_id")), []).append(binding)
    hops_by_carrier: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for hop in wiring.connection_hops:
        key = (str(hop.get("carrier_kind")), str(hop.get("carrier_id")))
        hops_by_carrier.setdefault(key, []).append(hop)

    lines: list[str] = []
    for resolution in sorted(
        selected,
        key=lambda item: (
            str(getattr(item, "owner_id", "")),
            str(getattr(item, "port", "")),
            str(getattr(item, "endpoint_id", "")),
            str(getattr(item, "binding_id", "")),
        ),
    ):
        signal_id = str(resolution.signal_id)
        signal = signals.get(signal_id, {})
        signal_tag = str(signal.get("tag") or signal_id)
        lines.append(
            f"{resolution.status} | Signal {signal_tag} [{signal_id}]"
        )
        lines.append(
            f"  Consumer: {resolution.owner_id}.{resolution.port} "
            f"[endpoint {resolution.endpoint_id}; binding {resolution.binding_id}]"
        )
        lines.append(
            f"  MeasurementChannel: {resolution.channel_id or 'unresolved'} | "
            f"Direction: {resolution.direction}"
        )

        declared_bindings = sorted(
            signal_bindings.get(signal_id, ()),
            key=lambda item: (str(item.get("carrier_kind")), str(item.get("carrier_id"))),
        )
        resolved_carrier_ids = set(resolution.carrier_ids)
        if not declared_bindings:
            lines.append("  Physical carriers: none explicitly bound.")
        for binding in declared_bindings:
            carrier_kind = str(binding.get("carrier_kind") or "UNKNOWN")
            carrier_id = str(binding.get("carrier_id") or "?")
            resolved = carrier_id in resolved_carrier_ids
            state = "resolved" if resolved else "declared; not resolved"
            if carrier_kind == "CABLE_CORE":
                carrier = cores.get(carrier_id)
                if carrier is None:
                    lines.append(f"  CABLE_CORE {carrier_id}: carrier record missing ({state}).")
                    continue
                cable = cables.get(str(carrier.get("cable_id")))
                cable_tag = str(cable.get("tag")) if cable is not None else str(carrier.get("cable_id") or "?")
                tag = str(carrier.get("core_tag") or f"{cable_tag}/C{carrier.get('core_number', '?')}")
                role = str(carrier.get("role") or "unspecified")
                terminal_path = tuple(carrier.get("terminal_path") or ())
            elif carrier_kind == "PANEL_WIRE":
                carrier = panel_wires.get(carrier_id)
                if carrier is None:
                    lines.append(f"  PANEL_WIRE {carrier_id}: carrier record missing ({state}).")
                    continue
                tag = str(carrier.get("tag") or carrier_id)
                role = str(carrier.get("role") or "unspecified")
                terminal_path = tuple(carrier.get("terminal_path") or ())
            else:
                lines.append(f"  {carrier_kind} {carrier_id} ({state}); no typed terminal path is available.")
                continue

            lines.append(f"  {carrier_kind}: {tag} [{carrier_id}] | role {role} | {state}")
            if terminal_path:
                lines.append(
                    "    Declared terminal path: "
                    + " -> ".join(_terminal_label(item) for item in terminal_path)
                )
            else:
                lines.append("    Declared terminal path: not recorded.")

            hops = sorted(
                hops_by_carrier.get((carrier_kind, carrier_id), ()),
                key=lambda item: (int(item.get("revision", 0)), str(item.get("id", ""))),
            )
            if hops:
                lines.append(
                    "    Stable physical hops: "
                    + ", ".join(
                        f"{item.get('id')} ({item.get('lifecycle_status', 'unknown')})"
                        for item in hops
                    )
                )
            else:
                lines.append("    Stable physical hops: no hop identity recorded for this carrier.")

        sink = resolution.physical_sink_terminal
        if isinstance(sink, Mapping):
            lines.append(f"  Declared input terminal: {_terminal_label(sink)}")
        for diagnostic in resolution.diagnostics:
            lines.append(f"  Diagnostic: {diagnostic}")

    return tuple(lines)


__all__ = ["instrumentation_wiring_provenance_lines"]
