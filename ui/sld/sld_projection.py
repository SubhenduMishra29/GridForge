# ============================================================
# File: ui/sld/sld_projection.py
# GridForge V2 — SLD Projection
# Author: Subhendu Mishra
# ============================================================
"""SLD presentation projection backed by Application read data."""

from __future__ import annotations

from core.application.read_models import ElementReadModel

from ui.projection.projection import Projection
from ui.projection.projection_state import ProjectionState
from ui.sld.sld_vocabulary import SLD_TOPOLOGY_BRANCH_TYPES


class SLDProjection(Projection):
    """Project one immutable Application element snapshot into SLD state."""

    def __init__(self, read_model: ElementReadModel) -> None:
        super().__init__(read_model.object_id)
        self.update_from_read_model(read_model)

    @property
    def element_type(self) -> str:
        return self._element_type

    @property
    def topology_endpoints(self) -> tuple[str, ...]:
        """Return presentation-only endpoint identities for topology-bearing elements."""
        explicit = (
            self._attributes.get("endpoint_from_id"),
            self._attributes.get("endpoint_to_id"),
        )
        endpoints = tuple(value for value in explicit if isinstance(value, str) and value)
        if len(endpoints) == 2:
            return endpoints
        return tuple(ref for ref in self._connectivity_refs if isinstance(ref, str) and ref)

    @property
    def is_topology_bearing(self) -> bool:
        return self.element_type in SLD_TOPOLOGY_BRANCH_TYPES

    def update_from_read_model(self, read_model: ElementReadModel) -> None:
        """Refresh this projection from an Application read snapshot."""
        if read_model.object_id != self.object_id:
            raise ValueError("SLD projection cannot change object identity")

        labels = tuple(
            str(value)
            for _, value in sorted(read_model.labels.items())
        )
        self._element_type = read_model.element_type
        self._connectivity_refs = tuple(read_model.connectivity_refs)
        self._attributes = dict(read_model.attributes)
        self.set_state(
            ProjectionState(
                object_id=read_model.object_id,
                display_type=read_model.element_type,
                labels=labels,
                connectivity_refs=read_model.connectivity_refs,
            )
        )


__all__ = ["SLDProjection"]
