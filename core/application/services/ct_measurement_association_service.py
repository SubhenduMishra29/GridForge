# ============================================================
# File: core/application/services/ct_measurement_association_service.py
# GridForge V2 — Application CT Measurement Association Service
# Author: Subhendu Mishra
# ============================================================

"""Project-scoped Application facade for Core CT association resolution."""

from __future__ import annotations

from typing import Any

from core.network import (
    CTMeasurementAssociation,
    CTMeasurementAssociationResolver,
)


class CTMeasurementAssociationService:
    """Resolve CT placement for the active project without mutating Core state.

    Application supplies the active project context and canonical Network.
    Core performs the electrical connectivity interpretation. Results are
    scoped to the active project's canonical Network by this service.
    """

    def resolve(self, context: Any, ct_id: str) -> CTMeasurementAssociation:
        if context is None:
            raise ValueError("An active project context is required for CT association resolution.")
        project_id = getattr(context, "project_id", None)
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("The active project context must expose a valid project_id.")
        network = getattr(context, "network", None)
        if network is None:
            raise ValueError("The active project context does not expose its canonical Network.")
        result = CTMeasurementAssociationResolver(network).resolve(ct_id)
        return result

    def resolve_all(self, context: Any) -> tuple[CTMeasurementAssociation, ...]:
        if context is None:
            raise ValueError("An active project context is required for CT association resolution.")
        project_id = getattr(context, "project_id", None)
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("The active project context must expose a valid project_id.")
        network = getattr(context, "network", None)
        if network is None:
            raise ValueError("The active project context does not expose its canonical Network.")
        return CTMeasurementAssociationResolver(network).resolve_all()


__all__ = ["CTMeasurementAssociationService"]
