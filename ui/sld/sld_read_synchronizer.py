# ============================================================
# File: ui/sld/sld_read_synchronizer.py
# GridForge V2 — SLD Read Synchronizer
# Author: Subhendu Mishra
# ============================================================
"""Read-only synchronization from Application read models to ephemeral SLD projections.

Persistent SLD state is deliberately absent from this module. Persistent
creation/update/delete and semantic binding reconciliation are owned by the
Application pre-commit path and SLDService. This synchronizer only refreshes
projection state from immutable Application read models.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel

from .sld_projection import SLDProjection
from .sld_projection_manager import SLDProjectionManager
from .sld_read_adapter import SLDReadAdapter
from .sld_vocabulary import semantic_type


class SLDReadSynchronizer:
    """Synchronize immutable Application read state into ephemeral SLD projections."""

    def __init__(self, projection_manager: SLDProjectionManager, application: Any = None) -> None:
        if not isinstance(projection_manager, SLDProjectionManager):
            raise TypeError("projection_manager must be an SLDProjectionManager")
        self._projection_manager = projection_manager
        self._read_adapter = SLDReadAdapter()
        self._application = application
        self._reconciliation_diagnostics: tuple[dict[str, Any], ...] = ()

    @property
    def projection_manager(self) -> SLDProjectionManager:
        return self._projection_manager

    @property
    def application(self) -> Any:
        return self._application

    def attach_application(self, application: Any) -> None:
        if application is None:
            raise TypeError("application must not be None")
        self._application = application

    def detach_application(self) -> Any:
        application = self._application
        self._application = None
        return application

    @property
    def reconciliation_diagnostics(self) -> tuple[dict[str, Any], ...]:
        """Return deterministic Core/SLD Simple Wire reconciliation diagnostics."""
        return self._reconciliation_diagnostics

    @staticmethod
    def _core_endpoint_identity(endpoint: Mapping[str, Any]) -> tuple[str, str, str | None] | None:
        kind = str(endpoint.get("kind", "")).strip().lower()
        if kind == "terminal":
            object_id = endpoint.get("object_id")
            role = endpoint.get("terminal_role")
            if isinstance(object_id, str) and object_id and isinstance(role, str) and role:
                return ("terminal", object_id, role)
            return None
        if kind == "bus":
            object_id = endpoint.get("object_id")
            attachment_id = endpoint.get("attachment_id")
            if isinstance(object_id, str) and object_id and isinstance(attachment_id, str) and attachment_id:
                return ("bus", object_id, attachment_id)
            return None
        if kind == "junction":
            junction_id = endpoint.get("junction_id", endpoint.get("object_id"))
            if isinstance(junction_id, str) and junction_id:
                return ("junction", junction_id, None)
        return None

    @staticmethod
    def _sld_endpoint_identity(endpoint: Any) -> tuple[str, str, str | None] | None:
        if endpoint is None:
            return None
        kind_value = getattr(getattr(endpoint, "kind", None), "value", getattr(endpoint, "kind", None))
        kind = str(kind_value or "").strip().lower()
        if kind == "equipment":
            equipment_id = getattr(endpoint, "equipment_id", None)
            role = getattr(endpoint, "terminal_role", None)
            if isinstance(equipment_id, str) and equipment_id and isinstance(role, str) and role:
                return ("terminal", equipment_id, role)
            return None
        if kind == "bus":
            bus_id = getattr(endpoint, "bus_id", None)
            attachment_id = getattr(endpoint, "attachment_id", None)
            if isinstance(bus_id, str) and bus_id and isinstance(attachment_id, str) and attachment_id:
                return ("bus", bus_id, attachment_id)
        return None

    def reconcile_simple_wires(
        self,
        read_model: NetworkReadModel | None = None,
        *,
        presentation: Any | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Audit Core wire identity and endpoint topology against one SLD document.

        This is read-only. Background-document callers pass the exact document;
        route geometry is deliberately excluded because it is presentation data.
        """
        application = self._require_application()
        if read_model is None:
            read_model = application.read_network()
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        if presentation is None:
            presentation = getattr(application, "presentation", None)
        model = getattr(presentation, "model", None)
        connections = tuple(getattr(model, "connections", ())) if model is not None else ()
        core_wires = {wire.connection_id: wire for wire in read_model.simple_wires}
        sld_projection = {}
        diagnostics = []
        for connection in connections:
            properties = getattr(connection, "properties", {})
            if str(properties.get("connection_kind", "")).upper() != "SIMPLE_WIRE":
                continue
            core_id = properties.get("core_connection_id")
            if not core_id:
                diagnostics.append({"code": "MISSING_CORE_CONNECTION_ID", "presentation_id": connection.connection_id})
                continue
            core_id = str(core_id)
            if core_id in sld_projection:
                diagnostics.append({"code": "DUPLICATE_PRESENTATION_COMPANION", "connection_id": core_id})
            sld_projection[core_id] = connection

        core_ids = set(core_wires)
        for core_id in sorted(core_ids - set(sld_projection)):
            diagnostics.append({"code": "CORE_WIRE_WITHOUT_SLD_COMPANION", "connection_id": core_id})
        for core_id in sorted(set(sld_projection) - core_ids):
            diagnostics.append({
                "code": "SLD_WIRE_WITHOUT_CORE",
                "connection_id": core_id,
                "presentation_id": sld_projection[core_id].connection_id,
            })

        for core_id in sorted(core_ids & set(sld_projection)):
            wire = core_wires[core_id]
            connection = sld_projection[core_id]
            core_pair = (
                self._core_endpoint_identity(wire.endpoint_a),
                self._core_endpoint_identity(wire.endpoint_b),
            )
            sld_pair = (
                self._sld_endpoint_identity(getattr(connection, "source_endpoint", None)),
                self._sld_endpoint_identity(getattr(connection, "target_endpoint", None)),
            )
            if any(endpoint is None for endpoint in sld_pair):
                diagnostics.append({
                    "code": "SLD_ENDPOINT_IDENTITY_MISSING",
                    "connection_id": core_id,
                    "presentation_id": connection.connection_id,
                })
                continue
            if any(endpoint is None for endpoint in core_pair):
                diagnostics.append({
                    "code": "UNSUPPORTED_CORE_ENDPOINT_IDENTITY",
                    "connection_id": core_id,
                    "presentation_id": connection.connection_id,
                })
                continue
            normalized_core = tuple(sorted(core_pair, key=repr))
            normalized_sld = tuple(sorted(sld_pair, key=repr))
            if normalized_core != normalized_sld:
                diagnostics.append({
                    "code": "CORE_SLD_ENDPOINT_MISMATCH",
                    "connection_id": core_id,
                    "presentation_id": connection.connection_id,
                    "core_endpoints": normalized_core,
                    "sld_endpoints": normalized_sld,
                })

        result = tuple(diagnostics)
        # Background audits must not overwrite the active document's diagnostics.
        if presentation is getattr(application, "presentation", None):
            self._reconciliation_diagnostics = result
        return result

    def synchronize_network_from_application(self) -> tuple[SLDProjection, ...]:
        return self.synchronize_network(None, self._require_application().read_network())

    def synchronize_protection_from_application(self) -> tuple[SLDProjection, ...]:
        return self.synchronize_protection(None, self._require_application().read_protection())

    def synchronize_element_from_application(self, element_type: str, object_id: str) -> SLDProjection:
        return self.synchronize_element(self._require_application().read_element(element_type, object_id))

    def synchronize_network(self, presentation: Any, read_model: NetworkReadModel, *, initial_positions: Mapping[str, tuple[float, float]] | None = None) -> tuple[SLDProjection, ...]:
        """Refresh only the NETWORK projection registry; never mutate persistent SLD state."""
        if not isinstance(read_model, NetworkReadModel):
            raise TypeError("read_model must be a NetworkReadModel")
        adapted = self._read_adapter.network(read_model)
        self.reconcile_simple_wires(adapted, presentation=presentation)
        projections = self._projection_manager.project_network(adapted)
        self._projection_manager.reconcile_network(frozenset(e.object_id for e in adapted.elements))
        return projections

    def synchronize_protection(self, presentation: Any, read_model: ProtectionReadModel) -> tuple[SLDProjection, ...]:
        """Refresh only the PROTECTION projection registry; never mutate persistent SLD state."""
        if not isinstance(read_model, ProtectionReadModel):
            raise TypeError("read_model must be a ProtectionReadModel")
        adapted = self._read_adapter.protection(read_model)
        projections = self._projection_manager.project_protection(adapted)
        self._projection_manager.reconcile_protection(frozenset(e.object_id for e in adapted.elements))
        return projections

    def synchronize_element(self, read_model: ElementReadModel) -> SLDProjection:
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        if semantic_type(read_model.element_type) == "RELAY":
            raise ValueError("Relay presentation belongs to the protection projection domain.")
        return self._projection_manager.project_network_element(self._read_adapter.element(read_model))

    def synchronize_protection_element(self, read_model: ElementReadModel) -> SLDProjection:
        if not isinstance(read_model, ElementReadModel):
            raise TypeError("read_model must be an ElementReadModel")
        return self._projection_manager.project_protection_element(self._read_adapter.element(read_model))

    def clear(self) -> None:
        self._projection_manager.clear()

    def _require_application(self) -> Any:
        if self._application is None:
            raise RuntimeError("SLD Application read facade is not configured")
        return self._application


__all__ = ["SLDReadSynchronizer"]
