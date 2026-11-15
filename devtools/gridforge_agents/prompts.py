from __future__ import annotations

from pathlib import Path


ARCHITECTURE_RULES = """
GridForge V2 engineering constraints:
- Core owns electrical/domain truth: equipment, terminals, topology/connectivity, validation, studies, calculations and results.
- Application owns commands, services, transactions, lifecycle, controlled mutation, events and read models.
- UI/SLD owns projection, geometry, interaction and presentation.
- Canonical path: UI -> Controller -> Command -> Application -> Core -> Event/Result -> Read Model/Projection -> UI.
- No Qt, QGraphicsItem, widget, SLD scene or UI symbols in Core.
- A symbol is not equipment. SLD geometry is not electrical topology. Draft state is not committed engineering state.
- Project persistence is project-rooted. Do not persist Qt runtime objects or live telemetry as project configuration.
- Do not add parallel registries, command managers, event buses, topology, measurement systems or persistence authorities.
- Preserve explicit IDs, units, timestamp domains, provenance, quality and fail-closed behavior. Never fabricate engineering data.
- Route mutations through canonical Application services/commands. Do not mutate Core directly from UI or runtime shortcuts.
- Inspect current source and callers before changing code. Issue descriptions may be stale.
- Keep changes narrow, avoid unrelated docs/generated files, and inspect the complete diff.
- Tests and CI are not acceptance gates unless the user or issue explicitly requires them. Run bounded source-level checks where useful.
- Never push, merge, close issues, alter remote branches or modify main. Work only in the isolated local worktree.
""".strip()


DOMAIN_GUIDANCE = {
    "core-topology": "Focus on Core equipment, terminal identity, physical conductor paths, topology and domain validation. Never infer electrical connectivity from geometry.",
    "sld-ui": "Focus on SLD, projection, controllers, workspace, Qt integration, editor-scoped commands and Apply/Discard behavior. Route mutations through Application.",
    "persistence": "Focus on .gridforge packaging, canonical project.json, schema migrations, save/load validation and project lifecycle compensation. Preserve deterministic backward compatibility.",
    "measurement": "Focus on CT/PT/CVT, RTD/thermocouple, acquisition channels, MeasurementChannel, calibration, quality, timestamps and physical wiring provenance. Keep physical wiring distinct from logical signals.",
    "protection": "Focus on relay inputs, function-specific measurement validity, protection zones, decisions, output mapping and fail-closed Application actuation. A decision is not an acknowledgement.",
    "control-simulation": "Focus on Control Canvas, typed channels, freshness, units, dynamic controllers, transient simulation scheduling, DeviceCommand and observed feedback.",
    "general": "Use the issue's own domain boundaries. Do not invent a new architecture or duplicate an existing service.",
}


def classify_issue(title: str, body: str) -> str:
    title_text = title.casefold()
    text = (title + " " + body).casefold()

    # Explicit issue ownership tags take precedence over incidental words in the body.
    if "[control" in title_text or "[dynamic control" in title_text:
        return "control-simulation"
    if "[protection" in title_text or "[ui/protection" in title_text:
        return "protection"
    if "[instrumentation" in title_text or "[measurement" in title_text or "[ui/measurement" in title_text:
        return "measurement"
    if "[simulation/measurement" in title_text and ("motor dynamics" in title_text or "actuation" in title_text):
        return "control-simulation"
    if title_text.startswith("[ui/") or "[control canvas" in title_text:
        return "sld-ui"
    if any(word in text for word in ("measurementchannel", "instrument", "ct/pt", "ct pt", "thermocouple", "rtd", "signal", "wiring")):
        return "measurement"
    if any(word in text for word in ("protection", "relay", "ansi", "overcurrent", "trip", "breaker failure")):
        return "protection"
    if any(word in text for word in ("control", "actuator", "governor", "avr", "pss", "transient")):
        return "control-simulation"
    if any(word in text for word in ("persistence", "save", "load", "schema", "serialization", "gridforge package")):
        return "persistence"
    if any(word in text for word in ("sld", "canvas", "qt", "viewport", "inspector", "keyboard", "tool strip", "projection")):
        return "sld-ui"
    if any(word in text for word in ("topology", "terminal", "conductor", "equipment", "transformer", "network")):
        return "core-topology"
    return "general"
