"""Read-only engineering schedules derived from canonical instrumentation wiring."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from core.application.read_models import (
    InstrumentationWiringReadModel,
    InstrumentationWiringSchedulesReadModel,
)


def _terminal_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "equipment_id": value.get("equipment_id"),
        "terminal_role": value.get("terminal_role"),
        "designation": value.get("designation"),
        "terminal_point_id": value.get("terminal_point_id"),
    }


def build_instrumentation_wiring_schedules(
    wiring: InstrumentationWiringReadModel,
    endpoint_resolutions: tuple[Any, ...] = (),
) -> InstrumentationWiringSchedulesReadModel:
    """Build all wiring schedules from one detached canonical project snapshot.

    The builder is deliberately read-only. Missing values remain None or
    unresolved diagnostics; no cable construction, route, rating, tag or
    terminal assignment is inferred.
    """
    if not isinstance(wiring, InstrumentationWiringReadModel):
        raise TypeError("wiring must be an InstrumentationWiringReadModel.")

    cables = {str(item["id"]): item for item in wiring.cables}
    cores = {str(item["id"]): item for item in wiring.cores}
    panel_wires = {str(item["id"]): item for item in wiring.panel_wires}
    signals = {str(item["id"]): item for item in wiring.signals}
    terminal_blocks = {str(item["id"]): item for item in wiring.terminal_blocks}
    terminal_points = {str(item["id"]): item for item in wiring.terminal_points}

    signal_bindings_by_carrier: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    signal_tags_by_carrier: dict[tuple[str, str], set[str]] = defaultdict(set)
    signal_ids_by_carrier: dict[tuple[str, str], set[str]] = defaultdict(set)
    for binding in wiring.signal_bindings:
        key = (str(binding["carrier_kind"]), str(binding["carrier_id"]))
        signal_bindings_by_carrier[key].append(binding)
        signal = signals.get(str(binding["signal_id"]))
        if signal is not None:
            signal_tags_by_carrier[key].add(str(signal["tag"]))
            signal_ids_by_carrier[key].add(str(signal["id"]))

    resolutions = {str(item.binding_id): item for item in endpoint_resolutions}
    endpoint_bindings_by_signal: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for binding in wiring.endpoint_bindings:
        endpoint_bindings_by_signal[str(binding["signal_id"])].append(binding)

    def carrier_summary(kind: str, carrier_id: str) -> dict[str, Any]:
        binding_records = signal_bindings_by_carrier.get((kind, carrier_id), ())
        if kind == "CABLE_CORE":
            carrier = cores.get(carrier_id)
            if carrier is None:
                return {"carrier_kind": kind, "carrier_id": carrier_id, "missing": True}
            cable = cables.get(str(carrier["cable_id"]))
            return {
                "carrier_kind": kind,
                "carrier_id": carrier_id,
                "carrier_tag": carrier.get("core_tag"),
                "cable_id": carrier.get("cable_id"),
                "cable_tag": cable.get("tag") if cable is not None else None,
                "core_number": carrier.get("core_number"),
                "conductor_role": carrier.get("role"),
                "colour": carrier.get("colour"),
                "pair_id": carrier.get("pair_id"),
                "terminal_path": tuple(_terminal_payload(item) for item in carrier.get("terminal_path", ())),
                "signal_ids": tuple(sorted(signal_ids_by_carrier.get((kind, carrier_id), ()))),
                "signal_tags": tuple(sorted(signal_tags_by_carrier.get((kind, carrier_id), ()))),
                "source_channel_ids": tuple(sorted({
                    str(item["source_channel_id"])
                    for item in binding_records if item.get("source_channel_id") is not None
                })),
                "directions": tuple(sorted({str(item.get("direction", "BIDIRECTIONAL")) for item in binding_records})),
            }
        if kind == "PANEL_WIRE":
            carrier = panel_wires.get(carrier_id)
            if carrier is None:
                return {"carrier_kind": kind, "carrier_id": carrier_id, "missing": True}
            return {
                "carrier_kind": kind,
                "carrier_id": carrier_id,
                "carrier_tag": carrier.get("tag"),
                "conductor_role": carrier.get("role"),
                "cross_section_mm2": carrier.get("cross_section_mm2"),
                "colour": carrier.get("colour"),
                "terminal_path": tuple(_terminal_payload(item) for item in carrier.get("terminal_path", ())),
                "signal_ids": tuple(sorted(signal_ids_by_carrier.get((kind, carrier_id), ()))),
                "signal_tags": tuple(sorted(signal_tags_by_carrier.get((kind, carrier_id), ()))),
                "source_channel_ids": tuple(sorted({
                    str(item["source_channel_id"])
                    for item in binding_records if item.get("source_channel_id") is not None
                })),
                "directions": tuple(sorted({str(item.get("direction", "BIDIRECTIONAL")) for item in binding_records})),
            }
        return {
            "carrier_kind": kind,
            "carrier_id": carrier_id,
            "carrier_tag": None,
            "signal_ids": tuple(sorted(signal_ids_by_carrier.get((kind, carrier_id), ()))),
            "signal_tags": tuple(sorted(signal_tags_by_carrier.get((kind, carrier_id), ()))),
            "source_channel_ids": tuple(sorted({
                str(item["source_channel_id"])
                for item in binding_records if item.get("source_channel_id") is not None
            })),
            "directions": tuple(sorted({str(item.get("direction", "BIDIRECTIONAL")) for item in binding_records})),
        }

    carrier_records: list[dict[str, Any]] = []
    for kind, records in (("CABLE_CORE", cores), ("PANEL_WIRE", panel_wires)):
        for carrier_id in sorted(records):
            carrier_records.append(carrier_summary(kind, carrier_id))

    cable_schedule = []
    for cable_id in sorted(cables):
        cable = cables[cable_id]
        cable_cores = [
            carrier_summary("CABLE_CORE", core_id)
            for core_id, core in cores.items()
            if str(core["cable_id"]) == cable_id
        ]
        cable_schedule.append({
            "cable_id": cable_id,
            "cable_tag": cable.get("tag"),
            "service": cable.get("service"),
            "core_count": cable.get("core_count"),
            "cable_type": cable.get("cable_type"),
            "conductor_material": cable.get("conductor_material"),
            "cross_section_mm2": cable.get("cross_section_mm2"),
            "rated_voltage_v": cable.get("rated_voltage_v"),
            "length_m": cable.get("length_m"),
            "from_location": cable.get("from_location"),
            "to_location": cable.get("to_location"),
            "revision": cable.get("revision"),
            "lifecycle_status": cable.get("lifecycle_status"),
            "cores": tuple(sorted(cable_cores, key=lambda item: (item.get("core_number") or 0, item["carrier_id"]))),
            "signal_tags": tuple(sorted({
                tag for item in cable_cores for tag in item.get("signal_tags", ())
            })),
        })

    core_schedule = sorted(
        (item for item in carrier_records if item["carrier_kind"] == "CABLE_CORE"),
        key=lambda item: (str(item.get("cable_tag") or ""), int(item.get("core_number") or 0), item["carrier_id"]),
    )

    connected_points: dict[str, list[dict[str, Any]]] = defaultdict(list)
    interconnection_list: list[dict[str, Any]] = []
    point_to_point_list: list[dict[str, Any]] = []

    for carrier in carrier_records:
        path = tuple(carrier.get("terminal_path", ()))
        kind = str(carrier["carrier_kind"])
        for index, terminal in enumerate(path):
            point_id = terminal.get("terminal_point_id")
            if point_id is not None:
                connected_points[str(point_id)].append({
                    "carrier_kind": kind,
                    "carrier_id": carrier["carrier_id"],
                    "carrier_tag": carrier.get("carrier_tag"),
                    "core_number": carrier.get("core_number"),
                    "position": index + 1,
                    "signal_tags": carrier.get("signal_tags", ()),
                })
        for index, (source, target) in enumerate(zip(path, path[1:]), start=1):
            interconnection_list.append({
                "carrier_kind": kind,
                "carrier_id": carrier["carrier_id"],
                "carrier_tag": carrier.get("carrier_tag"),
                "cable_id": carrier.get("cable_id"),
                "cable_tag": carrier.get("cable_tag"),
                "core_number": carrier.get("core_number"),
                "signal_tags": carrier.get("signal_tags", ()),
                "source_channel_ids": carrier.get("source_channel_ids", ()),
                "directions": carrier.get("directions", ()),
                "from_terminal": source,
                "to_terminal": target,
                "hop_number": index,
            })
        point_to_point_list.append({
            "carrier_kind": kind,
            "carrier_id": carrier["carrier_id"],
            "carrier_tag": carrier.get("carrier_tag"),
            "cable_id": carrier.get("cable_id"),
            "cable_tag": carrier.get("cable_tag"),
            "core_number": carrier.get("core_number"),
            "conductor_role": carrier.get("conductor_role"),
            "signal_tags": carrier.get("signal_tags", ()),
            "source_channel_ids": carrier.get("source_channel_ids", ()),
            "directions": carrier.get("directions", ()),
            "from_terminal": path[0] if path else None,
            "to_terminal": path[-1] if path else None,
            "intermediate_terminals": path[1:-1] if len(path) > 2 else (),
            "terminal_path": path,
            "complete": len(path) >= 2,
        })

    terminal_plan = []
    accessories_by_block: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for accessory in wiring.terminal_accessories:
        accessories_by_block[str(accessory["terminal_block_id"])].append(accessory)
    points_by_block: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for point in wiring.terminal_points:
        points_by_block[str(point["terminal_block_id"])].append(point)

    for block_id in sorted(terminal_blocks):
        block = terminal_blocks[block_id]
        points = []
        for point in sorted(points_by_block.get(block_id, ()), key=lambda item: (str(item["terminal_number"]), str(item["id"]))):
            points.append({
                "terminal_point_id": point["id"],
                "terminal_number": point["terminal_number"],
                "designation": point["designation"],
                "manufacturer_designation": point.get("manufacturer_designation"),
                "function": point.get("function"),
                "side": point.get("side"),
                "lifecycle_status": point.get("lifecycle_status"),
                "connected_carriers": tuple(sorted(
                    connected_points.get(str(point["id"]), ()),
                    key=lambda item: (item["carrier_kind"], item["carrier_id"], item["position"]),
                )),
            })
        accessories = tuple({
            "accessory_id": item["id"],
            "tag": item["tag"],
            "kind": item["kind"],
            "state": item["state"],
            "terminal_point_ids": tuple(item["terminal_point_ids"]),
            "conductive_pairs": tuple(tuple(pair) for pair in item.get("conductive_pairs", ())),
            "rated_voltage_v": item.get("rated_voltage_v"),
            "rated_current_a": item.get("rated_current_a"),
            "manufacturer": item.get("manufacturer"),
            "part_number": item.get("part_number"),
        } for item in sorted(accessories_by_block.get(block_id, ()), key=lambda item: str(item["tag"])))
        terminal_plan.append({
            "terminal_block_id": block_id,
            "terminal_block_tag": block.get("tag"),
            "panel_id": block.get("panel_id"),
            "location": block.get("location"),
            "terminal_count": block.get("terminal_count"),
            "terminal_type": block.get("terminal_type"),
            "manufacturer": block.get("manufacturer"),
            "part_number": block.get("part_number"),
            "revision": block.get("revision"),
            "lifecycle_status": block.get("lifecycle_status"),
            "terminals": tuple(points),
            "accessories": accessories,
        })

    instrument_loop_schedule = []
    for signal_id in sorted(signals):
        signal = signals[signal_id]
        bindings = endpoint_bindings_by_signal.get(signal_id, ())
        endpoint_rows = []
        for binding in sorted(bindings, key=lambda item: str(item["id"])):
            endpoint = binding["endpoint"]
            resolution = resolutions.get(str(binding["id"]))
            endpoint_rows.append({
                "binding_id": binding["id"],
                "endpoint_kind": endpoint.get("kind"),
                "endpoint_id": endpoint.get("endpoint_id"),
                "owner_id": endpoint.get("owner_id"),
                "port": endpoint.get("port"),
                "direction": binding.get("direction", "SOURCE_TO_SINK"),
                "physical_sink_terminal": (
                    _terminal_payload(endpoint["physical_terminal"])
                    if endpoint.get("physical_terminal") is not None else None
                ),
                "resolution_status": getattr(resolution, "status", "UNRESOLVED"),
                "diagnostics": tuple(getattr(resolution, "diagnostics", ("No active endpoint resolution is available.",))),
            })
        sources = tuple(
            row for row in endpoint_rows if row["endpoint_kind"] == "MEASUREMENT_CHANNEL"
        )
        consumers = tuple(
            row for row in endpoint_rows if row["endpoint_kind"] in {"CONTROL_INPUT", "PROTECTION_INPUT"}
        )
        signal_carriers = tuple(
            carrier for carrier in carrier_records
            if signal_id in carrier.get("signal_ids", ())
        )
        all_resolved = (
            bool(sources)
            and bool(consumers)
            and all(item["resolution_status"] == "RESOLVED" for item in endpoint_rows)
        )
        instrument_loop_schedule.append({
            "signal_id": signal_id,
            "signal_tag": signal.get("tag"),
            "description": signal.get("description"),
            "signal_kind": signal.get("kind"),
            "unit": signal.get("unit"),
            "phase": signal.get("phase"),
            "sources": sources,
            "consumers": consumers,
            "carriers": signal_carriers,
            "resolution_status": "RESOLVED" if all_resolved else "UNRESOLVED",
            "diagnostics": tuple(
                diagnostic for item in endpoint_rows for diagnostic in item["diagnostics"]
            ),
        })

    return InstrumentationWiringSchedulesReadModel(
        project_id=wiring.project_id,
        activation_generation=wiring.activation_generation,
        cable_schedule=tuple(cable_schedule),
        core_schedule=tuple(core_schedule),
        terminal_plan=tuple(terminal_plan),
        instrument_loop_schedule=tuple(instrument_loop_schedule),
        interconnection_list=tuple(sorted(
            interconnection_list,
            key=lambda item: (item["carrier_kind"], item["carrier_id"], item["hop_number"]),
        )),
        point_to_point_list=tuple(sorted(
            point_to_point_list,
            key=lambda item: (item["carrier_kind"], item["carrier_id"]),
        )),
    )


__all__ = ["build_instrumentation_wiring_schedules"]
