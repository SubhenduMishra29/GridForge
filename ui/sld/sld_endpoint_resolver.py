# ============================================================
# GridForge V2 — SLD semantic endpoint resolver
# ============================================================
"""Resolve semantic SLD endpoints into transient scene coordinates."""

from __future__ import annotations

from typing import Any, Mapping

from ui.core.qt import QPointF
from ui.sld.sld_model import SLDEndpoint


class SLDEndpointResolver:
    """Resolve presentation endpoint identity through the realized graphics items."""

    def resolve(self, endpoint: SLDEndpoint, items: Mapping[str, Any]) -> QPointF:
        if not isinstance(endpoint, SLDEndpoint):
            raise TypeError("endpoint must be an SLDEndpoint")
        item = items.get(endpoint.node_id)
        if item is None:
            raise KeyError(f"No realized SLD item for node {endpoint.node_id!r}")
        candidates = tuple(getattr(item, "snap_points", lambda: ())())
        if endpoint.kind.value == "equipment":
            if str(getattr(item, "object_id", "")) != str(endpoint.equipment_id):
                raise ValueError(
                    f"Equipment endpoint identity {endpoint.equipment_id!r} does not match "
                    f"realized node object {getattr(item, 'object_id', None)!r}"
                )
            matches = tuple(
                candidate for candidate in candidates
                if str(candidate.get("object_id", "")) == str(endpoint.equipment_id)
                and candidate.get("terminal_name") == endpoint.terminal_role
            )
        else:
            if str(getattr(item, "object_id", "")) != str(endpoint.bus_id):
                raise ValueError(
                    f"Bus endpoint identity {endpoint.bus_id!r} does not match "
                    f"realized node object {getattr(item, 'object_id', None)!r}"
                )
            matches = tuple(
                candidate for candidate in candidates
                if str(candidate.get("object_id", "")) == str(endpoint.bus_id)
                and str(candidate.get("bus_id", "")) == str(endpoint.bus_id)
                and candidate.get("attachment_id") == endpoint.attachment_id
            )
        if len(matches) != 1:
            raise ValueError(
                f"SLD endpoint {endpoint.to_dict()!r} resolved to {len(matches)} candidates"
            )
        position = matches[0].get("position")
        if position is None:
            raise ValueError("Resolved SLD endpoint has no scene position")
        return QPointF(float(position.x()), float(position.y()))


__all__ = ["SLDEndpointResolver"]
