"""Renderer-neutral Control/Protection signal provenance projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SignalProvenancePresentation:
    """Detached signal and physical carrier identity for one logical endpoint."""

    binding_id: str
    endpoint_kind: str
    endpoint_id: str
    owner_id: str | None
    port: str | None
    signal_id: str
    signal_tag: str
    carrier_labels: tuple[str, ...]
    status: str
    diagnostics: tuple[str, ...] = ()
    direction: str = "SOURCE_TO_SINK"
    physical_sink_terminal: tuple[str, ...] | None = None

    @property
    def short_label(self) -> str:
        if self.status != "RESOLVED":
            return f"! {self.status}: {self.signal_tag}"
        carrier_text = ", ".join(self.carrier_labels) if self.carrier_labels else "no physical carrier"
        return f"{self.signal_tag} | {carrier_text}"

    @property
    def detail_text(self) -> str:
        lines = [
            f"Signal: {self.signal_tag} ({self.signal_id})",
            f"Endpoint: {self.endpoint_kind} {self.owner_id or ''}/{self.endpoint_id}/{self.port or ''}",
            f"Physical carriers: {', '.join(self.carrier_labels) if self.carrier_labels else 'none'}",
            f"Direction: {self.direction}",
            (
                "Physical sink terminal: "
                + " / ".join(self.physical_sink_terminal)
                if self.physical_sink_terminal is not None
                else "Physical sink terminal: not declared"
            ),
            f"Resolution: {self.status}",
        ]
        lines.extend(f"Diagnostic: {item}" for item in self.diagnostics)
        return "\n".join(lines)


def project_signal_provenance(
    wiring: Any,
    resolutions: tuple[Any, ...] | list[Any],
) -> tuple[SignalProvenancePresentation, ...]:
    """Join detached wiring records and active endpoint resolution for UI use.

    This adapter never queries Core or mutates Application-owned records.
    """
    if wiring is None:
        return ()
    signals = {str(item["id"]): item for item in wiring.signals}
    cables = {str(item["id"]): item for item in wiring.cables}
    cores = {str(item["id"]): item for item in wiring.cores}
    panel_wires = {str(item["id"]): item for item in wiring.panel_wires}
    carriers_by_signal: dict[str, list[str]] = {}

    for binding in wiring.signal_bindings:
        signal_id = str(binding["signal_id"])
        kind = str(binding["carrier_kind"])
        carrier_id = str(binding["carrier_id"])
        label = carrier_id
        if kind == "CABLE_CORE":
            core = cores.get(carrier_id)
            if core is not None:
                cable = cables.get(str(core["cable_id"]))
                cable_tag = str(cable["tag"]) if cable is not None else str(core["cable_id"])
                core_designation = str(core.get("core_tag") or core["core_number"])
                label = f"{cable_tag} / core {core_designation}"
        elif kind == "PANEL_WIRE":
            wire = panel_wires.get(carrier_id)
            if wire is not None:
                label = str(wire["tag"])
        else:
            label = f"{kind}: {carrier_id}"
        carriers_by_signal.setdefault(signal_id, []).append(label)

    result: list[SignalProvenancePresentation] = []
    for resolution in resolutions:
        signal_id = str(resolution.signal_id)
        signal = signals.get(signal_id)
        if signal is None:
            continue
        result.append(SignalProvenancePresentation(
            binding_id=str(resolution.binding_id),
            endpoint_kind=str(resolution.endpoint_kind),
            endpoint_id=str(resolution.endpoint_id),
            owner_id=resolution.owner_id,
            port=resolution.port,
            signal_id=signal_id,
            signal_tag=str(signal["tag"]),
            carrier_labels=tuple(carriers_by_signal.get(signal_id, ())),
            status=str(resolution.status),
            diagnostics=tuple(resolution.diagnostics),
            direction=str(getattr(resolution, "direction", "SOURCE_TO_SINK")),
            physical_sink_terminal=(
                (
                    str(resolution.physical_sink_terminal["equipment_id"]),
                    str(resolution.physical_sink_terminal["terminal_role"]),
                    *(
                        str(resolution.physical_sink_terminal[key])
                        for key in ("equipment_id", "terminal_role", "designation", "terminal_point_id")
                        if resolution.physical_sink_terminal.get(key) is not None
                    ),
                )
                if getattr(resolution, "physical_sink_terminal", None) is not None
                else None
            ),
        ))
    return tuple(result)


__all__ = ["SignalProvenancePresentation", "project_signal_provenance"]
